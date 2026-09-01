"""Saltare le Pull Request già elaborate, senza chiamare alcun modello.

Il controllo è una lettura del database: si guarda se quel progetto e quel
numero risultano già elaborati, e in caso si salta. Nessun giudizio, nessuna
chiamata a pagamento — che è il punto: rielaborare una Pull Request già vista
costa da due a sei chiamate per riscoprire la stessa cosa.

La registrazione riguarda **ogni** esito, non solo le accettazioni. La tabella
dei requisiti conserva soltanto i successi: una Pull Request rifiutata o non
estraibile non vi lascia traccia, e senza una registrazione a parte verrebbe
rielaborata per sempre — proprio quella che conviene di più saltare, perché non
produce nulla.
"""

from __future__ import annotations

import pytest

from are.db import IN_MEMORY, SqliteRequirementRepository
from are.input import PullRequestRecord

RUN_ID = "20260901T100000Z"
ALTRA_RUN = "20260831T100000Z"


def pr(
    pr_number: int = 6870,
    repository: str = "owner/repo",
    timestamp: str = "2025-01-01T10:00:00Z",
) -> PullRequestRecord:
    return PullRequestRecord.from_mapping(
        {
            "id": f"{repository.replace('/', '-')}-pr-{pr_number}",
            "repository": repository,
            "pr_number": pr_number,
            "timestamp": timestamp,
            "title": "Fix the export",
            "body": "The export button did nothing.",
        }
    )


@pytest.fixture
def repository() -> SqliteRequirementRepository:
    with SqliteRequirementRepository(IN_MEMORY, RUN_ID) as repo:
        yield repo


# -- la registrazione -----------------------------------------------------


@pytest.mark.parametrize(
    "esito", ["ACCEPTED", "REJECTED", "NOT_EXTRACTABLE", "FAILED_VALIDATION"]
)
def test_every_outcome_is_recorded_not_only_the_accepted_one(repository, esito: str):
    """È la ragione per cui questa tabella esiste: senza, una Pull Request che
    non produce requisiti verrebbe rielaborata a ogni esecuzione."""

    repository.record_processed(pr(6875), esito)

    assert repository.processed_pull_requests("owner/repo") == {6875: esito}


def test_a_project_never_seen_gives_an_empty_map(repository):
    repository.record_processed(pr(6870, repository="owner/uno"), "ACCEPTED")

    assert repository.processed_pull_requests("owner/due") == {}


def test_projects_do_not_mix(repository):
    """Lo stesso numero su progetti diversi sono Pull Request diverse."""

    repository.record_processed(pr(1, repository="owner/uno"), "ACCEPTED")
    repository.record_processed(pr(1, repository="owner/due"), "REJECTED")

    assert repository.processed_pull_requests("owner/uno") == {1: "ACCEPTED"}
    assert repository.processed_pull_requests("owner/due") == {1: "REJECTED"}


def test_processing_the_same_pull_request_again_updates_the_row(repository):
    """Interessa sapere se è stata vista, non quante volte: una riga sola,
    con l'esito più recente."""

    repository.record_processed(pr(6870), "REJECTED")
    repository.record_processed(pr(6870), "ACCEPTED")

    assert repository.processed_pull_requests("owner/repo") == {6870: "ACCEPTED"}


def test_the_record_survives_a_different_execution(tmp_path):
    """Il filtro deve funzionare fra esecuzioni: è tutto il suo scopo.

    Serve un database su file: due connessioni a ``:memory:`` aprirebbero due
    database distinti, e il test passerebbe senza aver provato nulla.
    """

    condiviso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(condiviso, ALTRA_RUN) as altra:
        altra.record_processed(pr(6870), "ACCEPTED")

    with SqliteRequirementRepository(condiviso, RUN_ID) as mia:
        assert mia.processed_pull_requests("owner/repo") == {6870: "ACCEPTED"}


def test_recording_does_not_create_a_requirement(repository):
    """Sono due cose distinte: una Pull Request può risultare elaborata senza
    aver prodotto nulla."""

    repository.record_processed(pr(6875), "NOT_EXTRACTABLE")

    assert repository.count() == 0
    assert repository.processed_pull_requests("owner/repo") == {6875: "NOT_EXTRACTABLE"}


def test_an_accepted_requirement_alone_does_not_mark_it_processed(repository):
    """La scrittura del requisito e la registrazione sono separate: la prima
    avviene nel grafo, la seconda a esecuzione conclusa."""

    repository.store_accepted(pr(6870), "The system shall export the report.")

    assert repository.count() == 1
    assert repository.processed_pull_requests("owner/repo") == {}


# -- il filtro ------------------------------------------------------------


def test_a_new_pull_request_is_not_skipped(tmp_path):
    from are.__main__ import _split_already_processed

    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        repo.record_processed(pr(6870), "ACCEPTED")

    nuove, saltate = _split_already_processed([pr(6879)], percorso)

    assert [record.pr_number for record in nuove] == [6879]
    assert saltate == []


def test_an_already_processed_pull_request_is_skipped_with_its_outcome(tmp_path):
    from are.__main__ import _split_already_processed

    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        repo.record_processed(pr(6875), "NOT_EXTRACTABLE")

    nuove, saltate = _split_already_processed([pr(6875)], percorso)

    assert nuove == []
    assert [(record.pr_number, esito) for record, esito in saltate] == [
        (6875, "NOT_EXTRACTABLE")
    ]


def test_a_missing_database_skips_nothing(tmp_path):
    """Un progetto mai visto non ha un file: non è un errore, è il primo
    avvio."""

    from are.__main__ import _split_already_processed

    nuove, saltate = _split_already_processed([pr(6870)], tmp_path / "inesistente.db")

    assert len(nuove) == 1
    assert saltate == []


def test_the_order_of_the_new_pull_requests_is_preserved(tmp_path):
    """Il Runner riordina per data, ma il filtro non deve rimescolare nulla
    per conto suo."""

    from are.__main__ import _split_already_processed

    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        repo.record_processed(pr(2), "ACCEPTED")

    elenco = [pr(1), pr(2), pr(3), pr(4)]
    nuove, saltate = _split_already_processed(elenco, percorso)

    assert [record.pr_number for record in nuove] == [1, 3, 4]
    assert [record.pr_number for record, _ in saltate] == [2]


def test_pull_requests_of_another_project_are_not_skipped(tmp_path):
    from are.__main__ import _split_already_processed

    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        repo.record_processed(pr(6870, repository="owner/uno"), "ACCEPTED")

    nuove, saltate = _split_already_processed([pr(6870, repository="owner/due")], percorso)

    assert len(nuove) == 1
    assert saltate == []


def test_a_mixed_corpus_is_split_by_project(tmp_path):
    from are.__main__ import _split_already_processed

    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        repo.record_processed(pr(1, repository="owner/uno"), "ACCEPTED")
        repo.record_processed(pr(1, repository="owner/due"), "REJECTED")

    elenco = [
        pr(1, repository="owner/uno"),
        pr(1, repository="owner/due"),
        pr(2, repository="owner/uno"),
    ]
    nuove, saltate = _split_already_processed(elenco, percorso)

    assert [(r.repository, r.pr_number) for r in nuove] == [("owner/uno", 2)]
    assert len(saltate) == 2
