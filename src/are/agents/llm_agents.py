"""Implementazioni LLM delle porte del workflow (Decisioni 3.1 e 3.5).

Ogni agente traduce lo stato corrente in un messaggio, invoca il client LLM
configurato e converte la risposta in un tipo strutturato del workflow. Il
parsing è volutamente severo: una risposta malformata solleva un errore
esplicito invece di produrre un requisito o una decisione inventati.

Il formato di scambio è JSON prodotto dal modello e validato qui, non una
funzionalità proprietaria del fornitore: questo mantiene l'astrazione della
Decisione 3.2 (§4.3) e permette di sostituire il backend LLM senza modificare
gli agenti.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Sequence

from are.input import PullRequestRecord
from are.llm import LLMClient

from .prompts import (
    ASSESSMENT_AGENT,
    DEFAULT_PROMPT_VERSION,
    EXTRACTABILITY_AGENT,
    GENERATION_AGENT,
    load_prompt,
)
from .state import (
    AssessmentDecision,
    AssessmentFeedback,
    AssessmentResult,
    Extractability,
    ExtractabilityResult,
    RetrievedRequirement,
)

logger = logging.getLogger(__name__)

MAX_REASON_LENGTH = 500
_PREVIEW_LENGTH = 200


class AgentResponseError(Exception):
    """La risposta del modello non rispetta il contratto atteso dall'agente."""

    def __init__(self, agent: str, reason: str, raw_response: str) -> None:
        self.agent = agent
        self.reason = reason
        self.raw_response = raw_response
        preview = raw_response.strip().replace("\n", " ")
        if len(preview) > _PREVIEW_LENGTH:
            preview = preview[:_PREVIEW_LENGTH] + "..."
        super().__init__(
            f'Risposta non valida dall\'agente "{agent}": {reason}. Ricevuto: "{preview}"'
        )


def parse_json_object(text: str, agent: str) -> dict[str, Any]:
    """Estrae l'oggetto JSON dalla risposta del modello.

    Tollera il caso frequente in cui il modello racchiude il JSON in un blocco
    di codice markdown o lo accompagna con testo introduttivo, ma non accetta
    risposte prive di un oggetto JSON valido.

    Raises:
        AgentResponseError: se non è possibile ricavare un oggetto JSON.
    """

    candidate = text.strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise AgentResponseError(agent, "nessun oggetto JSON trovato", text) from None
        try:
            parsed = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError as exc:
            raise AgentResponseError(agent, f"JSON non valido ({exc.msg})", text) from exc

    if not isinstance(parsed, dict):
        raise AgentResponseError(agent, "la risposta non è un oggetto JSON", text)
    return parsed


