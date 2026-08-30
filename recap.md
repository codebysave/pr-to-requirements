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

## 2026-08-29 (pomeriggio) — Come recuperare dalla memoria: punto 5 per la tutor

**Branch:** `docs/memory-retrieval-question`

### 1. Perché questa modifica

Rileggendo il testo della proposta di stage è emerso che il recupero semantico
tramite embedding, previsto dalla Decisione 3.3 §8, **non è richiesto dalla
proposta**: questa chiede che il database «funga da long-term memory e consenta
di verificare duplicazioni o incoerenze», senza indicare come selezionare i
requisiti da confrontare.

Il *che cosa* è quindi fissato, il *come* no. La scelta va motivata e sottoposta
alla tutor invece di essere data per acquisita.

### 2. La soluzione adottata

**Recupero esaustivo**: si passano all'Assessment Agent *tutti* i requisiti già
validati, filtrati soltanto per progetto e per data della Pull Request di
origine. È il modello che, leggendo i testi, individua duplicati,
sovrapposizioni e contraddizioni.

Regge alla scala del progetto: 34 requisiti sono circa 1.000 token aggiunti ai
3.800 che il valutatore già riceve, cioè pochi centesimi per esecuzione. Su
progetti da 5-10 Pull Request l'aggiunta è trascurabile.

Ha inoltre un vantaggio non ovvio: **il modello legge le negazioni**. Molti dei
requisiti prodotti hanno forma «*shall not*», e distinguere un requisito dal suo
contrario è precisamente ciò che serve per riconoscere una contraddizione — cosa
che un embedding fa male.

### 3. Il nuovo punto 5 per la tutor

Aggiunto a `docs/meetings/open-questions-for-tutor-updated.md`: illustra le due
strade (recupero esaustivo e recupero semantico), confronta le due
implementazioni possibili degli embedding — servizio esterno *Voyage AI* contro
modello locale — ed elenca le ragioni a favore e contro, fra cui la debolezza
degli embedding sulle negazioni e l'assunzione di terze parti che
introdurrebbero.

La domanda posta non è quale soluzione sia migliore in assoluto, ma **se
l'implementazione del recupero semantico abbia valore per la tesi in sé**, anche
dove non sia tecnicamente necessaria.

### 4. Conseguenza sul piano di lavoro

La decisione sul fornitore di embedding, ferma da due giorni, **non blocca più
niente**: il recupero si può implementare subito senza sceglierlo, e le colonne
`embedding` ed `embedding_model` restano predisposte nello schema per un
passaggio futuro senza migrazioni.

L'ordine dei lavori diventa: file unico con isolamento per esecuzione, recupero
esaustivo, aggancio nel prompt del valutatore, verifica sulle tre coppie di
Pull Request duplicate presenti nel corpus, poi il server MCP — che la proposta
di stage nomina due volte ed è il pezzo mancante più rilevante.

### 5. Verifiche eseguite

Nessuna: la modifica riguarda un solo documento di progetto.

