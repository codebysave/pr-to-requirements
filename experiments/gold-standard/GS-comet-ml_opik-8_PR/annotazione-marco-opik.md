# Scheda di annotazione — Gold standard

**Annotatore:** Marco

Campione: `experiments/samples/sample-comet-ml_opik.json` — 8 Pull Request di `comet-ml/opik`,
in ordine cronologico. Riferimenti: Decisione 3.1 (forma e qualità), Decisione 3.7
(piano di valutazione).


## Forma del requisito (Decisione 3.1)

Inglese, `shall`, un solo obbligo, e uno dei cinque schemi EARS:

- **Ubiquitous** — `The system shall <response>.`
- **Event-driven** — `When <trigger>, the system shall <response>.`
- **State-driven** — `While <state>, the system shall <response>.`
- **Unwanted behaviour** — `If <undesired condition>, then the system shall <response>.`
- **Optional feature** — `Where <feature is present>, the system shall <response>.`

Nessun elemento che l'evidenza non sostenga: niente canali, tempi, formati o tecnologie
che la Pull Request non nomina. Nessun nome di libreria, funzione o modulo, salvo quando
il cambio di quel meccanismo è esso stesso l'oggetto della Pull Request.

---

# 1. PR #2662

`comet-ml-opik-pr-2662` — 2025-07-03

## Evidenza

```text
PULL REQUEST TITLE:
NA: Fix thread fields types on OpenAPI spec

PULL REQUEST BODY:
## Details
- This PR fixes the trace thread object spec, allowing Fern to create the proper mapping.
```

## La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
The system shall represent thread fields in the OpenAPI specification using types that allow the API definition generator to create the corresponding field mappings correctly.
```

**Schema EARS usato:** [X] ubiquitous ☐ event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
La PR corregge esplicitamente la specifica del thread per il mapping di Fern; il requisito descrive solo il comportamento dichiarato, senza dettagli su tipi o mapping non documentati.
```

---

# 2. PR #2685

`comet-ml-opik-pr-2685` — 2025-07-07

## Evidenza

```text
PULL REQUEST TITLE:
OPIK-1964: Fix JSON parsing exception in OpenTelemetryMapper

PULL REQUEST BODY:
- Add exception handling for invalid JSON strings in extractToJsonColumn method
- Add exception handling for invalid JSON strings in extractUsageField method
- Store invalid JSON as plain text instead of throwing exceptions
- Add comprehensive unit tests for JSON parsing scenarios
- Make extractToJsonColumn method package-private for testing

## Details

Fixed JSON parsing exception in OpenTelemetryMapper that was causing crashes when processing OpenTelemetry spans with invalid JSON strings. The issue occurred when the mapper tried to parse string values that looked like JSON (starting with `"`, `[`, or `{`) but were actually malformed (e.g., "Analyze this text").

### Changes Made:
- Added exception handling around JSON parsing in `extractToJsonColumn` method
- Added exception handling around JSON parsing in `extractUsageField` method
- Modified logic to store invalid JSON as plain text instead of throwing exceptions
- Added comprehensive unit tests covering various JSON parsing scenarios
- Made `extractToJsonColumn` method package-private to enable unit testing

### Technical Implementation:
- Wrapped `JsonUtils.getJsonNodeFromString()` calls in try-catch blocks
- Added debug logging for failed parsing attempts
- Implemented graceful fallback to store values as plain text
- Maintained backward compatibility for valid JSON parsing

## Issues

Resolves OPIK-1964

## Testing

- Created comprehensive unit tests (`OpenTelemetryMapperTest`) with 9 test cases
- Verified invalid JSON strings are handled gracefully without exceptions
- Confirmed valid JSON is still parsed correctly
- Ran existing integration tests (`OpenTelemetryResourceTest`) - all passing
- Tested edge cases: strings that look like JSON but are invalid, plain text, various data types

### Test Coverage:
- Valid JSON string parsing
- Invalid JSON string handling (e.g., "Analyze this text")
- Plain text string handling
- Integer, double, boolean, and array value processing
- Nested JSON parsing scenarios

## Documentation

- Added debug logging to track JSON parsing failures
- Updated method visibility for testing purposes
- Code comments explain the fallback behavior for invalid JSON
```

## La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
If a string value that appears to contain JSON cannot be parsed as valid JSON, then the system shall store the value as plain text.
```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven ☐ state-driven [X] unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Problema e comportamento voluto sono entrambi espliciti: le stringhe che sembrano JSON ma non lo sono non devono generare eccezioni e vanno conservate come testo — è la gestione di una condizione indesiderata.
```

---

# 3. PR #2695

`comet-ml-opik-pr-2695` — 2025-07-08

## Evidenza

```text
PULL REQUEST TITLE:
OPIK-1775 Fix issue with race condition and enforce consistent read when closing threads

