"""Costruzione del grafo LangGraph per la singola Pull Request (Decisione 3.5).

LangGraph è l'infrastruttura di controllo del flusso, non un sostituto della
logica applicativa: i nodi delegano alle porte iniettate e il routing resta
centralizzato in ``routing.py``. Il grafo elabora UNA Pull Request; il ciclo
sulle PR del file di input appartiene al Pipeline Runner.

Flusso:

    START → check_extractability ──→ mark_not_extractable → END
                 │
                 ▼
             generate ←──────────────────┐
                 │                       │ REVISE (entro il limite)
                 ├── rinuncia ────┐      │
                 ▼                ▼      │
           retrieve_memory     assess ───┤
                 │                │      │
                 └────────────────┤      │
                                  │      │
        ┌────────┬────────┬───────┴──────┘
        ▼        ▼        ▼        ▼
     accept  rejected  failed_validation  not_extractable
        │        │        │        │
        └────────┴────────┴────────┴──→ END
"""

from __future__ import annotations

import logging
from functools import partial

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from are import console

from .config import WorkflowConfig
from .ports import WorkflowDependencies
from .routing import (
    NODE_ACCEPT,
    NODE_ASSESS,
    NODE_CHECK_EXTRACTABILITY,
    NODE_GENERATE,
    NODE_MARK_FAILED_VALIDATION,
    NODE_MARK_NOT_EXTRACTABLE,
    NODE_MARK_REJECTED,
    NODE_RETRIEVE_MEMORY,
    route_after_assessment,
    route_after_extractability,
    route_after_generation,
    route_after_retrieval,
)
from .state import (
    AssessmentDecision,
    FinalStatus,
    IterationRecord,
    RequirementState,
)

logger = logging.getLogger(__name__)


def build_workflow(
    dependencies: WorkflowDependencies,
    config: WorkflowConfig,
) -> CompiledStateGraph:
    """Costruisce e compila il grafo con le dipendenze e la configurazione date.

    Raises:
        ValueError: se la configurazione richiede l'assessment ma nessun
            assessor è stato fornito.
    """

    if config.assessment_enabled and dependencies.assessor is None:
        raise ValueError("assessment_enabled è attivo ma WorkflowDependencies.assessor è assente.")

    nodes = _WorkflowNodes(dependencies, config)
    builder = StateGraph(RequirementState)

    builder.add_node(NODE_CHECK_EXTRACTABILITY, nodes.check_extractability)
    builder.add_node(NODE_GENERATE, nodes.generate)
    builder.add_node(NODE_RETRIEVE_MEMORY, nodes.retrieve_memory)
    builder.add_node(NODE_ASSESS, nodes.assess)
    builder.add_node(NODE_ACCEPT, nodes.accept)
    builder.add_node(NODE_MARK_NOT_EXTRACTABLE, nodes.mark_not_extractable)
    builder.add_node(NODE_MARK_REJECTED, nodes.mark_rejected)
    builder.add_node(NODE_MARK_FAILED_VALIDATION, nodes.mark_failed_validation)

    builder.add_edge(START, NODE_CHECK_EXTRACTABILITY)
    builder.add_conditional_edges(
        NODE_CHECK_EXTRACTABILITY,
        route_after_extractability,
        [NODE_GENERATE, NODE_MARK_NOT_EXTRACTABLE],
    )
    builder.add_conditional_edges(
        NODE_GENERATE,
        partial(route_after_generation, workflow_config=config),
        [NODE_RETRIEVE_MEMORY, NODE_ASSESS, NODE_MARK_NOT_EXTRACTABLE],
    )
    builder.add_conditional_edges(
        NODE_RETRIEVE_MEMORY,
        partial(route_after_retrieval, workflow_config=config),
        [NODE_ASSESS, NODE_ACCEPT],
    )
    builder.add_conditional_edges(
        NODE_ASSESS,
        partial(route_after_assessment, workflow_config=config),
        [
            NODE_ACCEPT,
            NODE_GENERATE,
            NODE_MARK_REJECTED,
            NODE_MARK_FAILED_VALIDATION,
            NODE_MARK_NOT_EXTRACTABLE,
        ],
    )
    builder.add_edge(NODE_ACCEPT, END)
    builder.add_edge(NODE_MARK_NOT_EXTRACTABLE, END)
    builder.add_edge(NODE_MARK_REJECTED, END)
    builder.add_edge(NODE_MARK_FAILED_VALIDATION, END)

    return builder.compile()


