# Scheda di annotazione — Gold standard

**Annotatore: Marco**

Campione: `experiments/samples/sample-scrapy_scrapy.json` — 9 Pull Request di `scrapy/scrapy`,
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

# 1. PR #6869

`scrapy-scrapy-pr-6869` — 2025-06-06

## Evidenza

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

## Parte A — La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
When handling content provided by external sources, the system shall not evaluate it as executable code.
```

**Schema EARS usato:** ☐ ubiquitous [X] event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Ho rimosso il riferimento alla funzione specifica (`eval()`) per concentrarmi sull'obiettivo funzionale: impedire l'esecuzione di contenuti dinamici di origine esterna.
```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | `experiments/runs/run-20260827T133248Z.json` |
| Modello generazione / valutazione | `claude-sonnet-5` / `claude-opus-5` |
| Esito del sistema | `ACCEPTED` |
| Tentativi | 2 |

**Requisito generato**

```text
The system shall not evaluate content originating from outside the program as executable code.
```

**1. Estraibilità** — il sistema ha deciso come me?

- [X] concorde
- [ ] discorde — il sistema dice: ______________

**2. Corrispondenza semantica con il mio requisito**

- [X] `MATCH` — stesso comportamento, anche se formulato diversamente
- [ ] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | X | ☐ | descrive un comportamento osservabile del sistema |
| Evidence fidelity | **sì** | X | ☐ | radicato nella vulnerabilità "contenuto esterno valutato come codice" |
| Necessary / supported | **sì** | X | ☐ | pienamente supportato dal corpo della PR |
| Atomic / singular | **sì** | X | ☐ | un solo obbligo |
| Unambiguous | **sì** | X | ☐ | lettura unica |
| Verifiable | **sì** | X | ☐ | testabile black-box |
| Clear | no | X | ☐ | |
| Complete relative to evidence | no | X | ☐ | |
| Feasible | no | X | ☐ | |
| Consistent | no | X | ☐ | |
| Correct abstraction | no | X | ☐ | nessun riferimento a eval() o scrapy/shell.py |
| Traceable | no | X | ☐ | |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [X] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

**5. Quality score** — criteri superati sul totale: **12** / 12

**Note della valutazione**

```text
Il sistema usa lo schema ubiquitario mentre io ho scelto event-driven ("When…"): il contenuto è equivalente e non c'è motivo dall'evidenza per privilegiare l'uno o l'altro.
```

---

# 2. PR #6870

`scrapy-scrapy-pr-6870` — 2025-06-06

## Evidenza

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

## Parte A — La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
When loading modules dynamically via user input, the system shall prevent the execution of arbitrary code.
```

**Schema EARS usato:** ☐ ubiquitous [X] event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
L'enfasi è spostata dalla soluzione tecnica (evitare `importlib.import_module()` con valori dinamici o usare whitelist) al comportamento garantito dall'esterno: il caricamento dinamico non deve mai innescare codice non fidato.
```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | `experiments/runs/run-20260827T133248Z.json` |
| Modello generazione / valutazione | `claude-sonnet-5` / `claude-opus-5` |
| Esito del sistema | `ACCEPTED` |
| Tentativi | 1 |

**Requisito generato**

```text
The system shall prevent untrusted user input from causing arbitrary code to be loaded and executed during module import.
```

**1. Estraibilità** — il sistema ha deciso come me?

- [X] concorde
- [ ] discorde — il sistema dice: ______________

**2. Corrispondenza semantica con il mio requisito**

- [X] `MATCH` — stesso comportamento, anche se formulato diversamente
- [ ] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | X | ☐ | descrive un comportamento del sistema |
| Evidence fidelity | **sì** | X | ☐ | "module import" è radicato nel contesto `importlib.import_module()` |
| Necessary / supported | **sì** | X | ☐ | direttamente supportato |
| Atomic / singular | **sì** | X | ☐ | un solo obbligo |
| Unambiguous | **sì** | X | ☐ | lettura unica |
| Verifiable | **sì** | X | ☐ | testabile black-box |
| Clear | no | X | ☐ | |
| Complete relative to evidence | no | X | ☐ | |
| Feasible | no | X | ☐ | |
| Consistent | no | X | ☐ | |
| Correct abstraction | no | X | ☐ | evita di nominare l'alternativa "whitelist" |
| Traceable | no | X | ☐ | |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [X] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