### 6. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[✔] Workflow LangGraph (agenti)     are.agents
[✔] Pipeline Runner                 are.runner
[ ] Memoria persistente (SQLite)    are.db          ← archiviazione fatta, recupero da fare
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale                         ← gold standard da rifare su OpenHands
```

Invariato: la modifica è documentale.

---

## 2026-08-29 — Il nome di un artefatto non è evidenza, e rilettura dei due prompt

**Branch:** `docs/named-artefact-question`

### 1. Perché questa modifica

Il corpus OpenHands contiene cinque Pull Request strutturalmente identiche
(`feat(ui): <nome> component`, circa 530 caratteri, stesso modulo compilato allo
stesso modo). In una sola esecuzione hanno ricevuto **quattro esiti diversi**, e
il valutatore ha motivato due di essi con affermazioni incompatibili fra loro:
su una Pull Request che un componente di interfaccia non ha comportamento
osservabile, su un'altra che «un requisito può essere fondato nella natura
dell'artefatto».

L'incoerenza non era un difetto di implementazione: era l'assenza di un
criterio. Il sistema non può essere coerente su una domanda a cui non avevamo
mai risposto.

### 2. La regola adottata

> Il significato convenzionale di un artefatto nominato non costituisce
> evidenza. Quando, rimosso il nome, l'evidenza non stabilisce più alcun
> comportamento osservabile, la Pull Request non è estraibile.

Tre ragioni, scritte per esteso nella nuova **Decisione 3.1 §9.2**: il requisito
che ne deriverebbe è vero di qualunque sistema dotato di quell'artefatto e non
trasporta informazione dall'evidenza; se il modello colma le lacune con la
propria conoscenza del dominio la misura sperimentale riguarda quella conoscenza
e non le Pull Request; ed è il caso complementare del *removal test* già
adottato.

La policy è **provvisoria**: il nuovo punto 4 di
`docs/meetings/open-questions-for-tutor-updated.md` la sottopone alla tutor
insieme all'alternativa, e dichiara che cosa costerebbe invertirla.

### 3. Il punto delicato: una scappatoia nel removal test

Il *removal test* diceva: rimossi i nomi, se non resta nulla allora il
cambiamento di meccanismo era lo scopo della Pull Request e nominarlo è
legittimo. Applicata a «Implements tab component» quella frase **autorizzava**
esattamente il caso da escludere — ed è la porta da cui il valutatore era
passato.

Il blocco `<definitions>`, condiviso dai due agenti, ora distingue i due casi in
base a ciò che dice l'evidenza: quando dichiara che cosa cambia per un
osservatore (un valore predefinito diverso, un risultato diverso, un effetto
visibile) nominare il meccanismo resta legittimo; quando dichiara soltanto che
l'artefatto è stato aggiunto, non c'è requisito da fondare.

### 4. Dove è stata inserita

- **Decisione 3.1 §9.2** — la regola, le motivazioni, la tabella dei casi che
  restano estraibili e la traduzione operativa.
- **Blocco `<definitions>`** — la distinzione del punto 3, identica nei due
  prompt.
- **Generation Agent** — un controllo in più al passo 4 della procedura, il caso
  aggiunto fra quelli in cui rispondere `cannot_ground`, e un esempio.
- **Assessment Agent** — un passo dedicato nella procedura, con esito `REJECT` e
  non `REVISE` perché è un difetto di fondatezza; una precisazione nella sezione
  che tratta le rinunce del redattore («un nome non è un'affermazione generale
  di comportamento»); un esempio.

Gli esempi sono inventati e neutri, come impone il test anti-contaminazione.

### 5. Cosa ha rivelato la rilettura completa dei due prompt

- **Il Generation Agent non aveva alcun esempio di rinuncia.** Sette esempi su
  sette producevano un requisito, mentre il formato `cannot_ground` era
  descritto solo a parole. L'esempio aggiunto colma la lacuna.
- **Un passo della procedura di valutazione era ambiguo**: «*A comment ... is
  not a requirement. If so, REJECT*», dove «if so» segue una frase negativa.
  Corretto in «*If it is not, REJECT*».
- **Un test asseriva tre decisioni su quattro**, ignorando
  `CONFIRM_NOT_EXTRACTABLE`. Corretto.
- **Nuovo test sulla numerazione della procedura**: i passi decidono in ordine e
  il primo che scatta vince, quindi un passo inserito senza rinumerare i
  successivi ne produrrebbe due con lo stesso numero.

### 6. Due rettifiche a voci precedenti di questo recap

- **Voce del 28 agosto.** Affermava che il prompt del valutatore non nomina i
  requisiti recuperati dalla memoria. È **falso**: la sezione
  `<historical_requirements>` esiste, corrisponde all'intestazione prodotta
  dall'agente e stabilisce che la somiglianza con un requisito storico non
  determina da sola l'esito. Resta un difetto minore, cioè che non è richiamata
  dalla `<procedure>`. La decisione di tenere spento il recupero non cambia:
  regge sulle altre due ragioni.
- **Voce del 27 agosto.** Diceva che i pattern EARS sono «consigliati e non
  obbligatori», in contrasto con la Decisione 3.1 §6 e con entrambi i prompt,
  dove l'uso di uno dei cinque è obbligatorio e la non conformità comporta
  `REVISE`.

### 7. Verifiche eseguite

- `uv run ruff check .` e `ruff format` — puliti;
- `uv run pytest` — **186 test passati** (2 nuovi: presenza del criterio in
  entrambi i prompt, numerazione consecutiva della procedura di valutazione);
- il test che verifica l'identità byte per byte del blocco `<definitions>`
  continua a passare dopo la modifica.

Nessuna esecuzione reale: la regola andrà verificata sulle cinque Pull Request
dell'esempio, e servirà **più di una replica**, dato che su quei casi abbiamo
già misurato esiti che cambiano fra esecuzioni identiche.

### 8. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[✔] Workflow LangGraph (agenti)     are.agents
[✔] Pipeline Runner                 are.runner
[ ] Memoria persistente (SQLite)    are.db          ← archiviazione fatta, recupero da fare
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale                         ← gold standard da rifare su OpenHands
```

