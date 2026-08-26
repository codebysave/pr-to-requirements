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

## 2026-08-26 — Prima esecuzione reale e ristrutturazione dei prompt

**Branch:** `feat/usage-tracking`

### 1. Il sistema ha girato per la prima volta sui dati veri

Con la chiave API disponibile, il sistema ha elaborato le 9 Pull Request del
campione scrapy dall'inizio alla fine. Tutta l'architettura costruita nei passi
precedenti — loader, configurazione, grafo, agenti, runner, report — ha
funzionato senza modifiche.

La prima esecuzione ha però rivelato subito un problema tecnico: l'SDK
`anthropic` 1.0.0 **non accetta più** i parametri di campionamento
`temperature`, `top_p` e `top_k`, rimossi dal fornitore. Il nostro client li
inviava e la chiamata falliva prima ancora di partire.

### 2. Conseguenza metodologica sulla riproducibilità

La Decisione 3.2 prevedeva di fissare `temperature = 0` per contenere la
variabilità. Non è più possibile. Abbiamo quindi:

- sostituito i parametri rimossi con `effort` (opzionale, non supportato dalla
  fascia Haiku);
- aggiunto alla Decisione 3.2 un aggiornamento datato che spiega la
  situazione: la variabilità non si può più **sopprimere**, va **misurata**
  con repliche multiple — il che rende il lavoro della tutor
  (Donato et al., 2025b) ancora più pertinente;
- annotato la lezione pratica: la configurazione va verificata contro l'SDK
  installato, non contro la documentazione ricordata.

### 3. Ristrutturazione dei tre prompt

Le prime esecuzioni hanno mostrato che i prompt erano **contraddittori**: il
valutatore suggeriva formulazioni che poi rifiutava, e il gate ammetteva Pull
Request che il valutatore scartava. Dopo una ricerca sulle linee guida
ufficiali di prompt engineering, i tre prompt sono stati riscritti:

- **struttura XML** (`<role>`, `<task>`, `<definitions>`, `<procedure>`,
  `<examples>`, `<output_format>`), che i modelli interpretano più
  affidabilmente dei titoli markdown;
- **blocco `<definitions>` identico nei tre prompt**, inserito
  programmaticamente e verificato da un test: gate e agenti non possono più
  usare nozioni diverse di «comportamento richiesto»;
- **procedura ordinata** al posto di principi che si bilanciavano: il primo
  passo che scatta decide, così il modello non sceglie arbitrariamente quale
  criterio applicare;
- **esempi diversificati** (5-7 per prompt) che coprono i casi problematici;
- **istruzioni in positivo**, ciascuna con la propria motivazione.

Sono stati inoltre rimossi dai prompt tutti i riferimenti al campione
sperimentale (nomi di moduli e funzioni delle PR di scrapy). Erano una
**contaminazione**: il modello riconosceva gli esempi invece di applicare i
criteri, e qualunque misura sarebbe risultata viziata. Un test automatico ora
lo impedisce, confrontando i prompt con il contenuto di
`experiments/samples/`.

### 4. Criteri di merito consolidati nella Decisione 3.1

Le discussioni nate dai risultati reali hanno prodotto tre precisazioni, ora
scritte nel documento di design:

- **§9** — criterio generale di estraibilità: una Pull Request è estraibile
  quando le sue informazioni sono sufficienti a identificare **in modo non
  ambiguo almeno un comportamento richiesto**, indipendentemente dalla sua
  tipologia;
- **§9.1** — il criterio riguarda il **comportamento, non il meccanismo**:
  l'ignoranza della tecnica non rende una PR non estraibile;
- **§4.1** — criterio operativo per il valutatore: «il requisito descrive un
  comportamento che il sistema deve garantire, o prescrive
  un'implementazione?». Se è la seconda, `REVISE`, perché è un difetto di
  formulazione e non di fondatezza;
- **§4.2** — l'osservabilità va calibrata sul tipo di software: per una
  libreria l'osservatore è chi usa l'interfaccia pubblica.

### 5. Strumenti di lavoro

- **Log leggibile**: al posto delle righe HTTP delle librerie, il flusso viene
  raccontato per fasi (`[GATE]`, `[GENERA]`, `[VALUTA]`) con esiti e feedback;
  con `--verbose` si vedono i messaggi inviati e le risposte grezze.
- **Selezione del modello**: `--model haiku|sonnet|opus`, oppure
  `--generation-model` / `--assessment-model` per combinazioni miste, oppure
  `--choose-model` per un menu numerato nelle prove manuali.
