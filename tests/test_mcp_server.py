"""Il server MCP in isolamento, senza sottoprocesso e senza modelli.

I tool vengono invocati direttamente sull'oggetto server, con un database in
memoria: è il livello che verifica il contratto del protocollo e i tre filtri
del recupero, senza pagare l'avvio di un processo.

Il contratto verificato qui non è un dettaglio formale. Un tool che non
dichiara il proprio tipo di ritorno non produce alcuno schema di output, e
l'SDK consegna la risposta come testo invece che come dato strutturato: il
client la considera mancante e la Pull Request si perde.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from are.db import IN_MEMORY, ExhaustiveRequirementRetriever, SqliteRequirementRepository
from are.input import PullRequestRecord
from are.mcp_server import create_server
from are.mcp_server.server import _parse_iso_timestamp

RUN_ID = "20260831T090000Z"
ALTRA_RUN = "20260830T090000Z"


def pr(
    pr_number: int = 1,
    timestamp: str = "2025-03-01T10:00:00Z",
    repository: str = "owner/repo",
    title: str = "Fix the report export",
    body: str = "The export button did nothing. This restores the download.",
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


@pytest.fixture
def repository() -> SqliteRequirementRepository:
    with SqliteRequirementRepository(IN_MEMORY, RUN_ID) as repo:
        yield repo


def build(repository: SqliteRequirementRepository, run_id: str | None = RUN_ID):
    """Server con retriever e repository iniettati, come in produzione."""

    retriever = ExhaustiveRequirementRetriever(repository, run_id=run_id)
    return create_server(repository, retriever)


def chiama(server, nome: str, argomenti: dict[str, Any]) -> dict[str, Any]:
    """Invoca un tool e restituisce il contenuto strutturato della risposta."""

    risultato = asyncio.run(server.call_tool(nome, argomenti))
    assert not risultato.is_error, f"il tool {nome} ha fallito: {risultato.content}"
    assert risultato.structured_content is not None, (
        f"il tool {nome} non ha prodotto structured_content: il tipo di ritorno "
        "dichiarato è ciò che fa generare all'SDK lo schema di output"
    )
    return risultato.structured_content


def cerca(server, **argomenti: Any) -> list[dict[str, Any]]:
    return chiama(server, "search_requirements", argomenti)["results"]


def salva(server, record: PullRequestRecord, statement: str) -> dict[str, Any]:
    return chiama(
        server,
        "store_accepted_requirement",
        {
            "statement": statement,
            "source_repository": record.repository,
            "source_pr_number": record.pr_number,
            "source_pr_timestamp": record.timestamp.isoformat(),
            "evidence": f"{record.title}\n\n{record.body}",
        },
    )


# -- il contratto dei tool -----------------------------------------------


def test_the_server_declares_exactly_the_two_tools_of_the_mvp(repository):
    """`get_requirement` e le relazioni restano fuori: nessuno le usa."""

    server = build(repository)
    nomi = {tool.name for tool in asyncio.run(server.list_tools())}
    assert nomi == {"search_requirements", "store_accepted_requirement"}


def test_both_tools_declare_an_output_schema(repository):
    """Senza tipo di ritorno l'SDK non genera lo schema e la risposta arriva
    come semplice testo: il client la vede come mancante."""

    server = build(repository)
    for tool in asyncio.run(server.list_tools()):
        assert tool.output_schema, f"il tool {tool.name} non dichiara uno schema di output"


def test_a_tool_answers_with_structured_content_not_only_text(repository):
    """È la forma che il client legge. Il testo resta come rappresentazione
    di cortesia, ma non è ciò su cui il workflow si basa."""

    server = build(repository)
    risultato = asyncio.run(
        server.call_tool("search_requirements", {"repository_id": "owner/repo"})
    )
    assert risultato.structured_content == {"results": []}


def test_an_empty_memory_is_a_success_not_an_error(repository):
    """Una memoria vuota è la condizione normale della prima Pull Request."""

    server = build(repository)
    assert cerca(server, repository_id="owner/repo") == []


# -- scrittura ------------------------------------------------------------


def test_the_write_tool_persists_the_requirement(repository):
    server = build(repository)
    salva(server, pr(pr_number=7), "The system shall export the report.")

    righe = repository.list_requirements()
    assert len(righe) == 1
    assert righe[0].statement == "The system shall export the report."
    assert righe[0].source_pr_number == 7


def test_the_write_tool_returns_the_creation_instant(repository):
    """Opzione A del MVP: si restituisce `created_at`, non l'id interno."""

    esito = salva(server := build(repository), pr(), "The system shall do it.")
    assert set(esito) == {"created_at"}
    assert esito["created_at"].endswith("+00:00")
    del server


