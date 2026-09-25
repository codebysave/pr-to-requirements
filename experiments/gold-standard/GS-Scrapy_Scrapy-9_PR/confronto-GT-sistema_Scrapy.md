# Confronto Ground Truth ↔ sistema — `scrapy/scrapy`, 9 Pull Request

**Progetto:** PR-to-Requirements
**Annotatori:** Andrea Saverino · Marco Saverino Salvatore
**Università degli Studi di Milano-Bicocca** · tutor: Benedetta Donato

**Ground Truth:** `unificazione-GT_Scrapy.md`
**Regole di unificazione:** `../legenda-unificazione-requisiti.md`
**Esecuzione del sistema:** `experiments/runs/run-20260827T133248Z.json` — generatore
`claude-sonnet-5`, valutatore `claude-opus-5`, prompt `v1`, massimo tre tentativi
per Pull Request.

---

## 1. Come confrontiamo

Abbiamo annotato le nove Pull Request separatamente, ciascuno con la sola
evidenza. Da quelle due schede ricaviamo **un unico requisito di
riferimento per Pull Request**, e solo quel riferimento viene messo a confronto
con l'output del sistema.

### 1.1 Perché un solo Ground Truth

**Due riferimenti per la stessa Pull Request non sono un riferimento.** Se il
requisito del sistema coincide con la lettura di uno di noi e non con quella
dell'altro, il risultato della misura dipende da quale delle due si guarda. Un
metro che dà due valori non misura.

**Un requisito valido non è «quello di Andrea» o «quello di Marco».** È quello
che le regole condivise producono a partire dall'evidenza. Unificare ci ha
costretti a rendere quelle regole esplicite e scritte, invece di tenerle nella
testa di ciascuno: sono in `legenda-unificazione-requisiti.md`, e chiunque può
ripercorrerle e ottenere lo stesso risultato.

**Le nostre differenze erano risolvibili.** Divergevamo sulla forma — schemi
EARS diversi per lo stesso comportamento — e sull'ampiezza di due requisiti. In
nessun caso sul comportamento. Risolverle applicando una regola ha fatto emergere
due casi in cui **eccedevamo entrambi**, che con tre colonne affiancate non
avremmo visto.

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

### PR #6869

**Evidenza (estratto)**

```text
Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic
content. If this content can be input from outside the program, this may be a
code injection vulnerability. Ensure evaluated content is not definable by
external sources.
```

| | Requisito |
|---|---|
| **Ground Truth** | *The system shall not evaluate content originating from outside the program as executable code.* |
| **Sistema** | *The system shall not evaluate content originating from outside the program as executable code.* |

**Che cosa ha fatto il sistema.** Due tentativi.

Al 1° il generatore scrive *«…as executable code **when processing shell
input**»*. Il valutatore risponde `REVISE`, registra `when processing shell
input` fra le affermazioni non sostenute e motiva:

> *«The evidence only locates the vulnerable call in the file `scrapy/shell.py`;
> it does not say what the evaluated content is or where it comes from.»*

Ha riconosciuto che l'ambito era stato dedotto dal **nome del file**. Al 2°
tentativo il generatore toglie la condizione e il valutatore accetta senza
rilievi.

**Differenze rispetto al riferimento:** nessuna. I due requisiti coincidono
parola per parola.

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |

*Forma:* verbo `shall` ✔ · schema **ubiquitous** per entrambi ✔

**Esito: `MATCH`** — 10/10 per entrambi. È il caso in cui il ciclo di revisione fa
esattamente il lavoro per cui esiste.

---

### PR #6870

**Evidenza (estratto)**

```text
Untrusted user input in `importlib.import_module()` function allows an attacker
to load arbitrary code. Avoid dynamic values in `importlib.import_module()` or
use a whitelist to prevent running untrusted code.
```

| | Requisito |
|---|---|
| **Ground Truth** | *The system shall prevent untrusted user input from causing arbitrary code to be loaded during module import.* |
| **Sistema** | *The system shall prevent untrusted user input from causing arbitrary code to be loaded **and executed** during module import.* |

**Che cosa ha fatto il sistema.** Un solo tentativo, accettato senza alcun
rilievo: nessuna affermazione non sostenuta, nessuna informazione mancante,
nessuna osservazione.

**Differenza:** il sistema aggiunge *«and executed»*.