- **Costi e riproducibilità**: ogni report registra consumo e stima di costo
  per agente, e la **versione datata** del modello (`claude-haiku-4-5-20251001`)
  oltre all'alias richiesto.

### 6. Risultati e limite raggiunto

I report delle esecuzioni sono in `experiments/runs/`. Il confronto fra
configurazioni mostra che **una sola Pull Request su 9 riceve lo stesso esito
in tutte le prove**: le altre cambiano al variare del modello o della
formulazione del prompt.

Questo è il limite della giornata, ed è metodologico più che tecnico: senza
sapere quale sia l'esito corretto per ciascuna Pull Request, ogni modifica ai
prompt sposta i risultati senza che si possa dire se li migliora. **Il passo
successivo è costruire il gold standard sulle 9 PR del campione**, come
previsto dalla Decisione 3.7.

> **Nota sui report allegati.** I prompt sono stati modificati più volte nel
> corso della giornata mantenendo l'etichetta `v1`, quindi i report riportano
> la stessa versione pur riferendosi a formulazioni diverse. È una fase
> esplorativa: da qui in avanti ogni modifica sostanziale dovrà produrre una
> nuova versione (`v2`, `v3`…) perché i confronti restino ricostruibili.

### 7. Verifiche eseguite

- `uv run ruff check .` e `ruff format` — puliti;
- `uv run pytest` — **146 test passati** (27 nuovi: consumo e costi, selezione
  dei modelli, struttura dei prompt, identità del blocco di definizioni,
  assenza di contaminazione dal campione);
- sei esecuzioni reali sul campione, con Haiku e con Opus.

### 8. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[✔] Workflow LangGraph (agenti)     are.agents
[✔] Pipeline Runner                 are.runner
[ ] Memoria persistente (SQLite)    are.db
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale
```

Nessuna casella nuova: il sistema era già completo, questa giornata lo ha reso
funzionante sui dati reali e ne ha stabilizzato i prompt.

---

## 2026-08-26 — Preparazione al primo test reale: costi e prompt

**Branch:** `feat/usage-tracking`

### 1. Perché questa modifica

Prima di eseguire il sistema con la chiave API vera mancavano tre cose: sapere
quanto costa ogni esecuzione, poter verificare la chiave senza lanciare un
intero batch, e avere prompt abbastanza espliciti per un modello piccolo come
Haiku.

### 2. Tracciamento del consumo e dei costi

La Decisione 3.2 (§6) chiede di tenere traccia del costo per esecuzione come
metrica di valutazione, accanto alla qualità. Finora i token erano disponibili
ma nessuno li sommava.

- Il client LLM ora accumula chiamate e token consumati, per agente.
- `are/llm/pricing.py` contiene il listino dei modelli e stima il costo in
  dollari. I token restano il dato oggettivo, il costo è una stima: se il
  modello non è in listino il valore è `null`, mai un numero inventato. La
  tabella riporta la data di riferimento del listino.
- Il report di ogni esecuzione include il consumo per agente, i totali e la
  stima di costo; il riepilogo a schermo li mostra a fine esecuzione.

### 3. Verifica rapida della chiave

Nuova opzione `--check-api`: esegue una sola chiamata minima e riporta esito,
modello effettivo e costo. Serve a scoprire subito una chiave mancante o
sbagliata, invece di accorgersene a metà di un batch.

```bash
uv run python -m are --check-api
```

### 4. Prompt rinforzati con esempi

I tre prompt ora contengono esempi concreti di coppie ingresso/uscita. È la
tecnica che aiuta di più i modelli piccoli: Haiku tende ad aggiungere testo
attorno al JSON o a inserire dettagli non richiesti, e un esempio esplicito
riduce entrambi i problemi.

- *extractability*: tre esempi, fra cui un typo fix e un refactoring interno,
  entrambi `NOT_EXTRACTABLE`;
- *generation*: due esempi completi, con l'annotazione di cosa è stato
  volutamente **omesso** perché non supportato dall'evidenza;
- *assessment*: la stessa Pull Request valutata due volte, una con un
  requisito che aggiunge dettagli inventati (`REVISE`, con le istruzioni di
  correzione) e una con il requisito corretto (`ACCEPT`).

Aggiunta anche una regola esplicita per l'assessment: giudicare solo rispetto
alla Pull Request ricevuta, senza usare la conoscenza pregressa del progetto
per dare per supportato un dettaglio plausibile. È la formulazione che
avevamo già trovato utile nel prototipo NovitAI.

Abbiamo modificato la versione `v1` invece di creare una `v2` perché `v1` non
ha mai prodotto risultati: non c'era nulla da preservare.

### 5. Verifiche eseguite

- `uv run ruff check .` e `ruff format` — puliti;
- `uv run pytest` — **129 test passati** (10 nuovi: consumo cumulato,
  chiamata fallita che non conta come consumo, stima dei costi, modello fuori
  listino, e due controlli di regressione sui prompt che verificano la
  presenza di esempi JSON realmente validi).

### 6. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[✔] Workflow LangGraph (agenti)     are.agents
[✔] Pipeline Runner                 are.runner
[ ] Memoria persistente (SQLite)    are.db
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale
```

