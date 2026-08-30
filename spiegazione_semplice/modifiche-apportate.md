# Modifiche apportate durante la revisione

Registro delle modifiche fatte ai file del repository durante la revisione
progressiva. Ogni voce indica il **file**, **cosa è stato cambiato** e
**perché**. Il file viene aggiornato ogni volta che completiamo la revisione di
un documento o di un pezzo di codice.

---

## `README`

**Data revisione:** 2026-08-30

### 1. Rimossa la sezione "Stato del progetto"

Rimossa completamente la sezione che riportava:

> *In fase di sviluppo. Stage avviato a luglio 2026, laurea prevista per
> settembre 2026.*

**Motivazione.**
- Informazioni che invecchiano da sole e nessuno aggiorna → diventano una fonte
  di dati sbagliati (la "laurea prevista a settembre" era già errata).
- Duplica informazioni già presenti in `worklog/diario-di-lavoro.md`,
  `recap.md` e nella cronologia dei commit.
- Un README non è un changelog: lo stato del lavoro sta nel diario, non nella
  vetrina del progetto.

### 2. Riformulata la frase su memoria + MCP

**Prima:**

> *I requisiti validati vengono salvati in un database persistente accessibile
> dagli agenti tramite MCP (Model Context Protocol), che funge da memoria a
> lungo termine e consente di verificare duplicazioni o incoerenze con i
> requisiti già generati.*

**Dopo:**

> *I requisiti generati, una volta validati, vengono salvati in un database
> persistente che funge da memoria a lungo termine del sistema. Gli agenti vi
> accedono tramite MCP (Model Context Protocol), che espone tool di ricerca
> sui requisiti storici e permette all'Assessment Agent di individuare
> duplicazioni o incoerenze con i requisiti già generati.*

**Motivazione.**
- La frase precedente attribuiva a MCP due ruoli che non gli appartengono: la
  **memoria a lungo termine** (che è il database, non il protocollo) e la
  **verifica di duplicati/incoerenze** (che la fa l'Assessment Agent
  ragionando sui candidati restituiti, non MCP).
- MCP è un **protocollo di interfaccia**: fa da ponte tra agenti e memoria
  esponendo dei tool. Non contiene dati e non prende decisioni.
- Cambiato anche *"requisiti validati vengono salvati"* → *"requisiti generati,
  una volta validati, vengono salvati"*: esplicita la sequenza reale
  (generazione → validazione → persistenza) e chiarisce che **non tutti** i
  requisiti generati finiscono in memoria, solo quelli con esito `ACCEPT`.

### 3. Accorpate "Autori" e "Supervisione" in un'unica sezione

**Prima:** due sezioni separate (`## Autori` e `## Supervisione`).

**Dopo:** un'unica sezione `## Autori e supervisione` che elenca in ordine
autori, tutor, università.

**Motivazione.**
- Evita due box piccoli e attaccati che spezzano inutilmente la lettura.
- Autori + tutor + istituzione fanno parte della stessa informazione
  ("attribuzione accademica del lavoro").

### Modifiche NON applicate (da valutare in seguito)

- **URL del `git clone`.** Al momento punta a
  `https://github.com/codebysave/pr-to-requirements.git`. Va verificato che
  sia il repository corretto e attivo prima di modificarlo.

---

## `spiegazione_semplice/pipeline.html`

**Data revisione:** 2026-08-30

### 4. Popolate le schede di dettaglio degli step 01 → 06

Le schede a comparsa dei blocchi del diagramma, che all'inizio contenevano
solo un messaggio "in stesura", sono state riempite man mano che gli step
sono stati analizzati:

- **Step 01 — PR normalizzata**: 6 campi, esempio JSON reale, cosa NON è.
- **Step 02 — PullRequestLoader**: 4 file del modulo `input/`, controlli a
  cascata (file/JSON/schema/unicità), le 5 scelte di design.
- **Step 03 — Extractability**: gate deterministico, due condizioni (body
  vuoto, lunghezza < 50 char), esempio di record dal file di run.
- **Step 04 — Generation Agent**: prompt v1 in blocchi, due esiti del JSON
  (`requirement` vs `cannot_ground`), aggancio al livello LLM Client.
- **Step 05 — Candidate Requirement**: cos'è un artefatto, le tre "vite" del
  candidato (RAM → report JSON → memoria persistente).
- **Step 06 — Memory Retrieval + MCP**: cosa c'è (DB SQLite), cosa manca
  (retriever semantico, server MCP), perché il retrieval è PRIMA
  dell'Assessment.

