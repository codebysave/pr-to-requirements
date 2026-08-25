from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from are.input import (
    PullRequestRecord,
    PullRequestRecordValidationError,
)


class PullRequestRecordTests(unittest.TestCase):
    def test_direct_construction_from_mapping(self) -> None:
        record = PullRequestRecord.from_mapping(
            {
                "id": "owner-repo-pr-42",
                "repository": "owner/repo",
                "pr_number": 42,
                "timestamp": "2026-08-25T10:15:00Z",
                "title": "Title",
                "body": "Body",
            }
        )

        self.assertEqual(record.repository, "owner/repo")
        self.assertEqual(record.pr_number, 42)

    def test_record_is_immutable(self) -> None:
        record = PullRequestRecord.from_mapping(
            {
                "id": "owner-repo-pr-42",
                "repository": "owner/repo",
                "pr_number": 42,
                "timestamp": "2026-08-25T10:15:00Z",
                "title": "Title",
                "body": "Body",
            }
        )

        with self.assertRaises(FrozenInstanceError):
            record.title = "Changed"  # type: ignore[misc]

    def test_direct_validation_returns_field_issues(self) -> None:
        with self.assertRaises(PullRequestRecordValidationError) as context:
            PullRequestRecord.from_mapping({})

        self.assertEqual(len(context.exception.issues), 6)


if __name__ == "__main__":
    unittest.main()
