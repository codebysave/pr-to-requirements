"""Client LLM di PR4Requirements: astrazione sopra il fornitore (Decisione 3.2).

Gli agenti dipendono soltanto dal protocollo ``LLMClient``; il fornitore
concreto (oggi Anthropic) resta un dettaglio sostituibile via configurazione.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

import anthropic

from .config import AgentLLMSettings
from .exceptions import LLMCallError, MissingApiKeyError

API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Risposta di una chiamata LLM, con i dati necessari a log e costi.

    ``input_tokens`` e ``output_tokens`` alimentano il tracciamento dei costi
    per esecuzione richiesto dalla Decisione 3.2.
    """

    text: str
    model: str
    stop_reason: str | None
    input_tokens: int
    output_tokens: int


class LLMClient(Protocol):
    """Interfaccia unica usata dagli agenti per invocare un LLM."""

    def complete(self, *, system: str, user_message: str) -> LLMResponse:
        """Esegue una singola richiesta e restituisce la risposta testuale."""
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

    def complete(self, *, system: str, user_message: str) -> LLMResponse:
        """Invia la richiesta al modello configurato.

        Raises:
            LLMCallError: per qualunque errore tecnico del fornitore (rete,
                autenticazione, rate limit, errori server). L'eccezione
                originale resta disponibile come causa.
        """

        params: dict[str, Any] = {
            "model": self._settings.model,
            "max_tokens": self._settings.max_tokens,
            "temperature": self._settings.temperature,
            "system": system,
            "messages": [{"role": "user", "content": user_message}],
        }
        if self._settings.top_p is not None:
            params["top_p"] = self._settings.top_p

        try:
            response = self._client.messages.create(**params)
        except anthropic.APIError as exc:
            raise LLMCallError(self._settings.model, str(exc)) from exc

        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResponse(
            text=text,
            model=response.model,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
