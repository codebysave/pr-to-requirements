"""Recupero dei requisiti storici da mostrare al valutatore (Decisione 3.3, §9).

Il recupero è **esaustivo**: restituisce tutti i requisiti già validati che
appartengono allo stesso progetto e che nascono da Pull Request precedenti a
quella in esame. Non ordina per somiglianza e non calcola punteggi.

La ragione è di scala. Un requisito occupa una trentina di token: anche il
corpus più grande di cui disponiamo ne produce poche decine, che si aggiungono
al messaggio del valutatore senza pesare. Selezionare i più affini richiederebbe
un modello di embedding, cioè una dipendenza esterna, una soglia arbitraria da
calibrare e una nozione di «stesso significato» presa da terzi. A questa scala
non risolverebbe alcun problema che abbiamo, e ne introdurrebbe uno noto: gli
embedding distinguono male una frase dal suo contrario, mentre buona parte dei
nostri requisiti è in forma negativa e riconoscere una contraddizione significa
esattamente quello.

A stabilire se il candidato duplichi, raffini o contraddica un requisito
storico è quindi l'Assessment Agent, che ne legge il testo. Il punto è discusso
nel punto 5 di `docs/meetings/open-questions-for-tutor-updated.md`; le colonne
per gli embedding esistono già nello schema, per il giorno in cui la memoria
crescesse oltre quanto sta comodamente in un messaggio.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from are.agents.state import RetrievedRequirement
from are.input import PullRequestRecord

from .repository import SqliteRequirementRepository

logger = logging.getLogger(__name__)

DEFAULT_MAX_REQUIREMENTS = 50


@dataclass(frozen=True, slots=True)
class ExhaustiveRequirementRetriever:
    """Restituisce i requisiti validati confrontabili con il candidato.

    ``run_id`` isola l'esecuzione corrente: con un database condiviso fra più
    esecuzioni, senza questo filtro una run vedrebbe i requisiti prodotti da
    quelle precedenti e i confronti fra configurazioni perderebbero senso. Con
    ``None`` il recupero attraversa tutte le esecuzioni, che è il comportamento
    di una memoria che si accumula davvero nel tempo.

    ``max_requirements`` è una salvaguardia, non un ``top_k``: serve solo a
    impedire che un archivio cresciuto oltre le previsioni gonfi il messaggio
    senza che nessuno se ne accorga.
    """

    store: SqliteRequirementRepository
    run_id: str | None = None
    max_requirements: int = DEFAULT_MAX_REQUIREMENTS

    def retrieve(
        self,
        candidate: str,
        pull_request: PullRequestRecord,
    ) -> tuple[RetrievedRequirement, ...]:
        """Implementa la porta ``MemoryRetriever`` del workflow.

        Il testo del candidato non viene usato: senza un confronto semantico
        non c'è nulla da confrontare, e il criterio di selezione è dato per
        intero dai due filtri.
        """

        return self.search(
            repository=pull_request.repository,
            before_timestamp=pull_request.timestamp,
        )

    def search(
        self,
        *,
        repository: str | None = None,
        before_timestamp: datetime | None = None,
        limit: int | None = None,
    ) -> tuple[RetrievedRequirement, ...]:
        """Interroga la memoria con i filtri espliciti.

        I parametri corrispondono a quelli del tool MCP ``search_requirements``
        (Decisione 3.4, §5.1). Passarli singolarmente, invece di ricavarli da un
        ``PullRequestRecord``, permette al futuro server MCP di restare il
        livello sottile che la stessa decisione richiede al §11: senza, il tool
        dovrebbe costruire un record fittizio per poter chiamare il retriever.
        """

        stored = self.store.list_requirements(
            repository=repository,
            before_timestamp=before_timestamp,
            run_id=self.run_id,
        )

        massimo = self.max_requirements if limit is None else limit
        if len(stored) > massimo:
            # Si tengono i più recenti: sono quelli temporalmente più vicini
            # alla Pull Request in esame, e quindi i più probabilmente in
            # relazione con essa.
            logger.warning(
                "  [MEMORIA] %d requisiti disponibili, ne vengono mostrati %d (i più recenti)",
                len(stored),
                massimo,
            )
            stored = stored[-massimo:]

        return tuple(
            RetrievedRequirement(
                requirement_id=str(item.id),
                statement=item.statement,
                source_pr_number=item.source_pr_number,
            )
            for item in stored
        )
