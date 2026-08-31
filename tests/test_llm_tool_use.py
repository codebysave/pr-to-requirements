"""La modalità con i tool del client LLM, con un doppio dell'SDK.

Nessuna chiamata di rete: il doppio registra le richieste e restituisce
risposte scritte a mano, incluse quelle che chiedono l'invocazione di un tool.

Ciò che questi test proteggono è la ricostruzione della conversazione. Il
client non conserva stato fra una chiamata e l'altra: a ogni giro rimette
insieme l'intero scambio a partire dai nostri tipi. Se quella ricomposizione
sbagliasse — un identificativo che non torna, un turno nell'ordine sbagliato —
il modello non riaggancerebbe il risultato alla propria richiesta, e il difetto
si vedrebbe solo pagando chiamate vere.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from are.llm import (
    AgentLLMSettings,
    AnthropicLLMClient,
    ToolDefinition,
    ToolResult,
    serialize_tool_content,
)

SETTINGS = AgentLLMSettings(model="claude-haiku-4-5", max_tokens=1024)

CERCA = ToolDefinition(
    name="search_requirements",
    description="Restituisce i requisiti già validati confrontabili con il candidato.",
    input_schema={"type": "object", "properties": {}, "required": []},
)


def blocco_testo(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def blocco_tool(id: str, name: str, input: dict[str, Any] | None = None) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=id, name=name, input=input or {})


def risposta(
    *blocchi: SimpleNamespace,
    stop_reason: str = "end_turn",
    input_tokens: int = 100,
    output_tokens: int = 20,
) -> SimpleNamespace:
    return SimpleNamespace(
        content=list(blocchi),
        model="claude-haiku-4-5",
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class SdkFinto:
    """Restituisce le risposte in sequenza e registra ogni richiesta."""

    def __init__(self, *risposte: SimpleNamespace) -> None:
        self.richieste: list[dict[str, Any]] = []
        self._risposte = list(risposte)
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs: Any) -> SimpleNamespace:
        self.richieste.append(kwargs)
        if not self._risposte:
            raise AssertionError("il client ha chiamato il modello più volte del previsto")
        return self._risposte.pop(0)


def client_con(*risposte: SimpleNamespace) -> tuple[AnthropicLLMClient, SdkFinto]:
    finto = SdkFinto(*risposte)
    return AnthropicLLMClient(SETTINGS, sdk_client=finto), finto  # type: ignore[arg-type]


# -- compatibilità con la modalità senza tool ----------------------------


def test_a_conversation_without_tools_sends_the_same_request_as_complete():
    """La modalità storica non deve cambiare: è la configurazione di
    riferimento degli esperimenti già eseguiti."""

    uno, finto_uno = client_con(risposta(blocco_testo("ok")))
    uno.complete(system="istruzioni", user_message="la Pull Request")

    due, finto_due = client_con(risposta(blocco_testo("ok")))
    due.converse(system="istruzioni", user_message="la Pull Request")

    assert finto_uno.richieste[0] == finto_due.richieste[0]


def test_no_tools_are_declared_when_none_are_given():
    """Dichiarare un elenco vuoto cambierebbe la richiesta senza motivo."""

    client, finto = client_con(risposta(blocco_testo("ok")))
    client.converse(system="istruzioni", user_message="messaggio")

    assert "tools" not in finto.richieste[0]


def test_a_text_answer_carries_no_tool_calls():
    client, _ = client_con(risposta(blocco_testo("The system shall do it.")))
    esito = client.converse(system="s", user_message="m", tools=[CERCA])

    assert esito.tool_calls == ()
    assert esito.wants_tools is False
    assert esito.text == "The system shall do it."


# -- dichiarazione dei tool ----------------------------------------------


def test_the_declared_tools_reach_the_request():
    client, finto = client_con(risposta(blocco_testo("ok")))
    client.converse(system="s", user_message="m", tools=[CERCA])

    dichiarati = finto.richieste[0]["tools"]
    assert len(dichiarati) == 1
    assert dichiarati[0]["name"] == "search_requirements"
    assert dichiarati[0]["description"].startswith("Restituisce")
    assert dichiarati[0]["input_schema"] == {"type": "object", "properties": {}, "required": []}


# -- lettura delle invocazioni -------------------------------------------


def test_a_tool_request_is_translated_into_a_tool_call():
    client, _ = client_con(
        risposta(
            blocco_tool("toolu_01", "search_requirements", {"candidate_text": "un requisito"}),
            stop_reason="tool_use",
        )
    )
    esito = client.converse(system="s", user_message="m", tools=[CERCA])

    assert esito.wants_tools is True
    assert esito.stop_reason == "tool_use"
    assert len(esito.tool_calls) == 1
    assert esito.tool_calls[0].id == "toolu_01"
    assert esito.tool_calls[0].name == "search_requirements"
    assert esito.tool_calls[0].arguments == {"candidate_text": "un requisito"}


def test_text_and_a_tool_request_can_arrive_together():
    """Il modello spesso motiva la ricerca prima di chiederla."""

    client, _ = client_con(
        risposta(
            blocco_testo("Controllo se esiste già un requisito simile."),
            blocco_tool("toolu_01", "search_requirements"),
            stop_reason="tool_use",
        )
    )
    esito = client.converse(system="s", user_message="m", tools=[CERCA])

    assert esito.text == "Controllo se esiste già un requisito simile."
    assert len(esito.tool_calls) == 1


def test_more_than_one_tool_can_be_requested_in_a_single_turn():
    client, _ = client_con(
        risposta(
            blocco_tool("toolu_01", "search_requirements", {"candidate_text": "primo"}),
            blocco_tool("toolu_02", "search_requirements", {"candidate_text": "secondo"}),
            stop_reason="tool_use",
        )
    )
    esito = client.converse(system="s", user_message="m", tools=[CERCA])

    assert [chiamata.id for chiamata in esito.tool_calls] == ["toolu_01", "toolu_02"]


def test_a_tool_request_without_arguments_gives_an_empty_mapping():
    """Un tool i cui parametri sono tutti imposti dal chiamante non ha nulla
    da far scegliere al modello."""

    client, _ = client_con(
        risposta(blocco_tool("toolu_01", "search_requirements", None), stop_reason="tool_use")
    )
    esito = client.converse(system="s", user_message="m", tools=[CERCA])

    assert esito.tool_calls[0].arguments == {}


# -- ricostruzione della conversazione -----------------------------------


def test_the_second_call_replays_the_whole_exchange():
    """È il cuore della modalità con i tool: il client non ricorda nulla, e
    rimette insieme la conversazione a ogni giro dai tipi che riceve."""

    primo = risposta(
        blocco_testo("Cerco."),
        blocco_tool("toolu_01", "search_requirements", {"candidate_text": "x"}),
        stop_reason="tool_use",
    )
    client, finto = client_con(primo, risposta(blocco_testo('{"decision": "ACCEPT"}')))

    apertura = client.converse(system="s", user_message="la Pull Request", tools=[CERCA])
    esiti = [ToolResult(call_id="toolu_01", content='{"results": []}')]
    client.converse(
        system="s",
        user_message="la Pull Request",
        exchanges=[(apertura, esiti)],
        tools=[CERCA],
    )

    messaggi = finto.richieste[1]["messages"]
    assert [m["role"] for m in messaggi] == ["user", "assistant", "user"]

    assert messaggi[0]["content"] == "la Pull Request"

    assistente = messaggi[1]["content"]
    assert assistente[0] == {"type": "text", "text": "Cerco."}
    assert assistente[1] == {
        "type": "tool_use",
        "id": "toolu_01",
        "name": "search_requirements",
        "input": {"candidate_text": "x"},
    }

    assert messaggi[2]["content"] == [
        {
            "type": "tool_result",
            "tool_use_id": "toolu_01",
            "content": '{"results": []}',
            "is_error": False,
        }
    ]


def test_the_identifier_links_the_result_to_its_request():
    """Senza l'identificativo il modello non saprebbe a quale delle sue
    richieste appartiene il risultato."""

    primo = risposta(
        blocco_tool("toolu_A", "search_requirements"),
        blocco_tool("toolu_B", "search_requirements"),
        stop_reason="tool_use",
    )
    client, finto = client_con(primo, risposta(blocco_testo("fatto")))

    apertura = client.converse(system="s", user_message="m", tools=[CERCA])
    client.converse(
        system="s",
        user_message="m",
        exchanges=[
            (
                apertura,
                [
                    ToolResult(call_id="toolu_A", content="risultato A"),
                    ToolResult(call_id="toolu_B", content="risultato B"),
                ],
            )
        ],
        tools=[CERCA],
    )

    risultati = finto.richieste[1]["messages"][2]["content"]
    assert [r["tool_use_id"] for r in risultati] == ["toolu_A", "toolu_B"]
    assert [r["content"] for r in risultati] == ["risultato A", "risultato B"]


def test_an_assistant_turn_without_text_carries_only_the_tool_request():
    """Un blocco di testo vuoto sarebbe rifiutato dall'API."""

    primo = risposta(blocco_tool("toolu_01", "search_requirements"), stop_reason="tool_use")
    client, finto = client_con(primo, risposta(blocco_testo("fatto")))

    apertura = client.converse(system="s", user_message="m", tools=[CERCA])
    client.converse(
        system="s",
        user_message="m",
        exchanges=[(apertura, [ToolResult(call_id="toolu_01", content="{}")])],
        tools=[CERCA],
    )

    assistente = finto.richieste[1]["messages"][1]["content"]
    assert len(assistente) == 1
    assert assistente[0]["type"] == "tool_use"


