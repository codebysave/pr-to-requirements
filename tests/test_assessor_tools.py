"""Il valutatore che interroga la memoria da sé, con un client finto.

Nessuna chiamata di rete e nessun sottoprocesso: il doppio dell'LLM restituisce
risposte scritte a mano, e il retriever dietro il tool è una lista in memoria.

Ciò che questi test proteggono è la garanzia su cui si regge l'intera
configurazione: **il modello sceglie quando cercare, mai cosa gli è permesso
vedere**. Lo schema del tool non espone i filtri, e i valori di progetto e di
data vengono imposti dal codice a partire dalla Pull Request in esame. Se
questa separazione si rompesse, un modello potrebbe farsi mostrare requisiti di
un altro progetto o nati da Pull Request successive, e l'esperimento perderebbe
la coerenza temporale che lo rende interpretabile.
"""

from __future__ import annotations

from typing import Any, Sequence

import pytest

from are.agents.llm_agents import LLMRequirementAssessor
from are.agents.memory_tool import SEARCH_TOOL_NAME, MemorySearchTool, unique_by_id
from are.agents.state import AssessmentDecision, RetrievedRequirement
from are.input import PullRequestRecord
from are.llm import LLMResponse, ToolCall

DECISIONE = (
    '{"decision": "ACCEPT", "issues": [], "unsupported_claims": [], '
    '"missing_information": [], "revision_instructions": []}'
)


def pr(
    pr_number: int = 6880,
    repository: str = "owner/repo",
    timestamp: str = "2025-06-01T10:00:00Z",
    title: str = "Fix the report export",
    body: str = "The export button did nothing. This restores the download.",
) -> PullRequestRecord:
    return PullRequestRecord.from_mapping(
        {
            "id": f"{repository.replace('/', '-')}-pr-{pr_number}",
            "repository": repository,
            "pr_number": pr_number,
            "timestamp": timestamp,
            "title": title,
            "body": body,
        }
    )


def requisito(numero: int = 6870, testo: str = "The system shall export.") -> RetrievedRequirement:
    return RetrievedRequirement(
        requirement_id=str(numero), statement=testo, source_pr_number=numero
    )


class RetrieverFinto:
    """Restituisce sempre gli stessi requisiti e registra come è stato chiamato."""

    def __init__(self, *requisiti: RetrievedRequirement) -> None:
        self._requisiti = requisiti
        self.chiamate: list[tuple[str, PullRequestRecord]] = []

    def retrieve(
        self, candidate: str, pull_request: PullRequestRecord
    ) -> Sequence[RetrievedRequirement]:
        self.chiamate.append((candidate, pull_request))
        return self._requisiti


def risposta(text: str = "", *, tool_calls: tuple[ToolCall, ...] = ()) -> LLMResponse:
    return LLMResponse(
        text=text,
        model="claude-haiku-4-5",
        stop_reason="tool_use" if tool_calls else "end_turn",
        input_tokens=100,
        output_tokens=20,
        tool_calls=tool_calls,
    )


class ClientFinto:
    """Doppio del client LLM che sa anche conversare con i tool."""

    def __init__(self, *risposte: LLMResponse) -> None:
        self._risposte = list(risposte)
        self.chiamate: list[dict[str, Any]] = []

    def complete(self, *, system: str, user_message: str) -> LLMResponse:
        return self.converse(system=system, user_message=user_message)

    def converse(
        self,
        *,
        system: str,
        user_message: str,
        exchanges: Sequence[Any] = (),
        tools: Sequence[Any] = (),
    ) -> LLMResponse:
        self.chiamate.append(
            {
                "system": system,
                "user_message": user_message,
                "exchanges": list(exchanges),
                "tools": list(tools),
            }
        )
        if not self._risposte:
            raise AssertionError("il valutatore ha chiamato il modello più volte del previsto")
        return self._risposte.pop(0)


def valutatore(client: ClientFinto, retriever: RetrieverFinto, **kwargs: Any):
    return LLMRequirementAssessor(
        client,  # type: ignore[arg-type]
        "v2",
        memory_tool=MemorySearchTool(retriever),  # type: ignore[arg-type]
        **kwargs,
    )


def chiamata_tool(id: str = "toolu_01") -> ToolCall:
    return ToolCall(id=id, name=SEARCH_TOOL_NAME, arguments={})


# -- il tool dichiarato ---------------------------------------------------


def test_the_tool_is_declared_to_the_model():
    client = ClientFinto(risposta(DECISIONE))
    valutatore(client, RetrieverFinto()).assess(pr(), "The system shall do it.", (), (), None)

    dichiarati = client.chiamate[0]["tools"]
    assert len(dichiarati) == 1
    assert dichiarati[0].name == SEARCH_TOOL_NAME


def test_the_tool_takes_no_arguments():
    """È la garanzia strutturale: senza parametri nello schema, il modello non
    ha nulla con cui allargare i filtri."""

    definizione = MemorySearchTool(RetrieverFinto()).definition  # type: ignore[arg-type]
    assert definizione.input_schema["properties"] == {}
    assert definizione.input_schema["required"] == []


