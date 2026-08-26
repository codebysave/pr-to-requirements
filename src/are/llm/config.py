"""Caricamento e validazione della configurazione LLM per agente (Decisione 3.2).

La configurazione vive in un file TOML versionato nel repository, così ogni
esecuzione sperimentale documenta con precisione modello e parametri usati da
ciascun agente. Le credenziali non compaiono mai qui: la chiave API arriva
esclusivamente dall'ambiente.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .exceptions import InvalidLLMConfigError, LLMConfigFileError

AGENT_SECTIONS: tuple[str, ...] = ("generation", "assessment")

_REQUIRED_KEYS = frozenset({"model", "max_tokens"})
_OPTIONAL_KEYS = frozenset({"effort"})
_ALLOWED_KEYS = _REQUIRED_KEYS | _OPTIONAL_KEYS

EFFORT_LEVELS: tuple[str, ...] = ("low", "medium", "high", "xhigh", "max")

# Scorciatoie per selezionare un modello da riga di comando durante la
# sperimentazione (Decisione 3.2, §4.2). Un identificativo completo può essere
# passato direttamente e viene lasciato invariato.
MODEL_ALIASES: dict[str, str] = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-5",
}


def resolve_model_alias(nome: str) -> str:
    """Traduce un alias nel corrispondente identificativo del modello."""

    return MODEL_ALIASES.get(nome.strip().lower(), nome.strip())


@dataclass(frozen=True, slots=True)
class AgentLLMSettings:
    """Parametri di generazione di un singolo agente.

    I parametri di campionamento ``temperature``, ``top_p`` e ``top_k`` non
    esistono più nell'API dei modelli attuali: sono stati rimossi dal
    fornitore. Al loro posto alcuni modelli accettano ``effort``, che regola
    la profondità del ragionamento e la spesa complessiva di token.

    ``effort`` è opzionale e non è supportato da tutti i modelli (la fascia
    Haiku lo rifiuta): quando è ``None`` non viene inviato e vale il
    comportamento predefinito del modello.
    """

    model: str
    max_tokens: int
    effort: str | None = None


@dataclass(frozen=True, slots=True)
class LLMConfig:
    """Configurazione LLM completa: un blocco di parametri per agente."""

    generation: AgentLLMSettings
    assessment: AgentLLMSettings


def load_llm_config(path: str | os.PathLike[str]) -> LLMConfig:
    """Legge e valida il file TOML di configurazione degli agenti.

    Raises:
        LLMConfigFileError: se il file non esiste o non è TOML valido.
        InvalidLLMConfigError: se lo schema non è rispettato; tutti i problemi
            riscontrati vengono riportati insieme.
    """

    config_path = Path(path)
    try:
        content = config_path.read_bytes()
    except FileNotFoundError as exc:
        raise LLMConfigFileError(config_path, "file non trovato") from exc
    except OSError as exc:
        raise LLMConfigFileError(config_path, str(exc)) from exc

    try:
        document = tomllib.loads(content.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise LLMConfigFileError(
            config_path, f"contenuto non codificato in UTF-8 (byte {exc.start})"
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise LLMConfigFileError(config_path, f"TOML non valido: {exc}") from exc

    issues: list[str] = []

    unexpected_sections = set(document.keys()).difference(AGENT_SECTIONS)
    for section in sorted(unexpected_sections):
        issues.append(f'sezione "{section}" non prevista dallo schema')

    settings: dict[str, AgentLLMSettings] = {}
    for section in AGENT_SECTIONS:
        if section not in document:
            issues.append(f'sezione obbligatoria "[{section}]" mancante')
            continue
        value = document[section]
        if not isinstance(value, dict):
            issues.append(f'la sezione "{section}" deve essere una tabella TOML')
            continue
        parsed = _parse_agent_section(section, value, issues)
        if parsed is not None:
            settings[section] = parsed

    if issues:
        raise InvalidLLMConfigError(config_path, issues)

    return LLMConfig(generation=settings["generation"], assessment=settings["assessment"])


def _parse_agent_section(
    section: str,
    data: dict[str, Any],
    issues: list[str],
) -> AgentLLMSettings | None:
    section_issues: list[str] = []

    for key in sorted(_REQUIRED_KEYS.difference(data.keys())):
        section_issues.append(f'[{section}] chiave obbligatoria "{key}" mancante')
    for key in sorted(set(data.keys()).difference(_ALLOWED_KEYS)):
        section_issues.append(f'[{section}] chiave "{key}" non prevista dallo schema')

    model = data.get("model")
    if "model" in data and (not isinstance(model, str) or not model.strip()):
        section_issues.append(f'[{section}] "model" deve essere una stringa non vuota')

    max_tokens = data.get("max_tokens")
    if "max_tokens" in data and (type(max_tokens) is not int or max_tokens <= 0):
        section_issues.append(f'[{section}] "max_tokens" deve essere un intero positivo')

    effort = data.get("effort")
    if "effort" in data and effort not in EFFORT_LEVELS:
        ammessi = ", ".join(EFFORT_LEVELS)
        section_issues.append(f'[{section}] "effort" deve essere uno fra: {ammessi}')

    issues.extend(section_issues)
    if section_issues:
        return None

    assert isinstance(model, str)
    assert type(max_tokens) is int
    return AgentLLMSettings(
        model=model,
        max_tokens=max_tokens,
        effort=effort if isinstance(effort, str) else None,
    )
