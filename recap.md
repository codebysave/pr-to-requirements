# Recap del lavoro svolto

Questo file tiene traccia, in ordine cronologico, di ogni modifica significativa
fatta al progetto: cosa è stato fatto, dove, perché, e come è stato verificato.
Ogni voce è divisa in pezzi semplici, così chiunque (inclusa la tutor) può
ricostruire rapidamente la storia del sistema senza leggere i diff.

**Convenzione.** La sezione "Stato del sistema" di ogni voce usa sempre lo
stesso elenco di componenti, nello stesso ordine (quello di costruzione
bottom-up della roadmap) e con gli stessi nomi. Tra una voce e l'altra cambia
soltanto lo stato delle caselle — `[✔]` fatto, `[ ]` da fare — e la freccia
`← questa modifica` che indica il componente completato dalla voce.

---

## 2026-08-25 — Configurazione e astrazione LLM (Decisione 3.2)

**Branch:** `feat/llm-config`

### 1. Cosa è stato costruito

Il livello di accesso agli LLM, prerequisito di entrambi gli agenti. È il
"passo 1" della roadmap dopo l'integrazione del loader. Tre pezzi:

1. **Configurazione versionata per agente** — `config/llm.toml` definisce
   modello e parametri separatamente per Generation Agent e Assessment Agent
   (come richiede la Decisione 3.2: il modello è una variabile
   dell'esperimento, non un valore cablato nel codice). In sviluppo entrambi
   usano `claude-haiku-4-5` (fascia economica) con `temperature = 0` per la
   riproducibilità.
2. **Modulo di caricamento config** — `src/are/llm/config.py` legge il TOML
   con la libreria standard (`tomllib`, niente dipendenze extra) e lo valida
   rigorosamente, nello stesso stile del loader: sezioni obbligatorie,
   chiavi sconosciute rifiutate, tipi e range controllati (`temperature` e
   `top_p` in [0,1], `max_tokens` intero positivo), tutti i problemi
   riportati insieme.
3. **Client LLM astratto** — `src/are/llm/client.py` definisce il protocollo
   `LLMClient` (l'interfaccia unica che gli agenti useranno) e
   l'implementazione `AnthropicLLMClient` sopra l'SDK ufficiale `anthropic`.
   La risposta (`LLMResponse`) include token in ingresso e uscita per il
   tracciamento dei costi previsto dalla Decisione 3.2. Gli errori del
   fornitore vengono incapsulati in `LLMCallError`.

### 2. Gestione della chiave API

- La chiave vive **solo** nella variabile d'ambiente `ANTHROPIC_API_KEY`,
  caricabile dal file `.env` (già escluso da Git) tramite
  `are.env.load_environment()`.
- Aggiunto `.env.example` versionato che documenta la variabile richiesta, e
  una sezione "Configurazione" nel README con le istruzioni.
- Se la chiave manca, il client fallisce subito con un errore chiaro
  (`MissingApiKeyError`) invece di fallire alla prima chiamata.

### 3. Scelte fatte e motivazioni

- **SDK Anthropic diretto, non LangChain** (deciso insieme): controllo totale
  e trasparente dei parametri inviati, meno dipendenze, più facile da
  documentare per la riproducibilità. LangGraph (passo 2) non richiede
  oggetti LangChain: i nodi sono normali funzioni Python.
- **Client iniettabile nei test**: `AnthropicLLMClient` accetta un SDK finto,
  così i test verificano esattamente quali parametri vengono inviati senza
  mai chiamare la rete.
- **Dipendenze aggiunte**: `anthropic` (SDK ufficiale, v1.0.0) e
  `python-dotenv` (caricamento `.env`). Prime dipendenze runtime del progetto.

### 4. Verifiche eseguite

- `uv run ruff check .` e `ruff format` — puliti;
- `uv run pytest` — **48 test passati** (25 del loader + 23 nuovi: 13 sulla
  validazione della config, 6 sul client con SDK finto, incluso il controllo
  che il file `config/llm.toml` del repository sia valido).

### 5. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm          ← questa modifica
[ ] Workflow LangGraph (agenti)     are.agents
[ ] Pipeline Runner
[ ] Memoria persistente (SQLite)    are.db
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale
```

---

## 2026-08-25 — Integrazione del primo nodo: Input Loader

**Branch:** `feat/input-loader`

### 1. Cosa è stato integrato

Il **PullRequestLoader**, il nodo di ingresso di PR4Requirements, sviluppato e
testato in precedenza come pacchetto separato (`PR4Requirements-Input-Loader`),
è stato portato dentro il repository ufficiale.

Il loader legge il file JSON normalizzato prodotto dal preprocessing (fuori dal
sistema), ne verifica rigorosamente il contratto e restituisce una lista di
`PullRequestRecord` immutabili, pronti per il futuro Pipeline Runner:

```text
JSON normalizzato → PullRequestLoader → list[PullRequestRecord]
```

Come da design (Decisioni 3.5 e 3.6), il loader fa parte del sistema ma resta
**fuori dal ciclo agentico**: non contiene LLM, LangGraph, Runner né persistenza.

### 2. Dove è stato collocato

- `src/are/input/` — il codice del nodo, come sottopackage di `are`
  (il package principale del progetto, accanto ai futuri `agents/`, `db/`,
  `mcp_server/`):
  - `models.py` — `PullRequestRecord`, il modello tipizzato e immutabile;
  - `loader.py` — `PullRequestLoader`, lettura e validazione del file;
  - `exceptions.py` — gerarchia degli errori (`PullRequestInputError` e derivati);
  - `__init__.py` — API pubblica del nodo.
- `tests/test_input_loader.py` e `tests/test_input_models.py` — i test del
  pacchetto originale, adattati al nuovo import `from are.input import ...`.
  Rimosso `tests/test_placeholder.py`, non più necessario.
- `experiments/samples/sample-scrapy_scrapy.json` — un campione reale di 9 PR
  del repository `scrapy/scrapy` (derivato da PR4Code tramite lo script di
  preprocessing), utile per provare subito il sistema.

Uso del nodo:

```python
from are.input import PullRequestLoader

records = PullRequestLoader().load("experiments/samples/sample-scrapy_scrapy.json")
```

### 3. Sistemazioni al progetto necessarie per l'integrazione

Due problemi del repository sono stati corretti in questa occasione:

1. **`pyproject.toml` non rendeva installabile il package.** Mancavano il
   `build-system` e la configurazione del layout `src/`: qualunque
   `import are` sarebbe fallito nei test e nella CI (il test placeholder
   passava solo perché non importava nulla). Aggiunti `[build-system]`
   (setuptools) e `[tool.setuptools.packages.find] where = ["src"]`.
   Ora `uv sync` installa il progetto in modalità sviluppo.
2. **Mancava il `.gitignore` alla radice.** Creato con le esclusioni standard:
   `.env` (le chiavi API non devono mai entrare nel repository, come da
   Decisione 3.2), `__pycache__`, ambienti virtuali, cache dei tool, database
   SQLite locali.

### 4. Scelte fatte e motivazioni

- **Percorso `are.input`** — il design chiama questo componente "livello di
  ingresso"; collocarlo come sottopackage di `are` mantiene un unico package
  installabile e prepara la struttura per i nodi successivi.
- **Codice sorgente invariato** — il loader era già completo, testato e
  conforme alle decisioni di design; è stato copiato senza modifiche di
  logica (cambiano solo il percorso del package e gli import nei test).
  Nessuna dipendenza runtime aggiunta: il nodo usa solo la libreria standard.
- **Sample nel repository** — avere un input reale versionato permette alla
  tutor di clonare, fare `uv sync` e vedere subito il nodo funzionare.

### 5. Verifiche eseguite

- `uv run ruff check .` — nessun errore di lint;
- `uv run pytest` — **25 test passati** (più 9 sottotest), tutti quelli del
  pacchetto originale;
- prova manuale sul campione reale: le 9 PR di `scrapy/scrapy` vengono
  caricate e validate correttamente, con timestamp timezone-aware.

### 6. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input        ← questa modifica
[ ] Configurazione + client LLM     are.llm
[ ] Workflow LangGraph (agenti)     are.agents
[ ] Pipeline Runner
[ ] Memoria persistente (SQLite)    are.db
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale
```
