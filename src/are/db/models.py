"""Modelli della memoria persistente (Decisione 3.3, §6).

Questi tipi rappresentano ciò che il repository restituisce, non ciò che
scrive: la scrittura parte da un ``PullRequestRecord`` e dal testo del
requisito accettato, mentre la lettura restituisce righe già identificate e
datate.

Le colonne ``embedding`` ed ``embedding_model`` esistono nello schema ma non
compaiono qui: finché non c'è un retriever semantico non c'è nulla che le
legga, e includerle costringerebbe ogni interrogazione a trasportare un vettore
inutilizzato.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RelationType(str, Enum):
    """Tassonomia preliminare delle relazioni fra requisiti (Decisione 3.3, §6.2).

    La tassonomia definitiva verrà consolidata nella fase sperimentale: questi
    valori sono quelli previsti dal documento di design.
    """

    DUPLICATE = "DUPLICATE"
    OVERLAPS = "OVERLAPS"
    REFINES = "REFINES"
    SUPERSEDES = "SUPERSEDES"
    CONFLICTS = "CONFLICTS"


@dataclass(frozen=True, slots=True)
class StoredRequirement:
    """Un requisito validato letto dalla memoria.

    ``source_pr_timestamp`` è la data della Pull Request di origine, mentre
    ``created_at`` è il momento in cui la riga è stata inserita. Sono due cose
    diverse e il retrieval storico deve usare la prima: filtrare sulla seconda
    ricostruirebbe l'ordine in cui abbiamo lanciato le esecuzioni, non la
    storia del progetto.
    """

    id: int
    statement: str
    source_repository: str
    source_pr_number: int
    source_pr_timestamp: datetime
    evidence: str | None
    created_at: datetime
    run_id: str


@dataclass(frozen=True, slots=True)
class RequirementRelation:
    """Una relazione fra due requisiti già validati.

    Nessun componente della pipeline produce oggi relazioni: la tabella e
    queste operazioni sono predisposte secondo la Decisione 3.3 e restano
    vuote finché non esisterà un componente che le rileva.
    """

    source_requirement_id: int
    target_requirement_id: int
    relation_type: RelationType
    score: float | None
    created_at: datetime