**5. Quality score** — criteri superati sul totale: **12** / 12

**Note della valutazione**

```text
Il sistema copre "loading AND execution" mentre io mi sono concentrato sull'esecuzione: contenuto equivalente, il sistema è leggermente più esplicito ma senza aggiungere elementi non supportati.
```

---

# 3. PR #6875

`scrapy-scrapy-pr-6875` — 2025-06-07

## Evidenza

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

## Parte A — La mia annotazione

**Estraibilità**

- [ ] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [X] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text

```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Si tratta esclusivamente della correzione di un refuso grammaticale all'interno di un commento. Come evidenziato dal sistema, nessuna logica o funzionalità del codice viene alterata, per cui non c'è alcun comportamento osservabile a runtime.
```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | `experiments/runs/run-20260827T133248Z.json` |
| Modello generazione / valutazione | `claude-sonnet-5` / `claude-opus-5` |
| Esito del sistema | `NOT_EXTRACTABLE` |
| Tentativi | 1 |

**Requisito generato**

```text
(nessuno — il sistema si è rifiutato per stessa ragione)
```

**1. Estraibilità** — il sistema ha deciso come me?

- [X] concorde
- [ ] discorde — il sistema dice: ______________

**2. Corrispondenza semantica con il mio requisito**

- [ ] `MATCH` — stesso comportamento, anche se formulato diversamente
- [ ] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

*(non applicabile: nessun requisito da confrontare)*

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

*(non applicabile: nessun requisito generato)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | ☐ | ☐ | n/a |
| Evidence fidelity | **sì** | ☐ | ☐ | n/a |
| Necessary / supported | **sì** | ☐ | ☐ | n/a |
| Atomic / singular | **sì** | ☐ | ☐ | n/a |
| Unambiguous | **sì** | ☐ | ☐ | n/a |
| Verifiable | **sì** | ☐ | ☐ | n/a |
| Clear | no | ☐ | ☐ | n/a |
| Complete relative to evidence | no | ☐ | ☐ | n/a |
| Feasible | no | ☐ | ☐ | n/a |
| Consistent | no | ☐ | ☐ | n/a |
| Correct abstraction | no | ☐ | ☐ | n/a |
| Traceable | no | ☐ | ☐ | n/a |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [ ] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

*(non applicabile)*

**5. Quality score** — criteri superati sul totale: **n/a** / 12

**Note della valutazione**

```text
Entrambi rifiutano per la stessa ragione: la PR dichiara esplicitamente che nessuna logica o funzionalità è alterata, quindi non c'è comportamento osservabile da formalizzare.
```

---

# 4. PR #6879

`scrapy-scrapy-pr-6879` — 2025-06-09

## Evidenza

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

## Parte A — La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
While executing spider generation commands, the system shall restrict user input to prevent the loading of arbitrary code.
```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven [X] state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Simile alla PR #6870, ma qui ho usato uno schema State-driven ("While...") per contestualizzare la restrizione di sicurezza all'operazione specifica dedotta dall'evidenza (la generazione di spider).
```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | `experiments/runs/run-20260827T133248Z.json` |
| Modello generazione / valutazione | `claude-sonnet-5` / `claude-opus-5` |
| Esito del sistema | `ACCEPTED` |
| Tentativi | 1 |

**Requisito generato**

```text
The system shall prevent user-supplied input from causing arbitrary code to be loaded and executed when generating a spider.
```

**1. Estraibilità** — il sistema ha deciso come me?

- [X] concorde
- [ ] discorde — il sistema dice: ______________

**2. Corrispondenza semantica con il mio requisito**

