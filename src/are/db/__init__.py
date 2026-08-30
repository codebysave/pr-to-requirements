"""Memoria persistente dei requisiti validati (Decisione 3.3).

Il pacchetto espone il repository SQLite, il recupero dei requisiti storici e i
loro modelli. La separazione fra i due componenti è quella prevista dal §9 della
decisione: il repository si occupa di persistenza, metadati e filtri, il
retriever di quali requisiti mostrare al valutatore.
"""

from .models import RelationType, RequirementRelation, StoredRequirement
from .repository import IN_MEMORY, SqliteRequirementRepository
from .retriever import DEFAULT_MAX_REQUIREMENTS, ExhaustiveRequirementRetriever

__all__ = [
    "DEFAULT_MAX_REQUIREMENTS",
    "IN_MEMORY",
    "ExhaustiveRequirementRetriever",
    "RelationType",
    "RequirementRelation",
    "SqliteRequirementRepository",
    "StoredRequirement",
]
