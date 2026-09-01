"""Entry point di PR-to-Requirements: dal file JSON ai requisiti generati.

Esecuzione tipica dalla radice del repository:

    uv run python -m are --input experiments/samples/sample-scrapy_scrapy.json

Il comando carica le Pull Request, costruisce gli agenti secondo la
configurazione versionata, esegue il workflow su una PR alla volta e salva il
report dell'esecuzione in `experiments/runs/`.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from are import console
from are.agents import (
    DeterministicExtractabilityChecker,
    NullMemoryRetriever,
    WorkflowDependencies,
    build_workflow,
    load_workflow_config,
)
from are.agents.llm_agents import (
    LLMRequirementAssessor,
    LLMRequirementGenerator,
)
from are.agents.memory_tool import MemorySearchTool
from are.agents.prompts import DEFAULT_PROMPT_VERSION
from are.db import ExhaustiveRequirementRetriever, SqliteRequirementRepository
from are.env import load_environment
from are.input import PullRequestInputError, PullRequestLoader, PullRequestRecord
from are.llm import (
    MODEL_ALIASES,
    PRICING_REFERENCE_DATE,
    AgentLLMSettings,
    AnthropicLLMClient,
    LLMCallError,
    LLMConfig,
    MissingApiKeyError,
    UsageStats,
    estimate_cost_usd,
    format_usage,
    load_llm_config,
    resolve_model_alias,
)
from are.mcp_client import McpMemorySessionConfig, mcp_memory_session
from are.runner import PipelineRunner, build_run_report, save_run_report, summarize

DEFAULT_LLM_CONFIG = Path("config/llm.toml")
DEFAULT_WORKFLOW_CONFIG = Path("config/workflow.toml")
DEFAULT_OUTPUT_DIR = Path("experiments/runs")
DEFAULT_MEMORY_DIR = Path("experiments/memory")
MEMORY_SCOPE_RUN = "run"
MEMORY_SCOPE_ALL = "all"
TOOL_PROMPT_VERSION = "v2"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )
    # Le librerie HTTP e l'SDK registrano una riga per ogni chiamata: rumore
    # che nasconde il flusso del workflow.
    for rumoroso in ("httpx", "httpx2", "httpcore", "anthropic"):
        logging.getLogger(rumoroso).setLevel(logging.WARNING)

    # Le risposte dei modelli contengono caratteri che le console Windows non
    # rappresentano: senza questa protezione una riga di log andrebbe persa.
    console.make_output_resilient()
    load_environment()

    if args.check_api:
        return _check_api(args.llm_config)

    if not args.input:
        print("Argomento --input obbligatorio (oppure usare --check-api).", file=sys.stderr)
        return 2

    try:
        pull_requests = PullRequestLoader().load(args.input)
    except PullRequestInputError as exc:
        print(f"Input non valido: {exc}", file=sys.stderr)
        return 2

    if args.limit is not None:
        pull_requests = pull_requests[: args.limit]

    memory_path = Path(args.memory_db) if args.memory_db else _default_memory_path()

    # Il controllo avviene qui, prima di costruire qualsiasi client e prima di
    # aprire la sessione MCP: e' una lettura del database, non richiede il
    # modello, e saltare una Pull Request costa zero invece delle due-sei
    # chiamate che sarebbero servite per rielaborarla.
    saltate: list[tuple[PullRequestRecord, str]] = []
    if args.skip_processed:
        pull_requests, saltate = _split_already_processed(pull_requests, memory_path)
        for record, esito in saltate:
            print(f"  [SALTATA]  PR #{record.pr_number} -- gia' elaborata ({esito})")
        if saltate:
            print(
                f"{len(saltate)} Pull Request saltate, "
                f"{len(pull_requests)} da elaborare\n"
            )
        if not pull_requests:
            print("Nessuna Pull Request nuova da elaborare.")
            return 0

    llm_config = _apply_model_overrides(load_llm_config(args.llm_config), args)
    workflow_config = load_workflow_config(args.workflow_config)
    prompt_version = _resolve_prompt_version(args)

    generation_client = AnthropicLLMClient(llm_config.generation)
    assessment_client = AnthropicLLMClient(llm_config.assessment)

    # Un solo timestamp per l'esecuzione: nomina il report, nomina il database
    # e identifica le righe che questa run scrive in memoria, così i tre
    # artefatti restano agganciati fra loro.
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Con --use-mcp l'accesso alla memoria passa interamente per il server, che
    # gira in un sottoprocesso e apre lui il database. Il processo padre non ne
    # apre uno proprio: sarebbe una seconda connessione allo stesso file, usata
    # per un solo conteggio, e contraddirebbe la premessa dell'isolamento -- la
    # pipeline non deve sapere che sotto c'e' SQLite.
    if args.use_mcp:
        mcp_config = McpMemorySessionConfig(
            db_path=memory_path,
            run_id=run_stamp,
            memory_scope=args.memory_scope,
            max_requirements=workflow_config.max_memory_requirements,
        )
        with mcp_memory_session(mcp_config) as (mcp_retriever, mcp_store):
            dependencies = _build_dependencies(
                workflow_config,
                generation_client,
                assessment_client,
                prompt_version,
                retriever=mcp_retriever,
                store=mcp_store,
                assessor_tools=args.assessor_tools,
            )
            results = _run_workflow(
                pull_requests,
                dependencies,
                workflow_config,
                llm_config,
                memory_path,
                args.memory_scope,
                use_mcp=True,
            )
        stored_requirements = _count_requirements(memory_path)
    else:
        # Path storico: chiamate dirette al retriever e al repository, senza MCP.
        memory = SqliteRequirementRepository(memory_path, run_stamp)
        dependencies = _build_dependencies(
            workflow_config,
            generation_client,
            assessment_client,
            prompt_version,
            retriever=_build_retriever(memory, run_stamp, args.memory_scope, workflow_config),
            store=memory,
            assessor_tools=args.assessor_tools,
        )
        try:
            results = _run_workflow(
                pull_requests,
                dependencies,
                workflow_config,
                llm_config,
                memory_path,
                args.memory_scope,
                use_mcp=False,
            )
            stored_requirements = memory.count()
        finally:
            memory.close()

    # Ogni Pull Request elaborata viene registrata con il suo esito, anche
    # quando non ha prodotto nulla: e' cio' che permette a --skip-processed di
    # non rielaborare all'infinito una PR rifiutata o non estraibile. Avviene
    # qui e non dentro il grafo perche' e' una nota dell'esecuzione, come il
    # report, e non un fatto del dominio.
    _record_processed(memory_path, run_stamp, results)

    usage = {
        "generation": (llm_config.generation.model, generation_client.usage),
        "assessment": (llm_config.assessment.model, assessment_client.usage),
    }
    resolved_models = {
        "generation": generation_client.resolved_model,
        "assessment": assessment_client.resolved_model,
    }

    report = build_run_report(
        results,
        metadata={
            "input_file": str(args.input),
            "pull_requests": len(pull_requests),
            "skipped_already_processed": [
                {"pr_number": record.pr_number, "previous_status": esito}
                for record, esito in saltate
            ],
            "prompt_version": prompt_version,
            "workflow": {
                "assessment_enabled": workflow_config.assessment_enabled,
                "memory_enabled": workflow_config.memory_enabled,
                "max_generation_attempts": workflow_config.max_generation_attempts,
                "memory_access": "mcp" if args.use_mcp else "direct",
                "retrieval_driver": "assessor_tool" if args.assessor_tools else "graph_node",
            },
            "llm": _describe_llm_config(llm_config, resolved_models),
            "usage": _describe_usage(usage),
            "memory": {
                "database": str(memory_path),
                "run_id": run_stamp,
                "stored_requirements": stored_requirements,
            },
        },
    )
    output_path = save_run_report(report, args.output or _default_output_path(run_stamp))

    _print_summary(results, output_path, usage)
    print(f"Requisiti in memoria dopo l'esecuzione: {stored_requirements} ({memory_path})")
    return 0


def _check_api(llm_config_path: str) -> int:
    """Verifica che la chiave API funzioni, con una chiamata minima."""

    llm_config = load_llm_config(llm_config_path)
    settings = llm_config.generation
    print(f"Verifica dell'accesso al modello {settings.model}...")

    try:
        client = AnthropicLLMClient(settings)
    except MissingApiKeyError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 3

    try:
        response = client.complete(
            system="Reply with a single word.",
            user_message="Say OK.",
        )
    except LLMCallError as exc:
        print(f"\nChiamata fallita: {exc}", file=sys.stderr)
        return 3

    print(f"Risposta ricevuta: {response.text.strip()[:60]}")
    print(f"Modello effettivo: {response.model}")
    print(f"Consumo: {format_usage(settings.model, client.usage)}")
    print("\nAccesso al modello funzionante.")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="are",
        description="Ricostruisce requisiti funzionali dalle Pull Request di un file JSON.",
    )
    parser.add_argument(
        "--input",
        help="file JSON normalizzato con le Pull Request",
    )
    parser.add_argument(
        "--check-api",
        action="store_true",
        help="verifica che la chiave API funzioni, con una sola chiamata minima, "
        "senza elaborare Pull Request",
    )
    parser.add_argument(
        "--output",
        help="file JSON del report (default: experiments/runs/run-<timestamp>.json)",
    )
    parser.add_argument(
        "--memory-scope",
        choices=(MEMORY_SCOPE_RUN, MEMORY_SCOPE_ALL),
        default=MEMORY_SCOPE_RUN,
        help="quali requisiti storici puo' vedere il valutatore. "
        "'run' (predefinito): solo quelli prodotti da questa esecuzione, cosi' due "
        "esecuzioni restano confrontabili. "
        "'all': quelli di tutte le esecuzioni, cioe' una memoria che si accumula "
        "davvero nel tempo -- da usare una volta sola per corpus, perche' "
        "rielaborando le stesse Pull Request la memoria si riempie di varianti "
        "dello stesso caso e il valutatore le vede come duplicati",
    )
    parser.add_argument(
        "--memory-db",
        help="database SQLite dei requisiti accettati "
        "(default: experiments/memory/pr-to-requirements.db)",
    )
    parser.add_argument(
        "--llm-config",
        default=DEFAULT_LLM_CONFIG,
        help=f"configurazione dei modelli (default: {DEFAULT_LLM_CONFIG})",
    )
    parser.add_argument(
        "--workflow-config",
        default=DEFAULT_WORKFLOW_CONFIG,
        help=f"configurazione del workflow (default: {DEFAULT_WORKFLOW_CONFIG})",
    )
    parser.add_argument(
        "--prompt-version",
        default=None,
        help=f"versione dei prompt da usare (default: {DEFAULT_PROMPT_VERSION}, "
        f"oppure {TOOL_PROMPT_VERSION} con --assessor-tools)",
    )
    alias = ", ".join(MODEL_ALIASES)
    parser.add_argument(
        "--model",
        help=f"modello per entrambi gli agenti: {alias}, oppure un identificativo completo. "
        "Prevale su config/llm.toml",
    )
    parser.add_argument(
        "--generation-model",
        help="modello del solo Generation Agent; prevale su --model",
    )
    parser.add_argument(
        "--assessment-model",
        help="modello del solo Assessment Agent; prevale su --model",
    )
    parser.add_argument(
        "--choose-model",
        action="store_true",
        help="chiede il modello all'avvio con un menu numerato (solo per prove manuali)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="elabora soltanto le prime N Pull Request del file (utile per contenere i costi)",
    )
    parser.add_argument(
        "--use-mcp",
        action="store_true",
        help="accede alla memoria (retrieval e persistenza) attraverso il "
        "server MCP invece che chiamando direttamente il repository/retriever. "
        "Il server viene avviato come sottoprocesso stdio e resta in vita per "
        "tutto il run.",
    )
    parser.add_argument(
        "--assessor-tools",
        action="store_true",
        help="il valutatore interroga la memoria da se', invocando un tool, invece "
        "di riceverne il contenuto gia' pronto nel messaggio. Il recupero smette "
        "di essere deterministico: il modello puo' non cercare affatto. Seleziona "
        "da solo la versione v2 del prompt, che descrive il tool, a meno che "
        "--prompt-version non sia indicata esplicitamente",
    )
    parser.add_argument(
        "--skip-processed",
        action="store_true",
        help="salta le Pull Request gia' elaborate in precedenza sullo stesso "
        "progetto, riconosciute dal numero. Nessuna chiamata al modello: e' un "
        "controllo sul database. Da tenere spento quando si rielabora lo stesso "
        "corpus di proposito, per esempio per misurare la variabilita' fra repliche",
    )
    parser.add_argument("--verbose", action="store_true", help="log di dettaglio")
    return parser.parse_args(argv)


def _apply_model_overrides(config: LLMConfig, args: argparse.Namespace) -> LLMConfig:
    """Sostituisce i modelli della configurazione con quelli richiesti a riga di comando.

    Le opzioni specifiche per agente prevalgono su ``--model``, che a sua volta
    prevale sul file di configurazione. Con ``--choose-model`` la scelta viene
    chiesta all'avvio: comoda per le prove manuali, da evitare negli script,
    dove conviene indicare il modello esplicitamente perché resti registrato.
    """

    scelta = args.model
    if args.choose_model and not scelta:
        scelta = _ask_model()

    generation = args.generation_model or scelta
    assessment = args.assessment_model or scelta

    return LLMConfig(
        generation=_with_model(config.generation, generation),
        assessment=_with_model(config.assessment, assessment),
    )


def _with_model(settings: AgentLLMSettings, model: str | None) -> AgentLLMSettings:
    if model is None:
        return settings
    return replace(settings, model=resolve_model_alias(model))


def _ask_model() -> str | None:
    """Menu numerato per scegliere il modello nelle prove manuali.

    Restituisce ``None`` quando si sceglie di mantenere la configurazione.
    """

    voci = list(MODEL_ALIASES.items())
    print("Scegli il modello da usare per questa esecuzione:")
    for numero, (alias, identificativo) in enumerate(voci, start=1):
        print(f"  {numero}) {alias:<8} {identificativo}")
    print(f"  {len(voci) + 1}) usa i modelli indicati in config/llm.toml")

    while True:
        risposta = input("Numero: ").strip()
        if risposta.isdigit():
            scelto = int(risposta)
            if 1 <= scelto <= len(voci):
                alias = voci[scelto - 1][0]
                print()
                return alias
            if scelto == len(voci) + 1:
                print()
                return None
        print("Scelta non valida.")


def _describe_llm_config(
    config: LLMConfig,
    resolved_models: dict[str, str | None] | None = None,
) -> dict[str, dict[str, object]]:
    resolved = resolved_models or {}
    return {
        "generation": _describe_agent_settings(config.generation, resolved.get("generation")),
        "assessment": _describe_agent_settings(config.assessment, resolved.get("assessment")),
    }


def _describe_agent_settings(
    settings: AgentLLMSettings,
    resolved_model: str | None = None,
) -> dict[str, object]:
    return {
        "model": settings.model,
        # Versione datata restituita dal fornitore: è il dato da citare per la
        # riproducibilità (Decisione 3.2, §4.4).
        "resolved_model": resolved_model,
        "max_tokens": settings.max_tokens,
        "effort": settings.effort,
    }


def _describe_usage(usage: dict[str, tuple[str, UsageStats]]) -> dict[str, object]:
    """Consumo per agente più il totale, con la stima di costo (Decisione 3.2, §6)."""

    per_agent: dict[str, object] = {}
    totale = UsageStats()
    costo_totale = 0.0
    costo_noto = True

    for agente, (model, stats) in usage.items():
        costo = estimate_cost_usd(model, stats)
        per_agent[agente] = {
            "model": model,
            "calls": stats.calls,
            "input_tokens": stats.input_tokens,
            "output_tokens": stats.output_tokens,
            "estimated_cost_usd": round(costo, 6) if costo is not None else None,
        }
        totale += stats
        if costo is None:
            costo_noto = False
        else:
            costo_totale += costo

    return {
        "per_agent": per_agent,
        "total_calls": totale.calls,
        "total_input_tokens": totale.input_tokens,
        "total_output_tokens": totale.output_tokens,
        "total_estimated_cost_usd": round(costo_totale, 6) if costo_noto else None,
        "pricing_reference_date": PRICING_REFERENCE_DATE,
    }


def _resolve_prompt_version(args: argparse.Namespace) -> str:
    """Sceglie la versione dei prompt, tenendo conto di ``--assessor-tools``.

    La v1 descrive requisiti «forniti» e non nomina alcun tool: usarla con il
    recupero guidato dall'agente lascerebbe il modello senza istruzioni su
    quando cercare. La v2 viene quindi selezionata da sola.

    L'opzione ha valore predefinito ``None`` proprio per distinguere «non
    indicata» da «indicata e uguale al predefinito»: una scelta dichiarata
    dall'utente non va sovrascritta in silenzio, nemmeno quando coincide con
    il valore che avremmo usato comunque.
    """

    if args.prompt_version is not None:
        return args.prompt_version
    if not args.assessor_tools:
        return DEFAULT_PROMPT_VERSION
    print(f"Recupero guidato dall'agente: uso i prompt {TOOL_PROMPT_VERSION}")
    return TOOL_PROMPT_VERSION


def _default_output_path(stamp: str) -> Path:
    return DEFAULT_OUTPUT_DIR / f"run-{stamp}.json"


def _build_dependencies(
    workflow_config,
    generation_client: AnthropicLLMClient,
    assessment_client: AnthropicLLMClient,
    prompt_version: str,
    *,
    retriever,
    store,
    assessor_tools: bool = False,
) -> WorkflowDependencies:
    """Costruisce ``WorkflowDependencies`` con retriever e store iniettati.

    L'unica differenza fra il path MCP e quello diretto e' quale
    implementazione di ``retriever``/``store`` viene passata: il grafo non se
    ne accorge, perche' entrambe rispettano lo stesso protocollo.

    Con ``assessor_tools`` il recupero cambia padrone. Il retriever vero passa
    al tool del valutatore, mentre al grafo ne viene dato uno inerte: cosi' il
    nodo ``retrieve_memory`` non recupera nulla e la ricerca avviene una volta
    sola, quando il modello decide di chiederla. Il grafo non ha bisogno di
    sapere in quale delle due configurazioni si trova.
    """

    if workflow_config.assessment_enabled:
        assessor = LLMRequirementAssessor(
            assessment_client,
            prompt_version,
            memory_tool=MemorySearchTool(retriever) if assessor_tools else None,
        )
    else:
        assessor = None

    return WorkflowDependencies(
        extractability_checker=DeterministicExtractabilityChecker(
            workflow_config.min_evidence_characters
        ),
        generator=LLMRequirementGenerator(generation_client, prompt_version),
        assessor=assessor,
        retriever=NullMemoryRetriever() if assessor_tools else retriever,
        store=store,
    )


def _run_workflow(
    pull_requests,
    dependencies: WorkflowDependencies,
    workflow_config,
    llm_config: LLMConfig,
    memory_path: Path,
    memory_scope: str,
    *,
    use_mcp: bool,
) -> list:
    """Costruisce il grafo, stampa il preambolo dell'esecuzione e lancia il runner."""

    graph = build_workflow(dependencies, workflow_config)
    runner = PipelineRunner(graph, chronological=True)

    accesso = "via MCP (server come sottoprocesso)" if use_mcp else "chiamata diretta"
    print(
        f"Elaborazione di {len(pull_requests)} Pull Request "
        f"(assessment={workflow_config.assessment_enabled}, "
        f"recupero dalla memoria={workflow_config.memory_enabled})"
    )
    print(
        f"Modelli: generazione={llm_config.generation.model}, "
        f"valutazione={llm_config.assessment.model}"
    )
    ambito = (
        "solo questa esecuzione" if memory_scope == MEMORY_SCOPE_RUN else "tutte le esecuzioni"
    )
    print(f"Memoria: {memory_path}  (accesso: {accesso}; il valutatore vede: {ambito})\n")

    return runner.run(pull_requests)


