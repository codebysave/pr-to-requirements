"""Caricamento delle variabili d'ambiente dal file locale ``.env``.

Il file ``.env`` contiene esclusivamente credenziali (la chiave API) ed è
escluso dal versionamento; ``.env.example`` documenta le variabili richieste.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv


def load_environment(dotenv_path: str | os.PathLike[str] | None = None) -> None:
    """Carica ``.env`` senza sovrascrivere variabili già presenti nell'ambiente.

    Va invocata una sola volta dall'entry point dell'applicazione, prima di
    creare i client LLM. Se il file non esiste non è un errore: le variabili
    possono essere fornite direttamente dall'ambiente.
    """

    load_dotenv(dotenv_path=dotenv_path, override=False)
