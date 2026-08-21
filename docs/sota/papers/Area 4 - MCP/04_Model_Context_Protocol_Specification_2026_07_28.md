# Model Context Protocol — Specification 2026-07-28

- **Autori / ente:** Model Context Protocol project / official maintainers
- **Anno:** 2026
- **Venue / fonte:** Official Model Context Protocol Specification
- **DOI:** non applicabile / non indicato
- **Link ufficiale:** https://modelcontextprotocol.io/specification/2026-07-28
- **Accesso open / repository:** https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/docs/specification/2026-07-28
- **Nota accesso:** Specifica ufficiale pubblica; repository ufficiale disponibile su GitHub.

## Breve riassunto

La specifica definisce Model Context Protocol (MCP) come un protocollo aperto che standardizza l'integrazione tra applicazioni LLM e fonti esterne di dati e strumenti. La revisione 2026-07-28 utilizza messaggi JSON-RPC 2.0 e distingue ruoli come host, client e server. I server possono esporre capability come Resources, Prompts e Tools, mentre il protocollo stabilisce il modo in cui tali capability vengono scoperte e invocate. MCP non definisce di per sé come debbano essere implementati database, vector store o politiche di persistenza: fornisce invece un boundary standardizzato attraverso cui un agente può accedere a tali sistemi esterni.

## Uso nello stato dell'arte PR-to-Requirements

Nel progetto PR-to-Requirements MCP viene usato come protocollo di accesso alla memoria persistente, non come memoria stessa. Il database/vector store e la strategia di retrieval risiedono dietro il server MCP. L'Assessment Agent può quindi eseguire operazioni read-only come search_requirements o find_candidate_relations, mentre la persistenza di un requisito dovrebbe avvenire solo dopo la sua validazione.