PULL REQUEST BODY:
## Details
- Fix small race condition issue with sampling
- Fix event publishing logic
- Enforce consistent reading after closing threads
```

## La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
When a thread is being closed, the system shall provide a consistent read of the thread after its closure.
```

**Schema EARS usato:** ☐ ubiquitous [X] event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
La PR dichiara due comportamenti: una race condition (dettaglio tecnico) e la lettura consistente dopo la chiusura del thread — solo quest'ultima è il comportamento osservabile sufficientemente supportato.
```

---

# 4. PR #2714

`comet-ml-opik-pr-2714` — 2025-07-13

## Evidenza

```text
PULL REQUEST TITLE:
[OPIK-2043] Follow-up fixes

PULL REQUEST BODY:
## Details
This PR contains a couple of minor fixes from a previous PR #2449.

## Issues
OPIK-2043

## Testing
Extended a test to cover the `null` change, the validation changes was already covered.
```

## La mia annotazione

**Estraibilità**

- [ ] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [X] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text

```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Il body parla genericamente di "minor fixes" su null e validazione, senza descrivere alcun comportamento funzionale: formulare un requisito richiederebbe inferenze non supportate.
```

---

# 5. PR #2715

`comet-ml-opik-pr-2715` — 2025-07-13

## Evidenza

```text
PULL REQUEST TITLE:
[NA] fix minor comments from PR #2689

PULL REQUEST BODY:
## Details
This PR has fixes for some minor comments that were left in #2689
```

## La mia annotazione

**Estraibilità**

- [ ] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [X] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text

```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Il body indica solo la correzione di commenti minori lasciati in una PR precedente, senza descrivere alcun comportamento richiesto al sistema.
```

---

# 6. PR #2719

`comet-ml-opik-pr-2719` — 2025-07-14

## Evidenza

```text
PULL REQUEST TITLE:
OPIK-1778: Fix read consistency issues

PULL REQUEST BODY:
## Details

- Addressing the read consistency issue by streaming threads pending closure, closing, and publishing them
-  Fix the null point caused by the exception without a cause in the Online Scoring subscriber.
```

## La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
While a thread is pending closure, being closed, or being published, the system shall provide a consistent read of the thread.
```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven [X] state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
"Streaming" nel body è il meccanismo con cui è stata risolta la read consistency, non il comportamento osservabile: rimosso applicando il removal test. Corretto per coerenza con #2695, che sullo stesso tema usa correttamente "provide a consistent read" senza nominare l'implementazione.
```

---

# 7. PR #2732

`comet-ml-opik-pr-2732` — 2025-07-15

## Evidenza

```text
PULL REQUEST TITLE:
OPIK-1778: Fix issues with read consistency by send entities into events

PULL REQUEST BODY:
## Details
- Fix issues with read consistency by sending entities into events.
- Fix LLM as Judge template to match the JSON schema property name.
```

## La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
When an entity is published through an event, the system shall include the entity in the event.
```

**Schema EARS usato:** ☐ ubiquitous [X] event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Il body indica esplicitamente il comportamento: le entità devono essere incluse negli eventi per risolvere la read consistency — verificabile ed esprimibile come risposta alla pubblicazione dell'evento.
```

---

# 8. PR #2757

`comet-ml-opik-pr-2757` — 2025-07-17

## Evidenza

```text
PULL REQUEST TITLE:
[NA] Fix prompt tags update

PULL REQUEST BODY:
## Details
Fix prompt tags update. Issue was reproducible if user tries to delete all/latest tag

## Testing
Integration tests
```

## La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
When a user deletes all prompt tags, the system shall update the prompt tags accordingly.
```

**Schema EARS usato:** ☐ ubiquitous [X] event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Il body indica chiaramente la condizione: l'eliminazione di tutti i tag di un prompt non aggiorna correttamente — il requisito descrive il comportamento atteso in quel caso.
```

---

# Riepilogo — il mio riferimento

| PR    | Estraibile | Requisito di riferimento (prime parole) |
|-------|:----------:|-----------------------------------------|
| #2662 | X          | The system shall represent thread fields…       |
| #2685 | X          | If a string value that appears to contain JSON… |
| #2695 | X          | When a thread is being closed…                  |
| #2714 | —          | *(NOT_EXTRACTABLE — solo "minor fixes" generici, nessun comportamento descritto)* |
| #2715 | —          | *(NOT_EXTRACTABLE — solo correzione di commenti minori)* |
| #2719 | X          | While a thread is pending closure…              |
| #2732 | X          | When an entity is published through an event…   |
| #2757 | X          | When a user deletes all prompt tags…             |
