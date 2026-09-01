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
from typing import Sequence

from are.agents.state import RelationClaim
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
    reason                TEXT,
    created_at            TEXT    NOT NULL,
    PRIMARY KEY (source_requirement_id, target_requirement_id, relation_type)
);

-- Ogni Pull Request elaborata, con l'esito, indipendentemente da cosa ha
-- prodotto. Serve a sapere che cosa e' gia' stato fatto, e la tabella dei
-- requisiti non basta a dirlo: conserva solo i successi, quindi una Pull
-- Request rifiutata o non estraibile non vi lascia traccia e verrebbe
-- rielaborata a ogni esecuzione, pagando ogni volta per riscoprire la stessa
-- cosa.
--
-- La chiave e' progetto piu' numero: la stessa Pull Request elaborata da piu'
-- esecuzioni resta una riga sola, aggiornata con l'esito piu' recente. Serve a
-- rispondere "l'ho gia' vista?", non a tenerne la storia -- quella sta nei
-- report sotto `experiments/runs/`.
CREATE TABLE IF NOT EXISTS processed_pull_requests (
    source_repository TEXT    NOT NULL,
    source_pr_number  INTEGER NOT NULL,
    final_status      TEXT    NOT NULL,
    run_id            TEXT    NOT NULL,
    processed_at      TEXT    NOT NULL,
    PRIMARY KEY (source_repository, source_pr_number)
);

-- Vista di lettura: un requisito per riga, con le sue relazioni riassunte in
-- una colonna. Non duplica nulla, viene calcolata a ogni interrogazione e non
-- puo' quindi disallinearsi dalle tabelle.
--
-- Esiste perche' sfogliando `requirements` non c'e' alcun segnale che una riga
-- sia in relazione con altre: bisogna sapere di dover guardare altrove. La
-- relazione resta pero' un fatto fra DUE requisiti, quindi non puo' diventare
-- una colonna della tabella senza perdere con chi, quante, e perche'.
--
-- La colonna `relations` e' vuota per i requisiti senza relazioni, che sono la
-- maggioranza.
CREATE VIEW requirements_overview AS
SELECT
    r.id,
    r.source_repository,
    r.source_pr_number,
    r.statement,
    COALESCE(
        (
            SELECT group_concat(riga, '  |  ')
              FROM (
                    SELECT rel.relation_type || ' con PR #' || bersaglio.source_pr_number
                           || CASE WHEN rel.reason IS NULL OR rel.reason = ''
                                   THEN '' ELSE ' -- ' || rel.reason END AS riga
                      FROM requirement_relations rel
                      JOIN requirements bersaglio
                        ON bersaglio.id = rel.target_requirement_id
                     WHERE rel.source_requirement_id = r.id
                     ORDER BY bersaglio.source_pr_number
                   )
        ),
        ''
    ) AS relations,
    r.source_pr_timestamp,
    r.created_at,
    r.run_id
  FROM requirements r
 ORDER BY r.id;

-- Il catalogo: un requisito per comportamento, senza ripetizioni. E' l'elenco
-- che si consegnerebbe a qualcuno come insieme dei requisiti del progetto.
--
-- Restano fuori due categorie, per ragioni opposte.
--
-- Chi ripete un requisito precedente: la relazione DUPLICATE va dal candidato
-- nuovo verso quello gia' in memoria, quindi si nasconde chi la dichiara e si
-- tiene quello arrivato prima, che ha introdotto il comportamento. La scelta
-- non e' neutra -- due Pull Request con lo stesso contenuto producono lo stesso
-- requisito, e a essere marcata e' semplicemente quella elaborata dopo -- ma un
-- criterio serve, e l'ordine cronologico e' l'unico non arbitrario.
--
-- Chi e' stato superato: con SUPERSEDES vale il verso opposto, perche' il
-- requisito obsoleto e' il bersaglio della relazione, non la fonte.
--
-- OVERLAPS e REFINES non escludono nulla: due requisiti che si sovrappongono in
-- parte restano due comportamenti distinti.
--
-- Questa vista mostra i duplicati che il valutatore ha *riconosciuto*. Un
-- duplicato che non ha visto resta qui, e un requisito legittimo marcato per
-- errore sparisce: per questo `requirements` e `requirements_overview`
-- continuano a mostrare tutto.
CREATE VIEW requirements_unique AS
SELECT
    r.id,
    r.source_repository,
    r.source_pr_number,
    r.statement,
    r.source_pr_timestamp,
    r.created_at,
    r.run_id
  FROM requirements r
 WHERE NOT EXISTS (
           SELECT 1
             FROM requirement_relations ripete
            WHERE ripete.source_requirement_id = r.id
              AND ripete.relation_type = 'DUPLICATE'
       )
   AND NOT EXISTS (
           SELECT 1
             FROM requirement_relations superato
            WHERE superato.target_requirement_id = r.id
              AND superato.relation_type = 'SUPERSEDES'
       )
 ORDER BY r.id;

