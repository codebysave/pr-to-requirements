# Confronto annotazioni — Andrea vs Marco vs Sistema

**Campione:** `experiments/samples/sample-scrapy_scrapy.json` — 9 Pull Request di `scrapy/scrapy`, in ordine cronologico.
**Run del sistema:** `experiments/runs/run-20260827T133248Z.json` (2026-08-27).
**Modelli:** generazione `claude-sonnet-5`, valutazione `claude-opus-5`.
**Riferimenti:** Decisione 3.1 (forma e qualità), Decisione 3.7 (piano di valutazione).

Per ogni PR mettiamo a confronto:

1. **Evidenza** — la Pull Request originale, esattamente come è arrivata al sistema.
2. **Confronto** — tabella con la triangolazione delle nostre due annotazioni (Andrea, Marco) e del requisito prodotto dal sistema.
3. **Osservazione** — sintesi della convergenza (o della divergenza) che abbiamo riscontrato.

In coda al documento raccogliamo il resoconto finale con tutte le metriche.

---

## 1. PR #6869

`scrapy-scrapy-pr-6869` — 2025-06-06

### Evidenza

```text
PULL REQUEST TITLE:
Fix: Dangerous Code Execution Function Could Allow External Attacks in scrapy/shell.py

PULL REQUEST BODY:
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic content. If this content can be input from outside the program, this may be a code injection vulnerability. Ensure evaluated content is not definable by external sources.
- **Rule ID:** python.lang.security.audit.eval-detected.eval-detected
- **Severity:** HIGH
- **File:** scrapy/shell.py
- **Lines Affected:** 76 - 76

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/shell.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

### Confronto

| Aspetto        | Andrea                                                                                     | Marco                                                                                                    | Sistema                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Estraibilità   | EXTRACTABLE                                                                                | EXTRACTABLE                                                                                              | ACCEPTED                                                                                             |
| Tentativi      | —                                                                                          | —                                                                                                        | 2                                                                                                    |
| Schema EARS    | ubiquitous                                                                                 | event-driven                                                                                             | ubiquitous                                                                                           |
| Requisito      | *The system shall prevent the execution of arbitrary code originating from untrusted input.* | *When handling content provided by external sources, the system shall not evaluate it as executable code.* | *The system shall not evaluate content originating from outside the program as executable code.*     |
| Corrispondenza | —                                                                                          | —                                                                                                        | **MATCH** con Andrea, **MATCH** con Marco                                                            |

### Osservazione

Convergiamo tutti e tre sul comportamento "non eseguire codice da input non attendibile". Al 1° tentativo il sistema aveva scritto "…when processing shell input", che l'Assessment ha giustamente rifiutato come non supportato dall'evidenza; al 2° tentativo è arrivato a una formulazione ubiquitaria pulita. Andrea e il sistema condividono lo schema ubiquitario, mentre Marco preferisce esplicitare il trigger.

---

## 2. PR #6870

`scrapy-scrapy-pr-6870` — 2025-06-06

### Evidenza

```text
PULL REQUEST TITLE:
Fix: Unsafe Code Loading from User Input Could Execute Malicious Programs in scrapy/commands/genspider.py

PULL REQUEST BODY:
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Untrusted user input in `importlib.import_module()` function allows an attacker to load arbitrary code. Avoid dynamic values in `importlib.import_module()` or use a whitelist to prevent running untrusted code.
- **Rule ID:** python.lang.security.audit.non-literal-import.non-literal-import
- **Severity:** MEDIUM
- **File:** scrapy/commands/genspider.py
- **Lines Affected:** 156 - 156

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/commands/genspider.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

### Confronto

