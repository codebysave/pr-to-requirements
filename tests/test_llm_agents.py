from __future__ import annotations

import pytest

from are.agents import (
    AssessmentDecision,
    AssessmentFeedback,
    Extractability,
    RetrievedRequirement,
)
from are.agents.llm_agents import (
    AgentResponseError,
    LLMExtractabilityChecker,
    LLMRequirementAssessor,
    LLMRequirementGenerator,
    parse_json_object,
)
from are.input import PullRequestRecord
from are.llm import LLMResponse

PR = PullRequestRecord.from_mapping(
    {
        "id": "owner-repo-pr-1",
        "repository": "owner/repo",
        "pr_number": 1,
        "timestamp": "2026-08-25T10:00:00Z",
        "title": "Add PDF export",
        "body": "Users can now export reports as PDF.",
    }
)


class FakeLLMClient:
    """Client LLM finto: restituisce testi scriptati e registra le richieste."""

    def __init__(self, *responses: str):
        self._responses = list(responses)
        self.requests: list[tuple[str, str]] = []

    def complete(self, *, system: str, user_message: str) -> LLMResponse:
        self.requests.append((system, user_message))
        text = self._responses[min(len(self.requests) - 1, len(self._responses) - 1)]
        return LLMResponse(
            text=text,
            model="fake-model",
            stop_reason="end_turn",
            input_tokens=10,
            output_tokens=5,
        )


# --- parsing delle risposte -------------------------------------------------


def test_parses_plain_json_object() -> None:
    assert parse_json_object('{"a": 1}', "test") == {"a": 1}


def test_parses_json_inside_markdown_fence() -> None:
    text = '```json\n{"decision": "ACCEPT"}\n```'

    assert parse_json_object(text, "test") == {"decision": "ACCEPT"}


def test_parses_json_surrounded_by_prose() -> None:
    text = 'Here is the result:\n{"decision": "REVISE"}\nLet me know.'

    assert parse_json_object(text, "test") == {"decision": "REVISE"}


def test_rejects_response_without_json() -> None:
    with pytest.raises(AgentResponseError, match="nessun oggetto JSON"):
        parse_json_object("The requirement looks fine to me.", "test")


def test_rejects_json_array_at_top_level() -> None:
    with pytest.raises(AgentResponseError, match="non è un oggetto JSON"):
        parse_json_object("[1, 2, 3]", "test")


def test_error_message_truncates_long_responses() -> None:
    with pytest.raises(AgentResponseError) as excinfo:
        parse_json_object("x" * 500, "test")

    assert "..." in str(excinfo.value)
    assert excinfo.value.raw_response == "x" * 500


# --- gate di estraibilità ---------------------------------------------------


def test_extractability_checker_reads_decision_and_reason() -> None:
    client = FakeLLMClient('{"extractability": "EXTRACTABLE", "reason": "new export capability"}')
    checker = LLMExtractabilityChecker(client)

    result = checker.check(PR)

    assert result.decision is Extractability.EXTRACTABLE
    assert result.reason == "new export capability"
    system, user_message = client.requests[0]
    assert "NOT_EXTRACTABLE" in system
    assert PR.title in user_message
    assert PR.body in user_message


def test_extractability_checker_accepts_not_extractable() -> None:
    client = FakeLLMClient('{"extractability": "not_extractable", "reason": "typo fix"}')

    result = LLMExtractabilityChecker(client).check(PR)

    assert result.decision is Extractability.NOT_EXTRACTABLE


def test_extractability_checker_rejects_unknown_verdict() -> None:
    client = FakeLLMClient('{"extractability": "MAYBE"}')

    with pytest.raises(AgentResponseError, match="MAYBE"):
        LLMExtractabilityChecker(client).check(PR)


def test_extractability_checker_tolerates_missing_reason() -> None:
    client = FakeLLMClient('{"extractability": "EXTRACTABLE"}')

    assert LLMExtractabilityChecker(client).check(PR).reason == ""


# --- Generation Agent -------------------------------------------------------


