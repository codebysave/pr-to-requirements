"""Client e server MCP collegati davvero, con il sottoprocesso vero.

Gli altri due file provano i due lati separatamente, con oggetti finti. Qui si
avvia il server come processo figlio via stdio e lo si interroga attraverso le
porte del workflow: è l'unico livello che esercita il ponte fra il grafo
sincrono e il client asincrono, e l'uso della connessione SQLite da un thread
diverso da quello che l'ha aperta.

Tre guasti reali sono stati scoperti qui e nessuno dei due lati, da solo,
li avrebbe visti:

* la sessione non si apriva, perché il portal entrava e usciva dal client in
  task distinti e i cancel scope di anyio non lo permettono;
* ogni chiamata a un tool falliva, perché l'SDK esegue i tool sincroni in un
  thread di lavoro mentre la connessione nasceva nel thread principale;
* la risposta non veniva letta, perché il client cercava campi con nomi
  inesistenti.

Questi test costano l'avvio di un processo Python (qualche decimo di secondo)
e non costano nulla in chiamate a pagamento: nessun modello viene contattato.
"""

from __future__ import annotations

import pytest

from are.db import SqliteRequirementRepository
from are.input import PullRequestRecord
from are.mcp_client import McpMemorySessionConfig, mcp_memory_session

RUN_ID = "20260831T120000Z"
ALTRA_RUN = "20260830T120000Z"


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
def sessione(tmp_path):
    """Le due porte del workflow, servite dal server MCP reale.

    Restituisce anche il percorso del database, per poter verificare che ciò
    che è passato dal protocollo sia arrivato davvero su disco.
    """

    percorso = tmp_path / "memoria.db"
    config = McpMemorySessionConfig(db_path=percorso, run_id=RUN_ID)
    with mcp_memory_session(config) as (retriever, store):
        yield retriever, store, percorso


def righe(percorso):
    with SqliteRequirementRepository(percorso, "lettura") as repo:
        return repo.list_requirements()


# -- la catena completa ---------------------------------------------------


def test_the_session_starts_and_stops_without_raising(sessione):
    """Il primo guasto che questi test avrebbero colto: la sessione non si
    apriva affatto, e nessuna Pull Request veniva elaborata."""

    retriever, store, _ = sessione
    assert retriever is not None and store is not None


def test_a_requirement_written_through_the_protocol_reaches_the_database(sessione):
    """Attraversa tutto: porta, client, stdio, server, repository, SQLite."""

    _, store, percorso = sessione
    store.store_accepted(pr(pr_number=6870), "The system shall export the report.")

    salvate = righe(percorso)
    assert len(salvate) == 1
    assert salvate[0].statement == "The system shall export the report."
    assert salvate[0].source_pr_number == 6870


def test_the_run_of_the_client_is_the_run_written_by_the_server(sessione):
    """Il `run_id` viaggia negli argomenti di lancio del sottoprocesso: se non
    arrivasse, le righe finirebbero sotto un'esecuzione sbagliata e i
    confronti fra configurazioni perderebbero senso."""

    _, store, percorso = sessione
    store.store_accepted(pr(), "The system shall do it.")

    assert righe(percorso)[0].run_id == RUN_ID


def test_the_evidence_survives_the_round_trip(sessione):
    _, store, percorso = sessione
    store.store_accepted(pr(title="Titolo", body="Corpo"), "The system shall do it.")

    assert righe(percorso)[0].evidence == "Titolo\n\nCorpo"


def test_what_was_written_can_be_read_back_through_the_protocol(sessione):
    """La verifica che conta per il workflow: il valutatore della Pull Request
    successiva riceve davvero ciò che la precedente ha prodotto."""

    retriever, store, _ = sessione
    store.store_accepted(
        pr(pr_number=6870, timestamp="2025-01-01T10:00:00Z"),
        "The system shall prevent arbitrary code execution.",
    )

    recuperati = retriever.retrieve(
        "un candidato", pr(pr_number=6879, timestamp="2025-06-01T10:00:00Z")
    )

    assert len(recuperati) == 1
    assert recuperati[0].statement == "The system shall prevent arbitrary code execution."
    assert recuperati[0].source_pr_number == 6870
    assert recuperati[0].requirement_id


def test_an_empty_memory_answers_with_no_results_and_no_error(sessione):
    """Prima Pull Request di un corpus: la memoria è vuota ed è normale."""

    retriever, _, _ = sessione
    assert retriever.retrieve("un candidato", pr()) == ()


# -- i tre filtri, attraverso il protocollo -------------------------------


def test_the_protocol_keeps_other_projects_out(sessione):
    retriever, store, _ = sessione
    store.store_accepted(pr(pr_number=1, repository="owner/uno"), "Requisito del primo.")

    fuori = retriever.retrieve(
        "x", pr(pr_number=2, repository="owner/due", timestamp="2025-09-01T10:00:00Z")
    )
    assert fuori == ()