def test_the_write_tool_records_the_run_that_produced_the_row(repository):
    """Il `run_id` arriva dal lancio del server, non dai parametri del tool:
    un client non può attribuire una riga a un'altra esecuzione."""

    salva(build(repository), pr(), "The system shall do it.")
    assert repository.list_requirements()[0].run_id == RUN_ID


def test_the_write_tool_keeps_the_evidence(repository):
    """Rende la memoria leggibile da sola, senza il JSON di partenza."""

    salva(build(repository), pr(title="Titolo", body="Corpo"), "The system shall do it.")
    assert repository.list_requirements()[0].evidence == "Titolo\n\nCorpo"


# -- i tre filtri del recupero -------------------------------------------


def test_the_search_is_restricted_to_the_same_repository(repository):
    """Requisiti di un altro progetto non devono comparire: parlano di un
    sistema diverso."""

    server = build(repository)
    salva(server, pr(pr_number=1, repository="owner/uno"), "Requisito del primo.")
    salva(server, pr(pr_number=2, repository="owner/due"), "Requisito del secondo.")

    risultati = cerca(server, repository_id="owner/uno", before_timestamp="2026-01-01T00:00:00Z")
    assert [r["statement"] for r in risultati] == ["Requisito del primo."]


def test_the_search_never_returns_requirements_from_the_future(repository):
    """La memoria ricostruita è quella disponibile all'epoca della Pull
    Request in esame, non quella di oggi."""

    server = build(repository)
    salva(server, pr(pr_number=1, timestamp="2025-01-01T10:00:00Z"), "Precedente.")
    salva(server, pr(pr_number=2, timestamp="2025-09-01T10:00:00Z"), "Successivo.")

    risultati = cerca(server, repository_id="owner/repo", before_timestamp="2025-06-01T10:00:00Z")
    assert [r["statement"] for r in risultati] == ["Precedente."]


def test_the_date_filter_is_exclusive(repository):
    """Una Pull Request non vede il requisito nato da se stessa."""

    server = build(repository)
    salva(server, pr(timestamp="2025-03-01T10:00:00Z"), "Sul confine.")

    assert cerca(server, repository_id="owner/repo", before_timestamp="2025-03-01T10:00:00Z") == []


def test_the_search_is_isolated_to_the_run_of_the_server(tmp_path):
    """Il database è condiviso fra esecuzioni: senza questo filtro una run
    partirebbe avvantaggiata dai requisiti di quelle precedenti.

    Serve un database su file: due connessioni a ``:memory:`` aprirebbero due
    database distinti, e il test passerebbe senza aver provato l'isolamento.
    """

    condiviso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(condiviso, ALTRA_RUN) as altra:
        altra.store_accepted(pr(pr_number=9, timestamp="2025-01-01T10:00:00Z"), "Di un'altra run.")

    with SqliteRequirementRepository(condiviso, RUN_ID) as mia:
        assert mia.count() == 1, "le due connessioni devono vedere lo stesso database"
        salva(build(mia), pr(pr_number=1, timestamp="2025-02-01T10:00:00Z"), "Di questa run.")

        risultati = cerca(
            build(mia, run_id=RUN_ID),
            repository_id="owner/repo",
            before_timestamp="2026-01-01T00:00:00Z",
        )
        assert [r["statement"] for r in risultati] == ["Di questa run."]