def test_generator_returns_requirement_text() -> None:
    client = FakeLLMClient(
        '{"requirement": "The system shall allow users to export reports in PDF format."}'
    )

    requirement = LLMRequirementGenerator(client).generate(PR, None, None)

    assert requirement == "The system shall allow users to export reports in PDF format."


def test_generator_first_attempt_sends_only_the_evidence() -> None:
    client = FakeLLMClient('{"requirement": "The system shall export reports."}')

    LLMRequirementGenerator(client).generate(PR, None, None)

    _, user_message = client.requests[0]
    assert PR.title in user_message
    assert "PREVIOUS REQUIREMENT" not in user_message
    assert "REVIEWER FEEDBACK" not in user_message


def test_generator_revision_receives_previous_candidate_and_feedback() -> None:
    client = FakeLLMClient('{"requirement": "The system shall notify the user."}')
    feedback = AssessmentFeedback(
        unsupported_claims=("email channel",),
        revision_instructions=("Remove the unsupported reference to email.",),
    )

    LLMRequirementGenerator(client).generate(PR, "The system shall send an email.", feedback)

    _, user_message = client.requests[0]
    assert "The system shall send an email." in user_message
    assert "email channel" in user_message
    assert "Remove the unsupported reference to email." in user_message


def test_generator_rejects_response_without_requirement_field() -> None:
    client = FakeLLMClient('{"text": "The system shall export reports."}')

    with pytest.raises(AgentResponseError, match="requirement"):
        LLMRequirementGenerator(client).generate(PR, None, None)


def test_generator_rejects_empty_requirement() -> None:
    client = FakeLLMClient('{"requirement": "   "}')

    with pytest.raises(AgentResponseError, match="requirement"):
        LLMRequirementGenerator(client).generate(PR, None, None)


# --- Assessment Agent -------------------------------------------------------


def test_assessor_reads_decision_and_structured_feedback() -> None:
    client = FakeLLMClient(
        """{
            "decision": "REVISE",
            "issues": ["Adds a delivery channel"],
            "unsupported_claims": ["email"],
            "missing_information": [],
            "revision_instructions": ["Remove the email reference."]
        }"""
    )

    result = LLMRequirementAssessor(client).assess(PR, "The system shall send an email.", ())

    assert result.decision is AssessmentDecision.REVISE
    assert result.feedback.issues == ("Adds a delivery channel",)
    assert result.feedback.unsupported_claims == ("email",)
    assert result.feedback.missing_information == ()
    assert result.feedback.revision_instructions == ("Remove the email reference.",)


def test_assessor_accepts_response_with_only_the_decision() -> None:
    client = FakeLLMClient('{"decision": "ACCEPT"}')

    result = LLMRequirementAssessor(client).assess(PR, "The system shall export reports.", ())

    assert result.decision is AssessmentDecision.ACCEPT
    assert result.feedback == AssessmentFeedback()


def test_assessor_rejects_unknown_decision() -> None:
    client = FakeLLMClient('{"decision": "MAYBE"}')

    with pytest.raises(AgentResponseError, match="MAYBE"):
        LLMRequirementAssessor(client).assess(PR, "candidate", ())


def test_assessor_rejects_malformed_feedback_lists() -> None:
    client = FakeLLMClient('{"decision": "REVISE", "issues": "not a list"}')

    with pytest.raises(AgentResponseError, match="issues"):
        LLMRequirementAssessor(client).assess(PR, "candidate", ())


def test_assessor_includes_retrieved_requirements_in_the_message() -> None:
    client = FakeLLMClient('{"decision": "ACCEPT"}')
    historical = RetrievedRequirement("FR-0007", "The system shall export data.", 0.87)

    LLMRequirementAssessor(client).assess(PR, "The system shall export reports.", (historical,))

    _, user_message = client.requests[0]
    assert "FR-0007" in user_message
    assert "The system shall export data." in user_message
    assert "0.87" in user_message


def test_assessor_omits_memory_section_when_no_requirements_retrieved() -> None:
    client = FakeLLMClient('{"decision": "ACCEPT"}')

    LLMRequirementAssessor(client).assess(PR, "candidate", ())

    _, user_message = client.requests[0]
    assert "PREVIOUSLY VALIDATED REQUIREMENTS" not in user_message
