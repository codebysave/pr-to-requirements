"""Configurazione del workflow (Decisione 3.5, §20).

I parametri dell'architettura restano esterni alla logica dei nodi: il file
TOML versionato permette di eseguire il workflow in configurazioni diverse
senza modificarne il codice, durante lo sviluppo incrementale e per le prove
progressive descritte nella Decisione 3.7.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .exceptions import InvalidWorkflowConfigError, WorkflowConfigFileError

_SECTION = "workflow"
_REQUIRED_KEYS = frozenset(
    {
        "assessment_enabled",
        "memory_enabled",
        "max_generation_attempts",
        "min_evidence_characters",
        "max_memory_requirements",
    }
)


@dataclass(frozen=True, slots=True)
class WorkflowConfig:
    """Parametri configurabili del workflow della singola Pull Request."""

    assessment_enabled: bool = True
    memory_enabled: bool = False
    max_generation_attempts: int = 3
    min_evidence_characters: int = 50
    max_memory_requirements: int = 50


def load_workflow_config(path: str | os.PathLike[str]) -> WorkflowConfig:
    """Legge e valida il file TOML della configurazione del workflow.

    Raises:
        WorkflowConfigFileError: se il file non esiste o non è TOML valido.
        InvalidWorkflowConfigError: se lo schema non è rispettato.
    """

    config_path = Path(path)
    try:
        content = config_path.read_bytes()
    except FileNotFoundError as exc:
        raise WorkflowConfigFileError(config_path, "file non trovato") from exc
    except OSError as exc:
        raise WorkflowConfigFileError(config_path, str(exc)) from exc

    try:
        document = tomllib.loads(content.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise WorkflowConfigFileError(
            config_path, f"contenuto non codificato in UTF-8 (byte {exc.start})"
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise WorkflowConfigFileError(config_path, f"TOML non valido: {exc}") from exc

    issues: list[str] = []

    for section in sorted(set(document.keys()).difference({_SECTION})):
        issues.append(f'sezione "{section}" non prevista dallo schema')

    data = document.get(_SECTION)
    if data is None:
        issues.append(f'sezione obbligatoria "[{_SECTION}]" mancante')
        raise InvalidWorkflowConfigError(config_path, issues)
    if not isinstance(data, dict):
        issues.append(f'la sezione "{_SECTION}" deve essere una tabella TOML')
        raise InvalidWorkflowConfigError(config_path, issues)

    for key in sorted(_REQUIRED_KEYS.difference(data.keys())):
        issues.append(f'[{_SECTION}] chiave obbligatoria "{key}" mancante')
    for key in sorted(set(data.keys()).difference(_REQUIRED_KEYS)):
        issues.append(f'[{_SECTION}] chiave "{key}" non prevista dallo schema')

    assessment_enabled = data.get("assessment_enabled")
    if "assessment_enabled" in data and not isinstance(assessment_enabled, bool):
        issues.append(f'[{_SECTION}] "assessment_enabled" deve essere un booleano')

    memory_enabled = data.get("memory_enabled")
    if "memory_enabled" in data and not isinstance(memory_enabled, bool):
        issues.append(f'[{_SECTION}] "memory_enabled" deve essere un booleano')

    max_attempts = data.get("max_generation_attempts")
    if "max_generation_attempts" in data and (type(max_attempts) is not int or max_attempts < 1):
        issues.append(
            f'[{_SECTION}] "max_generation_attempts" deve essere un intero maggiore o uguale a 1'
        )

    min_evidence = data.get("min_evidence_characters")
    if "min_evidence_characters" in data and (type(min_evidence) is not int or min_evidence < 0):
        issues.append(
            f'[{_SECTION}] "min_evidence_characters" deve essere un intero maggiore o uguale a 0'
        )

    max_memory = data.get("max_memory_requirements")
    if "max_memory_requirements" in data and (type(max_memory) is not int or max_memory < 1):
        issues.append(
            f'[{_SECTION}] "max_memory_requirements" deve essere un intero maggiore o uguale a 1'
        )

    if issues:
        raise InvalidWorkflowConfigError(config_path, issues)

    assert isinstance(assessment_enabled, bool)
    assert isinstance(memory_enabled, bool)
    assert type(max_attempts) is int
    assert type(min_evidence) is int
    assert type(max_memory) is int
    return WorkflowConfig(
        assessment_enabled=assessment_enabled,
        memory_enabled=memory_enabled,
        max_generation_attempts=max_attempts,
        min_evidence_characters=min_evidence,
        max_memory_requirements=max_memory,
    )
