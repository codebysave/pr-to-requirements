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

from are import console
from are.input import PullRequestRecord
from are.llm import LLMClient, LLMResponse, ToolResult, UsageStats, estimate_cost_usd

from .memory_tool import MemorySearchTool, unique_by_id
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
    RelationClaim,
    RelationKind,
    RetrievedRequirement,
)

logger = logging.getLogger(__name__)

_PREVIEW_LENGTH = 200


def _log_call(response: LLMResponse) -> None:
    """Riporta il consumo della singola chiamata, non solo il totale finale."""

    usage = UsageStats(
        calls=1, input_tokens=response.input_tokens, output_tokens=response.output_tokens
    )
    logger.info(
        "%s",
        console.call(
            response.model,
            response.input_tokens,
            response.output_tokens,
            estimate_cost_usd(response.model, usage),
        ),
    )


def _log_exchange(system: str, user_message: str, risposta: str) -> None:
    """Registra a livello DEBUG i messaggi scambiati con il modello.

    Il prompt di sistema è lungo e identico a ogni chiamata: se ne registra
    solo la dimensione, mentre il messaggio specifico della Pull Request e la
    risposta grezza vengono riportati per intero.
    """

    if not logger.isEnabledFor(logging.DEBUG):
        return
    logger.debug("%s", console.exchange(system, user_message, risposta))


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
        parsed = _first_json_object(candidate, agent, text)

    if not isinstance(parsed, dict):
        raise AgentResponseError(agent, "la risposta non è un oggetto JSON", text)
    return parsed


_DECODER = json.JSONDecoder()


def _first_json_object(candidate: str, agent: str, raw: str) -> Any:
    """Estrae il primo oggetto JSON completo, ignorando ciò che lo circonda.

    Si legge il primo oggetto *completo* invece di ritagliare dalla prima
    graffa aperta all'ultima chiusa. La differenza conta: capita che il modello
    produca il JSON e poi continui a ragionare a voce alta ("Wait, let me
    reconsider..."). Se quel testo contiene una graffa, il ritaglio comprende
    spazzatura e la Pull Request si perde per un errore di formato invece di
    ricevere una risposta che era già completa e valida.

    Le posizioni si provano in ordine perché la risposta può cominciare con
    della prosa che contiene una graffa: la prima che apre un oggetto valido
    vince.
    """

    ultimo_errore: json.JSONDecodeError | None = None
    posizione = candidate.find("{")
    while posizione != -1:
        try:
            parsed, _ = _DECODER.raw_decode(candidate, posizione)
        except json.JSONDecodeError as exc:
            ultimo_errore = exc
        else:
            if isinstance(parsed, dict):
                return parsed
        posizione = candidate.find("{", posizione + 1)

    if ultimo_errore is None:
        raise AgentResponseError(agent, "nessun oggetto JSON trovato", raw) from None
    raise AgentResponseError(
        agent, f"JSON non valido ({ultimo_errore.msg})", raw
    ) from ultimo_errore


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


