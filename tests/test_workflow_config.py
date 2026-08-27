from __future__ import annotations

from pathlib import Path

import pytest

from are.agents import (
    InvalidWorkflowConfigError,
    WorkflowConfigFileError,
    load_workflow_config,
)

VALID_CONFIG = """
[workflow]
assessment_enabled = true
memory_enabled = false
max_generation_attempts = 3
min_evidence_characters = 50
"""


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "workflow.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_valid_config(tmp_path: Path) -> None:
    config = load_workflow_config(write_config(tmp_path, VALID_CONFIG))

    assert config.assessment_enabled is True
    assert config.memory_enabled is False
    assert config.max_generation_attempts == 3
    assert config.min_evidence_characters == 50


def test_repository_config_file_is_valid() -> None:
    config = load_workflow_config(Path(__file__).parent.parent / "config" / "workflow.toml")

    assert config.max_generation_attempts >= 1


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(WorkflowConfigFileError, match="file non trovato"):
        load_workflow_config(tmp_path / "missing.toml")


def test_rejects_invalid_toml(tmp_path: Path) -> None:
    with pytest.raises(WorkflowConfigFileError, match="TOML non valido"):
        load_workflow_config(write_config(tmp_path, "[workflow\nx ="))


def test_rejects_missing_section(tmp_path: Path) -> None:
    with pytest.raises(InvalidWorkflowConfigError, match=r'"\[workflow\]" mancante'):
        load_workflow_config(write_config(tmp_path, "[other]\nkey = 1\n"))


def test_rejects_unknown_key(tmp_path: Path) -> None:
    content = VALID_CONFIG + "extra = 1\n"

    with pytest.raises(InvalidWorkflowConfigError, match='"extra" non prevista'):
        load_workflow_config(write_config(tmp_path, content))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("assessment_enabled", '"yes"'),
        ("assessment_enabled", "1"),
        ("memory_enabled", '"no"'),
        ("max_generation_attempts", "0"),
        ("max_generation_attempts", "true"),
        ("max_generation_attempts", '"3"'),
        ("min_evidence_characters", "-1"),
        ("min_evidence_characters", "true"),
    ],
)
def test_rejects_invalid_field_values(tmp_path: Path, field: str, value: str) -> None:
    lines = {
        "assessment_enabled": "true",
        "memory_enabled": "false",
        "max_generation_attempts": "3",
        "min_evidence_characters": "50",
    }
    lines[field] = value
    content = "[workflow]\n" + "\n".join(f"{key} = {val}" for key, val in lines.items())

    with pytest.raises(InvalidWorkflowConfigError, match=rf'"{field}"'):
        load_workflow_config(write_config(tmp_path, content))


def test_reports_all_issues_together(tmp_path: Path) -> None:
    content = "[workflow]\nassessment_enabled = 1\nunknown = 2\n"

    with pytest.raises(InvalidWorkflowConfigError) as excinfo:
        load_workflow_config(write_config(tmp_path, content))

    # tre chiavi obbligatorie mancanti, una sconosciuta, un tipo errato
    assert len(excinfo.value.issues) == 5
