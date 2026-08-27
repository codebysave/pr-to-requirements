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
    GENERATION_AGENT,
    load_prompt,
)
from .state import (
    AssessmentDecision,
    AssessmentFeedback,
    AssessmentResult,
    GenerationOutcome,
    IterationRecord,
    RetrievedRequirement,
)

logger = logging.getLogger(__name__)

_PREVIEW_LENGTH = 200


def _log_exchange(fase: str, system: str, user_message: str, risposta: str) -> None:
    """Registra a livello DEBUG i messaggi scambiati con il modello.

    Il prompt di sistema è lungo e identico a ogni chiamata: se ne registra
    solo la dimensione, mentre il messaggio specifico della Pull Request e la
    risposta grezza vengono riportati per intero.
    """

    if not logger.isEnabledFor(logging.DEBUG):
        return
    logger.debug("")
    logger.debug("   +-- %s: messaggio inviato ---", fase)
    logger.debug("   |   (prompt di sistema: %d caratteri, dai file in prompts/)", len(system))
    for riga in user_message.splitlines():
        logger.debug("   |   %s", riga)
    logger.debug("   +-- %s: risposta ricevuta ---", fase)
    for riga in risposta.splitlines():
        logger.debug("   |   %s", riga)
    logger.debug("")


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


def _format_history(history: Sequence[IterationRecord]) -> str:
    """Riassume i tentativi già valutati: candidato prodotto e verdetto dato."""

    blocchi: list[str] = []
    for record in history:
        if record.candidate is None:
            righe = [f"Attempt {record.attempt}: no requirement produced - {record.refusal_reason}"]
        else:
            righe = [f'Attempt {record.attempt}: "{record.candidate}"']
        assessment = record.assessment
        if assessment is not None:
            righe.append(f"  You decided: {assessment.decision.value}")
            for etichetta, valori in (
                ("You reported", assessment.feedback.issues),
                ("You flagged as unsupported", assessment.feedback.unsupported_claims),
                ("You asked for", assessment.feedback.revision_instructions),
            ):
                for valore in valori:
                    righe.append(f"  {etichetta}: {valore}")
        blocchi.append("\n".join(righe))
    return "\n\n".join(blocchi)


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
    ) -> GenerationOutcome:
        if feedback is None:
            logger.info("  [GENERA]  scrivo il requisito dalla sola evidenza della PR...")
        else:
            logger.info("  [GENERA]  riscrivo il requisito applicando il feedback ricevuto...")

        user_message = self._build_message(pull_request, previous_candidate, feedback)
        response = self._client.complete(system=self._system, user_message=user_message)
        _log_exchange("GENERA", self._system, user_message, response.text)

        data = parse_json_object(response.text, GENERATION_AGENT)

        # La rinuncia motivata è un esito legittimo (Decisione 3.1, §11.10):
        # sarà il valutatore a confermarla o a respingerla.
        motivo = data.get("cannot_ground")
        if isinstance(motivo, str) and motivo.strip():
            logger.info("  [GENERA]  -> nessun requisito ricostruibile: %s", motivo.strip())
            return GenerationOutcome(refusal_reason=motivo.strip())

        requisito = _require_non_empty_string(data, "requirement", GENERATION_AGENT, response.text)
        logger.info('  [GENERA]  -> "%s"', requisito)
        return GenerationOutcome(requirement=requisito)

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
        history: Sequence[IterationRecord] = (),
        generation_refusal: str | None = None,
    ) -> AssessmentResult:
        contesto = []
        if history:
            contesto.append(f"{len(history)} tentativi precedenti")
        if retrieved_requirements:
            contesto.append(f"{len(retrieved_requirements)} requisiti storici")
        cosa = "la rinuncia del redattore" if generation_refusal else "il requisito candidato"
        if contesto:
            logger.info("  [VALUTA]  esamino %s (%s)...", cosa, ", ".join(contesto))
        else:
            logger.info("  [VALUTA]  esamino %s...", cosa)

        user_message = self._build_message(
            pull_request, candidate, retrieved_requirements, history, generation_refusal
        )
        response = self._client.complete(system=self._system, user_message=user_message)
        _log_exchange("VALUTA", self._system, user_message, response.text)
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

        logger.info("  [VALUTA]  -> %s", decision.value)
        for etichetta, valori in (
            ("problema", feedback.issues),
            ("non supportato", feedback.unsupported_claims),
            ("informazione mancante", feedback.missing_information),
            ("istruzione", feedback.revision_instructions),
        ):
            for valore in valori:
                logger.info("              %s: %s", etichetta, valore)

        if decision is AssessmentDecision.REVISE and not feedback.revision_instructions:
            # Senza istruzioni il tentativo successivo ripeterebbe l'errore.
            logger.warning(
                "  [VALUTA]  attenzione: REVISE senza istruzioni di revisione (PR %s)",
                pull_request.id,
            )
        return AssessmentResult(decision=decision, feedback=feedback)

    def _build_message(
        self,
        pull_request: PullRequestRecord,
        candidate: str | None,
        retrieved_requirements: Sequence[RetrievedRequirement],
        history: Sequence[IterationRecord] = (),
        generation_refusal: str | None = None,
    ) -> str:
        sections = [_format_pull_request(pull_request)]
        # Lo storico precede il candidato: prima si ricorda cosa si è già
        # chiesto, poi si guarda che cosa è stato prodotto in risposta.
        if history:
            sections.append("PREVIOUS ATTEMPTS:\n" + _format_history(history))
        if generation_refusal is not None:
            sections.append(
                f"THE WRITER PRODUCED NO REQUIREMENT. Their stated reason:\n{generation_refusal}"
            )
        else:
            sections.append(f"CANDIDATE REQUIREMENT:\n{candidate}")
        if retrieved_requirements:
            lines = [
                f"- [{item.requirement_id}] {item.statement} "
                f"(similarity {item.similarity_score:.2f})"
                for item in retrieved_requirements
            ]
            sections.append("PREVIOUSLY VALIDATED REQUIREMENTS:\n" + "\n".join(lines))
        return "\n\n".join(sections)
