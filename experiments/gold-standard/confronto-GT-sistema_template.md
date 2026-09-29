# Confronto Ground Truth ↔ sistema — `____________/____________`, ___ Pull Request

**Progetto:** _______________
**Annotatori:** _______________ · _______________
**Istituzione:** _______________ · tutor: _______________

**Ground Truth:** `unificazione-GT_____________.md`
**Regole di unificazione:** `../legenda-unificazione-requisiti.md`
**Esecuzione del sistema:** `experiments/runs/____________________.json` — generatore
`____________`, valutatore `____________`, prompt `____`, massimo ___ tentativi
per Pull Request.

---

## 1. Come confrontiamo

Abbiamo annotato le Pull Request separatamente, ciascuno con la sola evidenza.
Da quelle due schede ricaviamo **un unico requisito di riferimento per Pull
Request**, e solo quel riferimento viene messo a confronto con l'output del
sistema.

### 1.1 Perché un solo Ground Truth

**Due riferimenti per la stessa Pull Request non sono un riferimento.** Se il
requisito del sistema coincide con la lettura di uno di noi e non con quella
dell'altro, il risultato della misura dipende da quale delle due si guarda. Un
metro che dà due valori non misura.

**Un requisito valido non è «quello di uno» o «quello dell'altro».** È quello
che le regole condivise producono a partire dall'evidenza. Unificare ci ha
costretti a rendere quelle regole esplicite e scritte, invece di tenerle nella
testa di ciascuno: sono in `legenda-unificazione-requisiti.md`, e chiunque può
ripercorrerle e ottenere lo stesso risultato.

**Le metriche si leggono senza mediare.** Con un solo riferimento la
corrispondenza semantica è una misura sola, non la media di due, e i criteri
della rubrica si applicano a un confronto invece che a due.

### 1.2 I due strumenti di misura

**a) La corrispondenza semantica** — il requisito del sistema descrive lo stesso
comportamento del riferimento?

```text
MATCH          stesso comportamento, anche se formulato diversamente
PARTIAL_MATCH  comportamento in parte corrispondente, più ristretto o più ampio
NO_MATCH       comportamento diverso
```

**b) La rubrica di qualità** (Decisione 3.7 §7) — i **dodici criteri**, applicati
**sia al riferimento sia al requisito del sistema**. Valutiamo anche il nostro per
due ragioni: verificare che il metro regga i propri criteri, e rendere visibile
dove il riferimento stesso è debole.

| | Significato |
|---|---|
| **✔** | criterio rispettato |
| **✘** | criterio non rispettato |
| **⚠** | rispettato, con un'osservazione riportata sotto la tabella |

Due criteri su dodici **non sono falsificabili** con questo disegno, e riportarli
come `PASS` gonfierebbe il punteggio senza dire nulla:

- **Feasible** — la fattibilità non è giudicabile dal solo testo di una Pull
  Request, come la Decisione 3.1 §3.1 già dichiara;
- **Traceable** — la tracciabilità è garantita per costruzione dalla pipeline,
  non dalla frase.

Li segniamo **—** e calcoliamo il punteggio sui **dieci criteri restanti**.

### 1.3 Da dove vengono i dati sul sistema

Non giudichiamo soltanto il requisito finale. Il rapporto di esecuzione conserva
per ogni Pull Request l'intera traccia: ogni tentativo di generazione, il
candidato prodotto, la decisione del valutatore e, quando non accetta, le
affermazioni non sostenute (`unsupported_claims`), le informazioni mancanti
(`missing_information`) e le motivazioni in chiaro (`issues`).

Ogni scheda riporta quindi **che cosa il sistema ha fatto**, non solo che cosa ha
prodotto. È l'unico modo per distinguere un requisito corretto per caso da uno
corretto perché il controllo ha funzionato — e, soprattutto, per vedere quali
difetti il valutatore intercetta e quali gli passano davanti.

---

## 2. Schede di confronto

<!-- Duplicare il blocco seguente (dall'inizio di "### PR #____" al separatore "---") per ogni Pull Request estraibile del campione. -->

### PR #____

**Evidenza (estratto)**

```text

```

| | Requisito |
|---|---|
| **Ground Truth** | *_____________________________________________________* |
| **Sistema** | *_____________________________________________________* |

**Che cosa ha fatto il sistema.** ___ tentativi.

```text

```

**Differenze rispetto al riferimento:** _______________

**Analisi.**

```text

```

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | | | | | | | | | — | | | — |
| **Sistema** | | | | | | | | | — | | | — |

*Forma:* verbo `shall` ☐ · schema GT ____________ ☐ · schema sistema ____________ ☐

**Esito:** ☐ `MATCH` ☐ `PARTIAL_MATCH` ☐ `NO_MATCH` — GT ___/10, sistema ___/10

---

<!-- Fine del blocco duplicabile per le Pull Request estraibili. -->

### PR non estraibili

<!-- Una riga per ciascuna Pull Request non estraibile del campione. -->

| PR | Ground Truth | Sistema |
|---|---|---|
| #____ | `NOT_EXTRACTABLE` — _______________ | _______________ |

**#____.** _______________

---

## 3. Resoconto

### 3.1 Esiti per Pull Request

| PR | Estraibilità | Tentativi | Corrispondenza | Rubrica GT | Rubrica sistema | Schema EARS |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| #____ | | | | | | |

| Metrica | Valore |
|---|---|
| Accuratezza sulla decisione di estraibilità | ___ / ___ |
| Corrispondenza semantica | ___ `MATCH` · ___ `PARTIAL` · ___ `NO_MATCH` su ___ |
| Punteggio medio di rubrica — Ground Truth | ___ / 10 |
| Punteggio medio di rubrica — sistema | ___ / 10 |
| Schema EARS corretto — sistema | ___ / ___ |
| Falsi positivi · falsi negativi | ___ · ___ |

### 3.2 Il quadro per criterio

| # | Criterio | Rispettato | Dove no |
|---|---|:---:|---|
| 1 | Functional | | |
| 2 | Evidence fidelity | | |
| 3 | Necessary / supported | | |
| 4 | Atomic / singular | | |
| 5 | Unambiguous | | |
| 6 | Clear | | |
| 7 | Complete relative to evidence | | |
| 8 | Verifiable | | |
| 9 | Feasible | — | non falsificabile |
| 10 | Consistent | | |
| 11 | Correct abstraction | | |
| 12 | Traceable | — | non falsificabile |

### 3.3 Che cosa fa il ciclo di revisione, dai dati

<!-- Una riga per ogni candidato su cui il valutatore è intervenuto (REVISE o REJECT). -->

| PR | Difetto intercettato | Esito |
|---|---|---|
| #____ | | |

_______________

### 3.4 Dove sbaglia

*(pattern di errore ricorrenti nel campione, se emergono; con quale evidenza)*

```text

```

### 3.5 Dove non sbaglia quasi mai

*(punti di forza sistematici nel campione)*

```text

```

### 3.6 Che cosa ne ricaviamo

*(conclusioni operative, numerate)*

1. _______________
2. _______________

### 3.7 I limiti di questo confronto

*(che cosa il campione permette di concludere, e che cosa no — dimensione del
campione, generalizzabilità, ripetibilità)*

```text

```
