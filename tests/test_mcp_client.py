"""Il client MCP, con un portal e un client finti: nessun sottoprocesso.

Questi test coprono la lettura della risposta e la costruzione degli
argomenti, che è dove si annidano gli errori silenziosi. Il caso che conta di
più è il primo: un tool fallito deve sollevare, non passare per riuscito.

La versione originale leggeva ``isError`` e ``structuredContent``, mentre
l'SDK espone ``is_error`` e ``structured_content``. Con ``getattr`` e un
valore predefinito, un nome sbagliato non dà errore: restituisce il default.
Così un tool che falliva a ogni chiamata risultava riuscito, e il guasto vero
emergeva molto più avanti sotto forma di messaggio fuorviante. I finti qui
sotto espongono i nomi veri, quindi un ritorno ai nomi sbagliati fa fallire
questi test invece di passare inosservato.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from are.input import PullRequestRecord
from are.mcp_client import (
    McpAcceptedRequirementStore,
    McpMemoryRetriever,
    McpMemorySessionConfig,
    _build_server_params,
    _McpBridge,
)


class BloccoDiTesto:
    def __init__(self, text: str) -> None:
        self.text = text


class RispostaFinta:
    """Riproduce la forma del ``CallToolResult`` dell'SDK."""

    def __init__(
        self,
        structured_content: dict[str, Any] | None = None,
        is_error: bool = False,
        content: list[BloccoDiTesto] | None = None,
    ) -> None:
        self.structured_content = structured_content
        self.is_error = is_error
        self.content = content or []


class PortalFinto:
    """Esegue subito ciò che gli viene passato e registra le chiamate."""

    def __init__(self, risposta: RispostaFinta) -> None:
        self._risposta = risposta
        self.chiamate: list[tuple[str, dict[str, Any]]] = []

    def call(self, funzione, *args):
        return funzione(*args)

    def call_tool(self, nome: str, argomenti: dict[str, Any]) -> RispostaFinta:
        self.chiamate.append((nome, argomenti))
        return self._risposta


class ClientFinto:
    def __init__(self, portal: PortalFinto) -> None:
        self.call_tool = portal.call_tool


def bridge_con(risposta: RispostaFinta) -> tuple[_McpBridge, PortalFinto]:
    portal = PortalFinto(risposta)
    return _McpBridge(portal, ClientFinto(portal)), portal


def pr(
    pr_number: int = 42,
    repository: str = "owner/repo",
    timestamp: str = "2025-03-01T10:00:00Z",
    title: str = "Fix the export",
    body: str = "The export button did nothing.",
) -> PullRequestRecord:
    return PullRequestRecord.from_mapping(
        {
            "id": f"{repository.replace('/', '-')}-pr-{pr_number}",
            "repository": repository,
            "pr_number": pr_number,
            "timestamp": timestamp,
            "title": title,
            "body": body,
        }
    )


# -- lettura della risposta ----------------------------------------------


def test_a_failing_tool_raises_and_carries_the_server_message():
    """Il caso che il codice originale lasciava passare per un successo."""

    bridge, _ = bridge_con(
        RispostaFinta(is_error=True, content=[BloccoDiTesto("il database non risponde")])
    )
    with pytest.raises(RuntimeError, match="il database non risponde"):
        bridge.call_tool("search_requirements", {})


def test_a_failing_tool_without_a_message_still_raises():
    bridge, _ = bridge_con(RispostaFinta(is_error=True))
    with pytest.raises(RuntimeError, match="nessun dettaglio"):
        bridge.call_tool("search_requirements", {})


def test_a_missing_structured_answer_raises_instead_of_being_read_as_empty():
    """Accade quando il tool non dichiara il tipo di ritorno: senza schema di
    output l'SDK consegna solo testo. Interpretarlo come "nessun risultato"
    farebbe valutare la Pull Request senza il suo contesto storico."""

    bridge, _ = bridge_con(RispostaFinta(structured_content=None))
    with pytest.raises(RuntimeError, match="structured_content"):
        bridge.call_tool("search_requirements", {})


def test_a_successful_call_returns_the_structured_content():
    bridge, _ = bridge_con(RispostaFinta(structured_content={"results": []}))
    assert bridge.call_tool("search_requirements", {}) == {"results": []}


# -- il retriever ---------------------------------------------------------


