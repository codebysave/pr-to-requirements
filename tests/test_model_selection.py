from __future__ import annotations

import argparse

import pytest

from are.__main__ import _apply_model_overrides
from are.llm import AgentLLMSettings, LLMConfig, resolve_model_alias

BASE = LLMConfig(
    generation=AgentLLMSettings(model="claude-haiku-4-5", max_tokens=1024),
    assessment=AgentLLMSettings(model="claude-haiku-4-5", max_tokens=2048),
)


def opzioni(**overrides: object) -> argparse.Namespace:
    valori: dict[str, object] = {
        "model": None,
        "generation_model": None,
        "assessment_model": None,
        "choose_model": False,
    }
    valori.update(overrides)
    return argparse.Namespace(**valori)


@pytest.mark.parametrize(
    ("alias", "atteso"),
    [
        ("haiku", "claude-haiku-4-5"),
        ("sonnet", "claude-sonnet-5"),
        ("opus", "claude-opus-5"),
        ("OPUS", "claude-opus-5"),
        ("  sonnet  ", "claude-sonnet-5"),
    ],
)
def test_resolves_known_aliases(alias: str, atteso: str) -> None:
    assert resolve_model_alias(alias) == atteso


def test_passes_through_full_model_identifiers() -> None:
    assert resolve_model_alias("claude-sonnet-4-6") == "claude-sonnet-4-6"


def test_without_options_the_configuration_is_unchanged() -> None:
    config = _apply_model_overrides(BASE, opzioni())

    assert config.generation.model == "claude-haiku-4-5"
    assert config.assessment.model == "claude-haiku-4-5"


def test_model_option_applies_to_both_agents() -> None:
    config = _apply_model_overrides(BASE, opzioni(model="sonnet"))

    assert config.generation.model == "claude-sonnet-5"
    assert config.assessment.model == "claude-sonnet-5"


def test_per_agent_options_allow_mixed_configurations() -> None:
    config = _apply_model_overrides(
        BASE, opzioni(generation_model="haiku", assessment_model="opus")
    )

    assert config.generation.model == "claude-haiku-4-5"
    assert config.assessment.model == "claude-opus-5"


def test_per_agent_option_wins_over_the_shared_one() -> None:
    config = _apply_model_overrides(BASE, opzioni(model="sonnet", assessment_model="opus"))

    assert config.generation.model == "claude-sonnet-5"
    assert config.assessment.model == "claude-opus-5"


def test_other_settings_are_preserved() -> None:
    config = _apply_model_overrides(BASE, opzioni(model="opus"))

    assert config.generation.max_tokens == 1024
    assert config.assessment.max_tokens == 2048


def test_interactive_menu_selects_an_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda *_: "2")

    config = _apply_model_overrides(BASE, opzioni(choose_model=True))

    assert config.generation.model == "claude-sonnet-5"


def test_interactive_menu_can_keep_the_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda *_: "4")

    config = _apply_model_overrides(BASE, opzioni(choose_model=True))

    assert config.generation.model == "claude-haiku-4-5"


def test_interactive_menu_rejects_invalid_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    risposte = iter(["", "nove", "0", "1"])
    monkeypatch.setattr("builtins.input", lambda *_: next(risposte))

    config = _apply_model_overrides(BASE, opzioni(choose_model=True))

    assert config.generation.model == "claude-haiku-4-5"