**Analisi.** L'esecuzione compare nell'evidenza — *«to prevent **running**
untrusted code»* — ma dentro la clausola che descrive il **rimedio suggerito**
(«or use a whitelist…»), non nella descrizione del problema. È un appiglio più
debole di quello che sostiene *«loaded»*, che è l'effetto dichiarato. L'elemento
è comunque nel testo e coerente con il comportamento: lo registriamo come
riserva, non come difetto.

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | ⚠ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |

*Forma:* verbo `shall` ✔ · schema **ubiquitous** per entrambi ✔

**Esito: `MATCH`** — GT 10/10, sistema 10/10 con una riserva su *Evidence
fidelity*.

---

### PR #6879

> **L'evidenza è identica byte per byte a quella di #6870.**

| | Requisito |
|---|---|
| **Ground Truth** | *The system shall prevent untrusted user input from causing arbitrary code to be loaded during module import.* (identico a #6870) |
| **Sistema** | *The system shall prevent user-supplied input from causing arbitrary code to be loaded and executed **when generating a spider**.* |

**Che cosa ha fatto il sistema.** Un solo tentativo, **accettato senza alcun
rilievo**: il valutatore non registra affermazioni non sostenute e non solleva
osservazioni.

**Differenza:** il sistema restringe il comportamento alla **generazione di
spider**.

**Analisi.** *«Generating a spider»* non compare nell'evidenza: si ricava dal
percorso `scrapy/commands/genspider.py`, riportato alla voce *File* del rapporto
automatico. Ricavare un ambito funzionale dal nome di un file è l'inferenza che
la Decisione 3.1 §9.2 esclude — il comportamento verrebbe da ciò che il lettore
sa di «genspider», non dal testo.

Ne segue una seconda infrazione, più grave: **a parità di evidenza il sistema
produce due requisiti diversi.** Su #6870 scrive *«during module import»*, qui
*«when generating a spider»*. Due Pull Request con evidenza identica non possono
dare requisiti con ambiti diversi.

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | **✘** | **✘** | ✔ | ✔ | ✔ | ✔ | ✔ | — | **✘** | ✔ | — |

- **Evidence fidelity ✘** — l'ambito non è sostenuto dall'evidenza.
- **Necessary / supported ✘** — la qualificazione non è né necessaria né
  giustificata dal testo.
- **Consistent ✘** — contraddice il requisito prodotto su evidenza identica.

*Forma:* verbo `shall` ✔ · schema **ubiquitous** per entrambi ✔

**Esito: `PARTIAL_MATCH`** — il sistema è più ristretto del riferimento. GT
10/10, **sistema 7/10**.

---

### PR #6880

**Evidenza (estratto)**

```text
Avoid using `pickle`, which is known to lead to code execution vulnerabilities.
When unpickling, the serialized data could be manipulated to run arbitrary code.
Instead, consider serializing the relevant data as JSON or a similar text-based
serialization format.
```

| | Requisito |
|---|---|
| **Ground Truth** | ***When** previously serialised item data is read back, the system shall process it without executing any code contained in that data.* |
| **Sistema** | ***If** previously serialised item data is read back, **then** the system shall process it without executing any code contained in that data.* |

**Che cosa ha fatto il sistema.** Due tentativi.

Al 1° il generatore scrive *«The system shall export data without using
deserialization methods that could execute arbitrary code…»*. Il valutatore
risponde `REVISE` con due motivazioni, entrambe corrette:

> *«The requirement is phrased as a prohibition on a class of mechanisms …
> whether a given method is used can only be checked by reading the source, not
> by observing the system.»*
>
> *«It attaches the guarantee to 'export' (serialisation) while the risk the
> evidence describes materialises when the serialised data is read back.»*

Al 2° tentativo il generatore corregge entrambi i difetti insieme e il valutatore
accetta.

**Differenza:** soltanto lo **schema EARS**. Il contenuto è identico parola per
parola.

**Analisi.** Il sistema usa *unwanted behaviour* (`If … then`), che richiede una
condizione **indesiderata**. Rileggere dati che il sistema stesso ha serializzato
è un'operazione **normale**: ciò che è indesiderato è la conseguenza —
l'esecuzione di codice — ed è proprio quello che la risposta vieta. Lo schema
corretto è *event-driven*, perché l'evidenza nomina un momento (*«when
unpickling»*).

