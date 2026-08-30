# La scelta del modello linguistico

**Materiale per la tesi — bozza di capitolo**
Progetto PR4Requirements · Andrea Saverino, Marco Saverino Salvatore
Università degli Studi di Milano-Bicocca · agosto 2026

---

## 1. Scopo di questo documento

PR4Requirements è costruito attorno a due agenti che sono, tecnicamente, due
modelli linguistici con istruzioni diverse. La scelta di *quale* modello mettere
in ciascuno dei due posti non è un dettaglio implementativo: come mostrano i dati
raccolti, sposta gli esiti del sistema più di qualunque altra modifica fatta
finora.

Questo documento raccoglie in un unico posto le nozioni necessarie a motivare
quella scelta e i risultati sperimentali su cui la scelta si appoggia. È pensato
come base per il capitolo corrispondente della tesi: la parte concettuale (§2–§5)
serve a definire i termini, la parte sperimentale (§6–§9) riporta i dati.

I riferimenti di progetto sono la **Decisione 3.2** (scelta del modello) e la
**Decisione 3.7** (piano di valutazione). Tutti i report citati sono in
`experiments/runs/`.

---

## 2. Dove gira il modello: locale o servizio remoto

La prima distinzione non riguarda la qualità del modello ma **dove viene
eseguito**.

### 2.1 Modello locale

Il modello viene scaricato ed eseguito sulla macchina di chi lo usa. I *pesi* —
i parametri numerici che costituiscono il modello, decine o centinaia di miliardi
di valori — risiedono su disco e vengono caricati in memoria a ogni utilizzo.

**Vantaggi.** Nessun costo per singola richiesta: una volta scaricato, il modello
si usa quanto si vuole. Nessun dato esce dalla macchina, il che conta quando si
elaborano informazioni riservate. E soprattutto **riproducibilità nel tempo**: un
modello scaricato oggi sarà identico fra un anno, perché nessuno può aggiornarlo
a nostra insaputa.

**Svantaggi.** Richiede hardware adeguato: i modelli di dimensioni interessanti
necessitano di schede grafiche con molta memoria dedicata, che nessuno dei due
computer usati per questo progetto possiede. I modelli eseguibili su hardware
comune sono sensibilmente meno capaci di quelli offerti come servizio. E l'onere
di installazione, aggiornamento e manutenzione ricade su chi sviluppa.

### 2.2 Servizio remoto

Il modello risiede sui server del fornitore. Il programma invia il testo
attraverso un'interfaccia di rete e riceve la risposta. È la modalità adottata in
questo progetto.

**Vantaggi.** Nessun requisito hardware; accesso ai modelli più capaci
disponibili; nessuna manutenzione.

**Svantaggi.** Ogni richiesta ha un costo; i dati transitano presso terzi; e il
fornitore può modificare o ritirare un modello. Quest'ultimo punto ha avuto una
conseguenza concreta su questo progetto ed è documentato al §10.

---

## 3. Aperto o proprietario, gratuito o a pagamento

Sono due distinzioni indipendenti che vengono spesso confuse.

### 3.1 Modelli aperti e modelli proprietari

Un modello si dice **aperto** quando i pesi sono pubblicamente scaricabili
(Llama di Meta, Mistral, Qwen di Alibaba, Gemma di Google). Chiunque può
eseguirlo sulla propria macchina, studiarlo e modificarlo. «Aperto» non significa
sempre «libero da vincoli»: le licenze variano e alcune limitano l'uso
commerciale.

Un modello è **proprietario** quando i pesi non vengono distribuiti e l'unico
modo di usarlo è attraverso il servizio del fornitore (GPT di OpenAI, Claude di
Anthropic, Gemini di Google). Non si può ispezionare, né eseguire altrove, né
conservare una copia.

### 3.2 Gratuito non significa senza costo

