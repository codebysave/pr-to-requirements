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
    """Decisione dell'Assessment Agent sul requisito candidato."""

    ACCEPT = "ACCEPT"
    REVISE = "REVISE"
    REJECT = "REJECT"


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
    """Decisione dell'assessment con il relativo feedback strutturato."""

    decision: AssessmentDecision
    feedback: AssessmentFeedback = field(default_factory=AssessmentFeedback)


@dataclass(frozen=True, slots=True)
class RetrievedRequirement:
    """Requisito storico recuperato dalla memoria per il confronto."""

    requirement_id: str
    statement: str
    similarity_score: float


@dataclass(frozen=True, slots=True)
class IterationRecord:
    """Un tentativo del loop Generation → Assessment, conservato per traccia.

    ``assessment`` è ``None`` quando la configurazione sperimentale esegue il
    workflow senza valutatore. Lo storico appartiene ai log dell'esecuzione,
    non alla memoria persistente dei requisiti validati.
    """

    attempt: int
    candidate: str
    assessment: AssessmentResult | None


class RequirementState(TypedDict):
    """Stato condiviso del grafo LangGraph per una singola Pull Request."""

    pull_request: PullRequestRecord
    extractability: ExtractabilityResult | None
    candidate_requirement: str | None
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
        generation_attempt=0,
        retrieved_requirements=(),
        assessment=None,
        final_status=None,
        accepted_requirement=None,
        iteration_history=(),
    )