Nessuna casella cambia: la modifica riguarda i criteri applicati dagli agenti,
non i componenti del sistema.

---

## 2026-08-28 — Memoria persistente su SQLite: archiviazione dei requisiti validati

**Branch:** `feat/memory-persistence`

### 1. Perché questa modifica

Fino a ieri ogni esecuzione produceva un report JSON e finiva lì: la run
successiva ripartiva da zero e nessun requisito sopravviveva. La Decisione 3.3
prevede una memoria persistente con due funzioni distinte, che conviene tenere
separate:

- **archivio** — i requisiti accettati si accumulano e diventano l'esito del
  sistema nel tempo;
- **contesto per il valutatore** — i requisiti affini vengono recuperati e
  mostrati all'Assessment Agent prima del giudizio.

Questa voce copre **soltanto la prima**. La seconda arriva dopo, per una ragione
scritta al punto 7.

### 2. Cosa esisteva già

Quasi tutto il cablaggio era pronto dai passi precedenti: i protocolli
`MemoryRetriever` e `AcceptedRequirementStore` in `ports.py` con implementazioni
inerti, il tipo `RetrievedRequirement`, il nodo `retrieve_memory` nel grafo, la
chiamata a `store_accepted` nel nodo di accettazione, e l'elaborazione in ordine
cronologico nel Runner.

Mancavano soltanto le implementazioni concrete. **Il grafo, il routing e gli
agenti non sono stati toccati.**

### 3. Il repository SQLite

Nuovo pacchetto `src/are/db/`:

- `models.py` — `StoredRequirement`, `RequirementRelation`, `RelationType`;
- `repository.py` — `SqliteRequirementRepository`, che implementa il protocollo
  `AcceptedRequirementStore` e offre `store_accepted`, `get_by_id`,
  `list_requirements`, `count`, `save_relation`, `get_relations`;
- `__init__.py` — API pubblica del pacchetto.

Nessuna dipendenza nuova: `sqlite3` è nella libreria standard di Python.

### 4. Le scelte fatte sullo schema

Quattro decisioni che vale la pena aver scritto:

- **Due date distinte.** `source_pr_timestamp` è la data della Pull Request,
  `created_at` è il momento dell'inserimento. Il filtro storico previsto dalla
  Decisione 3.3 §2 usa la **prima**: filtrare sulla seconda ricostruirebbe
  l'ordine in cui abbiamo lanciato gli script, non la storia del progetto. Le
  date sono normalizzate a UTC, così l'ordinamento lessicografico delle stringhe
  ISO coincide con quello cronologico.
- **Nessun vincolo di unicità sulla coppia (repository, numero PR).** Oggi la
  pipeline produce al massimo un requisito per Pull Request, ma inciderlo nello
  schema costringerebbe a una migrazione se un giorno ne producesse due.
