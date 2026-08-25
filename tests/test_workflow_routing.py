from __future__ import annotations

import pytest

from are.agents import (
    AssessmentDecision,
    AssessmentResult,
    Extractability,
    ExtractabilityResult,
    WorkflowConfig,
    create_initial_state,
)
from are.agents.routing import (
    NODE_ACCEPT,
    NODE_ASSESS,
    NODE_GENERATE,
    NODE_MARK_FAILED_VALIDATION,
    NODE_MARK_NOT_EXTRACTABLE,
    NODE_MARK_REJECTED,
    route_after_assessment,
    route_after_extractability,
    route_after_retrieval,
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


def state_with(**overrides):
    state = dict(create_initial_state(PR))
    state.update(overrides)
    return state


def test_extractable_routes_to_generation() -> None:
    state = state_with(extractability=ExtractabilityResult(Extractability.EXTRACTABLE))

    assert route_after_extractability(state) == NODE_GENERATE


def test_not_extractable_routes_to_termination() -> None:
    state = state_with(
        extractability=ExtractabilityResult(Extractability.NOT_EXTRACTABLE, "no behavior")
    )

    assert route_after_extractability(state) == NODE_MARK_NOT_EXTRACTABLE


def test_extractability_routing_requires_prior_check() -> None:
    with pytest.raises(ValueError):
        route_after_extractability(state_with())


def test_retrieval_routes_to_assessment_when_enabled() -> None:
    config = WorkflowConfig(assessment_enabled=True)

    assert route_after_retrieval(state_with(), config) == NODE_ASSESS


def test_retrieval_routes_to_accept_when_assessment_disabled() -> None:
    config = WorkflowConfig(assessment_enabled=False)

    assert route_after_retrieval(state_with(), config) == NODE_ACCEPT


def test_accept_routes_to_accept_node() -> None:
    state = state_with(assessment=AssessmentResult(AssessmentDecision.ACCEPT))

    assert route_after_assessment(state, WorkflowConfig()) == NODE_ACCEPT


def test_reject_routes_to_rejected() -> None:
    state = state_with(assessment=AssessmentResult(AssessmentDecision.REJECT))

    assert route_after_assessment(state, WorkflowConfig()) == NODE_MARK_REJECTED


def test_revise_within_limit_routes_back_to_generation() -> None:
    state = state_with(assessment=AssessmentResult(AssessmentDecision.REVISE), generation_attempt=2)

    assert route_after_assessment(state, WorkflowConfig()) == NODE_GENERATE


def test_revise_at_limit_routes_to_failed_validation() -> None:
    state = state_with(assessment=AssessmentResult(AssessmentDecision.REVISE), generation_attempt=3)

    assert route_after_assessment(state, WorkflowConfig()) == NODE_MARK_FAILED_VALIDATION


def test_revise_limit_is_configurable() -> None:
    state = state_with(assessment=AssessmentResult(AssessmentDecision.REVISE), generation_attempt=1)

    config = WorkflowConfig(max_generation_attempts=1)

    assert route_after_assessment(state, config) == NODE_MARK_FAILED_VALIDATION


def test_assessment_routing_requires_prior_assessment() -> None:
    with pytest.raises(ValueError):
        route_after_assessment(state_with(), WorkflowConfig())
