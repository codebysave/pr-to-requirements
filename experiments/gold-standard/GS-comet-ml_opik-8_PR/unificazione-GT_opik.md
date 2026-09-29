# Unificazione dei requisiti — `comet-ml/opik`, 8 Pull Request

**Progetto:** PR-to-Requirements
**Annotatori:** Andrea Saverino · Marco Saverino Salvatore
**Università degli Studi di Milano-Bicocca** · tutor: Benedetta Donato

**Campione:** `experiments/samples/sample-comet-ml_opik.json` — 8 Pull Request, di cui
**6 estraibili** (#2662, #2685, #2695, #2719, #2732, #2757).
**Regole applicate:** `unificazione_requisiti-GT.md` — documento separato e
unica fonte delle regole: qui non le duplichiamo, per non farle divergere.
**Data dell'unificazione:** 2026-09-29

---

## A che cosa serve questo documento

Abbiamo annotato le stesse otto Pull Request separatamente, ciascuno con la sola
evidenza sotto gli occhi. Le due schede che ne sono uscite sono valide entrambe
ma non coincidono su cinque delle sei Pull Request estraibili.

Qui le unifichiamo in **un unico requisito di riferimento per ogni Pull Request
estraibile**, applicando le regole che ci siamo dati. Il risultato — l'elenco in
fondo — è il **Ground Truth** con cui confronteremo i requisiti prodotti dal
sistema.

---

## Riepilogo degli esiti

| PR | Divergenza | Schema del GT | Esito | Il GT viene da |
|---|---|---|---|---|
| **#2662** | D1 + D2 | ubiquitous | unificato | Marco (contenuto e forma) |
| **#2685** | D1 + D2 | unwanted behaviour | unificato | ri-derivato (contesto di Andrea + precisione di Marco) |
| **#2695** | D1 | event-driven | unificato | ri-derivato |
| **#2714** | D0 | — | `NOT_EXTRACTABLE` | concorde |
| **#2715** | D0 | — | `NOT_EXTRACTABLE` | concorde |
| **#2719** | D1 | state-driven | unificato | Marco (schema e contenuto, confermati dalla regola) |
| **#2732** | D1 | event-driven | unificato | Marco (schema e contenuto, confermati dalla regola) |
| **#2757** | D2 | event-driven | unificato | ri-derivato (ampiezza di Andrea + precisione ri-derivata) |

**Sei Ground Truth su sei estraibili.** Nessuna Pull Request ha richiesto una
rianotazione: a differenza di Scrapy, qui non ci sono casi in cui entrambe le
annotazioni eccedevano l'evidenza allo stesso modo.

---

# Schede compilate

## PR #2662 — `comet-ml-opik-pr-2662` — 2025-07-03

**Evidenza rilevante**

```text
This PR fixes the trace thread object spec, allowing Fern to create the proper
mapping.
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | ubiquitous | ubiquitous |
| Requisito | *The system shall define the correct thread field types in the trace thread object OpenAPI specification.* | *The system shall represent thread fields in the OpenAPI specification using types that allow the API definition generator to create the corresponding field mappings correctly.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☒ D2 ☐ D3

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **ubiquitous** — nessuna condizione, nessun
  divieto: è una proprietà permanente della specifica. Concordi entrambi.
- Identificatore obbligatorio? **No.** Non è un cambio di valore predefinito di
  un'impostazione nominata (§2.2); è una correzione di tipi in una specifica.
  "Fern" non compare nel GT: è lo strumento che *consuma* la specifica, non
  l'oggetto della modifica.

**Passo 3 — Ampiezza**

- Elemento in discussione (E): il legame fra i tipi corretti e **l'esito
  osservabile** — "allowing Fern to create the proper mapping" — presente in
  Marco, assente in Andrea.
- Che cosa ne dice l'evidenza: lo **enuncia esplicitamente**: la PR esiste
  perché quei tipi permettono al generatore di creare il mapping corretto.
- Scelta: ☒ **tenuto**
- Motivazione:

```text
Senza il legame all'esito, "tipi corretti" non è verificabile: corretto
rispetto a cosa? L'evidenza dà la risposta — corretti nel senso che producono
il mapping giusto — e ometterla (Andrea) lascia il requisito senza un modo per
essere testato.
```

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
The system shall define thread fields in the OpenAPI specification using types
that allow the API definition generator to produce the correct field mappings.
```

---

## PR #2685 — `comet-ml-opik-pr-2685` — 2025-07-07

**Evidenza rilevante**

```text
Fixed JSON parsing exception in OpenTelemetryMapper that was causing crashes
when processing OpenTelemetry spans with invalid JSON strings. The issue
occurred when the mapper tried to parse string values that looked like JSON
(starting with ", [, or {) but were actually malformed. […] Modified logic to
store invalid JSON as plain text instead of throwing exceptions.
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | unwanted behaviour | unwanted behaviour |
| Requisito | *If an OpenTelemetry span contains an invalid JSON string, then the system shall store the value as plain text.* | *If a string value that appears to contain JSON cannot be parsed as valid JSON, then the system shall store the value as plain text.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☒ D2 ☐ D3

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **unwanted behaviour** — un input malformato è
  una condizione anomala (§2.1c), e la risposta è il fallback che la
  neutralizza. Concordi entrambi.
- Precisione della condizione: Marco — *«appears to contain JSON… cannot be
  parsed»* — ricalca l'evidenza alla lettera: *«string values that looked like
  JSON… but were actually malformed»*. Andrea — *«contains an invalid JSON
  string»* — è più generico e non cattura il dettaglio "sembra JSON ma non lo
  è". Si tiene la formulazione di Marco.
- Identificatore obbligatorio? **No.**

**Passo 3 — Ampiezza**

- Elemento in discussione (E): **"OpenTelemetry span"** come contenitore del
  valore, presente in Andrea, assente in Marco.
- Che cosa ne dice l'evidenza: lo **enuncia esplicitamente** — *«crashes when
  processing OpenTelemetry spans with invalid JSON strings»*.
- Scelta: ☒ **tenuto**
- Motivazione:

```text
Non è un'inferenza: il body nomina OpenTelemetry span come il contesto esatto
in cui il problema si presenta. Ometterlo (Marco) rende il requisito più
generico di quanto l'evidenza permetta.
```

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
If a value in an OpenTelemetry span appears to contain JSON but cannot be
parsed as valid JSON, then the system shall store the value as plain text.
```

---

## PR #2695 — `comet-ml-opik-pr-2695` — 2025-07-08

**Evidenza rilevante**

```text
Fix small race condition issue with sampling
Fix event publishing logic
Enforce consistent reading after closing threads
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | event-driven | event-driven |
| Requisito | *When closing threads, the system shall enforce consistent reading.* | *When a thread is being closed, the system shall provide a consistent read of the thread after its closure.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☐ D2 ☐ D3

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **event-driven** — concordi entrambi.
- Il trigger va corretto in entrambi i casi: l'evidenza dice *«after closing
  threads»* — la chiusura **avvenuta**, non quella in corso. Andrea (*«When
  closing»*) lascia il momento ambiguo; Marco mescola due tempi nella stessa
  frase (*«is being closed»* + *«after its closure»*), ridondante e
  internamente in tensione.
- Identificatore obbligatorio? **No.**

**Passo 3 — Ampiezza:** non applicabile (nessun D2).

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
When a thread has been closed, the system shall provide a consistent read of
the thread.
```

---

## PR #2719 — `comet-ml-opik-pr-2719` — 2025-07-14

**Evidenza rilevante**

```text
Addressing the read consistency issue by streaming threads pending closure,
closing, and publishing them
Fix the null point caused by the exception without a cause in the Online
Scoring subscriber.
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | event-driven | state-driven |
| Requisito | *When handling threads pending closure, the system shall stream them to address read consistency.* | *While a thread is pending closure, being closed, or being published, the system shall provide a consistent read of the thread.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☐ D2 ☐ D3

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **state-driven**. Test della durata (§2.1b):
  *«pending closure, closing, and publishing»* sono fasi che durano, non un
  singolo istante — *«per quanto tempo il thread è in questi stati?»* è una
  domanda che ha senso. Conferma lo schema già scelto da Marco.
- Contenuto: *"stream"* è il meccanismo, non il comportamento osservabile.
  Removal test: *«Addressing the read consistency issue by [streaming]
  threads…»* — tolto *"streaming"*, il senso regge (*«…issue for threads
  pending closure…»*). Va rimosso, coerentemente con la stessa correzione già
  applicata su #2695.
- Identificatore obbligatorio? **No.**

**Passo 3 — Ampiezza**

Il body descrive **due** comportamenti — la read consistency, e la gestione
dell'eccezione senza causa nell'Online Scoring subscriber. Si tiene solo il
primo: il sistema estrae **un solo requisito per Pull Request** per scelta
architetturale, quindi il Ground Truth deve avere la stessa granularità per
restare confrontabile con quello che il sistema può produrre. Fra i due, si
tiene quello che dà il titolo alla PR e che entrambe le annotazioni avevano
individuato come primario.

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
While a thread is pending closure, being closed, or being published, the
system shall provide a consistent read of the thread.
```

---

## PR #2732 — `comet-ml-opik-pr-2732` — 2025-07-15

**Evidenza rilevante**

```text
Fix issues with read consistency by sending entities into events.
Fix LLM as Judge template to match the JSON schema property name.
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | ubiquitous | event-driven |
| Requisito | *The system shall send entities into events to maintain read consistency.* | *When an entity is published through an event, the system shall include the entity in the event.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☐ D2 ☐ D3

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **event-driven**. Il corollario sui divieti
  (§2.1a) non si applica: non è un `shall not` che vale in ogni istante, è
  un'azione positiva (*"includere l'entità"*), sensata solo nel momento in cui
  un'evento viene pubblicato. Il trigger di Marco non è ridondante — descrive
  un'occasione precisa, non l'oggetto della risposta.
- Formulazione della risposta: Marco descrive l'esito (*"the entity is
  included"*); Andrea aggiunge una clausola di scopo (*"to maintain read
  consistency"*) sopra un verbo d'azione più vicino al meccanismo (*"send…
  into"*). Si tiene la formulazione di Marco: la risposta EARS descrive
  l'effetto, non la ragione per cui serve.
- Identificatore obbligatorio? **No.**

**Passo 3 — Ampiezza**

Stessa situazione di #2719: il body descrive **due** comportamenti (read
consistency via eventi, e il template LLM as Judge). Si tiene solo il primo,
per lo stesso vincolo — un requisito per Pull Request — e per la stessa
ragione: è quello che dà il titolo alla PR ed è quello che entrambe le
annotazioni avevano individuato come primario.

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
When an entity is published through an event, the system shall include the
entity in the event.
```

---

## PR #2757 — `comet-ml-opik-pr-2757` — 2025-07-17

**Evidenza rilevante**

```text
Fix prompt tags update. Issue was reproducible if user tries to delete
all/latest tag
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | event-driven | event-driven |
| Requisito | *When a user deletes all prompt tags, the system shall successfully execute the prompt tags update.* **e** *When a user deletes the latest prompt tag, the system shall successfully execute the prompt tags update.* | *When a user deletes all prompt tags, the system shall update the prompt tags accordingly.* |

**Passo 1 — Tipo di divergenza:** ☒ D2 ☐ D1 puro (concordano su schema, ma non su ampiezza) ☐ D3

**Passo 3 — Ampiezza** *(risolto per primo: determina se serve un trigger composto)*

- Elemento in discussione (E): la condizione **"the latest prompt tag"**,
  presente in Andrea (come secondo requisito parallelo), assente in Marco.
- Che cosa ne dice l'evidenza: la **enuncia esplicitamente**, alla pari della
  prima — *«reproducible if user tries to delete all/latest tag»*.
- Scelta: ☒ **tenuto**
- Motivazione:

```text
"All" e "latest" compaiono nello stesso elenco, con lo stesso peso testuale.
Tenere solo "all" (Marco) lascia fuori metà del bug che la PR dichiara di
correggere.
```

Le due condizioni di Andrea producono però **la stessa risposta** — non sono
due obblighi diversi, sono due trigger per un solo obbligo. Non è quindi un
vero conflitto di atomicità: si uniscono in un trigger composto invece di
sceglierne uno, come previsto quando l'unione non produce due obblighi
distinti.

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **event-driven**, concordi entrambi.
- Risposta: sia *"successfully execute the update"* (Andrea) sia *"update…
  accordingly"* (Marco) non dicono **qual è** lo stato finale osservabile —
  vicino alla trappola "il sistema deve funzionare correttamente". L'evidenza
  descrive il bug come un aggiornamento che non avviene: il requisito deve
  dire che il tag eliminato non compare più nella lista, non solo che
  l'operazione "riesce".

**Passo 4 — Un solo obbligo?** ☒ sì — un solo obbligo, due trigger nella
stessa clausola `When`.

**Requisito unificato (Ground Truth)**

```text
When a user deletes all or the latest prompt tag, the system shall update the
prompt's tags to reflect the deletion.
```

---

# Registro delle scelte (sunto del Passo 3)

| PR | Elemento (E) | Scelta | Motivazione sintetica |
|---|---|---|---|
| #2662 | legame fra tipi e mapping generato correttamente | **tenuto** | enunciato esplicitamente ("allowing Fern to create the proper mapping"); senza, il requisito non è verificabile |
| #2685 | contesto "OpenTelemetry span" | **tenuto** | enunciato esplicitamente, non un'inferenza |
| #2719 | gestione dell'eccezione nell'Online Scoring subscriber | **escluso** | il sistema estrae un solo requisito per PR; si tiene il comportamento primario (dà il titolo alla PR) |
| #2732 | fix del template LLM as Judge | **escluso** | stessa ragione di #2719 |
| #2757 | condizione "latest prompt tag" | **tenuto**, unito in trigger composto | enunciata alla pari di "all", stesso obbligo, non un secondo requisito |

**Come si legge questo registro.** Rispetto a Scrapy cambia il tipo di
scostamento dominante: lì la differenza più frequente era formulazioni
diverse per lo stesso comportamento; qui il pattern ricorrente è **un
comportamento secondario descritto nell'evidenza, escluso non perché non
fondato ma perché il sistema non lo estrarrebbe comunque** (#2719, #2732) — un
vincolo di granularità che il Ground Truth eredita dall'architettura del
sistema, non una scelta di merito sull'evidenza.

---

# Osservazioni dall'unificazione

**1. Nessun caso di Optional feature.** Come già notato da Andrea in fase di
annotazione: nessuna delle otto Pull Request descrive un cambio di valore
predefinito o una configurazione opzionale. Tutti e sei i Ground Truth
estraibili usano ubiquitous, event-driven, state-driven o unwanted behaviour —
coerente con un campione fatto di bug-fix, non di nuove funzionalità
configurabili.

**2. Un requisito per Pull Request, come il sistema.** #2719 e #2732
descrivono entrambi due comportamenti nel proprio corpo; il Ground Truth ne
formalizza uno solo per ciascuna, perché il sistema estrae un solo requisito
per Pull Request per scelta fatta in fase di realizzazione — non potrebbe
restituirne due nemmeno se l'evidenza li sostenesse entrambi. Il Ground Truth
segue la stessa granularità apposta per restare confrontabile: un riferimento
più fine del comportamento che il sistema può effettivamente produrre non
misurerebbe nulla.

**3. Una correzione già fatta prima dell'unificazione è stata confermata,
non ripetuta.** Su #2719, Marco aveva già corretto "stream" nella propria
scheda (confermato da lui direttamente). L'unificazione arriva alla stessa
correzione applicando le regole del Passo 2 all'evidenza — non perché la
scheda di Marco fosse già corretta, ma perché il removal test la richiede
comunque. È la differenza fra correggere dentro l'annotazione individuale
(che cancella l'indipendenza) e correggere qui (che è esattamente il lavoro
per cui questo passo esiste).

---

# Resoconto — il Ground Truth

Sono i requisiti di riferimento che escono dall'unificazione. Da qui in avanti
sono **questi** — non le nostre due schede separate — a fare da metro per i
requisiti prodotti dal sistema.

## Le sei Pull Request estraibili

| PR | Schema EARS | Requisito di riferimento |
|---|---|---|
| **#2662** | ubiquitous | The system shall define thread fields in the OpenAPI specification using types that allow the API definition generator to produce the correct field mappings. |
| **#2685** | unwanted behaviour | If a value in an OpenTelemetry span appears to contain JSON but cannot be parsed as valid JSON, then the system shall store the value as plain text. |
| **#2695** | event-driven | When a thread has been closed, the system shall provide a consistent read of the thread. |
| **#2719** | state-driven | While a thread is pending closure, being closed, or being published, the system shall provide a consistent read of the thread. |
| **#2732** | event-driven | When an entity is published through an event, the system shall include the entity in the event. |
| **#2757** | event-driven | When a user deletes all or the latest prompt tag, the system shall update the prompt's tags to reflect the deletion. |

Distribuzione degli schemi: *event-driven* ×3, *ubiquitous* ×1, *state-driven*
×1, *unwanted behaviour* ×1. Nessuno schema è stato scelto per abitudine: ognuno
esce dalla regola applicata al caso, e la scheda corrispondente dice quale.

## Le due Pull Request non estraibili

| PR | Decisione | Perché |
|---|---|---|
| **#2714** | `NOT_EXTRACTABLE` | "minor fixes" generici su null e validazione, nessun comportamento descritto |
| **#2715** | `NOT_EXTRACTABLE` | correzione di commenti minori lasciati in una PR precedente, nessun comportamento descritto |

## Elenco completo per il confronto

```text
#2662  EXTRACTABLE      The system shall define thread fields in the OpenAPI
                        specification using types that allow the API
                        definition generator to produce the correct field
                        mappings.

#2685  EXTRACTABLE      If a value in an OpenTelemetry span appears to
                        contain JSON but cannot be parsed as valid JSON, then
                        the system shall store the value as plain text.

#2695  EXTRACTABLE      When a thread has been closed, the system shall
                        provide a consistent read of the thread.

#2714  NOT_EXTRACTABLE  —

#2715  NOT_EXTRACTABLE  —

#2719  EXTRACTABLE      While a thread is pending closure, being closed, or
                        being published, the system shall provide a
                        consistent read of the thread.

#2732  EXTRACTABLE      When an entity is published through an event, the
                        system shall include the entity in the event.

#2757  EXTRACTABLE      When a user deletes all or the latest prompt tag, the
                        system shall update the prompt's tags to reflect the
                        deletion.
```

## Che cosa facciamo adesso

Il confronto con l'output del sistema, che è la fase successiva e separata
(Passo 6).

---

## Appendice — L'accordo fra i due annotatori

Si calcola sulle **schede originali**, mai sul Ground Truth: sul Ground Truth
farebbe 100% per costruzione e non dimostrerebbe nulla.

| | Valore |
|---|---|
| Stessa decisione di estraibilità | **8 / 8** |
| Corrispondenza semantica fra i due requisiti | 3 `MATCH` · 3 `PARTIAL_MATCH` · 0 `NO_MATCH` |

**Sugli scostamenti.** Nessuno è un disaccordo sul comportamento in sé — le
due letture concordano sempre su *che cosa* la Pull Request corregge. Tre casi
sono `PARTIAL_MATCH` per **ampiezza asimmetrica**, non per contenuto opposto:
#2662 (Marco lega il requisito all'esito osservabile, Andrea si ferma prima),
#2719 (Andrea non aveva ancora rimosso "stream", Marco sì) e #2757 (Andrea
copre due condizioni, Marco una). In tutti e tre i casi la lettura più
completa era già presente in una delle due annotazioni: l'unificazione ha
scelto, non inventato.
