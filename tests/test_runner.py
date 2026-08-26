from __future__ import annotations

import json
from pathlib import Path

from are.agents import (
    AssessmentDecision,
    AssessmentFeedback,
    AssessmentResult,
    Extractability,
    ExtractabilityResult,
    FinalStatus,
    IterationRecord,
    RequirementState,
    create_initial_state,
)
from are.input import PullRequestRecord
from are.runner import (
    PipelineRunner,
    build_run_report,
    save_run_report,
    summarize,
)


def make_pr(pr_number: int, timestamp: str) -> PullRequestRecord:
    return PullRequestRecord.from_mapping(
        {
            "id": f"owner-repo-pr-{pr_number}",
            "repository": "owner/repo",
            "pr_number": pr_number,
            "timestamp": timestamp,
            "title": f"Change {pr_number}",
            "body": "Body",
        }
    )


PR_OLD = make_pr(1, "2026-01-01T10:00:00Z")
PR_MIDDLE = make_pr(2, "2026-03-01T10:00:00Z")
PR_RECENT = make_pr(3, "2026-06-01T10:00:00Z")


class FakeGraph:
    """Grafo finto: registra le PR ricevute e restituisce uno stato finale."""

    def __init__(self, status: FinalStatus = FinalStatus.ACCEPTED, failing_ids: set | None = None):
        self.status = status
        self.failing_ids = failing_ids or set()
        self.seen: list[str] = []

    def invoke(self, state: RequirementState) -> RequirementState:
        pull_request = state["pull_request"]
        self.seen.append(pull_request.id)
        if pull_request.id in self.failing_ids:
            raise RuntimeError("chiamata LLM fallita")

        final = dict(state)
        final["final_status"] = self.status
        final["extractability"] = ExtractabilityResult(Extractability.EXTRACTABLE, "behaviour")
        final["generation_attempt"] = 1
        candidate = f"The system shall handle change {pull_request.pr_number}."
        final["candidate_requirement"] = candidate
        if self.status is FinalStatus.ACCEPTED:
            final["accepted_requirement"] = candidate
        final["iteration_history"] = (
            IterationRecord(
                attempt=1,
                candidate=candidate,
                assessment=AssessmentResult(
                    AssessmentDecision.ACCEPT,
                    AssessmentFeedback(issues=("none",)),
                ),
            ),
        )
        return final  # type: ignore[return-value]


def test_processes_pull_requests_in_chronological_order() -> None:
    graph = FakeGraph()

    results = PipelineRunner(graph).run([PR_RECENT, PR_OLD, PR_MIDDLE])

    assert graph.seen == [PR_OLD.id, PR_MIDDLE.id, PR_RECENT.id]
    assert [result.pull_request.id for result in results] == graph.seen


def test_preserves_input_order_when_chronological_is_disabled() -> None:
    graph = FakeGraph()

    PipelineRunner(graph, chronological=False).run([PR_RECENT, PR_OLD])

    assert graph.seen == [PR_RECENT.id, PR_OLD.id]


def test_processes_every_pull_request_of_the_batch() -> None:
    graph = FakeGraph()

    results = PipelineRunner(graph).run([PR_OLD, PR_MIDDLE, PR_RECENT])

    assert len(results) == 3
    assert all(result.succeeded for result in results)
    assert all(result.final_state["final_status"] is FinalStatus.ACCEPTED for result in results)


def test_technical_error_does_not_stop_the_batch() -> None:
    graph = FakeGraph(failing_ids={PR_MIDDLE.id})

    results = PipelineRunner(graph).run([PR_OLD, PR_MIDDLE, PR_RECENT])

    assert [result.succeeded for result in results] == [True, False, True]
    failed = results[1]
    assert failed.final_state is None
    assert "chiamata LLM fallita" in failed.error
    # Le PR successive vengono comunque elaborate.
    assert graph.seen == [PR_OLD.id, PR_MIDDLE.id, PR_RECENT.id]


def test_stop_on_error_interrupts_the_batch() -> None:
    graph = FakeGraph(failing_ids={PR_OLD.id})

    results = PipelineRunner(graph, stop_on_error=True).run([PR_OLD, PR_MIDDLE])

    assert len(results) == 1
    assert not results[0].succeeded
    assert graph.seen == [PR_OLD.id]


def test_summarize_counts_final_states_and_errors() -> None:
    graph = FakeGraph(failing_ids={PR_MIDDLE.id})

    results = PipelineRunner(graph).run([PR_OLD, PR_MIDDLE, PR_RECENT])

    assert summarize(results) == {"ACCEPTED": 2, "ERROR": 1}


def test_report_contains_results_metadata_and_summary() -> None:
    graph = FakeGraph()
    results = PipelineRunner(graph).run([PR_OLD, PR_MIDDLE])

    report = build_run_report(results, metadata={"prompt_version": "v1"})

    assert report["summary"] == {"ACCEPTED": 2}
    assert report["run"]["prompt_version"] == "v1"
    assert report["run"]["generated_at"]

    first = report["results"][0]
    assert first["pr_id"] == PR_OLD.id
    assert first["final_status"] == "ACCEPTED"
    assert first["extractability"] == "EXTRACTABLE"
    assert first["accepted_requirement"].startswith("The system shall")
    assert first["iteration_history"][0]["assessment"]["decision"] == "ACCEPT"


def test_report_records_failed_pull_requests() -> None:
    graph = FakeGraph(failing_ids={PR_OLD.id})
    results = PipelineRunner(graph).run([PR_OLD])

    entry = build_run_report(results)["results"][0]

    assert "error" in entry
    assert "final_status" not in entry


def test_saves_report_creating_missing_directories(tmp_path: Path) -> None:
    graph = FakeGraph()
    results = PipelineRunner(graph).run([PR_OLD])
    report = build_run_report(results)

    output = save_run_report(report, tmp_path / "runs" / "nested" / "run.json")

    assert output.exists()
    reloaded = json.loads(output.read_text(encoding="utf-8"))
    assert reloaded["summary"] == {"ACCEPTED": 1}


def test_initial_state_is_built_for_each_pull_request() -> None:
    state = create_initial_state(PR_OLD)

    assert state["pull_request"] is PR_OLD
    assert state["generation_attempt"] == 0
    assert state["final_status"] is None