def _require_non_empty_string(data: dict[str, Any], field: str, agent: str, raw: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise AgentResponseError(agent, f'campo "{field}" mancante o non valido', raw)
    return value.strip()


def _string_list(data: dict[str, Any], field: str, agent: str, raw: str) -> tuple[str, ...]:
    value = data.get(field, [])
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AgentResponseError(agent, f'campo "{field}" deve essere una lista di stringhe', raw)
    return tuple(item.strip() for item in value if item.strip())


def _format_pull_request(pull_request: PullRequestRecord) -> str:
    return f"PULL REQUEST TITLE:\n{pull_request.title}\n\nPULL REQUEST BODY:\n{pull_request.body}"


def _format_feedback(feedback: AssessmentFeedback) -> str:
    blocks: list[str] = []
    for label, values in (
        ("Issues", feedback.issues),
        ("Unsupported claims", feedback.unsupported_claims),
        ("Missing information", feedback.missing_information),
        ("Revision instructions", feedback.revision_instructions),
    ):
        if values:
            blocks.append(f"{label}:\n" + "\n".join(f"- {value}" for value in values))
    return "\n\n".join(blocks) if blocks else "No specific feedback provided."


class LLMExtractabilityChecker:
    """Verifica preliminare di estraibilità tramite LLM (Decisione 3.5, §6)."""

    def __init__(self, client: LLMClient, prompt_version: str = DEFAULT_PROMPT_VERSION) -> None:
        self._client = client
        self._prompt_version = prompt_version
        self._system = load_prompt(EXTRACTABILITY_AGENT, prompt_version)

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    def check(self, pull_request: PullRequestRecord) -> ExtractabilityResult:
        response = self._client.complete(
            system=self._system,
            user_message=_format_pull_request(pull_request),
        )
        data = parse_json_object(response.text, EXTRACTABILITY_AGENT)

        raw_decision = _require_non_empty_string(
            data, "extractability", EXTRACTABILITY_AGENT, response.text
        ).upper()
        try:
            decision = Extractability(raw_decision)
        except ValueError as exc:
            raise AgentResponseError(
                EXTRACTABILITY_AGENT,
                f'esito "{raw_decision}" non riconosciuto',
                response.text,
            ) from exc

        raw_reason = data.get("reason", "")
        reason = raw_reason.strip()[:MAX_REASON_LENGTH] if isinstance(raw_reason, str) else ""
        return ExtractabilityResult(decision=decision, reason=reason)


class LLMRequirementGenerator:
    """Requirement Generation Agent (Decisioni 3.1, §11 e 3.5, §4.1)."""

    def __init__(self, client: LLMClient, prompt_version: str = DEFAULT_PROMPT_VERSION) -> None:
        self._client = client
        self._prompt_version = prompt_version
        self._system = load_prompt(GENERATION_AGENT, prompt_version)

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    def generate(
        self,
        pull_request: PullRequestRecord,
        previous_candidate: str | None,
        feedback: AssessmentFeedback | None,
    ) -> str:
        response = self._client.complete(
            system=self._system,
            user_message=self._build_message(pull_request, previous_candidate, feedback),
        )
        data = parse_json_object(response.text, GENERATION_AGENT)
        return _require_non_empty_string(data, "requirement", GENERATION_AGENT, response.text)

    def _build_message(
        self,
        pull_request: PullRequestRecord,
        previous_candidate: str | None,
        feedback: AssessmentFeedback | None,
    ) -> str:
        sections = [_format_pull_request(pull_request)]

        # Al tentativo successivo passiamo soltanto evidenza, requisito
        # precedente e feedback strutturato, non l'intero storico delle
        # iterazioni (Decisione 3.5, §11).
        if previous_candidate is not None:
            sections.append(f"PREVIOUS REQUIREMENT:\n{previous_candidate}")
        if feedback is not None:
            sections.append("REVIEWER FEEDBACK:\n" + _format_feedback(feedback))
        return "\n\n".join(sections)


class LLMRequirementAssessor:
    """Requirement Assessment Agent (Decisioni 3.1, §12 e 3.5, §4.2)."""

    def __init__(self, client: LLMClient, prompt_version: str = DEFAULT_PROMPT_VERSION) -> None:
        self._client = client
        self._prompt_version = prompt_version
        self._system = load_prompt(ASSESSMENT_AGENT, prompt_version)

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    def assess(
        self,
        pull_request: PullRequestRecord,
        candidate: str,
        retrieved_requirements: Sequence[RetrievedRequirement],
    ) -> AssessmentResult:
        response = self._client.complete(
            system=self._system,
            user_message=self._build_message(pull_request, candidate, retrieved_requirements),
        )
        data = parse_json_object(response.text, ASSESSMENT_AGENT)

        raw_decision = _require_non_empty_string(
            data, "decision", ASSESSMENT_AGENT, response.text
        ).upper()
        try:
            decision = AssessmentDecision(raw_decision)
        except ValueError as exc:
            raise AgentResponseError(
                ASSESSMENT_AGENT,
                f'decisione "{raw_decision}" non riconosciuta',
                response.text,
            ) from exc

        feedback = AssessmentFeedback(
            issues=_string_list(data, "issues", ASSESSMENT_AGENT, response.text),
            unsupported_claims=_string_list(
                data, "unsupported_claims", ASSESSMENT_AGENT, response.text
            ),
            missing_information=_string_list(
                data, "missing_information", ASSESSMENT_AGENT, response.text
            ),
            revision_instructions=_string_list(
                data, "revision_instructions", ASSESSMENT_AGENT, response.text
            ),
        )

        if decision is AssessmentDecision.REVISE and not feedback.revision_instructions:
            # Senza istruzioni il tentativo successivo ripeterebbe l'errore.
            logger.warning(
                "Assessment REVISE senza revision_instructions per la PR %s", pull_request.id
            )
        return AssessmentResult(decision=decision, feedback=feedback)

    def _build_message(
        self,
        pull_request: PullRequestRecord,
        candidate: str,
        retrieved_requirements: Sequence[RetrievedRequirement],
    ) -> str:
        sections = [
            _format_pull_request(pull_request),
            f"CANDIDATE REQUIREMENT:\n{candidate}",
        ]
        if retrieved_requirements:
            lines = [
                f"- [{item.requirement_id}] {item.statement} "
                f"(similarity {item.similarity_score:.2f})"
                for item in retrieved_requirements
            ]
            sections.append("PREVIOUSLY VALIDATED REQUIREMENTS:\n" + "\n".join(lines))
        return "\n\n".join(sections)