def _build_retriever(
    memory: SqliteRequirementRepository,
    run_stamp: str,
    scope: str,
    workflow_config,
) -> ExhaustiveRequirementRetriever:
    """Costruisce il recupero dei requisiti storici secondo l'ambito richiesto.

    Con ``run`` ogni esecuzione vede soltanto sé stessa, anche condividendo il
    file con le altre: è la condizione perché due configurazioni siano
    confrontabili. Con ``all`` la memoria si accumula davvero fra esecuzioni,
    che è il comportamento previsto dalla Decisione 3.3 per l'uso reale ma che
    negli esperimenti falserebbe i confronti.
    """

    return ExhaustiveRequirementRetriever(
        memory,
        run_id=run_stamp if scope == MEMORY_SCOPE_RUN else None,
        max_requirements=workflow_config.max_memory_requirements,
    )


def _split_already_processed(
    pull_requests: list[PullRequestRecord],
    memory_path: Path,
) -> tuple[list[PullRequestRecord], list[tuple[PullRequestRecord, str]]]:
    """Separa le Pull Request nuove da quelle gia' elaborate in precedenza.

    Il riconoscimento e' per progetto e numero: la stessa Pull Request non viene
    rielaborata, qualunque esito avesse avuto. Una rifiutata o non estraibile e'
    stata elaborata comunque, e rielaborarla significherebbe pagare per
    riscoprire la stessa cosa.

    Il database viene aperto e chiuso qui, prima che la sessione MCP esista: e'
    una lettura, e un file mancante e' semplicemente un progetto mai visto.
    """

    if not memory_path.exists():
        return pull_requests, []

    with SqliteRequirementRepository(memory_path, "lettura") as repository:
        gia_viste: dict[str, dict[int, str]] = {}
        nuove: list[PullRequestRecord] = []
        saltate: list[tuple[PullRequestRecord, str]] = []
        for record in pull_requests:
            if record.repository not in gia_viste:
                gia_viste[record.repository] = repository.processed_pull_requests(
                    record.repository
                )
            esito = gia_viste[record.repository].get(record.pr_number)
            if esito is None:
                nuove.append(record)
            else:
                saltate.append((record, esito))
    return nuove, saltate


