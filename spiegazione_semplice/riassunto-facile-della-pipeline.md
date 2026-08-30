# Riassunto facile della pipeline pr-to-requirements

Riassunti brevi degli step della pipeline man mano che li abbiamo studiati
insieme. Ogni voce dice cos'è, cosa fa e le scelte importanti. Il diagramma
interattivo con i dettagli completi vive in `pipeline.html` (stessa cartella).

---

## Step 01 — PR normalizzata

Uno **script di preprocessing**, scritto da noi, prende le PR dal dataset
**PR4Code** (della tutor) e le riscrive nel formato che il sistema si aspetta.
Nel farlo rimuove tutto ciò che è **rumore** rispetto al task attuale: stato e
informazioni sul branch, sequenza e messaggi dei commit, file modificati,
patch e diff, numero di righe aggiunte/rimosse, versioni prima/dopo dei file,
e in generale tutti i metadati sul contesto di sviluppo.

Restano **6 campi**, il minimo necessario per lavorare in modo pulito:

- `title` + `body` — l'**evidenza semantica** su cui il sistema ragiona
  (Decisione 01 §7);
- `id`, `repository`, `pr_number` — tre metadati di **identità e tracciabilità**
  (ricondurre ogni requisito prodotto alla PR di origine);
- `timestamp` — serve al Runner per **ordinare cronologicamente** le PR prima
  di elaborarle, così la memoria si costruisce nel giusto ordine.

La scelta di ridurre ai 6 minimi è deliberata: la misura sperimentale che
vogliamo fare è *"quanto è ricostruibile un requisito dal solo testo
descrittivo della PR"*. Se lasciassimo i diff, il modello **barerebbe** leggendo
il codice. Se lasciassimo i commit, mescolerebbe intento originale e cronaca
dello sviluppo. Meno campi = misura più pulita.

---

## Step 02 — PullRequestLoader

Il **PullRequestLoader** (`src/are/input/loader.py`) è la **porta d'ingresso**
del sistema. Prende il file JSON prodotto dallo script di preprocessing, ne
verifica rigorosamente il formato, e lo trasforma in una lista di oggetti
Python immutabili (`PullRequestRecord`, in `src/are/input/models.py`) su cui
gli step successivi potranno lavorare senza dover rifare controlli.

I controlli fatti sono in cascata:

- **File**: esiste? è un file (non una cartella)? è leggibile come UTF-8?
- **JSON**: è valido? è un array? l'array non è vuoto? nessuna chiave
  duplicata? nessun numero non-standard (`NaN`, `Infinity`)?
- **Record per record** (schema del contratto di ingresso): ci sono tutti e
  soli i **6 campi previsti**? i tipi sono giusti (`title`/`body` stringhe,
  `pr_number` intero puro, `timestamp` ISO-8601 con fuso orario esplicito)?
- **Unicità**: due PR non possono avere lo stesso `id`.

Ogni tipo di problema ha un errore tipizzato dedicato
(`src/are/input/exceptions.py`) con un messaggio umano che dice esattamente
cosa non va — così se il file di input ha un difetto, la pipeline **si ferma
subito**, prima che gli agenti comincino a lavorare.

