"""Modelli tipizzati del contratto di input di PR-to-Requirements."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar

from .exceptions import FieldValidationIssue, PullRequestRecordValidationError


@dataclass(frozen=True, slots=True)
class PullRequestRecord:
    """Una Pull Request normalizzata e validata.

    ``title`` e ``body`` possono essere stringhe vuote: stabilire se contengano
    informazione sufficiente è responsabilità dei nodi semantici successivi.
    """

    id: str
    repository: str
    pr_number: int
    timestamp: datetime
    title: str
    body: str

    FIELD_NAMES: ClassVar[frozenset[str]] = frozenset(
        {"id", "repository", "pr_number", "timestamp", "title", "body"}
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> PullRequestRecord:
        """Valida un mapping e costruisce un record senza coercizioni silenziose.

        Raises:
            PullRequestRecordValidationError: se uno o più campi non rispettano
                il contratto.
        """

        issues: list[FieldValidationIssue] = []

        missing_fields = cls.FIELD_NAMES.difference(data.keys())
        for field in sorted(missing_fields):
            issues.append(FieldValidationIssue(field, "campo obbligatorio mancante"))

        unexpected_fields = set(data.keys()).difference(cls.FIELD_NAMES)
        for field in sorted(unexpected_fields, key=str):
            issues.append(FieldValidationIssue(str(field), "campo non previsto dallo schema"))

        id_value = _strict_string(data, "id", issues)
        repository = _strict_string(data, "repository", issues)
        title = _strict_string(data, "title", issues)
        body = _strict_string(data, "body", issues)

        pr_number_value = data.get("pr_number")
        pr_number: int | None = None
        if "pr_number" in data:
            if type(pr_number_value) is not int:
                issues.append(
                    FieldValidationIssue(
                        "pr_number",
                        f"deve essere un intero, ricevuto {_json_type_name(pr_number_value)}",
                    )
                )
            else:
                pr_number = pr_number_value

        timestamp_value = data.get("timestamp")
        timestamp: datetime | None = None
        if "timestamp" in data:
            if not isinstance(timestamp_value, str):
                issues.append(
                    FieldValidationIssue(
                        "timestamp",
                        "deve essere una stringa ISO 8601, ricevuto "
                        f"{_json_type_name(timestamp_value)}",
                    )
                )
            else:
                timestamp = _parse_timestamp(timestamp_value, issues)

        if issues:
            raise PullRequestRecordValidationError(issues)

        # I controlli precedenti garantiscono i tipi; gli assert aiutano anche i type checker.
        assert id_value is not None
        assert repository is not None
        assert pr_number is not None
        assert timestamp is not None
        assert title is not None
        assert body is not None
        return cls(
            id=id_value,
            repository=repository,
            pr_number=pr_number,
            timestamp=timestamp,
            title=title,
            body=body,
        )


def _strict_string(
    data: Mapping[str, Any],
    field: str,
    issues: list[FieldValidationIssue],
) -> str | None:
    if field not in data:
        return None

    value = data[field]
    if not isinstance(value, str):
        issues.append(
            FieldValidationIssue(
                field,
                f"deve essere una stringa, ricevuto {_json_type_name(value)}",
            )
        )
        return None
    return value


def _parse_timestamp(
    value: str,
    issues: list[FieldValidationIssue],
) -> datetime | None:
    if not value:
        issues.append(FieldValidationIssue("timestamp", "non può essere una stringa vuota"))
        return None

    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        issues.append(FieldValidationIssue("timestamp", "non è un timestamp ISO 8601 valido"))
        return None

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        issues.append(
            FieldValidationIssue(
                "timestamp",
                "deve includere il fuso orario (per esempio Z oppure +02:00)",
            )
        )
        return None
    return parsed


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
    if isinstance(value, int):
        return "intero"
    if isinstance(value, float):
        return "numero decimale"
    return type(value).__name__
