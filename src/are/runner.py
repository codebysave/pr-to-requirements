"""Pipeline Runner: il ciclo esterno sulle Pull Request (Decisione 3.5, §4.4).

Il Runner non è un agente e non prende decisioni semantiche. Riceve i record
prodotti dal Loader, determina l'ordine di elaborazione, invoca il workflow
LangGraph una Pull Request alla volta e raccoglie i risultati.

L'ordine è cronologico quando è disponibile un timestamp affidabile: con la
memoria attiva una PR successiva può consultare requisiti validati da PR
precedenti, mentre una PR più vecchia non deve poter recuperare requisiti
provenienti dal futuro.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Protocol, Sequence

from are import console
from are.agents import RequirementState, create_initial_state
from are.input import PullRequestRecord

logger = logging.getLogger(__name__)


class WorkflowGraph(Protocol):
    """Il grafo compilato invocato dal Runner per una singola Pull Request."""

    def invoke(self, state: RequirementState) -> RequirementState: ...


@dataclass(frozen=True, slots=True)
class RunResult:
    """Esito dell'elaborazione di una singola Pull Request.

    ``error`` è valorizzato soltanto quando l'esecuzione si è interrotta per un
    errore tecnico (chiamata LLM fallita, risposta malformata). Un errore
    tecnico resta distinto dagli stati finali del workflow, che rappresentano
    esiti semantici (Decisione 3.5, §22).
    """

    pull_request: PullRequestRecord
    final_state: RequirementState | None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


class PipelineRunner:
    """Coordina le esecuzioni successive del workflow sulle Pull Request."""

    def __init__(
        self,
        graph: WorkflowGraph,
        *,
        chronological: bool = True,
        stop_on_error: bool = False,
    ) -> None:
        self._graph = graph
        self._chronological = chronological
        self._stop_on_error = stop_on_error

    def run(self, pull_requests: Iterable[PullRequestRecord]) -> list[RunResult]:
        """Elabora tutte le Pull Request, una alla volta e fino allo stato finale."""

        ordered = self._order(pull_requests)
        results: list[RunResult] = []

        for index, pull_request in enumerate(ordered, start=1):
            self._log_header(index, len(ordered), pull_request)
            try:
                final_state = self._graph.invoke(create_initial_state(pull_request))
            except Exception as exc:  # errore tecnico: non interrompe il batch
                logger.error("%s", console.phase("ERRORE TECNICO"))
                logger.error("%s", console.note(f"{type(exc).__name__}: {exc}"))
                logger.info("%s", console.outcome("interrotto da un errore tecnico"))
                results.append(RunResult(pull_request, None, f"{type(exc).__name__}: {exc}"))
                if self._stop_on_error:
                    break
                continue

            self._log_outcome(final_state)
            results.append(RunResult(pull_request, final_state))

        return results

    @staticmethod
    def _log_header(index: int, totale: int, pull_request: PullRequestRecord) -> None:
        logger.info(
            "%s",
            console.pull_request_header(
                index,
                totale,
                pull_request.pr_number,
                pull_request.repository,
                pull_request.title,
            ),
        )

    @staticmethod
    def _log_outcome(state: RequirementState) -> None:
        status = state["final_status"]
        logger.info(
            "%s",
            console.outcome(
                status.value if status is not None else "SCONOSCIUTO",
                state["accepted_requirement"],
            ),
        )

    def _order(self, pull_requests: Iterable[PullRequestRecord]) -> list[PullRequestRecord]:
        records = list(pull_requests)
        if not self._chronological:
            return records
        return sorted(records, key=lambda record: record.timestamp)


def summarize(results: Sequence[RunResult]) -> dict[str, int]:
    """Conta gli esiti per stato finale, più gli eventuali errori tecnici."""

    summary: dict[str, int] = {}
    for result in results:
        if not result.succeeded:
            summary["ERROR"] = summary.get("ERROR", 0) + 1
            continue
        assert result.final_state is not None
        status = result.final_state["final_status"]
        key = status.value if status is not None else "UNKNOWN"
        summary[key] = summary.get(key, 0) + 1
    return summary


def build_run_report(
    results: Sequence[RunResult],
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Costruisce il report serializzabile di un'esecuzione.

    Il report contiene i risultati e i metadati necessari alla riproducibilità
    (Decisione 3.6, §15): configurazione, modelli e versioni dei prompt usati.
    """

    return {
        "run": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        },
        "summary": summarize(results),
        "results": [_serialize_result(result) for result in results],
    }


def save_run_report(report: dict[str, Any], path: str | os.PathLike[str]) -> Path:
    """Scrive il report su file JSON, creando le cartelle mancanti."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def _serialize_result(result: RunResult) -> dict[str, Any]:
    pull_request = result.pull_request
    payload: dict[str, Any] = {
        "pr_id": pull_request.id,
        "repository": pull_request.repository,
        "pr_number": pull_request.pr_number,
        "timestamp": pull_request.timestamp.isoformat(),
        "title": pull_request.title,
    }

    if not result.succeeded:
        payload["error"] = result.error
        return payload

    state = result.final_state
    assert state is not None
    extractability = state["extractability"]
    final_status = state["final_status"]

    payload.update(
        {
            "final_status": final_status.value if final_status is not None else None,
            "extractability": (
                extractability.decision.value if extractability is not None else None
            ),
            "extractability_reason": extractability.reason if extractability is not None else None,
            "accepted_requirement": state["accepted_requirement"],
            "generation_attempts": state["generation_attempt"],
            "iteration_history": [
                {
                    "attempt": record.attempt,
                    "candidate": record.candidate,
                    "refusal_reason": record.refusal_reason,
                    "assessment": _serialize_assessment(record.assessment),
                }
                for record in state["iteration_history"]
            ],
        }
    )
    return payload


def _serialize_assessment(assessment: Any) -> dict[str, Any] | None:
    if assessment is None:
        return None
    feedback = assessment.feedback
    return {
        "decision": assessment.decision.value,
        "issues": list(feedback.issues),
        "unsupported_claims": list(feedback.unsupported_claims),
        "missing_information": list(feedback.missing_information),
        "revision_instructions": list(feedback.revision_instructions),
    }
