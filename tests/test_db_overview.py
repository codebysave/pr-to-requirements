"""La vista di lettura e la migrazione dello schema.

`requirements_overview` esiste per un motivo di leggibilità: sfogliando la
tabella `requirements` non c'è alcun segnale che una riga sia in relazione con
altre, e bisogna sapere di dover guardare altrove.

La relazione resta però un fatto fra **due** requisiti, quindi non può diventare
una colonna di quella tabella: si perderebbe con chi, quante, e perché. Un
requisito di questa run ne ha tre contemporaneamente. La vista riassume senza
duplicare — viene calcolata a ogni interrogazione, quindi non può disallinearsi.
"""

from __future__ import annotations

import sqlite3

import pytest

from are.agents.state import RelationClaim, RelationKind
from are.db import IN_MEMORY, RelationType, SqliteRequirementRepository
from are.input import PullRequestRecord

RUN_ID = "20260831T210000Z"


def pr(pr_number: int = 6870, timestamp: str = "2025-01-01T10:00:00Z") -> PullRequestRecord:
    return PullRequestRecord.from_mapping(
        {
            "id": f"owner-repo-pr-{pr_number}",
            "repository": "owner/repo",
            "pr_number": pr_number,
            "timestamp": timestamp,
            "title": "Fix the export",
            "body": "The export button did nothing.",
        }
    )


def claim(target_id: int, target_pr: int, kind: RelationKind, reason: str = "") -> RelationClaim:
    return RelationClaim(
        kind=kind,
        target_requirement_id=str(target_id),
        target_pr_number=target_pr,
        reason=reason,
    )


@pytest.fixture
def repository() -> SqliteRequirementRepository:
    with SqliteRequirementRepository(IN_MEMORY, RUN_ID) as repo:
        yield repo


def overview(repository: SqliteRequirementRepository) -> list[sqlite3.Row]:
    return list(repository._connection.execute("SELECT * FROM requirements_overview"))


# -- la vista -------------------------------------------------------------


def test_the_view_exists_as_soon_as_the_database_is_opened(repository):
    """Deve comparire nell'elenco di DB Browser senza doverla creare a mano."""

    viste = {
        riga["name"]
        for riga in repository._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view'"
        )
    }
    assert "requirements_overview" in viste


def test_a_requirement_without_relations_shows_an_empty_column(repository):
    """È il caso della maggioranza delle righe: la colonna vuota dice
    «nessuna eccezione da rivedere»."""

    repository.store_accepted(pr(), "The system shall export the report.")

    righe = overview(repository)
    assert len(righe) == 1
    assert righe[0]["relations"] == ""


def test_a_relation_appears_with_its_type_and_the_pull_request(repository):
    repository.store_accepted(pr(6870, "2025-01-01T10:00:00Z"), "Il primo.")
    primo = repository.list_requirements()[0]
    repository.store_accepted(
        pr(6879, "2025-06-01T10:00:00Z"),
        "Il secondo.",
        (claim(primo.id, 6870, RelationKind.DUPLICATE),),
    )

    seconda = overview(repository)[1]
    assert "DUPLICATE" in seconda["relations"]
    assert "PR #6870" in seconda["relations"]


def test_the_reason_is_shown_next_to_the_relation(repository):
    """Senza il perché, la vista direbbe che due requisiti sono in relazione
    ma non permetterebbe di decidere nulla: bisognerebbe cercare il report."""

    repository.store_accepted(pr(6870, "2025-01-01T10:00:00Z"), "Il primo.")
    primo = repository.list_requirements()[0]
    repository.store_accepted(
        pr(6879, "2025-06-01T10:00:00Z"),
        "Il secondo.",
        (claim(primo.id, 6870, RelationKind.CONFLICTS, "opposite obligations"),),
    )

    assert "opposite obligations" in overview(repository)[1]["relations"]


def test_several_relations_are_summarised_on_one_line(repository):
    """Il caso che rende impossibile una colonna sulla tabella: un requisito
    di una run reale ne aveva tre contemporaneamente."""

    for numero, mese in ((6869, "01"), (6870, "02"), (6879, "03")):
        repository.store_accepted(pr(numero, f"2025-{mese}-01T10:00:00Z"), f"R{numero}.")
    esistenti = repository.list_requirements()

    repository.store_accepted(
        pr(6880, "2025-06-01T10:00:00Z"),
        "Il quarto.",
        tuple(
            claim(r.id, r.source_pr_number, RelationKind.OVERLAPS) for r in esistenti
        ),
    )

    riassunto = overview(repository)[-1]["relations"]
    for numero in (6869, 6870, 6879):
        assert f"PR #{numero}" in riassunto


def test_the_view_orders_the_relations_by_pull_request(repository):
    """Un ordine stabile rende confrontabili due letture della stessa riga."""

    for numero, mese in ((6879, "01"), (6869, "02"), (6870, "03")):
        repository.store_accepted(pr(numero, f"2025-{mese}-01T10:00:00Z"), f"R{numero}.")
    esistenti = repository.list_requirements()

    repository.store_accepted(
        pr(6880, "2025-06-01T10:00:00Z"),
        "Il quarto.",
        tuple(claim(r.id, r.source_pr_number, RelationKind.OVERLAPS) for r in esistenti),
    )

    riassunto = overview(repository)[-1]["relations"]
    posizioni = [riassunto.index(f"PR #{n}") for n in (6869, 6870, 6879)]
    assert posizioni == sorted(posizioni)


