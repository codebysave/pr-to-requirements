from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2
import pytest

from are.llm import (
    API_KEY_ENV_VAR,
    AgentLLMSettings,
    AnthropicLLMClient,
    LLMCallError,
    MissingApiKeyError,
)

SETTINGS = AgentLLMSettings(model="claude-haiku-4-5", temperature=0.0, max_tokens=1024)


def make_sdk_response(**overrides: Any) -> SimpleNamespace:
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="The system shall notify the user.")],
        model="claude-haiku-4-5",
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=120, output_tokens=15),
    )
    for key, value in overrides.items():
        setattr(response, key, value)
    return response


class FakeSdkClient:
    """Doppio dell'SDK Anthropic: registra la richiesta e restituisce una risposta fissa."""

    def __init__(self, response: SimpleNamespace | None = None, error: Exception | None = None):
        self.requests: list[dict[str, Any]] = []
        self._response = response or make_sdk_response()
        self._error = error
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs: Any) -> SimpleNamespace:
        self.requests.append(kwargs)
        if self._error is not None:
            raise self._error
        return self._response


def test_complete_sends_configured_parameters() -> None:
    fake = FakeSdkClient()
    client = AnthropicLLMClient(SETTINGS, sdk_client=fake)  # type: ignore[arg-type]

    response = client.complete(system="You are an agent.", user_message="PR title and body")

    request = fake.requests[0]
    assert request["model"] == "claude-haiku-4-5"
    assert request["temperature"] == 0.0
    assert request["max_tokens"] == 1024
    assert request["system"] == "You are an agent."
    assert request["messages"] == [{"role": "user", "content": "PR title and body"}]
    assert "top_p" not in request
    assert response.text == "The system shall notify the user."
    assert response.stop_reason == "end_turn"
    assert response.input_tokens == 120
    assert response.output_tokens == 15


def test_complete_sends_top_p_only_when_configured() -> None:
    fake = FakeSdkClient()
    settings = AgentLLMSettings(model="m", temperature=0.5, max_tokens=10, top_p=0.9)
    client = AnthropicLLMClient(settings, sdk_client=fake)  # type: ignore[arg-type]

    client.complete(system="s", user_message="u")

    assert fake.requests[0]["top_p"] == 0.9


def test_complete_concatenates_only_text_blocks() -> None:
    response = make_sdk_response(
        content=[
            SimpleNamespace(type="thinking", thinking="internal"),
            SimpleNamespace(type="text", text="First. "),
            SimpleNamespace(type="text", text="Second."),
        ]
    )
    client = AnthropicLLMClient(SETTINGS, sdk_client=FakeSdkClient(response))  # type: ignore[arg-type]

    assert client.complete(system="s", user_message="u").text == "First. Second."


def test_wraps_sdk_errors_in_llm_call_error() -> None:
    sdk_error = anthropic.APIConnectionError(
        request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    )
    client = AnthropicLLMClient(SETTINGS, sdk_client=FakeSdkClient(error=sdk_error))  # type: ignore[arg-type]

    with pytest.raises(LLMCallError) as excinfo:
        client.complete(system="s", user_message="u")

    assert excinfo.value.model == "claude-haiku-4-5"
    assert excinfo.value.__cause__ is sdk_error


def test_missing_api_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)

    with pytest.raises(MissingApiKeyError, match=API_KEY_ENV_VAR):
        AnthropicLLMClient(SETTINGS)


def test_api_key_from_environment_builds_real_sdk_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(API_KEY_ENV_VAR, "test-key-not-real")

    client = AnthropicLLMClient(SETTINGS)

    assert client.settings is SETTINGS
