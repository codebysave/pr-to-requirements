from __future__ import annotations

import logging

from are.db import IN_MEMORY, ExhaustiveRequirementRetriever, SqliteRequirementRepository
from are.input import PullRequestRecord

RUN = "20260830T120000Z"


def pr(
    pr_number: int,
    giorno: int = 15,
    repository: str = "owner/repo",
) -> PullRequestRecord:
    return PullRequestRecord.from_mapping(
        {
            "id": f"{repository.replace('/', '-')}-pr-{pr_number}",
            "repository": repository,
            "pr_number": pr_number,
            "timestamp": f"2026-03-{giorno:02d}T10:00:00Z",
            "title": "Titolo della Pull Request",
            "body": "Corpo sufficientemente lungo da superare il gate.",
        }
    )


def popolato(
    store: SqliteRequirementRepository,
    *,
    run_id: str | None = RUN,
    massimo: int = 50,
) -> ExhaustiveRequirementRetriever:
    return ExhaustiveRequirementRetriever(store, run_id=run_id, max_requirements=massimo)


# -- filtri --------------------------------------------------------------


def test_returns_the_requirements_of_earlier_pull_requests() -> None:
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        store.store_accepted(pr(1, giorno=1), "Primo requisito.")
        store.store_accepted(pr(2, giorno=5), "Secondo requisito.")

        recuperati = popolato(store).retrieve("un candidato qualsiasi", pr(3, giorno=10))

    assert [item.statement for item in recuperati] == ["Primo requisito.", "Secondo requisito."]


def test_never_returns_requirements_from_later_pull_requests() -> None:
    """La memoria disponibile è quella del momento, non quella finale."""

    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        store.store_accepted(pr(9, giorno=20), "Nato da una Pull Request successiva.")

        recuperati = popolato(store).retrieve("candidato", pr(1, giorno=10))

    assert recuperati == ()


def test_never_returns_requirements_of_another_project() -> None:
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        store.store_accepted(pr(1, giorno=1, repository="owner/altro"), "Di un altro progetto.")

        recuperati = popolato(store).retrieve("candidato", pr(2, giorno=10))

    assert recuperati == ()


def test_returns_nothing_when_the_memory_is_empty() -> None:
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        assert popolato(store).retrieve("candidato", pr(1)) == ()


# -- isolamento fra esecuzioni -------------------------------------------


def test_sees_only_the_current_run(tmp_path) -> None:
    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, "run-precedente") as store:
        store.store_accepted(pr(1, giorno=1), "Prodotto da un'altra esecuzione.")
    with SqliteRequirementRepository(percorso, RUN) as store:
        store.store_accepted(pr(2, giorno=2), "Prodotto da questa esecuzione.")

        recuperati = popolato(store).retrieve("candidato", pr(3, giorno=10))

    assert [item.statement for item in recuperati] == ["Prodotto da questa esecuzione."]


def test_sees_every_run_when_no_run_is_given(tmp_path) -> None:
    """È la modalità di una memoria che si accumula davvero nel tempo."""

    percorso = tmp_path / "memoria.db"
    with SqliteRequirementRepository(percorso, "run-precedente") as store:
        store.store_accepted(pr(1, giorno=1), "Prodotto da un'altra esecuzione.")
    with SqliteRequirementRepository(percorso, RUN) as store:
        store.store_accepted(pr(2, giorno=2), "Prodotto da questa esecuzione.")

        recuperati = popolato(store, run_id=None).retrieve("candidato", pr(3, giorno=10))

    assert len(recuperati) == 2


# -- conversione ---------------------------------------------------------


def test_carries_the_source_pull_request_number() -> None:
    """Serve al valutatore per citare il caso invece di segnalarlo genericamente."""

    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        store.store_accepted(pr(6870, giorno=1), "Il requisito.")

        recuperato = popolato(store).retrieve("candidato", pr(6879, giorno=10))[0]

    assert recuperato.source_pr_number == 6870
    assert recuperato.statement == "Il requisito."
    assert recuperato.requirement_id


# -- salvaguardia --------------------------------------------------------


def test_truncates_to_the_maximum_keeping_the_most_recent(caplog) -> None:
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        for numero in range(1, 6):
            store.store_accepted(pr(numero, giorno=numero), f"Requisito {numero}.")

        with caplog.at_level(logging.WARNING):
            recuperati = popolato(store, massimo=2).retrieve("candidato", pr(9, giorno=20))

    assert [item.statement for item in recuperati] == ["Requisito 4.", "Requisito 5."]
    assert "5 requisiti disponibili" in caplog.text


def test_does_not_truncate_when_within_the_maximum() -> None:
    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        store.store_accepted(pr(1, giorno=1), "Unico requisito.")

        assert len(popolato(store, massimo=2).retrieve("candidato", pr(2, giorno=10))) == 1


def test_an_explicit_limit_overrides_the_default() -> None:
    """Il tool MCP `search_requirements` riceve `top_k` dal chiamante."""

    with SqliteRequirementRepository(IN_MEMORY, RUN) as store:
        for numero in range(1, 4):
            store.store_accepted(pr(numero, giorno=numero), f"Requisito {numero}.")

        recuperati = popolato(store).search(repository="owner/repo", limit=1)

    assert [item.statement for item in recuperati] == ["Requisito 3."]
