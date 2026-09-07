# Valutazione complessiva del sistema

**PR-to-Requirements — resoconto sperimentale**
Andrea Saverino · Marco Saverino Salvatore
Università degli Studi di Milano-Bicocca · settembre 2026

---

## 1. Che cosa dimostriamo

Il nostro sistema ricostruisce requisiti funzionali a partire da Pull Request
usando due agenti: un **generatore**, che propone il requisito, e un
**valutatore**, che lo giudica rispetto all'evidenza e può rimandarlo indietro
con istruzioni di correzione.

Nel corso del progetto abbiamo condotto esperimenti, gold standard e prove su
**molti insiemi diversi di Pull Request** — `scrapy/scrapy`, `django/django`,
`All-Hands-AI/OpenHands` — per oltre duecento elaborazioni distribuite su
trentuno esecuzioni registrate. In questo documento portiamo l'analisi in
profondità su un singolo insieme: le **nove Pull Request di `scrapy/scrapy`**,
per le quali abbiamo costruito a mano il riferimento annotato che useremo come
metro di giudizio.

Su quel campione dimostriamo quattro cose:

1. **Un generatore da solo non produce requisiti utilizzabili.** Non è una
   questione di percentuale: **nessuno** dei nove requisiti prodotti in modalità
   *one-shot* supera i criteri obbligatori che ci siamo dati.
2. **Aggiungere un critico che non corregge migliora la diagnosi, non il
   prodotto.** Il critico individua i difetti e li motiva con precisione, ma
   l'insieme dei requisiti in uscita resta identico.
3. **Solo il nostro ciclo di revisione trasforma la diagnosi in correzione.**
   È l'unica delle tre architetture che produce requisiti conformi.
4. **Gli esiti del nostro sistema coincidono con quelli di due annotatori umani
   su tutte e nove le Pull Request**, sia sulla decisione di estraibilità sia sul
   contenuto dei requisiti.

Riferimenti di progetto: Decisione 3.1 (forma e qualità), Decisione 3.5 (ciclo di
revisione), Decisione 3.7 (piano di valutazione).

---

## 2. Il metodo

### 2.1 Il campione e ciò che il sistema vede

Nove Pull Request di `scrapy/scrapy`
(`experiments/samples/sample-scrapy_scrapy.json`). Il sistema riceve **titolo e
corpo, nient'altro**: nessun file sorgente e nessun accesso al
repository. È un vincolo che ci siamo imposti perché è la condizione realistica
in cui un requisito va ricostruito a posteriori.

### 2.2 Il metro di giudizio

Il **gold standard** che abbiamo annotato a mano entrambi, indipendentemente,
sulle stesse nove Pull Request
(`experiments/gold-standard/GS-Scrapy_Scrapy-9_PR/`):

```
ESTRAIBILI      #6869  #6870  #6879  #6880  #6881  #6936      (6)
NON ESTRAIBILI  #6875  #6899  #6947                            (3)
```

I criteri che abbiamo applicato (Decisione 3.1) sono sei, tutti obbligatori:

| # | Criterio | Che cosa richiede |
|---|---|---|
| 1 | **Forma ISO** | inglese, verbo `shall` (non `must`, non `should`) |
| 2 | **Schema EARS** | uno dei cinque: *ubiquitous*, *event-driven*, *state-driven*, *unwanted behaviour*, *optional feature* |
| 3 | **Atomicità** | un solo obbligo per requisito |
| 4 | **Astrazione corretta** | nessun nome di libreria, funzione, modulo o file — salvo quando il cambio di quel meccanismo è esso stesso l'oggetto della Pull Request |
| 5 | **Fedeltà all'evidenza** | nessun elemento che il testo non sostenga |
| 6 | **Verificabilità black-box** | una prova potrebbe fallire prima della modifica e passare dopo, senza leggere il sorgente |

Un requisito è valido solo se li supera **tutti e sei**. È un gate, non un
punteggio: un solo criterio mancato basta a invalidarlo.

### 2.3 Le tre architetture che abbiamo messo a confronto

Le abbiamo eseguite tutte e tre realmente, con gli **stessi modelli**, sullo
stesso campione, cambiando una sola cosa: quanto del meccanismo di controllo è
attivo.

| | Architettura | Come funziona |
|---|---|---|
| **A** | solo generatore | il modello legge la Pull Request e scrive il requisito. |
| **B** | generatore + critico, **senza** ciclo | il critico esamina e motiva, ma le sue osservazioni **non tornano** al generatore |
| **C** | generatore + critico **con ciclo** — *il nostro sistema* | le istruzioni di revisione tornano al generatore, che riscrive; il critico riesamina |