def test_the_protocol_keeps_the_future_out(sessione):
    """Una Pull Request non può conoscere requisiti nati da Pull Request
    successive: la memoria ricostruita è quella della sua epoca."""

    retriever, store, _ = sessione
    store.store_accepted(pr(pr_number=2, timestamp="2025-09-01T10:00:00Z"), "Del futuro.")

    indietro = retriever.retrieve("x", pr(pr_number=1, timestamp="2025-01-01T10:00:00Z"))
    assert indietro == ()


def test_the_protocol_isolates_the_current_run(tmp_path):
    """Un database che sopravvive a più esecuzioni non deve far partire la
    seconda avvantaggiata dai requisiti della prima."""

    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, ALTRA_RUN) as precedente:
        precedente.store_accepted(
            pr(pr_number=9, timestamp="2025-01-01T10:00:00Z"), "Di un'altra esecuzione."
        )

    config = McpMemorySessionConfig(db_path=percorso, run_id=RUN_ID)
    with mcp_memory_session(config) as (retriever, _):
        assert retriever.retrieve("x", pr(pr_number=1, timestamp="2025-06-01T10:00:00Z")) == ()


def test_the_all_scope_lets_the_memory_span_executions(tmp_path):
    """`--memory-scope all`: la memoria si accumula davvero nel tempo."""

    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, ALTRA_RUN) as precedente:
        precedente.store_accepted(
            pr(pr_number=9, timestamp="2025-01-01T10:00:00Z"), "Di un'altra esecuzione."
        )

    config = McpMemorySessionConfig(db_path=percorso, run_id=RUN_ID, memory_scope="all")
    with mcp_memory_session(config) as (retriever, _):
        recuperati = retriever.retrieve("x", pr(pr_number=1, timestamp="2025-06-01T10:00:00Z"))

    assert [r.statement for r in recuperati] == ["Di un'altra esecuzione."]


def test_the_maximum_is_carried_to_the_server(tmp_path):
    """La salvaguardia sul numero di requisiti viaggia negli argomenti di
    lancio: se non arrivasse, il server userebbe il proprio valore
    predefinito e il limite configurato non avrebbe effetto."""

    percorso = tmp_path / "memoria.db"
    config = McpMemorySessionConfig(db_path=percorso, run_id=RUN_ID, max_requirements=2)
    with mcp_memory_session(config) as (retriever, store):
        for numero in range(1, 5):
            store.store_accepted(
                pr(pr_number=numero, timestamp=f"2025-0{numero}-01T10:00:00Z"), f"R{numero}."
            )
        recuperati = retriever.retrieve("x", pr(pr_number=9, timestamp="2025-12-01T10:00:00Z"))

    assert len(recuperati) == 2


# -- il ciclo di vita -----------------------------------------------------


def test_one_subprocess_serves_the_whole_run(sessione):
    """La sessione resta viva per tutte le Pull Request: riavviare il processo
    a ogni chiamata costerebbe centinaia di millisecondi ciascuna."""

    retriever, store, _ = sessione
    for numero in range(1, 4):
        store.store_accepted(
            pr(pr_number=numero, timestamp=f"2025-0{numero}-01T10:00:00Z"), f"R{numero}."
        )
        retriever.retrieve("x", pr(pr_number=9, timestamp="2025-12-01T10:00:00Z"))

    recuperati = retriever.retrieve("x", pr(pr_number=9, timestamp="2025-12-01T10:00:00Z"))
    assert [r.statement for r in recuperati] == ["R1.", "R2.", "R3."]


def cause(errore: BaseException) -> list[BaseException]:
    """Appiattisce i gruppi di eccezioni annidati in un elenco di cause."""

    interne = getattr(errore, "exceptions", None)
    if not interne:
        return [errore]
    return [causa for interna in interne for causa in cause(interna)]


def test_an_exception_inside_the_session_still_commits_what_was_written(tmp_path):
    """Un errore del workflow non deve lasciare un processo orfano né perdere
    i requisiti già scritti.

    L'eccezione originale **non** arriva nuda al chiamante: il task group di
    anyio che gestisce il sottoprocesso la avvolge in un ``ExceptionGroup``.
    Resta comunque un ``Exception``, quindi il Runner continua a catturarla,
    ma chi legge il messaggio vede il gruppo e non la causa: per risalire
    all'errore vero bisogna scorrere ``exceptions``.
    """

    config = McpMemorySessionConfig(db_path=tmp_path / "memoria.db", run_id=RUN_ID)

    with pytest.raises(Exception) as errore:
        with mcp_memory_session(config) as (_, store):
            store.store_accepted(pr(), "The system shall do it.")
            raise ZeroDivisionError("guasto simulato del workflow")

    tipi = [type(causa) for causa in cause(errore.value)]
    assert ZeroDivisionError in tipi, f"causa originale non ritrovata fra {tipi}"
    assert len(righe(tmp_path / "memoria.db")) == 1
