"""Errori pubblici della configurazione del workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


class WorkflowConfigError(Exception):
    """Classe base per gli errori di configurazione del workflow."""


class WorkflowConfigFileError(WorkflowConfigError):
    """Il file di configurazione non esiste o non può essere letto come TOML."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f'Configurazione workflow non leggibile da "{path}": {reason}.')


class InvalidWorkflowConfigError(WorkflowConfigError):
    """Il contenuto della configurazione non rispetta lo schema previsto."""

    def __init__(self, path: Path, issues: Sequence[str]) -> None:
        if not issues:
            raise ValueError("È necessario specificare almeno un problema di validazione.")
        self.path = path
        self.issues = tuple(issues)
        details = "\n".join(f"- {issue}" for issue in self.issues)
        super().__init__(f'Configurazione workflow non valida in "{path}":\n{details}')