A e B le abbiamo eseguite esternamente al sistema, con gli stessi modelli;
C è la configurazione di riferimento, `run-20260827T133248Z.json` — generatore
`claude-sonnet-5`, valutatore `claude-opus-5`, massimo tre
tentativi per Pull Request.

---

## 3. Architettura A — solo generatore

### 3.1 Che cosa produce

```text
#6869  The system must not use the eval() function to evaluate dynamic content
       from external sources in the scrapy/shell.py file, in order to prevent
       code injection vulnerabilities.

#6870  The system must validate or avoid dynamic values in the
       importlib.import_module() function in scrapy/commands/genspider.py to
       prevent the loading and execution of arbitrary code from untrusted input.

#6875  The source code in the scrapy/cmdline.py file must include grammatically
       correct comments (e.g., using "an argument" instead of "a argument"...)
       to ensure the clarity of internal documentation.

#6879  The system must block the execution of malicious programs by implementing
       a whitelist or avoiding the use of dynamic values in
       importlib.import_module() within scrapy/commands/genspider.py.

#6880  The system must avoid using the pickle library for data processing in
       scrapy/exporters.py, favoring safe, text-based serialization formats
       like JSON to prevent code execution vulnerabilities.

#6881  The system must use the defusedxml.xmlrpc library instead of xmlrpc in
       the scrapy/http/request/rpc.py file to prevent attacks related to unsafe
       XML data processing.

#6899  The system must handle the typing of the dynamic request attribute on
       Failure objects by introducing a dedicated subclass (FailureWithRequest)
       to support static type checkers (e.g., mypy) while keeping runtime
       behavior unchanged.

#6936  The system must set the DownloaderAwarePriorityQueue class as the default
       value for the SCHEDULER_PRIORITY_QUEUE parameter in the default settings
       (default_settings.py).

#6947  The system must ban disallowed imports that include and load the
       twisted.internet.reactor module.
```

### 3.2 Come li giudichiamo rispetto al gold standard

**Decisione di estraibilità: 6 su 9.** Il generatore produce un requisito per
**ognuna** delle nove Pull Request, comprese le tre che abbiamo classificato come
non estraibili.

```
FALSI POSITIVI

#6875   una correzione di refuso in un commento
        → "il codice sorgente deve contenere commenti grammaticalmente corretti"
        Non è un comportamento del sistema: è una proprietà del testo sorgente.
        Nessuna prova black-box potrebbe distinguere il sistema prima e dopo.

#6899   una modifica di sola tipizzazione statica
        → il requisito contiene letteralmente "while keeping runtime behavior
          unchanged". Dichiara da sé la propria non osservabilità.

#6947   un vincolo interno alla codebase
        → "must ban disallowed imports": circolare. Vietati da che cosa?
          Dal divieto stesso.
```

**Conformità formale: nessun requisito la raggiunge.**