- **L'evidenza viene salvata**: titolo e corpo della Pull Request finiscono nella
  riga. Costa una sessantina di KB su 46 requisiti e rende il database
  **autosufficiente** — si legge un requisito e si vede da cosa nasce, senza il
  file JSON di partenza a fianco. Per un allegato di tesi è la differenza fra un
  artefatto leggibile e una tabella di stringhe.
- **`run_id`, unica aggiunta rispetto alla Decisione 3.3.** Identifica
  l'esecuzione che ha scritto ogni riga: senza, in un database condiviso fra più
  run non si potrebbe sapere quale esecuzione ha prodotto cosa, né ripulire
  selettivamente. Coincide con il timestamp che nomina il report.

Le colonne `embedding` ed `embedding_model` esistono ma restano vuote: crearle
adesso costa zero ed evita una migrazione quando arriverà il retriever.

### 5. Il cablaggio, e i due interruttori

`__main__.py` costruisce il repository e lo passa nelle `WorkflowDependencies`.
Nuova opzione `--memory-db` per puntare a un database esistente; senza, ogni
esecuzione ne crea uno nuovo in `experiments/memory/run-<timestamp>.db`.

Il default è deliberato: una run che partisse con la memoria già popolata dalla
precedente avrebbe un vantaggio e il confronto fra esecuzioni non direbbe più
nulla. Chi vuole accumulare lo chiede esplicitamente.

Da qui in avanti il sistema ha **due interruttori indipendenti** per le due
funzioni del punto 1:

- il **database viene sempre scritto** (l'archivio non altera il comportamento
  degli agenti);
- **`memory_enabled` governa soltanto il recupero**, cioè l'unica cosa che
  cambia l'input del valutatore. Resta a `false`.

Il report di ogni esecuzione registra ora percorso del database, `run_id` e
numero di requisiti archiviati.

### 6. Prova reale

Esecuzione con Haiku su 5 Pull Request del campione OpenHands
(`experiments/runs/run-20260828T142024Z.json`, $0,044): 3 requisiti accettati,
3 righe scritte in memoria, con tracciabilità corretta alla Pull Request di
origine, date coerenti e relazioni vuote come previsto.

Nota emersa dalla prova, più importante della prova stessa: sulle stesse 5 Pull
Request, con lo stesso modello e gli stessi prompt di ieri e senza alcuna
modifica al codice fra le due esecuzioni, la PR #9590 è passata da
`NOT_EXTRACTABLE` ad `ACCEPTED` e la #9591 da `REJECTED` a `NOT_EXTRACTABLE`.
**Il 40% degli esiti si è spostato senza che nulla di osservabile cambiasse.**

Entrambe appartengono al gruppo dei cinque componenti UI: i quattro esiti diversi
su cinque input equivalenti non erano quindi un incidente di una singola
esecuzione. La misura è stata scritta in `confronto-modelli.md` §7.2, e ne è
seguito un aggiornamento datato al §8: con una sola replica per configurazione,
differenze di uno o due requisiti su nove rientrano nella banda di rumore, quindi
la raccomandazione su quale coppia di modelli usare resta un'indicazione
operativa e non un risultato. Reggono invece il numero di revisioni e la qualità
dei requisiti finali, che sono osservazioni sul comportamento del ciclo e non
conteggi al margine.

### 7. Cosa non fa ancora, e perché

- **Il retriever semantico non esiste.** Richiede una decisione sugli embedding
  (fornitore esterno o modello locale) ancora aperta.
- **La tabella delle relazioni è predisposta ma vuota**: nessun componente della
  pipeline rileva oggi duplicati o conflitti. Le operazioni ci sono, il
  produttore no.
