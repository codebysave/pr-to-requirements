"""Client MCP per l'accesso alla memoria persistente (Decisione 3.4).

Espone due implementazioni delle porte del workflow che, invece di leggere
e scrivere direttamente sul DB, dialogano con il server MCP di
``are.mcp_server`` via stdio.

Il ponte fra il grafo LangGraph (sincrono) e il client MCP dell'SDK
(asincrono) e' gestito da un ``BlockingPortal`` di ``anyio``: l'event loop
async gira in un thread di background, e le chiamate sincrone del grafo
vengono trasportate al loop dal portal. Il grafo non conosce ``asyncio``.

Il ciclo di vita e' un unico sottoprocesso per l'intero run: viene avviato
all'ingresso del context manager :class:`mcp_memory_session` e terminato
all'uscita. Riutilizzare la sessione fra Pull Request evita il costo di
riavvio del processo e mantiene stabile la connessione al DB.

Filosofia. Il codice del retriever e del repository di Marco non viene
toccato: le nuove classi implementano gli stessi protocolli
(``MemoryRetriever`` e ``AcceptedRequirementStore``) e possono essere
iniettate in ``WorkflowDependencies`` al posto delle implementazioni
dirette senza modificare il grafo.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

import anyio.from_thread
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

from are.agents.state import RelationClaim, RetrievedRequirement
from are.input import PullRequestRecord


@dataclass(frozen=True, slots=True)
class McpMemorySessionConfig:
    """Parametri per costruire i parametri di lancio del server MCP.

    ``memory_scope`` e ``max_requirements`` sono passati al sottoprocesso
    come argomenti CLI, coerentemente con ``are.mcp_server.__main__``.
    """

    db_path: Path
    run_id: str
    memory_scope: str = "run"
    max_requirements: int = 50


class _McpBridge:
    """Ponte fra il grafo sincrono e il client MCP asincrono.

    Non e' pubblico: esiste per centralizzare in un unico oggetto la
    sessione con il server e il portal di ``anyio`` che la mantiene in
    vita. Le due porte (retriever e store) delegano qui le loro chiamate.
    """

    def __init__(self, portal: anyio.from_thread.BlockingPortal, client: Client) -> None:
        self._portal = portal
        self._client = client

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoca un tool MCP dal grafo sincrono, restituendo il dict strutturato.

        L'SDK espone i campi del ``CallToolResult`` in ``snake_case``:
        ``is_error`` e ``structured_content``. Vi si accede direttamente e non
        con ``getattr`` e un valore predefinito: un nome sbagliato deve
        sollevare un errore, non essere scambiato per una risposta valida. Con
        ``getattr(result, "isError", False)`` un tool fallito risultava
        riuscito, e il guasto vero emergeva molto piu' avanti sotto forma di
        messaggio fuorviante.

        ``structured_content`` e' valorizzato soltanto se il tool dichiara un
        tipo di ritorno: e' l'annotazione a far generare all'SDK lo schema di
        output. Senza, la risposta arriverebbe come semplice testo.
        """

        result = self._portal.call(self._client.call_tool, name, arguments)
        if result.is_error:
            # Il messaggio di errore, se presente, sta nel primo blocco testuale.
            text = _first_text_block(result)
            raise RuntimeError(
                f"tool MCP {name!r} ha restituito un errore: {text or 'nessun dettaglio'}"
            )
        if result.structured_content is None:
            raise RuntimeError(
                f"tool MCP {name!r} non ha restituito structured_content: "
                "il tool deve dichiarare un tipo di ritorno perche' l'SDK "
                "produca lo schema di output"
            )
        return result.structured_content


class McpMemoryRetriever:
    """Implementa la porta ``MemoryRetriever`` chiamando il server MCP.

    Traduce la richiesta del grafo in una chiamata al tool
    ``search_requirements`` del server. Il ``candidate_text`` viene inoltrato
    per rispettare la firma generica (Strada B), anche se il retriever
    esaustivo di oggi non lo utilizza: se un domani il retriever diventasse
    semantico, il client resterebbe invariato.
    """

    def __init__(self, bridge: _McpBridge) -> None:
        self._bridge = bridge

    def retrieve(
        self,
        candidate: str,
        pull_request: PullRequestRecord,
    ) -> tuple[RetrievedRequirement, ...]:
        response = self._bridge.call_tool(
            "search_requirements",
            {
                "candidate_text": candidate,
                "repository_id": pull_request.repository,
                "before_timestamp": pull_request.timestamp.isoformat(),
            },
        )
        return tuple(
            RetrievedRequirement(
                requirement_id=str(item["requirement_id"]),
                statement=item["statement"],
                source_pr_number=int(item["source_pr_number"]),
            )
            for item in response.get("results", [])
        )


