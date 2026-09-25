# PR-to-Requirements

Automatic requirement extraction from Pull Requests using LLM-based agents.

The system reconstructs the functional requirement behind a change from the
**title and body of a Pull Request alone** — no code, no diff, no commit
history — and writes it as a single sentence in EARS form, following the
quality characteristics of ISO/IEC/IEEE 29148.

---

## How it works

Two agents alternate inside a deterministic state machine built with LangGraph.
Control flow belongs to the graph, never to the agents.

1. **Input loading** — Pull Requests are read from a normalised JSON file and
   validated field by field.
2. **Extractability gate** — a deterministic check (no model call) sets aside
   Pull Requests whose evidence is too short to support any requirement.
3. **Generation Agent** — writes one candidate requirement, or declares that
   the evidence grounds none.
4. **Assessment Agent** — judges the candidate against the evidence alone and
   returns one of four decisions: `ACCEPT`, `REVISE`, `REJECT`,
   `CONFIRM_NOT_EXTRACTABLE`.
5. **Revision loop** — on `REVISE` the generator rewrites following the
   assessor's instructions, up to `max_generation_attempts` in total.
6. **Persistence** — only accepted requirements enter the memory; the assessor
   sees the requirements already stored for the same project, so it can point
   out duplications and inconsistencies.
7. **Report** — every run writes a JSON report with the outcome of each Pull
   Request, the full revision history, the models and prompts used, and token
   consumption with a cost estimate.

Each Pull Request ends in one of four final states: `ACCEPTED`,
`NOT_EXTRACTABLE`, `REJECTED` (the assessor ruled the evidence grounds no
requirement) and `FAILED_VALIDATION` (the revision budget ran out with the
assessor still asking for changes). A technical failure does not stop the
batch: that Pull Request is recorded as `ERROR` in the report and the run
carries on.

---

## Requirements

