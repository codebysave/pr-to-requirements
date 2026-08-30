# Scelta dei modelli — cosa abbiamo imparato

**Data:** 27 agosto 2026
**Autori:** Andrea, Marco
**Report grezzi:** `experiments/runs/run-20260827T13*.json`

---

## 0. Di cosa parla questo documento

In una giornata abbiamo lanciato il sistema **cinque volte sullo stesso identico
materiale**: le stesse 9 Pull Request di `scrapy/scrapy`, lo stesso codice, gli
stessi prompt. L'unica cosa che cambiava era **quale modello faceva il
generatore e quale faceva il valutatore**.

Questo documento raccoglie cosa è successo, con gli esempi veri presi dai
report, spiegati in modo che si capiscano rileggendoli fra un mese.

Attenzione a una cosa fin da subito: **non abbiamo ancora il gold standard**.
Quindi quando qui si legge "migliore", vuol dire "a noi sembra più preciso e più
verificabile", non "misurato". Le schede in `experiments/gold-standard/` servono
proprio a trasformare questa impressione in un numero.

---

## 1. I tre modelli, in due righe

| Modello | Costo ingresso | Costo uscita | In parole povere |
|---|---|---|---|
| **Haiku 4.5** | $1 / milione di token | $5 / milione | piccolo, velocissimo, economico |
| **Sonnet 5** | $3 / milione | $15 / milione | intermedio |
| **Opus 5** | $5 / milione | $25 / milione | il più capace, il più caro |

Opus costa **cinque volte** Haiku. Non è un dettaglio: se un giorno il sistema
dovrà girare su migliaia di Pull Request invece che su nove, questo fattore 5
decide se l'esperimento è fattibile.

Listino aggiornato al 26 agosto 2026, scritto in `src/are/llm/pricing.py`.

---

## 2. Il sistema ha due posti dove infilare un modello

```text
Pull Request -> [ GATE ]  ->  [ GENERATORE ]  <->  [ VALUTATORE ]  ->  requisito
                  script          modello 1           modello 2
               (niente LLM)
```

- **Il gate** non usa LLM: è uno script che scarta le Pull Request con corpo
  vuoto o con meno di 50 caratteri fra titolo e corpo. Non entra in questo
  confronto perché si comporta sempre allo stesso modo.
- **Il generatore** legge titolo e corpo e prova a scrivere una frase di
  requisito. Può anche dire "non ci riesco" e spiegare perché.
- **Il valutatore** legge il candidato e decide: `ACCEPT`, `REVISE` (con
  istruzioni di correzione), `REJECT`, oppure `CONFIRM_NOT_EXTRACTABLE` se è
  d'accordo con il rifiuto del generatore.

Se il valutatore dice `REVISE`, si torna dal generatore — fino a 3 tentativi.
**Questo giro si chiama "ciclo di revisione" ed è il cuore del sistema.** Tutto
il resto del documento gira intorno a quando questo ciclo si accende e a cosa
succede quando si accende.

---

## 3. Le cinque prove, in una tabella

| # | Generatore -> Valutatore | Accettati | Non estraibili | Rifiutati | Errori | Revisioni | Chiamate | Costo |
|---|---|---|---|---|---|---|---|---|
| 1 | Haiku -> Haiku | 3 | 6 | 0 | 0 | **5** | 28 | **$0,11** |
| 2 | Haiku -> Opus | 6 | 3 | 0 | 0 | 2 | 22 | $0,46 |
| 3 | Opus -> Sonnet | 6 | 2 | 0 | **1** | **0** | 18 | $0,43 |
| 4 | Opus -> Opus | **7** | 2 | 0 | 0 | **0** | 18 | $0,53 |
| 5 | Sonnet -> Opus | 6 | 2 | 1 | 0 | **3** | 24 | **$0,65** |

Su nove Pull Request, gli esiti vanno da 3 a 7 requisiti accettati. **La scelta
del modello sposta i risultati più di qualunque modifica ai prompt fatta finora.**

