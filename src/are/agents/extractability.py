"""Verifica preliminare di estraibilità, deterministica (Decisione 3.5, §6).

La verifica non usa un modello linguistico. La Decisione 3.5 (§4.3) la
definisce come fase preliminare della pipeline e ne consente, senza imporla,
un'implementazione basata su LLM: qui si è scelto un controllo deterministico
per tre ragioni.

La prima è la riproducibilità: un controllo sintattico dà sempre lo stesso
esito, mentre un modello può cambiarlo fra un'esecuzione e l'altra. La seconda
è che questo controllo decide *senza vedere il requisito*, mentre l'Assessment
Agent lo ha davanti: il giudizio semantico appartiene quindi a quest'ultimo,
che dispone di più informazione e che può rifiutare con `REJECT`. La terza è
il costo, nullo invece di una chiamata per Pull Request.

Il compito di questo componente è di conseguenza limitato: scartare i casi
incontestabili, in cui non esiste testo sufficiente perché una qualsiasi
valutazione sia possibile. Tutto il resto prosegue verso la generazione.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from are.input import PullRequestRecord

from .state import Extractability, ExtractabilityResult

logger = logging.getLogger(__name__)

DEFAULT_MIN_EVIDENCE_CHARACTERS = 50


@dataclass(frozen=True, slots=True)
class DeterministicExtractabilityChecker:
    """Scarta le Pull Request prive di testo sufficiente a essere valutate.

    ``min_evidence_characters`` è la lunghezza minima complessiva di titolo e
    corpo, contata ignorando gli spazi iniziali e finali. Il valore è
    provvisorio e andrà calibrato sul gold standard: è un criterio di comodo,
    non una soglia fondata (si veda il punto aperto sulle Pull Request con
    corpo assente o scarsamente informativo, in `docs/meetings/`).
    """

    min_evidence_characters: int = DEFAULT_MIN_EVIDENCE_CHARACTERS

    def check(self, pull_request: PullRequestRecord) -> ExtractabilityResult:
        title = pull_request.title.strip()
        body = pull_request.body.strip()

        logger.info("  [GATE]    controllo che la PR contenga testo sufficiente...")
        result = self._evaluate(title, body)
        logger.info("  [GATE]    -> %s: %s", result.decision.value, result.reason)
        return result

    def _evaluate(self, title: str, body: str) -> ExtractabilityResult:
        if not body:
            return ExtractabilityResult(
                decision=Extractability.NOT_EXTRACTABLE,
                reason="il corpo della Pull Request è vuoto",
            )

        lunghezza = len(title) + len(body)
        if lunghezza < self.min_evidence_characters:
            return ExtractabilityResult(
                decision=Extractability.NOT_EXTRACTABLE,
                reason=(
                    f"titolo e corpo contengono {lunghezza} caratteri, "
                    f"meno del minimo richiesto di {self.min_evidence_characters}"
                ),
            )

        return ExtractabilityResult(
            decision=Extractability.EXTRACTABLE,
            reason=(f"titolo e corpo contengono {lunghezza} caratteri: la valutazione prosegue"),
        )