def test_without_a_run_filter_the_memory_spans_every_execution(tmp_path):
    """È il comportamento di `--memory-scope all`: una memoria che si accumula
    davvero nel tempo."""

    condiviso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(condiviso, ALTRA_RUN) as altra:
        altra.store_accepted(pr(pr_number=9, timestamp="2025-01-01T10:00:00Z"), "Di un'altra run.")

    with SqliteRequirementRepository(condiviso, RUN_ID) as mia:
        salva(build(mia), pr(pr_number=1, timestamp="2025-02-01T10:00:00Z"), "Di questa run.")

        risultati = cerca(
            build(mia, run_id=None),
            repository_id="owner/repo",
            before_timestamp="2026-01-01T00:00:00Z",
        )
        assert len(risultati) == 2


def test_the_limit_caps_the_number_of_results(repository):
    """Salvaguardia contro un archivio cresciuto oltre le previsioni, non un
    top-k: la ricerca resta esaustiva entro i filtri."""

    server = build(repository)
    for numero in range(1, 6):
        salva(server, pr(pr_number=numero, timestamp=f"2025-0{numero}-01T10:00:00Z"), f"R{numero}.")

    assert len(cerca(server, repository_id="owner/repo", limit=2)) == 2


def test_the_candidate_text_is_accepted_and_does_not_change_the_results(repository):
    """Strada B: il campo esiste nel contratto per un futuro retriever
    semantico, ma quello esaustivo di oggi non lo usa."""

    server = build(repository)
    salva(server, pr(pr_number=1, timestamp="2025-01-01T10:00:00Z"), "Unico requisito.")

    senza = cerca(server, repository_id="owner/repo", before_timestamp="2026-01-01T00:00:00Z")
    con = cerca(
        server,
        candidate_text="qualcosa di completamente diverso",
        repository_id="owner/repo",
        before_timestamp="2026-01-01T00:00:00Z",
    )
    assert senza == con


# -- errori ---------------------------------------------------------------


def test_a_naive_timestamp_is_refused(repository):
    """La memoria confronta stringhe ISO normalizzate a UTC: una data senza
    fuso orario renderebbe il confronto ambiguo."""

    with pytest.raises(ValueError, match="senza fuso orario"):
        _parse_iso_timestamp("2025-03-01T10:00:00")


def test_the_z_suffix_and_an_explicit_offset_are_both_accepted(repository):
    assert _parse_iso_timestamp("2025-03-01T10:00:00Z").utcoffset().total_seconds() == 0
    assert _parse_iso_timestamp("2025-03-01T12:00:00+02:00").utcoffset().total_seconds() == 7200


def test_a_failing_tool_raises_instead_of_answering_with_an_empty_result(repository):
    """Un argomento non valido non deve produrre una lista vuota, che il
    workflow leggerebbe come "nessun requisito storico".

    Invocato in-process il tool propaga l'eccezione; è il livello di
    protocollo a tradurla nel campo ``is_error`` della risposta, e quella
    traduzione è verificata dai test di integrazione.
    """

    server = build(repository)
    with pytest.raises(Exception, match="search_requirements"):
        asyncio.run(
            server.call_tool(
                "search_requirements",
                {"repository_id": "owner/repo", "before_timestamp": "non-una-data"},
            )
        )


def test_the_structured_answer_and_the_text_answer_agree(repository):
    """Il testo resta una rappresentazione della stessa risposta: se i due
    divergessero, il client e un lettore umano vedrebbero cose diverse."""

    server = build(repository)
    salva(server, pr(pr_number=1, timestamp="2025-01-01T10:00:00Z"), "Un requisito.")

    risultato = asyncio.run(
        server.call_tool(
            "search_requirements",
            {"repository_id": "owner/repo", "before_timestamp": "2026-01-01T00:00:00Z"},
        )
    )
    testo = next(blocco.text for blocco in risultato.content if getattr(blocco, "text", None))
    assert json.loads(testo) == risultato.structured_content
