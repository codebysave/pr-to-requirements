from __future__ import annotations

from typing import Sequence

import pytest

from are.agents import (
    AssessmentDecision,
    AssessmentFeedback,
    AssessmentResult,
    Extractability,
    ExtractabilityResult,
    FinalStatus,
    RetrievedRequirement,
    WorkflowConfig,
    WorkflowDependencies,
    build_workflow,
    create_initial_state,
)
from are.input import PullRequestRecord

PR = PullRequestRecord.from_mapping(
    {
        "id": "owner-repo-pr-1",
        "repository": "owner/repo",
        "pr_number": 1,
        "timestamp": "2026-08-25T10:00:00Z",
        "title": "Add export",
        "body": "Users can now export reports.",
    }
)

EXTRACTABLE = ExtractabilityResult(Extractability.EXTRACTABLE, "functional behavior")
NOT_EXTRACTABLE = ExtractabilityResult(Extractability.NOT_EXTRACTABLE, "refactoring only")

ACCEPT = AssessmentResult(AssessmentDecision.ACCEPT)
REJECT = AssessmentResult(AssessmentDecision.REJECT)
REVISE = AssessmentResult(
    AssessmentDecision.REVISE,
    AssessmentFeedback(
        issues=("Unsupported delivery channel.",),
        unsupported_claims=("The notification is sent by email",),
        revision_instructions=("Remove the unsupported reference to email.",),
    ),
)


class ScriptedChecker:
    def __init__(self, result: ExtractabilityResult):
        self.result = result
        self.calls = 0

    def check(self, pull_request: PullRequestRecord) -> ExtractabilityResult:
        self.calls += 1
        return self.result


class ScriptedGenerator:
    """Genera candidati numerati e registra gli argomenti ricevuti."""

    def __init__(self):
        self.calls: list[tuple[str | None, AssessmentFeedback | None]] = []

    def generate(self, pull_request, previous_candidate, feedback):
        self.calls.append((previous_candidate, feedback))
        return f"The system shall allow users to export reports. (v{len(self.calls)})"


class ScriptedAssessor:
    """Restituisce decisioni in sequenza e registra gli argomenti ricevuti."""

    def __init__(self, decisions: Sequence[AssessmentResult]):
        self.decisions = list(decisions)
        self.calls: list[tuple[str, tuple[RetrievedRequirement, ...]]] = []

    def assess(self, pull_request, candidate, retrieved_requirements):
        self.calls.append((candidate, tuple(retrieved_requirements)))
        return self.decisions[len(self.calls) - 1]


class RecordingRetriever:
    def __init__(self, results: Sequence[RetrievedRequirement] = ()):
        self.results = tuple(results)
        self.calls: list[str] = []

    def retrieve(self, candidate, pull_request):
        self.calls.append(candidate)
        return self.results


class RecordingStore:
    def __init__(self):
        self.stored: list[tuple[str, str]] = []

    def store_accepted(self, pull_request, statement):
        self.stored.append((pull_request.id, statement))


def run_workflow(
    *,
    checker=None,
    generator=None,
    assessor=None,
    retriever=None,
    store=None,
    config=None,
):
    dependencies = WorkflowDependencies(
        extractability_checker=checker or ScriptedChecker(EXTRACTABLE),
        generator=generator or ScriptedGenerator(),
        assessor=assessor,
        retriever=retriever or RecordingRetriever(),
        store=store or RecordingStore(),
    )
    graph = build_workflow(dependencies, config or WorkflowConfig())
    return graph.invoke(create_initial_state(PR))


def test_not_extractable_terminates_without_generation() -> None:
    generator = ScriptedGenerator()

    final = run_workflow(
        checker=ScriptedChecker(NOT_EXTRACTABLE),
        generator=generator,
        assessor=ScriptedAssessor([]),
    )

    assert final["final_status"] is FinalStatus.NOT_EXTRACTABLE
    assert generator.calls == []
    assert final["candidate_requirement"] is None
    assert final["iteration_history"] == ()


def test_accept_on_first_attempt_persists_and_terminates() -> None:
    store = RecordingStore()

    final = run_workflow(assessor=ScriptedAssessor([ACCEPT]), store=store)

    assert final["final_status"] is FinalStatus.ACCEPTED
    assert final["accepted_requirement"] == final["candidate_requirement"]
    assert final["generation_attempt"] == 1
    assert store.stored == [(PR.id, final["accepted_requirement"])]
    assert len(final["iteration_history"]) == 1
    assert final["iteration_history"][0].assessment is ACCEPT


