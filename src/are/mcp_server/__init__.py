"""Server MCP per l'accesso alla memoria persistente (Decisione 3.4).

Il pacchetto espone la funzione :func:`create_server`, unico punto di
costruzione del server MCP con le sue dipendenze applicative iniettate.
L'entry point CLI per avviare il server come sottoprocesso stdio vive
in :mod:`are.mcp_server.__main__`.
"""

from .server import create_server

__all__ = ["create_server"]
