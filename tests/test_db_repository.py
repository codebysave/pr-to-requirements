from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from are.db import (
    IN_MEMORY,
    RelationType,
    SqliteRequirementRepository,
)
from are.input import PullRequestRecord

RUN_ID = "20260828T090000Z"


def pr(
    pr_number: int = 1,
    timestamp: str = "2026-08-26T10:00:00Z",
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


# -- scrittura e lettura -------------------------------------------------


def test_stores_and_reads_back_an_accepted_requirement(
    repository: SqliteRequirementRepository,
) -> None:
    repository.store_accepted(pr(), "The system shall export the report on request.")

    stored = repository.list_requirements()

    assert len(stored) == 1
    assert stored[0].statement == "The system shall export the report on request."
    assert stored[0].source_repository == "owner/repo"
    assert stored[0].source_pr_number == 1


def test_records_the_run_that_produced_the_requirement(
    repository: SqliteRequirementRepository,
) -> None:
    repository.store_accepted(pr(), "The system shall export the report on request.")

    assert repository.list_requirements()[0].run_id == RUN_ID


def test_stores_the_pull_request_text_as_evidence(
    repository: SqliteRequirementRepository,
) -> None:
    repository.store_accepted(pr(title="Fix export", body="It did nothing."), "A shall B.")

    evidence = repository.list_requirements()[0].evidence

    assert evidence is not None
    assert "Fix export" in evidence
    assert "It did nothing." in evidence


def test_leaves_evidence_empty_when_the_pull_request_has_no_text(
    repository: SqliteRequirementRepository,
) -> None:
    repository.store_accepted(pr(title="", body="   "), "A shall B.")

    assert repository.list_requirements()[0].evidence is None


def test_get_by_id_returns_the_requirement(repository: SqliteRequirementRepository) -> None:
    repository.store_accepted(pr(), "The system shall export the report on request.")
    identifier = repository.list_requirements()[0].id

    assert repository.get_by_id(identifier) is not None


def test_get_by_id_returns_none_for_an_unknown_identifier(
    repository: SqliteRequirementRepository,
) -> None:
    assert repository.get_by_id(999) is None


def test_counts_the_stored_requirements(repository: SqliteRequirementRepository) -> None:
    assert repository.count() == 0

    repository.store_accepted(pr(pr_number=1), "A shall B.")
    repository.store_accepted(pr(pr_number=2), "C shall D.")

    assert repository.count() == 2


def test_allows_more_than_one_requirement_for_the_same_pull_request(
    repository: SqliteRequirementRepository,
) -> None:
    # Oggi la pipeline ne produce al massimo uno, ma lo schema non lo impone:
    # un vincolo di unicità costringerebbe a una migrazione se un giorno una
    # Pull Request ne generasse due.
    repository.store_accepted(pr(pr_number=7), "The system shall do one thing.")
    repository.store_accepted(pr(pr_number=7), "The system shall do another thing.")

    assert repository.count() == 2


# -- filtri --------------------------------------------------------------


def test_filters_by_repository(repository: SqliteRequirementRepository) -> None:
    repository.store_accepted(pr(pr_number=1, repository="owner/one"), "A shall B.")
    repository.store_accepted(pr(pr_number=2, repository="owner/two"), "C shall D.")

    stored = repository.list_requirements(repository="owner/one")

    assert [item.source_pr_number for item in stored] == [1]


def test_filters_on_the_pull_request_date_not_the_insertion_date(
    repository: SqliteRequirementRepository,
) -> None:
    # Le due righe vengono inserite adesso, in quest'ordine, ma appartengono a
    # Pull Request di gennaio e marzo: il filtro deve seguire la storia del
    # progetto, non l'ordine in cui abbiamo lanciato l'esecuzione.
    repository.store_accepted(pr(pr_number=1, timestamp="2026-03-01T10:00:00Z"), "Late.")
    repository.store_accepted(pr(pr_number=2, timestamp="2026-01-01T10:00:00Z"), "Early.")

    limite = datetime(2026, 2, 1, tzinfo=timezone.utc)
    stored = repository.list_requirements(before_timestamp=limite)

    assert [item.statement for item in stored] == ["Early."]


def test_the_date_filter_is_exclusive(repository: SqliteRequirementRepository) -> None:
    momento = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    repository.store_accepted(pr(timestamp="2026-03-01T10:00:00Z"), "On the boundary.")

    assert repository.list_requirements(before_timestamp=momento) == []
    assert len(repository.list_requirements(before_timestamp=momento + timedelta(seconds=1))) == 1


def test_lists_requirements_in_chronological_order_of_pull_request(
    repository: SqliteRequirementRepository,
) -> None:
    repository.store_accepted(pr(pr_number=3, timestamp="2026-05-01T10:00:00Z"), "Third.")
    repository.store_accepted(pr(pr_number=1, timestamp="2026-01-01T10:00:00Z"), "First.")
    repository.store_accepted(pr(pr_number=2, timestamp="2026-03-01T10:00:00Z"), "Second.")

    stored = repository.list_requirements()

    assert [item.statement for item in stored] == ["First.", "Second.", "Third."]


def test_compares_dates_across_different_time_zones(
    repository: SqliteRequirementRepository,
) -> None:
    # 2026-03-01T01:00+02:00 è 2026-02-28T23:00 UTC: precede il limite anche
    # se la stringa originale, confrontata alla lettera, sembrerebbe seguirlo.
    repository.store_accepted(pr(timestamp="2026-03-01T01:00:00+02:00"), "Really February.")

    limite = datetime(2026, 3, 1, tzinfo=timezone.utc)

    assert len(repository.list_requirements(before_timestamp=limite)) == 1


def test_filters_combine(repository: SqliteRequirementRepository) -> None:
    repository.store_accepted(
        pr(pr_number=1, repository="owner/one", timestamp="2026-01-01T10:00:00Z"), "Wanted."
    )
    repository.store_accepted(
        pr(pr_number=2, repository="owner/two", timestamp="2026-01-01T10:00:00Z"), "Other repo."
    )
    repository.store_accepted(
        pr(pr_number=3, repository="owner/one", timestamp="2026-06-01T10:00:00Z"), "Too late."
    )

    stored = repository.list_requirements(
        repository="owner/one",
        before_timestamp=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )

    assert [item.statement for item in stored] == ["Wanted."]


# -- relazioni (predisposte, non alimentate dalla pipeline) ---------------


def test_saves_and_reads_a_relation(repository: SqliteRequirementRepository) -> None:
    repository.store_accepted(pr(pr_number=1), "A shall B.")
    repository.store_accepted(pr(pr_number=2), "A shall B, more or less.")
    primo, secondo = (item.id for item in repository.list_requirements())

    repository.save_relation(primo, secondo, RelationType.DUPLICATE, score=0.94)
    relations = repository.get_relations(primo)

    assert len(relations) == 1
    assert relations[0].relation_type is RelationType.DUPLICATE
    assert relations[0].score == pytest.approx(0.94)


def test_finds_a_relation_from_either_side(repository: SqliteRequirementRepository) -> None:
    repository.store_accepted(pr(pr_number=1), "A shall B.")
    repository.store_accepted(pr(pr_number=2), "C shall D.")
    primo, secondo = (item.id for item in repository.list_requirements())
    repository.save_relation(primo, secondo, RelationType.REFINES)

    assert len(repository.get_relations(secondo)) == 1


def test_saving_the_same_relation_twice_updates_it(
    repository: SqliteRequirementRepository,
) -> None:
    repository.store_accepted(pr(pr_number=1), "A shall B.")
    repository.store_accepted(pr(pr_number=2), "C shall D.")
    primo, secondo = (item.id for item in repository.list_requirements())

    repository.save_relation(primo, secondo, RelationType.OVERLAPS, score=0.5)
    repository.save_relation(primo, secondo, RelationType.OVERLAPS, score=0.8)
    relations = repository.get_relations(primo)

    assert len(relations) == 1
    assert relations[0].score == pytest.approx(0.8)


def test_rejects_a_relation_towards_an_unknown_requirement(
    repository: SqliteRequirementRepository,
) -> None:
    repository.store_accepted(pr(), "A shall B.")
    esistente = repository.list_requirements()[0].id

    with pytest.raises(sqlite3.IntegrityError):
        repository.save_relation(esistente, 999, RelationType.CONFLICTS)


# -- persistenza su file -------------------------------------------------


def test_survives_reopening_the_database_file(tmp_path) -> None:
    percorso = tmp_path / "memoria" / "requisiti.db"

    with SqliteRequirementRepository(percorso, RUN_ID) as repo:
        repo.store_accepted(pr(), "The system shall export the report on request.")

    with SqliteRequirementRepository(percorso, "un-altra-run") as repo:
        stored = repo.list_requirements()

    assert len(stored) == 1
    assert stored[0].run_id == RUN_ID


def test_creates_the_parent_directory(tmp_path) -> None:
    percorso = tmp_path / "non" / "ancora" / "esistente" / "requisiti.db"

    with SqliteRequirementRepository(percorso, RUN_ID):
        pass

    assert percorso.exists()


# -- isolamento fra esecuzioni -------------------------------------------


def test_lists_only_the_requirements_of_one_run(tmp_path) -> None:
    """Il database è condiviso: senza questo filtro le run si contaminerebbero.

    Una seconda esecuzione che vedesse i requisiti della prima partirebbe
    avvantaggiata, e il confronto fra due configurazioni non direbbe più nulla.
    """

    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, "run-uno") as repo:
        repo.store_accepted(pr(pr_number=1), "Prodotto dalla prima esecuzione.")
    with SqliteRequirementRepository(percorso, "run-due") as repo:
        repo.store_accepted(pr(pr_number=2), "Prodotto dalla seconda esecuzione.")

        della_seconda = repo.list_requirements(run_id="run-due")
        tutte = repo.list_requirements()

    assert [item.statement for item in della_seconda] == ["Prodotto dalla seconda esecuzione."]
    assert len(tutte) == 2


def test_the_run_filter_combines_with_the_others(tmp_path) -> None:
    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, "run-uno") as repo:
        repo.store_accepted(
            pr(pr_number=1, repository="owner/uno", timestamp="2026-01-01T10:00:00Z"), "Voluto."
        )
        repo.store_accepted(
            pr(pr_number=2, repository="owner/due", timestamp="2026-01-01T10:00:00Z"), "Altro repo."
        )
        repo.store_accepted(
            pr(pr_number=3, repository="owner/uno", timestamp="2026-06-01T10:00:00Z"),
            "Troppo tardi.",
        )
    with SqliteRequirementRepository(percorso, "run-due") as repo:
        repo.store_accepted(
            pr(pr_number=4, repository="owner/uno", timestamp="2026-01-01T10:00:00Z"), "Altra run."
        )

        stored = repo.list_requirements(
            repository="owner/uno",
            before_timestamp=datetime(2026, 2, 1, tzinfo=timezone.utc),
            run_id="run-uno",
        )

    assert [item.statement for item in stored] == ["Voluto."]
