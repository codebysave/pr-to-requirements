"""Il tool sulla memoria, esposto all'Assessment Agent (Decisione 3.4).

Nella configurazione predefinita è il grafo a recuperare i requisiti storici e
a consegnarli al valutatore già pronti nel messaggio. Qui il recupero diventa
invece un'azione dell'agente: il modello interrompe la propria risposta,
chiede, riceve, e riprende.

**I filtri non passano dal modello.** Il messaggio dell'agente contiene
soltanto titolo e corpo della Pull Request: non il nome del repository, non la
data. Il modello non è quindi in grado di popolare quei parametri nemmeno
volendo, e lo schema del tool non glieli espone. È il chiamante, che conosce la
Pull Request in corso, a timbrarli prima di inoltrare la richiesta.

Il modello ottiene libertà sul *quando* cercare, mai sul *cosa gli è permesso
vedere*: l'isolamento per progetto e la coerenza temporale restano garantiti
dal codice, esattamente come nel recupero deterministico.

Il tool è costruito sopra la porta ``MemoryRetriever``, quindi funziona
indifferentemente con il retriever diretto e con quello che dialoga via MCP:
è la stessa scelta di iniezione che regge tutto il resto del workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from are.input import PullRequestRecord
from are.llm import ToolCall, ToolDefinition, ToolResult, serialize_tool_content

from .ports import MemoryRetriever
from .state import RetrievedRequirement

SEARCH_TOOL_NAME = "search_requirements"

_DESCRIPTION = (
    "Returns the requirements already validated for this project that come "
    "from Pull Requests older than the one you are judging. Call it once, "
    "before deciding, whenever a comparison with earlier requirements could "
    "matter. The project and the date are applied for you: you cannot see "
    "another project, and you cannot see anything from the future. An empty "
    "list means the memory holds nothing comparable yet, which is a normal "
    "answer and not a failure."
)

# Lo schema è deliberatamente vuoto: non c'è nulla che il modello debba
# scegliere. Un tool senza argomenti rende impossibile, per costruzione, che
# il modello allarghi i filtri.
_INPUT_SCHEMA = {"type": "object", "properties": {}, "required": []}


@dataclass(frozen=True, slots=True)
class MemorySearchTool:
    """Espone ``search_requirements`` al modello, con i filtri imposti."""

    retriever: MemoryRetriever

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=SEARCH_TOOL_NAME,
            description=_DESCRIPTION,
            input_schema=dict(_INPUT_SCHEMA),
        )

    def execute(
        self,
        call: ToolCall,
        pull_request: PullRequestRecord,
        candidate: str | None,
    ) -> tuple[ToolResult, tuple[RetrievedRequirement, ...]]:
        """Esegue l'invocazione e restituisce anche ciò che è stato recuperato.

        Il secondo valore serve alla tracciabilità: il report deve registrare
        che cosa il modello ha effettivamente ottenuto, altrimenti verificare
        il recupero richiederebbe di rileggere i log a occhio.

        Un nome di tool sconosciuto non solleva: viene restituito come errore
        dichiarato, così il modello può correggersi invece di veder fallire
        l'intera Pull Request per una sua svista.
        """

        if call.name != SEARCH_TOOL_NAME:
            return (
                ToolResult(
                    call_id=call.id,
                    content=f"unknown tool {call.name!r}; the only tool available "
                    f"is {SEARCH_TOOL_NAME!r}",
                    is_error=True,
                ),
                (),
            )

        recuperati = tuple(self.retriever.retrieve(candidate or "", pull_request))
        payload = {
            "results": [
                {
                    "requirement_id": item.requirement_id,
                    "statement": item.statement,
                    "source_pr_number": item.source_pr_number,
                }
                for item in recuperati
            ]
        }
        return ToolResult(call_id=call.id, content=serialize_tool_content(payload)), recuperati


def unique_by_id(
    gruppi: Sequence[Sequence[RetrievedRequirement]],
) -> tuple[RetrievedRequirement, ...]:
    """Unisce più recuperi conservando l'ordine e scartando i duplicati.

    Il modello può invocare il tool più di una volta nello stesso giro. Ai fini
    della traccia interessa l'insieme di ciò che ha visto, non quante volte lo
    ha chiesto: il numero di invocazioni è registrato a parte.
    """

    visti: set[str] = set()
    unione: list[RetrievedRequirement] = []
    for gruppo in gruppi:
        for elemento in gruppo:
            if elemento.requirement_id in visti:
                continue
            visti.add(elemento.requirement_id)
            unione.append(elemento)
    return tuple(unione)