| Aspetto        | Andrea                                                                                          | Marco                                                                                                    | Sistema                                                                                                                          |
| -------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Estraibilità   | EXTRACTABLE                                                                                     | EXTRACTABLE                                                                                              | ACCEPTED                                                                                                                         |
| Tentativi      | —                                                                                               | —                                                                                                        | 1                                                                                                                                |
| Schema EARS    | ubiquitous                                                                                      | event-driven                                                                                             | ubiquitous                                                                                                                       |
| Requisito      | *The system shall prevent the loading of arbitrary code originating from untrusted user input.* | *When loading modules dynamically via user input, the system shall prevent the execution of arbitrary code.* | *The system shall prevent untrusted user input from causing arbitrary code to be loaded and executed during module import.*      |
| Corrispondenza | —                                                                                               | —                                                                                                        | **MATCH** con Andrea, **MATCH** con Marco                                                                                        |

### Osservazione

Convergiamo pienamente sul comportamento (input non attendibile → nessun caricamento/esecuzione di codice arbitrario). Notiamo che il sistema aggiunge il momento "during module import", scelta che riteniamo legittima perché radicata in `importlib.import_module()` citato dall'evidenza.

---

## 3. PR #6875

`scrapy-scrapy-pr-6875` — 2025-06-07

### Evidenza

```text
PULL REQUEST TITLE:
Fix typo in cmdline.py comment: 'a argument' -> 'an argument'

PULL REQUEST BODY:
Description:

This pull request fixes a minor typo in a comment in scrapy/cmdline.py:

Changes "a argument" to "an argument" for correct English usage.

Also improves the comment's clarity by changing "that is" to "that it is" for better English grammar.

No code logic or functionality is affected by this change.



Checklist:

[x] My change is as small as possible and focused on a single issue (typo fix).

[x] No tests are needed as this is a comment-only change.

[x] I have followed the contribution guidelines.
```

### Confronto

| Aspetto        | Andrea          | Marco           | Sistema                       |
| -------------- | --------------- | --------------- | ----------------------------- |
| Estraibilità   | NOT_EXTRACTABLE | NOT_EXTRACTABLE | NOT_EXTRACTABLE               |
| Tentativi      | —               | —               | 1                             |
| Schema EARS    | —               | —               | —                             |
| Requisito      | —               | —               | —                             |
| Corrispondenza | —               | —               | **concorde** con entrambi     |

### Osservazione

Rifiutiamo entrambi la PR e il sistema si comporta come noi, per la stessa ragione: la PR dichiara esplicitamente "No code logic or functionality is affected", quindi non c'è alcun comportamento osservabile black-box da formalizzare.

---

## 4. PR #6879

`scrapy-scrapy-pr-6879` — 2025-06-09

### Evidenza

```text
PULL REQUEST TITLE:
Fix: Unsafe Code Loading from User Input Could Execute Malicious Programs in scrapy/commands/genspider.py

PULL REQUEST BODY:
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Untrusted user input in `importlib.import_module()` function allows an attacker to load arbitrary code. Avoid dynamic values in `importlib.import_module()` or use a whitelist to prevent running untrusted code.
- **Rule ID:** python.lang.security.audit.non-literal-import.non-literal-import
- **Severity:** MEDIUM
- **File:** scrapy/commands/genspider.py
- **Lines Affected:** 156 - 156

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/commands/genspider.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

> **Nota:** l'evidenza è byte per byte identica a quella di **PR #6870**.

### Confronto

| Aspetto        | Andrea                                                                                          | Marco                                                                                                              | Sistema                                                                                                                       |
| -------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Estraibilità   | EXTRACTABLE                                                                                     | EXTRACTABLE                                                                                                        | ACCEPTED                                                                                                                      |
| Tentativi      | —                                                                                               | —                                                                                                                  | 1                                                                                                                             |
| Schema EARS    | ubiquitous                                                                                      | state-driven                                                                                                       | ubiquitous                                                                                                                    |
| Requisito      | *The system shall prevent the loading of arbitrary code originating from untrusted user input.* | *While executing spider generation commands, the system shall restrict user input to prevent the loading of arbitrary code.* | *The system shall prevent user-supplied input from causing arbitrary code to be loaded and executed when generating a spider.* |
| Corrispondenza | —                                                                                               | —                                                                                                                  | **PARTIAL** con Andrea (più restretto), **MATCH** con Marco                                                                     |

### Osservazione

Andrea produce lo **stesso requisito** di #6870 — un overlap che consideriamo legittimo, essendo l'evidenza identica (Decisione 01 §12.3). Marco e il sistema restringono invece lo scope alla "generazione di spider", scelta coerente con `genspider.py`. Notiamo che il sistema, tra #6870 e #6879 con la stessa evidenza, ha scelto due formulazioni diverse (momento "module import" vs "generating a spider") — non ha riconosciuto l'overlap.

---

## 5. PR #6880

`scrapy-scrapy-pr-6880` — 2025-06-09

### Evidenza

```text
PULL REQUEST TITLE:
Fix: Unsafe Data Processing Method Allows Malicious Code Execution in scrapy/exporters.py

