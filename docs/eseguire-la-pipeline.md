# Eseguire la pipeline, da un repository a un report

Procedura completa: dal repository grezzo su GitHub fino al report di
esecuzione. Presuppone l'installazione descritta nel README (`uv sync`,
`.env` con la chiave API).

---

## 1. Procurarsi un repository del dataset PR4Code

Scarichiamo un repository fra quelli inclusi nel dataset **PR4Code**
(Donato, Mariani, Micucci e Riganelli, 2026) — 13.339 Pull Request reali da
1.055 repository GitHub, in Java e Python.

## 2. Normalizzare le Pull Request

Carichiamo il repository scaricato nel **PR4Code-JSON-Converter**, che
restituisce un file `sample-<nome-repo>.json` con le Pull Request
normalizzate: solo i campi che il sistema usa davvero (identificativo,
repository, numero, timestamp, titolo, corpo), non l'intera ricchezza del
dataset sorgente (commit, diff, versioni dei file, eccetera).

## 3. Posizionare il campione

Copiamo `sample-<nome-repo>.json` dentro `experiments/samples/` del
repository `pr-to-requirements`.

## 4. Eseguire la pipeline

Comando da lanciare **dalla root del repository** (`pr-to-requirements/`,
non da dentro `src/are/`):

```bash
uv run python -m are --input experiments/samples/sample-<nome-repo>.json
```

Il report viene salvato in `experiments/runs/`; i requisiti accettati
confluiscono nel database di memoria in `experiments/memory/`.

---

## Che cosa fa il sistema se non specifichiamo nessuna opzione

Il comando sopra è valido così com'è — tutto il resto ha un default. Vale la
pena saperlo esplicitamente, perché **il comportamento silenzioso non è
"nessuna scelta": è una scelta precisa, fatta dai file di configurazione
versionati.**

| Aspetto | Default | Dove è definito |
|---|---|---|
| Pull Request elaborate | **tutte** quelle nel file di input | nessun `--limit` |
| Report | `experiments/runs/run-<timestamp>.json` | `__main__.py` |
| Database memoria | `experiments/memory/pr-to-requirements.db` | `__main__.py` |
| Modello — Generation Agent | `claude-sonnet-5` | `config/llm.toml` |
| Modello — Assessment Agent | `claude-opus-5` | `config/llm.toml` |
| Assessment Agent | **attivo** | `config/workflow.toml` → `assessment_enabled = true` |
| Recupero dalla memoria | **attivo** | `config/workflow.toml` → `memory_enabled = true` |
| Tentativi massimi di generazione | 3 (1 iniziale + 2 revisioni) | `config/workflow.toml` → `max_generation_attempts` |
| Ambito della memoria | `all` — accumula da **tutte** le esecuzioni precedenti sullo stesso progetto | `--memory-scope` non specificato |
| Come il valutatore riceve la memoria | **via MCP**: server avviato come sottoprocesso stdio, resta in vita per tutto il run | né `--no-mcp` né `--assessor-tools` |
| Pull Request già elaborate | **saltate**, nessuna chiamata al modello | `--reprocess` non specificato |
| Versione prompt — generazione | `v2`, unica esistente | fissa, non configurabile |
| Versione prompt — valutazione | `v1` (`v2` solo con `--assessor-tools`) | automatica, non configurabile |
| Log | sintetico, per fase | `--verbose` non specificato |

In breve: **di default il sistema gira nella configurazione completa e finita**
— generatore su Sonnet, valutatore su Opus, memoria attiva via MCP e che si
accumula da tutte le esecuzioni precedenti, tre tentativi, Pull Request già
viste saltate automaticamente. È la configurazione pensata per l'uso reale
del sistema, non per la sperimentazione: per confrontare configurazioni
diverse o misurare la variabilità fra repliche vanno usati esplicitamente
`--memory-scope run` (altrimenti una run vedrebbe già i requisiti prodotti
dalla precedente) e `--reprocess` (altrimenti lo stesso corpus non verrebbe
rielaborato una seconda volta).

---

## Opzioni utili

- `--limit N` — elabora solo le prime N Pull Request del file, per contenere i costi
- `--output PATH` — sceglie il file del report
- `--model NAME` — `haiku`, `sonnet` o `opus` per entrambi gli agenti;
  `--generation-model` e `--assessment-model` li impostano separatamente
- `--memory-scope run` — isola il valutatore ai requisiti di questa sola esecuzione (il default, `all`, accumula fra le esecuzioni; usare `run` per confronti fra configurazioni o repliche comparabili)
- `--reprocess` — rielabora anche le Pull Request già elaborate per lo stesso progetto (di default vengono saltate)
- `--no-mcp` — chiama direttamente il repository/retriever invece di passare per il server MCP (di default sempre attivo)
- `--assessor-tools` — il valutatore interroga la memoria da sé, come un tool
- `--verbose` — log di dettaglio

`uv run python -m are --help` le elenca tutte.

**Nota — perché la versione dei prompt non è un'opzione.** Il generatore ha
un'unica formulazione; il valutatore ne ha due, accoppiate a
`--assessor-tools` (deterministico → `v1`, guidato dall'agente → `v2`). Non
è esposta come flag apposta: permetterebbe di combinare `--assessor-tools`
con la formulazione sbagliata, lasciando il modello con istruzioni per un
meccanismo che non esiste in quella run. Chi vuole provare una formulazione
diversa la aggiunge in `prompts/` e modifica direttamente `__main__.py`.
