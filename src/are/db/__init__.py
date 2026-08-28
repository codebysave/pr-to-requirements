"""Memoria persistente dei requisiti validati (Decisione 3.3).

Il pacchetto espone il repository SQLite e i suoi modelli. La ricerca
semantica dei requisiti affini è un componente separato (`RequirementRetriever`,
Decisione 3.3 §9) e non vive qui: il repository si occupa di persistenza,
metadati, filtri e relazioni.
"""

from .models import RelationType, RequirementRelation, StoredRequirement
from .repository import IN_MEMORY, SqliteRequirementRepository

__all__ = [
    "IN_MEMORY",
    "RelationType",
    "RequirementRelation",
    "SqliteRequirementRepository",
    "StoredRequirement",
]