Un modello aperto eseguito localmente **non costa per richiesta**, ma costa in
hardware, energia e tempo di configurazione. Per un progetto che deve elaborare
poche centinaia di Pull Request, l'acquisto o il noleggio di una macchina adatta
supera ampiamente la spesa in chiamate a un servizio: l'intera fase sperimentale
di questo progetto è costata **meno di cinque dollari** (§9).

I fornitori di servizi offrono a volte piani gratuiti, ma con limiti di velocità
stretti e senza garanzie di stabilità: adatti a una prova, non a una serie
sperimentale che deve essere ripetibile.

### 3.3 La combinazione realmente disponibile

Le quattro combinazioni non sono equiprobabili nella pratica:

| | Locale | Servizio remoto |
|---|---|---|
| **Aperto** | scenario tipico: Llama, Mistral su hardware proprio | possibile: fornitori che ospitano modelli aperti |
| **Proprietario** | non disponibile | scenario tipico: GPT, Claude, Gemini |

---

## 4. La scelta compiuta e le sue ragioni

Il progetto usa **modelli proprietari della famiglia Claude, accessibili come
servizio remoto** (Anthropic). Le ragioni, in ordine di peso.

**Il vincolo del progetto.** La proposta di stage richiede che il database sia
accessibile agli agenti tramite **MCP** (*Model Context Protocol*), lo standard
introdotto da Anthropic per esporre capacità ai modelli. Lavorare nell'ecosistema
in cui MCP nasce riduce l'attrito realizzativo su una componente che la proposta
indica come centrale.

**L'hardware disponibile.** Nessuna delle macchine del progetto può eseguire
localmente un modello di capacità paragonabile. La qualità del ragionamento
richiesto ai due agenti — riconoscere se una frase afferma più di quanto
l'evidenza sostenga — non è un compito su cui un modello piccolo eseguito in
locale sia competitivo, come mostrano indirettamente i risultati del §8.

**La possibilità di confrontare fasce diverse.** Un unico fornitore offre più
modelli con la stessa interfaccia. Cambiare fascia è un parametro di
configurazione, non una riscrittura: è ciò che ha reso possibile l'esperimento
descritto al §7.

**La reversibilità della scelta.** La Decisione 3.2 §4.3 impone un livello di
astrazione fra gli agenti e il fornitore. Nel codice, gli agenti dipendono da
un'interfaccia (`LLMClient`) e non dall'SDK: introdurre un modello aperto
richiederebbe una nuova implementazione di quell'interfaccia, non modifiche agli
agenti. La scelta è quindi motivata ma non irreversibile.

---

## 5. I modelli all'interno della famiglia

Anthropic organizza i modelli in tre fasce, disponibili contemporaneamente e con
la stessa interfaccia.

| Fascia | Prezzo ingresso | Prezzo uscita | Posizionamento |
|---|---|---|---|
| **Haiku** | $1 / milione di token | $5 / milione | rapido ed economico |
| **Sonnet** | $3 / milione | $15 / milione | intermedio |
| **Opus** | $5 / milione | $25 / milione | il più capace |

*Listino al 26 agosto 2026, riportato in `src/are/llm/pricing.py`.*

Il prezzo si applica ai **token**, l'unità in cui il testo viene suddiviso — un
token corrisponde grossomodo a tre quarti di parola in inglese. Il testo prodotto
dal modello costa **cinque volte** quello ricevuto: è la ragione per cui un
agente che argomenta a lungo pesa sul costo molto più di uno che risponde con una
frase, come si vede al §9.

Fra Haiku e Opus corre un fattore **cinque** sul prezzo. Non è un dettaglio: su
un corpus di poche decine di Pull Request è irrilevante, su migliaia decide se
l'esperimento sia realizzabile.

---

## 6. Il metodo dell'esperimento

Per rendere confrontabili le configurazioni è stata cambiata **una sola
variabile**: quale modello occupa il ruolo di generatore e quale quello di
valutatore.

Restano fissi: il campione (9 Pull Request del repository `scrapy/scrapy`), i
prompt di sistema dei due agenti, il codice, la configurazione del workflow, il
numero massimo di tentativi. Ogni esecuzione registra il modello nella sua
versione datata, il consumo di token e il costo stimato.