-- Le sole relazioni che chiedono una decisione a una persona.
--
-- Restano fuori OVERLAPS e REFINES. Non perche' siano sbagliate, ma perche' a
-- questo livello di generalita' sono quasi sempre vere: in un corpus di
-- correzioni di sicurezza ogni requisito si sovrappone tematicamente a ogni
-- altro, e la quinta Pull Request ne ha gia' dichiarate tre. Su un corpus da
-- quaranta sarebbero quaranta, e seppellirebbero i due segnali che contano.
--
-- Quelli che contano sono: CONFLICTS, perche' due requisiti incompatibili non
-- possono valere entrambi e qualcuno deve stabilire quale sopravvive;
-- SUPERSEDES, perche' un requisito superato va ritirato; DUPLICATE, perche' un
-- comportamento descritto due volte va consolidato.
--
-- L'ordinamento mette per primo cio' che e' piu' urgente: una contraddizione
-- prima di una sostituzione, una sostituzione prima di una ripetizione.
CREATE VIEW relations_to_review AS
SELECT
    rel.relation_type,
    fonte.source_pr_number     AS pr_number,
    fonte.statement            AS requirement,
    bersaglio.source_pr_number AS related_pr_number,
    bersaglio.statement        AS related_requirement,
    rel.reason,
    fonte.id                   AS requirement_id,
    bersaglio.id               AS related_requirement_id,
    rel.created_at
  FROM requirement_relations rel
  JOIN requirements fonte     ON fonte.id = rel.source_requirement_id
  JOIN requirements bersaglio ON bersaglio.id = rel.target_requirement_id
 WHERE rel.relation_type IN ('CONFLICTS', 'SUPERSEDES', 'DUPLICATE')
 ORDER BY CASE rel.relation_type
              WHEN 'CONFLICTS'  THEN 1
              WHEN 'SUPERSEDES' THEN 2
              ELSE 3
          END,
          rel.created_at;
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
        # ``check_same_thread=False`` serve al server MCP: l'SDK esegue i tool
        # sincroni in un thread di lavoro, mentre la connessione nasce nel
        # thread principale, e il modulo ``sqlite3`` vieta l'uso incrociato.
        # Le chiamate restano comunque serializzate: il workflow elabora una
        # Pull Request alla volta e invoca un tool alla volta, quindi non ci
        # sono due scritture concorrenti sulla stessa connessione.
        self._connection = sqlite3.connect(self._path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        # I vincoli di chiave esterna in SQLite sono disattivati per
        # impostazione predefinita e vanno abilitati a ogni connessione.
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._migrate()
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    def _migrate(self) -> None:
        """Allinea un database creato da una versione precedente dello schema.

        ``CREATE TABLE IF NOT EXISTS`` non modifica una tabella che esiste già:
        su un database aperto da una versione precedente la colonna
        ``reason`` mancherebbe, e la scrittura di una relazione fallirebbe.

        La vista invece viene ricreata sempre, prima di essere ridefinita dallo
        schema: non contiene dati, quindi ricostruirla è gratuito, e così la
        sua definizione resta quella corrente anche su un database vecchio.
        """

        tabelle = {
            riga["name"]
            for riga in self._connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if "requirement_relations" in tabelle:
            colonne = {
                riga["name"]
                for riga in self._connection.execute("PRAGMA table_info(requirement_relations)")
            }
            if "reason" not in colonne:
                logger.info("  [MEMORIA] aggiungo la colonna 'reason' alle relazioni")
                self._connection.execute("ALTER TABLE requirement_relations ADD COLUMN reason TEXT")

        for vista in ("requirements_overview", "requirements_unique", "relations_to_review"):
            self._connection.execute(f"DROP VIEW IF EXISTS {vista}")

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

    def store_accepted(
        self,
        pull_request: PullRequestRecord,
        statement: str,
        relations: Sequence[RelationClaim] = (),
    ) -> None:
        """Persiste un requisito accettato e le sue relazioni (Decisione 3.3, §5).

        Invocata dal controller dopo `ACCEPT`, mai dagli agenti: nella memoria
        entrano soltanto requisiti che hanno superato la valutazione.

        L'evidenza salvata è il testo della Pull Request di origine, così il
        database resta leggibile da solo, senza il file JSON di partenza a
        fianco.

        Le relazioni vengono scritte nella stessa transazione del requisito:
        l'identificativo appena assegnato serve solo qui e non esce dallo
        store. Una relazione che punta a un requisito inesistente viene
        scartata con un avviso invece di far fallire la scrittura: il requisito
        è stato validato e va conservato comunque, mentre l'osservazione del
        modello su un identificativo sbagliato non vale la perdita del dato.
        """

        evidence = f"{pull_request.title}\n\n{pull_request.body}".strip()
        adesso = _to_utc_iso(datetime.now(timezone.utc))
        with self._connection:
            cursore = self._connection.execute(
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
                    adesso,
                    self._run_id,
                ),
            )
            nuovo_id = int(cursore.lastrowid or 0)
            for relazione in relations:
                if not self._requirement_exists(relazione.target_requirement_id):
                    logger.warning(
                        "  [MEMORIA] relazione %s scartata: il requisito %s non esiste",
                        relazione.kind,
                        relazione.target_requirement_id,
                    )
                    continue
                self._connection.execute(
                    "INSERT INTO requirement_relations ("
                    "  source_requirement_id, target_requirement_id,"
                    "  relation_type, score, reason, created_at"
                    ") VALUES (?, ?, ?, ?, ?, ?)"
                    " ON CONFLICT (source_requirement_id, target_requirement_id, relation_type)"
                    " DO UPDATE SET reason = excluded.reason,"
                    "               created_at = excluded.created_at",
                    (
                        nuovo_id,
                        int(relazione.target_requirement_id),
                        str(relazione.kind),
                        None,
                        relazione.reason or None,
                        adesso,
                    ),
                )
                logger.info(
                    "  [MEMORIA] relazione %s verso la PR #%s",
                    relazione.kind,
                    relazione.target_pr_number,
                )
        logger.info("  [MEMORIA] requisito archiviato per la PR #%s", pull_request.pr_number)

    def _requirement_exists(self, requirement_id: str) -> bool:
        try:
            numero = int(requirement_id)
        except (TypeError, ValueError):
            return False
        riga = self._connection.execute(
            "SELECT 1 FROM requirements WHERE id = ?", (numero,)
        ).fetchone()
        return riga is not None

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

    def record_processed(
        self,
        pull_request: PullRequestRecord,
        final_status: str,
    ) -> None:
        """Registra che questa Pull Request e' stata elaborata, e con quale esito.

        Invocata a esecuzione conclusa per **ogni** Pull Request, non solo per
        quelle accettate: una rifiutata o non estraibile e' comunque stata
        elaborata, e senza questa riga verrebbe rielaborata per sempre.

        Una Pull Request gia' registrata viene aggiornata invece di duplicata:
        interessa sapere se e' stata vista, non quante volte.
        """

        with self._connection:
            self._connection.execute(
                "INSERT INTO processed_pull_requests ("
                "  source_repository, source_pr_number, final_status, run_id, processed_at"
                ") VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT (source_repository, source_pr_number)"
                " DO UPDATE SET final_status = excluded.final_status,"
                "               run_id       = excluded.run_id,"
                "               processed_at = excluded.processed_at",
                (
                    pull_request.repository,
                    pull_request.pr_number,
                    final_status,
                    self._run_id,
                    _to_utc_iso(datetime.now(timezone.utc)),
                ),
            )

    # -- lettura ---------------------------------------------------------

    def processed_pull_requests(self, repository: str) -> dict[int, str]:
        """I numeri delle Pull Request gia' elaborate per un progetto, con l'esito.

        Restituisce una mappa numero -> esito, cosi' chi decide di saltarle puo'
        anche dire perche'. Un progetto mai visto da' una mappa vuota.
        """

        righe = self._connection.execute(
            "SELECT source_pr_number, final_status"
            "  FROM processed_pull_requests"
            " WHERE source_repository = ?",
            (repository,),
        ).fetchall()
        return {riga["source_pr_number"]: riga["final_status"] for riga in righe}


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
