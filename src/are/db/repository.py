"""Memoria persistente dei requisiti validati su SQLite (Decisione 3.3).

Il repository incapsula l'accesso al database: il resto del sistema non scrive
SQL e non conosce SQLite. Implementa il protocollo ``AcceptedRequirementStore``
del workflow, quindi si inserisce al posto di ``NullRequirementStore`` senza
modifiche al grafo.

Due scelte meritano una nota.

Lo schema è una costante di questo modulo e non un file ``.sql`` a fianco:
un file di dati richiederebbe una configurazione di packaging per finire nel
pacchetto installato, e il beneficio non giustifica il rischio di un'installazione
in cui lo schema manca.

Le date sono normalizzate a UTC e scritte in ISO 8601. SQLite non ha un tipo
data: confronta stringhe. Con l'offset sempre a ``+00:00`` l'ordinamento
lessicografico coincide con quello cronologico, che è ciò su cui si regge il
filtro ``before_timestamp``.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType

from are.input import PullRequestRecord

from .models import RelationType, RequirementRelation, StoredRequirement

logger = logging.getLogger(__name__)

IN_MEMORY = ":memory:"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS requirements (
    id                  INTEGER PRIMARY KEY,
    statement           TEXT    NOT NULL,
    source_repository   TEXT    NOT NULL,
    source_pr_number    INTEGER NOT NULL,
    source_pr_timestamp TEXT    NOT NULL,
    evidence            TEXT,
    created_at          TEXT    NOT NULL,
    embedding           BLOB,
    embedding_model     TEXT,
    run_id              TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_requirements_repository
    ON requirements (source_repository);
CREATE INDEX IF NOT EXISTS idx_requirements_pr_timestamp
    ON requirements (source_pr_timestamp);
CREATE INDEX IF NOT EXISTS idx_requirements_run
    ON requirements (run_id);

CREATE TABLE IF NOT EXISTS requirement_relations (
    source_requirement_id INTEGER NOT NULL REFERENCES requirements (id) ON DELETE CASCADE,
    target_requirement_id INTEGER NOT NULL REFERENCES requirements (id) ON DELETE CASCADE,
    relation_type         TEXT    NOT NULL CHECK (relation_type IN (
                              'DUPLICATE', 'OVERLAPS', 'REFINES', 'SUPERSEDES', 'CONFLICTS')),
    score                 REAL,
    created_at            TEXT    NOT NULL,
    PRIMARY KEY (source_requirement_id, target_requirement_id, relation_type)
);
"""

_REQUIREMENT_COLUMNS = (
    "id, statement, source_repository, source_pr_number, "
    "source_pr_timestamp, evidence, created_at, run_id"
)


def _to_utc_iso(moment: datetime) -> str:
    """Normalizza a UTC e formatta in ISO 8601.

    Un timestamp senza fuso orario viene interpretato come UTC: il Loader
    produce sempre date timezone-aware, ma il repository non può assumerlo per
    dati che arrivassero da un'altra sorgente.
    """

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat()


def _from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