Le esecuzioni citate sono del 27 agosto 2026 e si trovano in
`experiments/runs/run-20260827T13*.json`.

**Un limite dichiarato in partenza.** Ogni configurazione è stata eseguita **una
sola volta**. Il §10 mostra che la variabilità fra esecuzioni identiche è
tutt'altro che trascurabile: le differenze di uno o due requisiti riportate nella
tabella che segue vanno quindi lette con prudenza, mentre reggono le osservazioni
di natura qualitativa.

---

## 7. Risultati: cinque configurazioni a confronto

| Generatore → Valutatore | Accettati | Non estraibili | Rifiutati | Errori | Revisioni | Costo |
|---|---|---|---|---|---|---|
| Haiku → Haiku | 3 | 6 | 0 | 0 | 5 | $0,11 |
| Haiku → Opus | 6 | 3 | 0 | 0 | 2 | $0,46 |
| Opus → Sonnet | 6 | 2 | 0 | 1 | 0 | $0,43 |
| Opus → Opus | 7 | 2 | 0 | 0 | 0 | $0,53 |
| Sonnet → Opus | 6 | 2 | 1 | 0 | 3 | $0,65 |

Su nove Pull Request gli esiti vanno da tre a sette requisiti accettati. Tre
osservazioni emergono dai dati.

### 7.1 Il ciclo di revisione si attiva solo in presenza di un divario

La colonna «Revisioni» conta quante volte il valutatore ha rimandato indietro un
candidato. Accostata ai modelli, mostra un andamento non monotono:

| Configurazione | Divario di capacità | Revisioni | Effetto |
|---|---|---|---|
| Haiku → Haiku | nullo, entrambi deboli | 5 | gira a vuoto e impoverisce |
| Opus → Opus | nullo, entrambi forti | 0 | non si attiva |
| Opus → Sonnet | negativo | 0 | non si attiva |
| Haiku → Opus | ampio | 2 | si attiva, ma il generatore non regge |
| **Sonnet → Opus** | **intermedio** | **3** | **si attiva e migliora** |

Il ciclo generatore–critico, che è la ragione per cui il sistema ha due agenti
invece di uno, **non si attiva da solo**. Richiede un valutatore capace di
individuare un difetto *e* un generatore capace di applicare la correzione. Se
manca uno dei due, si pagano due modelli per il lavoro di uno.

Con due modelli deboli il ciclo non solo è inefficace, è dannoso: su una Pull
Request il valutatore ha chiesto tre revisioni successive e il requisito si è
progressivamente svuotato fino a una tautologia — *«Where the scheduler priority
queue setting has not been overridden, the system shall apply a default priority
queue implementation»*, una frase vera per definizione di «default».

### 7.2 Lo stesso modello è più severo come critico che come autore

Nella configurazione Opus → Opus il modello ha accettato senza obiezioni la
formulazione:

> *When handling XML-RPC data, the system shall process the XML without allowing
> maliciously crafted content to **compromise the application**.*

Nella configurazione Sonnet → Opus, lo **stesso modello** in ruolo di valutatore
ha respinto la medesima idea proveniente da Sonnet, con questa motivazione:

> *L'obbligo è formulato come obiettivo di protezione anziché come comportamento
> osservabile (…). Il qualificatore «che potrebbe compromettere l'applicazione» è
> **circolare**: definisce l'input attraverso il danno stesso che il requisito
> dovrebbe escludere.*

Non è incoerenza: il valutatore giudica il **candidato**, e nel primo caso quel
candidato non era mai passato sotto uno sguardo critico, perché a produrlo era la
stessa istanza che avrebbe dovuto criticarlo.

È il fenomeno descritto da **Huang et al. (2024)**, *Large Language Models Cannot
Self-Correct Reasoning Yet*, osservato sui dati di questo progetto, e costituisce
l'argomento più concreto a favore di **due modelli distinti** nei due ruoli.

