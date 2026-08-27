"""Porte del workflow: le interfacce dei componenti invocati dal grafo.

Il grafo LangGraph non conosce implementazioni concrete: riceve questi
protocolli via ``WorkflowDependencies``. Gli agenti LLM reali (passo
successivo) e la memoria persistente (Decisioni 3.3/3.4) implementeranno
queste interfacce senza richiedere modifiche al workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence

from are.input import PullRequestRecord

from .state import (
    AssessmentFeedback,
    AssessmentResult,
    ExtractabilityResult,
    GenerationOutcome,
    IterationRecord,
    RetrievedRequirement,
)


class ExtractabilityChecker(Protocol):
    """Verifica preliminare: la PR consente di ricostruire un requisito funzionale?

    Può usare un LLM nella sua implementazione, ma è una fase della pipeline,
    non un terzo agente autonomo (Decisione 3.5, §4.3).
    """

    def check(self, pull_request: PullRequestRecord) -> ExtractabilityResult: ...


class RequirementGenerator(Protocol):
    """Requirement Generation Agent: produce il requisito funzionale candidato."""

    def generate(
        self,
        pull_request: PullRequestRecord,
        previous_candidate: str | None,
        feedback: AssessmentFeedback | None,
    ) -> GenerationOutcome:
        """Genera un candidato; dal secondo tentativo riceve anche il feedback.

        Può restituire un esito di rinuncia motivata quando l'evidenza non
        consente di ricostruire alcun requisito: la rinuncia viene comunque
        sottoposta al valutatore.
        """
        ...


class RequirementAssessor(Protocol):
    """Requirement Assessment Agent: valuta il candidato e decide il routing."""

    def assess(
        self,
        pull_request: PullRequestRecord,
        candidate: str | None,
        retrieved_requirements: Sequence[RetrievedRequirement],
        history: Sequence[IterationRecord] = (),
        generation_refusal: str | None = None,
    ) -> AssessmentResult:
        """Valuta il candidato corrente.

        ``history`` contiene i tentativi già esaminati in questa esecuzione,
        con i rispettivi verdetti: serve a mantenere coerenza fra un giro e
        l'altro e a riconoscere un ciclo che non converge. È vuoto al primo
        tentativo.

        ``generation_refusal`` è valorizzato quando il generatore ha rinunciato
        motivatamente invece di produrre un requisito: in quel caso ``candidate``
        è ``None`` e l'oggetto della valutazione è la rinuncia stessa, da
        confermare con ``CONFIRM_NOT_EXTRACTABLE`` o respingere con ``REVISE``.
        """
        ...


class MemoryRetriever(Protocol):
    """Recupero deterministico dei requisiti storici affini al candidato."""

    def retrieve(
        self,
        candidate: str,
        pull_request: PullRequestRecord,
    ) -> Sequence[RetrievedRequirement]: ...


class AcceptedRequirementStore(Protocol):
    """Persistenza del requisito validato, invocata dal controller dopo ACCEPT."""

    def store_accepted(self, pull_request: PullRequestRecord, statement: str) -> None: ...


class NullMemoryRetriever:
    """Retriever inerte, usato quando la memoria è disattivata."""

    def retrieve(
        self,
        candidate: str,
        pull_request: PullRequestRecord,
    ) -> Sequence[RetrievedRequirement]:
        return ()


class NullRequirementStore:
    """Store inerte, usato finché la memoria persistente non è disponibile."""

    def store_accepted(self, pull_request: PullRequestRecord, statement: str) -> None:
        return None


@dataclass(frozen=True, slots=True)
class WorkflowDependencies:
    """Componenti concreti iniettati nel grafo."""

    extractability_checker: ExtractabilityChecker
    generator: RequirementGenerator
    assessor: RequirementAssessor | None = None
    retriever: MemoryRetriever = field(default_factory=NullMemoryRetriever)
    store: AcceptedRequirementStore = field(default_factory=NullRequirementStore)