- [X] `MATCH` — stesso comportamento, anche se formulato diversamente
- [ ] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | X | ☐ | descrive un comportamento del sistema |
| Evidence fidelity | **sì** | X | ☐ | "generating a spider" corrisponde a `genspider` nel path del file |
| Necessary / supported | **sì** | X | ☐ | supportato |
| Atomic / singular | **sì** | X | ☐ | un solo obbligo |
| Unambiguous | **sì** | X | ☐ | lettura unica |
| Verifiable | **sì** | X | ☐ | testabile black-box |
| Clear | no | X | ☐ | |
| Complete relative to evidence | no | X | ☐ | |
| Feasible | no | X | ☐ | |
| Consistent | no | X | ☐ | |
| Correct abstraction | no | X | ☐ | nessun riferimento a `importlib.import_module` |
| Traceable | no | X | ☐ | |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [X] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

**5. Quality score** — criteri superati sul totale: **12** / 12

**Note della valutazione**

```text
Entrambi ancorati alla generazione di spider (io con "While", il sistema con "when generating a spider"): stesso comportamento espresso in schemi EARS diversi.
```

---

# 5. PR #6880

`scrapy-scrapy-pr-6880` — 2025-06-09

## Evidenza

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

## Parte A — La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
When reading previously serialized item data, the system shall process the information without triggering the execution of embedded code.
```

**Schema EARS usato:** ☐ ubiquitous [X] event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Seguendo la logica del sistema, invece di imporre un formato di serializzazione come JSON (o vietare `pickle`), il requisito esplicita la garanzia fondamentale di sicurezza al momento della lettura (deserializzazione) dei dati.
```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | `experiments/runs/run-20260827T133248Z.json` |
| Modello generazione / valutazione | `claude-sonnet-5` / `claude-opus-5` |
| Esito del sistema | `ACCEPTED` |
| Tentativi | 2 |

**Requisito generato**

```text
If previously serialised item data is read back, then the system shall process it without executing any code contained in that data.
```

**1. Estraibilità** — il sistema ha deciso come me?

- [X] concorde
- [ ] discorde — il sistema dice: ______________

**2. Corrispondenza semantica con il mio requisito**

- [X] `MATCH` — stesso comportamento, anche se formulato diversamente
- [ ] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | X | ☐ | comportamento osservabile al momento del read-back |
| Evidence fidelity | **sì** | X | ☐ | coerente con la vulnerabilità di deserializzazione |
| Necessary / supported | **sì** | X | ☐ | supportato dall'evidenza |
| Atomic / singular | **sì** | X | ☐ | un solo obbligo |
| Unambiguous | **sì** | X | ☐ | lettura unica |
| Verifiable | **sì** | X | ☐ | testabile black-box |
| Clear | no | X | ☐ | |
| Complete relative to evidence | no | X | ☐ | |
| Feasible | no | X | ☐ | |
| Consistent | no | X | ☐ | |
| Correct abstraction | no | X | ☐ | nessun riferimento a pickle o JSON |
| Traceable | no | X | ☐ | |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [X] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

**5. Quality score** — criteri superati sul totale: **12** / 12

**Note della valutazione**

```text
Praticamente identico al mio (io "When…", sistema "If… then…"): entrambi ancorano la garanzia al momento della lettura dei dati serializzati.
```

---

# 6. PR #6881

`scrapy-scrapy-pr-6881` — 2025-06-09

## Evidenza

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

## Parte A — La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
If XML-RPC content is received from an untrusted source, then the system shall prevent the resolution of external entities.
```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven ☐ state-driven [X] unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Non si nomina più il modulo `defusedxml.xmlrpc`. Il requisito definisce l'effetto osservabile di quella libreria: se arriva contenuto XML potenzialmente insicuro, le entità esterne non devono essere risolte.
```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | `experiments/runs/run-20260827T133248Z.json` |
| Modello generazione / valutazione | `claude-sonnet-5` / `claude-opus-5` |
| Esito del sistema | `ACCEPTED` |
| Tentativi | 2 |