- **Il prompt del valutatore tratta già i requisiti recuperati**, nella sezione
  `<historical_requirements>`, che corrisponde all'intestazione prodotta
  dall'agente (`PREVIOUSLY VALIDATED REQUIREMENTS`) e stabilisce che la
  relazione con un requisito storico non determina da sola l'esito. *Rettifica
  del 29 agosto: la prima stesura di questa voce affermava il contrario. La
  sezione esiste; resta un difetto minore, cioè che non è richiamata dalla
  `<procedure>`, l'elenco ordinato che decide l'esito.*
- Il recupero resta comunque disattivato per le altre due ragioni: la decisione
  sugli embedding e la dipendenza dall'ordine.
- **Il recupero rende il sistema dipendente dall'ordine** di elaborazione: va
  documentato nella Decisione 3.7 come variabile sperimentale prima di
  accenderlo, non dopo aver visto i risultati.

### 8. Verifiche eseguite

- `uv run ruff check .` e `ruff format` — puliti;
- `uv run pytest` — **184 test passati** (20 nuovi: scrittura e rilettura,
  tracciabilità, filtri per repository e per data, confronto fra fusi orari
  diversi, relazioni e vincoli di integrità, persistenza su file). I test girano
  su un database in memoria e non lasciano file;
- una esecuzione reale end-to-end con ispezione del database prodotto.

### 9. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[✔] Workflow LangGraph (agenti)     are.agents
[✔] Pipeline Runner                 are.runner
[ ] Memoria persistente (SQLite)    are.db          ← archiviazione fatta, recupero da fare
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale                         ← gold standard da rifare su OpenHands
```

La casella resta aperta di proposito: metà del componente è in funzione e
verificata, l'altra metà dipende da una decisione non ancora presa.

---

## 2026-08-27 (pomeriggio) — Secondo corpus, limite del valutatore alzato, analisi estesa

**Branch:** `chore/openhands-corpus`

### 1. Perché questa modifica

La voce precedente si chiudeva con un limite dichiarato: le cinque prove sui
modelli giravano tutte sullo stesso campione di 9 Pull Request, di cui 5
generate da uno scanner automatico. Non sapevamo quanto di quei risultati
dipendesse dal campione. Questa modifica lo misura.

### 2. Il secondo corpus

Aggiunto `experiments/samples/sample-All-Hands-AI_OpenHands.json`: **46 Pull
Request** di `All-Hands-AI/OpenHands`, scritte da persone, media 1.422 caratteri
fra titolo e corpo, nessuna sotto la soglia del gate. È materiale molto più
onesto del campione scrapy.

Eseguito con Haiku su entrambi gli agenti, a codice e prompt invariati
(`experiments/runs/run-20260827T140858Z.json`).

### 3. Il risultato: il corpus conta più del modello

| | scrapy (9 PR) | OpenHands (46 PR) |
|---|---|---|
| Accettati | 3 (33%) | 34 (74%) |
| Non estraibili | 6 (67%) | 11 (24%) |
| Rifiutati | 0 | 1 |
| PR che entrano nel ciclo | 5 su 9 (55%) | 4 su 46 (8,7%) |
| Costo | $0,11 | $0,38 |

Cambiando **soltanto il corpus**, lo stesso modello passa dal 33% al 74% di
accettazione: uno scarto più grande di qualunque differenza fra modelli
misurata nella voce precedente.

Conseguenza metodologica: i **valori assoluti** delle cinque prove sono una
proprietà del campione, non dei modelli. Il confronto *fra* le cinque prove
resta valido, perché la variabile cambiata era una sola.

### 4. I difetti non spariscono, si spostano

Su scrapy Haiku rifiutava troppo; su OpenHands accetta troppo. Cinque
accettazioni non superano i criteri della Decisione 3.1 — fra cui un requisito
di puro meccanismo (`use the RuntimeStatus enum instead of hardcoded strings`),
uno che descrive il comportamento del linter invece che del prodotto, e una
tautologia sulla configurazione. Le 11 rinunce sono invece quasi tutte fondate.

Ne emerge un'asimmetria utile: **quando Haiku rifiuta ha quasi sempre ragione,
quando accetta spesso no.**

### 5. L'esperimento naturale dei cinque componenti UI

Il corpus contiene cinque Pull Request quasi identiche (`feat(ui): <nome>
component`, ~530 caratteri, stesso template) che hanno ricevuto **quattro esiti
diversi nella stessa esecuzione**: una `NOT_EXTRACTABLE`, una `REJECTED`, una
accettata al primo colpo conservando il nome del componente, due accettate dopo
due giri con il nome del componente rimosso.

Il valutatore si contraddice apertamente sul punto: su una PR scrive che un
componente UI «è un blocco costruttivo interno», su un'altra che «un requisito
può essere fondato nella natura dell'artefatto, non solo in una descrizione
esplicita». Resta aperta una domanda mai decisa: **il significato convenzionale
di un artefatto nominato conta come evidenza?**

È il risultato più solido della giornata e va portato alla tutor.

### 6. Limite di token del valutatore alzato

`max_tokens` dell'assessment passa da 2048 a **4096** in `config/llm.toml`, con
la motivazione scritta nel file: a 2048 una risposta di Sonnet era stata
troncata a metà JSON e la Pull Request era finita in `ERROR`. La modifica era
stata rimandata di proposito per non rendere incomparabili le cinque prove.

### 7. Documento di analisi esteso

`experiments/analisi/confronto-modelli.md` guadagna il §9 con la verifica, e due
**aggiornamenti datati** ai paragrafi che generalizzavano troppo (§4.1 su Haiku,
§7.4 sul campione). La conclusione operativa è che il gold standard va costruito
sul corpus OpenHands e non su scrapy: le schede attuali sono tarate sulle Pull
Request sbagliate.

### 8. Verifiche eseguite

- `uv run ruff check .` e `ruff format` — puliti;
- `uv run pytest` — **164 test passati** (nessun test nuovo: la modifica è di
  configurazione e documentazione, il codice non cambia);
- 11 esecuzioni reali nella giornata, 136 Pull Request elaborate, **$3,40** di
  costo complessivo.

### 9. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[✔] Workflow LangGraph (agenti)     are.agents
[✔] Pipeline Runner                 are.runner
[ ] Memoria persistente (SQLite)    are.db
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale                         ← gold standard da rifare su OpenHands
```

