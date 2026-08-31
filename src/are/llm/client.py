"""Client LLM di PR-to-Requirements: astrazione sopra il fornitore (Decisione 3.2).

Gli agenti dipendono soltanto dal protocollo ``LLMClient``; il fornitore
concreto (oggi Anthropic) resta un dettaglio sostituibile via configurazione.

Il client offre due modalita'. ``complete`` esegue uno scambio isolato:
un messaggio, una risposta testuale, nessuno stato. ``converse`` aggiunge la
possibilita' di dichiarare dei tool e di proseguire la conversazione dopo che
il modello ne ha invocato uno.

Le due modalita' convivono perche' servono a cose diverse. Il recupero
deterministico dalla memoria non ha bisogno di tool: e' il grafo a cercare, e
al modello arriva un messaggio gia' completo. I tool servono quando e' il
modello a decidere se e quando cercare. Entrambe restano disponibili come
condizioni sperimentali distinte.

Anche con i tool la conversazione **non e' tenuta dal client**: chi chiama
passa gli scambi gia' avvenuti a ogni invocazione. Il client resta senza
stato, come il resto del sistema, e due chiamate identiche producono la
stessa richiesta.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

import anthropic

from .config import AgentLLMSettings
from .exceptions import LLMCallError, MissingApiKeyError
from .pricing import UsageStats

API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Un tool dichiarato al modello.

    ``input_schema`` e' uno JSON Schema: descrive gli argomenti che il modello
    puo' produrre. Non tutti i parametri accettati dal tool sottostante devono
    comparire qui -- quelli che il chiamante impone (per esempio i filtri di
    progetto e di data) restano fuori dallo schema, cosi' il modello non puo'
    scegliere valori diversi da quelli previsti.
    """

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """Una invocazione richiesta dal modello.

    ``id`` va restituito insieme al risultato: e' cio' che permette al modello
    di riagganciare la risposta alla richiesta quando ne ha fatte piu' d'una
    nello stesso turno.
    """

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolResult:
    """L'esito di un tool, da rimandare al modello.

    ``content`` e' testo: qualunque struttura va serializzata da chi esegue il
    tool. ``is_error`` segnala al modello che l'invocazione e' fallita, cosi'
    che possa correggere gli argomenti o rinunciare, invece di ricevere un
    esito ambiguo.
    """

    call_id: str
    content: str
    is_error: bool = False


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Risposta di una chiamata LLM, con i dati necessari a log e costi.

    ``input_tokens`` e ``output_tokens`` alimentano il tracciamento dei costi
    per esecuzione richiesto dalla Decisione 3.2.

    ``tool_calls`` e' vuoto nella modalita' senza tool e in ogni risposta
    conclusiva. Quando non lo e', ``stop_reason`` vale ``"tool_use"``: il
    modello si e' fermato a meta' e attende i risultati per proseguire.
    """

    text: str
    model: str
    stop_reason: str | None
    input_tokens: int
    output_tokens: int
    tool_calls: tuple[ToolCall, ...] = field(default_factory=tuple)

    @property
    def wants_tools(self) -> bool:
        """Il modello ha interrotto la risposta per invocare almeno un tool."""

        return bool(self.tool_calls)


class LLMClient(Protocol):
    """Interfaccia unica usata dagli agenti per invocare un LLM."""

    def complete(self, *, system: str, user_message: str) -> LLMResponse:
        """Esegue una singola richiesta e restituisce la risposta testuale."""
        ...


class ConversingLLMClient(LLMClient, Protocol):
    """Client che sa anche dichiarare tool e proseguire una conversazione.

    E' un protocollo distinto da ``LLMClient`` per non invalidare i doppi di
    prova che implementano il solo ``complete``: un agente che non usa i tool
    continua a dipendere dall'interfaccia piu' stretta.
    """

    def converse(
        self,
        *,
        system: str,
        user_message: str,
        exchanges: Sequence[tuple[LLMResponse, Sequence[ToolResult]]] = (),
        tools: Sequence[ToolDefinition] = (),
    ) -> LLMResponse:
        """Prosegue la conversazione dopo gli scambi gia' avvenuti."""
        ...


