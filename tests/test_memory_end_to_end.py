"""La catena completa della memoria, senza chiamare alcun modello.

Questi test percorrono tutto il tragitto che un requisito compie realmente:
viene accettato, scritto nel database, recuperato durante l'elaborazione di una
Pull Request successiva, portato dentro lo stato del grafo e infine composto
nel messaggio che raggiunge il valutatore.

I test unitari verificano i pezzi uno per uno; questi verificano che siano
davvero collegati fra loro. Girano su un database in memoria con agenti finti,
quindi non lasciano file e non costano nulla: è la verifica che vogliamo aver
superato *prima* di accendere qualcosa che consuma chiamate a pagamento.
"""

from __future__ import annotations

from are.agents import (
    AssessmentDecision,
    AssessmentResult,
    Extractability,
    ExtractabilityResult,
    FinalStatus,
    GenerationOutcome,
    RetrievedRequirement,
    WorkflowConfig,
    WorkflowDependencies,
    build_workflow,
)
from are.agents.llm_agents import LLMRequirementAssessor
from are.db import IN_MEMORY, ExhaustiveRequirementRetriever, SqliteRequirementRepository
from are.input import PullRequestRecord
from are.llm import LLMResponse
from are.runner import PipelineRunner

RUN = "20260830T140000Z"


def pr(pr_number: int, giorno: int, repository: str = "owner/repo") -> PullRequestRecord:
    return PullRequestRecord.from_mapping(
        {
            "id": f"{repository.replace('/', '-')}-pr-{pr_number}",
            "repository": repository,
            "pr_number": pr_number,
            "timestamp": f"2026-04-{giorno:02d}T10:00:00Z",
            "title": f"Pull Request numero {pr_number}",
            "body": "Corpo sufficientemente lungo da superare il gate di ingresso.",
        }
    )


class AlwaysExtractable:
    def check(self, pull_request: PullRequestRecord) -> ExtractabilityResult:
        return ExtractabilityResult(Extractability.EXTRACTABLE, "testo sufficiente")


class GeneratorPerPullRequest:
    """Produce un requisito riconoscibile, così si vede da dove proviene."""

    def generate(self, pull_request, previous_candidate, feedback):
        numero = pull_request.pr_number
        return GenerationOutcome(
            requirement=f"The system shall satisfy the need of Pull Request {numero}."
        )


class AcceptingAssessor:
    """Accetta sempre, e registra i requisiti storici che ha ricevuto."""

    def __init__(self) -> None:
        self.received: list[tuple[int, tuple[RetrievedRequirement, ...]]] = []

    def assess(
        self, pull_request, candidate, retrieved_requirements, history=(), generation_refusal=None
    ):
        self.received.append((pull_request.pr_number, tuple(retrieved_requirements)))
        return AssessmentResult(AssessmentDecision.ACCEPT)


class FakeLLMClient:
    """Client finto: risponde sempre ACCEPT e conserva i messaggi ricevuti."""

    def __init__(self) -> None:
        self.requests: list[str] = []

    def complete(self, *, system: str, user_message: str) -> LLMResponse:
        self.requests.append(user_message)
        return LLMResponse(
            text='{"decision": "ACCEPT", "issues": [], "unsupported_claims": [],'
            ' "missing_information": [], "revision_instructions": []}',
            model="fake-model",
            stop_reason="end_turn",
            input_tokens=10,
            output_tokens=5,
        )


def esegui(store: SqliteRequirementRepository, pull_requests, assessor):
    """Esegue il workflow reale con la memoria attiva, una PR alla volta."""

    dependencies = WorkflowDependencies(
        extractability_checker=AlwaysExtractable(),
        generator=GeneratorPerPullRequest(),
        assessor=assessor,
        retriever=ExhaustiveRequirementRetriever(store, run_id=store.run_id),
        store=store,
    )
    graph = build_workflow(dependencies, WorkflowConfig(memory_enabled=True))
    return PipelineRunner(graph, chronological=True).run(pull_requests)


