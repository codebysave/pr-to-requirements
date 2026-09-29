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

## La mia annotazione

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

---

<!-- Fine del blocco duplicabile. Il Riepilogo va compilato una sola volta, alla fine del documento. -->

# Riepilogo — il mio riferimento

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