**Requisito generato**

```text
When processing XML-RPC content received from an untrusted source, the system shall not execute or resolve any external entities or code embedded within that content.
```

**1. Estraibilità** — il sistema ha deciso come me?

- [X] concorde
- [ ] discorde — il sistema dice: ______________

**2. Corrispondenza semantica con il mio requisito**

- [ ] `MATCH` — stesso comportamento, anche se formulato diversamente
- [X] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | X | ☐ | descrive un comportamento osservabile di processing |
| Evidence fidelity | **sì** | X | ☐ | XXE/code-execution rientrano nella classe di vulnerabilità XML-RPC citata |
| Necessary / supported | **sì** | X | ☐ | supportato |
| Atomic / singular | **sì** | X | ☐ | un solo divieto, due forme enumerate della stessa classe |
| Unambiguous | **sì** | X | ☐ | lettura unica |
| Verifiable | **sì** | X | ☐ | testabile black-box |
| Clear | no | X | ☐ | |
| Complete relative to evidence | no | X | ☐ | |
| Feasible | no | X | ☐ | |
| Consistent | no | X | ☐ | |
| Correct abstraction | no | X | ☐ | nessun riferimento a defusedxml |
| Traceable | no | X | ☐ | |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [X] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

**5. Quality score** — criteri superati sul totale: **12** / 12

**Note della valutazione**

```text
Il mio requisito copre solo la risoluzione delle entità esterne; il sistema aggiunge anche l'esecuzione di codice embedded — il suo è un superset del mio (PARTIAL_MATCH: il mio è più ristretto).
```

---

# 7. PR #6899

`scrapy-scrapy-pr-6899` — 2025-06-21

## Evidenza

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

## Parte A — La mia annotazione

**Estraibilità**

- [ ] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [X] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text

```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
L'evidenza stessa dichiara esplicitamente che il comportamento a runtime rimane invariato. La modifica introduce solo una sottoclasse per aggirare avvisi dei sistemi di analisi statica dei tipi, pertanto fallisce il test funzionale "black-box".
```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | `experiments/runs/run-20260827T133248Z.json` |
| Modello generazione / valutazione | `claude-sonnet-5` / `claude-opus-5` |
| Esito del sistema | `NOT_EXTRACTABLE` |
| Tentativi | 1 |

**Requisito generato**

```text
(nessuno — il sistema si è rifiutato per stessa ragione)
```

**1. Estraibilità** — il sistema ha deciso come me?

- [X] concorde
- [ ] discorde — il sistema dice: ______________

**2. Corrispondenza semantica con il mio requisito**

- [ ] `MATCH` — stesso comportamento, anche se formulato diversamente
- [ ] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

*(non applicabile: nessun requisito da confrontare)*

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

*(non applicabile: nessun requisito generato)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | ☐ | ☐ | n/a |
| Evidence fidelity | **sì** | ☐ | ☐ | n/a |
| Necessary / supported | **sì** | ☐ | ☐ | n/a |
| Atomic / singular | **sì** | ☐ | ☐ | n/a |
| Unambiguous | **sì** | ☐ | ☐ | n/a |
| Verifiable | **sì** | ☐ | ☐ | n/a |
| Clear | no | ☐ | ☐ | n/a |
| Complete relative to evidence | no | ☐ | ☐ | n/a |
| Feasible | no | ☐ | ☐ | n/a |
| Consistent | no | ☐ | ☐ | n/a |
| Correct abstraction | no | ☐ | ☐ | n/a |
| Traceable | no | ☐ | ☐ | n/a |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [ ] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

*(non applicabile)*

**5. Quality score** — criteri superati sul totale: **n/a** / 12

**Note della valutazione**

```text
Entrambi rifiutano per la stessa ragione: la PR preserva esplicitamente il comportamento a runtime, quindi una modifica di solo tipo statico fallisce il test di osservabilità black-box.
```

---

# 8. PR #6936

`scrapy-scrapy-pr-6936` — 2025-07-03

