from __future__ import annotations

import pytest

from are.__main__ import (
    MEMORY_SCOPE_ALL,
    MEMORY_SCOPE_RUN,
    _build_retriever,
    _default_memory_path,
    _parse_args,
)
from are.agents import WorkflowConfig
from are.db import IN_MEMORY, SqliteRequirementRepository

RUN = "20260830T150000Z"


def store() -> SqliteRequirementRepository:
    return SqliteRequirementRepository(IN_MEMORY, RUN)


# -- opzione da riga di comando ------------------------------------------


def test_the_default_scope_isolates_the_run() -> None:
    """È il comportamento che rende confrontabili due esecuzioni."""

    args = _parse_args(["--input", "x.json"])

    assert args.memory_scope == MEMORY_SCOPE_RUN


def test_the_scope_can_be_widened_to_every_run() -> None:
    args = _parse_args(["--input", "x.json", "--memory-scope", "all"])

    assert args.memory_scope == MEMORY_SCOPE_ALL


def test_an_unknown_scope_is_rejected() -> None:
    with pytest.raises(SystemExit):
        _parse_args(["--input", "x.json", "--memory-scope", "qualsiasi"])


# -- costruzione del retriever -------------------------------------------


def test_the_run_scope_binds_the_retriever_to_this_execution() -> None:
    with store() as memory:
        retriever = _build_retriever(memory, RUN, MEMORY_SCOPE_RUN, WorkflowConfig())

    assert retriever.run_id == RUN


def test_the_all_scope_leaves_the_retriever_free_to_see_every_run() -> None:
    with store() as memory:
        retriever = _build_retriever(memory, RUN, MEMORY_SCOPE_ALL, WorkflowConfig())

    assert retriever.run_id is None


def test_the_limit_comes_from_the_workflow_configuration() -> None:
    with store() as memory:
        retriever = _build_retriever(
            memory, RUN, MEMORY_SCOPE_RUN, WorkflowConfig(max_memory_requirements=7)
        )

    assert retriever.max_requirements == 7


# -- percorso del database -----------------------------------------------


def test_the_default_database_is_a_single_shared_file() -> None:
    """Un file solo: l'isolamento fra esecuzioni è nella colonna, non nel nome."""

    percorso = _default_memory_path()

    assert percorso.name == "pr4requirements.db"
    assert percorso.parent.as_posix() == "experiments/memory"