class AnthropicLLMClient:
    """Implementazione di ``LLMClient`` basata sull'SDK ufficiale Anthropic.

    I parametri di generazione arrivano da ``AgentLLMSettings`` e vengono
    inviati identici a ogni chiamata: nessun valore viene deciso nel codice.
    """

    def __init__(
        self,
        settings: AgentLLMSettings,
        *,
        api_key: str | None = None,
        sdk_client: anthropic.Anthropic | None = None,
    ) -> None:
        self._settings = settings
        self._usage = UsageStats()
        self._resolved_model: str | None = None
        if sdk_client is not None:
            self._client = sdk_client
        else:
            key = api_key or os.environ.get(API_KEY_ENV_VAR)
            if not key:
                raise MissingApiKeyError(API_KEY_ENV_VAR)
            self._client = anthropic.Anthropic(api_key=key)

    @property
    def settings(self) -> AgentLLMSettings:
        return self._settings

    @property
    def usage(self) -> UsageStats:
        """Consumo cumulato dall'inizio dell'esecuzione (Decisione 3.2, §6)."""
        return self._usage

    @property
    def resolved_model(self) -> str | None:
        """Versione esatta del modello che ha risposto, es. ``...-20251001``.

        La configurazione indica un alias di famiglia (``claude-haiku-4-5``);
        il fornitore lo risolve in una versione datata, che è il dato da
        riportare per la riproducibilità (Decisione 3.2, §4.4). Vale ``None``
        finché non è stata effettuata alcuna chiamata.
        """
        return self._resolved_model

    def complete(self, *, system: str, user_message: str) -> LLMResponse:
        """Invia la richiesta al modello configurato.

        E' il caso particolare di ``converse`` senza tool e senza scambi
        precedenti: la richiesta prodotta e' identica a quella di prima che i
        tool esistessero.

        Raises:
            LLMCallError: per qualunque errore tecnico del fornitore (rete,
                autenticazione, rate limit, errori server). L'eccezione
                originale resta disponibile come causa.
        """

        return self.converse(system=system, user_message=user_message)

    def converse(
        self,
        *,
        system: str,
        user_message: str,
        exchanges: Sequence[tuple[LLMResponse, Sequence[ToolResult]]] = (),
        tools: Sequence[ToolDefinition] = (),
    ) -> LLMResponse:
        """Invia la conversazione al modello, con gli eventuali tool dichiarati.

        ``exchanges`` contiene le coppie (risposta del modello, risultati che
        gli abbiamo restituito) gia' avvenute in questo scambio. Il client le
        ricostruisce nel formato del fornitore a ogni chiamata: non conserva
        nulla fra un'invocazione e l'altra.

        Il costo cresce a ogni giro, perche' l'intera conversazione viene
        rispedita. E' il motivo per cui chi chiama deve porre un limite al
        numero di giri.

        Raises:
            LLMCallError: per qualunque errore tecnico del fornitore.
        """

        params: dict[str, Any] = {
            "model": self._settings.model,
            "max_tokens": self._settings.max_tokens,
            "system": system,
            "messages": _build_messages(user_message, exchanges),
        }
        if self._settings.effort is not None:
            params["output_config"] = {"effort": self._settings.effort}
        if tools:
            params["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in tools
            ]

        try:
            response = self._client.messages.create(**params)
        except anthropic.APIError as exc:
            raise LLMCallError(self._settings.model, str(exc)) from exc

        text = "".join(block.text for block in response.content if block.type == "text")
        tool_calls = tuple(
            ToolCall(id=block.id, name=block.name, arguments=dict(block.input or {}))
            for block in response.content
            if block.type == "tool_use"
        )
        self._resolved_model = response.model
        self._usage += UsageStats(
            calls=1,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return LLMResponse(
            text=text,
            model=response.model,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            tool_calls=tool_calls,
        )


def _build_messages(
    user_message: str,
    exchanges: Sequence[tuple[LLMResponse, Sequence[ToolResult]]],
) -> list[dict[str, Any]]:
    """Ricostruisce la conversazione nel formato dell'API.

    Il turno del modello viene ricomposto dai nostri tipi -- testo piu'
    invocazioni -- invece di conservare gli oggetti dell'SDK. Cosi' il
    fornitore resta un dettaglio del client e non entra nello stato del
    chiamante (Decisione 3.2, §4.3).
    """

    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]

    for risposta, risultati in exchanges:
        blocchi: list[dict[str, Any]] = []
        if risposta.text:
            blocchi.append({"type": "text", "text": risposta.text})
        for chiamata in risposta.tool_calls:
            blocchi.append(
                {
                    "type": "tool_use",
                    "id": chiamata.id,
                    "name": chiamata.name,
                    "input": chiamata.arguments,
                }
            )
        messages.append({"role": "assistant", "content": blocchi})
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": esito.call_id,
                        "content": esito.content,
                        "is_error": esito.is_error,
                    }
                    for esito in risultati
                ],
            }
        )

    return messages


def serialize_tool_content(value: Any) -> str:
    """Prepara il risultato di un tool per essere rimandato al modello.

    Il protocollo trasporta testo: una struttura va serializzata. Si usa JSON
    perche' e' la stessa forma in cui i tool MCP rispondono, e perche' il
    modello la legge senza ambiguita'.
    """

    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)
