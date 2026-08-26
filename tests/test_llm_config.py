from __future__ import annotations

from pathlib import Path

import pytest

from are.llm import InvalidLLMConfigError, LLMConfigFileError, load_llm_config

VALID_SECTION = {"model": '"claude-haiku-4-5"', "max_tokens": "1024"}


def render_config(
    generation: dict[str, str] | None = None,
    assessment: dict[str, str] | None = None,
) -> str:
    lines: list[str] = []
    for name, fields in (("generation", generation), ("assessment", assessment)):
        if fields is None:
            continue
        lines.append(f"[{name}]")
        lines.extend(f"{key} = {value}" for key, value in fields.items())
        lines.append("")
    return "\n".join(lines)


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "llm.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_valid_config_with_per_agent_settings(tmp_path: Path) -> None:
    content = render_config(
        generation=VALID_SECTION,
        assessment={**VALID_SECTION, "effort": '"high"'},
    )

    config = load_llm_config(write_config(tmp_path, content))

    assert config.generation.model == "claude-haiku-4-5"
    assert config.generation.max_tokens == 1024
    assert config.generation.effort is None
    assert config.assessment.effort == "high"


def test_repository_config_file_is_valid() -> None:
    config = load_llm_config(Path(__file__).parent.parent / "config" / "llm.toml")

    assert config.generation.model
    assert config.assessment.model


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(LLMConfigFileError, match="file non trovato"):
        load_llm_config(tmp_path / "missing.toml")


def test_rejects_invalid_toml(tmp_path: Path) -> None:
    with pytest.raises(LLMConfigFileError, match="TOML non valido"):
        load_llm_config(write_config(tmp_path, "[generation\nmodel ="))


def test_rejects_missing_section_and_reports_unknown_one(tmp_path: Path) -> None:
    content = render_config(generation=VALID_SECTION) + "\n[other]\nkey = 1\n"

    with pytest.raises(InvalidLLMConfigError) as excinfo:
        load_llm_config(write_config(tmp_path, content))

    message = str(excinfo.value)
    assert '"[assessment]" mancante' in message
    assert '"other" non prevista' in message


def test_rejects_unknown_key_in_section(tmp_path: Path) -> None:
    content = render_config(
        generation={**VALID_SECTION, "api_key": '"secret"'},
        assessment=VALID_SECTION,
    )

    with pytest.raises(InvalidLLMConfigError, match='"api_key" non prevista'):
        load_llm_config(write_config(tmp_path, content))


def test_rejects_missing_required_key(tmp_path: Path) -> None:
    generation = {key: value for key, value in VALID_SECTION.items() if key != "model"}
    content = render_config(generation=generation, assessment=VALID_SECTION)

    with pytest.raises(InvalidLLMConfigError, match=r'\[generation\] chiave obbligatoria "model"'):
        load_llm_config(write_config(tmp_path, content))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("model", '""'),
        ("model", "7"),
        ("effort", '"turbo"'),
        ("effort", "3"),
        ("max_tokens", "0"),
        ("max_tokens", '"1024"'),
        ("max_tokens", "true"),
    ],
)
def test_rejects_invalid_field_values(tmp_path: Path, field: str, value: str) -> None:
    content = render_config(
        generation={**VALID_SECTION, field: value},
        assessment=VALID_SECTION,
    )

    with pytest.raises(InvalidLLMConfigError, match=rf'\[generation\] "{field}"'):
        load_llm_config(write_config(tmp_path, content))


def test_reports_all_issues_together(tmp_path: Path) -> None:
    content = render_config(generation={"effort": '"turbo"', "max_tokens": "-1"})

    with pytest.raises(InvalidLLMConfigError) as excinfo:
        load_llm_config(write_config(tmp_path, content))

    # model mancante, max_tokens non positivo, effort non valido, sezione assessment mancante
    assert len(excinfo.value.issues) == 4