Nessuna casella nuova: la modifica misura il sistema esistente e ne corregge la
documentazione. Il prossimo componente da costruire è la memoria persistente.

---

## 2026-08-27 — Gate deterministico, rifiuto motivato, memoria del valutatore e confronto fra modelli

**Branch:** `feat/deterministic-gate`

### 1. Perché questa giornata

La giornata precedente si era chiusa con un problema chiaro: il sistema
funzionava, ma i suoi esiti cambiavano a ogni modifica dei prompt senza che si
potesse dire se stessero migliorando. Sono emersi tre difetti concreti dalle
esecuzioni reali, e questa voce racconta come sono stati corretti; poi cinque
esecuzioni controllate hanno finalmente separato l'effetto dei prompt da quello
del modello.

### 2. Il gate non è più un agente LLM

Il primo controllo della pipeline — «questa Pull Request contiene abbastanza
informazione perché valga la pena valutarla?» — era affidato a un modello. Era
la scelta sbagliata per tre motivi, ora scritti in testa a
`src/are/agents/extractability.py`:

- **riproducibilità**: un controllo sintattico dà sempre lo stesso esito, un
  modello no;
- **informazione disponibile**: il gate decide *senza vedere il requisito*,
  mentre l'Assessment Agent ce l'ha davanti. Il giudizio semantico spetta
  quindi a quest'ultimo, che può rifiutare con `REJECT`;
- **costo**: zero invece di una chiamata per Pull Request.

Il nuovo `DeterministicExtractabilityChecker` scarta soltanto i casi
incontestabili: corpo vuoto o assente, oppure titolo più corpo sotto una soglia
di caratteri (`min_evidence_characters`, default 50, configurabile in
`config/workflow.toml`). La soglia è dichiarata nel codice e nella
configurazione come **criterio di comodo da calibrare sul gold standard**, non
come valore fondato.