def test_revise_feeds_previous_candidate_and_feedback_to_generator() -> None:
    generator = ScriptedGenerator()

    final = run_workflow(generator=generator, assessor=ScriptedAssessor([REVISE, ACCEPT]))

    assert final["final_status"] is FinalStatus.ACCEPTED
    assert final["generation_attempt"] == 2

    first_call, second_call = generator.calls
    assert first_call == (None, None)
    previous_candidate, feedback = second_call
    assert previous_candidate is not None and "(v1)" in previous_candidate
    assert feedback is REVISE.feedback

    history = final["iteration_history"]
    assert [record.attempt for record in history] == [1, 2]
    assert history[0].assessment is REVISE
    assert history[1].assessment is ACCEPT


def test_revise_beyond_limit_fails_validation_without_persisting() -> None:
    store = RecordingStore()

    final = run_workflow(
        assessor=ScriptedAssessor([REVISE, REVISE, REVISE]),
        store=store,
    )

    assert final["final_status"] is FinalStatus.FAILED_VALIDATION
    assert final["generation_attempt"] == 3
    assert store.stored == []
    assert final["accepted_requirement"] is None
    assert len(final["iteration_history"]) == 3


def test_reject_terminates_without_retry_or_persistence() -> None:
    generator = ScriptedGenerator()
    store = RecordingStore()

    final = run_workflow(generator=generator, assessor=ScriptedAssessor([REJECT]), store=store)

    assert final["final_status"] is FinalStatus.REJECTED
    assert len(generator.calls) == 1
    assert store.stored == []


def test_max_attempts_is_configurable() -> None:
    final = run_workflow(
        assessor=ScriptedAssessor([REVISE]),
        config=WorkflowConfig(max_generation_attempts=1),
    )

    assert final["final_status"] is FinalStatus.FAILED_VALIDATION
    assert final["generation_attempt"] == 1


def test_assessment_disabled_accepts_first_candidate_directly() -> None:
    store = RecordingStore()

    final = run_workflow(
        assessor=None,
        store=store,
        config=WorkflowConfig(assessment_enabled=False),
    )

    assert final["final_status"] is FinalStatus.ACCEPTED
    assert final["generation_attempt"] == 1
    assert len(store.stored) == 1
    assert len(final["iteration_history"]) == 1
    assert final["iteration_history"][0].assessment is None


def test_memory_disabled_never_calls_retriever() -> None:
    retriever = RecordingRetriever()

    final = run_workflow(
        assessor=ScriptedAssessor([ACCEPT]),
        retriever=retriever,
        config=WorkflowConfig(memory_enabled=False),
    )

    assert final["final_status"] is FinalStatus.ACCEPTED
    assert retriever.calls == []
    assert final["retrieved_requirements"] == ()


def test_memory_enabled_retrieves_after_every_generation() -> None:
    historical = RetrievedRequirement("FR-0001", "The system shall export reports.", 0.91)
    retriever = RecordingRetriever([historical])
    assessor = ScriptedAssessor([REVISE, ACCEPT])

    final = run_workflow(
        assessor=assessor,
        retriever=retriever,
        config=WorkflowConfig(memory_enabled=True),
    )

    assert final["final_status"] is FinalStatus.ACCEPTED
    # Un retrieval per ciascuna generazione (Decisione 3.5, §8).
    assert len(retriever.calls) == 2
    assert "(v1)" in retriever.calls[0] and "(v2)" in retriever.calls[1]
    # I requisiti recuperati arrivano all'assessor.
    assert assessor.calls[0][1] == (historical,)
    assert assessor.calls[1][1] == (historical,)


def test_build_workflow_requires_assessor_when_assessment_enabled() -> None:
    dependencies = WorkflowDependencies(
        extractability_checker=ScriptedChecker(EXTRACTABLE),
        generator=ScriptedGenerator(),
        assessor=None,
    )

    with pytest.raises(ValueError, match="assessor"):
        build_workflow(dependencies, WorkflowConfig(assessment_enabled=True))