Sui dodici criteri i due requisiti risultano indistinguibili: la scelta dello
schema non è fra i criteri della rubrica, ed è per questo che la riportiamo a
parte in ogni scheda.

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |

*Forma:* verbo `shall` ✔ per entrambi · schema — GT *event-driven* ✔, sistema
*unwanted behaviour* **✘**

**Esito: `MATCH`** — 10/10 per entrambi sulla rubrica, schema non conforme per il
sistema.

---

### PR #6881

**Evidenza**

```text
TITOLO: Fix: Unsafe XML Processing Library Could Allow Malicious Attacks in
        scrapy/http/request/rpc.py
CORPO:  Detected use of xmlrpc. xmlrpc is not inherently safe from
        vulnerabilities. Use defusedxml.xmlrpc instead. […] This change is
        necessary to protect the application from potential security risks.
```

| | Requisito |
|---|---|
| **Ground Truth** | *The system shall not allow XML-RPC content it processes to have any effect on the application beyond the data that content carries.* |
| **Sistema** | *When processing XML-RPC content **received from an untrusted source**, the system shall not **execute or resolve any external entities or code** embedded within that content.* |

**Che cosa ha fatto il sistema.** Due tentativi, ed è il percorso più istruttivo
del campione.

Al 1° il generatore scrive *«…the system shall protect against malicious XML
input that could compromise the application»*. Il valutatore risponde `REVISE`
con due motivazioni che condividiamo:

> *«The obligation is phrased as a protection goal rather than an observable
> behaviour … close to 'the system must be secure' and gives a black-box test
> nothing to check.»*
>
> *«The qualifier 'that could compromise the application' is circular: it defines
> the input by the very harm the requirement is supposed to exclude.»*

Al 2° tentativo il generatore rende il requisito verificabile **nominando entità
esterne ed esecuzione di codice**, e il valutatore accetta **senza registrare
alcuna affermazione non sostenuta**.

**Differenze:** il sistema nomina entità esterne ed esecuzione di codice, e
aggiunge la provenienza da fonte non attendibile.

**Analisi.** Nessuno dei tre elementi compare nell'evidenza. Il corpo dice che
`xmlrpc` «is not inherently safe from vulnerabilities» e che si usi
`defusedxml.xmlrpc`: non dice mai *che cosa* la vulnerabilità permetta di fare,
né distingue contenuto fidato da non fidato. Tutti e tre provengono dalla
conoscenza della classe di vulnerabilità XXE, cioè dal significato convenzionale
di un artefatto nominato (§9.2).

La traccia mostra **come** ci è arrivato: il valutatore chiede verificabilità, e
su un'evidenza che non enuncia l'effetto indesiderato l'unico modo di essere
verificabili è prendere l'effetto da un'altra parte. Verificabilità e fedeltà
all'evidenza tirano qui in direzioni opposte, e il ciclo spinge verso la prima.

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | **✘** | **✘** | ⚠ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |

- **Evidence fidelity ✘** e **Necessary / supported ✘** — tre elementi non
  sostenuti dal testo.
- **Atomic ⚠** — *«shall not execute **or** resolve»* enuncia due comportamenti
  vietati; li leggiamo come un unico divieto su un insieme, ma la formulazione è
  al limite.