Il prompt `prompts/extractability/v1.md` e la classe `LLMExtractabilityChecker`
sono stati **eliminati**. Da qui in avanti il sistema ha **due agenti e due
prompt**: il gate non è un agente.

### 3. Il valutatore ora vede i propri giudizi precedenti

Nelle esecuzioni si vedeva il valutatore chiedere una correzione, riceverla, e
poi chiederne una opposta al giro successivo: a ogni chiamata partiva da zero,
senza sapere di aver già parlato di quella Pull Request.

Ora l'`IterationRecord` con i tentativi precedenti viene passato dal grafo al
nodo di assessment, e il prompt contiene un blocco `<previous_attempts>` con
una regola esplicita: **se il problema segnalato è stato risolto non va
ripetuto; se è rimasto, può essere riproposto.** Non è un divieto di insistere,
è un divieto di contraddirsi.

Effetto misurato: da quel momento in poi nessuna esecuzione ha più prodotto
`FAILED_VALIDATION` per esaurimento dei tentativi.

### 4. Il generatore può dichiarare di non riuscire, e il valutatore conferma o dissente

Prima il generatore era obbligato a produrre una frase anche quando l'evidenza
non la sosteneva: ne uscivano requisiti inventati, oppure campi vuoti e prosa
al posto del JSON.

Ora può rispondere `{"cannot_ground": "..."}` con la motivazione. Il flusso
prosegue comunque verso il valutatore, che ha due strade:

- **concorda** → `CONFIRM_NOT_EXTRACTABLE`, la Pull Request si chiude come non
  estraibile;
- **dissente** → `REVISE`, spiegando perché un requisito è invece fondato e da
  dove partire per scriverlo.

In codice: nuovi `GenerationOutcome` e `AssessmentDecision.CONFIRM_NOT_EXTRACTABLE`
in `state.py`, nuovo instradamento `route_after_generation` (una rinuncia non
passa dal recupero in memoria, che presuppone un candidato da confrontare),
firma di `assess()` estesa in `ports.py`. Il flusso è documentato nella
Decisione 3.5, §10.4.

### 5. Precisazioni ai documenti di design

- **Decisione 3.1 §6.5** — introdotto il **quinto pattern EARS** (*optional
  feature*: `Where <feature is present>, the system shall <response>`), che
  mancava e che è il pattern corretto per i valori predefiniti. L'uso di uno
  dei cinque resta **obbligatorio** per il Generation Agent (§6), ma la
  mancata conformità è un difetto di **formulazione**: comporta `REVISE` e non
  `REJECT`, perché un requisito fondato ma mal formattato è recuperabile.
  *Rettifica del 29 agosto: la prima stesura di questa voce diceva
  «consigliati e non obbligatori», in contrasto con il §6 della Decisione 3.1
  e con entrambi i prompt.*
- **Decisione 3.1 §8.1** — il test black-box come criterio operativo di
  «comportamento richiesto».
- **Decisione 3.1 §8.2** — il requisito descrive il **sistema**, non la
  modifica: «il sistema ora usa X» non è un requisito.
- **Decisione 3.5 §4.3, §10.3, §10.4, §18** — riallineate al gate
  deterministico e al nuovo flusso di rifiuto.

### 6. Cinque esecuzioni per capire la scelta dei modelli

Con il codice fermo e i prompt fermi, il sistema è stato lanciato **cinque
volte sullo stesso campione** cambiando soltanto quale modello sta al posto del
generatore e quale al posto del valutatore.

| Generatore → Valutatore | Accettati | Non estraibili | Rifiutati | Errori | Revisioni | Costo |
|---|---|---|---|---|---|---|
| Haiku → Haiku | 3 | 6 | 0 | 0 | 5 | $0,11 |
| Haiku → Opus | 6 | 3 | 0 | 0 | 2 | $0,46 |
| Opus → Sonnet | 6 | 2 | 0 | 1 | 0 | $0,43 |
| Opus → Opus | 7 | 2 | 0 | 0 | 0 | $0,53 |
| Sonnet → Opus | 6 | 2 | 1 | 0 | 3 | $0,65 |

