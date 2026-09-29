# Confronto Ground Truth ↔ sistema — `comet-ml/opik`, 8 Pull Request

**Progetto:** PR-to-Requirements
**Annotatori:** Andrea Saverino · Marco Saverino Salvatore
**Università degli Studi di Milano-Bicocca** · tutor: Benedetta Donato

**Ground Truth:** `unificazione-GT_opik.md`
**Regole di unificazione:** `../unificazione_requisiti-GT.md`
**Esecuzione del sistema:** `experiments/runs/run-20260929T100302Z.json` — generatore
`claude-sonnet-5`, valutatore `claude-opus-5`, prompt generazione `v2` (fisso),
prompt valutazione `v1` (recupero deterministico via MCP), un solo tentativo
consentito prima che il sistema si sia fermato su ognuna delle otto Pull
Request — nessuna ha richiesto una revisione.

---

## 1. Come confrontiamo

Confrontiamo il Ground Truth unificato — non le due annotazioni originali — con
il requisito prodotto dal sistema, sulla corrispondenza semantica
(`MATCH`/`PARTIAL_MATCH`/`NO_MATCH`) e sulla rubrica di qualità a dieci
criteri, applicata a entrambi (due dei dodici criteri della rubrica completa
non si possono giudicare qui — si veda sotto). Guardiamo anche la traccia
completa dell'esecuzione — tentativi, decisione del valutatore, affermazioni
non sostenute — non solo il requisito finale.

---

## 2. Schede di confronto

### PR #2662

**Evidenza (estratto)**

```text
This PR fixes the trace thread object spec, allowing Fern to create the proper
mapping.
```

| | Requisito |
|---|---|
| **Ground Truth** | *The system shall define thread fields in the OpenAPI specification using types that allow the API definition generator to produce the correct field mappings.* |
| **Sistema** | *(nessun requisito accettato — vedi sotto)* |

**Che cosa ha fatto il sistema.** Un solo tentativo, **rifiutato dal
valutatore**: `REJECTED`.

```text
Candidato: "The system shall represent trace thread fields in the API
specification with types that correctly map to the actual field data
returned."

Il valutatore lo respinge con quattro affermazioni non sostenute: "types that
correctly map", "the actual field data returned", "which trace thread fields
are concerned", "which types they now have". Motivazione: "the evidence
states only that a specification document was corrected so that a
code-generation tool produces a proper mapping; it names no field, no type,
and no change observable from outside the system […] once the unsupported
elements are removed, nothing remains but the fact that a specification file
was edited, so no rewrite can produce a grounded behavioural requirement."
```

**Differenze rispetto al riferimento:** il sistema non produce alcun requisito.

**Analisi.**

```text
Questo è un disaccordo reale, non un errore evidente da una sola parte. Il
nostro Ground Truth (e prima ancora entrambe le annotazioni originali) tratta
"tipi che permettono al generatore di produrre il mapping corretto" come
comportamento sufficientemente generale da essere fondato (Decisione 3.1
§9.1). Il valutatore del sistema applica un criterio più severo: senza sapere
QUALE campo o QUALE tipo sia cambiato, anche una formulazione generica
resterebbe non verificabile, perché non c'è nulla di concreto da controllare
al di fuori di leggere la specifica e confrontarla con il codice.

Il punto ha un merito reale: né la nostra formulazione né le due originali
nominano un campo o un tipo specifico — sono generiche quanto il candidato del
sistema. Se il criterio del valutatore è corretto, lo stesso argomento
si applicherebbe anche al nostro Ground Truth.
```

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | — | — | — | — | — | — | — | — | — | — | — | — |

*Forma:* verbo `shall` ✔ · schema GT **ubiquitous** ✔ · schema sistema — nessun requisito accettato

