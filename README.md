# PR-to-Requirements

Automatic Requirement Extraction from PRs using LLM-based Agents.

## Description

The project builds a pipeline based on LLMs and AI agents that reconstructs
functional software requirements from the title and body of a Pull Request.

The system uses two agents:

- **Requirement Generation Agent**: writes the requirement from the Pull
  Request.
- **Requirement Assessment Agent**: judges its quality, clarity and conformity
  to the required style. If the requirement does not pass, generation is
  repeated.

Once validated, the requirements are saved in a **persistent database** that
acts as the **long-term memory** of the system. Before each assessment the
Assessment Agent receives the requirements already validated, so that it can
spot duplications or inconsistencies with what has been produced before.

The memory is also exposed as an **MCP (Model Context Protocol)** server, which
the pipeline uses when started with `--use-mcp`.

## Authors and supervision

- **Andrea Saverino** — 914388
- **Marco Saverino Salvatore** — 847000
- **Tutor**: Benedetta Donato
- **University**: Università degli Studi di Milano-Bicocca

## Repository structure

- `src/` — source code of the pipeline
- `prompts/` — agent prompts, versioned
- `config/` — model and workflow configuration
- `tests/` — automated tests
- `experiments/` — samples, run reports, memory and gold standard
- `docs/` — documentation (state of the art, design decisions, minutes)
- `thesis/` — material for the theses

## Installation

Requirements: Python >= 3.11, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/codebysave/pr-to-requirements.git
cd pr-to-requirements
uv sync
```

## Configuration

The models and LLM parameters of the two agents are set in `config/llm.toml`,
and the pipeline behaviour in `config/workflow.toml`; both are versioned. The
API key never goes in the repository: copy `.env.example` into `.env` and put
your Anthropic key there.

```bash
cp .env.example .env
```

## Running

To check that the API key works, with one minimal call:

```bash
uv run python -m are --check-api
```

To process a file of Pull Requests and produce the requirements:

```bash
uv run python -m are --input experiments/samples/sample-scrapy_scrapy.json --limit 3
```

The run report is saved in `experiments/runs/` and holds the accepted
requirements, the final states, the revision history, the models and prompts
used, and token consumption with a cost estimate. The accepted requirements are
stored in `experiments/memory/pr-to-requirements.db`.

Useful options:

- `--limit N` — process only the first N Pull Requests, to keep costs down
- `--output PATH` — choose the report file
- `--model NAME` — `haiku`, `sonnet` or `opus` for both agents;
  `--generation-model` and `--assessment-model` set them one by one
- `--prompt-version V` — use a different version of the prompts
- `--memory-scope all` — let the assessor see the requirements of every run,
  not only those of the current one
- `--skip-processed` — skip Pull Requests already processed for the same
  project
- `--use-mcp` — reach the memory through the MCP server
- `--assessor-tools` — let the assessor query the memory by itself, as a tool
- `--verbose` — detailed logging

`uv run python -m are --help` lists them all.

## Tests

```bash
uv run ruff check .
uv run pytest
```