PULL REQUEST BODY:
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Avoid using `pickle`, which is known to lead to code execution vulnerabilities. When unpickling, the serialized data could be manipulated to run arbitrary code. Instead, consider serializing the relevant data as JSON or a similar text-based serialization format.
- **Rule ID:** python.lang.security.deserialization.pickle.avoid-pickle
- **Severity:** MEDIUM
- **File:** scrapy/exporters.py
- **Lines Affected:** 303 - 303

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/exporters.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

### Confronto

| Aspetto        | Andrea                                                                                | Marco                                                                                                                        | Sistema                                                                                                                            |
| -------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Estraibilità   | EXTRACTABLE                                                                           | EXTRACTABLE                                                                                                                  | ACCEPTED                                                                                                                           |
| Tentativi      | —                                                                                     | —                                                                                                                            | 2                                                                                                                                  |
| Schema EARS    | ubiquitous                                                                            | event-driven                                                                                                                 | unwanted behaviour                                                                                                                 |
| Requisito      | *The system shall not export data whose loading executes code contained in the data.* | *When reading previously serialized item data, the system shall process the information without triggering the execution of embedded code.* | *If previously serialised item data is read back, then the system shall process it without executing any code contained in that data.* |
| Corrispondenza | —                                                                                     | —                                                                                                                            | **MATCH** con Andrea, **MATCH** con Marco                                                                                          |

### Osservazione

Al 1° tentativo il sistema aveva scritto "…export data without using deserialization methods…", ma l'Assessment lo ha rifiutato per due motivi che condividiamo: (a) è un divieto su una classe di meccanismi, non un comportamento osservabile; (b) il rischio si materializza in **lettura**, non in scrittura. Al 2° tentativo il sistema converge sulla stessa lettura di Marco (guarantee al read-back). Andrea aveva scelto "export" — meno preciso ma comportamentalmente equivalente a ciò che abbiamo formalizzato.

---

## 6. PR #6881

`scrapy-scrapy-pr-6881` — 2025-06-09

### Evidenza

```text
PULL REQUEST TITLE:
Fix: Unsafe XML Processing Library Could Allow Malicious Attacks in scrapy/http/request/rpc.py

PULL REQUEST BODY:
**Context and Purpose:**

This PR automatically remediates a security vulnerability:
- **Description:** Detected use of xmlrpc. xmlrpc is not inherently safe from vulnerabilities. Use defusedxml.xmlrpc instead.
- **Rule ID:** python.lang.security.use-defused-xmlrpc.use-defused-xmlrpc
- **Severity:** MEDIUM
- **File:** scrapy/http/request/rpc.py
- **Lines Affected:** 10 - 10

This change is necessary to protect the application from potential security risks associated with this vulnerability.

**Solution Implemented:**

The automated remediation process has applied the necessary changes to the affected code in `scrapy/http/request/rpc.py` to resolve the identified issue.

Please review the changes to ensure they are correct and integrate as expected.
```

### Confronto

| Aspetto        | Andrea                                                                                | Marco                                                                                                     | Sistema                                                                                                                                             |
| -------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Estraibilità   | EXTRACTABLE                                                                           | EXTRACTABLE                                                                                               | ACCEPTED                                                                                                                                            |
| Tentativi      | —                                                                                     | —                                                                                                         | 2                                                                                                                                                   |
| Schema EARS    | ubiquitous                                                                            | unwanted behaviour                                                                                        | event-driven                                                                                                                                        |
| Requisito      | *The system shall process XML-RPC data without executing arbitrary code contained in the data.* | *If XML-RPC content is received from an untrusted source, then the system shall prevent the resolution of external entities.* | *When processing XML-RPC content received from an untrusted source, the system shall not execute or resolve any external entities or code embedded within that content.* |
| Corrispondenza | —                                                                                     | —                                                                                                         | **MATCH** con Andrea, **PARTIAL** con Marco (più ristretto)                                                                                          |

