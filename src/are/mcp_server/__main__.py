"""Entry point del server MCP di pr-to-requirements.

Costruisce le dipendenze applicative (repository e retriever) dai
parametri CLI e avvia il server con trasporto stdio (Decisione 3.4 §10).
Invocato dal client MCP come sottoprocesso; non e' pensato per essere
lanciato interattivamente da un umano.

Uso::

    python -m are.mcp_server <db_path> <run_id>

    python -m are.mcp_server experiments/memory/shared.db 20260831T142024Z
    python -m are.mcp_server experiments/memory/shared.db 20260831T142024Z --memory-scope all
"""

from __future__ import annotations

import argparse

from are.db import ExhaustiveRequirementRetriever, SqliteRequirementRepository
from are.mcp_server.server import create_server


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Server MCP per la memoria persistente di pr-to-requirements",
    )
    parser.add_argument(
        "db_path",
        help="Percorso del file SQLite della memoria persistente",
    )
    parser.add_argument(
        "run_id",
        help="Identificativo del run corrente, usato come chiave di isolamento",
    )
    parser.add_argument(
        "--memory-scope",
        choices=["run", "all"],
        default="run",
        help=(
            "'run' isola il retrieval al run corrente (utile per esperimenti puliti); "
            "'all' attraversa tutti i run del DB (memoria che si accumula)."
        ),
    )
    parser.add_argument(
        "--max-requirements",
        type=int,
        default=50,
        help=(
            "Numero massimo di requisiti restituiti dal retriever. "
            "Salvaguardia, non un top-k: la ricerca resta esaustiva entro i filtri."
        ),
    )
    args = parser.parse_args()

    repository = SqliteRequirementRepository(args.db_path, args.run_id)
    scope_run_id = args.run_id if args.memory_scope == "run" else None
    retriever = ExhaustiveRequirementRetriever(
        store=repository,
        run_id=scope_run_id,
        max_requirements=args.max_requirements,
    )

    server = create_server(repository, retriever)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