Nessuna casella nuova: è una modifica di preparazione. Il sistema è pronto per
la prima esecuzione con la chiave API reale.

---

## 2026-08-26 — Agenti reali e Pipeline Runner: sistema completo end-to-end

**Branch:** `feat/agents-and-runner`

### 1. Cosa è stato costruito

I passi 3 e 4 della roadmap insieme: il sistema passa da scheletro a pipeline
funzionante, dal file JSON ai requisiti generati.

1. **Prompt versionati** (`prompts/<agente>/v1.md`) — tre prompt in inglese
   che traducono la Decisione 3.1 in istruzioni operative:
   - *extractability*: quando una PR non consente di ricostruire un requisito
     (refactoring interno, dipendenze, documentazione, typo, test, modifiche
     di tipizzazione, descrizioni troppo vaghe);
   - *generation*: forma `shall`, i quattro pattern EARS adottati,
     distinzione WHAT/HOW con esempio, divieto di aggiungere canali, limiti
     temporali o tecnologie non supportate, gestione della revisione;
   - *assessment*: le sei condizioni necessarie (fidelity, natura funzionale,
     fedeltà, atomicità, non ambiguità, verificabilità), i criteri ulteriori,
     l'uso dei requisiti storici e il criterio per distinguere `REVISE` da
     `REJECT`.
2. **Caricatore dei prompt** (`are/agents/prompts.py`) — carica una versione
   specifica e fallisce con errore chiaro se manca o è vuota. La versione
   usata finisce nei metadati del report.
3. **Agenti LLM** (`are/agents/llm_agents.py`) — le tre implementazioni
   concrete delle porte definite al passo 2: gate di estraibilità,
   Generation Agent e Assessment Agent. Ognuno costruisce il messaggio,
   invoca il client LLM e valida la risposta.
4. **Pipeline Runner** (`are/runner.py`) — il ciclo esterno: ordina le PR
   cronologicamente, invoca il grafo una PR alla volta fino allo stato finale,
   raccoglie i risultati e produce il report JSON con storico e metadati.
5. **Entry point** (`are/__main__.py`) — il comando che collega tutto:
   `uv run python -m are --input <file.json> --limit N`.

### 2. Scelte fatte e motivazioni

- **JSON validato lato applicativo, non structured output del fornitore.**
  Gli agenti chiedono al modello un oggetto JSON e lo validano qui. Usare una
  funzionalità proprietaria avrebbe legato il codice ad Anthropic, contro il
  principio di astrazione della Decisione 3.2 (§4.3).
- **Parsing tollerante ma severo.** Accetta il JSON racchiuso in un blocco
  markdown o accompagnato da testo (casi frequenti nei modelli piccoli), ma
  una risposta senza JSON valido, con una decisione non riconosciuta o con
  campi malformati solleva `AgentResponseError`: meglio un errore esplicito
  che un requisito inventato.
- **Errori tecnici distinti dagli esiti semantici.** Se una chiamata LLM
  fallisce, il Runner registra l'errore su quella PR e prosegue con le altre;
  l'errore non diventa uno stato finale del workflow. Risolve il punto aperto
  della Decisione 3.5 §22.
- **Ordine cronologico sempre attivo** nel Runner: quando la memoria sarà
  disponibile, una PR non deve poter recuperare requisiti dal futuro.
- **`--limit`** per elaborare poche PR e contenere i costi durante le prove.
- **Il gate di estraibilità riusa la configurazione del Generation Agent**:
  è una fase della pipeline, non un terzo agente (Decisione 3.5, §4.3).

### 3. Verifiche eseguite