class SqliteRequirementRepository:
    """Persistenza dei requisiti validati in un singolo file SQLite.

    ``run_id`` identifica l'esecuzione che produce le righe scritte da questa
    istanza. Serve quando un database sopravvive a più esecuzioni: senza,
    non si potrebbe sapere quale run ha prodotto quale requisito, né ripulire
    selettivamente. Coincide con il timestamp che nomina il report in
    ``experiments/runs/``, così i due artefatti restano agganciati.

    Usare ``IN_MEMORY`` come percorso per un database temporaneo che vive
    quanto l'oggetto: è la modalità usata dai test, senza file su disco.
    """

    def __init__(self, database_path: str | Path, run_id: str) -> None:
        self._run_id = run_id
        self._path = str(database_path)
        if self._path != IN_MEMORY:
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._path)
        self._connection.row_factory = sqlite3.Row
        # I vincoli di chiave esterna in SQLite sono disattivati per
        # impostazione predefinita e vanno abilitati a ogni connessione.
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    # -- ciclo di vita ---------------------------------------------------

    @property
    def path(self) -> str:
        return self._path

    @property
    def run_id(self) -> str:
        return self._run_id

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> SqliteRequirementRepository:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    # -- scrittura -------------------------------------------------------

    def store_accepted(self, pull_request: PullRequestRecord, statement: str) -> None:
        """Persiste un requisito accettato (Decisione 3.3, §5).

        Invocata dal controller dopo `ACCEPT`, mai dagli agenti: nella memoria
        entrano soltanto requisiti che hanno superato la valutazione.

        L'evidenza salvata è il testo della Pull Request di origine, così il
        database resta leggibile da solo, senza il file JSON di partenza a
        fianco.
        """

        evidence = f"{pull_request.title}\n\n{pull_request.body}".strip()
        with self._connection:
            self._connection.execute(
                "INSERT INTO requirements ("
                "  statement, source_repository, source_pr_number,"
                "  source_pr_timestamp, evidence, created_at, run_id"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    statement,
                    pull_request.repository,
                    pull_request.pr_number,
                    _to_utc_iso(pull_request.timestamp),
                    evidence or None,
                    _to_utc_iso(datetime.now(timezone.utc)),
                    self._run_id,
                ),
            )
        logger.info("  [MEMORIA] requisito archiviato per la PR #%s", pull_request.pr_number)

    def save_relation(
        self,
        source_requirement_id: int,
        target_requirement_id: int,
        relation_type: RelationType,
        score: float | None = None,
    ) -> None:
        """Inserisce o aggiorna una relazione fra due requisiti.

        Nessun componente della pipeline la invoca oggi: l'operazione è
        prevista dalla Decisione 3.3 §7 e resta a disposizione del futuro
        rilevatore di relazioni.
        """

        with self._connection:
            self._connection.execute(
                "INSERT INTO requirement_relations ("
                "  source_requirement_id, target_requirement_id,"
                "  relation_type, score, created_at"
                ") VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT (source_requirement_id, target_requirement_id, relation_type)"
                " DO UPDATE SET score = excluded.score, created_at = excluded.created_at",
                (
                    source_requirement_id,
                    target_requirement_id,
                    relation_type.value,
                    score,
                    _to_utc_iso(datetime.now(timezone.utc)),
                ),
            )

    # -- lettura ---------------------------------------------------------

    def get_by_id(self, requirement_id: int) -> StoredRequirement | None:
        row = self._connection.execute(
            f"SELECT {_REQUIREMENT_COLUMNS} FROM requirements WHERE id = ?",
            (requirement_id,),
        ).fetchone()
        return None if row is None else _to_requirement(row)

    def list_requirements(
        self,
        *,
        repository: str | None = None,
        before_timestamp: datetime | None = None,
        run_id: str | None = None,
    ) -> list[StoredRequirement]:
        """Elenca i requisiti validati, in ordine cronologico di Pull Request.

        ``before_timestamp`` è **esclusivo** e filtra sulla data della Pull
        Request di origine: serve a ricostruire la memoria disponibile a un
        certo istante (Decisione 3.3, §2), non a filtrare per data di
        inserimento.

        ``run_id`` isola una singola esecuzione. Serve perché il database è
        condiviso fra esecuzioni diverse: senza il filtro, una run vedrebbe i
        requisiti prodotti da quelle precedenti e partirebbe avvantaggiata,
        rendendo i confronti fra configurazioni privi di significato.
        """

        clauses: list[str] = []
        parameters: list[object] = []
        if repository is not None:
            clauses.append("source_repository = ?")
            parameters.append(repository)
        if before_timestamp is not None:
            clauses.append("source_pr_timestamp < ?")
            parameters.append(_to_utc_iso(before_timestamp))
        if run_id is not None:
            clauses.append("run_id = ?")
            parameters.append(run_id)

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._connection.execute(
            f"SELECT {_REQUIREMENT_COLUMNS} FROM requirements{where}"
            " ORDER BY source_pr_timestamp, id",
            parameters,
        ).fetchall()
        return [_to_requirement(row) for row in rows]

    def get_relations(self, requirement_id: int) -> list[RequirementRelation]:
        """Recupera le relazioni che coinvolgono il requisito, in entrambi i versi."""

        rows = self._connection.execute(
            "SELECT source_requirement_id, target_requirement_id, relation_type,"
            "       score, created_at"
            "  FROM requirement_relations"
            " WHERE source_requirement_id = ? OR target_requirement_id = ?"
            " ORDER BY created_at, source_requirement_id, target_requirement_id",
            (requirement_id, requirement_id),
        ).fetchall()
        return [
            RequirementRelation(
                source_requirement_id=row["source_requirement_id"],
                target_requirement_id=row["target_requirement_id"],
                relation_type=RelationType(row["relation_type"]),
                score=row["score"],
                created_at=_from_iso(row["created_at"]),
            )
            for row in rows
        ]

    def count(self) -> int:
        row = self._connection.execute("SELECT COUNT(*) AS totale FROM requirements").fetchone()
        return int(row["totale"])


def _to_requirement(row: sqlite3.Row) -> StoredRequirement:
    return StoredRequirement(
        id=row["id"],
        statement=row["statement"],
        source_repository=row["source_repository"],
        source_pr_number=row["source_pr_number"],
        source_pr_timestamp=_from_iso(row["source_pr_timestamp"]),
        evidence=row["evidence"],
        created_at=_from_iso(row["created_at"]),
        run_id=row["run_id"],
    )