- Python **3.11** or newer
- [uv](https://docs.astral.sh/uv/)
- An Anthropic API key

## Installation

```bash
git clone https://github.com/codebysave/pr-to-requirements.git
cd pr-to-requirements
uv sync
```

Then create your `.env` from the template and paste your key into it:

```bash
cp .env.example .env
```

```text
ANTHROPIC_API_KEY=sk-ant-...
```

`.env` is git-ignored and must never be committed. The key lives there and
nowhere else — not in `config/llm.toml`, not in the code.

## First run

Check that the key works, with one minimal call:

```bash
uv run python -m are --check-api
```

Process three Pull Requests from a sample and produce the requirements:

```bash
uv run python -m are --input experiments/samples/sample-scrapy_scrapy.json --limit 3
```

The report is written to `experiments/runs/run-<timestamp>.json`.

> **Every run calls a paid API.** Keep `--limit` on while you are trying things
> out, and check the cost estimate printed at the end of the run.

---

## Command reference

All options of `python -m are`:

| Option | What it does | Default |
|---|---|---|
| `--input PATH` | Normalised JSON file with the Pull Requests to process | — |
| `--check-api` | Verifies the API key with one minimal call and exits, without processing anything | off |
| `--output PATH` | Where to write the run report | `experiments/runs/run-<timestamp>.json` |
| `--limit N` | Processes only the first N Pull Requests of the file | all of them |
| `--model NAME` | Model for both agents: `haiku`, `sonnet`, `opus`, or a full model identifier. Overrides `config/llm.toml` | from config |
| `--generation-model NAME` | Model for the Generation Agent only; wins over `--model` | from config |
| `--assessment-model NAME` | Model for the Assessment Agent only; wins over `--model` | from config |
| `--choose-model` | Asks which model to use at start-up, with a numbered menu (manual trials only) | off |
| `--prompt-version V` | Prompt version for both agents, from `prompts/<agent>/<version>.md` | `v1` (`v2` with `--assessor-tools`) |
| `--memory-scope run\|all` | Which stored requirements the assessor may see: only this run's (`run`) or every run's (`all`) | `run` |
| `--memory-db PATH` | SQLite file holding the accepted requirements | `experiments/memory/pr-to-requirements.db` |
| `--skip-processed` | Skips Pull Requests already processed for the same project, recognised by number. A database check, no model call | off |
| `--use-mcp` | Reaches the memory through the MCP server instead of calling the repository directly. The server runs as a stdio subprocess for the whole run | off |
| `--assessor-tools` | The assessor queries the memory itself by invoking a tool, instead of receiving its content ready-made. Retrieval stops being deterministic: the model may not search at all | off |
| `--llm-config PATH` | Model configuration file | `config/llm.toml` |
| `--workflow-config PATH` | Workflow configuration file | `config/workflow.toml` |
| `--verbose` | Detailed logging | off |

---

## Recipes

**Smoke test on a single Pull Request** — the cheapest way to check that
everything is wired up:

```bash
uv run python -m are --input experiments/samples/sample-django_django.json --limit 1 --verbose
```

**Run a whole sample:**

```bash
uv run python -m are --input experiments/samples/sample-scrapy_scrapy.json
```

**Use a different model for each role** — a strong critic over a cheaper
author is the configuration the project is built around:

```bash
uv run python -m are \
  --input experiments/samples/sample-scrapy_scrapy.json \
  --generation-model sonnet \
  --assessment-model opus
```

**Build a memory that accumulates across runs** — let the assessor see
everything stored so far, and do not redo Pull Requests already handled:

```bash
uv run python -m are \
  --input experiments/samples/sample-All-Hands-AI_OpenHands.json \
  --memory-scope all \
  --skip-processed
```

**Measure variability between replicas** — same input, same settings, run it
again on purpose, so leave `--skip-processed` off and keep the scope at `run`:

```bash
uv run python -m are --input experiments/samples/sample-scrapy_scrapy.json --output experiments/runs/replica-2.json
```

**Route the memory through MCP** instead of calling it directly:

```bash
uv run python -m are --input experiments/samples/sample-scrapy_scrapy.json --use-mcp
```

**Let the assessor search the memory by itself**, as a tool call (this also
selects the `v2` prompts, which describe the tool):

```bash
uv run python -m are --input experiments/samples/sample-scrapy_scrapy.json --assessor-tools
```

**Keep an experiment's memory separate** from the main one:

```bash
uv run python -m are \
  --input experiments/samples/sample-AntonOsika_gpt-engineer.json \
  --memory-db experiments/memory/experiment-01.db \
  --output experiments/runs/experiment-01.json
```

---

## Configuration

Three files govern a run. None of them contains credentials.

### `config/llm.toml` — which model each agent uses

One block per agent, so the two roles can be given different models. The
command line overrides this file.

```toml
[generation]
model = "claude-haiku-4-5"
max_tokens = 1024

[assessment]
model = "claude-haiku-4-5"
max_tokens = 8192
```

Aliases accepted by `--model` and friends: `haiku` → `claude-haiku-4-5`,
`sonnet` → `claude-sonnet-5`, `opus` → `claude-opus-5`. Keep the assessor's
`max_tokens` generous: a truncated answer is not a degraded answer, it is a
lost one, and the Pull Request ends in `ERROR`.

### `config/workflow.toml` — how the pipeline behaves

| Key | Meaning | Default |
|---|---|---|
| `assessment_enabled` | Runs the Assessment Agent. With `false` the first candidate is accepted and stored as it is, with no review | `true` |
| `memory_enabled` | Governs **retrieval** only — whether the assessor is shown the stored requirements. Storage happens either way | `true` |
| `max_generation_attempts` | One initial generation plus up to two revisions | `3` |
| `min_evidence_characters` | Minimum combined length of title and body for a Pull Request to reach the agents. With `0`, only empty bodies are discarded | `50` |
| `max_memory_requirements` | Cap on how many stored requirements are shown to the assessor. Retrieval is exhaustive within the project and date filters; this only prevents a grown archive from silently bloating the message | `50` |

### `.env` — the API key

```text
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Input format

A JSON array of Pull Requests, each with six fields:

```json
[
  {
    "id": "scrapy-scrapy-pr-6869",
    "repository": "scrapy/scrapy",
    "pr_number": 6869,
    "timestamp": "2025-06-06T13:17:48Z",
    "title": "Fix unsafe use of eval() in scrapy/shell.py",
    "body": "Detected the use of eval(). eval() can be dangerous ..."
  }
]
```

`timestamp` is the moment the Pull Request was opened, and it is what orders
processing and filters the memory — a requirement is never compared against
one that came later. Ready-made samples live in `experiments/samples/`.

## Output: the run report

`experiments/runs/run-<timestamp>.json` has three top-level keys:

- **`run`** — input file, how many Pull Requests were processed and how many
  were skipped as already processed, prompt version, workflow and model
  settings, memory settings, token usage and cost estimate;
- **`summary`** — how many Pull Requests ended in each final state;
- **`results`** — one entry per Pull Request: final state, extractability and
  its reason, the accepted requirement, how many generation attempts it took,
  and the full iteration history with every candidate and every decision of
  the assessor.

The history is what makes a run auditable: it shows not only what the system
produced, but what it did to get there.

---

## The persistent memory

Accepted requirements are stored in a single SQLite file, by default
`experiments/memory/pr-to-requirements.db`. Three tables hold the data —
`requirements`, `requirement_relations`, `processed_pull_requests` — and three
views make it readable:

| View | What it answers |
|---|---|
| `requirements_overview` | Every stored requirement with its Pull Request, run and relations |
| `requirements_unique` | The catalogue without recognised duplicates and superseded entries |
| `relations_to_review` | The relations the assessor declared that deserve a human decision |

Relations the assessor can declare between a new requirement and a stored one:
`DUPLICATE`, `OVERLAPS`, `REFINES`, `SUPERSEDES`, `CONFLICTS`. They are
declared, never acted upon automatically: the system records the judgement and
leaves the decision to you.

Inspect the database with any SQLite client:

```bash
sqlite3 experiments/memory/pr-to-requirements.db ".tables"
sqlite3 experiments/memory/pr-to-requirements.db "SELECT * FROM requirements_unique;"
sqlite3 experiments/memory/pr-to-requirements.db "SELECT * FROM relations_to_review;"
```

Without the `sqlite3` client installed, the standard library does the same job:

```bash
uv run python -c "import sqlite3;[print(r) for r in sqlite3.connect('experiments/memory/pr-to-requirements.db').execute('SELECT * FROM requirements_overview')]"
```

**On `--memory-scope`.** `run` keeps each run isolated, so two runs stay
comparable — that is why it is the default. `all` gives a memory that really
accumulates over time, and should be used once per corpus: reprocessing the
same Pull Requests fills the memory with variants of the same case, which the
assessor then sees as duplicates.

---

## The MCP interface

The memory is also exposed as a **Model Context Protocol** server, which
publishes two tools:

- `search_requirements` — read access, used by the Assessment Agent;
- `store_accepted_requirement` — write access, used when a requirement is
  accepted.

Adding `--use-mcp` to a normal run makes the pipeline reach the memory through
that server instead of calling the repository directly; the server is started
as a stdio subprocess and stays alive for the whole run. Nothing else changes —
same workflow, same results.

The server can also be started on its own, which is how an external MCP client
would use it (it is not meant to be driven by hand):

```bash
uv run python -m are.mcp_server experiments/memory/pr-to-requirements.db <run_id>
uv run python -m are.mcp_server experiments/memory/pr-to-requirements.db <run_id> --memory-scope all
```

It takes the database file and the identifier of the current run — which is
what isolates retrieval — plus `--memory-scope` and `--max-requirements`, the
two settings that decide what a search may return.

---

## Development

```bash
uv run ruff check .     # linting
uv run pytest           # test suite
```

These are the two checks continuous integration runs, on Python 3.11, for every
push to `main` and every Pull Request. `mypy` is available as a development
dependency but is not part of the pipeline.

## Repository layout

| Path | Contents |
|---|---|
| `src/are/` | Source code: agents, graph, database, LLM clients, MCP server and client |
| `prompts/` | Agent prompts, versioned (`generation/`, `assessment/`) |
| `config/` | Model and workflow configuration |
| `tests/` | Test suite |
| `experiments/samples/` | Normalised Pull Request datasets |
| `experiments/runs/` | Run reports |
| `experiments/memory/` | SQLite memory files |
| `experiments/gold-standard/` | Manual annotations, unified ground truth, comparisons |
| `experiments/analisi/` | Analyses of the runs |
| `docs/design/decisions/` | The design decisions the system is built on |
| `thesis/` | Thesis material |
| `pipeline.html` | Interactive diagram of the workflow |

The decisions in `docs/design/decisions/` explain *why* the system is built the
way it is: quality standard (01), model choice (02), memory (03), MCP interface
(04), multi-agent architecture (05), dataset (06), evaluation method (07).

## Authors and supervision

- **Andrea Saverino** — 914388
- **Marco Saverino Salvatore** — 847000
- **Tutor:** Benedetta Donato
- **Università degli Studi di Milano-Bicocca**