**Esito:** nessuno dei tre (concordi sulla natura EXTRACTABLE/NOT del comportamento, **discordi sull'esito**) — GT 10/10, sistema **n/a**

---

### PR #2685

**Evidenza (estratto)**

```text
Fixed JSON parsing exception in OpenTelemetryMapper that was causing crashes
when processing OpenTelemetry spans with invalid JSON strings. […] Modified
logic to store invalid JSON as plain text instead of throwing exceptions.
```

| | Requisito |
|---|---|
| **Ground Truth** | *If a value in an OpenTelemetry span appears to contain JSON but cannot be parsed as valid JSON, then the system shall store the value as plain text.* |
| **Sistema** | *If a value in an OpenTelemetry span looks like JSON but cannot be parsed as valid JSON, then the system shall store that value as plain text instead of raising an exception.* |

**Che cosa ha fatto il sistema.** Un solo tentativo, **accettato senza alcun
rilievo**: nessuna affermazione non sostenuta, nessuna osservazione.

**Differenze rispetto al riferimento:** il sistema aggiunge *«instead of
raising an exception»*.

**Analisi.**

```text
L'aggiunta è grounded: il body lo dice alla lettera — "instead of throwing
exceptions". Il nostro Ground Truth lo lascia implicito nella scelta dello
schema (unwanted behaviour), il sistema lo rende esplicito nella risposta. Non
è un'eccedenza: è un dettaglio che l'evidenza fornisce e che il nostro
riferimento non riporta.
```

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |

*Forma:* verbo `shall` ✔ · schema GT **unwanted behaviour** ✔ · schema sistema **unwanted behaviour** ✔

**Esito: `MATCH`** — GT 10/10, sistema 10/10.

---

### PR #2695

**Evidenza (estratto)**

```text
Fix small race condition issue with sampling
Fix event publishing logic
Enforce consistent reading after closing threads
```

| | Requisito |
|---|---|
| **Ground Truth** | *When a thread has been closed, the system shall provide a consistent read of the thread.* |
| **Sistema** | *When a thread is closed, the system shall guarantee that subsequent reads of that thread return consistent, up-to-date data reflecting the closure.* |

**Che cosa ha fatto il sistema.** Un solo tentativo, **accettato senza alcun
rilievo**.

**Differenze rispetto al riferimento:** il sistema aggiunge *«up-to-date»*.

**Analisi.**

```text
Il body dice solo "consistent reading", non "up-to-date". È un'aggiunta
plausibile ma non letteralmente enunciata — una piccola estensione oltre
l'evidenza, non un errore che cambia il comportamento descritto.
```

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | ⚠ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |

*Forma:* verbo `shall` ✔ · schema GT **event-driven** ✔ · schema sistema **event-driven** ✔

**Esito: `MATCH`** — GT 10/10, sistema 10/10 con una riserva su *Evidence fidelity*.

---

### PR #2719

**Evidenza (estratto)**

```text
Addressing the read consistency issue by streaming threads pending closure,
closing, and publishing them
Fix the null point caused by the exception without a cause in the Online
Scoring subscriber.
```

| | Requisito |
|---|---|
| **Ground Truth** | *While a thread is pending closure, being closed, or being published, the system shall provide a consistent read of the thread.* |
| **Sistema** | *If a thread is pending closure, then the system shall complete and publish its closure so that subsequent reads reflect the thread's correct closed state.* |

**Che cosa ha fatto il sistema.** Un solo tentativo, **accettato**. Il
valutatore registra una relazione `OVERLAPS` con il requisito storico di
#2695 (*"the earlier one guarantees consistent reads after closure while the
candidate obliges the system to complete and publish closures that are
pending"*) — annotata, non trattata come difetto — e osserva che il
requisito copre solo la parte sulla chiusura del thread, non la seconda metà
della PR (il fix del puntatore nullo).

**Differenze rispetto al riferimento:** il sistema sposta l'obbligo centrale.
Il nostro GT afferma che le **letture** devono restare consistenti durante
queste fasi; il sistema afferma che il sistema deve **completare e pubblicare
la chiusura**, con la lettura consistente relegata a conseguenza (*"so
that…"*).

**Analisi.**

```text
Non è un'invenzione: "streaming threads pending closure, closing, and
publishing them" implica che il sistema esegua quelle operazioni, e questo è
osservabile (si può interrogare lo stato del thread). Ma il corpo della PR
dichiara esplicitamente il proprio scopo — "Addressing the read consistency
issue" — e il requisito del sistema fa di quello scopo una premessa
subordinata invece dell'obbligo stesso. È lo stesso tipo di inversione
oggetto/meccanismo di cui avevamo discusso in fase di annotazione (il caso
"stream" corretto sia da Marco sia in unificazione): qui non è il verbo
meccanicistico a essere il problema, è che l'obbligo asserito non è più
quello che l'evidenza dichiara come proprio scopo.

Il valutatore non lo rileva: gli unici due rilievi riguardano l'overlap con
#2695 e l'omissione del fix del puntatore nullo, mai lo spostamento
dell'obbligo centrale.
```

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | ⚠ | ✔ | ✔ | ✔ | ✔ | ⚠ | ✔ | — | ✔ | ⚠ | — |

*Forma:* verbo `shall` ✔ · schema GT **state-driven** ✔ · schema sistema **unwanted behaviour** ⚠ (difendibile: *"pending closure"* come condizione anomala da risolvere, non solo come stato)

**Esito: `NO_MATCH`** — comportamento asserito diverso, non una riformulazione
dello stesso. GT 10/10, sistema 10/10 con tre riserve.

---

### PR #2732

**Evidenza (estratto)**

```text
Fix issues with read consistency by sending entities into events.
Fix LLM as Judge template to match the JSON schema property name.
```

| | Requisito |
|---|---|
| **Ground Truth** | *When an entity is published through an event, the system shall include the entity in the event.* |
| **Sistema** | *If an entity is created or modified, then the system shall ensure that subsequent reads of that entity return consistent, up-to-date data.* |

**Che cosa ha fatto il sistema.** Un solo tentativo, **accettato**. Il
valutatore registra due relazioni `OVERLAPS` (con #2695 e con #2719,
entrambe sulla stessa base: *"both guarantee that subsequent reads return
consistent, up-to-date data"*) e osserva che il fix del template LLM as
Judge, secondo comportamento della PR, resta fuori e non è un difetto di
questa frase.

**Differenze rispetto al riferimento:** il trigger. *"An entity is created or
modified"* non compare nell'evidenza in nessuna forma — il corpo dice solo
che il fix invia entità negli eventi per risolvere la read consistency,
senza mai dire **quando** questo accade.

**Analisi.**

```text
A differenza di #2719, qui il problema non è uno spostamento dell'obbligo, è
un'aggiunta non fondata: "created or modified" è un'inferenza plausibile su
come un sistema di questo tipo funziona di solito, non un'informazione
enunciata dalla PR. È esattamente il tipo di errore che le regole del
progetto sono scritte per escludere (Decisione 3.1 §9.2) — e qui non è un
nome di libreria dedotto da un file, è una condizione temporale intera
dedotta dalla conoscenza di dominio.

Il valutatore accetta scrivendo che il requisito è formulato "at the general
level the evidence supports" — ma il livello generale che l'evidenza
sostiene è "il sistema deve includere le entità negli eventi", non "ogni
lettura successiva alla creazione o modifica deve essere consistente": sono
due affermazioni di ampiezza diversa, e la seconda eccede quello che il testo
dice.
```

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | **✘** | **✘** | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |

- **Evidence fidelity ✘** — *"created or modified"* non è enunciato.
- **Necessary / supported ✘** — la condizione non è né necessaria né
  giustificata dal testo: è un'inferenza di dominio.

*Forma:* verbo `shall` ✔ · schema GT **event-driven** ✔ · schema sistema **unwanted behaviour** (difendibile in astratto, ma la condizione stessa non è fondata)

**Esito: `NO_MATCH`** — GT 10/10, **sistema 8/10, `NOT_VALID`** (due criteri
obbligatori falliti).

---

### PR #2757

**Evidenza (estratto)**

```text
Fix prompt tags update. Issue was reproducible if user tries to delete
all/latest tag
```

| | Requisito |
|---|---|
| **Ground Truth** | *When a user deletes all or the latest prompt tag, the system shall update the prompt's tags to reflect the deletion.* |
| **Sistema** | *When a user deletes all or the last remaining tag from a prompt, the system shall update the prompt's tags successfully.* |

**Che cosa ha fatto il sistema.** Un solo tentativo, **accettato senza alcun
rilievo**.

**Differenze rispetto al riferimento:** la risposta. Il sistema scrive
*"update…successfully"* dove il nostro GT dice *"update… to reflect the
deletion"*.

**Analisi.**

```text
Sul trigger il sistema converge in modo indipendente sulla stessa sintesi a
cui siamo arrivati in unificazione: un trigger composto ("all or the last
remaining tag") invece di scegliere fra le due condizioni che l'evidenza
enuncia alla pari. Sulla risposta, invece, il sistema riproduce esattamente
la stessa imprecisione che avevamo corretto nella bozza originale di Andrea:
"successfully" non dice qual è lo stato finale osservabile, è vicino alla
formulazione "il sistema deve funzionare correttamente" che i nostri stessi
criteri escludono.
```

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ⚠ | — | ✔ | ✔ | — |

- **Verifiable ⚠** — *"successfully"* non specifica lo stato finale
  osservabile della lista dei tag.

*Forma:* verbo `shall` ✔ · schema GT **event-driven** ✔ · schema sistema **event-driven** ✔

**Esito: `MATCH`** — GT 10/10, sistema 10/10 con una riserva su *Verifiable*.

---

### PR non estraibili

| PR | Ground Truth | Sistema |
|---|---|---|
| #2714 | `NOT_EXTRACTABLE` — "minor fixes" generici su null e validazione | il generatore **si rifiuta di generare**; il valutatore conferma |
| #2715 | `NOT_EXTRACTABLE` — correzione di commenti minori | il generatore **si rifiuta di generare**; il valutatore conferma |

**#2714.** Il generatore dichiara: *"The evidence only mentions unspecified
'minor fixes' and a 'null change'… without describing what problem existed or
what observable behaviour the system now guarantees."* Il valutatore conferma
con la stessa motivazione. Concordanza piena con la nostra lettura.

**#2715.** Stesso schema: *"The evidence only says minor comments from a
previous PR were addressed, without stating what behaviour changed."*
Concordanza piena.

---

## 3. Resoconto

### 3.1 Esiti per Pull Request

| PR | Estraibilità | Tentativi | Corrispondenza | Rubrica GT | Rubrica sistema | Schema EARS |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| #2662 | **discorde** | 1 | n/a | 10/10 | n/a | — |
| #2685 | concorde | 1 | `MATCH` | 10/10 | 10/10 | ✔ |
| #2695 | concorde | 1 | `MATCH` | 10/10 | 10/10 ⚠ | ✔ |
| #2714 | concorde | 1 | — | — | — | — |
| #2715 | concorde | 1 | — | — | — | — |
| #2719 | concorde | 1 | `NO_MATCH` | 10/10 | 10/10 ⚠⚠⚠ | ⚠ |
| #2732 | concorde | 1 | `NO_MATCH` | 10/10 | **8/10 — NOT_VALID** | ⚠ |
| #2757 | concorde | 1 | `MATCH` | 10/10 | 10/10 ⚠ | ✔ |

| Metrica | Valore |
|---|---|
| Accuratezza sulla decisione di estraibilità | **7 / 8** |
| Corrispondenza semantica | **3 `MATCH` · 0 `PARTIAL` · 2 `NO_MATCH`** su 5 confrontabili (#2662 esclusa: nessun requisito del sistema) |
| Punteggio medio di rubrica — Ground Truth | **10,0 / 10** |
| Punteggio medio di rubrica — sistema | **9,6 / 10** (sulle 5 PR con requisito accettato) |
| Schema EARS corretto — sistema | **3 / 5** confermato dalla regola, 2 difendibili ma diversi dal GT |
| Falsi positivi · falsi negativi | **1 · 0** — su #2732 il valutatore accetta un requisito che fallisce l'hard gate esterno |

### 3.2 Il quadro per criterio

| # | Criterio | Rispettato | Dove no |
|---|---|:---:|---|
| 1 | Functional | **5/5** | — *(#2662 esclusa, nessun testo)* |
| 2 | Evidence fidelity | **3/5** | #2732 ✘, riserve su #2695 e #2719 |
| 3 | Necessary / supported | **4/5** | #2732 ✘ |
| 4 | Atomic / singular | **5/5** | — |
| 5 | Unambiguous | **5/5** | — |
| 6 | Clear | **5/5** | — |
| 7 | Complete relative to evidence | **5/5** | *(riserva: #2719)* |
| 8 | Verifiable | **5/5** | *(riserva: #2757)* |
| 9 | Feasible | — | non giudicabile dal solo testo |
| 10 | Consistent | **5/5** | — |
| 11 | Correct abstraction | **5/5** | *(riserva: #2719)* |
| 12 | Traceable | — | garantita dalla pipeline, non dalla frase |

Il Ground Truth rispetta tutti e dieci i criteri giudicabili su tutte e sei
le Pull Request estraibili — coerente con Scrapy, verifica di autoconsistenza
del metro, non un risultato.

### 3.3 Che cosa fa il ciclo di revisione, dai dati

**Zero interventi su otto Pull Request.** Ogni PR è stata decisa al **primo**
tentativo — nessun `REVISE`, in nessun caso. A differenza di Scrapy, dove il
ciclo interveniva su più della metà dei candidati prodotti, qui il valutatore
non ha mai chiesto una seconda stesura.

| PR | Che cosa succede | Esito |
|---|---|---|
| #2662 | il candidato viene **respinto direttamente** (`REJECT`), non rivisto | nessun requisito |
| #2719 | accettato al primo tentativo; l'obbligo centrale è spostato rispetto all'evidenza, il valutatore non lo rileva | difetto non intercettato |
| #2732 | accettato al primo tentativo; il trigger non è fondato, il valutatore lo definisce "al livello generale che l'evidenza sostiene" | difetto non intercettato |

Il ciclo non è quindi assente per scelta di progetto — la configurazione è la
stessa usata su Scrapy, con la stessa soglia di tre tentativi — è
semplicemente **rimasto inerte** in questa esecuzione, e nei due punti in cui
sarebbe servito non si è attivato.

### 3.4 Dove sbaglia

**Un pattern, non tre errori indipendenti.** Confrontando i requisiti del
sistema su #2695, #2719 e #2732 — tre Pull Request diverse, con evidenza
diversa — la stessa struttura ricorre tre volte:

```text
#2695  "…the system shall guarantee that subsequent reads of that thread
        return consistent, up-to-date data reflecting the closure."

#2719  "…so that subsequent reads reflect the thread's correct closed
        state."

#2732  "…the system shall ensure that subsequent reads of that entity
        return consistent, up-to-date data."
```

Il sistema converge sulla stessa formula — *"subsequent reads return
consistent, up-to-date data"* — indipendentemente da quanto l'evidenza di
ciascuna PR sostenga quella formulazione specifica. Su #2695 regge (è quasi
esattamente ciò che il body dice). Su #2719 e #2732 no: sposta l'obbligo
(#2719) o introduce un trigger non enunciato (#2732) pur di far rientrare
l'evidenza nello stesso stampo.

Il meccanismo di relazioni della memoria lo conferma indirettamente: il
valutatore dichiara `OVERLAPS` fra #2719↔#2695 e fra #2732↔#2695 e
#2732↔#2719 — le tre PR vengono effettivamente lette come varianti dello
stesso caso, il che è coerente con quanto sopra: non è un caso isolato, è la
stessa lente applicata tre volte.

### 3.5 Dove non sbaglia quasi mai

**Sulla forma, quasi mai.** Verbo `shall`, atomicità, non ambiguità,
chiarezza: pieno su tutte e cinque le PR con requisito accettato. Nessun
nome di funzione, file o libreria compare in nessun requisito accettato —
`OpenTelemetryMapper`, `extractToJsonColumn`, `Online Scoring subscriber` come
identificatore di codice non compaiono mai, coerente con la regola.

**Sulla natura estraibile/non estraibile, quasi sempre.** Le due PR non
estraibili sono riconosciute con la stessa identica motivazione della nostra
lettura, in entrambi i casi senza bisogno di generare un candidato prima.

**Sull'aggiunta di dettagli grounded, bene.** Su #2685 il sistema aggiunge
*"instead of raising an exception"* — non presente nel nostro GT ma
letteralmente nel body — un'estensione che migliora la fedeltà, non la
peggiora.

### 3.6 Che cosa ne ricaviamo

1. **Il disaccordo su #2662 è il più interessante del campione.** Il
   valutatore del sistema applica alla nostra stessa evidenza un criterio più
   severo di quello che noi (e prima ancora entrambe le annotazioni
   originali) avevamo applicato, e l'argomento — nessun campo o tipo
   nominato, quindi nulla di concreto da verificare — si potrebbe rivolgere
   anche al nostro Ground Truth. Non lo risolviamo qui: lo registriamo come
   un punto su cui il confine dell'estraibilità va rivisto insieme, non
   deciso da una sola lettura.
2. **Il ciclo di revisione qui non ha lavorato, e sui due casi in cui
   sarebbe servito non si è attivato.** A differenza di Scrapy, la messa in
   sicurezza del secondo tentativo non è nemmeno scattata: zero `REVISE` su
   otto Pull Request. Un ciclo che non interviene mai su questo campione non
   è una controprova che non serva — è che qui il valutatore ha accettato al
   primo colpo requisiti che una rubrica esterna boccia.
3. **Il pattern di #2695/#2719/#2732 è un rischio di generalizzazione, non
   un incidente locale.** Convergere su una formula quando funziona (#2695) e
   riadattarla quando l'evidenza dice altro (#2719, #2732) suggerisce che il
   sistema, quando la memoria mostra requisiti tematicamente simili, tende a
   riprodurre la stessa forma invece di ripartire dalla singola evidenza —
   il tipo di deriva che il recupero dalla memoria dovrebbe, in teoria,
   aiutare a evitare (confrontare, non copiare).
4. **Le affermazioni non sostenute non sono più il canale principale
   dell'errore.** Su Scrapy il valutatore intercettava quasi sempre
   affermazioni non sostenute esplicite. Qui, su #2719 e #2732, non c'è
   nessuna `unsupported_claims` registrata: il problema non è un'affermazione
   isolata da rimuovere, è la forma stessa del requisito che si allontana
   dall'evidenza. È un tipo di difetto diverso da quello per cui il prompt di
   valutazione sembra più allenato a cercare.

### 3.7 I limiti di questo confronto

Cinque requisiti confrontabili sono ancora meno dei sei di Scrapy: *3/5* e
*2/5* sono indicazioni, non tassi. Quello che il campione stabilisce con
sicurezza non è **quanto spesso** il sistema produce questo pattern di
convergenza, ma **che esiste** e **che il valutatore, in questa esecuzione,
non l'ha intercettato mai**. Se sia un tratto sistematico del modello o un
effetto della memoria condivisa fra le PR di questo campione specifico
richiede repliche — esattamente il vincolo già registrato nel documento di
Scrapy.

---

## Appendice — L'accordo fra i due annotatori

Si calcola sulle **schede originali**, mai sul Ground Truth.

| | Valore |
|---|---|
| Stessa decisione di estraibilità | **8 / 8** |
| Corrispondenza semantica fra i due requisiti | 3 `MATCH` · 3 `PARTIAL_MATCH` · 0 `NO_MATCH` |

Il dettaglio è in `unificazione-GT_opik.md`, Appendice.