def _record_processed(memory_path: Path, run_stamp: str, results: list) -> None:
    """Annota l'esito di ogni Pull Request elaborata in questa esecuzione.

    Un errore tecnico non conta come elaborazione: la Pull Request non ha
    ricevuto un giudizio, e alla prossima esecuzione va ritentata.
    """

    with SqliteRequirementRepository(memory_path, run_stamp) as repository:
        for result in results:
            if not result.succeeded:
                continue
            stato = result.final_state["final_status"]
            if stato is None:
                continue
            repository.record_processed(result.pull_request, stato.value)


def _count_requirements(memory_path: Path) -> int:
    """Conta le righe del database a esecuzione conclusa.

    Il conteggio e' diagnostica del runner, non memoria del workflow: si apre
    una connessione breve al solo scopo di riportare il numero nel report,
    dopo che il server MCP e' terminato e ha rilasciato il file.
    """

    with SqliteRequirementRepository(memory_path, "readonly") as repository:
        return repository.count()


def _default_memory_path() -> Path:
    """Un unico database per tutte le esecuzioni.

    L'isolamento fra esecuzioni non è affidato al file ma alla colonna
    ``run_id``: il recupero filtra su di essa, quindi ogni run si comporta come
    se partisse da una memoria vuota. In cambio resta un solo artefatto da
    aprire, sfogliare e allegare, e confrontare due esecuzioni diventa una
    interrogazione invece di un confronto fra file.
    """

    return DEFAULT_MEMORY_DIR / "pr-to-requirements.db"


def _print_summary(
    results: list,
    output_path: Path,
    usage: dict[str, tuple[str, UsageStats]] | None = None,
) -> None:
    for result in results:
        pull_request = result.pull_request
        if not result.succeeded:
            print(f"PR #{pull_request.pr_number}: ERRORE - {result.error}")
            continue
        state = result.final_state
        status = state["final_status"].value if state["final_status"] else "UNKNOWN"
        print(f"PR #{pull_request.pr_number}: {status}")
        if state["accepted_requirement"]:
            print(f"   {state['accepted_requirement']}")

    print("\nRiepilogo:")
    for status, count in sorted(summarize(results).items()):
        print(f"  {status}: {count}")

    if usage:
        print("\nConsumo:")
        for agente, (model, stats) in usage.items():
            if stats.calls:
                print(f"  {agente}: {format_usage(model, stats)}")

    print(f"\nReport salvato in: {output_path}")


if __name__ == "__main__":
    raise SystemExit(main())