def test_the_view_carries_the_columns_needed_to_read_a_row(repository):
    repository.store_accepted(pr(), "The system shall export the report.")

    riga = overview(repository)[0]
    for colonna in ("id", "source_pr_number", "statement", "relations", "run_id"):
        assert colonna in riga.keys()


def test_the_view_reflects_a_relation_added_afterwards(repository):
    """Non duplica i dati: è calcolata a ogni interrogazione, quindi non può
    restare indietro rispetto alle tabelle."""

    repository.store_accepted(pr(6870, "2025-01-01T10:00:00Z"), "Il primo.")
    repository.store_accepted(pr(6879, "2025-06-01T10:00:00Z"), "Il secondo.")
    primo, secondo = repository.list_requirements()

    assert overview(repository)[1]["relations"] == ""

    repository.save_relation(secondo.id, primo.id, RelationType.DUPLICATE)
    assert "DUPLICATE" in overview(repository)[1]["relations"]


# -- la migrazione --------------------------------------------------------


def vecchio_schema(percorso) -> None:
    """Ricostruisce lo schema precedente: nessuna colonna `reason`, nessuna vista."""

    conn = sqlite3.connect(percorso)
    conn.executescript(
        """
        CREATE TABLE requirements (
            id INTEGER PRIMARY KEY, statement TEXT NOT NULL,
            source_repository TEXT NOT NULL, source_pr_number INTEGER NOT NULL,
            source_pr_timestamp TEXT NOT NULL, evidence TEXT,
            created_at TEXT NOT NULL, embedding BLOB, embedding_model TEXT,
            run_id TEXT NOT NULL
        );
        CREATE TABLE requirement_relations (
            source_requirement_id INTEGER NOT NULL REFERENCES requirements (id),
            target_requirement_id INTEGER NOT NULL REFERENCES requirements (id),
            relation_type TEXT NOT NULL CHECK (relation_type IN (
                'DUPLICATE', 'OVERLAPS', 'REFINES', 'SUPERSEDES', 'CONFLICTS')),
            score REAL, created_at TEXT NOT NULL,
            PRIMARY KEY (source_requirement_id, target_requirement_id, relation_type)
        );
        INSERT INTO requirements (statement, source_repository, source_pr_number,
            source_pr_timestamp, created_at, run_id)
        VALUES ('Vecchio requisito.', 'owner/repo', 6869,
            '2025-01-01T10:00:00+00:00', '2026-08-30T10:00:00+00:00', 'RUN-VECCHIA');
        """
    )
    conn.commit()
    conn.close()


def test_an_older_database_gains_the_missing_column(tmp_path):
    """`CREATE TABLE IF NOT EXISTS` non modifica una tabella esistente: senza
    migrazione la scrittura di una relazione fallirebbe su un database aperto
    da una versione precedente."""

    percorso = tmp_path / "vecchio.db"
    vecchio_schema(percorso)

    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        colonne = {
            riga["name"]
            for riga in repo._connection.execute("PRAGMA table_info(requirement_relations)")
        }
        assert "reason" in colonne


def test_an_older_database_keeps_its_rows(tmp_path):
    """La migrazione aggiunge, non ricostruisce: i requisiti già raccolti sono
    dati sperimentali e non vanno persi."""

    percorso = tmp_path / "vecchio.db"
    vecchio_schema(percorso)

    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        assert repo.count() == 1
        assert repo.list_requirements()[0].statement == "Vecchio requisito."


def test_an_older_database_gains_the_view(tmp_path):
    percorso = tmp_path / "vecchio.db"
    vecchio_schema(percorso)

    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        assert len(overview(repo)) == 1


def test_a_relation_can_be_written_on_a_migrated_database(tmp_path):
    """La verifica che conta: la migrazione serve a questo."""

    percorso = tmp_path / "vecchio.db"
    vecchio_schema(percorso)

    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        vecchio = repo.list_requirements()[0]
        repo.store_accepted(
            pr(6879, "2025-06-01T10:00:00Z"),
            "Il nuovo.",
            (claim(vecchio.id, 6869, RelationKind.SUPERSEDES, "replaces it"),),
        )

        assert "SUPERSEDES" in overview(repo)[1]["relations"]
        assert "replaces it" in overview(repo)[1]["relations"]


def test_opening_the_same_database_twice_is_harmless(tmp_path):
    """Ogni esecuzione riapre il database: la migrazione deve poter girare
    molte volte senza effetti."""

    percorso = tmp_path / "memoria.db"
    for _ in range(3):
        with SqliteRequirementRepository(percorso, RUN_ID) as repo:
            repo.store_accepted(pr(), "The system shall export the report.")

    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        assert repo.count() == 3
        assert len(overview(repo)) == 3
