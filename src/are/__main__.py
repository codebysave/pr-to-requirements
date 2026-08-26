"""Entry point di PR4Requirements: dal file JSON ai requisiti generati.

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
from datetime import datetime, timezone
from pathlib import Path

from are.agents import (
    WorkflowDependencies,
    build_workflow,
    load_workflow_config,
)
from are.agents.llm_agents import (
    LLMExtractabilityChecker,
    LLMRequirementAssessor,
    LLMRequirementGenerator,
)
from are.agents.prompts import DEFAULT_PROMPT_VERSION
from are.env import load_environment
from are.input import PullRequestInputError, PullRequestLoader
from are.llm import AgentLLMSettings, AnthropicLLMClient, LLMConfig, load_llm_config
from are.runner import PipelineRunner, build_run_report, save_run_report, summarize

DEFAULT_LLM_CONFIG = Path("config/llm.toml")
DEFAULT_WORKFLOW_CONFIG = Path("config/workflow.toml")
DEFAULT_OUTPUT_DIR = Path("experiments/runs")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)-8s %(message)s",
    )

    load_environment()

    try:
        pull_requests = PullRequestLoader().load(args.input)
    except PullRequestInputError as exc:
        print(f"Input non valido: {exc}", file=sys.stderr)
        return 2

    if args.limit is not None:
        pull_requests = pull_requests[: args.limit]

    llm_config = load_llm_config(args.llm_config)
    workflow_config = load_workflow_config(args.workflow_config)

    generation_client = AnthropicLLMClient(llm_config.generation)
    assessment_client = AnthropicLLMClient(llm_config.assessment)

    # Il gate di estraibilità è una fase della pipeline, non un terzo agente:
    # riusa la configurazione del Generation Agent (Decisione 3.5, §4.3).
    dependencies = WorkflowDependencies(
        extractability_checker=LLMExtractabilityChecker(generation_client, args.prompt_version),
        generator=LLMRequirementGenerator(generation_client, args.prompt_version),
        assessor=(
            LLMRequirementAssessor(assessment_client, args.prompt_version)
            if workflow_config.assessment_enabled
            else None
        ),
    )

    graph = build_workflow(dependencies, workflow_config)
    runner = PipelineRunner(graph, chronological=True)

    print(
        f"Elaborazione di {len(pull_requests)} Pull Request "
        f"(assessment={workflow_config.assessment_enabled}, "
        f"memory={workflow_config.memory_enabled})\n"
    )
    results = runner.run(pull_requests)

    report = build_run_report(
        results,
        metadata={
            "input_file": str(args.input),
            "pull_requests": len(pull_requests),
            "prompt_version": args.prompt_version,
            "workflow": {
                "assessment_enabled": workflow_config.assessment_enabled,
                "memory_enabled": workflow_config.memory_enabled,
                "max_generation_attempts": workflow_config.max_generation_attempts,
            },
            "llm": _describe_llm_config(llm_config),
        },
    )
    output_path = save_run_report(report, args.output or _default_output_path())

    _print_summary(results, output_path)
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="are",
        description="Ricostruisce requisiti funzionali dalle Pull Request di un file JSON.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="file JSON normalizzato con le Pull Request",
    )
    parser.add_argument(
        "--output",
        help="file JSON del report (default: experiments/runs/run-<timestamp>.json)",
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
        default=DEFAULT_PROMPT_VERSION,
        help=f"versione dei prompt da usare (default: {DEFAULT_PROMPT_VERSION})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="elabora soltanto le prime N Pull Request del file (utile per contenere i costi)",
    )
    parser.add_argument("--verbose", action="store_true", help="log di dettaglio")
    return parser.parse_args(argv)


def _describe_llm_config(config: LLMConfig) -> dict[str, dict[str, object]]:
    return {
        "generation": _describe_agent_settings(config.generation),
        "assessment": _describe_agent_settings(config.assessment),
    }


def _describe_agent_settings(settings: AgentLLMSettings) -> dict[str, object]:
    return {
        "model": settings.model,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "top_p": settings.top_p,
    }


def _default_output_path() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_OUTPUT_DIR / f"run-{stamp}.json"


def _print_summary(results: list, output_path: Path) -> None:
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
    print(f"\nReport salvato in: {output_path}")


if __name__ == "__main__":
    raise SystemExit(main())