### Osservazione

Al 1° tentativo il sistema aveva scritto "protect against malicious XML input that could compromise the application", che l'Assessment ha respinto per due motivi che condividiamo ("protect against" è vago e non testabile; il qualificatore "that could compromise" è circolare). Al 2° tentativo il sistema converge su una formulazione osservabile che è un **superset** di entrambe le nostre: copre sia le external entities (Marco) sia l'esecuzione di codice embedded (Andrea).

---

## 7. PR #6899

`scrapy-scrapy-pr-6899` — 2025-06-21

### Evidenza

```text
PULL REQUEST TITLE:
Fix typing of dynamic `request` attribute on `Failure` with a cast subclass

PULL REQUEST BODY:
This PR addresses a longstanding `TODO` in the `call_spider_async` method regarding the typing of the dynamically added `request` attribute on `twisted.python.failure.Failure` objects.



Since `Failure` does not originally define the `request` attribute, adding it dynamically causes static type checkers (e.g., mypy) to raise errors.



To resolve this without changing runtime behavior or introducing new `Failure` instances, this PR introduces a lightweight subclass `FailureWithRequest` used solely for static typing purposes via `cast()`. This approach:



- Provides type safety and clarity for static analysis tools  

- Avoids creating new `Failure` instances, preserving error context and traceback  

- Keeps runtime behavior unchanged  

- Offers a balanced solution (middle ground) between ignoring type checks and a full refactor of `Failure` usage


```

### Confronto

| Aspetto        | Andrea          | Marco           | Sistema                       |
| -------------- | --------------- | --------------- | ----------------------------- |
| Estraibilità   | NOT_EXTRACTABLE | NOT_EXTRACTABLE | NOT_EXTRACTABLE               |
| Tentativi      | —               | —               | 1                             |
| Schema EARS    | —               | —               | —                             |
| Requisito      | —               | —               | —                             |
| Corrispondenza | —               | —               | **concorde** con entrambi     |

### Osservazione

Rifiutiamo entrambi e il sistema converge con noi: la PR preserva esplicitamente il comportamento a runtime ("Keeps runtime behavior unchanged"), quindi un cambio di sola tipizzazione statica non è osservabile black-box.

---

## 8. PR #6936

`scrapy-scrapy-pr-6936` — 2025-07-03

### Evidenza

```text
PULL REQUEST TITLE:
feat(settings): Change default SCHEDULER_PRIORITY_QUEUE (closes #6924)

PULL REQUEST BODY:
## Description

Changes default `SCHEDULER_PRIORITY_QUEUE` to `DownloaderAwarePriorityQueue` (closes #6924).



Depends on #6921 (merged) where the new queue was implemented.



## Changes

- Updated `SCHEDULER_PRIORITY_QUEUE` default in `default_settings.py`

- Updated documentation in `docs/topics/settings.rst`



## Verification

- Ran tests with `pytest`

- Confirmed backward compatibility



## Testing

- Ran priority queue tests (`test_pqueues.py`) - 11 passed, 2 skipped

- Verified with `scrapy bench` (manual testing)
```

### Confronto