### 7.3 La configurazione con il modello migliore non è la migliore

Contando i soli requisiti accettati vince Opus → Opus (sette su nove). Esaminando
il **testo** dei requisiti finali, la configurazione Sonnet → Opus li produce
migliori:

| PR | Opus → Opus | Sonnet → Opus |
|---|---|---|
| #6880 | *…shall serialize them in a form that does not allow arbitrary code to be executed when the exported data is later read back* | *If previously serialised item data is read back, then the system shall process it without executing any code contained in that data* |
| #6881 | *…shall process the XML without allowing maliciously crafted content to **compromise the application*** | *…shall not **execute or resolve any external entities or code** embedded within that content* |

Il risultato del ciclo può quindi **superare quello che il modello più capace
produce da solo**, purché esista un divario che lo attivi. È la tesi di **Wang et
al. (2025)**, *Cross-Refine*, verificata su questo campione: due modelli
**diversi** che si correggono a vicenda ottengono un risultato migliore di un
modello forte che si autovaluta.

Questo giustifica a posteriori la scelta della Decisione 3.2 §4.2 di rendere il
modello configurabile **per agente** anziché fissarne uno per l'intero sistema.

---

## 8. Perché, a parità di istruzioni, un modello riesce e un altro no

I due agenti ricevono **le stesse identiche istruzioni** indipendentemente dal
modello. La differenza di comportamento non può quindi essere attribuita al
prompt. Le esecuzioni raccolte permettono di caratterizzarla con precisione,
invece di attribuirla genericamente a una diversa «capacità».

**Il modello meno capace conosce la regola ma non riconosce quando si applica.**
Non la ignora — la esegue, e la esegue anche fuori dal suo ambito. Sono
documentati tre casi.

### 8.1 Il *removal test* applicato oltre il suo scopo

I prompt contengono un criterio: rimuovere dal requisito i nomi di libreria o
modulo e verificare se resta un comportamento; se resta, quel nome era dettaglio
implementativo.

Serve a evitare requisiti come *«il sistema deve usare la libreria X»*. Applicato
senza giudizio, smonta qualsiasi frase: nella configurazione Haiku → Haiku il
ciclo ha girato tre volte su una Pull Request rimuovendo a ogni giro un elemento,
fino a lasciare una frase priva di contenuto. Il valutatore aveva scritto
un'istruzione corretta — *«applica il removal test in modo rigoroso»* — e il
generatore l'aveva applicata alla lettera.

### 8.2 La regola sull'artefatto nominato estesa oltre il suo dominio

Il 29 agosto è stata introdotta una regola secondo cui il significato
convenzionale di un artefatto nominato non costituisce evidenza: da *«implements
tab component»* non si può ricavare un requisito, perché il comportamento
verrebbe da ciò che chi legge sa dei *tab*, non dal testo.

Nell'esecuzione del 30 agosto, il valutatore Haiku ha esteso quella regola alle
Pull Request di sicurezza, rifiutandole con la motivazione che *«qualunque
requisito ripeterebbe il significato del nome di una tecnica»*. Il conteggio,
sulle stesse 9 Pull Request:

| | Haiku | Sonnet |
|---|---|---|
| PR in cui pretende di conoscere il meccanismo del fix | **4** | **0** |

La pretesa contraddice la Decisione 3.1 §9.1, che stabilisce esplicitamente che
l'ignoranza del meccanismo non rende una Pull Request non estraibile — e che
porta come esempio proprio una delle Pull Request rifiutate.

**Sonnet non ha commesso l'errore su nessuna delle nove.**

### 8.3 Un errore di formulazione della regola, rivelato da entrambi

La stessa esecuzione ha però mostrato un difetto che non dipende dal modello:
anche Sonnet ha applicato la regola sull'artefatto nominato a una Pull Request
che cambiava un **valore predefinito**, rifiutandola.