Tre risultati non ovvi, tutti documentati con gli esempi veri in
`experiments/analisi/confronto-modelli.md`:

1. **il ciclo di revisione si accende solo se c'è un divario di capacità** fra i
   due ruoli — con modelli pari (Haiku→Haiku, Opus→Opus) o con valutatore più
   debole (Opus→Sonnet) non produce alcun miglioramento;
2. **lo stesso modello è più severo da giudice che da autore**: Opus accetta
   senza obiezioni una formulazione scritta da Opus che poi boccia, definendola
   «circolare», quando arriva da Sonnet. È il rischio di Huang et al. 2024
   osservato sui nostri dati, e un argomento concreto per usare due modelli
   diversi;
3. **la configurazione con il modello migliore ovunque non è la migliore**: i
   requisiti finali di Sonnet→Opus superano quelli di Opus→Opus, perché il ciclo
   li corregge. È la tesi di Wang et al. 2025 (*Cross-Refine*) verificata sul
   nostro campione, e giustifica a posteriori la scelta della Decisione 3.2 di
   rendere il modello configurabile **per agente**.

### 7. Materiale per la valutazione

- `experiments/analisi/confronto-modelli.md` — il documento di analisi delle
  cinque esecuzioni, in italiano, con le citazioni tradotte e i rimandi ai
  report grezzi;
- `experiments/gold-standard/` — le schede di annotazione (`scheda-annotazione.md`
  come modello, una copia per annotatore) e `pull-request-in-input.md` con i
  soli testi delle 9 Pull Request, da leggere **prima** di guardare qualunque
  output del sistema;
- `experiments/runs/` — dieci nuovi report della giornata.

### 8. Limiti noti, dichiarati e non risolti

- **Manca il gold standard.** Ogni giudizio di qualità in questa voce è nostro,
  non misurato. È il passo che blocca tutto il resto.
- **`max_tokens = 2048` per il valutatore è troppo basso**: nell'esecuzione
  Opus→Sonnet ha troncato una risposta e la Pull Request è finita in `ERROR`.
  Va portato a 4096; non è stato fatto durante la serie per non rendere le
  cinque esecuzioni incomparabili.
- **Una sola esecuzione per configurazione** non permette di distinguere la
  differenza fra modelli dal rumore del campionamento — e senza `temperature`
  la variabilità non si può più sopprimere, va misurata con repliche.
- **Il campione è piccolo e sbilanciato**: 9 Pull Request, di cui 5 generate da
  uno scanner automatico con lo stesso boilerplate.

### 9. Verifiche eseguite

- `uv run ruff check .` e `ruff format` — puliti;
- `uv run pytest` — **164 test passati** (18 nuovi: gate deterministico,
  instradamento dopo la generazione, rifiuto motivato e conferma, blocco dei
  tentativi precedenti nel prompt);
- cinque esecuzioni reali complete sul campione, con tutte le combinazioni di
  modelli previste.

### 10. Stato del sistema dopo questa modifica

```text
[✔] Preprocessing del dataset       (script esterno al sistema)
[✔] Input Loader                    are.input
[✔] Configurazione + client LLM     are.llm
[✔] Workflow LangGraph (agenti)     are.agents
[✔] Pipeline Runner                 are.runner
[ ] Memoria persistente (SQLite)    are.db
[ ] Server MCP                      are.mcp_server
[ ] Valutazione sperimentale                         ← iniziata: gold standard da compilare
```

Nessuna casella nuova completata: la giornata ha corretto tre difetti degli
agenti e prodotto il primo confronto controllato fra modelli. L'ultima casella
è ora **in corso** — le schede del gold standard esistono ma vanno compilate a
mano, ed è la condizione perché qualunque altra modifica sia misurabile.

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