*Forma:* verbo `shall` ✔ · schema — GT *ubiquitous* ✔, sistema *event-driven* ⚠
(il trigger «processing XML-RPC content» coincide con l'oggetto della risposta)

**Esito: `PARTIAL_MATCH`** — il sistema è più specifico del riferimento. GT
10/10, **sistema 8/10**.

> **Punto da fissare.** Questo scarto lo contiamo una volta sola. Oggi compare sia
> come `PARTIAL_MATCH` sia come `✘` su *Evidence fidelity*: va deciso quale delle
> due misure lo registra, prima delle prove finali.

---

### PR #6936

**Evidenza (estratto)**

```text
feat(settings): Change default SCHEDULER_PRIORITY_QUEUE (closes #6924)
Changes default `SCHEDULER_PRIORITY_QUEUE` to `DownloaderAwarePriorityQueue`.
[…] Confirmed backward compatibility
```

| | Requisito |
|---|---|
| **Ground Truth** | *Where the **SCHEDULER_PRIORITY_QUEUE** setting has not been overridden, the system shall use **DownloaderAwarePriorityQueue** as the scheduler priority queue.* |
| **Sistema** | *Where the **scheduler priority queue setting** has not been overridden, the system shall use the **downloader-aware priority queue** to schedule requests.* |

**Che cosa ha fatto il sistema.** Un solo tentativo, accettato senza rilievi.

**Differenza:** identificatori esatti (riferimento) contro descrizione in prosa
(sistema). Schema e comportamento coincidono.

**Analisi.** La nostra convenzione impone l'identificatore quando l'evidenza
dichiara quale impostazione cambia e a quale valore, perché la prova del
requisito è *«non sovrascrivere nulla e guardare quale valore si applica»* e
richiede di sapere **quale** impostazione lasciare intatta. La prosa del sistema
è comprensibile ma non identifica univocamente l'impostazione.

Lo registriamo come **riserva su *Verifiable***, non come difetto: la convenzione
sugli identificatori vincola la scrittura del riferimento, mentre il confronto con
il sistema è semantico e non lessicale. Contarla come errore introdurrebbe di
nascosto un criterio testuale in una misura dichiarata semantica.

| | Func | Evid | Nec | Atom | Unamb | Clear | Compl | Verif | Feas | Cons | Abstr | Trace |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **GT** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | ✔ | ✔ | — |
| **Sistema** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ⚠ | — | ✔ | ✔ | — |

*Forma:* verbo `shall` ✔ · schema **optional feature** per entrambi ✔ — è l'unica
Pull Request con un cambio di valore predefinito, e il sistema sceglie da solo lo
schema corretto.

**Esito: `MATCH`** — GT 10/10, sistema 10/10 con una riserva su *Verifiable*.

---

### PR #6875, #6899, #6947 — le non estraibili

| PR | Ground Truth | Sistema |
|---|---|---|
| **#6875** | `NOT_EXTRACTABLE` — correzione di refusi in commenti | il generatore **si rifiuta di generare**; il valutatore conferma |
| **#6899** | `NOT_EXTRACTABLE` — sola tipizzazione statica | il generatore **si rifiuta di generare**; il valutatore conferma |
| **#6947** | `NOT_EXTRACTABLE` — vincolo interno alla codebase | candidato generato, poi **rifiutato** dal valutatore |

**#6875.** Il generatore dichiara: *«The change only corrects wording in a source
code comment and explicitly states no code logic or functionality is affected»*.
Il valutatore conferma aggiungendo che *«no black-box test could distinguish the
system before and after the change»*. È la nostra stessa motivazione.

**#6899.** Il generatore dichiara che si tratta di *«a static-typing fix … that
explicitly preserves runtime behavior»*; il valutatore conferma con il test
black-box. Ancora la nostra stessa motivazione.

**#6947.** Qui il generatore non si ferma: produce *«The system shall prevent
modules that import the reactor from being imported»*. Il valutatore lo respinge
con `REJECT` registrando **tre** affermazioni non sostenute — l'effetto di
applicazione al momento dell'import, l'insieme dei moduli interessati, e
l'esistenza di una garanzia di sistema anziché di una convenzione della codebase
— e conclude:

> *«Once the unsupported run-time prevention is removed, only 'some imports were
> banned in the codebase' remains, which establishes no observable required
> behaviour, so no rewrite at a higher level can be grounded in this evidence.»*

L'esito è quello corretto e la motivazione coincide con la nostra, ma costa una
chiamata di generazione: il controllo d'ingresso, basato sulla sola lunghezza del
testo, lascia passare tutte e nove le Pull Request.

---

## 3. Resoconto

### 3.1 Esiti per Pull Request

| PR | Estraibilità | Tentativi | Corrispondenza | Rubrica GT | Rubrica sistema | Schema EARS |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| #6869 | concorde | 2 | `MATCH` | 10/10 | 10/10 | ✔ |
| #6870 | concorde | 1 | `MATCH` | 10/10 | 10/10 ⚠ | ✔ |
| #6875 | concorde | 1 | — | — | — | — |
| #6879 | concorde | 1 | `PARTIAL` | 10/10 | **7/10** | ✔ |
| #6880 | concorde | 2 | `MATCH` | 10/10 | 10/10 | **✘** |
| #6881 | concorde | 2 | `PARTIAL` | 10/10 | **8/10** | ⚠ |
| #6899 | concorde | 1 | — | — | — | — |
| #6936 | concorde | 1 | `MATCH` | 10/10 | 10/10 ⚠ | ✔ |
| #6947 | concorde | 1 | — | — | — | — |

| Metrica | Valore |
|---|---|
| Accuratezza sulla decisione di estraibilità | **9 / 9** |
| Corrispondenza semantica | **4 `MATCH` · 2 `PARTIAL` · 0 `NO_MATCH`** su 6 |
| Punteggio medio di rubrica — Ground Truth | **10,0 / 10** |
| Punteggio medio di rubrica — sistema | **9,2 / 10** |
| Schema EARS corretto — sistema | **4 / 6** (1 errore, 1 riserva) |
| Falsi positivi · falsi negativi | **0 · 0** |

### 3.2 Il quadro per criterio

| # | Criterio | Rispettato | Dove no |
|---|---|:---:|---|
| 1 | Functional | **6/6** | — |
| 2 | Evidence fidelity | **4/6** | #6879, #6881 *(riserva: #6870)* |
| 3 | Necessary / supported | **4/6** | #6879, #6881 |
| 4 | Atomic / singular | **6/6** | *(riserva: #6881)* |
| 5 | Unambiguous | **6/6** | — |
| 6 | Clear | **6/6** | — |
| 7 | Complete relative to evidence | **6/6** | — |
| 8 | Verifiable | **6/6** | *(riserva: #6936)* |
| 9 | Feasible | — | non falsificabile |
| 10 | Consistent | **5/6** | #6879 |
| 11 | Correct abstraction | **6/6** | — |
| 12 | Traceable | — | non falsificabile |

Il Ground Truth rispetta tutti e dieci i criteri falsificabili su tutte e sei le
Pull Request. Era atteso — lo abbiamo costruito applicando quegli stessi criteri
— e vale come verifica di coerenza del metro, non come risultato.

### 3.3 Che cosa fa il ciclo di revisione, dai dati

Sui sette candidati prodotti, il valutatore interviene **quattro volte**:

| PR | Difetto intercettato | Esito |
|---|---|---|
| #6869 | ambito dedotto dal nome del file | corretto al 2° tentativo |
| #6880 | divieto su una classe di meccanismi, e momento del rischio sbagliato | corretti entrambi al 2° tentativo |
| #6881 | obbligo circolare e non verificabile | corretto al 2° tentativo |
| #6947 | tre affermazioni non sostenute | candidato bloccato |

Tre requisiti su sei sarebbero entrati nell'archivio difettosi senza il ciclo, e
il quarto non sarebbe dovuto esistere affatto. Il ciclo non è un componente di
riserva: interviene su più della metà del materiale prodotto.

### 3.4 Dove sbaglia — e la cosa più interessante del campione

Le due infrazioni hanno **la stessa causa**: un pezzo di comportamento ricavato
dal **nome di un artefatto**, che la Decisione 3.1 §9.2 vieta.

| PR | Elemento non sostenuto | Da dove viene |
|---|---|---|
| #6879 | *«when generating a spider»* | dal nome del file `genspider.py` |
| #6881 | *«external entities»*, *«code»*, *«untrusted source»* | dal nome della libreria `defusedxml` |

Ma la traccia di esecuzione dice qualcosa di più preciso, e cambia la diagnosi.

**Su #6869 il valutatore ha intercettato esattamente questo errore.** Il primo
candidato conteneva *«when processing shell input»*, ambito dedotto da
`scrapy/shell.py`, e il valutatore l'ha registrato fra le affermazioni non
sostenute motivando che *«the evidence only locates the vulnerable call in the
file; it does not say what the evaluated content is or where it comes from»*.

**Su #6879, nella stessa esecuzione, lo stesso errore è passato senza un
rilievo.** *«When generating a spider»* è dedotto da `genspider.py` con la
medesima struttura, e il valutatore ha accettato al primo colpo senza registrare
nulla.

Non è quindi una regola che manca: **è una regola che il sistema possiede e
applica in modo non uniforme.** Lo stesso valutatore, nella stessa esecuzione, con
lo stesso prompt, la fa scattare su una Pull Request e non sull'altra.

Il fenomeno si vede anche dal lato del generatore: **#6870 e #6879 hanno evidenza
identica**, e il generatore produce due ambiti diversi — *«during module import»*
in un caso, *«when generating a spider»* nell'altro. La variabilità è su entrambi
gli agenti, e il valutatore non la corregge.

Una differenza fra i due casi la notiamo, e la proponiamo come ipotesi da
verificare: in #6869 l'elemento dedotto riguardava la **provenienza** del
contenuto, in #6879 l'**occasione** in cui il comportamento vale. Il valutatore
potrebbe essere più sensibile alle affermazioni di provenienza che a quelle di
ambito. È una congettura, non una conclusione: si verifica ripetendo l'esecuzione
sulle stesse Pull Request e contando quante volte #6879 viene intercettato.

### 3.5 Dove non sbaglia quasi mai

**Sulla forma non sbaglia mai.** Verbo prescrittivo, atomicità, non ambiguità,
chiarezza, completezza rispetto all'evidenza, astrazione corretta: **6 su 6**.
Nessun requisito accettato nomina una libreria, una funzione o un file — con la
sola eccezione legittima di #6936, dove il cambio dell'impostazione nominata è
l'oggetto stesso della Pull Request.

**Sulla natura funzionale non sbaglia mai.** Su tutte e tre le Pull Request senza
comportamento osservabile arriva a «nessun requisito», due volte fermandosi in
generazione e una con il rifiuto del valutatore, con motivazioni che coincidono
con le nostre.

### 3.6 Che cosa ne ricaviamo

1. **Il margine di miglioramento non sta nell'aggiungere regole.** La regola §9.2
   c'è, e quando scatta funziona: su #6869 ha corretto il difetto al primo giro.
   Quello che manca è la **costanza di applicazione**, che è un problema diverso e
   non si risolve scrivendo il prompt in modo più dettagliato.
2. **Ripetere le esecuzioni è una necessità, non un'accortezza.** Con un'unica
   esecuzione non possiamo distinguere un difetto sistematico da una variazione
   fra repliche. Le stesse nove Pull Request, ripetute, ci dicono quante volte
   #6879 viene intercettato — e la risposta cambia la conclusione.
3. **La coerenza va decisa.** Il sistema produce due requisiti diversi da evidenza
   identica e non se ne accorge. Il meccanismo per accorgersene esiste — il
   confronto con i requisiti storici in memoria — ma per progetto le relazioni
   vengono dichiarate e non fatte decidere. Oggi la rubrica valuta *Consistent*
   come `PASS`/`FAIL` mentre il sistema la tratta come osservazione: le due cose
   non possono restare entrambe.
4. **Lo schema EARS va misurato.** L'errore di #6880 non compare in nessuno dei
   dodici criteri. O si aggiunge un criterio alla rubrica, o il controllo di forma
   resta dichiarato a parte — ma va scritto nella Decisione 3.7.
5. **Il controllo d'ingresso può fare di più.** Basandosi sulla sola lunghezza
   lascia passare tutte e nove le Pull Request; su #6947 questo costa una chiamata
   di generazione inutile.

### 3.7 I limiti di questo confronto

Sei requisiti sono pochi per parlare di frequenze: *4/6* e *5/6* sono indicazioni,
non tassi. Quello che il campione stabilisce con sicurezza non è **quanto spesso**
il sistema sbaglia, ma **come** sbaglia quando sbaglia — e i due casi convergono
senza ambiguità su un'unica regola. La misura della frequenza spetta al corpus
OpenHands e alle repliche.

---

## Appendice — L'accordo fra noi due annotatori

Si calcola sulle **schede originali**, mai sul Ground Truth: sul Ground Truth
farebbe 100% per costruzione e non dimostrerebbe nulla. È il dato che stabilisce
se i criteri della Decisione 3.1 siano applicabili da persone diverse in modo
indipendente.

| | Valore |
|---|---|
| Stessa decisione di estraibilità | **9 / 9** |
| Corrispondenza semantica fra i due requisiti | 5 `MATCH` · 1 `PARTIAL` · 0 `NO_MATCH` |

L'unico scostamento è su **#6881**, dove uno di noi limitava il requisito alle
entità esterne e l'altro copriva anche l'esecuzione di codice. L'unificazione ha
poi stabilito che nessuna delle due letture era sostenuta dall'evidenza: è la
Pull Request su cui il campione è più fragile, e non è un caso che sia anche
quella su cui il sistema si spinge più in là.