class _WorkflowNodes:
    """Nodi del grafo: funzioni sottili che delegano alle porte iniettate."""

    def __init__(self, dependencies: WorkflowDependencies, config: WorkflowConfig) -> None:
        self._deps = dependencies
        self._config = config

    def check_extractability(self, state: RequirementState) -> dict:
        result = self._deps.extractability_checker.check(state["pull_request"])
        return {"extractability": result}

    def generate(self, state: RequirementState) -> dict:
        previous_candidate = state["candidate_requirement"]
        assessment = state["assessment"]
        feedback = None
        if assessment is not None and assessment.decision is AssessmentDecision.REVISE:
            feedback = assessment.feedback

        outcome = self._deps.generator.generate(state["pull_request"], previous_candidate, feedback)
        return {
            "candidate_requirement": outcome.requirement,
            "generation_refusal": outcome.refusal_reason,
            "generation_attempt": state["generation_attempt"] + 1,
        }

    def retrieve_memory(self, state: RequirementState) -> dict:
        # Il retrieval è deterministico e ripetuto dopo ogni generazione
        # (Decisione 3.5, §8): una revisione può cambiare i requisiti affini.
        #
        # A memoria disattivata la fase non viene nemmeno annunciata: una riga
        # per ogni Pull Request su una funzionalità spenta è solo rumore.
        if not self._config.memory_enabled:
            return {"retrieved_requirements": ()}
        candidate = state["candidate_requirement"]
        assert candidate is not None

        logger.info("%s", console.phase("MEMORIA"))
        logger.info(
            "%s",
            console.note("cerco requisiti gia' validati con cui confrontare il candidato"),
        )
        results = tuple(self._deps.retriever.retrieve(candidate, state["pull_request"]))
        if results:
            logger.info("%s", console.result(f"{len(results)} requisiti recuperati"))
            for item in results:
                logger.info("%s", console.quoted(item.statement))
        else:
            logger.info(
                "%s",
                console.result("nessun requisito precedente da confrontare", console.OK),
            )
        return {"retrieved_requirements": results}

    def assess(self, state: RequirementState) -> dict:
        assessor = self._deps.assessor
        assert assessor is not None
        candidate = state["candidate_requirement"]
        refusal = state["generation_refusal"]
        assert candidate is not None or refusal is not None

        # Lo storico dei tentativi già valutati permette al valutatore di
        # restare coerente con sé stesso e di accorgersi se il ciclo non
        # converge (Decisione 3.5, §19).
        result = assessor.assess(
            state["pull_request"],
            candidate,
            state["retrieved_requirements"],
            state["iteration_history"],
            refusal,
        )
        record = IterationRecord(
            attempt=state["generation_attempt"],
            candidate=candidate,
            assessment=result,
            refusal_reason=refusal,
            # Con il recupero deterministico i requisiti storici stanno nello
            # stato; con quello guidato dall'agente li conosce solo il
            # valutatore, che li riporta nel proprio esito. La traccia nel
            # report deve dire cosa e' stato davvero mostrato al modello, in
            # entrambe le configurazioni.
            retrieved=result.retrieved or tuple(state["retrieved_requirements"]),
        )
        return {
            "assessment": result,
            "iteration_history": state["iteration_history"] + (record,),
        }

    def accept(self, state: RequirementState) -> dict:
        candidate = state["candidate_requirement"]
        assert candidate is not None

        # La scrittura permanente avviene qui, fuori dagli agenti, soltanto
        # dopo ACCEPT (Decisione 3.5, §17).
        self._deps.store.store_accepted(state["pull_request"], candidate)

        update: dict = {
            "final_status": FinalStatus.ACCEPTED,
            "accepted_requirement": candidate,
        }
        if not self._config.assessment_enabled:
            record = IterationRecord(
                attempt=state["generation_attempt"],
                candidate=candidate,
                assessment=None,
            )
            update["iteration_history"] = state["iteration_history"] + (record,)
        return update

    def mark_not_extractable(self, state: RequirementState) -> dict:
        return {"final_status": FinalStatus.NOT_EXTRACTABLE}

    def mark_rejected(self, state: RequirementState) -> dict:
        return {"final_status": FinalStatus.REJECTED}

    def mark_failed_validation(self, state: RequirementState) -> dict:
        return {"final_status": FinalStatus.FAILED_VALIDATION}