In quel caso la regola era formulata male. Esiste una differenza fra *«questa
cosa ora esiste»*, che non fonda alcun comportamento, e *«questa impostazione ora
vale X»*, che è un'affermazione sul sistema verificabile senza conoscere il
funzionamento interno di X. La distinzione mancava, ed è stata aggiunta.

Il caso è istruttivo per la tesi perché separa due cause spesso confuse: un
modello che applica male una regola corretta (§8.1, §8.2) e una regola scritta
male che qualunque modello applicherebbe allo stesso modo (§8.3).

### 8.4 Formulazione generale

Applicare correttamente un criterio richiede due capacità distinte:

1. **conoscere la regola** — che un modello piccolo apprende dal prompt senza
   difficoltà;
2. **riconoscere i confini del suo dominio di applicazione** — che richiede di
   valutare se il caso presente somigli a quello per cui la regola è stata
   scritta.

I dati raccolti indicano che la differenza fra le fasce si manifesta quasi
interamente sulla seconda. È un risultato con una conseguenza pratica: **un
prompt più dettagliato non compensa un modello meno capace**, perché aggiungere
regole aumenta le occasioni di applicarle fuori luogo. Riformulare il prompt e
cambiare modello non sono interventi intercambiabili.

---

## 9. Costi reali

### 9.1 Costo delle cinque configurazioni

| Configurazione | Costo | Chiamate | Costo per requisito accettato |
|---|---|---|---|
| Haiku → Haiku | $0,11 | 28 | $0,036 |
| Opus → Sonnet | $0,43 | 18 | $0,071 |
| Opus → Opus | $0,53 | 18 | $0,075 |
| Haiku → Opus | $0,46 | 22 | $0,076 |
| Sonnet → Opus | $0,65 | 24 | $0,108 |

Due osservazioni apparentemente paradossali.

**La configurazione con più chiamate è la più economica.** Haiku → Haiku ne
effettua 28 contro le 18 di Opus → Opus e costa un quinto: il numero di chiamate
e il costo sono grandezze indipendenti, perché il prezzo per token differisce di
un fattore cinque.

**La configurazione migliore è la più cara pur usando un modello più economico
per metà del lavoro.** Sonnet → Opus costa più di Opus → Opus perché le revisioni
si pagano due volte: più chiamate, e soprattutto un valutatore che quando ha
correzioni da motivare produce molto più testo — 7.633 token di uscita contro i
3.644 della configurazione in cui non aveva nulla da obiettare.

**Il requisito migliore costa il 23% in più di quello prodotto in maggior
quantità.** È il compromesso che la Decisione 3.2 §6 chiede di documentare
esplicitamente anziché risolvere implicitamente.

### 9.2 Costo complessivo del progetto

L'intera fase sperimentale — **22 esecuzioni, 225 elaborazioni di Pull Request**,
comprese le prove di sviluppo — è costata **$4,90**.

Il dato è rilevante per la tesi in due direzioni. Da un lato conferma che, a
questa scala, il costo non è un vincolo di progetto e non giustifica la scelta di
un modello meno capace. Dall'altro va estrapolato con prudenza: le stesse
proporzioni applicate a un corpus di migliaia di Pull Request con la
configurazione più costosa porterebbero a cifre di ordini di grandezza diversi.

---

## 10. Riproducibilità e variabilità

### 10.1 I parametri di campionamento non sono più disponibili

La Decisione 3.2 prevedeva di contenere la variabilità fissando il parametro
`temperature` a zero. In fase di implementazione si è constatato che
`temperature`, `top_p` e `top_k` **sono stati rimossi** dall'API dei modelli
attuali. Alcune fasce accettano al loro posto `effort`, che regola la profondità
del ragionamento; la fascia Haiku non lo supporta.

**Conseguenza metodologica:** la variabilità non può più essere soppressa, deve
essere **misurata** attraverso repliche della stessa configurazione. Il peso si
sposta interamente sulle contromisure già previste: registrare modello, versione
datata e versione dei prompt di ogni esecuzione.

### 10.2 Quanto è ampia la variabilità

