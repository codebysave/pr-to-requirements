"""Stato condiviso e tipi del workflow della singola Pull Request (Decisione 3.5).

Lo stato rappresenta il contesto corrente dell'elaborazione di UNA Pull
Request. Il contenuto completo non viene passato integralmente agli LLM: ogni
agente riceve soltanto le informazioni necessarie alla propria responsabilità.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypedDict

from are.input import PullRequestRecord


class Extractability(StrEnum):
    """Esito della verifica preliminare di estraibilità."""

    EXTRACTABLE = "EXTRACTABLE"
    NOT_EXTRACTABLE = "NOT_EXTRACTABLE"


class AssessmentDecision(StrEnum):
    """Decisione dell'Assessment Agent (Decisione 3.5, §10).

    ``CONFIRM_NOT_EXTRACTABLE`` è la risposta alla dichiarazione con cui il
    Generation Agent constata di non poter ricostruire alcun requisito: il
    valutatore la conferma, oppure dissente con ``REVISE`` spiegando quale
    comportamento ritiene identificabile.
    """

    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    REJECT = "REJECT"
    CONFIRM_NOT_EXTRACTABLE = "CONFIRM_NOT_EXTRACTABLE"


class FinalStatus(StrEnum):
    """Stato finale esplicito di ogni elaborazione (Decisione 3.5, §18)."""

    ACCEPTED = "ACCEPTED"
    NOT_EXTRACTABLE = "NOT_EXTRACTABLE"
    REJECTED = "REJECTED"
    FAILED_VALIDATION = "FAILED_VALIDATION"


@dataclass(frozen=True, slots=True)
class ExtractabilityResult:
    """Esito e motivazione della verifica di estraibilità."""

    decision: Extractability
    reason: str = ""


@dataclass(frozen=True, slots=True)
class AssessmentFeedback:
    """Feedback strutturato prodotto dall'Assessment Agent (Decisione 3.5, §11).

    Deve essere direttamente utilizzabile dal Generation Agent nel tentativo
    successivo; non è un commento libero.
    """

    issues: tuple[str, ...] = ()
    unsupported_claims: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    revision_instructions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AssessmentResult:
    """Decisione dell'assessment con il relativo feedback strutturato.

    ``retrieved`` e ``tool_rounds`` restano vuoti nel recupero deterministico,
    dove è il grafo a cercare e a conservare l'esito nello stato. Sono
    valorizzati soltanto quando è il valutatore stesso a invocare il tool sulla
    memoria: in quel caso il grafo non sa cosa il modello abbia chiesto, e
    senza questi due campi non resterebbe traccia verificabile del recupero.
    """

    decision: AssessmentDecision
    feedback: AssessmentFeedback = field(default_factory=AssessmentFeedback)
    retrieved: tuple[RetrievedRequirement, ...] = ()
    tool_rounds: int = 0


@dataclass(frozen=True, slots=True)
class RetrievedRequirement:
    """Requisito storico recuperato dalla memoria per il confronto.

    Non c'è alcun punteggio di somiglianza: il recupero è esaustivo entro i
    filtri di progetto e di data, e a stabilire se il candidato duplichi,
    raffini o contraddica uno di questi requisiti è l'Assessment Agent
    leggendone il testo. Un punteggio che nessuno calcola sarebbe un numero
    inventato, e comunicarlo al modello lo indurrebbe in errore.

    ``source_pr_number`` accompagna il testo perché il valutatore possa citare
    la Pull Request di origine: una segnalazione di duplicazione che nomina il
    caso è verificabile, una generica non lo è.
    """

    requirement_id: str
    statement: str
    source_pr_number: int


@dataclass(frozen=True, slots=True)
class GenerationOutcome:
    """Esito di un tentativo di generazione.

    Il Generation Agent produce un requisito oppure constata di non poterlo
    ricostruire senza inventare (Decisione 3.1, §11.10). La constatazione non
    chiude da sola l'elaborazione: viene sottoposta al valutatore, che la
    conferma o la respinge.
    """

    requirement: str | None = None
    refusal_reason: str | None = None

    @property
    def refused(self) -> bool:
        return self.requirement is None


@dataclass(frozen=True, slots=True)
class IterationRecord:
    """Un tentativo del loop Generation → Assessment, conservato per traccia.

    ``candidate`` è ``None`` quando il generatore ha dichiarato di non poter
    ricostruire un requisito, e la motivazione si trova in ``refusal_reason``.
    ``assessment`` è ``None`` quando la configurazione sperimentale esegue il
    workflow senza valutatore. Lo storico appartiene ai log dell'esecuzione,
    non alla memoria persistente dei requisiti validati.
    """

    attempt: int
    candidate: str | None
    assessment: AssessmentResult | None
    refusal_reason: str | None = None
    retrieved: tuple[RetrievedRequirement, ...] = ()
    """Requisiti storici mostrati al valutatore in questo tentativo.

    Senza questa traccia nel report, verificare che il recupero abbia funzionato
    richiederebbe di rileggere il log a occhio su decine di Pull Request: qui
    diventa un controllo automatico.
    """


class RequirementState(TypedDict):
    """Stato condiviso del grafo LangGraph per una singola Pull Request."""

    pull_request: PullRequestRecord
    extractability: ExtractabilityResult | None
    candidate_requirement: str | None
    generation_refusal: str | None
    generation_attempt: int
    retrieved_requirements: tuple[RetrievedRequirement, ...]
    assessment: AssessmentResult | None
    final_status: FinalStatus | None
    accepted_requirement: str | None
    iteration_history: tuple[IterationRecord, ...]


def create_initial_state(pull_request: PullRequestRecord) -> RequirementState:
    """Costruisce lo stato iniziale del workflow per una Pull Request."""

    return RequirementState(
        pull_request=pull_request,
        extractability=None,
        candidate_requirement=None,
        generation_refusal=None,
        generation_attempt=0,
        retrieved_requirements=(),
        assessment=None,
        final_status=None,
        accepted_requirement=None,
        iteration_history=(),
    )