# -- la catena regge -----------------------------------------------------


def test_an_accepted_requirement_reaches_the_next_pull_request() -> None:
    """Scrittura, recupero e passaggio nello stato del grafo, in un colpo solo."""

    assessor = AcceptingAssessor()
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        esegui(store, [pr(1, giorno=1), pr(2, giorno=2)], assessor)

    prima, seconda = assessor.received
    assert prima == (1, ())
    assert [item.source_pr_number for item in seconda[1]] == [1]
    assert seconda[1][0].statement == "The system shall satisfy the need of Pull Request 1."


def test_the_requirement_appears_in_the_message_sent_to_the_model() -> None:
    """L'ultimo anello: il requisito storico finisce davvero nel testo inviato."""

    client = FakeLLMClient()
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        esegui(store, [pr(1, giorno=1), pr(2, giorno=2)], LLMRequirementAssessor(client))

    primo_messaggio, secondo_messaggio = client.requests
    assert "PREVIOUSLY VALIDATED REQUIREMENTS" not in primo_messaggio
    assert "PREVIOUSLY VALIDATED REQUIREMENTS" in secondo_messaggio
    assert "The system shall satisfy the need of Pull Request 1." in secondo_messaggio
    assert "from Pull Request #1" in secondo_messaggio


def test_the_memory_grows_as_the_batch_proceeds() -> None:
    assessor = AcceptingAssessor()
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        esegui(store, [pr(numero, giorno=numero) for numero in (1, 2, 3)], assessor)
        totale = store.count()

    quanti_visti = [len(recuperati) for _, recuperati in assessor.received]
    assert quanti_visti == [0, 1, 2]
    assert totale == 3


# -- e non perde la testa ------------------------------------------------


def test_the_processing_order_is_chronological_not_the_input_order() -> None:
    """La memoria ha senso solo se le Pull Request sono elaborate in ordine."""

    assessor = AcceptingAssessor()
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        # Fornite al contrario: la più recente per prima.
        esegui(store, [pr(9, giorno=20), pr(3, giorno=3)], assessor)

    assert [numero for numero, _ in assessor.received] == [3, 9]
    assert [item.source_pr_number for item in assessor.received[1][1]] == [3]


def test_a_pull_request_never_sees_requirements_from_its_own_future() -> None:
    assessor = AcceptingAssessor()
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        store.store_accepted(pr(99, giorno=28), "Requisito nato da una Pull Request successiva.")
        esegui(store, [pr(1, giorno=1)], assessor)

    assert assessor.received[0][1] == ()


def test_requirements_of_another_project_never_appear() -> None:
    assessor = AcceptingAssessor()
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        store.store_accepted(pr(1, giorno=1, repository="altro/progetto"), "Di un altro progetto.")
        esegui(store, [pr(2, giorno=10)], assessor)

    assert assessor.received[0][1] == ()


def test_only_accepted_requirements_enter_the_memory() -> None:
    """Un requisito rifiutato non deve comparire nel confronto successivo."""

    class RejectingThenAccepting:
        def __init__(self) -> None:
            self.received: list[tuple[int, tuple[RetrievedRequirement, ...]]] = []

        def assess(
            self,
            pull_request,
            candidate,
            retrieved_requirements,
            history=(),
            generation_refusal=None,
        ):
            self.received.append((pull_request.pr_number, tuple(retrieved_requirements)))
            decisione = (
                AssessmentDecision.REJECT
                if pull_request.pr_number == 1
                else AssessmentDecision.ACCEPT
            )
            return AssessmentResult(decisione)

    assessor = RejectingThenAccepting()
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        risultati = esegui(store, [pr(1, giorno=1), pr(2, giorno=2)], assessor)
        totale = store.count()

    assert risultati[0].final_state["final_status"] is FinalStatus.REJECTED
    assert assessor.received[1][1] == ()
    assert totale == 1