## Evidenza

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

## Parte A — La mia annotazione

**Estraibilità**

- [X] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text
If the priority queue setting is left to its default, then the system shall schedule requests using a downloader-aware queue.
```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven ☐ state-driven [X] unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
(Tecnicamente un costrutto Unwanted behaviour viene usato anche per fallback logici). Trasforma la modifica a una variabile di codice (`SCHEDULER_PRIORITY_QUEUE`) in una regola di business chiara che descrive come il sistema gestisce la priorità di default.
```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | `experiments/runs/run-20260827T133248Z.json` |
| Modello generazione / valutazione | `claude-sonnet-5` / `claude-opus-5` |
| Esito del sistema | `ACCEPTED` |
| Tentativi | 1 |

**Requisito generato**

```text
Where the scheduler priority queue setting has not been overridden, the system shall use the downloader-aware priority queue to schedule requests.
```

**1. Estraibilità** — il sistema ha deciso come me?

- [X] concorde
- [ ] discorde — il sistema dice: ______________

**2. Corrispondenza semantica con il mio requisito**

- [X] `MATCH` — stesso comportamento, anche se formulato diversamente
- [ ] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | X | ☐ | descrive un comportamento del sistema (scelta della coda di default) |
| Evidence fidelity | **sì** | X | ☐ | direttamente radicato nel cambio di default |
| Necessary / supported | **sì** | X | ☐ | supportato |
| Atomic / singular | **sì** | X | ☐ | un solo obbligo |
| Unambiguous | **sì** | X | ☐ | lettura unica |
| Verifiable | **sì** | X | ☐ | testabile black-box tramite il comportamento osservato della coda |
| Clear | no | X | ☐ | |
| Complete relative to evidence | no | X | ☐ | |
| Feasible | no | X | ☐ | |
| Consistent | no | X | ☐ | |
| Correct abstraction | no | X | ☐ | usa prosa descrittiva invece degli identificatori esatti — scelta stilistica legittima |
| Traceable | no | X | ☐ | |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [X] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

**5. Quality score** — criteri superati sul totale: **12** / 12

**Note della valutazione**

```text
Stesso contenuto del mio; il sistema ha usato lo schema Optional feature ("Where…") mentre io Unwanted behaviour ("If…default…") — il pattern Optional feature è tecnicamente più aderente al caso "cambio di default".
```

---

# 9. PR #6947

`scrapy-scrapy-pr-6947` — 2025-07-10

## Evidenza

```text
PULL REQUEST TITLE:
Ban more imports that import twisted.internet.reactor.

PULL REQUEST BODY:
This partially rolls back the import changes in #6941 but not all of these were correct before that PR.
```

## Parte A — La mia annotazione

**Estraibilità**

- [ ] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [X] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text

```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text
Seguendo la stretta interpretazione black-box del modulo di valutazione, il divieto di importare una libreria (come `twisted.internet.reactor`) è una policy della codebase per gli sviluppatori, non un comportamento del sistema in esecuzione verificabile da un utente o un servizio chiamante. Pertanto, va scartato (o respinto).
```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | `experiments/runs/run-20260827T133248Z.json` |
| Modello generazione / valutazione | `claude-sonnet-5` / `claude-opus-5` |
| Esito del sistema | `REJECTED` |
| Tentativi | 1 |

**Requisito generato**

```text
(nessuno accettato — candidato rifiutato: "The system shall prevent modules that import the reactor from being imported.")
```

**1. Estraibilità** — il sistema ha deciso come me?

- [X] concorde
- [ ] discorde — il sistema dice: ______________

*(sul risultato pratico: entrambi non producono un requisito valido. Il sistema ha superato il gate iniziale di estraibilità e ha tentato la generazione, poi l'Assessment ha rifiutato per le stesse ragioni della mia NOT_EXTRACTABLE — l'evidenza descrive una convenzione di codice, non un comportamento del sistema.)*

**2. Corrispondenza semantica con il mio requisito**

