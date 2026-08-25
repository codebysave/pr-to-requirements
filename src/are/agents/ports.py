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
    ) -> str:
        """Genera un candidato; dal secondo tentativo riceve anche il feedback."""
        ...


class RequirementAssessor(Protocol):
    """Requirement Assessment Agent: valuta il candidato e decide il routing."""

    def assess(
        self,
        pull_request: PullRequestRecord,
        candidate: str,
        retrieved_requirements: Sequence[RetrievedRequirement],
    ) -> AssessmentResult: ...


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
