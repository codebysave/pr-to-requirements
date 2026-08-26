"""Caricamento dei prompt versionati degli agenti (Decisione 3.2).

I prompt vivono fuori dal codice, in `prompts/<agente>/<versione>.md`, e sono
versionati nel repository: ogni esecuzione sperimentale può così dichiarare
con quale formulazione e' stata prodotta.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_PROMPT_VERSION = "v1"

# La cartella `prompts/` sta nella radice del repository, accanto a `src/`.
DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"

EXTRACTABILITY_AGENT = "extractability"
GENERATION_AGENT = "generation"
ASSESSMENT_AGENT = "assessment"


class PromptNotFoundError(Exception):
    """Il prompt richiesto non esiste o non è leggibile."""

    def __init__(self, agent: str, version: str, path: Path, reason: str) -> None:
        self.agent = agent
        self.version = version
        self.path = path
        self.reason = reason
        super().__init__(
            f'Prompt "{agent}" versione "{version}" non disponibile in "{path}": {reason}.'
        )


def load_prompt(
    agent: str,
    version: str = DEFAULT_PROMPT_VERSION,
    prompts_dir: str | os.PathLike[str] | None = None,
) -> str:
    """Restituisce il testo del prompt di sistema di un agente.

    Raises:
        PromptNotFoundError: se il file non esiste, non e' leggibile, non e'
            UTF-8 valido oppure e' vuoto.
    """

    directory = Path(prompts_dir) if prompts_dir is not None else DEFAULT_PROMPTS_DIR
    path = directory / agent / f"{version}.md"

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PromptNotFoundError(agent, version, path, "file non trovato") from exc
    except UnicodeDecodeError as exc:
        raise PromptNotFoundError(
            agent, version, path, f"contenuto non codificato in UTF-8 (byte {exc.start})"
        ) from exc
    except OSError as exc:
        raise PromptNotFoundError(agent, version, path, str(exc)) from exc

    if not text.strip():
        raise PromptNotFoundError(agent, version, path, "il prompt è vuoto")
    return text
