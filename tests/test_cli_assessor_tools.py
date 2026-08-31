"""Il cablaggio di ``--assessor-tools``: chi recupera, e con quale prompt.

Nessuna chiamata di rete: si costruiscono le dipendenze e si guarda com'è
fatto il grafo che ne esce.

Il punto che questi test proteggono è che le due configurazioni non si
sovrappongano. Con il recupero guidato dall'agente il nodo del grafo deve
smettere di cercare: se continuasse, il valutatore riceverebbe i requisiti
storici sia nel messaggio sia dal tool, e la differenza fra le due condizioni
sperimentali sparirebbe.
"""

from __future__ import annotations

import argparse

from are.__main__ import (
    TOOL_PROMPT_VERSION,
    _build_dependencies,
    _resolve_prompt_version,
)
from are.agents import NullMemoryRetriever, WorkflowConfig
from are.agents.prompts import DEFAULT_PROMPT_VERSION
from are.db import IN_MEMORY, ExhaustiveRequirementRetriever, SqliteRequirementRepository
from are.llm import AgentLLMSettings, AnthropicLLMClient

SETTINGS = AgentLLMSettings(model="claude-haiku-4-5", max_tokens=1024)


class SdkFinto:
    """Basta a costruire il client: nessuna chiamata viene mai eseguita."""

    def __init__(self) -> None:
        self.messages = None


def client() -> AnthropicLLMClient:
    return AnthropicLLMClient(SETTINGS, sdk_client=SdkFinto())  # type: ignore[arg-type]


def dipendenze(*, assessor_tools: bool, assessment_enabled: bool = True):
    repository = SqliteRequirementRepository(IN_MEMORY, "R1")
    retriever = ExhaustiveRequirementRetriever(repository, run_id="R1")
    return _build_dependencies(
        WorkflowConfig(assessment_enabled=assessment_enabled, memory_enabled=True),
        client(),
        client(),
        "v2" if assessor_tools else "v1",
        retriever=retriever,
        store=repository,
        assessor_tools=assessor_tools,
    )


def args(**valori) -> argparse.Namespace:
    predefiniti = {"assessor_tools": False, "prompt_version": None}
    predefiniti.update(valori)
    return argparse.Namespace(**predefiniti)


# -- chi recupera -----------------------------------------------------------


def test_by_default_the_graph_node_retrieves():
    deps = dipendenze(assessor_tools=False)

    assert isinstance(deps.retriever, ExhaustiveRequirementRetriever)
    assert deps.assessor.uses_tools is False


def test_with_the_flag_the_graph_node_stops_retrieving():
    """Il retriever vero passa al tool del valutatore; al grafo ne resta uno
    inerte, così la ricerca avviene una volta sola."""

    deps = dipendenze(assessor_tools=True)

    assert isinstance(deps.retriever, NullMemoryRetriever)
    assert deps.assessor.uses_tools is True


def test_the_inert_retriever_returns_nothing():
    deps = dipendenze(assessor_tools=True)
    assert deps.retriever.retrieve("candidato", None) == ()


def test_the_store_is_never_replaced_by_the_flag():
    """La scrittura resta al nodo `accept` in entrambe le configurazioni: al
    modello non viene mai dato il tool di scrittura."""

    con = dipendenze(assessor_tools=True)
    senza = dipendenze(assessor_tools=False)

    assert isinstance(con.store, SqliteRequirementRepository)
    assert isinstance(senza.store, SqliteRequirementRepository)


def test_the_generator_never_gets_a_memory_tool():
    """Il redattore scrive dalla sola evidenza: l'accesso allo storico sarebbe
    un invito a copiare."""

    deps = dipendenze(assessor_tools=True)
    assert not hasattr(deps.generator, "_memory_tool")


def test_without_an_assessor_there_is_no_tool_to_give():
    deps = dipendenze(assessor_tools=True, assessment_enabled=False)
    assert deps.assessor is None


# -- quale prompt -----------------------------------------------------------


def test_without_the_flag_the_prompt_version_is_untouched():
    assert _resolve_prompt_version(args()) == DEFAULT_PROMPT_VERSION


def test_the_flag_selects_the_prompt_that_describes_the_tool():
    """La v1 non nomina alcun tool: userebbe il modello senza dirgli che può
    cercare."""

    assert _resolve_prompt_version(args(assessor_tools=True)) == TOOL_PROMPT_VERSION


def test_an_explicit_version_is_not_overridden():
    """Una scelta dichiarata dall'utente non va sovrascritta in silenzio:
    serve a poter provare una formulazione nuova."""

    scelta = args(assessor_tools=True, prompt_version="v3")
    assert _resolve_prompt_version(scelta) == "v3"


def test_asking_for_v1_with_the_flag_is_respected():
    """Configurazione volutamente scorretta, ma è una scelta esplicita: serve
    a misurare cosa fa un modello a cui il tool non è stato descritto."""

    scelta = args(assessor_tools=True, prompt_version="v1")
    assert _resolve_prompt_version(scelta) == "v1"