def test_the_description_tells_the_model_the_filters_are_imposed():
    """Il modello deve sapere perché non può scegliere: altrimenti tenterebbe
    di passare argomenti e riceverebbe errori."""

    descrizione = MemorySearchTool(RetrieverFinto()).definition.description  # type: ignore[arg-type]
    assert "applied for you" in descrizione
    assert "another project" in descrizione


# -- il ciclo di invocazione ---------------------------------------------


def test_the_model_can_answer_without_calling_the_tool():
    """Il recupero guidato dall'agente è per definizione facoltativo: se il
    modello non cerca, la valutazione procede con zero invocazioni."""

    client = ClientFinto(risposta(DECISIONE))
    retriever = RetrieverFinto(requisito())

    esito = valutatore(client, retriever).assess(pr(), "The system shall do it.", (), (), None)

    assert esito.decision is AssessmentDecision.ACCEPT
    assert esito.tool_rounds == 0
    assert esito.retrieved == ()
    assert retriever.chiamate == []


def test_a_tool_request_is_served_and_the_conversation_continues():
    client = ClientFinto(
        risposta("Controllo la memoria.", tool_calls=(chiamata_tool(),)),
        risposta(DECISIONE),
    )
    retriever = RetrieverFinto(requisito(6870, "The system shall export."))

    esito = valutatore(client, retriever).assess(pr(), "The system shall do it.", (), (), None)

    assert esito.decision is AssessmentDecision.ACCEPT
    assert esito.tool_rounds == 1
    assert [r.source_pr_number for r in esito.retrieved] == [6870]
    assert len(client.chiamate) == 2


def test_the_second_call_carries_the_exchange_back_to_the_model():
    client = ClientFinto(
        risposta("Cerco.", tool_calls=(chiamata_tool("toolu_A"),)),
        risposta(DECISIONE),
    )
    valutatore(client, RetrieverFinto(requisito())).assess(pr(), "candidato", (), (), None)

    scambi = client.chiamate[1]["exchanges"]
    assert len(scambi) == 1
    _, esiti = scambi[0]
    assert esiti[0].call_id == "toolu_A"
    assert "6870" in esiti[0].content


def test_an_empty_memory_is_served_as_an_empty_list():
    client = ClientFinto(
        risposta(tool_calls=(chiamata_tool(),)),
        risposta(DECISIONE),
    )
    valutatore(client, RetrieverFinto()).assess(pr(), "candidato", (), (), None)

    _, esiti = client.chiamate[1]["exchanges"][0]
    assert esiti[0].is_error is False
    assert '"results": []' in esiti[0].content


# -- i filtri imposti dal codice -----------------------------------------


def test_the_pull_request_under_judgement_decides_the_filters():
    """Il modello non passa né progetto né data: li ricava il codice dalla
    Pull Request in esame, che è l'unica fonte legittima."""

    client = ClientFinto(risposta(tool_calls=(chiamata_tool(),)), risposta(DECISIONE))
    retriever = RetrieverFinto()
    la_pr = pr(pr_number=6880, repository="owner/uno", timestamp="2025-06-01T10:00:00Z")

    valutatore(client, retriever).assess(la_pr, "candidato", (), (), None)

    _, ricevuta = retriever.chiamate[0]
    assert ricevuta.repository == "owner/uno"
    assert ricevuta.timestamp.isoformat().startswith("2025-06-01T10:00:00")


def test_arguments_invented_by_the_model_are_ignored():
    """Anche se il modello inventasse dei parametri, non arriverebbero al
    retriever: il tool non li legge."""

    client = ClientFinto(
        risposta(
            tool_calls=(
                ToolCall(
                    id="toolu_01",
                    name=SEARCH_TOOL_NAME,
                    arguments={"repository_id": "owner/ALTRO", "before_timestamp": "2099-01-01"},
                ),
            )
        ),
        risposta(DECISIONE),
    )
    retriever = RetrieverFinto()
    valutatore(client, retriever).assess(pr(repository="owner/uno"), "c", (), (), None)

    _, ricevuta = retriever.chiamate[0]
    assert ricevuta.repository == "owner/uno"


def test_an_unknown_tool_is_reported_as_an_error_not_raised():
    """Una svista del modello non deve far perdere la Pull Request: riceve un
    errore dichiarato e può correggersi."""

    client = ClientFinto(
        risposta(tool_calls=(ToolCall(id="toolu_01", name="inventato", arguments={}),)),
        risposta(DECISIONE),
    )
    retriever = RetrieverFinto(requisito())

    esito = valutatore(client, retriever).assess(pr(), "candidato", (), (), None)

    assert esito.decision is AssessmentDecision.ACCEPT
    _, esiti = client.chiamate[1]["exchanges"][0]
    assert esiti[0].is_error is True
    assert "inventato" in esiti[0].content
    assert retriever.chiamate == []


# -- il messaggio ---------------------------------------------------------


