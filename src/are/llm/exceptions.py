"""Errori pubblici del livello di accesso agli LLM."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


class LLMConfigError(Exception):
    """Classe base per gli errori di configurazione LLM."""


class LLMConfigFileError(LLMConfigError):
    """Il file di configurazione non esiste o non può essere letto come TOML."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f'Configurazione LLM non leggibile da "{path}": {reason}.')


class InvalidLLMConfigError(LLMConfigError):
    """Il contenuto della configurazione non rispetta lo schema previsto."""

    def __init__(self, path: Path, issues: Sequence[str]) -> None:
        if not issues:
            raise ValueError("È necessario specificare almeno un problema di validazione.")
        self.path = path
        self.issues = tuple(issues)
        details = "\n".join(f"- {issue}" for issue in self.issues)
        super().__init__(f'Configurazione LLM non valida in "{path}":\n{details}')


class LLMClientError(Exception):
    """Classe base per gli errori del client LLM."""


class MissingApiKeyError(LLMClientError):
    """La chiave API non è disponibile né come parametro né nell'ambiente."""

    def __init__(self, env_var: str) -> None:
        self.env_var = env_var
        super().__init__(
            f"Chiave API non trovata: impostare la variabile d'ambiente {env_var} "
            "(ad esempio tramite il file .env, mai committato) oppure passare "
            "api_key esplicitamente."
        )


class LLMCallError(LLMClientError):
    """La chiamata al fornitore LLM è fallita per un errore tecnico."""

    def __init__(self, model: str, reason: str) -> None:
        self.model = model
        self.reason = reason
        super().__init__(f'Chiamata LLM fallita (modello "{model}"): {reason}.')