| Aspetto        | Andrea                                                                                                                                     | Marco                                                                                                              | Sistema                                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Estraibilità   | EXTRACTABLE                                                                                                                                | EXTRACTABLE                                                                                                        | ACCEPTED                                                                                                                                    |
| Tentativi      | —                                                                                                                                          | —                                                                                                                  | 1                                                                                                                                           |
| Schema EARS    | optional feature                                                                                                                           | unwanted behaviour                                                                                                 | optional feature                                                                                                                            |
| Requisito      | *Where the SCHEDULER_PRIORITY_QUEUE setting has not been overridden, the system shall use DownloaderAwarePriorityQueue as the scheduler priority queue.* | *If the priority queue setting is left to its default, then the system shall schedule requests using a downloader-aware queue.* | *Where the scheduler priority queue setting has not been overridden, the system shall use the downloader-aware priority queue to schedule requests.* |
| Corrispondenza | —                                                                                                                                          | —                                                                                                                  | **MATCH** con Andrea, **MATCH** con Marco                                                                                                   |

### Osservazione

Il contenuto è identico nei tre casi; solo lo schema EARS differisce (Marco preferisce l'unwanted-behaviour come fallback logico, mentre Andrea e il sistema usano Optional feature — tecnicamente più aderente per un "cambio di default"). Andrea usa gli identificatori esatti, il sistema li descrive in prosa.

---

## 9. PR #6947

`scrapy-scrapy-pr-6947` — 2025-07-10

### Evidenza

```text
PULL REQUEST TITLE:
Ban more imports that import twisted.internet.reactor.

PULL REQUEST BODY:
This partially rolls back the import changes in #6941 but not all of these were correct before that PR.
```

### Confronto

| Aspetto        | Andrea          | Marco           | Sistema                                                                                          |
| -------------- | --------------- | --------------- | ------------------------------------------------------------------------------------------------ |
| Estraibilità   | NOT_EXTRACTABLE | NOT_EXTRACTABLE | REJECTED                                                                                         |
| Tentativi      | —               | —               | 1                                                                                                |
| Schema EARS    | —               | —               | —                                                                                                |
| Requisito      | —               | —               | *(candidato rifiutato: "The system shall prevent modules that import the reactor from being imported.")* |
| Corrispondenza | —               | —               | **concorde in outcome** (pratico)                                                                |

### Osservazione

Escludiamo subito entrambi la PR perché il divieto di import è una convenzione della codebase, non un comportamento del sistema. Il sistema supera il gate iniziale (basato solo sulla lunghezza), genera un candidato, e l'Assessment lo rifiuta per le stesse ragioni che ci portano al nostro rifiuto: la convenzione non è un comportamento a runtime. La convergenza sul risultato ("nessun requisito valido") è pratica, ma il sistema spende una call di generazione in più.

---

# Resoconto finale

## Parte A — allineamento fra annotatori umani

| PR      | Andrea          | Marco           | Andrea vs Marco (semantica)          |
| ------- | :-------------: | :-------------: | :----------------------------------: |
| #6869   | EXTRACTABLE     | EXTRACTABLE     | MATCH                                |
| #6870   | EXTRACTABLE     | EXTRACTABLE     | MATCH                                |
| #6875   | NOT_EXTRACTABLE | NOT_EXTRACTABLE | concordi                             |
| #6879   | EXTRACTABLE     | EXTRACTABLE     | MATCH (Andrea più generico)          |
| #6880   | EXTRACTABLE     | EXTRACTABLE     | MATCH                                |
| #6881   | EXTRACTABLE     | EXTRACTABLE     | PARTIAL (Marco più ristretto)        |
| #6899   | NOT_EXTRACTABLE | NOT_EXTRACTABLE | concordi                             |
| #6936   | EXTRACTABLE     | EXTRACTABLE     | MATCH (diverso schema EARS)          |
| #6947   | NOT_EXTRACTABLE | NOT_EXTRACTABLE | concordi                             |

**Preferenze di schema EARS.** Andrea privilegia lo schema *ubiquitous* per le proprietà di sicurezza (l'assenza di codice non fidato è una proprietà sempre-vera, non una reazione a un evento). Marco preferisce esplicitare il trigger con *event-driven* o *state-driven*. Riteniamo che entrambe le scelte siano valide per Decisione 3.1: la differenza è stilistica e non incide sull'osservabile.

## Parte B — sistema vs gold standard

| PR      | Esito sistema      | Tentativi | vs Andrea | vs Marco | Qualità |
| ------- | :----------------: | :-------: | :-------: | :------: | :-----: |
| #6869   | ACCEPTED           |     2     |   MATCH   |  MATCH   |  12/12  |
| #6870   | ACCEPTED           |     1     |   MATCH   |  MATCH   |  12/12  |
| #6875   | NOT_EXTRACTABLE    |     1     | concorde  | concorde |   n/a   |
| #6879   | ACCEPTED           |     1     |  PARTIAL  |  MATCH   |  12/12  |
| #6880   | ACCEPTED           |     2     |   MATCH   |  MATCH   |  12/12  |
| #6881   | ACCEPTED           |     2     |   MATCH   | PARTIAL  |  12/12  |
| #6899   | NOT_EXTRACTABLE    |     1     | concorde  | concorde |   n/a   |
| #6936   | ACCEPTED           |     1     |   MATCH   |  MATCH   |  12/12  |
| #6947   | REJECTED           |     1     | concorde  | concorde |   n/a   |

## Metriche complessive (Decisione 3.7, §12)

| Metrica                                            | Valore                                  |
| -------------------------------------------------- | --------------------------------------- |
| Valid Requirement Rate                             | **6 / 7 = 85,7 %**                      |
| Unsupported Claim Rate                             | **2 / 12 ≈ 16,7 %**                     |
| Estraibilità — accuratezza in outcome              | **9 / 9**                               |
| Quality score medio (sui 6 requisiti accettati)    | **12 / 12**                             |
| Corrispondenza semantica sistema vs Andrea         | 5 MATCH · 1 PARTIAL · 0 NO_MATCH        |
| Corrispondenza semantica sistema vs Marco          | 5 MATCH · 1 PARTIAL · 0 NO_MATCH        |

> - *Valid Requirement Rate*: requisiti validi / candidati generati. #6947 ha generato un candidato poi rifiutato dall'Assessment.
> - *Unsupported Claim Rate*: iterazioni con almeno un claim non supportato — #6869 attempt 1 (condizione non supportata) e #6947 attempt 1 (tre claim non supportati) — su 12 iterazioni totali di assessment.
> - *Accuratezza in outcome*: in ogni PR il sistema arriva allo stesso esito finale che ci trova d'accordo (requisito valido oppure nessun requisito).

## Osservazioni qualitative

1. **Convergenza sull'outcome.** Sui 9 PR, il sistema arriva sempre allo stesso esito finale a cui arriviamo noi due — o un requisito valido, o nessuno. Non abbiamo osservato falsi positivi (requisito generato dove non c'era comportamento osservabile) né falsi negativi (rifiuto dove il comportamento c'era).
2. **Il caso #6947.** Unico "quasi-disaccordo": il gate iniziale di estraibilità (basato sulla sola lunghezza del testo) lascia passare il PR; poi l'Assessment converge sul rifiuto per le stesse ragioni che ci hanno guidato. Riteniamo che un'euristica di estraibilità più fine risparmierebbe una call di generazione.
3. **L'Assessment come rete di sicurezza.** Su 3 delle 6 PR accettate (#6869, #6880, #6881) il 1° tentativo del generatore ha prodotto un candidato con problemi (claim non supportati, formulazioni non osservabili, qualificatori circolari) — l'Assessment li ha rifiutati e il generatore ha corretto al 2° tentativo. A nostro giudizio la pipeline funziona come progettata (Decisione 3.5 sul revise-loop).
4. **Divergenze di stile fra noi.** Andrea preferisce lo schema *ubiquitous* per la sicurezza; Marco predilige gli schemi condizionati (event/state/unwanted). Il sistema alterna in base al contesto — coerente con l'insieme delle nostre due scelte, senza uno schema dominante. Su #6881 il sistema produce la formulazione più completa dei tre (superset di entrambe le nostre).
5. **L'unico PARTIAL vs Marco (PR #6881).** Marco copre solo le external entities; Andrea e il sistema estendono anche all'esecuzione di codice embedded. Riteniamo che entrambe le letture siano ancorate nell'evidenza (la classe di vulnerabilità XML-RPC/XXE): la differenza è di ampiezza dello scope, non di correttezza.
