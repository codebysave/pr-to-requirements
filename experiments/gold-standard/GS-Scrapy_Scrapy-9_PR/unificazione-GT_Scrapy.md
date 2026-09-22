# Unificazione dei requisiti — `scrapy/scrapy`, 9 Pull Request

**Progetto:** PR-to-Requirements
**Annotatori:** Andrea Saverino · Marco Saverino Salvatore
**Università degli Studi di Milano-Bicocca** · tutor: Benedetta Donato

**Campione:** `experiments/samples/sample-scrapy_scrapy.json` — 9 Pull Request, di cui
**6 estraibili** (#6869, #6870, #6879, #6880, #6881, #6936).
**Regole applicate:** `legenda-unificazione-requisiti.md` — documento separato e
unica fonte delle regole: qui non le duplichiamo, per non farle divergere.
**Data dell'unificazione:** 2026-09-22

---

## A che cosa serve questo documento

Abbiamo annotato le stesse nove Pull Request separatamente, ciascuno con la sola
evidenza sotto gli occhi. Le due schede che ne sono uscite sono valide entrambe
ma non coincidono: formulazioni diverse e, sistematicamente, schemi EARS diversi.

Qui le unifichiamo in **un unico requisito di riferimento per ogni Pull Request
estraibile**, applicando le regole che ci siamo dati. Il risultato — l'elenco in
fondo — è il **Ground Truth** con cui confronteremo i requisiti prodotti dal
sistema.

Per ogni Pull Request riportiamo l'evidenza su cui poggia la decisione, le due
annotazioni di partenza, la regola che ha deciso o la motivazione della scelta, e
il requisito unificato. Chi legge deve poter rifare il percorso e arrivare allo
stesso risultato: se non ci riesce, l'unificazione è sbagliata.

---

## Riepilogo degli esiti

| PR | Divergenza | Schema del GT | Esito | Il GT viene da |
|---|---|---|---|---|
| **#6869** | D1 | ubiquitous | unificato | ri-derivato (schema di Andrea, verbo di Marco) |
| **#6870** | D1 + D2 | ubiquitous | unificato | ri-derivato |
| **#6879** | D1 + D2 | ubiquitous | unificato — **identico a #6870** | Andrea |
| **#6880** | D1 + D2 | event-driven | unificato | Marco (contenuto), ri-derivato (forma) |
| **#6881** | D2 | ubiquitous | **rianotata** → unificato | ri-derivato (nessuna delle due formulazioni reggeva) |
| **#6936** | D1 | optional feature | unificato | Andrea |

**Sei Ground Truth su sei.** Cinque escono direttamente dai passi; #6881 non supera
il Passo 3 e viene **rianotata in fondo alla propria scheda**, dove la discussione
e le motivazioni producono il requisito unificato.

---

# Schede compilate

## PR #6869 — `scrapy-scrapy-pr-6869` — 2025-06-06

**Evidenza rilevante**

```text
Detected the use of eval(). eval() can be dangerous if used to evaluate dynamic
content. If this content can be input from outside the program, this may be a
code injection vulnerability. Ensure evaluated content is not definable by
external sources.
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | ubiquitous | event-driven |
| Requisito | *The system shall prevent the execution of arbitrary code originating from untrusted input.* | *When handling content provided by external sources, the system shall not evaluate it as executable code.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☐ D2 ☐ D3

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **ubiquitous**
- Regola applicata: **test del trigger** (§2.1a). Il trigger di Marco — *«content
  provided by external sources»* — è la stessa entità dell'oggetto della sua
  risposta (*«it»*). Spostandolo sull'oggetto non si perde nulla, quindi era una
  ripetizione. Si applica inoltre il **corollario sui divieti**: un `shall not`
  che vale in ogni istante non ha un momento in cui scatta.
- Scelta del verbo: si tiene **«evaluate … as executable code»** (Marco) e non
  «prevent the execution of arbitrary code» (Andrea), perché l'evidenza prescrive
  un comportamento sulla **valutazione** — *«Ensure evaluated content is not
  definable by external sources»* — mentre l'esecuzione di codice è la
  conseguenza che quella valutazione produrrebbe.
- Identificatore obbligatorio? **No** — nessun valore predefinito cambia.
  `eval()` e `scrapy/shell.py` non devono comparire.

**Passo 3 — Ampiezza:** non applicabile (nessun D2).

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
The system shall not evaluate content originating from outside the program as
executable code.
```

---

## PR #6870 — `scrapy-scrapy-pr-6870` — 2025-06-06

**Evidenza rilevante**

```text
Untrusted user input in `importlib.import_module()` function allows an attacker
to load arbitrary code. Avoid dynamic values in `importlib.import_module()` or
use a whitelist to prevent running untrusted code.
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | ubiquitous | event-driven |
| Requisito | *The system shall prevent the loading of arbitrary code originating from untrusted user input.* | *When loading modules dynamically via user input, the system shall prevent the execution of arbitrary code.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☒ D2 ☐ D3

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **ubiquitous**
- Regola applicata: **test del trigger** (§2.1a). L'informazione contenuta nel
  `When` di Marco — che il caricamento avviene a partire da input dell'utente —
  può essere portata **sull'oggetto** della risposta senza perdite. Vale inoltre
  il corollario sui divieti.
- Identificatore obbligatorio? **No.** `importlib.import_module()` è un nome di
  funzione e non deve comparire; il **caricamento di moduli** come operazione sì,
  perché l'evidenza lo descrive in prosa (vedi Passo 3).

**Passo 3 — Ampiezza**

- Elemento in discussione (E): il **contesto del caricamento di moduli**, presente
  in Marco e assente in Andrea.
- Che cosa ne dice l'evidenza: lo **enuncia esplicitamente**, e non soltanto come
  nome di funzione — *«Untrusted user input … allows an attacker to **load
  arbitrary code**»*. L'operazione di caricamento è descritta, non dedotta.
- Scelta: ☒ **tenuto**
- Motivazione:

```text
Il caricamento di codice è scritto nel testo, quindi ometterlo (Andrea) perde
informazione funzionale che l'evidenza fornisce. Teniamo l'operazione ma non il
nome della funzione che la realizza: `importlib.import_module()` è meccanismo,
"module import" è il comportamento osservabile.

Nota di controllo: l'evidenza SUGGERISCE una whitelist ("or use a whitelist"),
non dichiara di averla applicata. Nessuno dei due l'ha asserita, e nel GT non
deve comparire.
```

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
The system shall prevent untrusted user input from causing arbitrary code to be
loaded during module import.
```

---

## PR #6879 — `scrapy-scrapy-pr-6879` — 2025-06-09

> **L'evidenza è identica byte per byte a quella di #6870.**

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | ubiquitous | state-driven |
| Requisito | *The system shall prevent the loading of arbitrary code originating from untrusted user input.* | *While executing spider generation commands, the system shall restrict user input to prevent the loading of arbitrary code.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☒ D2 ☐ D3

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **ubiquitous**
- Regola applicata: §2.1b. `While` richiede uno stato **chiaramente ricostruibile
  dall'evidenza** (Dec. 3.1 §6.3). *«Executing spider generation commands»* non
  compare nell'evidenza: si deduce dal percorso del file
  `scrapy/commands/genspider.py`. Uno stato dedotto da un nome di file non è
  ricostruibile dall'evidenza — è un'inferenza, §9.2. In dubbio, e qui non c'è
  dubbio, non si usa `While`.

**Passo 3 — Ampiezza**

- Elemento in discussione (E): l'ambito **«generazione di spider»**, presente in
  Marco e assente in Andrea.
- Che cosa ne dice l'evidenza: **niente**. La generazione di spider compare solo
  dentro il percorso `scrapy/commands/genspider.py`, alla voce *File* del report
  automatico.
- Scelta: ☒ **tolto**
- Motivazione:

```text
Il nome di un file dice DOVE si trova il codice, non CHE COSA il sistema deve
fare. Ricavarne un ambito funzionale è esattamente l'inferenza che la Decisione
3.1 §9.2 esclude: il comportamento verrebbe da ciò che noi sappiamo di
"genspider", non dal testo.

Contro-argomento, registrato perché non è debole: il percorso del file è
materialmente scritto nel corpo della PR, quindi è "nel testo". Lo respingiamo
perché §9.2 non parla di presenza del nome, ma di derivazione del comportamento
dal nome — ed è precisamente ciò che l'ambito "spider generation" fa.

CONSEGUENZA: essendo l'evidenza identica a quella di #6870, il Ground Truth deve
essere lo stesso requisito. Due PR con la stessa evidenza non possono avere due
riferimenti diversi.
```

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
The system shall prevent untrusted user input from causing arbitrary code to be
loaded during module import.
```

*(identico al GT di #6870, per identità dell'evidenza)*

---

## PR #6880 — `scrapy-scrapy-pr-6880` — 2025-06-09

**Evidenza rilevante**

```text
Avoid using `pickle`, which is known to lead to code execution vulnerabilities.
When unpickling, the serialized data could be manipulated to run arbitrary code.
Instead, consider serializing the relevant data as JSON or a similar text-based
serialization format.
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | ubiquitous | event-driven |
| Requisito | *The system shall not export data whose loading executes code contained in the data.* | *When reading previously serialized item data, the system shall process the information without triggering the execution of embedded code.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☒ D2 ☐ D3

**Passo 3 — Ampiezza** *(risolto per primo: determina la forma)*

- Elemento in discussione (E): **il momento in cui il rischio si materializza** —
  l'esportazione/scrittura (Andrea) contro la rilettura (Marco).
- Che cosa ne dice l'evidenza: lo enuncia **alla lettera** — *«**When
  unpickling**, the serialized data could be manipulated to run arbitrary
  code»*. *Unpickling* è la rilettura.
- Scelta: ☒ **tenuta la rilettura**, tolta l'esportazione
- Motivazione:

```text
L'evidenza colloca il pericolo nella deserializzazione, non nella scrittura.
"Export" (Andrea) sposta il comportamento in un momento che il testo non indica:
è un'infedeltà all'evidenza, anche se il comportamento risultante è simile.

Nota di controllo: JSON è un rimedio SUGGERITO ("consider serializing … as
JSON"), mai dichiarato applicato. Non deve comparire nel GT. Nessuno dei due
l'ha asserito.
```

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **event-driven**
- Regola applicata: l'evidenza nomina un **momento** (*when unpickling*) distinto
  dall'oggetto della risposta, quindi il test del trigger (§2.1a) non lo elimina:
  togliendo il `When` si perde il momento, e l'oggetto da solo non lo porta.
- Perché **non** unwanted behaviour (§2.1c): rileggere dati che il sistema stesso
  ha serializzato è un'operazione **normale**, non una condizione anomala. Ciò
  che è indesiderato è la conseguenza — l'esecuzione di codice — ed è
  esattamente quello che la risposta vieta. Metterla nella clausola `If`
  significherebbe scambiare la conseguenza per la condizione.
- Identificatore obbligatorio? **No.** `pickle`, `JSON` e `scrapy/exporters.py`
  non devono comparire.

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
When previously serialised item data is read back, the system shall process it
without executing any code contained in that data.
```

---

## PR #6881 — `scrapy-scrapy-pr-6881` — 2025-06-09 — **rianotata**

**Evidenza integrale rilevante**

```text
TITOLO: Fix: Unsafe XML Processing Library Could Allow Malicious Attacks in
        scrapy/http/request/rpc.py

CORPO:  Detected use of xmlrpc. xmlrpc is not inherently safe from
        vulnerabilities. Use defusedxml.xmlrpc instead.
        […] This change is necessary to protect the application from potential
        security risks associated with this vulnerability.
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | ubiquitous | unwanted behaviour |
| Requisito | *The system shall process XML-RPC data without executing arbitrary code contained in the data.* | *If XML-RPC content is received from an untrusted source, then the system shall prevent the resolution of external entities.* |

**Passo 1 — Tipo di divergenza:** ☐ D1 ☒ D2 ☐ D3

**Passo 3 — Ampiezza**

Tre elementi in discussione, e la domanda del Passo 3 dà la stessa risposta a
tutti e tre:

| E | Presente in | L'evidenza lo enuncia? |
|---|---|---|
| *«executing arbitrary code contained in the data»* | Andrea | **no** |
| *«the resolution of external entities»* | Marco | **no** |
| *«received from an untrusted source»* | Marco | **no** |

- Scelta: ☐ tenuto ☒ **entrambe le annotazioni eccedono → nucleo comune** ☒ **il
  nucleo comune non è verificabile → rianotare**
- Motivazione:

```text
Il corpo della PR dice tre cose: che è stato rilevato l'uso di `xmlrpc`, che
`xmlrpc` "is not inherently safe from vulnerabilities", e che si deve usare
`defusedxml.xmlrpc`. NON dice mai CHE COSA faccia la vulnerabilità.

Sia le entità esterne (Marco) sia l'esecuzione di codice (Andrea) provengono da
ciò che NOI sappiamo di defusedxml e della classe XXE — cioè dal significato
convenzionale di un artefatto nominato. È il caso diretto della Decisione 3.1
§9.2. Le due annotazioni non divergono per ampiezza: eccedono entrambe, in
direzioni diverse, a partire dalla stessa conoscenza esterna.

Tolti gli elementi non fondati, il nucleo comune è "il sistema deve elaborare
contenuto XML-RPC senza esserne compromesso" — che è la forma "il sistema deve
essere sicuro": un attributo di qualità su cui non si può scrivere una prova
black-box. Fallisce la verificabilità.

Contro-argomento, registrato: il titolo dice "Could Allow Malicious Attacks" e il
corpo parla di "protect the application from potential security risks", quindi
QUALCOSA sulla sicurezza è enunciato. Lo respingiamo perché "proteggere da
rischi" non è un comportamento osservabile, ed è la formulazione che i nostri
stessi criteri escludono.

DECISIONE: la Pull Request torna in annotazione. Va deciso — insieme, e prima di
riscrivere i requisiti — se l'evidenza sostenga un comportamento verificabile o
se #6881 vada riclassificata NOT_EXTRACTABLE.
```
**Passo 4 —** rimandato alla rianotazione qui sotto.

**Requisito unificato (Ground Truth)**

```text
— si veda la rianotazione —
```

### Rianotazione — la discussione

**Che cosa ci siamo detti.** Nessuna delle due formulazioni regge così com'è:
*«esecuzione di codice arbitrario»* (Andrea) e *«risoluzione di entità esterne»*
(Marco) non compaiono nel testo, vengono entrambe da ciò che sappiamo di
`defusedxml` e della classe XXE — §9.2. Ma l'evidenza non è muta: dice che il
contenuto XML-RPC elaborato poteva permettere attacchi all'applicazione e che il
problema è stato risolto. Il comportamento c'è, soltanto in **termini generali**
— e la Decisione 3.1 §9.1 stabilisce che un comportamento sostenuto in termini
generali va scritto in termini generali: il requisito astratto ma fondato è la
risposta corretta, non un ripiego.

**Le scelte, e perché.**

- *«beyond the data it carries»* al posto di «entità esterne» o «esecuzione di
  codice»: è il confine più stretto che possiamo tracciare **senza** nominare la
  classe di vulnerabilità, e rende il divieto osservabile — si dà in pasto al
  sistema un contenuto che tenta un effetto collaterale e si guarda se accade.
- Fuori `defusedxml`, `xmlrpc` e `rpc.py`: sono meccanismo e file (§9.2, removal
  test).
- Fuori *«received from an untrusted source»* (Marco): l'evidenza non distingue
  fra contenuto fidato e non fidato, quindi la condizione restringerebbe il
  requisito senza sostegno.
- Schema **ubiquitous** per il corollario sui divieti (§2.1a): un divieto che
  vale in ogni istante non ha un trigger che lo faccia scattare, e il contesto
  «contenuto XML-RPC» sta già sull'oggetto della risposta.

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
The system shall not allow XML-RPC content it processes to have any effect on
the application beyond the data that content carries.
```

---

## PR #6936 — `scrapy-scrapy-pr-6936` — 2025-07-03

**Evidenza rilevante**

```text
TITOLO: feat(settings): Change default SCHEDULER_PRIORITY_QUEUE (closes #6924)

CORPO:  Changes default `SCHEDULER_PRIORITY_QUEUE` to
        `DownloaderAwarePriorityQueue` (closes #6924).
        […] Confirmed backward compatibility
```

**Le due annotazioni**

| | Andrea | Marco |
|---|---|---|
| Schema EARS | optional feature | unwanted behaviour |
| Requisito | *Where the SCHEDULER_PRIORITY_QUEUE setting has not been overridden, the system shall use DownloaderAwarePriorityQueue as the scheduler priority queue.* | *If the priority queue setting is left to its default, then the system shall schedule requests using a downloader-aware queue.* |

**Passo 1 — Tipo di divergenza:** ☒ D1 ☐ D2 ☐ D3 — il comportamento è identico.

**Passo 2 — Forma**

- Schema derivato dall'evidenza: **optional feature**
- Regola applicata: §2.1d, caso chiuso una volta per tutte — un **cambio di
  valore predefinito** prende `Where … has not been overridden`. Lo `If … then`
  di Marco tratta come **condizione indesiderata** l'assetto predefinito, che è
  invece la configurazione **normale** del sistema: è l'errore descritto in
  §2.1c, la condizione scambiata per un'anomalia.
- Identificatore obbligatorio? ☒ **Sì.** L'evidenza dichiara quale impostazione
  cambia e a quale valore (*«Changes default `SCHEDULER_PRIORITY_QUEUE` to
  `DownloaderAwarePriorityQueue`»*), quindi scatta l'obbligo del §2.2: entrambi
  gli identificatori devono comparire. La prosa di Marco («the priority queue
  setting», «a downloader-aware queue») non permette di stabilire quale
  impostazione lasciare intatta per verificare il requisito.

**Passo 3 — Ampiezza:** non applicabile (nessun D2).

**Passo 4 — Un solo obbligo?** ☒ sì

**Requisito unificato (Ground Truth)**

```text
Where the SCHEDULER_PRIORITY_QUEUE setting has not been overridden, the system
shall use DownloaderAwarePriorityQueue as the scheduler priority queue.
```

---

# Registro delle scelte (sunto del Passo 3)

| PR | Elemento (E) | Scelta | Motivazione sintetica |
|---|---|---|---|
| #6870 | contesto del caricamento di moduli | **tenuto** | enunciato in prosa (*«allows an attacker to load arbitrary code»*), non solo come nome di funzione |
| #6870 | whitelist | **escluso** | rimedio soltanto *suggerito* dall'analizzatore, mai dichiarato applicato |
| #6879 | ambito «generazione di spider» | **tolto** | compare solo nel percorso `genspider.py`: comportamento dedotto da un nome, §9.2 |
| #6880 | momento del rischio: export contro rilettura | **tenuta la rilettura** | *«When unpickling»* è scritto alla lettera; l'export non compare |
| #6880 | formato JSON | **escluso** | rimedio suggerito (*«consider serializing … as JSON»*), non applicato |
| #6881 | esecuzione di codice arbitrario | **tolto** | non enunciato: deriva dalla conoscenza della classe XXE |
| #6881 | risoluzione di entità esterne | **tolto** | non enunciato: stessa origine |
| #6881 | «received from an untrusted source» | **tolto** | non enunciato |
| #6881 | *(rianotazione)* «effetto oltre i dati trasportati» | **aggiunto** | è il confine più stretto tracciabile senza nominare la classe di vulnerabilità; §9.1 ammette il requisito generale quando l'evidenza sostiene solo in generale |

**Come si legge questo registro.** Le nove decisioni si riducono a **quattro
criteri usati sempre nello stesso modo**: (1) un elemento enunciato in prosa si
tiene, un elemento dedotto da un nome si toglie; (2) un rimedio suggerito non è un
rimedio applicato; (3) il momento in cui l'evidenza colloca il fenomeno è parte
del comportamento, non un dettaglio; (4) quando l'evidenza sostiene il
comportamento soltanto in termini generali, il requisito si scrive in termini
generali invece di rinunciarvi. Non ci sono eccezioni una tantum: è il segno che
le regole reggono sul campione.

---

# Tre conseguenze che portiamo nella fase di misura

**1. #6870 e #6879 hanno lo stesso Ground Truth.** L'evidenza è identica byte per
byte, quindi il riferimento deve esserlo. Ne segue un criterio per valutare il
sistema: **produrre due formulazioni con ambiti diversi a partire dalla stessa
evidenza è un'incoerenza**, e va registrata come tale — non come due esiti
indipendenti entrambi corretti.

**2. Su #6881 il Ground Truth è più generale di quello che il sistema ha
prodotto.** Il nostro requisito unificato si ferma a *«any effect beyond the data
that content carries»*; il sistema nomina entità esterne ed esecuzione di codice,
cioè **più di quanto l'evidenza enunci**. Ci serve una regola dichiarata per
questo caso: un requisito **più specifico del riferimento** lo contiamo `MATCH`,
`PARTIAL` o difetto di fedeltà? Sono tre risposte diverse, e la scegliamo prima
di contare.

**3. Lo schema derivato coincide 5 volte su 6 con quello di Andrea.** Non è un
giudizio sugli annotatori: dipende dal fatto che cinque delle sei Pull Request
sono **fix di sicurezza**, e una proprietà di sicurezza formulata come divieto
permanente ricade per costruzione sotto il corollario ubiquitous
(§2.1a). Sul contenuto, invece, il GT segue **Marco** dove l'evidenza gli dà
ragione (#6880, il momento della rilettura). Le regole distribuiscono per caso,
non per persona — ma su un corpus più vario la distribuzione degli schemi sarà
diversa, e non la presentiamo come una proprietà del metodo.

---

# Resoconto — il Ground Truth

Sono i requisiti di riferimento che escono dall'unificazione. Da qui in avanti
sono **questi** — non le nostre due schede separate — a fare da metro per i
requisiti prodotti dal sistema.

## Le sei Pull Request estraibili

| PR | Schema EARS | Requisito di riferimento |
|---|---|---|
| **#6869** | ubiquitous | The system shall not evaluate content originating from outside the program as executable code. |
| **#6870** | ubiquitous | The system shall prevent untrusted user input from causing arbitrary code to be loaded during module import. |
| **#6879** | ubiquitous | The system shall prevent untrusted user input from causing arbitrary code to be loaded during module import. |
| **#6880** | event-driven | When previously serialised item data is read back, the system shall process it without executing any code contained in that data. |
| **#6881** | ubiquitous | The system shall not allow XML-RPC content it processes to have any effect on the application beyond the data that content carries. |
| **#6936** | optional feature | Where the SCHEDULER_PRIORITY_QUEUE setting has not been overridden, the system shall use DownloaderAwarePriorityQueue as the scheduler priority queue. |

**#6870 e #6879 hanno lo stesso requisito**, e deve essere così: la loro evidenza
è identica byte per byte.

Distribuzione degli schemi: *ubiquitous* ×4, *event-driven* ×1, *optional
feature* ×1. Nessuno schema è stato scelto per abitudine: ognuno esce dalla
regola applicata al caso, e la scheda corrispondente dice quale.

## Le tre Pull Request non estraibili

Fanno parte del Ground Truth quanto le altre: la decisione «nessun requisito» è
essa stessa un riferimento con cui il sistema va confrontato.

| PR | Decisione | Perché |
|---|---|---|
| **#6875** | `NOT_EXTRACTABLE` | correzione di refusi in commenti: proprietà del testo sorgente, non comportamento del sistema |
| **#6899** | `NOT_EXTRACTABLE` | modifica di sola tipizzazione statica, con il comportamento a runtime dichiarato invariato |
| **#6947** | `NOT_EXTRACTABLE` | vincolo interno alla codebase (divieto di import), non garanzia del sistema in esecuzione |

## Elenco completo per il confronto

```text
#6869  EXTRACTABLE      The system shall not evaluate content originating from
                        outside the program as executable code.

#6870  EXTRACTABLE      The system shall prevent untrusted user input from
                        causing arbitrary code to be loaded during module import.

#6875  NOT_EXTRACTABLE  —

#6879  EXTRACTABLE      The system shall prevent untrusted user input from
                        causing arbitrary code to be loaded during module import.

#6880  EXTRACTABLE      When previously serialised item data is read back, the
                        system shall process it without executing any code
                        contained in that data.

#6881  EXTRACTABLE      The system shall not allow XML-RPC content it processes
                        to have any effect on the application beyond the data
                        that content carries.

#6899  NOT_EXTRACTABLE  —

#6936  EXTRACTABLE      Where the SCHEDULER_PRIORITY_QUEUE setting has not been
                        overridden, the system shall use
                        DownloaderAwarePriorityQueue as the scheduler priority
                        queue.

#6947  NOT_EXTRACTABLE  —
```

## Che cosa facciamo adesso

Il confronto con l'output del sistema, che è la fase successiva e separata
(Passo 6). Prima di cominciare a contare fissiamo le due regole che l'unificazione
ha fatto emergere: come trattiamo un requisito **più specifico del riferimento**
(§2 delle conseguenze) e come registriamo un'**incoerenza fra Pull Request con
evidenza identica** (§1). Entrambe vanno decise prima, non dopo aver visto i
numeri.
