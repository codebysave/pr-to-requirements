from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from are.agents.prompts import (
    ASSESSMENT_AGENT,
    EXTRACTABILITY_AGENT,
    GENERATION_AGENT,
    PromptNotFoundError,
    load_prompt,
)


def test_repository_prompts_are_available_for_every_agent() -> None:
    for agent in (EXTRACTABILITY_AGENT, GENERATION_AGENT, ASSESSMENT_AGENT):
        prompt = load_prompt(agent)

        assert prompt.strip()


def test_generation_prompt_states_the_project_conventions() -> None:
    prompt = load_prompt(GENERATION_AGENT)

    # I vincoli della Decisione 3.1 devono essere presenti nel prompt.
    assert "shall" in prompt
    assert "When <trigger>" in prompt
    assert "While <state>" in prompt
    assert "If <undesired condition>" in prompt


def test_assessment_prompt_lists_the_three_decisions() -> None:
    prompt = load_prompt(ASSESSMENT_AGENT)

    for decision in ("ACCEPT", "REVISE", "REJECT"):
        assert decision in prompt


def test_every_prompt_requires_a_single_json_object() -> None:
    for agent in (EXTRACTABILITY_AGENT, GENERATION_AGENT, ASSESSMENT_AGENT):
        prompt = load_prompt(agent)

        assert "single JSON object" in prompt, agent
        assert "no markdown code fences" in prompt, agent


def test_every_prompt_contains_at_least_one_valid_json_example() -> None:
    """Gli esempi guidano i modelli piccoli: devono essere JSON realmente validi."""

    for agent in (EXTRACTABILITY_AGENT, GENERATION_AGENT, ASSESSMENT_AGENT):
        prompt = load_prompt(agent)
        # Le righe che iniziano e finiscono con graffa e non contengono il
        # carattere di alternativa dello schema sono esempi concreti.
        esempi = [
            riga for riga in re.findall(r"^\{.*\}$", prompt, re.MULTILINE) if '" | "' not in riga
        ]

        assert esempi, f"nessun esempio in {agent}"
        for esempio in esempi:
            json.loads(esempio)  # solleva se malformato


def test_loads_prompt_from_custom_directory(tmp_path: Path) -> None:
    agent_dir = tmp_path / "generation"
    agent_dir.mkdir()
    (agent_dir / "v2.md").write_text("Prompt sperimentale", encoding="utf-8")

    assert load_prompt("generation", "v2", tmp_path) == "Prompt sperimentale"


def test_rejects_missing_prompt(tmp_path: Path) -> None:
    with pytest.raises(PromptNotFoundError, match="file non trovato"):
        load_prompt("generation", "v99", tmp_path)


def test_rejects_empty_prompt(tmp_path: Path) -> None:
    agent_dir = tmp_path / "generation"
    agent_dir.mkdir()
    (agent_dir / "v1.md").write_text("   \n", encoding="utf-8")

    with pytest.raises(PromptNotFoundError, match="vuoto"):
        load_prompt("generation", "v1", tmp_path)