- [ ] `MATCH` — stesso comportamento, anche se formulato diversamente
- [ ] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

*(non applicabile: nessun requisito accettato da confrontare)*

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

*(non applicabile: nessun requisito accettato)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | ☐ | ☐ | n/a |
| Evidence fidelity | **sì** | ☐ | ☐ | n/a |
| Necessary / supported | **sì** | ☐ | ☐ | n/a |
| Atomic / singular | **sì** | ☐ | ☐ | n/a |
| Unambiguous | **sì** | ☐ | ☐ | n/a |
| Verifiable | **sì** | ☐ | ☐ | n/a |
| Clear | no | ☐ | ☐ | n/a |
| Complete relative to evidence | no | ☐ | ☐ | n/a |
| Feasible | no | ☐ | ☐ | n/a |
| Consistent | no | ☐ | ☐ | n/a |
| Correct abstraction | no | ☐ | ☐ | n/a |
| Traceable | no | ☐ | ☐ | n/a |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [ ] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

*(non applicabile)*

**5. Quality score** — criteri superati sul totale: **n/a** / 12

**Note della valutazione**

```text
Convergenza pratica con la mia NOT_EXTRACTABLE: l'Assessment ha rifiutato il candidato per la stessa ragione (una convenzione di codice, non un comportamento a runtime). Il sistema ha speso una call di generazione prima di arrivarci; la mia euristica di estraibilità l'avrebbe risparmiata.
```

---

# Riepilogo

## Parte A — il mio riferimento

| PR | Estraibile | Requisito di riferimento (prime parole) |
|---|:---:|---|
| #6869 | X | When handling content provided by external sources… |
| #6870 | X | When loading modules dynamically via user input… |
| #6875 | — | *(NOT_EXTRACTABLE — correzione di refuso in commento)* |
| #6879 | X | While executing spider generation commands… |
| #6880 | X | When reading previously serialized item data… |
| #6881 | X | If XML-RPC content is received from an untrusted source… |
| #6899 | — | *(NOT_EXTRACTABLE — solo tipizzazione statica, runtime invariato)* |
| #6936 | X | If the priority queue setting is left to its default… |
| #6947 | — | *(NOT_EXTRACTABLE — policy della codebase sui divieti di import)* |

## Parte B — come si è comportato il sistema

| PR | Estraibilità concorde | Corrispondenza | Validità | Quality score |
|---|:---:|:---:|:---:|:---:|
| #6869 | ✓ | MATCH | VALID | 12/12 |
| #6870 | ✓ | MATCH | VALID | 12/12 |
| #6875 | ✓ | n/a | n/a | n/a |
| #6879 | ✓ | MATCH | VALID | 12/12 |
| #6880 | ✓ | MATCH | VALID | 12/12 |
| #6881 | ✓ | PARTIAL_MATCH | VALID | 12/12 |
| #6899 | ✓ | n/a | n/a | n/a |
| #6936 | ✓ | MATCH | VALID | 12/12 |
| #6947 | ✓ *(pratico)* | n/a | n/a | n/a |

**Metriche complessive** (Decisione 3.7, §12)

- Valid Requirement Rate: **6 / 7 = 85,7 %** (requisiti validi / candidati generati; #6947 ha generato un candidato poi rifiutato)
- Unsupported Claim Rate: **2 / 12 ≈ 16,7 %** (iterazioni con almeno un claim non supportato — attempt 1 di #6869 e attempt 1 di #6947 — su 12 iterazioni di assessment totali)
- Corrispondenza semantica: MATCH **5**, PARTIAL **1**, NO_MATCH **0** (sui 6 requisiti validi)
- Estraibilità — accuratezza: **9 / 9** in outcome (in ogni PR il sistema è arrivato allo stesso esito finale — requisito valido oppure nessun requisito). Su #6947 il sistema supera il gate iniziale ma l'Assessment converge sul rifiuto.
- Quality score medio: **12 / 12** (i 6 requisiti accettati passano tutti i criteri della rubrica)