- `uv run ruff check .` e `ruff format` — puliti;
- `uv run pytest` — **119 test passati** (37 nuovi: 6 sui prompt, 20 sugli
  agenti LLM con client finto, 11 sul Runner). Coperti: parsing di risposte
  in tutte le forme, decisioni non riconosciute, campi mancanti, feedback
  strutturato passato al generatore in revisione, requisiti storici inseriti
  nel messaggio dell'assessment, ordine cronologico, errore tecnico che non
  blocca il batch, struttura del report;
- **prova della catena completa** con client LLM simulato sulle 9 PR reali di
  scrapy: gate che scarta correttamente il typo fix, loop
  `REVISE → generate → ACCEPT` con il feedback che raggiunge il generatore,
  report salvato con storico e metadati.

### 4. Come eseguirlo davvero

Serve la chiave API Anthropic in `.env` (`ANTHROPIC_API_KEY`). Poi:

```bash
uv run python -m are --input experiments/samples/sample-scrapy_scrapy.json --limit 3
```

Finché la chiave non è disponibile il codice resta completo e testato: non
sarà necessaria alcuna modifica, solo il file `.env`.

### 5. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[✔] Workflow LangGraph (agenti)     are.agents        ← questa modifica
[✔] Pipeline Runner                 are.runner        ← questa modifica
[ ] Memoria persistente (SQLite)    are.db
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale
```

Il sistema è ora completo dal file di input ai requisiti generati. Restano la
memoria persistente con il suo accesso via MCP e la fase di valutazione.

---

## 2026-08-25 — Allineamento delle Decisioni 3.2 e 3.5 al piano di valutazione 3.7

**Branch:** `feat/workflow-skeleton`

### 1. Il problema rilevato

La Decisione 3.7 è stata rivista in corso d'opera: il piano di valutazione non
prevede più un **disegno fattoriale 2×2** (valutatore × memoria), ma un
approccio diverso — le prove progressive (solo Generation, Generation +
Assessment, workflow completo) risultano già svolte durante lo sviluppo e
hanno portato ad adottare il **workflow completo come configurazione di
riferimento**; la valutazione formale riguarda la qualità dei requisiti
prodotti da quella configurazione, tramite gold standard, rubrica PASS/FAIL,
hard gate e valutazione umana.

Le Decisioni 3.2 e 3.5, però, facevano ancora riferimento al vecchio impianto.
In particolare la 3.2 (§6) prometteva esplicitamente un "disegno fattoriale
2×2" che la 3.7 attuale non definisce più: una tutor che legge i documenti in
sequenza avrebbe trovato una contraddizione.

### 2. Cosa è stato modificato

- **Decisione 3.2, §6** — il paragrafo sulla fase sperimentale non cita più il
  2×2: ora dichiara il workflow completo come configurazione di riferimento e
  rimanda alla 3.7 per la valutazione. Resta il principio di controllo dei
  confondenti (modello costante all'interno di una campagna di valutazione;
  un eventuale confronto tra modelli è un'analisi separata).
- **Decisione 3.5, §20** — la configurabilità non viene più motivata come
  confronto sperimentale tra configurazioni, ma con le tre ragioni reali:
  sviluppo incrementale, esecuzione controllata delle prove progressive della
  3.7 e debug di un singolo componente. Aggiunta la precisazione che la
  configurazione di riferimento per la valutazione è il workflow completo.
- **Decisione 3.5, §2 e §8** — riformulati due passaggi minori che parlavano
  di "confrontare configurazioni" e di esecuzione "per gli esperimenti".
- **Codice e commenti** — rimossi i riferimenti al 2×2 da
  `config/workflow.toml`, dal docstring di `are/agents/config.py`, da quello
  di `route_after_retrieval` e dalla voce di recap del workflow skeleton.

### 3. Cosa NON è cambiato

I flag `assessment_enabled` e `memory_enabled` restano invariati: sono
richiesti dalla Decisione 3.5 §20, servono alle prove progressive della 3.7 e
sono comunque necessari finché la memoria persistente non esiste. È cambiata
soltanto la motivazione dichiarata, non il comportamento del sistema — infatti
nessun test è stato modificato e tutti continuano a passare.

### 4. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[ ] Workflow LangGraph (agenti)     are.agents
[ ] Pipeline Runner
[ ] Memoria persistente (SQLite)    are.db
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale
```

Voce di sola documentazione: nessuna casella cambia stato.

---

## 2026-08-25 — Scheletro del workflow LangGraph (Decisione 3.5)

**Branch:** `feat/workflow-skeleton`