**Motivazione.**
- Le schede stub non davano valore aggiunto al diagramma: chi cliccava
  vedeva solo "sezione in stesura".
- Popolarle in ordine col flusso di studio (01 → 06) ha permesso di
  costruire progressivamente una spiegazione coerente, dove ogni scheda si
  aggancia alla precedente.
- Sono la memoria "cliccabile" del progetto: al posto di rileggere pagine di
  documentazione, un click sul blocco dà il dettaglio completo di quel pezzo.

### 3. Aggiunta la linea `cannot_ground` (04 → 07, salta 05 e 06)

Aggiunto al diagramma un arco che parte dal fondo del blocco 04 (Generation
Agent), passa sotto i blocchi 05 e 06, e arriva al fondo del blocco 07
(Assessment Agent), etichettato `cannot_ground · salta 05, 06`.

Aggiornata la figcaption per menzionare esplicitamente il nuovo ramo.

**Motivazione.**
- Il Generation Agent ha **due** esiti possibili — `requirement` e
  `cannot_ground` — con due percorsi diversi nel grafo LangGraph
  (vedi `src/are/agents/graph.py`).
- Il percorso `cannot_ground` non passa per Memory Retrieval perché senza un
  candidato non c'è una query semantica da fare — l'Assessment viene chiamato
  con il parametro `generation_refusal` invece che con `candidate`.
- Il diagramma precedente rappresentava solo il percorso principale
  (`04 → 05 → 06 → 07`), lasciando invisibile un esito legittimo previsto
  dalla Decisione 01 §11.10.

### 2. Aggiunto il livello "LLM Client" al diagramma

Aggiunta una nuova barra tratteggiata in alto al diagramma (viewBox esteso da
`0 0 1600 780` a `0 0 1600 920`) che rappresenta il **livello LLM Client** —
l'infrastruttura condivisa dagli agenti descritta nella voce di recap del
25/08 "Configurazione e astrazione LLM (Decisione 3.2)".

Elementi aggiunti:
- barra tratteggiata (x=560, y=30, w=760, h=80) con etichetta
  "INFRASTRUTTURA · DECISIONE 3.2", titolo "LLM Client" e sottotitolo
  "config/llm.toml · AnthropicLLMClient · SDK ufficiale";
- due connettori tratteggiati verticali dalla barra ai blocchi 04 (Generation
  Agent) e 07 (Assessment Agent), con etichetta "chiama";
- nuova voce in legenda: "Infrastruttura LLM" (swatch dashed);
- nuova entry `"llm-client"` nel dizionario `steps` del JavaScript, con
  contenuto completo tratto dal recap: i 3 pezzi costruiti, gestione della
  chiave API, scelte (no LangChain, client iniettabile), nota sui parametri
  di temperatura rimossi dall'API, verifica (48 test verdi);
- figcaption aggiornata per spiegare cos'è la barra tratteggiata.

Tutte le coordinate y del diagramma esistente sono state spostate in giù di
120 unità per fare spazio al nuovo livello in cima.

**Motivazione.**
- Il livello LLM è infrastruttura condivisa, non una tappa della pipeline:
  visualizzarlo come "substrato in alto" con connettori tratteggiati (invece
  che come blocco nel flusso) rende chiaro il ruolo.
- Il click sulla barra apre la scheda dettagliata, uniformando il pattern
  interattivo con gli altri blocchi.

### 1. Sostituito "PR-to-Requirements" con "pr-to-requirements" (3 occorrenze)

Sostituzioni fatte:

- `<title>Pipeline PR-to-Requirements</title>` → `<title>Pipeline pr-to-requirements</title>` (titolo del tab del browser).
- `<div class="eyebrow">Diagramma interattivo · PR-to-Requirements</div>` → `... · pr-to-requirements`.
- `aria-label="Diagramma della pipeline PR-to-Requirements: ..."` → `aria-label="Diagramma della pipeline pr-to-requirements: ..."`.

**Motivazione.**
- Uniformità con il nome ufficiale del repository (`pr-to-requirements`), che è
  quello a cui il progetto viene riferito su GitHub e nel `README`.
- Sostituzione limitata alle occorrenze presenti nei file creati/modificati in
  questa sessione. Le occorrenze presenti in altri file del repository
  (`recap.md`, decisioni di design, codice `src/are/`, config, worklog) sono
  state **volutamente lasciate invariate**: verranno sostituite man mano che
  ciascun file entrerà nella revisione.
