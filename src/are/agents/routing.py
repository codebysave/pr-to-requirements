"""Routing centralizzato del workflow (Decisione 3.5, §16).

Le decisioni di transizione tra i nodi non sono distribuite negli agenti:
vivono qui come funzioni pure, testabili senza invocare alcun LLM.
"""

from __future__ import annotations

from .config import WorkflowConfig
from .state import AssessmentDecision, Extractability, RequirementState

NODE_CHECK_EXTRACTABILITY = "check_extractability"
NODE_GENERATE = "generate"
NODE_RETRIEVE_MEMORY = "retrieve_memory"
NODE_ASSESS = "assess"
NODE_ACCEPT = "accept"
NODE_MARK_NOT_EXTRACTABLE = "mark_not_extractable"
NODE_MARK_REJECTED = "mark_rejected"
NODE_MARK_FAILED_VALIDATION = "mark_failed_validation"


def route_after_extractability(state: RequirementState) -> str:
    """`EXTRACTABLE` → generazione; `NOT_EXTRACTABLE` → terminazione della PR."""

    result = state["extractability"]
    if result is None:
        raise ValueError("Routing invocato prima della verifica di estraibilità.")
    if result.decision is Extractability.EXTRACTABLE:
        return NODE_GENERATE
    return NODE_MARK_NOT_EXTRACTABLE


def route_after_retrieval(state: RequirementState, workflow_config: WorkflowConfig) -> str:
    """Con il valutatore attivo si passa all'assessment; senza, il candidato
    del Generation Agent diventa direttamente l'output (configurazione delle
    prove progressive, Decisione 3.7 §2)."""

    if workflow_config.assessment_enabled:
        return NODE_ASSESS
    return NODE_ACCEPT


def route_after_assessment(state: RequirementState, workflow_config: WorkflowConfig) -> str:
    """Applica `ACCEPT` / `REVISE` / `REJECT` e il limite di tentativi.

    `REVISE` oltre l'ultimo tentativo disponibile non accetta il requisito:
    produce `FAILED_VALIDATION` (Decisione 3.5, §13: nessuna promozione
    automatica del "miglior candidato").
    """

    result = state["assessment"]
    if result is None:
        raise ValueError("Routing invocato prima dell'assessment.")

    if result.decision is AssessmentDecision.ACCEPT:
        return NODE_ACCEPT
    if result.decision is AssessmentDecision.REJECT:
        return NODE_MARK_REJECTED
    if state["generation_attempt"] < workflow_config.max_generation_attempts:
        return NODE_GENERATE
    return NODE_MARK_FAILED_VALIDATION