def test_the_history_is_not_written_into_the_message_in_tool_mode():
    """Scriverlo darebbe al modello lo storico due volte e renderebbe inutile
    la scelta che questa configurazione vuole misurare."""

    client = ClientFinto(risposta(DECISIONE))
    valutatore(client, RetrieverFinto()).assess(
        pr(), "candidato", (requisito(6870),), (), None
    )

    assert "PREVIOUSLY VALIDATED REQUIREMENTS" not in client.chiamate[0]["user_message"]


def test_the_evidence_and_the_candidate_are_still_in_the_message():
    client = ClientFinto(risposta(DECISIONE))
    valutatore(client, RetrieverFinto()).assess(
        pr(title="Il titolo"), "Il candidato.", (), (), None
    )

    messaggio = client.chiamate[0]["user_message"]
    assert "Il titolo" in messaggio
    assert "Il candidato." in messaggio


# -- il limite di invocazioni --------------------------------------------


def test_a_model_that_keeps_asking_is_stopped():
    """Ogni giro è una chiamata a pagamento con l'intera conversazione
    rispedita: senza limite il costo crescerebbe senza convergere.

    Con ``max_tool_rounds=2`` il modello viene servito due volte, la terza
    riceve il rifiuto, e l'ultima chiamata gli chiede la decisione.
    """

    insistente = [risposta(tool_calls=(chiamata_tool(f"t{n}"),)) for n in range(3)]
    client = ClientFinto(*insistente, risposta(DECISIONE))

    esito = valutatore(client, RetrieverFinto(requisito()), max_tool_rounds=2).assess(
        pr(), "candidato", (), (), None
    )

    assert esito.decision is AssessmentDecision.ACCEPT
    assert esito.tool_rounds == 3
    assert len(client.chiamate) == 4


def test_the_final_call_declares_no_tools_so_the_model_must_answer():
    """È ciò che rende il limite efficace: senza tool dichiarati il modello non
    ha modo di chiederne un altro e deve produrre la decisione."""

    insistente = [risposta(tool_calls=(chiamata_tool(f"t{n}"),)) for n in range(2)]
    client = ClientFinto(*insistente, risposta(DECISIONE))

    valutatore(client, RetrieverFinto(), max_tool_rounds=1).assess(pr(), "c", (), (), None)

    assert client.chiamate[-1]["tools"] == []


def test_the_last_exchange_tells_the_model_to_decide_with_what_it_has():
    insistente = [risposta(tool_calls=(chiamata_tool(f"t{n}"),)) for n in range(2)]
    client = ClientFinto(*insistente, risposta(DECISIONE))

    valutatore(client, RetrieverFinto(), max_tool_rounds=1).assess(pr(), "c", (), (), None)

    _, esiti = client.chiamate[-1]["exchanges"][-1]
    assert esiti[0].is_error is True
    assert "decide with what you have" in esiti[0].content


# -- unione dei recuperi --------------------------------------------------


def test_repeated_retrievals_are_merged_without_duplicates():
    uno = (requisito(6870), requisito(6879))
    due = (requisito(6879), requisito(6880))

    unione = unique_by_id([uno, due])

    assert [r.source_pr_number for r in unione] == [6870, 6879, 6880]


def test_merging_nothing_gives_an_empty_tuple():
    assert unique_by_id([]) == ()


# -- la modalità senza tool resta intatta --------------------------------


def test_without_a_tool_the_assessor_behaves_as_before():
    """La configurazione di riferimento non deve cambiare: è quella con cui
    sono stati eseguiti gli esperimenti già registrati."""

    client = ClientFinto(risposta(DECISIONE))
    semplice = LLMRequirementAssessor(client, "v1")  # type: ignore[arg-type]

    esito = semplice.assess(pr(), "candidato", (requisito(6870),), (), None)

    assert esito.decision is AssessmentDecision.ACCEPT
    assert esito.tool_rounds == 0
    assert esito.retrieved == ()
    assert client.chiamate[0]["tools"] == []
    assert "PREVIOUSLY VALIDATED REQUIREMENTS" in client.chiamate[0]["user_message"]


def test_the_two_modes_are_distinguishable():
    con = valutatore(ClientFinto(), RetrieverFinto())
    senza = LLMRequirementAssessor(ClientFinto(), "v1")  # type: ignore[arg-type]

    assert con.uses_tools is True
    assert senza.uses_tools is False


# -- il prompt v2 ---------------------------------------------------------


def test_the_v2_prompt_names_the_tool():
    from are.agents.prompts import load_prompt

    testo = load_prompt("assessment", "v2")
    assert SEARCH_TOOL_NAME in testo


def test_the_v1_prompt_does_not_name_the_tool():
    """v1 descrive requisiti «forniti», non un tool da invocare: usarlo con i
    tool attivi lascerebbe il modello senza istruzioni su quando cercare."""

    from are.agents.prompts import load_prompt

    assert SEARCH_TOOL_NAME not in load_prompt("assessment", "v1")


@pytest.mark.parametrize("versione", ["v1", "v2"])
def test_both_prompt_versions_load(versione: str):
    from are.agents.prompts import load_prompt

    assert load_prompt("assessment", versione).strip()
    assert load_prompt("generation", versione).strip()
