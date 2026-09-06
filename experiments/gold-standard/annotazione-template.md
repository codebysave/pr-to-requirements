# Scheda di annotazione — Gold standard

**Annotatore:** _______________

Campione: `experiments/samples/________________________.json` — ___ Pull Request di `_____________/_____________`,
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

<!-- Duplicare il blocco seguente (dall'inizio del titolo "# N. PR #____" al separatore "---") per ogni Pull Request del campione, aggiornando N e il numero della PR. -->

# N. PR #____

`____________-____________-pr-____` — YYYY-MM-DD

## Evidenza

```text
PULL REQUEST TITLE:


PULL REQUEST BODY:

```

## Parte A — La mia annotazione

**Estraibilità**

- [ ] `EXTRACTABLE` — dall'evidenza si identifica almeno un comportamento richiesto
- [ ] `NOT_EXTRACTABLE` — l'evidenza non consente di identificarne alcuno

**Requisito di riferimento** *(solo se estraibile)*

```text

```

**Schema EARS usato:** ☐ ubiquitous ☐ event-driven ☐ state-driven ☐ unwanted behaviour ☐ optional feature

**Note** *(perché ho deciso così; dubbi; elementi che ho scartato di proposito)*

```text

```

## Parte B — Confronto con l'esecuzione

| | |
|---|---|
| Run (file) | |
| Modello generazione / valutazione | |
| Esito del sistema | `ACCEPTED` / `REJECTED` / `NOT_EXTRACTABLE` / `FAILED_VALIDATION` |
| Tentativi | |

**Requisito generato**

```text

```

**1. Estraibilità** — il sistema ha deciso come me?

- [ ] concorde
- [ ] discorde — il sistema dice: ______________

**2. Corrispondenza semantica con il mio requisito**

- [ ] `MATCH` — stesso comportamento, anche se formulato diversamente
- [ ] `PARTIAL_MATCH` — comportamento in parte corrispondente, o più ristretto/ampio
- [ ] `NO_MATCH` — comportamento diverso

**3. Rubrica di qualità** *(sul requisito generato, indipendentemente dal mio)*

| Criterio | Obbligatorio | PASS | FAIL | Note |
|---|:---:|:---:|:---:|---|
| Functional | **sì** | ☐ | ☐ | |
| Evidence fidelity | **sì** | ☐ | ☐ | |
| Necessary / supported | **sì** | ☐ | ☐ | |
| Atomic / singular | **sì** | ☐ | ☐ | |
| Unambiguous | **sì** | ☐ | ☐ | |
| Verifiable | **sì** | ☐ | ☐ | |
| Clear | no | ☐ | ☐ | |
| Complete relative to evidence | no | ☐ | ☐ | |
| Feasible | no | ☐ | ☐ | |
| Consistent | no | ☐ | ☐ | |
| Correct abstraction | no | ☐ | ☐ | |
| Traceable | no | ☐ | ☐ | |

**4. Hard gate** — se anche uno solo dei criteri obbligatori è `FAIL`, l'esito è
`NOT_VALID`, indipendentemente dagli altri.

- [ ] `VALID`
- [ ] `NOT_VALID` — criterio che ha fatto fallire: ______________

**5. Quality score** — criteri superati sul totale: ______ / 12

**Note della valutazione**

```text

```

---

<!-- Fine del blocco duplicabile. Il Riepilogo va compilato una sola volta, alla fine del documento. -->

# Riepilogo

## Parte A — il mio riferimento

| PR   | Estraibile | Requisito di riferimento (prime parole) |
|------|:----------:|-----------------------------------------|
| #____ |            |                                         |
| #____ |            |                                         |
| #____ |            |                                         |
| #____ |            |                                         |
| #____ |            |                                         |
| #____ |            |                                         |
| #____ |            |                                         |
| #____ |            |                                         |
| #____ |            |                                         |

## Parte B — come si è comportato il sistema

| PR    | Estraibilità concorde | Corrispondenza | Validità | Quality score |
|-------|:---------------------:|:--------------:|:--------:|:-------------:|
| #____ |                       |                |          |               |
| #____ |                       |                |          |               |
| #____ |                       |                |          |               |
| #____ |                       |                |          |               |
| #____ |                       |                |          |               |
| #____ |                       |                |          |               |
| #____ |                       |                |          |               |
| #____ |                       |                |          |               |
| #____ |                       |                |          |               |

**Metriche complessive** (Decisione 3.7, §12)

- Valid Requirement Rate: ____ / ____ = ____ %
- Unsupported Claim Rate: ____ / ____ = ____ %
- Corrispondenza semantica: MATCH ____, PARTIAL ____, NO_MATCH ____
- Estraibilità — accuratezza: ____ / ____
- Quality score medio: ____ / 12