Il campione contiene un caso che permette di misurarla senza esperimenti
aggiuntivi: le Pull Request **#6870 e #6879 hanno titolo e corpo identici byte per
byte** — il dataset contiene lo stesso cambiamento due volte. Su sedici
esecuzioni:

| Confronto fra i due esiti sulla coppia identica | Coincidono |
|---|---|
| Classificazione (estraibile / non estraibile) | **15 su 16** |
| Formulazione del requisito prodotto | **2 su 14** |

La **decisione** è quindi ragionevolmente stabile, la **formulazione** quasi mai.
Le due sole coincidenze testuali si sono avute con Opus in ruolo di generatore.

Un secondo dato, ottenuto rieseguendo la stessa configurazione sullo stesso
sottoinsieme a distanza di un giorno: **due esiti su cinque sono cambiati**.

### 10.3 Conseguenze per il piano sperimentale

Ne discendono due vincoli per la fase di valutazione:

- ogni configurazione va eseguita in **più repliche**, e le differenze vanno
  interpretate rispetto all'ampiezza della variabilità osservata;
- il confronto con il gold standard **non può basarsi sull'uguaglianza testuale**,
  perché la stessa Pull Request produce quasi sempre una formulazione diversa.

---

## 11. Raccomandazione operativa

Alla luce dei dati raccolti:

**Configurazione di riferimento: Sonnet come generatore, Opus come valutatore.**
È l'unica in cui il ciclo di revisione svolge la funzione per cui è stato
progettato, e produce i requisiti finali qualitativamente migliori.

**Haiku su entrambi gli agenti resta utile per le verifiche tecniche** — accertare
che la pipeline giri dopo una modifica — perché costa un quinto e per quello scopo
la qualità del ragionamento è irrilevante.

**Sconsigliata la configurazione con lo stesso modello in entrambi i ruoli**, per
la ragione del §7.2: il modello tende a ratificare il proprio output.

---

## 12. Limiti di questa analisi

Vanno dichiarati esplicitamente, perché condizionano la forza delle conclusioni.

**Manca il gold standard.** I giudizi di qualità espressi al §7.3 sono degli
autori, non misurati. La costruzione del riferimento annotato a mano è il passo
che trasforma queste osservazioni in risultati.

**Una sola replica per configurazione.** Come mostra il §10.2, differenze di uno
o due requisiti su nove rientrano plausibilmente nella variabilità.

**Campione ridotto e non rappresentativo.** Nove Pull Request, di cui cinque
generate da uno strumento automatico di analisi della sicurezza e recanti lo
stesso testo di base. Una verifica su un secondo corpus di 46 Pull Request scritte
da persone ha mostrato che **il materiale in ingresso sposta gli esiti più del
modello**: a parità di modello e di prompt, il tasso di accettazione passa dal 33%
al 74%. I valori assoluti della tabella al §7 sono quindi una proprietà del
campione, non dei modelli; resta valido il confronto *fra* le configurazioni,
poiché la variabile cambiata era una sola.

**Un solo fornitore.** Non sono stati confrontati modelli di fornitori diversi né
modelli aperti eseguiti localmente. L'astrazione descritta al §4 rende il
confronto realizzabile, ma non è stato eseguito.

---

## Riferimenti

**Documenti di progetto.** Decisione 3.1 (forma e qualità dei requisiti),
Decisione 3.2 (scelta del modello), Decisione 3.7 (piano di valutazione);
`experiments/analisi/confronto-modelli.md` per l'analisi estesa delle cinque
configurazioni; `experiments/runs/` per i report integrali.

**Letteratura.**

- Huang, J. et al. (2024). *Large Language Models Cannot Self-Correct Reasoning
  Yet.* ICLR 2024.
- Wang, Q. et al. (2025). *Cross-Refine: Improving Natural Language Explanation
  Generation by Learning in Tandem.* COLING 2025.
- Madaan, A. et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.*
  NeurIPS 2023.
- Donato, B. et al. (2025b), sulla variabilità fra repliche della stessa
  richiesta a un modello linguistico.
