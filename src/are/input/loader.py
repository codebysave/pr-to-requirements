"""Caricamento deterministico del JSON normalizzato delle Pull Request."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .exceptions import (
    DuplicatePullRequestIdError,
    EmptyPullRequestCollectionError,
    FieldValidationIssue,
    InputFileNotFoundError,
    InputFileReadError,
    InputPathNotFileError,
    InvalidInputPathError,
    InvalidJsonError,
    InvalidPullRequestRecordError,
    InvalidRootStructureError,
    PullRequestRecordValidationError,
)
from .models import PullRequestRecord

logger = logging.getLogger(__name__)


class PullRequestLoader:
    """Legge e valida un array JSON di Pull Request normalizzate."""

    def load(self, path: str | os.PathLike[str]) -> list[PullRequestRecord]:
        """Carica ``path`` e restituisce i record nello stesso ordine del file.

        Nessun dato viene corretto, riordinato o sottoposto ad analisi semantica.
        Tutti gli errori attesi derivano da ``PullRequestInputError``.
        """

        input_path = self._normalize_path(path)
        document = self._read_json(input_path)

        if not isinstance(document, list):
            raise InvalidRootStructureError(input_path, _json_type_name(document))
        if not document:
            raise EmptyPullRequestCollectionError(input_path)

        records: list[PullRequestRecord] = []
        seen_ids: dict[str, int] = {}

        for index, item in enumerate(document):
            if not isinstance(item, dict):
                raise InvalidPullRequestRecordError(
                    index,
                    (
                        FieldValidationIssue(
                            "<record>",
                            f"deve essere un oggetto JSON, ricevuto {_json_type_name(item)}",
                        ),
                    ),
                )

            record_id = item.get("id") if isinstance(item.get("id"), str) else None
            try:
                record = PullRequestRecord.from_mapping(item)
            except PullRequestRecordValidationError as exc:
                raise InvalidPullRequestRecordError(
                    index,
                    exc.issues,
                    record_id=record_id,
                ) from exc

            first_index = seen_ids.get(record.id)
            if first_index is not None:
                raise DuplicatePullRequestIdError(record.id, first_index, index)

            seen_ids[record.id] = index
            records.append(record)

        logger.info(
            "Validato file di input %s: %d Pull Request",
            input_path,
            len(records),
        )
        return records

    @staticmethod
    def _normalize_path(path: str | os.PathLike[str]) -> Path:
        try:
            input_path = Path(path)
        except (TypeError, ValueError) as exc:
            raise InvalidInputPathError(path) from exc

        try:
            exists = input_path.exists()
            is_file = input_path.is_file() if exists else False
        except OSError as exc:
            raise InputFileReadError(input_path, str(exc)) from exc

        if not exists:
            raise InputFileNotFoundError(input_path)
        if not is_file:
            raise InputPathNotFileError(input_path)
        return input_path

    @staticmethod
    def _read_json(path: Path) -> Any:
        try:
            # utf-8-sig accetta sia UTF-8 puro sia il BOM emesso da alcuni tool Windows.
            content = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InputFileReadError(
                path,
                f"contenuto non codificato in UTF-8 (byte {exc.start})",
            ) from exc
        except OSError as exc:
            raise InputFileReadError(path, str(exc)) from exc

        try:
            return json.loads(
                content,
                object_pairs_hook=_object_without_duplicate_keys,
                parse_constant=_reject_non_standard_number,
            )
        except json.JSONDecodeError as exc:
            raise InvalidJsonError(
                path,
                exc.msg,
                line=exc.lineno,
                column=exc.colno,
            ) from exc
        except _DuplicateJsonKeyError as exc:
            raise InvalidJsonError(path, f'chiave JSON duplicata "{exc.key}"') from exc
        except _NonStandardNumberError as exc:
            raise InvalidJsonError(
                path,
                f'valore numerico non ammesso "{exc.value}"',
            ) from exc


class _DuplicateJsonKeyError(ValueError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(key)


class _NonStandardNumberError(ValueError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(value)


def _object_without_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError(key)
        result[key] = value
    return result


def _reject_non_standard_number(value: str) -> None:
    raise _NonStandardNumberError(value)


def _json_type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "booleano"
    if isinstance(value, str):
        return "stringa"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "oggetto"
    if isinstance(value, (int, float)):
        return "numero"
    return type(value).__name__
