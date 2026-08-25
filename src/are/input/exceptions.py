"""Errori pubblici prodotti dal livello di ingresso delle Pull Request."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class PullRequestInputError(Exception):
    """Classe base per tutti gli errori attesi del nodo di ingresso."""


class InvalidInputPathError(PullRequestInputError):
    """Il valore ricevuto non può essere interpretato come percorso."""

    def __init__(self, value: object) -> None:
        self.value = value
        super().__init__(
            "Il percorso del file JSON deve essere una stringa o un oggetto "
            f"os.PathLike; ricevuto {type(value).__name__}."
        )


class InputFileNotFoundError(PullRequestInputError):
    """Il file indicato non esiste."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f'File JSON non trovato: "{path}".')


class InputPathNotFileError(PullRequestInputError):
    """Il percorso esiste, ma non identifica un file regolare."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f'Il percorso di input non identifica un file: "{path}".')


class InputFileReadError(PullRequestInputError):
    """Il file esiste ma non può essere letto come testo UTF-8."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f'Impossibile leggere il file JSON "{path}": {reason}.')


class InvalidJsonError(PullRequestInputError):
    """Il contenuto del file non è JSON valido e non ambiguo."""

    def __init__(
        self,
        path: Path,
        reason: str,
        *,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        self.path = path
        self.reason = reason
        self.line = line
        self.column = column

        location = ""
        if line is not None and column is not None:
            location = f" alla riga {line}, colonna {column}"
        super().__init__(f'JSON non valido in "{path}"{location}: {reason}.')


class InvalidRootStructureError(PullRequestInputError):
    """La radice JSON non è un array."""

    def __init__(self, path: Path, actual_type: str) -> None:
        self.path = path
        self.actual_type = actual_type
        super().__init__(
            f"La radice del JSON deve essere un array di Pull Request; ricevuto {actual_type}."
        )


class EmptyPullRequestCollectionError(PullRequestInputError):
    """L'array non contiene Pull Request."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(
            f'Il file JSON "{path}" contiene un array vuoto; è richiesta almeno una Pull Request.'
        )


@dataclass(frozen=True, slots=True)
class FieldValidationIssue:
    """Descrive un singolo problema riscontrato in un record."""

    field: str
    reason: str

    def __str__(self) -> str:
        return f'- campo "{self.field}": {self.reason}'


class PullRequestRecordValidationError(ValueError):
    """Errore di schema prodotto direttamente da ``PullRequestRecord``."""

    def __init__(self, issues: Sequence[FieldValidationIssue]) -> None:
        if not issues:
            raise ValueError("È necessario specificare almeno un problema di validazione.")
        self.issues = tuple(issues)
        super().__init__("\n".join(str(issue) for issue in self.issues))


class InvalidPullRequestRecordError(PullRequestInputError):
    """Un elemento dell'array non rispetta lo schema di una PR."""

    def __init__(
        self,
        index: int,
        issues: Sequence[FieldValidationIssue],
        *,
        record_id: str | None = None,
    ) -> None:
        self.index = index
        self.record_id = record_id
        self.issues = tuple(issues)

        identity = f', id "{record_id}"' if record_id is not None else ""
        details = "\n".join(str(issue) for issue in self.issues)
        super().__init__(f"Pull Request non valida all'indice {index}{identity}:\n{details}")


class DuplicatePullRequestIdError(PullRequestInputError):
    """Due record dello stesso file dichiarano il medesimo identificativo."""

    def __init__(self, duplicate_id: str, first_index: int, duplicate_index: int) -> None:
        self.duplicate_id = duplicate_id
        self.first_index = first_index
        self.duplicate_index = duplicate_index
        super().__init__(
            f'ID Pull Request duplicato "{duplicate_id}": presente agli indici '
            f"{first_index} e {duplicate_index}."
        )
