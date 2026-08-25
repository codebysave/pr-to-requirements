from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from are.input import (
    DuplicatePullRequestIdError,
    EmptyPullRequestCollectionError,
    InputFileNotFoundError,
    InputFileReadError,
    InputPathNotFileError,
    InvalidInputPathError,
    InvalidJsonError,
    InvalidPullRequestRecordError,
    InvalidRootStructureError,
    PullRequestLoader,
)


def valid_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": "django-django-pr-19511",
        "repository": "django/django",
        "pr_number": 19511,
        "timestamp": "2025-05-29T02:33:52Z",
        "title": "Handle empty combinator arguments",
        "body": "This change restores the previous behavior.",
    }
    record.update(overrides)
    return record


class PullRequestLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)
        self.loader = PullRequestLoader()

    def write_json(self, value: object, filename: str = "input.json") -> Path:
        path = self.directory / filename
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def write_text(self, value: str, filename: str = "input.json") -> Path:
        path = self.directory / filename
        path.write_text(value, encoding="utf-8")
        return path

    def test_loads_one_valid_pull_request_as_typed_record(self) -> None:
        records = self.loader.load(self.write_json([valid_record()]))

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].id, "django-django-pr-19511")
        self.assertEqual(records[0].pr_number, 19511)
        self.assertEqual(
            records[0].timestamp,
            datetime(2025, 5, 29, 2, 33, 52, tzinfo=timezone.utc),
        )

    def test_loads_multiple_records_and_preserves_input_order(self) -> None:
        source = [
            valid_record(id="third", pr_number=3),
            valid_record(id="first", pr_number=1),
            valid_record(id="second", pr_number=2),
        ]

        records = self.loader.load(self.write_json(source))

        self.assertEqual([record.id for record in records], ["third", "first", "second"])

    def test_preserves_unicode_markdown_urls_code_blocks_and_newlines(self) -> None:
        title = "对 Update 的修改 — correzione"
        body = (
            "## Descrizione\r\n\r\n"
            "Visita https://example.test/path?q=è\r\n\r\n"
            '```python\r\nprint("ciao 👋")\r\n```\r\n'
            "- [x] completato"
        )

        record = self.loader.load(self.write_json([valid_record(title=title, body=body)]))[0]

        self.assertEqual(record.title, title)
        self.assertEqual(record.body, body)

    def test_accepts_empty_title_and_body_without_semantic_validation(self) -> None:
        record = self.loader.load(self.write_json([valid_record(title="", body="")]))[0]

        self.assertEqual(record.title, "")
        self.assertEqual(record.body, "")

    def test_accepts_utf8_bom(self) -> None:
        path = self.directory / "bom.json"
        path.write_text(
            json.dumps([valid_record()], ensure_ascii=False),
            encoding="utf-8-sig",
        )

        self.assertEqual(len(self.loader.load(path)), 1)

    def test_rejects_malformed_json_with_location(self) -> None:
        path = self.write_text('[{"id": 1,,}]')

        with self.assertRaises(InvalidJsonError) as context:
            self.loader.load(path)

        self.assertIsNotNone(context.exception.line)
        self.assertIsNotNone(context.exception.column)

    def test_rejects_duplicate_keys_in_a_json_object(self) -> None:
        path = self.write_text(
            '[{"id":"one","id":"two","repository":"a/b","pr_number":1,'
            '"timestamp":"2025-01-01T00:00:00Z","title":"","body":""}]'
        )

        with self.assertRaisesRegex(InvalidJsonError, "chiave JSON duplicata"):
            self.loader.load(path)

    def test_rejects_non_standard_json_numbers(self) -> None:
        path = self.write_text(
            '[{"id":"one","repository":"a/b","pr_number":NaN,'
            '"timestamp":"2025-01-01T00:00:00Z","title":"","body":""}]'
        )

        with self.assertRaisesRegex(InvalidJsonError, "NaN"):
            self.loader.load(path)

    def test_rejects_root_that_is_not_an_array(self) -> None:
        with self.assertRaises(InvalidRootStructureError):
            self.loader.load(self.write_json(valid_record()))

    def test_rejects_empty_array(self) -> None:
        with self.assertRaises(EmptyPullRequestCollectionError):
            self.loader.load(self.write_json([]))

    def test_rejects_non_object_array_element_and_reports_index(self) -> None:
        path = self.write_json([valid_record(), "not-an-object"])

        with self.assertRaises(InvalidPullRequestRecordError) as context:
            self.loader.load(path)

        self.assertEqual(context.exception.index, 1)
        self.assertIn("oggetto JSON", str(context.exception))

    def test_reports_all_missing_or_invalid_fields_for_a_record(self) -> None:
        invalid = valid_record()
        del invalid["body"]
        invalid["title"] = 7
        invalid["pr_number"] = "19511"

        with self.assertRaises(InvalidPullRequestRecordError) as context:
            self.loader.load(self.write_json([invalid]))

        fields = {issue.field for issue in context.exception.issues}
        self.assertEqual(fields, {"body", "title", "pr_number"})
        self.assertEqual(context.exception.index, 0)
        self.assertEqual(context.exception.record_id, "django-django-pr-19511")

    def test_rejects_null_for_required_fields(self) -> None:
        for field in ("id", "repository", "pr_number", "timestamp", "title", "body"):
            with self.subTest(field=field):
                with self.assertRaises(InvalidPullRequestRecordError):
                    self.loader.load(
                        self.write_json(
                            [valid_record(**{field: None})],
                            filename=f"null-{field}.json",
                        )
                    )

    def test_rejects_boolean_as_pr_number_without_coercion(self) -> None:
        with self.assertRaises(InvalidPullRequestRecordError) as context:
            self.loader.load(self.write_json([valid_record(pr_number=True)]))

        self.assertIn("intero", str(context.exception))

    def test_rejects_invalid_or_timezone_less_timestamp(self) -> None:
        for timestamp in ("not-a-date", "2025-05-29T02:33:52", ""):
            with self.subTest(timestamp=timestamp):
                with self.assertRaises(InvalidPullRequestRecordError):
                    self.loader.load(
                        self.write_json(
                            [valid_record(timestamp=timestamp)],
                            filename=f"timestamp-{len(timestamp)}.json",
                        )
                    )

    def test_accepts_iso_timestamp_with_explicit_offset(self) -> None:
        record = self.loader.load(
            self.write_json([valid_record(timestamp="2025-05-29T04:33:52+02:00")])
        )[0]

        self.assertEqual(record.timestamp.utcoffset().total_seconds(), 7200)

    def test_rejects_duplicate_ids_and_reports_both_indices(self) -> None:
        source = [
            valid_record(id="duplicate", pr_number=1),
            valid_record(id="other", pr_number=2),
            valid_record(id="duplicate", pr_number=3),
        ]

        with self.assertRaises(DuplicatePullRequestIdError) as context:
            self.loader.load(self.write_json(source))

        self.assertEqual(context.exception.duplicate_id, "duplicate")
        self.assertEqual(context.exception.first_index, 0)
        self.assertEqual(context.exception.duplicate_index, 2)

    def test_rejects_unexpected_fields_instead_of_dropping_them(self) -> None:
        with self.assertRaises(InvalidPullRequestRecordError) as context:
            self.loader.load(self.write_json([valid_record(extra="value")]))

        self.assertIn("non previsto", str(context.exception))

    def test_rejects_missing_file(self) -> None:
        with self.assertRaises(InputFileNotFoundError):
            self.loader.load(self.directory / "missing.json")

    def test_rejects_directory_path(self) -> None:
        with self.assertRaises(InputPathNotFileError):
            self.loader.load(self.directory)

    def test_rejects_invalid_path_value(self) -> None:
        with self.assertRaises(InvalidInputPathError):
            self.loader.load(None)  # type: ignore[arg-type]

    def test_rejects_non_utf8_input(self) -> None:
        path = self.directory / "invalid-encoding.json"
        path.write_bytes(b"[\xff]")

        with self.assertRaises(InputFileReadError):
            self.loader.load(path)


if __name__ == "__main__":
    unittest.main()