class McpAcceptedRequirementStore:
    """Implementa la porta ``AcceptedRequirementStore`` chiamando il server MCP.

    Traduce la scrittura del grafo in una chiamata al tool
    ``store_accepted_requirement``. Come da Opzione A concordata nel MVP, il
    tool restituisce solo ``created_at``: l'``id`` interno del requisito non
    viene esposto e non viene tracciato lato client.
    """

    def __init__(self, bridge: _McpBridge) -> None:
        self._bridge = bridge

    def store_accepted(
        self,
        pull_request: PullRequestRecord,
        statement: str,
        relations: Sequence[RelationClaim] = (),
    ) -> None:
        evidence = f"{pull_request.title}\n\n{pull_request.body}".strip() or None
        self._bridge.call_tool(
            "store_accepted_requirement",
            {
                "statement": statement,
                "source_repository": pull_request.repository,
                "source_pr_number": pull_request.pr_number,
                "source_pr_timestamp": pull_request.timestamp.isoformat(),
                "evidence": evidence,
                "relations": [
                    {
                        "type": str(relazione.kind),
                        "target_requirement_id": relazione.target_requirement_id,
                        "target_pr_number": relazione.target_pr_number,
                        "reason": relazione.reason,
                    }
                    for relazione in relations
                ],
            },
        )


@contextmanager
def mcp_memory_session(
    config: McpMemorySessionConfig,
    *,
    server_command: str | None = None,
) -> Iterator[tuple[McpMemoryRetriever, McpAcceptedRequirementStore]]:
    """Apre una sessione con il server MCP e fornisce le due porte.

    Il sottoprocesso viene avviato una volta sola all'ingresso del context
    manager e chiuso in modo pulito all'uscita, anche in caso di eccezione.
    Il retriever e lo store restituiti implementano i protocolli previsti da
    ``WorkflowDependencies`` e possono essere iniettati direttamente nel
    grafo.

    ``server_command`` permette di sostituire il comando che lancia il
    server (utile nei test, dove si vuole avviare un server con
    dipendenze finte). Nel caso normale viene usato l'interprete Python
    corrente.
    """

    server_params = _build_server_params(config, server_command)

    with anyio.from_thread.start_blocking_portal() as portal:
        # Ingresso e uscita dal client devono avvenire nello stesso task del
        # loop: i cancel scope di anyio lo impongono, e il client MCP ne apre
        # uno per il task group che gestisce il sottoprocesso. Due
        # ``portal.call`` distinti per ``__aenter__`` e ``__aexit__`` girano in
        # task diversi e la sessione non si apre nemmeno. ``anyio`` fornisce
        # ``wrap_async_context_manager`` esattamente per questo caso: un solo
        # oggetto che entra ed esce dallo stesso task.
        with portal.wrap_async_context_manager(Client(server_params)) as client:
            bridge = _McpBridge(portal, client)
            yield McpMemoryRetriever(bridge), McpAcceptedRequirementStore(bridge)


def _build_server_params(
    config: McpMemorySessionConfig,
    server_command: str | None,
) -> StdioServerParameters:
    """Costruisce i parametri di lancio del server MCP.

    Il comando corrisponde a ``python -m are.mcp_server`` con gli argomenti
    del ``McpMemorySessionConfig``; usiamo l'interprete Python corrente
    (``sys.executable``) per assicurarci che il sottoprocesso usi lo stesso
    ambiente virtuale del client.
    """

    command = server_command or sys.executable
    args = [
        "-m",
        "are.mcp_server",
        str(config.db_path),
        config.run_id,
        f"--memory-scope={config.memory_scope}",
        f"--max-requirements={config.max_requirements}",
    ]
    return StdioServerParameters(command=command, args=args)


def _first_text_block(result: Any) -> str | None:
    """Estrae il primo blocco di testo da un ``CallToolResult``, se presente."""

    content = getattr(result, "content", None) or ()
    for block in content:
        text = getattr(block, "text", None)
        if isinstance(text, str) and text:
            return text
    return None