---

## 4. Prova per prova, cosa succede davvero

### 4.1 Haiku -> Haiku — il cieco che guida il cieco

Solo 3 requisiti su 9. Sei Pull Request finiscono "non estraibili", comprese
alcune che tutte le altre configurazioni riescono a trattare.

Il problema non è che Haiku sia svogliato: è che **applica i criteri alla
lettera senza capire dove fermarsi**. Il caso più chiaro è la PR #6936, quella
che cambia la coda di priorità di default.

Il generatore scrive:

> *Where the scheduler priority queue has not been overridden, the system shall
> use DownloaderAwarePriorityQueue.*

Il valutatore Haiku applica il "removal test" (togli il nome della classe: se
resta un comportamento, quel nome era un dettaglio implementativo) e chiede di
toglierlo. Il generatore obbedisce e produce:

> *Where the scheduler priority queue setting has not been overridden, the
> system shall apply a default priority queue implementation.*

Il valutatore accetta. Ma leggilo bene: **questa frase non dice niente.** "Se
l'impostazione non è stata cambiata, il sistema applica un'implementazione di
default" è vero per definizione di "default". È una tautologia, e Haiku non se
ne accorge.

Peggio ancora, su #6881 (l'XML-RPC) il ciclo gira **tre volte** e a ogni giro il
requisito si svuota, finché il generatore si arrende. Il valutatore Haiku aveva
scritto:

> *Applica il removal test in modo rigoroso: togliendo i nomi delle librerie e i
> metodi deve restare un comportamento.*

L'istruzione è corretta. Ma applicata senza giudizio porta a smontare qualsiasi
frase fino a non lasciare più niente.

**La lezione:** un valutatore troppo debole non è "permissivo". È *rigido*, e la
rigidità senza giudizio distrugge i requisiti invece di migliorarli.

> **Aggiornamento del 27 agosto (pomeriggio).** Questa lezione va corretta: vale
> su *questo* campione, non su Haiku in generale. Sullo stesso identico codice e
> con gli stessi prompt, ma su un corpus di 46 Pull Request scritte da persone,
> Haiku→Haiku accetta il 74% invece del 33% e il ciclo si accende su 4 casi su 46
> invece di 5 su 9. Non è rigido: **non ha un criterio stabile**, e si lascia
> spingere dalla direzione dell'evidenza. Il §9 riporta la verifica.

### 4.2 Haiku -> Opus — il maestro severo e l'allievo che non sa scrivere

Salto netto: da 3 a 6 requisiti accettati, cambiando **soltanto il valutatore**.
Stesso generatore, stessi prompt.

Opus corregge dove Haiku sbagliava. Su #6869 il generatore scrive "*in the shell
module*" e Opus spiega perché va tolto:

> *Togliendo "in the shell module" resta comunque un comportamento completo,
> quindi il nome del modulo è un dettaglio implementativo individuato dallo
> scanner, non parte del comportamento richiesto.*

Corretto, e il generatore corregge al primo colpo.

Il limite però si vede nella qualità di ciò che esce. Su #6881, dopo la
revisione, il requisito finale è:

> *The system shall prevent malicious XML-RPC inputs from causing attacks.*

Opus lo accetta. Ma "impedire che input malevoli causino attacchi" è quasi
vuoto: non dice *cosa* il sistema debba fare o non fare. Haiku non è capace di
scrivere di meglio, e il valutatore non può scrivere al posto suo — può solo
bocciare, e a un certo punto smette di bocciare.

**La lezione:** un valutatore forte alza il pavimento, non il soffitto. Il
soffitto lo mette il generatore.

### 4.3 Opus -> Sonnet — il maestro più debole dell'allievo

6 accettati, **zero revisioni**. Sonnet accetta tutto quello che Opus scrive al
primo colpo.

Non è per forza sbagliato — i requisiti di Opus sono buoni. Ma il ciclo di
revisione, che è la cosa per cui abbiamo costruito due agenti invece di uno,
**non si accende mai**. Stiamo pagando un secondo modello per un timbro.