La filosofia è **"zero coercizioni silenziose"**: se il preprocessing ha
sbagliato (es. `pr_number` è la stringa `"123"` invece dell'intero `123`), il
loader **non converte**, rifiuta. Se il preprocessing ha aggiunto un campo in
più (es. `author`), rifiuta pure quello. Meglio scoprire subito un errore
chiaro che scoprire dopo un'ora un requisito prodotto su dati mal formati.
Zero dipendenze esterne (solo libreria standard di Python) per lo stesso
motivo: meno cose che si possono rompere in futuro.

Il loader **fa poco e lo fa bene**: legge, valida, restituisce. Non ordina
cronologicamente (lo farà il Runner), non filtra le PR, non giudica il
contenuto (titolo o body vuoti sono accettati, decideranno i nodi semantici),
non conosce PR4Code (sa solo lo schema del JSON normalizzato — se domani
cambierete dataset, il loader non se ne accorge).

---

## Step 03 — Extractability (il gate)

L'**Extractability** (`src/are/agents/extractability.py`) è il **primo
cancello** della pipeline: decide se la Pull Request contiene abbastanza
testo per essere anche solo *valutata*. È l'unico punto in cui una PR può
essere scartata **prima** di chiamare l'LLM.

**È deterministico, non è un agente LLM.** La Decisione 05 permetterebbe di
implementarlo anche come agente LLM, ma qui è stato scelto un **controllo
sintattico** per tre motivi:

- **Riproducibilità** — un controllo sintattico dà sempre lo stesso esito; un
  LLM può cambiare risposta tra un'esecuzione e l'altra.
- **Divisione di responsabilità** — questo gate decide *senza vedere il
  requisito*; il giudizio semantico spetta all'Assessment Agent, che ha
  davanti anche il candidato prodotto e può eventualmente rifiutare più tardi
  con `REJECT`.
- **Costo** — zero chiamate all'LLM per PR scartabili "in modo incontestabile".

Controlla due sole condizioni: il **body è vuoto**? → scarta. La **lunghezza
totale** (titolo + body, spazi tolti) è **sotto i 50 caratteri**? → scarta.
Altrimenti → passa. La soglia di 50 caratteri è dichiaratamente **provvisoria**
("criterio di comodo") e va calibrata sul gold standard.

Restituisce un oggetto con due campi:

- `decision` — `EXTRACTABLE` o `NOT_EXTRACTABLE`, serve al **codice** per
  decidere dove andare;
- `reason` — una stringa in italiano **scritta da noi nel codice** (nessun
  LLM), utile agli **umani**: appare nel log a schermo mentre gira e nel file
  di report del run (`experiments/runs/run-*.json`). Le motivazioni possibili
  sono in tutto 3, cablate come template — non generate.

Il gate **non fa** valutazioni semantiche: non giudica se la PR contenga
davvero un comportamento funzionale (lo fa l'Assessment), non applica la
regola "il nome di un artefatto non è evidenza" (Decisione 01 §9.2, la applica
l'Assessment con `REJECT`), non chiama l'LLM.

Esiti: `EXTRACTABLE` → si passa allo Step 04 (Generation Agent).
`NOT_EXTRACTABLE` → si va direttamente al terminale DECLINE, senza consumare
nemmeno un token.

### Cosa c'è dentro un log del run

Ogni esecuzione della pipeline produce un file JSON in `experiments/runs/`
che riassume tutto quello che è successo. Struttura tipica:

- `run` — metadati dell'esecuzione: data, file di input, modelli usati per i
  due agenti, configurazione del workflow, e **usage aggregato** (numero di
  chiamate LLM, token in/out per agente, costo stimato in USD, riferimento
  del pricing);
- `summary` — quante PR sono finite in ciascun esito (`ACCEPTED`,
  `NOT_EXTRACTABLE`, `REJECTED`, ecc.);
- `results` — per ogni PR elaborata: id, titolo, esito finale,
  `extractability_reason` (la nostra stringa cablata), il requisito accettato
  se c'è, il numero di tentativi di generazione, e lo storico iterazione per
  iterazione (candidato prodotto, decisione dell'Assessment, eventuale
  feedback strutturato).

Aprire uno di questi file — es. `run-20260828T142024Z.json` — basta a capire
mesi dopo cos'ha fatto il sistema su quel campione, senza rieseguirlo.

---

## Step 04 — Generation Agent

Il **primo dei due agenti LLM** della pipeline. Dato titolo e body di una PR,
scrive **un requisito funzionale** che esprima il comportamento che il sistema
deve garantire. È il momento in cui la pipeline "produce": tutto quello che
c'è prima è preparazione, tutto quello che c'è dopo è valutazione.

Vive in tre file che lavorano insieme:

- `src/are/agents/llm_agents.py` — la classe `LLMRequirementGenerator`
  (righe 164-219): il codice dell'agente. Prepara il messaggio, chiama il
  modello, interpreta la risposta.
- `prompts/generation/v1.md` — il **prompt di sistema** in inglese: chi è
  l'agente, cosa deve fare, i 5 pattern EARS, 8 esempi. È l'anima
  dell'agente. Il suffisso `v1` significa "versione 1": se domani il prompt
  cambia, nasce un `v2.md` e si può confrontare esperimenti fatti con
  versioni diverse.
- `src/are/agents/prompts.py` — piccolo modulo di supporto che legge il file
  `.md` dal disco nella versione richiesta.

L'agente ha **due modalità**. **Prima generazione**: scrive dalla sola evidenza
della PR. **Revisione**: ha ricevuto un `REVISE` dall'Assessment, riceve anche
il candidato precedente + feedback strutturato e riscrive applicandolo.
Riceve solo il tentativo immediatamente precedente, non lo storico completo
(scelta esplicita: messaggio corto e focalizzato).

Come si aggancia al **livello LLM Client** (la barra tratteggiata in cima al
diagramma, Decisione 02): l'agente riceve dall'esterno un `LLMClient`
(un'interfaccia astratta). Non sa se sotto ci sia `AnthropicLLMClient` o un
client finto per i test. Vede solo il "tubo": `self._client.complete(system,
user_message)`. Cambiare fornitore = riscrivere solo il client, non l'agente.
Il prompt `v1.md` viene caricato **una sola volta** in fase di creazione
dell'agente (in `__init__`), non a ogni chiamata.

Il modello restituisce **sempre JSON**, in una di due forme:

- `{"requirement": "..."}` — requisito prodotto. Passa allo **Step 05**
  (Candidate) → **Step 06** (Memory Retrieval) → **Step 07** (Assessment).
- `{"cannot_ground": "..."}` — **rinuncia motivata**, esito legittimo
  previsto dalla Decisione 01 §11.10. L'agente dichiara *"non posso
  scrivere un requisito fondato"* invece di inventarne uno. **Salta Step 05
  e Step 06** e va direttamente all'Assessment (non c'è candidato = non c'è
  cosa cercare in memoria). L'Assessment può poi confermare la rinuncia
  (→ terminale `NOT_EXTRACTABLE`) o dissentire con `REVISE`.

Il **prompt v1** è la traduzione operativa della Decisione 01: EARS + `shall`
obbligatorio, grounding, WHAT/HOW, removal test, regola "il nome di un
artefatto non è evidenza". È organizzato in blocchi: `<role>`, `<task>`,
`<definitions>`, `<procedure>`, `<examples>` (8 esempi concreti),
`<output_format>`. Il modello lo riceve intero a ogni chiamata.

Filosofia: **parsing severo**. Se il modello risponde male (JSON invalido,
campo mancante), l'agente non prova a rimediare — alza `AgentResponseError` e
la pipeline si ferma per quella PR. Preferiamo un fallimento visibile a un
requisito inventato dal parser.

Cosa NON fa: non decide se la PR è estraibile (fatto dallo Step 03); non
valuta la qualità del proprio output (Step 07); non consulta la memoria
(Step 06); non decide se rifare (Step 08).

### iteration_history — cos'è

Nel file di report del run (`experiments/runs/run-*.json`), sotto ogni PR
elaborata, c'è un campo `iteration_history`: una lista con **un elemento per
ogni tentativo** che il generator ha fatto su quella PR. Ogni elemento
contiene: numero del tentativo, candidato prodotto (o `null` se rinuncia),
motivazione della rinuncia (se c'è), e cosa ha detto l'Assessment su quel
tentativo (decisione + le 4 liste di feedback strutturato).

Non è "quello che ha fatto solo il generator": è **lo scambio completo
generator ↔ Assessment** per ciascun tentativo, in ordine. Se una PR ha
`iteration_history` con 3 elementi, significa che il generator ha prodotto 3
candidati diversi e il valutatore ha risposto 3 volte.

Attenzione alla gerarchia: **1 run → 1 file JSON → N PR → M tentativi
ciascuna** (max 3). L'`iteration_history` è una sezione dentro il record di
una singola PR, non un file separato.

---

## Step 05 — Candidate Requirement

**È un artefatto, non uno step di lavoro.** Nessun codice viene eseguito qui:
è la rappresentazione visuale nel diagramma del requisito che il Generation
Agent (Step 04) ha appena prodotto, in attesa di essere sottoposto a Memory
Retrieval e Assessment.

**Cos'è un "artefatto".** In ingegneria del software un artefatto è **un pezzo
di lavoro prodotto o consumato** durante un processo — *la cosa che resta dopo
un'azione*: un file di codice, un requisito scritto, un JSON di configurazione,
un log. Nella nostra pipeline sono artefatti i dati che passano da uno step al
successivo (la PR normalizzata, il candidato, l'assessment result, il file di
report). Sono **cose statiche**, in contrapposizione agli step che sono
**azioni**.

**Tecnicamente**, il candidato è una stringa in inglese in forma EARS. Vive
dentro `GenerationOutcome` (`src/are/agents/state.py`), che ha due campi:
`requirement: str | None` (il candidato) e `refusal_reason: str | None` (la
rinuncia). Uno dei due è valorizzato, l'altro è `None`.

**Perché "candidate"**: perché non è ancora accettato. È una proposta del
Generator in attesa di validazione. Solo dopo l'`ACCEPT` dell'Assessment
diventa un requisito "vero" nella memoria a lungo termine. Fino a quel momento
può essere accettato, rimandato indietro con `REVISE`, o rifiutato con
`REJECT`.

### Dove il candidato viene salvato (tre "vite")

1. **In RAM, durante l'esecuzione** (secondi). Solo oggetto Python in memoria,
   nessun file. Vive in `GenerationOutcome` e `RequirementState`. Attenzione:
   `state.py` *definisce la forma* (la classe), ma non contiene il candidato
   di alcuna PR specifica — le istanze nascono al volo mentre la pipeline
   gira.

2. **Persistito nel file di report, dopo l'esecuzione** (per sempre). Quando
   il Runner finisce di elaborare tutto, serializza in JSON e scrive
   `experiments/runs/run-YYYYMMDDTHHMMSSZ.json`. Il candidato compare **in
   due posti**: dentro `iteration_history` (un elemento per tentativo, con il
   candidato di quel tentativo), e nel campo `accepted_requirement` (solo se
   la PR è finita in `ACCEPTED`, contiene il candidato vincente). Formato:
   JSON. Non esiste un file dedicato "solo al candidato".

3. **Nella memoria a lungo termine, se è accettato** (per sempre, riutilizzabile).
   Se ottiene `ACCEPT`, va *anche* nel database SQLite in
   `experiments/memory/run-*.db`. Da lì può essere recuperato come "requisito
   storico" quando l'Assessment valuta PR successive. Dettagli allo Step 06.

### Come si aggancia al flusso

Arriva dal Generator (04), va a Memory Retrieval (06) come query semantica, e
poi all'Assessment (07) dentro il prompt come `CANDIDATE REQUIREMENT:`. Se
invece del candidato c'è `cannot_ground`, questo blocco viene saltato insieme
al Memory Retrieval (arco grigio nel diagramma).

**Contiene**: solo la frase del requisito. **Non contiene**: ragionamento del
Generator, token usati, numero di tentativo, esito dell'Assessment. Tutte
cose che vivono altrove nello stato del workflow.

---

## Step 06 — Memory Retrieval + MCP

Il **ponte con la memoria a lungo termine**: dopo la generazione, il sistema
dovrebbe interrogare i requisiti storici semanticamente simili al candidato e
passarli all'Assessment come contesto. È lo step con la parte più corposa
ancora da fare: **DB c'è, retrieval semantico e server MCP no**.

**Il concetto (obiettivo del design).** Dopo che il Generator ha prodotto un
candidato, il sistema fa una query semantica sui requisiti già validati e
restituisce una lista top-k. L'Assessment li usa per classificare la
relazione: `NEW`, `DUPLICATE`, `OVERLAPS`, `REFINES`, `SUPERSEDES`,
`CONFLICTS`.

**Perché il retrieval PRIMA dell'Assessment, non dopo.** Domanda ricorrente:
"non è l'Assessment che guarda la memoria?". No: il retrieval è un **helper**,
l'Assessment è il **giudice**. Metafora del tribunale: l'ufficiale che va in
archivio a recuperare i casi simili non è il giudice. Il giudice decide
*dopo* che il fascicolo è sul tavolo. Meccanicamente: `assess()` ha
`retrieved_requirements` come parametro in ingresso, e i risultati vengono
incollati nel prompt del valutatore sotto `PREVIOUSLY VALIDATED REQUIREMENTS:`.
L'Assessment li **consuma**, non li cerca.

Sequenza obbligata `04 → 05 → 06 → 07`: il retrieval usa il candidato come
query (deve esistere), l'Assessment consuma i risultati (li deve avere già
pronti).

### Cosa c'è di costruito

**✅ Database persistente su SQLite** (`src/are/db/`). Il
`SqliteRequirementRepository` sa scrivere requisiti accettati
(`store_accepted`) e leggerli con filtri per repository e data
(`list_requirements`). Schema con due tabelle: `requirements` (colonne
`embedding` e `embedding_model` predisposte ma NON usate) e
`requirement_relations` (esiste, vuota).

**⚠️ Retrieval semantico — NON implementato.** Il nodo del grafo
(`retrieve_memory`) esiste, il campo nello stato (`retrieved_requirements`)
esiste, ma il retriever vero (calcolo similarità sugli embedding) non c'è.
Nei run attuali `memory_enabled: false`: retrieval disattivato. La scrittura
sul DB avviene comunque, quindi il database si popola in vista del
completamento.

**❌ Server MCP — cartella VUOTA.** `src/are/mcp_server/` contiene solo un
`__init__.py` vuoto. Il server che dovrebbe esporre tool come
`search_requirements` agli agenti non è ancora stato scritto.

### Oggi vs domani

**Oggi** — accesso diretto: il controller chiama
`repository.store_accepted(...)`. Nessun MCP di mezzo.

**Domani** (obiettivo Decisione 04): Assessment → tool MCP → server MCP →
Retriever → Repository → SQLite. Il fatto che sotto ci sia SQLite diventa
un dettaglio implementativo, cambiare DB non tocca gli agenti.

### Persist via MCP (il rettangolo viola del diagramma)

Terzo momento in cui la memoria entra in gioco: **dopo** un `ACCEPT`, il
candidato viene scritto nella memoria a lungo termine. Oggi lo fa
direttamente `repository.store_accepted(pull_request, statement)`. Nel report
si legge il conteggio finale (`stored_requirements: N`) e il percorso del
file `.db`. **Un DB per run**: il nome coincide col timestamp del report, run
diversi non si contaminano.

### Un dettaglio importante — due date diverse

Ogni requisito nel DB ha due date: `source_pr_timestamp` (quando la PR fu
aperta su GitHub) e `created_at` (quando è stato inserito nel DB). Il
retrieval storico usa **la prima**: filtrare per la seconda ricostruirebbe
l'ordine dei tuoi esperimenti, non la storia del progetto.

### Cosa manca per completare lo Step 06

1. **`RequirementRetriever`** — componente che calcola embedding e li
   confronta (usa le colonne `embedding`/`embedding_model` già nello schema).
2. **Server MCP** — espone `search_requirements` e altri tool secondo la
   spec del Model Context Protocol.
3. **Aggancio nel grafo** — usare il retriever tramite MCP quando
   `memory_enabled=true`, invece del `NullRequirementStore` attuale.

Sono i prossimi grossi lavori dopo la fase di revisione.