def test_a_failed_tool_is_reported_as_such_to_the_model():
    """Il modello deve poter correggere gli argomenti o rinunciare, invece di
    ricevere un esito ambiguo che scambierebbe per «nessun risultato»."""

    primo = risposta(blocco_tool("toolu_01", "search_requirements"), stop_reason="tool_use")
    client, finto = client_con(primo, risposta(blocco_testo("fatto")))

    apertura = client.converse(system="s", user_message="m", tools=[CERCA])
    client.converse(
        system="s",
        user_message="m",
        exchanges=[
            (
                apertura,
                [ToolResult(call_id="toolu_01", content="memoria irraggiungibile", is_error=True)],
            )
        ],
        tools=[CERCA],
    )

    assert finto.richieste[1]["messages"][2]["content"][0]["is_error"] is True


def test_three_rounds_produce_three_conversation_turns():
    primo = risposta(blocco_tool("t1", "search_requirements"), stop_reason="tool_use")
    secondo = risposta(blocco_tool("t2", "search_requirements"), stop_reason="tool_use")
    client, finto = client_con(primo, secondo, risposta(blocco_testo("fatto")))

    a = client.converse(system="s", user_message="m", tools=[CERCA])
    scambi = [(a, [ToolResult(call_id="t1", content="{}")])]
    b = client.converse(system="s", user_message="m", exchanges=scambi, tools=[CERCA])
    scambi.append((b, [ToolResult(call_id="t2", content="{}")]))
    client.converse(system="s", user_message="m", exchanges=scambi, tools=[CERCA])

    assert [m["role"] for m in finto.richieste[2]["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
    ]


# -- consumo e costi ------------------------------------------------------


def test_every_round_is_counted_in_the_usage():
    """Un giro di tool è una chiamata a pagamento in più: se non venisse
    contata, il costo riportato nel report sarebbe sottostimato."""

    primo = risposta(
        blocco_tool("t1", "search_requirements"),
        stop_reason="tool_use",
        input_tokens=1000,
        output_tokens=50,
    )
    secondo = risposta(blocco_testo("fatto"), input_tokens=1200, output_tokens=80)
    client, _ = client_con(primo, secondo)

    a = client.converse(system="s", user_message="m", tools=[CERCA])
    client.converse(
        system="s",
        user_message="m",
        exchanges=[(a, [ToolResult(call_id="t1", content="{}")])],
        tools=[CERCA],
    )

    assert client.usage.calls == 2
    assert client.usage.input_tokens == 2200
    assert client.usage.output_tokens == 130


def test_the_resolved_model_is_recorded_in_the_tool_mode_too():
    """Serve alla riproducibilità (Decisione 3.2, §4.4)."""

    client, _ = client_con(risposta(blocco_testo("ok")))
    client.converse(system="s", user_message="m", tools=[CERCA])

    assert client.resolved_model == "claude-haiku-4-5"


# -- serializzazione dei risultati ---------------------------------------


def test_a_structure_is_serialised_as_json():
    testo = serialize_tool_content({"results": [{"statement": "The system shall do it."}]})
    assert '"statement"' in testo
    assert "The system shall do it." in testo


def test_text_is_passed_through_unchanged():
    assert serialize_tool_content("già testo") == "già testo"


def test_accented_characters_survive_the_serialisation():
    """Con l'escaping predefinito di JSON il modello leggerebbe sequenze
    illeggibili al posto delle lettere accentate."""

    assert "però" in serialize_tool_content({"nota": "però"})


def test_an_empty_result_is_still_valid_content():
    assert serialize_tool_content({"results": []}) == '{\n  "results": []\n}'


# -- errori ---------------------------------------------------------------


def test_a_provider_failure_is_reported_as_a_call_error():
    """Stesso comportamento della modalità senza tool: un guasto tecnico non
    deve essere scambiato per una risposta."""

    import anthropic

    from are.llm import LLMCallError

    class SdkRotto:
        def __init__(self) -> None:
            self.messages = SimpleNamespace(create=self._create)

        def _create(self, **kwargs: Any):
            raise anthropic.APIError("rete non raggiungibile", request=None, body=None)

    client = AnthropicLLMClient(SETTINGS, sdk_client=SdkRotto())  # type: ignore[arg-type]
    with pytest.raises(LLMCallError):
        client.converse(system="s", user_message="m", tools=[CERCA])
