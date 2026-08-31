"""Server MCP per l'accesso alla memoria persistente (Decisione 3.4).

Espone come tool MCP le operazioni di lettura e scrittura sulla memoria
dei requisiti validati. La logica di persistenza e retrieval resta nei
componenti applicativi (``SqliteRequirementRepository`` e
``ExhaustiveRequirementRetriever`` in ``src/are/db/``): il server si limita a
tradurre le richieste MCP in chiamate a quei componenti (Decisione 3.4 §11).

Il server viene costruito tramite :func:`create_server`, che inietta le
dipendenze come parametri e i tool le catturano via closure. Questa
struttura permette di testare il server con repository e retriever in
memoria, senza toccare il DB reale.

**Nota sul contratto generico.** Il tool ``search_requirements`` accetta
``candidate_text`` anche se l'``ExhaustiveRequirementRetriever`` attuale non lo
usa. La descrizione di un tool MCP è leggibile da una macchina, e un contratto
che dichiara di accettare il testo del candidato permette a un futuro retriever
semantico di subentrare senza rinegoziare l'interfaccia né aggiornare i client.
Le colonne per gli embedding sono già nello schema del database (Decisione 3.3):
il contratto è coerente con una porta già lasciata aperta. Il punto è discusso
nel punto 5 di ``docs/meetings/open-questions-for-tutor-updated.md``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TypedDict

from mcp.server.mcpserver import MCPServer

from are.db import ExhaustiveRequirementRetriever, SqliteRequirementRepository
from are.input import PullRequestRecord


class RetrievedRequirementPayload(TypedDict):
    """Un requisito storico, come viaggia sul protocollo."""

    requirement_id: str
    statement: str
    source_pr_number: int


class SearchRequirementsResult(TypedDict):
    """Esito di ``search_requirements``. La lista puo' essere vuota."""

    results: list[RetrievedRequirementPayload]


class StoreAcceptedRequirementResult(TypedDict):
    """Esito di ``store_accepted_requirement`` (Opzione A: nessun id esposto)."""

    created_at: str


def create_server(
    repository: SqliteRequirementRepository,
    retriever: ExhaustiveRequirementRetriever,
) -> MCPServer:
    """Costruisce il server MCP con retriever e repository iniettati.

    Il server non conosce SQLite né la strategia di retrieval: delega
    tutto ai due componenti applicativi passati come parametro. Questa
    firma rende esplicito l'unico modo previsto di configurare il server.
    """

    server = MCPServer(
        name="pr-to-requirements-memory",
        description=(
            "Accesso alla memoria persistente dei requisiti validati di "
            "pr-to-requirements. Espone due tool: search_requirements "
            "(lettura, usato dal workflow per fornire il contesto storico "
            "all'Assessment) e store_accepted_requirement (scrittura, "
            "invocato dal controller dopo un ACCEPT)."
        ),
    )

    @server.tool(
        description=(
            "Restituisce i requisiti gia' validati che possono essere confrontati "
            "con un candidato. Oggi la ricerca e' esaustiva entro i filtri di "
            "repository e data; candidate_text viene accettato per compatibilita' "
            "futura con un retriever semantico ma non viene attualmente usato. "
            "Una lista vuota e' un successo, non un errore."
        ),
    )
    def search_requirements(
        candidate_text: str | None = None,
        repository_id: str | None = None,
        before_timestamp: str | None = None,
        limit: int | None = None,
    ) -> SearchRequirementsResult:
        """Interroga la memoria e restituisce i requisiti storici.

        Args:
            candidate_text: testo del requisito candidato. Oggi ignorato,
                accettato per Strada B (compatibilita' con futuro retriever
                semantico).
            repository_id: filtro sul repository (es. ``scrapy/scrapy``).
                Se ``None``, nessun filtro.
            before_timestamp: filtro sulla data della PR di origine
                (ISO-8601, es. ``2025-04-18T09:22:04Z``). Se ``None``,
                nessun filtro.
            limit: numero massimo di risultati restituiti. E' una
                salvaguardia, non un top-k: il retriever esaustivo
                restituisce comunque tutto entro i filtri, e questo campo
                serve solo a evitare messaggi troppo grandi.

        Returns:
            ``{"results": [{"requirement_id": str, "statement": str,
            "source_pr_number": int}, ...]}``. La lista puo' essere vuota.
        """

        # ``candidate_text`` non viene passato al retriever esaustivo di
        # oggi: si veda la nota sulla Strada B nel docstring del modulo.
        _ = candidate_text

        parsed_timestamp: datetime | None = None
        if before_timestamp is not None:
            parsed_timestamp = _parse_iso_timestamp(before_timestamp)

        results = retriever.search(
            repository=repository_id,
            before_timestamp=parsed_timestamp,
            limit=limit,
        )

        return {
            "results": [
                {
                    "requirement_id": item.requirement_id,
                    "statement": item.statement,
                    "source_pr_number": item.source_pr_number,
                }
                for item in results
            ]
        }

    @server.tool(
        description=(
            "Persiste nella memoria un requisito che ha superato la valutazione "
            "con esito ACCEPT. Il tool non decide se accettare: riceve solo "
            "requisiti gia' validati dal workflow (Decisione 3.4 §7). Nel MVP "
            "l'id interno del requisito non viene esposto (Opzione A)."
        ),
    )
    def store_accepted_requirement(
        statement: str,
        source_repository: str,
        source_pr_number: int,
        source_pr_timestamp: str,
        evidence: str | None = None,
    ) -> StoreAcceptedRequirementResult:
        """Scrive un requisito validato nella memoria.

        Args:
            statement: testo del requisito accettato.
            source_repository: repository di origine (es. ``scrapy/scrapy``).
            source_pr_number: numero della PR di origine su GitHub.
            source_pr_timestamp: data della PR di origine (ISO-8601).
            evidence: title + body della PR, opzionale. Salvato nel DB
                per rendere la memoria leggibile da sola.

        Returns:
            ``{"created_at": <ISO-8601 UTC>}``.
        """

        parsed_timestamp = _parse_iso_timestamp(source_pr_timestamp)

        # ``store_accepted`` accetta un ``PullRequestRecord`` intero, non
        # i singoli campi: costruiamo un record equivalente qui. L'``id``
        # del record non viene usato dal metodo, ma il tipo lo richiede.
        # L'evidenza viene concatenata dal repository come
        # ``title + "\\n\\n" + body``: mettere l'intera evidenza nel body
        # e lasciare il title vuoto produce lo stesso risultato di prima
        # nel campo ``evidence`` della tabella.
        record = PullRequestRecord(
            id=f"{source_repository}-pr-{source_pr_number}",
            repository=source_repository,
            pr_number=source_pr_number,
            timestamp=parsed_timestamp,
            title="",
            body=evidence or "",
        )
        repository.store_accepted(record, statement)

        return {"created_at": datetime.now(timezone.utc).isoformat()}

    return server


def _parse_iso_timestamp(value: str) -> datetime:
    """Parsa una stringa ISO-8601 in datetime timezone-aware.

    Accetta sia il suffisso ``Z`` sia l'offset esplicito. Un timestamp
    senza fuso orario viene rifiutato: la memoria richiede sempre
    timestamp timezone-aware (Decisione 3.3 sulla scrittura in ISO 8601
    UTC).
    """

    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(
            f"timestamp senza fuso orario: {value!r}. "
            "Richiesto ISO-8601 con suffisso Z oppure offset esplicito."
        )
    return parsed