| Criterio obbligatorio | Conformi |
|---|:---:|
| 1 — verbo `shall` | **0 / 9** *(tutti usano `must`)* |
| 2 — schema EARS riconoscibile | **0 / 9** |
| 3 — un solo obbligo | 7 / 9 *(#6870 e #6879: «validate **or** avoid»)* |
| 4 — nessun nome di meccanismo | **0 / 9** |
| 5 — fedeltà all'evidenza | 7 / 9 |
| 6 — verificabilità black-box | 6 / 9 |
| **Requisiti che superano tutti e sei** | **0 / 9** |

### 3.3 I due difetti sistematici che abbiamo riscontrato

**Descrive il rimedio, non il comportamento.** Ogni requisito nomina la funzione,
la libreria e il file. Lo verifichiamo con il *removal test*: tolti i nomi, il
requisito #6881 diventa *«il sistema deve prevenire attacchi legati
all'elaborazione non sicura di dati XML»* — cioè *«il sistema deve essere
sicuro»*, un attributo di qualità su cui non si può scrivere una prova. Tolto il
meccanismo, non resta un comportamento.

**Ripete il suggerimento dello strumento come se fosse il rimedio applicato.**
L'evidenza di #6879 *suggerisce* una whitelist; il requisito la **asserisce**.
L'evidenza di #6880 *suggerisce* JSON; il requisito lo **prescrive**. Nessuno dei
due è ciò che la Pull Request dichiara di aver fatto: sono raccomandazioni
dell'analizzatore statico, trasformate in obblighi.

> **Nota su #6870 e #6879.** Le due Pull Request hanno titolo e corpo **identici
> byte per byte**. Il generatore da solo produce due requisiti **diversi**, e il
> secondo è il peggiore dei due perché vi aggiunge la whitelist.

---

## 4. Architettura B — generatore + critico, senza ciclo

### 4.1 Che cosa produce

```text
#6869  The system shall prevent arbitrary code execution from dynamically
       evaluated content through eval() in scrapy/shell.py.

#6870  The system shall prevent arbitrary code loading from untrusted user input
       through importlib.import_module() in scrapy/commands/genspider.py.

#6875  The system shall maintain grammatically correct and clear comments in
       scrapy/cmdline.py without modifying application logic.

#6879  The system shall prevent arbitrary code loading from untrusted user input
       through importlib.import_module() in scrapy/commands/genspider.py.

#6880  The system shall avoid using pickle for data deserialization in
       scrapy/exporters.py and use a safer serialization format such as JSON or
       an equivalent alternative.

#6881  The system shall use defusedxml.xmlrpc instead of xmlrpc for XML-RPC
       processing in scrapy/http/request/rpc.py.

#6899  The system shall provide correct static typing for the dynamically added
       request attribute on Failure objects without changing runtime behavior.

#6936  The system shall use DownloaderAwarePriorityQueue as the default value
       for the SCHEDULER_PRIORITY_QUEUE setting.

#6947  The system shall prevent imports that import twisted.internet.reactor in
       the affected modules.
```

### 4.2 Che cosa dice il critico

Il critico esamina i nove requisiti e li giudica su chiarezza, univocità,
verificabilità, atomicità, necessità e assenza di dettagli implementativi non
necessari. Confrontiamo le sue osservazioni con il nostro gold standard:

| Req | Osservazione del critico (sintesi) | vs gold standard |
|:---:|---|:---:|
| 1 | dettaglio implementativo `eval()`; testabilità da verificare | ✅ corretto |
| 2 | legato all'implementazione; *«untrusted user input»* impreciso | ✅ corretto |
| 3 | **«non è realmente un requisito funzionale»** — manutenzione, non comportamento | ✅ coglie il falso positivo |
| 4 | è un duplicato del Requisito 2, stessa PR e stessa soluzione | ✅ corretto |
| 5 | prescrive la soluzione; *«or an equivalent alternative»* è ambiguo | ✅ corretto |
| 6 | requisito tecnico: dovrebbe definire il comportamento, non la libreria | ✅ corretto |
| 7 | *«correct static typing»* non misurabile; classificazione discutibile | ✅ coglie il falso positivo |
| 8 | requisito di configurazione, non propriamente funzionale | ⚠️ più severo del nostro giudizio |
| 9 | *«the affected modules»* non identifica nulla; troppo generico | ✅ coglie il falso positivo |

**Le osservazioni sono accurate: otto su nove coincidono con il nostro giudizio.**
L'unico scostamento è sul Requisito 8 (#6936), dove il critico è più severo di
noi: lo considera una scelta di configurazione interna, mentre noi lo giudichiamo
estraibile perché il cambio di quel valore predefinito è osservabile dall'esterno.

### 4.3 E tuttavia: nulla cambia

Le nove osservazioni sono corrette, motivate e specifiche. **Ma non tornano al
generatore.** L'insieme dei requisiti in uscita è quello del §4.1, invariato.

| Criterio obbligatorio | A | **B** |
|---|:---:|:---:|
| 1 — verbo `shall` | 0 / 9 | **9 / 9** ✅ |
| 2 — schema EARS riconoscibile | 0 / 9 | 9 / 9 *(tutti ubiquitous; #6936 richiederebbe* `Where`*)* |
| 3 — un solo obbligo | 7 / 9 | 8 / 9 |
| 4 — nessun nome di meccanismo | 0 / 9 | **0 / 9** ❌ |
| 5 — fedeltà all'evidenza | 7 / 9 | 8 / 9 |
| 6 — verificabilità black-box | 6 / 9 | 6 / 9 |
| Falsi positivi | 3 | **3** ❌ |
| **Requisiti che superano tutti e sei** | **0 / 9** | **0 / 9** |

La forma migliora — il verbo `shall` compare ovunque — ma i due difetti
sostanziali restano intatti: **tutti e nove i requisiti nominano ancora il
meccanismo, e i tre falsi positivi sono ancora lì.**

> **È il risultato centrale di questa sezione.** Un critico che osserva senza
> poter correggere produce una **diagnosi accurata** e un **miglioramento del
> prodotto pari a zero** sui criteri che contano. Sa dire che cosa non va;
> non può ripararlo. Il valore di un giudizio sta nell'essere **eseguito**, non
> nell'essere corretto.

---

## 5. Architettura C — il nostro sistema

### 5.1 Che cosa produce

Sulle nove Pull Request il generatore si rifiuta di generare su due (#6875,
#6899), produce sette candidati, e il ciclo interviene su quattro di essi.

```text
#6869  The system shall not evaluate content originating from outside the
       program as executable code.                              (2 tentativi)

#6870  The system shall prevent untrusted user input from causing arbitrary code
       to be loaded and executed during module import.           (1 tentativo)

#6875  — nessun requisito, rifiuto in generazione

#6879  The system shall prevent user-supplied input from causing arbitrary code
       to be loaded and executed when generating a spider.       (1 tentativo)

#6880  If previously serialised item data is read back, then the system shall
       process it without executing any code contained in that data.
                                                                 (2 tentativi)

#6881  When processing XML-RPC content received from an untrusted source, the
       system shall not execute or resolve any external entities or code
       embedded within that content.                             (2 tentativi)

#6899  — nessun requisito, rifiuto in generazione

#6936  Where the scheduler priority queue setting has not been overridden, the
       system shall use the downloader-aware priority queue to schedule
       requests.                                                 (1 tentativo)

#6947  — candidato generato e RIFIUTATO dal critico
```

Nessun nome di libreria o di file. Cinque schemi EARS diversi usati a seconda del
caso. Nessun requisito per le tre Pull Request che non ne contengono.

### 5.2 I quattro interventi del ciclo, uno per uno

**#6869 — un'affermazione che l'evidenza non sostiene**

```
prima    ...as executable code when processing shell input.
         → REVISE, claim non supportato: "when processing shell input"
dopo     The system shall not evaluate content originating from outside the
         program as executable code.                                  ✓ ACCEPT
```

Il critico motiva: *«l'evidenza individua soltanto il file in cui si trova la
chiamata vulnerabile; non dice che cosa sia il contenuto valutato né da dove
provenga»*. Il generatore aveva dedotto il canale d'ingresso dal nome del file.

**#6880 — la direzione del rischio invertita**

```
prima    The system shall export data without using deserialization methods
         that could execute arbitrary code contained in the data.
dopo     If previously serialised item data is read back, then the system shall
         process it without executing any code contained in that data. ✓ ACCEPT
```

Due difetti corretti insieme: il divieto era formulato su una **classe di
meccanismi** anziché su un comportamento, e collocava il pericolo nella scrittura
mentre l'evidenza lo colloca nella **rilettura** (*«when unpickling, the
serialized data could be manipulated to run arbitrary code»*).

**#6881 — un obbligo circolare e non verificabile**

```
prima    ...the system shall protect against malicious XML input that could
         compromise the application.
dopo     When processing XML-RPC content received from an untrusted source, the
         system shall not execute or resolve any external entities or code
         embedded within that content.                                ✓ ACCEPT
```

*«Proteggere da»* non è un comportamento su cui si possa scrivere una prova, e il
qualificatore *«che potrebbe compromettere l'applicazione»* è **circolare**:
definisce l'input attraverso il danno che il requisito dovrebbe escludere.

**#6947 — un requisito che non doveva esistere**

```
candidato  The system shall prevent modules that import the reactor from being
           imported.
           → REJECT, tre claim non supportati:
             · l'effetto di applicazione al momento dell'import
             · l'insieme dei moduli interessati
             · l'esistenza di una garanzia di sistema anziché di una
               convenzione della codebase
           → nessun requisito registrato
```

È il caso in cui il ciclo **non** corregge, e fa bene: la Pull Request descrive
una regola interna al progetto, non un comportamento del sistema in esecuzione.

---

## 6. Le tre architetture a confronto

| | **A** one-shot | **B** con critico, senza ciclo | **C** il nostro sistema |
|---|:---:|:---:|:---:|
| Requisiti emessi | 9 | 9 | **6** |
| Falsi positivi | **3** | **3** | **0** |
| Verbo `shall` | 0 / 9 | 9 / 9 | 6 / 6 |
| Schema EARS appropriato | 0 / 9 | 8 / 9 | **6 / 6** |
| Nominano il meccanismo | 9 / 9 | 9 / 9 | **0 / 6** ¹ |
| Claim non sostenuti | 2 | 1 | **0** |
| **Superano tutti e sei i criteri** | **0 / 9** | **0 / 9** | **6 / 6** |
| Copertura rispetto al gold standard | 0 / 6 | 0 / 6 | **6 / 6** |

¹ *Con l'eccezione legittima di #6936, dove il cambio dell'impostazione nominata è
esso stesso l'oggetto della Pull Request.*

**Da A a B il prodotto non migliora.** Migliora la forma superficiale — compare
il verbo `shall` — e nasce una diagnosi accurata. Ma i falsi positivi restano
tre, i nomi di meccanismo restano nove su nove, e i requisiti conformi restano
**zero**.

**Da B a C il prodotto cambia natura.** Le stesse osservazioni che in B restavano
sulla carta diventano istruzioni eseguite: i tre falsi positivi spariscono, i
nomi di meccanismo spariscono, e sei requisiti su sei superano tutti i criteri.

> Il salto di qualità non si ha tra A → B. **Si ha tra B → C.** Il critico serve a poco se non può
> rimandare indietro il lavoro.

---

## 7. Il confronto con il gold standard

### 7.1 Come lo abbiamo costruito

Ciascuno di noi due ha compilato la propria scheda sulle stesse nove Pull
Request, con la sola evidenza sotto gli occhi, applicando i criteri della
Decisione 3.1. Le due schede sono risultate **distinte nel contenuto**: requisiti
formulati diversamente e, sistematicamente, schemi EARS diversi.

```
Andrea   ubiquitous ×5,  optional feature ×1
Marco    event-driven ×3,  state-driven ×1,  unwanted behaviour ×2
```

### 7.2 Il nostro accordo come annotatori

| | Valore |
|---|---|
| Stessa decisione di estraibilità | **9 / 9** |
| Corrispondenza semantica fra i due requisiti | 5 MATCH · 1 PARTIAL · 0 NO_MATCH |

L'unico scostamento lo abbiamo avuto sulla sulla **PR #6881**: Uno di noi limita il requisito alle entità
esterne, mentre l'altro copre anche l'esecuzione di codice. È una differenza di
**ampiezza dello scope**, non di correttezza.

### 7.3 L'accordo fra il nostro sistema e noi

| PR | Esito sistema | Tent. | vs Andrea | vs Marco | Qualità |
|---|:---:|:---:|:---:|:---:|:---:|
| #6869 | ACCEPTED | 2 | MATCH | MATCH | 12/12 |
| #6870 | ACCEPTED | 1 | MATCH | MATCH | 12/12 |
| #6875 | NOT_EXTRACTABLE | 1 | concorde | concorde | — |
| #6879 | ACCEPTED | 1 | PARTIAL | MATCH | 12/12 |
| #6880 | ACCEPTED | 2 | MATCH | MATCH | 12/12 |
| #6881 | ACCEPTED | 2 | MATCH | PARTIAL | 12/12 |
| #6899 | NOT_EXTRACTABLE | 1 | concorde | concorde | — |
| #6936 | ACCEPTED | 1 | MATCH | MATCH | 12/12 |
| #6947 | REJECTED | 1 | concorde | concorde | — |

| Metrica | Valore |
|---|---|
| Accuratezza sulla decisione di estraibilità | **9 / 9** |
| Corrispondenza semantica *(sistema vs due annotatori)* | **10 MATCH · 2 PARTIAL · 0 NO_MATCH** |
| Requisiti che superano il gate obbligatorio | **6 / 6** |
| Quality score medio sui requisiti accettati | **12 / 12** |
| Falsi positivi | **0** |
| Falsi negativi | **0** |

### 7.4 Correttezza sintattica e semantica, separate

La domanda «i requisiti sono corretti?» si scompone in due, e i nostri dati
rispondono separatamente.

**Sintattica** — la forma è conforme alla Decisione 3.1. Coperta dai criteri
*Atomic*, *Unambiguous*, *Verifiable* e *Correct abstraction*: **6 su 6 li
superano tutti**. Ogni requisito accettato usa uno dei cinque schemi EARS, il
verbo `shall`, e contiene un solo obbligo.

**Semantica** — il requisito descrive il comportamento che l'evidenza sostiene.
La misuriamo con la corrispondenza rispetto alle nostre annotazioni: **10 MATCH
su 12 confronti**, 2 PARTIAL, **nessun NO_MATCH**. In nessun caso il sistema ha
formalizzato un comportamento diverso da quello che avevamo individuato noi.

### 7.5 I due scostamenti fra il nostro sistema e noi

**#6879.** I corpi di #6870 e #6879 sono identici byte per byte. Il sistema
produce due formulazioni con ambiti diversi (*«during module import»* contro
*«when generating a spider»*): entrambe corrette rispetto all'evidenza, la
seconda più ristretta. Marco aveva ristretto allo stesso modo, Andrea no — da cui
il PARTIAL.

**#6881.** Il sistema produce il **superset** delle nostre due letture: copre sia
le entità esterne (Marco) sia l'esecuzione di codice incorporato (Andrea).
Formalmente è il requisito più completo dei tre — ed è la Pull Request su cui
anche noi due divergiamo.

---

## 8. Perché le combinazioni di modelli cambiano gli esiti

Abbiamo eseguito cinque configurazioni sullo stesso campione, con gli stessi
prompt e lo stesso codice. **L'unica variabile che abbiamo cambiato è quale
modello occupa quale ruolo:**

| Generatore → Valutatore | Accettati | Revisioni | Costo |
|---|:---:|:---:|---:|
| Haiku → Haiku | 3 | 5 | $0,11 |
| Haiku → Opus | 6 | 2 | $0,46 |
| Opus → Sonnet | 6 | 0 | $0,43 |
| Opus → Opus | 7 | 0 | $0,53 |
| **Sonnet → Opus** | **6** | **3** | $0,65 |

La colonna **Revisioni** non cresce con la capacità dei modelli: ha un massimo
**intermedio**. È il dato da cui parte la nostra spiegazione.

### 8.1 Il ciclo richiede un divario, non due modelli potenti

Perché il ciclo produca un miglioramento servono **due capacità distinte in due
posti diversi**: un valutatore capace di individuare il difetto, e un generatore
capace di applicare la correzione. Se manca l'una o l'altra, si pagano due
modelli per il lavoro di uno.

| Configurazione | Divario | Revisioni | Effetto |
|---|---|:---:|---|
| Haiku → Haiku | nullo, entrambi deboli | 5 | gira a vuoto e **impoverisce** |
| Opus → Opus | nullo, entrambi forti | 0 | **non si attiva** |
| Opus → Sonnet | negativo | 0 | non si attiva |
| Haiku → Opus | ampio | 2 | si attiva, ma il generatore non regge |
| **Sonnet → Opus** | **intermedio** | **3** | **si attiva e migliora** |

Con due modelli deboli il ciclo non è soltanto inefficace: è **dannoso**. Su una
Pull Request il valutatore Haiku ha chiesto tre revisioni successive e il
requisito si è progressivamente svuotato fino a una tautologia — *«Where the
scheduler priority queue setting has not been overridden, the system shall apply
a default priority queue implementation»*, una frase vera per definizione di
«default».

### 8.2 Lo stesso modello è più severo come critico che come autore

Nella configurazione **Opus → Opus** il modello ha accettato senza obiezioni:

> *When handling XML-RPC data, the system shall process the XML without allowing
> maliciously crafted content to **compromise the application**.*

Nella configurazione **Sonnet → Opus**, lo **stesso modello** in ruolo di
valutatore ha respinto la medesima idea proveniente da Sonnet, definendo il
qualificatore **circolare** (§5.2).

Non è incoerenza: il valutatore giudica **il candidato che riceve**, e nel primo
caso quel candidato non era mai passato sotto uno sguardo esterno — a produrlo era
la stessa istanza che avrebbe dovuto criticarlo.

È il fenomeno descritto da **Huang et al. (2024)**, *Large Language Models Cannot
Self-Correct Reasoning Yet*, che abbiamo osservato direttamente sui nostri dati.
Motiva la scelta della Decisione 3.2 §4.2 di rendere il modello configurabile
**per agente** anziché fissarlo per l'intero sistema.

### 8.3 Il ciclo supera ciò che il modello migliore produce da solo

Contando i soli requisiti accettati vincerebbe Opus → Opus (sette su nove).
Esaminando il **testo**, Sonnet → Opus li produce migliori:

| PR | Opus → Opus | Sonnet → Opus |
|---|---|---|
| #6881 | *…without allowing maliciously crafted content to **compromise the application*** | *…shall not **execute or resolve any external entities or code** embedded within that content* |

È la tesi di **Wang et al. (2025)**, *Cross-Refine*, che verifichiamo su questo
campione: due modelli **diversi** che si correggono a vicenda ottengono un
risultato migliore di un modello forte che si autovaluta. E colloca il nostro
sistema rispetto a **Madaan et al. (2023)**, *Self-Refine*, che proponeva il ciclo
con un solo modello: i nostri dati indicano che la separazione dei ruoli fra
modelli diversi non è un dettaglio realizzativo, è **la condizione perché il ciclo
funzioni**.

### 8.4 Perché un modello meno capace applica peggio le stesse regole

I due agenti ricevono **le stesse identiche istruzioni**, qualunque sia il
modello. La differenza di comportamento non può quindi dipendere dal prompt. Ma dal capire quando applicare o meno quelle regole descritte nel prompt.

**Non dalla conoscenza della regola.** Se interrogato, anche il modello più
piccolo la ripete correttamente. 

**Dipende dal riconoscere quando la regola si applica.** Ed è un'operazione
diversa dal conoscerla: richiede di confrontare il caso che si ha davanti con il
caso per cui la regola è stata scritta, e decidere se la *ragione* della regola
vale ancora.

Il modello meno capace decide questo confronto sulla **forma superficiale**;
quello più capace sulla **ragione sottostante**. Lo abbiamo osservato con
precisione su un caso.

> **La regola.** *Il significato convenzionale di un artefatto nominato non è
> evidenza.* Serve a impedire che da *«implementa il componente tab»* si ricavi un
> requisito: il comportamento verrebbe da ciò che il lettore sa dei *tab*, non dal
> testo della Pull Request.
>
> **L'errore.** Il valutatore Haiku ha applicato quella regola alle Pull Request
> di sicurezza, rifiutandole con la motivazione che *«qualunque requisito
> ripeterebbe il significato del nome di una tecnica»*.
>
> **Perché è un errore.** Quelle Pull Request **non contengono solo un nome**:
> descrivono il problema in prosa — *«eval() can be dangerous if used to evaluate
> dynamic content… this may be a code injection vulnerability»*. L'evidenza c'è,
> scritta. Haiku ha riconosciuto la forma *«qui compare un termine tecnico»* e ha
> fatto scattare la regola, senza verificare la condizione che la giustifica —
> cioè che il nome sia **l'unica** cosa presente.

Sulle stesse nove Pull Request:

| | Haiku | Sonnet |
|---|:---:|:---:|
| PR rifiutate perché *«conosceremmo il meccanismo solo dal nome»* | **4** | **0** |

**Sonnet non ha commesso l'errore su nessuna delle nove.**

Da qui la conseguenza pratica più importante che abbiamo ricavato: **un prompt più
dettagliato non compensa un modello meno capace.** Ogni regola che si aggiunge dà
al modello debole un'occasione in più di applicarla fuori luogo. Riformulare il
prompt e cambiare modello non sono interventi intercambiabili: il primo agisce
sulla conoscenza della regola, che non è il vero problema; il secondo sulla
capacità di collocarla, che lo è.

---

## 9. Conclusioni

### 9.1 Le tre architetture non sono tre gradi dello stesso risultato

Il dato che riteniamo più significativo è che il salto di qualità **non è
graduale**. Le prime due architetture producono lo stesso identico risultato
misurabile — **zero requisiti conformi su nove** — pur essendo una il doppio
dell'altra in termini di componenti e di costo.

```
A  generatore                          0 / 9 conformi
B  generatore + critico                0 / 9 conformi
C  generatore + critico + ciclo        6 / 6 conformi
```

Aggiungere il critico raddoppia il costo e non cambia il prodotto. Solo la
**restituzione del giudizio al generatore** produce un salto, e quando lo produce
è totale.

Questo ci porta a una formulazione più forte di quella da cui eravamo partiti:
**in un'architettura generatore–critico il valore non sta nel giudizio, sta nella
sua esecuzione.** Un giudizio accurato che non torna indietro è un documento, non
un meccanismo di controllo.

### 9.2 Che cosa fa esattamente il ciclo, e quanto spesso

Il ciclo interviene su **quattro dei sette candidati** — più della metà del
materiale prodotto. Non è un componente di riserva che si attiva nei casi limite:
è il percorso ordinario.

| Difetto intercettato | PR | Esito |
|---|---|---|
| affermazione non sostenuta dall'evidenza | #6869 | corretto |
| direzione del rischio invertita | #6880 | corretto |
| obbligo circolare e non verificabile | #6881 | corretto |
| requisito estratto da materiale non estraibile | #6947 | bloccato |

I tre requisiti corretti al secondo tentativo **sarebbero entrati nel catalogo (ovvero nel DB)
così com'erano** in qualunque architettura senza ciclo. Il quarto non sarebbe mai
dovuto esistere, e nelle architetture A e B esiste.

### 9.3 Il sistema decide quasi allo stesso modo di un ingegnere dei requisiti

Sulle nove Pull Request il nostro sistema arriva **sempre** all'esito a cui
arriviamo noi due: o un requisito valido, o nessun requisito.

```
Accuratezza sulla decisione di estraibilità     9 / 9
Falsi positivi                                  0
Falsi negativi                                  0
```

Non ha mai formalizzato un comportamento dove non ce n'era — l'errore in cui
l'architettura A cade tre volte su nove — e non ha mai rifiutato una Pull Request
da cui un comportamento si poteva ricavare.

### 9.4 I requisiti sono corretti nella forma e nel contenuto

Le due cose vanno misurate separatamente, e i nostri dati le separano.

**Nella forma** — tutti e sei i requisiti accettati usano il verbo `shall`, uno
dei cinque schemi EARS, contengono un solo obbligo, e non nominano alcun
meccanismo salvo dove il cambio di quel meccanismo è l'oggetto della Pull
Request. **6 su 6 superano tutti e sei i criteri obbligatori**, con quality score
12 su 12.

**Nel contenuto** — su dodici confronti fra i requisiti del sistema e i nostri,
**dieci sono corrispondenze piene, due parziali, nessuna discordante**. I due
parziali non sono errori: sono differenze di **ampiezza dello scope** su cui anche
noi due annotatori non coincidiamo.

Vale la pena sottolineare che il sistema riscrive con parole proprie: nessuno dei
sei requisiti è la copia di uno dei nostri, eppure descrivono lo stesso
comportamento. **La corrispondenza è semantica, non testuale** — che è esattamente
ciò che ci aspettiamo da un sistema che ricostruisce requisiti anziché ricopiarli.

### 9.5 La scelta dei modelli è parte dell'architettura

A parità di prompt e di codice, la stessa pipeline produce **da tre a sette
requisiti** a seconda di quale modello occupa quale ruolo.  

Le regole che ne ricaviamo sono tre.

**Il ciclo si attiva solo in presenza di un divario di capacità** fra generatore e
valutatore. Con due modelli identici non scatta — il modello ratifica il proprio
output — e con due modelli entrambi deboli scatta ma degrada il requisito.

**Il modello più capace va nel ruolo di valutatore.** È il ruolo in cui la
capacità di riconoscere quando una regola si applica fa la differenza, ed è quella
la capacità che separa le fasce (§8.4).

**Un prompt migliore non sostituisce un modello migliore.** Aggiungere regole
aumenta le occasioni di applicarle fuori luogo: sul modello debole il prompt più
dettagliato peggiora il risultato invece di migliorarlo.

### 9.6 In sintesi

Sulle nove Pull Request di `scrapy/scrapy`, con il gold standard che abbiamo
annotato a mano come metro di giudizio:

> **Il nostro sistema è l'unica delle tre architetture a produrre requisiti
> funzionali validi.** Le altre due — il generatore da solo e il generatore
> affiancato da un critico che osserva senza correggere — ne producono **zero**.
>
> I sei requisiti che il sistema accetta sono **corretti nella forma** (6/6 sui
> criteri obbligatori) e **corretti nel contenuto** (10 corrispondenze piene su
> 12, nessuna discordanza con due annotatori umani).
>
> Il sistema **decide come decidiamo noi** su tutte e nove le Pull Request, senza
> falsi positivi né falsi negativi.

---

## Riferimenti

**Documenti di progetto.** Decisione 3.1 (forma e qualità dei requisiti),
Decisione 3.2 (scelta del modello), Decisione 3.5 (ciclo di revisione),
Decisione 3.7 (piano di valutazione).
`experiments/gold-standard/GS-Scrapy_Scrapy-9_PR/confronto-annotazioni_Scrapy.md`
per il confronto integrale Pull Request per Pull Request;
`experiments/analisi/confronto-modelli.md` per l'analisi estesa delle cinque
configurazioni; `experiments/runs/` per i report completi delle esecuzioni.

**Letteratura.**

- Huang, J. et al. (2024). *Large Language Models Cannot Self-Correct Reasoning
  Yet.* ICLR 2024.
- Wang, Q. et al. (2025). *Cross-Refine: Improving Natural Language Explanation
  Generation by Learning in Tandem.* COLING 2025.
- Madaan, A. et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.*
  NeurIPS 2023.
- Mavin, A. et al. (2009). *EARS (Easy Approach to Requirements Syntax).* RE'09.
- ISO/IEC/IEEE 29148:2018 — *Systems and software engineering — Life cycle
  processes — Requirements engineering.*
- Donato, B. et al. (2025b), sulla variabilità fra repliche della stessa richiesta
  a un modello linguistico.