def test_the_retriever_sends_the_project_and_the_date_of_the_pull_request():
    """I due filtri non arrivano dal modello: li impone il client, che
    conosce la Pull Request in corso."""

    bridge, portal = bridge_con(RispostaFinta(structured_content={"results": []}))
    McpMemoryRetriever(bridge).retrieve("un candidato", pr(repository="owner/uno"))

    nome, argomenti = portal.chiamate[0]
    assert nome == "search_requirements"
    assert argomenti["repository_id"] == "owner/uno"
    assert argomenti["before_timestamp"].startswith("2025-03-01T10:00:00")


def test_the_retriever_forwards_the_candidate_text():
    """Strada B: il contratto resta generico anche se il retriever esaustivo
    di oggi ignora il campo."""

    bridge, portal = bridge_con(RispostaFinta(structured_content={"results": []}))
    McpMemoryRetriever(bridge).retrieve("il testo del candidato", pr())

    assert portal.chiamate[0][1]["candidate_text"] == "il testo del candidato"


def test_the_retriever_translates_the_answer_into_workflow_types():
    bridge, _ = bridge_con(
        RispostaFinta(
            structured_content={
                "results": [
                    {
                        "requirement_id": "7",
                        "statement": "The system shall do it.",
                        "source_pr_number": 6870,
                    }
                ]
            }
        )
    )
    risultati = McpMemoryRetriever(bridge).retrieve("x", pr())

    assert len(risultati) == 1
    assert risultati[0].requirement_id == "7"
    assert risultati[0].statement == "The system shall do it."
    assert risultati[0].source_pr_number == 6870


def test_an_empty_memory_gives_an_empty_tuple_not_an_error():
    bridge, _ = bridge_con(RispostaFinta(structured_content={"results": []}))
    assert McpMemoryRetriever(bridge).retrieve("x", pr()) == ()


# -- lo store -------------------------------------------------------------


def test_the_store_sends_every_field_the_memory_needs():
    risposta = RispostaFinta(structured_content={"created_at": "2026-08-31T00:00:00+00:00"})
    bridge, portal = bridge_con(risposta)
    McpAcceptedRequirementStore(bridge).store_accepted(
        pr(pr_number=6880, repository="owner/uno"), "The system shall do it."
    )

    nome, argomenti = portal.chiamate[0]
    assert nome == "store_accepted_requirement"
    assert argomenti["statement"] == "The system shall do it."
    assert argomenti["source_repository"] == "owner/uno"
    assert argomenti["source_pr_number"] == 6880
    assert argomenti["source_pr_timestamp"].startswith("2025-03-01T10:00:00")


def test_the_store_sends_the_evidence_as_title_and_body():
    """Rende la memoria leggibile da sola, senza il JSON di partenza."""

    bridge, portal = bridge_con(RispostaFinta(structured_content={"created_at": "x"}))
    McpAcceptedRequirementStore(bridge).store_accepted(
        pr(title="Titolo", body="Corpo"), "The system shall do it."
    )

    assert portal.chiamate[0][1]["evidence"] == "Titolo\n\nCorpo"


def test_an_empty_pull_request_sends_no_evidence_rather_than_whitespace():
    bridge, portal = bridge_con(RispostaFinta(structured_content={"created_at": "x"}))
    McpAcceptedRequirementStore(bridge).store_accepted(
        pr(title="", body=""), "The system shall do it."
    )

    assert portal.chiamate[0][1]["evidence"] is None


# -- il lancio del server -------------------------------------------------


def test_the_server_is_launched_with_the_interpreter_of_the_current_environment():
    """Un interprete diverso non troverebbe il pacchetto ``are``."""

    import sys

    config = McpMemorySessionConfig(db_path=Path("memoria.db"), run_id="R1")
    params = _build_server_params(config, None)
    assert params.command == sys.executable


def test_the_launch_arguments_carry_the_database_the_run_and_the_scope():
    config = McpMemorySessionConfig(
        db_path=Path("experiments/memory/m.db"),
        run_id="20260831T120000Z",
        memory_scope="all",
        max_requirements=17,
    )
    args = _build_server_params(config, None).args

    assert args[:2] == ["-m", "are.mcp_server"]
    assert "20260831T120000Z" in args
    assert "--memory-scope=all" in args
    assert "--max-requirements=17" in args


def test_the_default_scope_isolates_the_run():
    config = McpMemorySessionConfig(db_path=Path("m.db"), run_id="R1")
    assert "--memory-scope=run" in _build_server_params(config, None).args