Questa è anche l'unica prova con un **errore tecnico**: su #6947 Sonnet ha
scritto una risposta più lunga del limite di `max_tokens = 2048` e il JSON è
arrivato tagliato a metà. Il sistema ha correttamente segnalato `ERROR` invece
di inventare un risultato, ma il limite va alzato.

**La lezione:** se il valutatore è più debole del generatore, il sistema a due
agenti degenera in un sistema a un agente, e paghi il doppio.

### 4.4 Opus -> Opus — il campione che si dà ragione da solo

Il punteggio più alto: **7 accettati su 9**. E anche qui **zero revisioni**:
Opus accetta sempre Opus al primo tentativo.

E qui c'è la cosa più interessante di tutta la giornata. Su #6881 Opus
generatore scrive:

> *When handling XML-RPC data, the system shall process the XML without allowing
> maliciously crafted content to compromise the application.*

E Opus valutatore accetta senza una parola. Ma "*compromise the application*"
è vago esattamente quanto la frase di Haiku del §4.2 — e infatti nella prova
successiva, quando la stessa formulazione arriva da Sonnet, **lo stesso modello
la boccia**. Ci torniamo al §5.2.

**La lezione:** quando generatore e valutatore sono lo stesso modello, il
secondo tende a ratificare il primo. È esattamente il rischio descritto in
Huang et al. 2024 (*Large Language Models Cannot Self-Correct Reasoning Yet*),
che avevamo citato nella Decisione 3.2 come motivo per tenere i due ruoli
separati e configurabili. L'abbiamo visto succedere sui nostri dati.

### 4.5 Sonnet -> Opus — la coppia che funziona

6 accettati, 1 rifiutato, e soprattutto **tre revisioni**, tutte con
miglioramenti veri. È la prova che ci ha insegnato di più.

**Esempio 1 — #6880 (serializzazione): il momento sbagliato.**

Sonnet scrive:

> *The system shall export data without using deserialization methods that could
> execute arbitrary code contained in the data.*

Opus boccia con due argomenti:

> *Il requisito è formulato come divieto di una classe di meccanismi ("senza
> usare metodi di deserializzazione"): se un dato metodo sia usato si può
> verificare solo leggendo il codice sorgente, non osservando il sistema.*
>
> *E attribuisce la garanzia all'export, mentre il rischio che l'evidenza
> descrive si materializza quando i dati serializzati vengono riletti: il momento
> in cui la garanzia vale è indicato in modo impreciso.*

Il secondo punto è **un errore di sostanza, non di forma**: il pericolo non è
nello scrivere il file, è nel rileggerlo. Nessun'altra configurazione se ne era
accorta. Sonnet corregge:

> *If previously serialised item data is read back, then the system shall process
> it without executing any code contained in that data.*

Accettato. Ed è nel pattern EARS giusto (*unwanted behaviour*: `If ... then ...`).

**Esempio 2 — #6881 (XML-RPC): la definizione circolare.**

Sonnet scrive:

> *When processing XML-RPC content, the system shall protect against malicious
> XML input that could compromise the application.*

Opus boccia:

> *L'obbligo è formulato come obiettivo di protezione anziché come comportamento
> osservabile: "proteggere da input XML malevoli che potrebbero compromettere
> l'applicazione" è vicino a "il sistema deve essere sicuro" e non dà nulla da
> verificare a un test black-box.*
>
> *Il qualificatore "che potrebbe compromettere l'applicazione" è circolare:
> definisce l'input attraverso il danno stesso che il requisito dovrebbe
> escludere.*

Quella parola — **circolare** — è la diagnosi esatta. Sonnet corregge:

> *When processing XML-RPC content received from an untrusted source, the system
> shall not execute or resolve any external entities or code embedded within that
> content.*

Accettato. **È il miglior requisito prodotto per quella Pull Request in tutte e
cinque le prove.**

**Esempio 3 — #6947: il primo `REJECT` in assoluto.**

Sonnet scrive "*The system shall prevent modules that import the reactor from
being imported*". Opus non chiede di correggere: rifiuta, e spiega perché non c'è
niente da correggere.

> *L'evidenza descrive una restrizione applicata in fase di sviluppo al codice
> sorgente del progetto, non un comportamento che il sistema in esecuzione
> fornisce a un utente o a un chiamante.*
>
> *Una volta rimossa la prevenzione a runtime non supportata, resta soltanto
> "alcuni import sono stati vietati nel codice", che non stabilisce alcun
> comportamento osservabile.*

Questo è il passo 3 della procedura del prompt applicato alla lettera: togli
quello che l'evidenza non sostiene, guarda cosa resta, e se non resta niente
rifiuta invece di far girare il ciclo a vuoto.

---

## 5. Le tre cose che abbiamo imparato

### 5.1 Il ciclo di revisione si accende solo se c'è un divario

Guarda la colonna "Revisioni" della tabella al §3 e mettila accanto ai modelli:

| Configurazione | Divario | Revisioni | Cosa succede |
|---|---|---|---|
| Haiku -> Haiku | nessuno (entrambi deboli) | 5 | gira a vuoto e peggiora |
| Opus -> Opus | nessuno (entrambi forti) | 0 | non si accende |
| Opus -> Sonnet | negativo | 0 | non si accende |
| Haiku -> Opus | troppo ampio | 2 | si accende ma l'allievo non regge |
| **Sonnet -> Opus** | **giusto** | **3** | **si accende e migliora** |

Il ciclo di revisione **non è gratis e non si accende da solo**. Ha bisogno di un
valutatore capace di vedere un difetto *e* di un generatore capace di capire la
correzione. Se manca uno dei due, stai pagando due modelli per il lavoro di uno.

### 5.2 Lo stesso modello è più severo da giudice che da autore

Questo è il risultato che non ci aspettavamo. La formulazione

> *...without allowing maliciously crafted content to compromise the application*

viene **accettata da Opus** quando è Opus ad averla scritta (§4.4), e **bocciata
da Opus** — con la diagnosi "circolare" — quando la stessa idea arriva da Sonnet
(§4.5).

Non è un bug e non è incoerenza: il valutatore giudica il **candidato**, e nella
prova 4 quel candidato non è mai passato sotto uno sguardo critico, perché chi lo
ha scritto è la stessa istanza che poi doveva criticarlo.

Lo si vede anche su #6947, dove lo stesso valutatore Opus:

- **accetta** la formulazione prudente scritta da Opus (*When a module that is
  prohibited from depending on the Twisted global reactor is imported...*);
- **rifiuta** la formulazione assertiva scritta da Sonnet (*shall prevent modules
  ... from being imported*).

Coerente: giudica la frase che ha davanti, non la Pull Request.

### 5.3 Il modello migliore non fa il sistema migliore

Se conti solo gli accettati, vince Opus -> Opus (7 su 9). Ma se guardi **cosa c'è
scritto** nei requisiti, vince Sonnet -> Opus:

| PR | Opus -> Opus | Sonnet -> Opus |
|---|---|---|
| #6880 | *...shall serialize them in a form that does not allow arbitrary code to be executed when the exported data is later read back* | *If previously serialised item data is read back, then the system shall process it without executing any code contained in that data* |
| #6881 | *...shall process the XML without allowing maliciously crafted content to **compromise the application*** | *...shall not **execute or resolve any external entities or code** embedded within that content* |

**Il risultato del ciclo può superare quello che il modello migliore produce da
solo.** È la tesi di Wang et al. 2025 (*Cross-Refine*, in
`docs/sota/papers/Area 3 - Multi-Agents System/`) verificata sui nostri dati: due
modelli **diversi** che si correggono a vicenda fanno meglio di un modello forte
che si autovaluta.

E questo giustifica a posteriori una scelta di design che avevamo fatto quasi per
igiene: nella Decisione 3.2 il modello è **configurabile per agente** invece di
essere fissato per tutto il sistema. Se avessimo deciso "usiamo il modello
migliore ovunque" non avremmo mai visto questo risultato.

---

## 6. Il costo non segue la qualità

| Configurazione | Costo | Chiamate | $ per requisito accettato |
|---|---|---|---|
| Haiku -> Haiku | $0,11 | 28 | $0,036 |
| Opus -> Sonnet | $0,43 | 18 | $0,071 |
| Opus -> Opus | $0,53 | 18 | $0,075 |
| Haiku -> Opus | $0,46 | 22 | $0,076 |
| Sonnet -> Opus | $0,65 | 24 | $0,108 |

Due osservazioni che sembrano paradossi e non lo sono.

**Haiku -> Haiku fa il maggior numero di chiamate (28) ed è la più economica.**
Perché il numero di chiamate e il costo sono due cose diverse: 28 chiamate a
$1/$5 per milione costano meno di 18 chiamate a $5/$25.

**Sonnet -> Opus è la più cara pur usando Sonnet, che costa meno di Opus.**
Perché le revisioni si pagano due volte: più giri (24 chiamate invece di 18) e,
soprattutto, un valutatore che quando ha qualcosa da correggere **scrive molto di
più**. Opus valutatore ha prodotto 7.633 token di uscita in questa prova contro i
3.644 della prova 4, dove non aveva nulla da dire. Più del doppio.

**In sintesi: la configurazione che produce i requisiti migliori costa il 23% in
più di quella che ne produce di più.** È esattamente il tipo di compromesso che
la Decisione 3.2 (§6) chiede di documentare invece di risolvere a occhio.

---

## 7. Quello che ancora non sappiamo

### 7.1 Non abbiamo un metro

Tutti i giudizi di qualità in questo documento sono nostri. Finché non compiliamo
le schede in `experiments/gold-standard/` — ognuno la sua, **senza guardare gli
output del sistema** — non possiamo dire se Sonnet -> Opus è davvero meglio o se
semplicemente ci piace di più.

È il passo che blocca tutto il resto, e va fatto prima di toccare ancora i
prompt.

### 7.2 Lo stesso modello non dà sempre la stessa risposta

L'SDK ha rimosso i parametri `temperature` e `top_p`, quindi **non possiamo più
chiedere al modello di essere deterministico** (aggiornamento datato nella
Decisione 3.2 §4.4). E si vede:

su #6936 lo stesso valutatore Opus, in due prove diverse, **accetta sia il
requisito che contiene il nome della classe** `DownloaderAwarePriorityQueue`
(prova 2) **sia la sua parafrasi** senza nome di classe (prove 4 e 5). Sono due
livelli di astrazione diversi, entrambi passati.

Non sappiamo se in un'altra esecuzione avrebbe bocciato il nome della classe.
**Con una sola esecuzione per configurazione non possiamo distinguere la
differenza fra modelli dal rumore del singolo campionamento.**

> **Prova diretta, 28 agosto.** Non è più un'ipotesi. Rilanciando Haiku→Haiku
> sulle **prime 5 Pull Request di OpenHands** — stesso modello, stessi prompt,
> stesso input del giorno prima, nessuna modifica al codice fra le due
> esecuzioni — due esiti su cinque sono cambiati:
>
> | PR | 27 agosto | 28 agosto |
> |---|---|---|
> | #9590 (spinner) | `NOT_EXTRACTABLE` | **`ACCEPTED`** |
> | #9591 (dialog) | `REJECTED` | **`NOT_EXTRACTABLE`** |
>
> Il 40% degli esiti si è spostato senza che nulla di osservabile cambiasse.
> Entrambe le Pull Request appartengono al gruppo dei cinque componenti UI del
> §9.3, il che rafforza quella tabella: i quattro esiti diversi su cinque input
> equivalenti non erano un incidente di una singola esecuzione, sono il
> comportamento normale del sistema su quel tipo di evidenza.
>
> Report: `experiments/runs/run-20260828T142024Z.json`.

Conseguenza pratica: la variabilità non si può più sopprimere, **va misurata**,
ripetendo la stessa configurazione più volte. Va nel piano di valutazione
(Decisione 3.7), e con una priorità più alta di quella che gli avevamo dato:
finché non sappiamo quanto è ampia la banda di rumore, **nessun confronto fra
due configurazioni è interpretabile**, comprese le cinque prove del §3.

### 7.3 Non sappiamo se il divario è la causa o una coincidenza

L'idea "serve un divario intermedio" nasce da **una** prova (Sonnet -> Opus) su
**nove** Pull Request. È una spiegazione plausibile, non un risultato. Per
verificarla servirebbe almeno Haiku -> Sonnet, più la ripetizione di
Sonnet -> Opus.

### 7.4 Il campione è piccolo e sbilanciato

Nove Pull Request, di cui **cinque generate da uno scanner automatico di
sicurezza** con lo stesso testo di boilerplate. Non è un campione
rappresentativo: è quello che avevamo per far girare il sistema. Le differenze
fra modelli misurate qui potrebbero non reggere su Pull Request scritte da umani.

> **Aggiornamento del 27 agosto (pomeriggio).** Non "potrebbero": **non
> reggono**. La verifica su un secondo corpus (§9) mostra che il campione sposta
> l'esito più del modello. Le cinque prove di questo documento restano valide
> come confronto *fra loro* — la variabile cambiata era una sola — ma i valori
> assoluti sono legati al campione scrapy e non vanno citati come proprietà dei
> modelli.

### 7.5 Un limite tecnico da alzare

`max_tokens = 2048` per il valutatore è troppo basso: nella prova 3 ha tagliato
una risposta a metà e la Pull Request è finita in `ERROR`. Va portato a 4096.
Non l'abbiamo fatto durante la serie per non rendere le cinque prove
incomparabili fra loro.

---

## 8. Cosa ne ricaviamo, in pratica

**Per le prossime esecuzioni.** Configurazione di riferimento **Sonnet
generatore + Opus valutatore**, perché è l'unica in cui il ciclo di revisione fa
il lavoro per cui l'abbiamo costruito. Haiku -> Haiku resta utile per le prove
tecniche (verificare che la pipeline giri) perché costa un quinto.

> **Aggiornamento del 28 agosto.** Questa raccomandazione va presa come
> un'indicazione operativa provvisoria, non come un risultato. La prova del
> §7.2 mostra che il 40% degli esiti può cambiare fra due esecuzioni identiche:
> con una sola replica per configurazione, differenze di uno o due requisiti su
> nove — cioè quasi tutte quelle della tabella al §3 — rientrano nella banda di
> rumore. Quello che regge è il dato qualitativo: **il numero di revisioni** e
> **la qualità dei requisiti finali**, che sono osservazioni sul comportamento
> del ciclo e non conteggi al margine.

**Per la tesi.** Abbiamo tre osservazioni riproducibili e non ovvie:

1. il ciclo generatore–critico produce valore solo in presenza di un divario di
   capacità fra i due ruoli;
2. lo stesso modello è più severo come critico che come autore, il che è un
   argomento concreto a favore di usare due modelli diversi;
3. la configurazione con il modello più capace ovunque non è la configurazione
   migliore.

**Per la tutor.** Le tre domande da portare al prossimo incontro:

- quante ripetizioni per configurazione servono perché la differenza fra due
  modelli sia distinguibile dal rumore?
- il gold standard va costruito sul comportamento *atteso* o sul requisito
  *scritto meglio*? Sono due metri diversi e finora li abbiamo mescolati.
- ha senso includere nel dataset finale le Pull Request generate da scanner
  automatici, o falsano la misura perché condividono lo stesso boilerplate?

---

## 9. Verifica su un secondo corpus — e cosa ci ha costretto a correggere

*Aggiunto il 27 agosto, pomeriggio. Report:
`experiments/runs/run-20260827T140858Z.json`.*

Le cinque prove dei paragrafi precedenti girano tutte sullo stesso campione. Per
capire quanto contasse il campione, abbiamo lanciato **Haiku→Haiku su un corpus
diverso**: 46 Pull Request di `All-Hands-AI/OpenHands`, scritte da persone,
media 1.422 caratteri fra titolo e corpo. Codice, prompt e modelli identici.

### 9.1 Il corpus conta più del modello

| | scrapy (9 PR) | OpenHands (46 PR) |
|---|---|---|
| Accettati | 3 (33%) | **34 (74%)** |
| Non estraibili | 6 (67%) | 11 (24%) |
| Rifiutati | 0 | 1 |
| PR che entrano nel ciclo | 5 su 9 (55%) | **4 su 46 (8,7%)** |
| Chiamate per PR | 3,1 | 2,26 |
| Costo | $0,11 | $0,38 |

Cambiando **soltanto il corpus**, lo stesso modello passa dal 33% al 74% di
accettazione. È uno scarto più grande di qualunque differenza fra modelli
misurata al §3.

La spiegazione sta nel materiale: su scrapy 5 Pull Request su 9 erano generate da
uno scanner di sicurezza e dicevano «è stata rilevata una vulnerabilità e la
remediation automatica ha applicato le modifiche necessarie» senza mai dire
*quali*. Su un'evidenza così, rifiutare è il comportamento corretto.

**Conseguenza metodologica:** i numeri assoluti delle cinque prove sono una
proprietà del campione, non dei modelli. Il confronto *fra* le cinque prove resta
valido, perché la variabile cambiata era una sola.

### 9.2 I difetti non spariscono, si spostano

Il conteggio migliora, la qualità no. Su OpenHands Haiku accetta cose che i
criteri della Decisione 3.1 escludono:

- **#9601** — *"The system shall use the RuntimeStatus enum for all runtime status
  codes instead of hardcoded strings."* Puro meccanismo: nessun test black-box
  distingue un enum da una stringa. E «instead of hardcoded strings» descrive la
  modifica, non il sistema (§8.2).
- **#9616** — *"When the linter runs, the system shall report an error if it
  detects string literals that have not been localized."* Qui il «sistema» è il
  linter. È una regola di sviluppo, la stessa categoria che Opus aveva rifiutato
  su scrapy #6947. Nella stessa esecuzione, però, **#9639** (upgrade di Node)
  viene correttamente scartato come «parametro di configurazione, non
  comportamento richiesto».
- **#9693** — *"Where a configuration field specifies whether to initialize a git
  repository, the system shall initialize a git repository according to that
  configuration."* Tautologia, stessa forma vuota di `apply a default priority
  queue implementation` (§4.1). Passata al primo colpo, mentre **#9724**, sulla
  stessa funzionalità, viene revisionata e ne esce un requisito preciso.
- **#9661**, **#9633**, **#9634** — contengono «properly» e «correctly», che non
  sono verificabili.
- **#9586** — tre obblighi in una sola frase.

Le **11 rinunce**, invece, sono quasi tutte fondate: template vuoti, aggiornamenti
di metadati, version bump, type hint, fix descritti in modo troppo vago. Ne emerge
un'asimmetria utile: **quando Haiku rifiuta ha quasi sempre ragione, quando
accetta spesso no.** Andrebbe usato come filtro negativo, non come produttore.

### 9.3 L'esperimento naturale: cinque componenti UI

Il corpus contiene cinque Pull Request praticamente identiche — stesso template,
circa 530 caratteri, titolo `feat(ui): <nome> component`. Non l'avevamo
progettato, ma è l'esperimento controllato migliore che abbiamo.

| PR | Componente | Esito | Tentativi |
|---|---|---|---|
| #9590 | spinner | **NOT_EXTRACTABLE** | 1 |
| #9591 | dialog | **REJECTED** | 1 |
| #9632 | toast | **ACCEPTED**, mantiene «toast component» | 1 |
| #9673 | tab | **ACCEPTED**, rimosso «tab component» | 3 |
| #9712 | select | **ACCEPTED**, rimosso «select component» | 3 |

**Cinque input equivalenti, quattro esiti diversi, in un'unica esecuzione.**

E il valutatore si contraddice apertamente. Su **#9591**:

> *Un componente dialog è un blocco costruttivo interno. Il requisito non dice
> cosa utenti o chiamanti vedono fare al sistema.*

Su **#9673**, nello stesso report:

> *Il ragionamento dello scrittore presuppone che la Pull Request debba descrivere
> il comportamento a parole. Non è così: il fatto che un componente tab sia stato
> implementato stabilisce il comportamento per riferimento a ciò che un componente
> del genere fa. Un requisito può essere fondato nella natura dell'artefatto, non
> solo in una descrizione esplicita.*

Le due affermazioni sono incompatibili. E la seconda apre una domanda che **non
abbiamo mai deciso**: *il significato convenzionale di un artefatto nominato conta
come evidenza?* Se sì, «tab component» fonda un requisito; se no, nessuno dei
cinque lo fonda. Il sistema ha risposto in entrambi i modi.

C'è poi un'incoerenza secca e non difendibile: #9632 conserva «toast component»
nel requisito finale, mentre #9673 e #9712 sono stati costretti in due giri a
togliere «tab component» e «select component» perché «nominano il meccanismo».

### 9.4 Il percorso di rinuncia funziona

Tre delle quattro attivazioni del ciclo partono da una **rinuncia del generatore
ribaltata dal valutatore** — la funzionalità aggiunta il 27 agosto mattina. Il
caso migliore è **#9617**: il generatore rinuncia («è un refactoring interno, il
comportamento visibile non cambia»), il valutatore dissente distinguendo il
meccanismo dal comportamento che abilita, e ne esce

> *The system shall present user-facing text in the frontend according to the
> user's language selection or locale.*

È la prima volta che quel percorso produce valore misurabile. Il rovescio è che lo
stesso meccanismo ha prodotto anche i casi discutibili di #9673 e #9712.

### 9.5 Cosa cambia per il piano

1. **Il gold standard va costruito su OpenHands, non su scrapy.** Le schede in
   `experiments/gold-standard/` sono tarate sulle 9 Pull Request sbagliate.
2. **Serve una regola esplicita sui componenti nominati**, in un senso o
   nell'altro. Oggi il sistema decide caso per caso.
3. Le cinque prove del §3 **non vanno ripetute**: hanno già dato quello che
   potevano dare. La domanda successiva non è più «quale modello», è «rispetto a
   quale riferimento».

---

## Appendice — Dove sono i dati

| Prova | File |
|---|---|
| 1. Haiku -> Haiku | `experiments/runs/run-20260827T130351Z.json` |
| 2. Haiku -> Opus | `experiments/runs/run-20260827T131513Z.json` |
| 3. Opus -> Sonnet | `experiments/runs/run-20260827T132820Z.json` |
| 4. Opus -> Opus | `experiments/runs/run-20260827T130619Z.json` |
| 5. Sonnet -> Opus | `experiments/runs/run-20260827T133248Z.json` |

Le cinque prove usano `experiments/samples/sample-scrapy_scrapy.json` (9 PR). La
verifica del §9 usa un campione diverso:

| Verifica | File |
|---|---|
| 6. Haiku -> Haiku su OpenHands (46 PR) | `experiments/runs/run-20260827T140858Z.json` |

Ogni file contiene, per ciascuna Pull Request, tutti i tentativi con il testo del
candidato e il feedback integrale del valutatore. Le citazioni di questo
documento sono tradotte dall'inglese: l'originale è nei report.

Per rifare una prova:

```bash
uv run python -m are --input experiments/samples/sample-scrapy_scrapy.json --generation-model sonnet --assessment-model opus
```