### 1. Cosa è stato costruito

La macchina a stati che governa l'elaborazione di una singola Pull Request:
il "passo 2" della roadmap. Tutto vive nel package `are.agents` (il nome
riprende il titolo della Decisione 3.5, "Architettura degli agenti"):

1. **Stato condiviso** (`state.py`) — `RequirementState` con le sezioni
   previste dal design: Pull Request, estraibilità, generazione (candidato e
   numero tentativo), memoria recuperata, assessment, stato finale e storico
   delle iterazioni. Più i tipi strutturati: `AssessmentFeedback` (issues,
   unsupported claims, missing information, revision instructions),
   `IterationRecord`, gli enum `ACCEPT/REVISE/REJECT`,
   `EXTRACTABLE/NOT_EXTRACTABLE` e i 4 stati finali
   (`ACCEPTED`, `NOT_EXTRACTABLE`, `REJECTED`, `FAILED_VALIDATION`).
2. **Porte** (`ports.py`) — le interfacce (Protocol) che il grafo usa senza
   conoscere le implementazioni: `ExtractabilityChecker`,
   `RequirementGenerator`, `RequirementAssessor`, `MemoryRetriever`,
   `AcceptedRequirementStore`. Gli agenti LLM reali (passo 3) e la memoria
   (passi 5-6) implementeranno queste interfacce senza toccare il workflow.
3. **Routing centralizzato** (`routing.py`) — funzioni pure e testabili senza
   LLM: estraibilità → generazione o terminazione; dopo il retrieval →
   assessment (o accettazione diretta se il valutatore è disattivato); dopo
   l'assessment → `ACCEPT`/`REVISE`/`REJECT` con il limite di tentativi
   (`REVISE` oltre il limite → `FAILED_VALIDATION`, mai promozione automatica
   del miglior candidato).
4. **Grafo LangGraph** (`graph.py`) — nodi sottili che delegano alle porte:
   `check_extractability → generate → retrieve_memory → assess → accept` più
   i nodi terminali. Il retrieval viene ripetuto dopo ogni generazione e la
   persistenza avviene solo nel nodo `accept`, fuori dagli agenti, come da
   design.
5. **Configurazione del workflow** — `config/workflow.toml` con
   `assessment_enabled`, `memory_enabled`, `max_generation_attempts = 3`,
   validati rigorosamente come le altre config. Servono a eseguire il
   workflow in configurazioni diverse senza toccare il codice: sviluppo
   incrementale (la memoria non esiste ancora), prove progressive della
   Decisione 3.7 §2 e debug di un singolo componente.

### 2. Scelte fatte e motivazioni

- **Dependency injection ovunque**: il grafo riceve le implementazioni via
  `WorkflowDependencies`. Oggi sono stub nei test; al passo 3 diventeranno
  gli agenti LLM veri. Questo permette di testare l'intera macchina a stati
  senza chiamare la rete, come richiede la Decisione 3.5 (§21).
- **`memory_enabled = false` di default**: la memoria non esiste ancora
  (passi 5-6); il grafo la salta e usa un retriever/store inerte
  (`NullMemoryRetriever`, `NullRequirementStore`).
- **Parametro di routing rinominato** `workflow_config`: LangGraph riserva
  il nome `config` per il proprio `RunnableConfig`.
- **Dipendenza aggiunta**: `langgraph` 1.2.11.

### 3. Verifiche eseguite

- `uv run ruff check .` e `ruff format` — puliti, nessun warning;
- `uv run pytest` — **82 test passati** (34 nuovi: 12 sul routing puro,
  11 sulla config, 11 end-to-end sul grafo con agenti finti). Coperti tutti
  i percorsi della Decisione 3.5: NOT_EXTRACTABLE senza generazione, ACCEPT
  al primo colpo con persistenza, REVISE con feedback e candidato precedente
  passati al generatore, tre REVISE → FAILED_VALIDATION senza persistenza,
  REJECT terminale, limite tentativi configurabile, workflow senza
  valutatore, retrieval ripetuto a ogni generazione.

### 4. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[ ] Workflow LangGraph (agenti)     are.agents
[ ] Pipeline Runner
[ ] Memoria persistente (SQLite)    are.db
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale
```

Nessuna casella nuova in questa voce: lo scheletro del workflow è completo e
testato, ma la casella "Workflow LangGraph (agenti)" verrà spuntata al passo
successivo, quando gli agenti stub saranno sostituiti da quelli reali con i
prompt (passo 3).

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
