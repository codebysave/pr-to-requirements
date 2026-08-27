from __future__ import annotations

import logging

import pytest

from are.agents import DeterministicExtractabilityChecker, Extractability
from are.input import PullRequestRecord

TESTO_LUNGO = (
    "Users could not download their reports, and the export button did nothing. "
    "This restores the download."
)


def pr(title: str = "Fix the report export", body: str = TESTO_LUNGO) -> PullRequestRecord:
    return PullRequestRecord.from_mapping(
        {
            "id": "owner-repo-pr-1",
            "repository": "owner/repo",
            "pr_number": 1,
            "timestamp": "2026-08-26T10:00:00Z",
            "title": title,
            "body": body,
        }
    )


def test_accepts_a_pull_request_with_enough_text() -> None:
    result = DeterministicExtractabilityChecker().check(pr())

    assert result.decision is Extractability.EXTRACTABLE


@pytest.mark.parametrize("body", ["", "   ", "\n\t  \n"])
def test_rejects_an_empty_body(body: str) -> None:
    result = DeterministicExtractabilityChecker().check(pr(body=body))

    assert result.decision is Extractability.NOT_EXTRACTABLE
    assert "vuoto" in result.reason


def test_rejects_text_shorter_than_the_threshold() -> None:
    result = DeterministicExtractabilityChecker(min_evidence_characters=50).check(
        pr(title="Bump version", body="Routine update.")
    )

    assert result.decision is Extractability.NOT_EXTRACTABLE
    # La motivazione deve dire quanti caratteri c'erano e quanti ne servivano.
    assert "27" in result.reason
    assert "50" in result.reason


def test_counts_title_and_body_together() -> None:
    checker = DeterministicExtractabilityChecker(min_evidence_characters=30)
    corto = "Short body here."  # 16 caratteri

    solo_corpo = checker.check(pr(title="", body=corto))
    con_titolo = checker.check(pr(title="A reasonably long title", body=corto))

    assert solo_corpo.decision is Extractability.NOT_EXTRACTABLE
    assert con_titolo.decision is Extractability.EXTRACTABLE


def test_ignores_surrounding_whitespace_when_counting() -> None:
    checker = DeterministicExtractabilityChecker(min_evidence_characters=30)

    result = checker.check(pr(title="", body="   " + "x" * 20 + "   \n\n"))

    assert result.decision is Extractability.NOT_EXTRACTABLE


def test_threshold_zero_only_rejects_empty_bodies() -> None:
    checker = DeterministicExtractabilityChecker(min_evidence_characters=0)

    assert checker.check(pr(title="", body="x")).decision is Extractability.EXTRACTABLE
    assert checker.check(pr(body="  ")).decision is Extractability.NOT_EXTRACTABLE


def test_is_deterministic_across_repeated_calls() -> None:
    """È la ragione principale per cui questa fase non usa un modello."""

    checker = DeterministicExtractabilityChecker()
    record = pr()

    esiti = {checker.check(record).decision for _ in range(20)}

    assert len(esiti) == 1


def test_reports_the_reason_in_the_log(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="are.agents.extractability"):
        DeterministicExtractabilityChecker().check(pr(body=""))

    messaggi = " ".join(record.getMessage() for record in caplog.records)
    assert "NOT_EXTRACTABLE" in messaggi
    assert "vuoto" in messaggi
