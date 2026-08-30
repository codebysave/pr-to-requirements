from __future__ import annotations

import pytest

from are.agents import (
    AssessmentDecision,
    AssessmentFeedback,
    AssessmentResult,
    IterationRecord,
    RetrievedRequirement,
)
from are.agents.llm_agents import (
    AgentResponseError,
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


def test_parses_json_followed_by_the_model_thinking_aloud() -> None:
    """Il caso reale che ha fatto perdere una Pull Request il 30 agosto.

    Il generatore ha prodotto il JSON dentro un blocco markdown e ha poi
    continuato a ragionare. La risposta era completa e valida: perderla per
    quello che veniva dopo era uno spreco.
    """

    text = (
        '```json\n{"requirement": "The system shall export reports."}\n```\n\n'
        "Wait, let me reconsider. The reviewer might object that {this} is too broad."
    )

    assert parse_json_object(text, "test") == {"requirement": "The system shall export reports."}


def test_parses_json_when_prose_before_it_contains_a_brace() -> None:
    text = 'The set {a, b} is irrelevant. Here is the answer: {"decision": "ACCEPT"}'

    assert parse_json_object(text, "test") == {"decision": "ACCEPT"}


def test_still_rejects_a_genuinely_malformed_object() -> None:
    with pytest.raises(AgentResponseError, match="JSON non valido"):
        parse_json_object('{"decision": "ACCEPT",}', "test")


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


# --- Generation Agent -------------------------------------------------------


def test_generator_returns_requirement_text() -> None:
    client = FakeLLMClient(
        '{"requirement": "The system shall allow users to export reports in PDF format."}'
    )

    outcome = LLMRequirementGenerator(client).generate(PR, None, None)

    assert outcome.requirement == "The system shall allow users to export reports in PDF format."
    assert not outcome.refused


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
    historical = RetrievedRequirement("7", "The system shall export data.", source_pr_number=4242)

    LLMRequirementAssessor(client).assess(PR, "The system shall export reports.", (historical,))

    _, user_message = client.requests[0]
    assert "The system shall export data." in user_message
    # Il numero della Pull Request permette al valutatore di citare il caso
    # invece di segnalare una duplicazione generica.
    assert "4242" in user_message


def test_assessor_omits_memory_section_when_no_requirements_retrieved() -> None:
    client = FakeLLMClient('{"decision": "ACCEPT"}')

    LLMRequirementAssessor(client).assess(PR, "candidate", ())

    _, user_message = client.requests[0]
    assert "PREVIOUSLY VALIDATED REQUIREMENTS" not in user_message


# --- storico dei tentativi precedenti --------------------------------------


def revise_result(instruction: str) -> AssessmentResult:
    return AssessmentResult(
        AssessmentDecision.REVISE,
        AssessmentFeedback(
            issues=("Names a library.",),
            unsupported_claims=("SomeLibrary",),
            revision_instructions=(instruction,),
        ),
    )


def test_assessor_omits_the_history_section_on_the_first_attempt() -> None:
    client = FakeLLMClient('{"decision": "ACCEPT"}')

    LLMRequirementAssessor(client).assess(PR, "The system shall export reports.", ())

    _, user_message = client.requests[0]
    assert "PREVIOUS ATTEMPTS" not in user_message


def test_assessor_receives_previous_candidates_and_its_own_verdicts() -> None:
    client = FakeLLMClient('{"decision": "ACCEPT"}')
    history = (
        IterationRecord(1, "The system shall use SomeLibrary.", revise_result("Remove it.")),
    )

    LLMRequirementAssessor(client).assess(PR, "The system shall parse safely.", (), history)

    _, user_message = client.requests[0]
    assert "PREVIOUS ATTEMPTS" in user_message
    assert "Attempt 1" in user_message
    assert "The system shall use SomeLibrary." in user_message
    assert "REVISE" in user_message
    assert "Remove it." in user_message
    # Lo storico precede il candidato corrente nel messaggio.
    assert user_message.index("PREVIOUS ATTEMPTS") < user_message.index("CANDIDATE REQUIREMENT")


def test_assessor_reports_every_previous_attempt_in_order() -> None:
    client = FakeLLMClient('{"decision": "REJECT"}')
    history = (
        IterationRecord(1, "First try.", revise_result("Fix A.")),
        IterationRecord(2, "Second try.", revise_result("Fix B.")),
    )

    LLMRequirementAssessor(client).assess(PR, "Third try.", (), history)

    _, user_message = client.requests[0]
    assert user_message.index("Attempt 1") < user_message.index("Attempt 2")
    assert "Fix A." in user_message and "Fix B." in user_message