def _relation_claims(
    data: dict[str, Any],
    retrieved: Sequence[RetrievedRequirement],
    raw: str,
) -> tuple[RelationClaim, ...]:
    """Legge le relazioni dichiarate dal valutatore, verificandole.

    Una relazione viene tenuta solo se punta a una Pull Request che il modello
    ha davvero ricevuto: se non è fra i requisiti recuperati, l'osservazione
    non è verificabile e va scartata invece di finire nel database. Vale anche
    per un tipo di relazione fuori dalla tassonomia.

    Le voci malformate non sollevano: una relazione è un'informazione
    aggiuntiva, e perdere un requisito validato per un campo scritto male
    sarebbe sproporzionato. L'anomalia viene registrata nel log.
    """

    grezze = data.get("relations", [])
    if grezze is None:
        return ()
    if not isinstance(grezze, list):
        raise AgentResponseError(ASSESSMENT_AGENT, 'campo "relations" deve essere una lista', raw)

    per_pr = {item.source_pr_number: item for item in retrieved}
    dichiarate: list[RelationClaim] = []
    for voce in grezze:
        if not isinstance(voce, dict):
            logger.warning("  [VALUTA]  relazione ignorata: non è un oggetto (%r)", voce)
            continue
        tipo = str(voce.get("type", "")).strip().upper()
        try:
            kind = RelationKind(tipo)
        except ValueError:
            logger.warning("  [VALUTA]  relazione ignorata: tipo %r non riconosciuto", tipo)
            continue
        numero = voce.get("source_pr_number")
        if not isinstance(numero, int) or numero not in per_pr:
            logger.warning(
                "  [VALUTA]  relazione %s ignorata: la PR #%r non è fra quelle mostrate",
                tipo,
                numero,
            )
            continue
        motivo = voce.get("reason")
        dichiarate.append(
            RelationClaim(
                kind=kind,
                target_requirement_id=per_pr[numero].requirement_id,
                target_pr_number=numero,
                reason=motivo.strip() if isinstance(motivo, str) else "",
            )
        )
    return tuple(dichiarate)


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
        # Il generatore non conosce il numero del tentativo: la firma della
        # porta non lo prevede, e il contatore delle fasi rende comunque
        # leggibile la successione dei giri.
        logger.info(
            "%s",
            console.phase("GENERAZIONE", "prima stesura" if feedback is None else "revisione"),
        )
        if feedback is None:
            logger.info(
                "%s", console.note("scrivo il requisito dalla sola evidenza della Pull Request")
            )
        else:
            quante = len(feedback.revision_instructions)
            logger.info(
                "%s",
                console.note(
                    f"riscrivo applicando le {quante} istruzioni ricevute"
                    if quante != 1
                    else "riscrivo applicando l'istruzione ricevuta"
                ),
            )

        user_message = self._build_message(pull_request, previous_candidate, feedback)
        response = self._client.complete(system=self._system, user_message=user_message)
        _log_call(response)
        _log_exchange(self._system, user_message, response.text)

        data = parse_json_object(response.text, GENERATION_AGENT)

        # La rinuncia motivata è un esito legittimo (Decisione 3.1, §11.10):
        # sarà il valutatore a confermarla o a respingerla.
        motivo = data.get("cannot_ground")
        if isinstance(motivo, str) and motivo.strip():
            logger.info("%s", console.result("nessun requisito ricostruibile", console.STOP))
            logger.info("%s", console.items("motivo", [motivo.strip()]))
            return GenerationOutcome(refusal_reason=motivo.strip())

        requisito = _require_non_empty_string(data, "requirement", GENERATION_AGENT, response.text)
        logger.info("%s", console.result("REQUISITO"))
        logger.info("%s", console.quoted(requisito))
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
    """Requirement Assessment Agent (Decisioni 3.1, §12 e 3.5, §4.2).

    Con ``memory_tool`` valorizzato il valutatore non riceve più i requisiti
    storici già pronti nel messaggio: gli viene dichiarato un tool e decide
    lui se e quando invocarlo. È la seconda condizione sperimentale, non un
    rimpiazzo della prima (si veda il punto 6 delle domande aperte per la
    tutor).

    ``max_tool_rounds`` limita i giri di invocazione. Serve perché ogni giro è
    una chiamata a pagamento in più e la conversazione viene rispedita per
    intero: senza limite, un modello che continuasse a chiedere farebbe
    crescere il costo senza convergere.
    """

    def __init__(
        self,
        client: LLMClient,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
        *,
        memory_tool: MemorySearchTool | None = None,
        max_tool_rounds: int = 3,
    ) -> None:
        self._client = client
        self._prompt_version = prompt_version
        self._system = load_prompt(ASSESSMENT_AGENT, prompt_version)
        self._memory_tool = memory_tool
        self._max_tool_rounds = max_tool_rounds

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    @property
    def uses_tools(self) -> bool:
        """Il recupero è deciso dal modello anziché dal grafo."""

        return self._memory_tool is not None

    def assess(
        self,
        pull_request: PullRequestRecord,
        candidate: str,
        retrieved_requirements: Sequence[RetrievedRequirement],
        history: Sequence[IterationRecord] = (),
        generation_refusal: str | None = None,
    ) -> AssessmentResult:
        logger.info("%s", console.phase("VALUTAZIONE", f"tentativo {len(history) + 1}"))
        cosa = "la rinuncia del redattore" if generation_refusal else "il requisito candidato"
        logger.info("%s", console.note(f"esamino {cosa}"))
        if history:
            logger.info(
                "%s",
                console.note(
                    f"ho davanti anche i {len(history)} tentativi precedenti e i miei verdetti"
                ),
            )
        if retrieved_requirements:
            logger.info(
                "%s",
                console.note(
                    f"e {len(retrieved_requirements)} requisiti gia' validati con cui confrontarlo"
                ),
            )

        user_message = self._build_message(
            pull_request, candidate, retrieved_requirements, history, generation_refusal
        )
        if self._memory_tool is None:
            response = self._client.complete(system=self._system, user_message=user_message)
            _log_call(response)
            _log_exchange(self._system, user_message, response.text)
            recuperati: tuple[RetrievedRequirement, ...] = ()
            giri = 0
        else:
            response, recuperati, giri = self._converse_with_tools(
                user_message, pull_request, candidate
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

        visti = recuperati or tuple(retrieved_requirements)
        relazioni = _relation_claims(data, visti, response.text)

        passata = decision is AssessmentDecision.ACCEPT
        rilievi = (
            feedback.issues
            + feedback.unsupported_claims
            + feedback.missing_information
            + feedback.revision_instructions
        )
        esito = decision.value if rilievi else f"{decision.value}  {console.DOT}  nessun rilievo"
        logger.info("%s", console.result(esito, console.OK if passata else console.STOP))

        for etichetta, valori in (
            # `issues` non contiene soltanto difetti: il valutatore ci mette
            # anche le relazioni con i requisiti storici, come il prompt gli
            # chiede, e le motivazioni di un'accettazione, che non gli chiede
            # nessuno. Chiamarlo «problema» faceva leggere "problema 1 di 2"
            # sotto un ACCEPT pulito, che sembra una contraddizione e non lo e'.
            # L'etichetta neutra dice cos'e' davvero: un'osservazione.
            ("osservazione", feedback.issues),
            ("non supportato dall'evidenza", feedback.unsupported_claims),
            ("informazione mancante", feedback.missing_information),
            ("istruzione", feedback.revision_instructions),
        ):
            blocco = console.items(etichetta, list(valori))
            if blocco:
                logger.info("%s", blocco)

        if decision is AssessmentDecision.REVISE and not feedback.revision_instructions:
            # Senza istruzioni il tentativo successivo ripeterebbe l'errore.
            logger.warning(
                "  [VALUTA]  attenzione: REVISE senza istruzioni di revisione (PR %s)",
                pull_request.id,
            )
        for relazione in relazioni:
            logger.info(
                "%s",
                console.result(f"{relazione.kind} rispetto alla PR #{relazione.target_pr_number}"),
            )
            if relazione.reason:
                logger.info("%s", console.quoted(relazione.reason))

        return AssessmentResult(
            decision=decision,
            feedback=feedback,
            retrieved=recuperati,
            tool_rounds=giri,
            relations=relazioni,
        )

    def _converse_with_tools(
        self,
        user_message: str,
        pull_request: PullRequestRecord,
        candidate: str | None,
    ) -> tuple[LLMResponse, tuple[RetrievedRequirement, ...], int]:
        """Conduce la conversazione finché il modello smette di chiedere tool.

        Restituisce anche l'insieme dei requisiti che il modello ha
        effettivamente ottenuto e il numero di giri compiuti: senza questa
        traccia il report non permetterebbe di verificare se abbia cercato.
        """

        assert self._memory_tool is not None
        strumenti = [self._memory_tool.definition]
        scambi: list[tuple[LLMResponse, list[ToolResult]]] = []
        gruppi: list[tuple[RetrievedRequirement, ...]] = []

        for giro in range(self._max_tool_rounds + 1):
            response = self._client.converse(
                system=self._system,
                user_message=user_message,
                exchanges=scambi,
                tools=strumenti,
            )
            _log_call(response)
            _log_exchange(self._system, user_message, response.text)

            if not response.wants_tools:
                return response, unique_by_id(gruppi), len(scambi)

            if giro == self._max_tool_rounds:
                # Il modello continua a chiedere: si chiude lo scambio
                # rispondendo che non ci sono altre ricerche disponibili, così
                # che possa comunque produrre una decisione.
                logger.warning(
                    "  [VALUTA]  limite di %d invocazioni raggiunto (PR %s)",
                    self._max_tool_rounds,
                    pull_request.id,
                )
                scambi.append(
                    (
                        response,
                        [
                            ToolResult(
                                call_id=chiamata.id,
                                content=(
                                    "no further searches are available; "
                                    "decide with what you have"
                                ),
                                is_error=True,
                            )
                            for chiamata in response.tool_calls
                        ],
                    )
                )
                finale = self._client.converse(
                    system=self._system, user_message=user_message, exchanges=scambi
                )
                _log_call(finale)
                _log_exchange(self._system, user_message, finale.text)
                return finale, unique_by_id(gruppi), len(scambi)

            logger.info(
                "%s",
                console.note(f"il valutatore interroga la memoria ({len(response.tool_calls)})"),
            )
            esiti: list[ToolResult] = []
            for chiamata in response.tool_calls:
                esito, ottenuti = self._memory_tool.execute(chiamata, pull_request, candidate)
                esiti.append(esito)
                gruppi.append(ottenuti)
                if ottenuti:
                    logger.info("%s", console.result(f"{len(ottenuti)} requisiti recuperati"))
                    for elemento in ottenuti:
                        logger.info("%s", console.quoted(elemento.statement))
                else:
                    logger.info("%s", console.result("nessun requisito precedente", console.OK))
            scambi.append((response, esiti))

        raise AssertionError("il ciclo dei tool deve terminare con un return")

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
        # Con il tool attivo lo storico non entra nel messaggio: è il modello a
        # chiederlo. Scriverlo comunque lo darebbe due volte, e renderebbe
        # inutile la scelta che la configurazione vuole misurare.
        if retrieved_requirements and self._memory_tool is None:
            lines = [
                f"- (from Pull Request #{item.source_pr_number}) {item.statement}"
                for item in retrieved_requirements
            ]
            sections.append("PREVIOUSLY VALIDATED REQUIREMENTS:\n" + "\n".join(lines))
        return "\n\n".join(sections)
