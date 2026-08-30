# Diario di lavoro — PR-to-Requirements

Diario dello stage di Andrea Saverino e Marco Saverino Salvatore.
Università degli Studi di Milano-Bicocca — tutor: Benedetta Donato.

Annotiamo qui, giorno per giorno, cosa abbiamo fatto, cosa abbiamo deciso e
dove ci siamo bloccati. È un racconto del lavoro, non una documentazione
tecnica: per quella ci sono i documenti di design in `docs/` e il registro
delle modifiche in `recap.md`.

Il diario copre due fasi. La prima, da fine aprile a metà luglio, è di
formazione e prototipazione: abbiamo studiato gli strumenti e li abbiamo
provati su progetti nostri, prima di sapere con precisione su cosa avremmo
lavorato. La seconda, da fine luglio, è lo stage vero e proprio.

---

# Parte 1 — Formazione e prototipazione

## 27 aprile – 8 maggio — Primo contatto con LangChain e LangGraph

### Lunedì 27 aprile — venerdì 1 maggio

Abbiamo iniziato a studiare LangChain, incuriositi dal fatto che se ne parlasse
ovunque ma senza capire bene cosa fosse. La prima settimana è servita
soprattutto a chiarirci le idee su un punto: questi strumenti non "fanno
funzionare meglio" un modello linguistico, servono a organizzare il lavoro
attorno al modello. Il modello resta quello che è; cambia il modo in cui gli
si passano le informazioni e si gestisce quello che risponde.

Lettura della documentazione ufficiale e prove con esempi minimi, per capire i
concetti di base: come si struttura una richiesta, come si concatenano più
passaggi, come si tiene traccia di quello che è successo prima.

### Lunedì 4 maggio — venerdì 8 maggio

Passaggio a LangGraph, che è la parte che ci interessava davvero. La
differenza rispetto a una semplice sequenza di passaggi è che qui si disegna
un grafo: ci sono nodi che fanno qualcosa, uno stato condiviso che passa da
un nodo all'altro, e soprattutto si possono fare dei **cicli**, cioè tornare
indietro a un passaggio precedente.

È stato il momento in cui abbiamo capito perché serve: se vuoi che un sistema
produca qualcosa, lo controlli, e in caso rifaccia il lavoro, ti serve
esattamente questo. Con una catena lineare non si può.

Abbiamo studiato come si definisce lo stato, come si collegano i nodi e come
si scrivono le condizioni che decidono dove andare dopo. Prove con grafi
piccolissimi, giusto per vedere il ciclo funzionare.

Nota che ci siamo segnati: sono strumenti recenti e in evoluzione rapida.
Molti esempi trovati online erano già scritti per versioni precedenti e non
funzionavano più. Conviene fidarsi della documentazione ufficiale e
diffidare dei tutorial vecchi di qualche mese.

---

## 11 – 22 maggio — Model Context Protocol

### Lunedì 11 maggio — venerdì 15 maggio

Studio di MCP, il Model Context Protocol. All'inizio non ci era chiaro che
problema risolvesse. Poi l'abbiamo inquadrato così: un modello linguistico da
solo sa solo produrre testo, non può leggere un file o interrogare un
database. Per fargli fare queste cose bisogna metterlo in condizione di
chiedere a qualcun altro di farle. MCP è un modo standard di offrire questi
"servizi".

La cosa che ci ha convinti è che è uno standard e non una soluzione fatta in
casa: si descrive una volta cosa un servizio sa fare, e chiunque può usarlo.

### Lunedì 18 maggio — venerdì 22 maggio

Approfondimento pratico: com'è fatto un server, come si dichiarano gli
strumenti che mette a disposizione, che forma hanno le richieste e le
risposte. Abbiamo provato a scriverne uno piccolissimo per capire il
meccanismo dall'interno.

Ci siamo appuntati una cosa che si rivelerà importante più avanti: MCP è il
modo di **esporre** delle capacità, non è il posto dove i dati vivono. Il
database resta una cosa a parte.

---

## 25 maggio – 5 giugno — Primi prototipi e studio delle API

### Lunedì 25 maggio — venerdì 29 maggio

Primo esperimento vero, per mettere insieme le cose studiate: una piccola
pipeline che legge le email di una casella e le organizza da sola. Il sistema
legge il messaggio, decide a quale categoria appartiene — spam, pubblicità,
lavoro, personale — crea l'etichetta corrispondente e sposta l'email nella
cartella giusta.

Ha funzionato meglio di quanto ci aspettassimo sui casi ovvi, ma ci ha
insegnato qualcosa sui casi ambigui: una newsletter di lavoro va in
"pubblicità" o in "lavoro"? Senza un criterio scritto in modo esplicito, il
sistema decideva in modo diverso ogni volta.

È stata la prima volta che ci siamo scontrati con un problema che poi
ritroveremo identico nello stage: **se non definisci con precisione i criteri,
il modello se li inventa**, e i risultati non sono confrontabili tra
un'esecuzione e l'altra.

### Lunedì 1 giugno — venerdì 5 giugno

Settimana dedicata al lato pratico dei modelli: come si collega un modello a
un programma tramite API, come si ottiene e si conserva una chiave di accesso,
come si costruisce una richiesta.

Studio dei costi. Abbiamo capito il meccanismo dei token: si paga per quanto
testo entra e per quanto ne esce, con prezzi diversi tra i due, e il testo in
uscita costa parecchio di più. Abbiamo fatto qualche conto per capire quanto
costerebbe far girare una pipeline decine di volte al giorno durante lo
sviluppo — abbastanza da farci decidere di usare sempre il modello più
economico finché si tratta solo di verificare che il codice funzioni.

Confronto tra i modelli della famiglia Claude: le fasce disponibili, la
differenza di prezzo tra l'una e l'altra, e in quali casi conviene salire di
livello. Ci siamo segnati anche la questione della riproducibilità: lo stesso
modello con la stessa richiesta può rispondere in modo diverso, e i modelli
vengono aggiornati nel tempo. Se si vogliono confrontare dei risultati bisogna
annotare con precisione quale modello e quali impostazioni si sono usati.

---

## 8 – 19 giugno — NovitAI.it, il progetto gemello

### Lunedì 8 giugno — venerdì 12 giugno

Due settimane sul progetto più impegnativo di questa fase: **NovitAI.it**, un
blog che si gestisce da solo. L'idea è che una pipeline si occupi dell'intero
processo: cercare argomenti di attualità, scrivere l'articolo, rivederlo e
pubblicarlo online, senza intervento umano.

L'abbiamo costruito con la stessa tecnologia che avremmo usato poi nello
stage: LangGraph per il flusso, MCP per l'accesso ai dati, un database per
tenere memoria di quello che è già stato pubblicato, le API dei modelli per la
scrittura, istruzioni di sistema per definire il comportamento di ogni
passaggio, e un ciclo di revisione prima della pubblicazione.

La prima settimana è servita a mettere in piedi la struttura e a far arrivare
un articolo dalla ricerca dell'argomento fino alla bozza.

### Lunedì 15 giugno — venerdì 19 giugno

Seconda settimana: revisione e pubblicazione. Qui abbiamo aggiunto il
passaggio che controlla l'articolo prima che vada online, e il ciclo che lo fa
riscrivere se non va bene.

Due lezioni che ci siamo portati dietro:

La prima è che il controllo automatico serve davvero, ma solo se ha criteri
propri. Un modello a cui chiedi "va bene questo articolo?" tende a rispondere
di sì; se invece gli dai una lista precisa di cose da verificare, inizia a
trovare i problemi.

La seconda riguarda la memoria: senza un archivio di quello che era già stato
pubblicato, il sistema riscriveva articoli su argomenti già trattati. Il
database non serviva solo ad archiviare, serviva a **non ripetersi**.

---

## 22 giugno – 10 luglio — Messa a punto e bilancio

### Lunedì 22 giugno — venerdì 3 luglio

Periodo di osservazione e correzioni su NovitAI. Con il sistema in funzione
sono emersi i problemi che a tavolino non si vedono: articoli troppo simili
tra loro, passaggi che ogni tanto si bloccavano, costi più alti del previsto
quando il ciclo di revisione girava troppe volte.

Da qui la decisione, presa qui e poi ripresa nello stage, di **mettere sempre
un limite al numero di tentativi**: un ciclo che può girare all'infinito
prima o poi lo fa, e la bolletta se ne accorge.

### Lunedì 6 luglio — venerdì 10 luglio

Bilancio di questa prima fase. In poco più di due mesi eravamo passati dal non
sapere cosa fosse LangGraph ad avere un sistema funzionante che pubblicava
articoli da solo.

Soprattutto, avevamo capito quali sono i pezzi ricorrenti di questo tipo di
sistemi: un flusso a stati con la possibilità di tornare indietro, istruzioni
scritte con cura, un controllo con criteri espliciti, una memoria di quello
che è già stato fatto, e un limite ai tentativi.

---

## 13 – 17 luglio — Preparazione allo stage

Contatti con l'università per l'avvio dello stage e prime informazioni sul
tema proposto. Sapendo che avrebbe riguardato modelli linguistici e agenti,
abbiamo ripreso e riordinato gli appunti dei mesi precedenti, per arrivare al
primo incontro con un'idea chiara di cosa sapevamo fare.

---

# Parte 2 — Lo stage

## 20 – 24 luglio — Avvio e inquadramento del problema

### Lunedì 20 luglio

Primo incontro con la tutor. Ci ha presentato l'idea dello stage: partire dalle
Pull Request di progetti reali e provare a ricostruire automaticamente i
requisiti funzionali che stanno dietro alle modifiche, usando modelli
linguistici e agenti.

L'idea ci è sembrata subito interessante ma anche molto aperta: non era chiaro
fin dove ci si potesse spingere partendo solo dal testo di una Pull Request.
Abbiamo preso appunti sulle domande da chiarire.

### Martedì 21 luglio

Giornata di letture generali per capire il contesto. Abbiamo cercato di
farci un'idea di cosa si intenda esattamente per "requisito funzionale" e di
come venga scritto nella pratica industriale. Ci siamo accorti subito che il
confine tra "cosa deve fare il sistema" e "come è stato implementato" è meno
ovvio di quanto pensassimo.

### Mercoledì 22 luglio

Abbiamo iniziato a cercare articoli scientifici sul tema. Ci siamo divisi il
lavoro: Andrea sulla parte relativa alle informazioni ricavabili dalle Pull
Request, Marco sull'uso dei modelli linguistici per generare requisiti.

Prime difficoltà nella ricerca: cercando "pull request requirements" escono
soprattutto lavori sulla generazione di codice, non sui requisiti. Abbiamo
allargato la ricerca a temi vicini, come il recupero dei collegamenti tra
requisiti e codice.

### Giovedì 23 luglio

Continuazione della ricerca bibliografica. Abbiamo raccolto una prima lista di
articoli candidati e li abbiamo scremati leggendo abstract e conclusioni.

Abbiamo deciso di organizzare la bibliografia per aree tematiche invece che in
un unico elenco: era già evidente che il lavoro toccava argomenti abbastanza
diversi tra loro.

### Venerdì 24 luglio

Secondo incontro con la tutor. Le abbiamo mostrato i primi articoli trovati e
lei ci ha indirizzato verso alcuni lavori che non avevamo considerato, tra cui
alcuni suoi. Ci ha anche segnalato l'esistenza di un dataset di Pull Request
costruito dal suo gruppo, che potremmo usare come base sperimentale.

Uscendo dall'incontro avevamo le quattro aree di ricerca definite:
informazioni ricavabili dalle Pull Request, modelli linguistici per i
requisiti, sistemi multi-agente, e il protocollo MCP per la memoria.

---

## 27 – 31 luglio — Stato dell'arte

### Lunedì 27 luglio

Lettura approfondita dei primi articoli dell'area 1. Ci ha colpito quanto le
descrizioni delle Pull Request siano irregolari nella realtà: alcune sono
dettagliate, altre sono una riga sola. Ce lo siamo segnato come problema da
affrontare presto, perché se il testo è povero non c'è molto da estrarre.

### Martedì 28 luglio

Lettura degli articoli sull'uso dei modelli linguistici per la generazione e la
valutazione dei requisiti. Abbiamo trovato lavori che usano un modello per
generare e un secondo passaggio per valutare la qualità: è più o meno l'idea
che avevamo in mente anche noi.

### Mercoledì 29 luglio

Area 3, sistemi multi-agente. Qui abbiamo trovato la questione più delicata di
tutto lo stato dell'arte: alcuni articoli mostrano che un modello che corregge
sé stesso non necessariamente migliora, e a volte peggiora. Il punto è che
serve un'informazione nuova perché la revisione abbia senso.

Ne abbiamo discusso a lungo tra noi. La conclusione è stata che il nostro
valutatore deve avere qualcosa in più rispetto al generatore — criteri
espliciti e, più avanti, la memoria dei requisiti già prodotti — altrimenti
rischiamo di costruire un ciclo che gira a vuoto.

### Giovedì 30 luglio

Area 4, lettura della specifica del Model Context Protocol. Serviva capire se
avesse senso usarlo per far accedere gli agenti a un archivio di requisiti.
La risposta ci è sembrata sì, ma con un'avvertenza che ci siamo appuntati: MCP
è un modo di esporre delle funzionalità, non è il database.

### Venerdì 31 luglio

Abbiamo messo insieme gli appunti delle quattro aree e iniziato a scrivere una
sintesi. Discussione con la tutor sullo stato dell'arte: ci ha suggerito di
non fermarci al riassunto dei singoli articoli ma di far emergere il vuoto che
il nostro lavoro va a riempire.

---

## 3 – 7 agosto — Nascita del progetto

### Lunedì 3 agosto

Abbiamo deciso di dare una forma concreta al progetto e di smettere di tenere
tutto in appunti sparsi. Discussione su come organizzare il repository: quali
cartelle servono, dove mettere i documenti, dove il codice.

Abbiamo scelto di separare fin dall'inizio la parte scritta (stato dell'arte,
decisioni, verbali) dalla parte di codice, e di tenere una cartella dedicata
agli esperimenti.

### Martedì 4 agosto

Creazione del repository su GitHub e stesura del README: descrizione del
progetto, i due agenti previsti, autori, e la tabella con la struttura delle
cartelle. Abbiamo dato al progetto il nome interno **PR-to-Requirements**, e al
pacchetto di codice la sigla **ARE** (Automatic Requirement Extraction).

Prime prove con i comandi git per prendere confidenza con il flusso di lavoro
condiviso.

### Mercoledì 5 agosto

Configurazione dell'ambiente di sviluppo: Python, gestione delle dipendenze,
controllo automatico dello stile del codice e dei test a ogni modifica.

Abbiamo scritto anche il documento con le regole di collaborazione: un ramo di
lavoro per ogni attività, messaggi di commit con un formato fisso, e revisione
reciproca prima di unire il lavoro. Ci è sembrato utile fissarle subito,
lavorando in due sullo stesso repository.

### Giovedì 6 agosto

Ripresa della scrittura dello stato dell'arte. Abbiamo riorganizzato le schede
degli articoli letti in luglio dando a ciascuna la stessa struttura, così da
poterle confrontare.

### Venerdì 7 agosto

Incontro settimanale. Abbiamo mostrato alla tutor l'impostazione del
repository e la bozza dello stato dell'arte. Ci ha chiesto di essere più
espliciti su un punto: cosa consideriamo esattamente un requisito funzionale
nel nostro contesto. Non era una domanda banale e ci ha tenuti occupati per i
giorni successivi.

---

## 10 – 14 agosto — Stato dell'arte e prime decisioni

### Lunedì 10 — mercoledì 12 agosto

Giorni dedicati alla stesura vera e propria del documento di stato dell'arte.
Abbiamo unito le quattro aree in un discorso unico, cercando di far emergere
il filo: dalle Pull Request si possono ricavare informazioni utili, i modelli
linguistici sanno scrivere requisiti, l'auto-revisione da sola non basta,
serve un modo per dare memoria al sistema.

### Giovedì 13 agosto

Discussione tra noi sul confine del lavoro. Ci siamo resi conto che stavamo
mescolando due domande diverse: *come deve essere fatto un buon requisito* e
*come si fa a ricostruirlo da una Pull Request*. Abbiamo deciso di tenerle
separate anche nei documenti.

### Venerdì 14 agosto

Caricato in repository il documento di stato dell'arte. È il primo risultato
consistente dello stage.

Breve pausa per Ferragosto.

---

## 17 – 22 agosto — Le decisioni di design

### Lunedì 17 — martedì 18 agosto

Ripresa del lavoro. Abbiamo iniziato a formalizzare le scelte progettuali in
documenti numerati, uno per decisione, con lo stesso schema: contesto,
alternative valutate, scelta, motivazione, punti ancora aperti.

L'idea è che quando arriveremo a scrivere la tesi non dovremo ricostruire a
memoria perché avevamo fatto una certa scelta.

### Mercoledì 19 agosto

Lavoro sullo standard di qualità dei requisiti. Abbiamo confrontato le
alternative disponibili e ci siamo accorti che quella più citata negli
articoli è in realtà superata da uno standard più recente. Abbiamo scelto
quello aggiornato, per non partire con un riferimento facilmente contestabile.

Abbiamo anche deciso di adottare una forma fissa per scrivere i requisiti, in
inglese e con il verbo "shall", basata su quattro schemi ricorrenti.

### Giovedì 20 agosto

Completata e caricata la prima decisione di design. Insieme a questa abbiamo
aperto un documento con le domande ancora aperte da porre alla tutor: quali
Pull Request considerare estraibili, come gestire quelle miste, cosa fare con
le descrizioni troppo brevi.

La parte che ci ha impegnato di più è stata la distinzione tra *cosa* il
sistema deve fare e *come* è stato realizzato. Abbiamo scritto degli esempi
concreti per fissarla.

### Venerdì 21 agosto

Caricate in repository le schede degli articoli, divise nelle quattro aree.

Nel pomeriggio, decisione sul modello linguistico da usare. Abbiamo scelto un
modello economico per la fase di sviluppo, perché durante la scrittura del
codice la maggior parte delle chiamate serve solo a verificare che il
programma funzioni, e sarebbe uno spreco pagare un modello costoso per quello.

Abbiamo però deciso che il modello deve essere scelto separatamente per
ciascun agente e scritto in un file di configurazione, non nel codice, così
da poterlo cambiare senza toccare il programma.

### Sabato 22 agosto

Decisione sulla memoria dei requisiti. Abbiamo valutato diverse soluzioni e
scelto un database locale semplice, senza server da avviare: per il numero di
requisiti che prevediamo è più che sufficiente, e ha il vantaggio di poter
essere copiato come un file singolo per conservare lo stato di un esperimento.

Abbiamo anche stabilito una regola che ci sembra importante: nella memoria
finisce solo ciò che è stato approvato. Un requisito scartato non deve poter
influenzare le valutazioni successive.

Nella stessa giornata abbiamo documentato come intendiamo trattare le Pull
Request con poco testo.

---

## 24 – 26 agosto — Dal progetto al codice

### Lunedì 24 agosto

Giornata lunga, dedicata a chiudere l'impianto progettuale.

Abbiamo scritto la decisione sull'architettura degli agenti: come si passa
dalla Pull Request al requisito, quando si rigenera, quando ci si ferma.
Abbiamo fissato a tre il numero massimo di tentativi e stabilito che se il
valutatore continua a chiedere modifiche oltre il limite il requisito **non**
viene accettato lo stesso: si registra il fallimento. Ci è sembrato più
onesto che accontentarsi del "meno peggio".

Poi la decisione sul dataset: useremo il dataset di Pull Request del gruppo
della tutor, partendo da un solo progetto e da poche Pull Request, usando
solo titolo e descrizione come materiale di partenza. Escludere volontariamente
il codice modificato è una scelta: vogliamo capire fin dove si arriva con la
sola descrizione, prima di aggiungere altro.

Aggiornato anche il documento delle domande aperte per la tutor.

### Martedì 25 agosto — mattina

Completate le ultime decisioni: l'interfaccia per l'accesso alla memoria e il
piano di valutazione.

Sul piano di valutazione abbiamo discusso parecchio. Il punto critico è che il
nostro sistema contiene già un valutatore: se usassimo quello per dire quanto
è bravo il sistema, staremmo facendo giudicare il lavoro a una sua stessa
parte. Abbiamo quindi deciso che la valutazione finale sarà fatta da noi, a
mano, con un riferimento costruito separatamente e una griglia di criteri.

### Martedì 25 agosto — pomeriggio

Iniziata la parte pratica. Il dataset di partenza ha una struttura ricca e
articolata, mentre a noi servono solo pochi campi. Abbiamo scritto uno script
che legge il dataset, seleziona il progetto e le Pull Request che ci
interessano ed estrae solo quello che serve, producendo un unico file in un
formato semplice e sempre uguale.

È stata una scelta importante più di quanto sembri: da quel file in poi il
resto del sistema non deve più sapere da quale dataset arrivano i dati.

Per comodità abbiamo aggiunto allo script una piccola interfaccia grafica, così
da poter scegliere il progetto e il numero di Pull Request senza dover
ricordare i parametri da riga di comando. Serve soprattutto a noi, ma rende la
cosa mostrabile anche a chi non usa il terminale.

### Martedì 25 agosto — sera

Per chiarirci le idee sul funzionamento complessivo abbiamo costruito uno
schema interattivo in una pagina web, in cui si possono seguire tutti i
percorsi possibili: la Pull Request che non produce nulla, quella accettata
subito, quella che passa da una revisione, quella che fallisce dopo tre
tentativi.

Vederlo disegnato ci ha fatto notare un paio di casi che avevamo lasciato
implicito nel documento e che così abbiamo reso espliciti.

Sempre in giornata abbiamo scritto il componente che legge il file di Pull
Request e ne controlla la correttezza, con i relativi test, e lo abbiamo
integrato nel repository del progetto. Abbiamo scoperto in questa occasione
che il progetto non era configurato correttamente per essere installato: i
test funzionavano solo perché non usavano ancora il codice vero. Sistemato.

Subito dopo abbiamo aggiunto la configurazione dei modelli e il collegamento
al servizio, tenendo la chiave di accesso fuori dal repository.

### Mercoledì 26 agosto — mattina

Costruito lo scheletro del flusso di lavoro: la macchina che porta una Pull
Request dall'inizio alla fine, con tutte le diramazioni previste dal progetto.

Abbiamo tenuto le decisioni su dove andare in un punto solo, invece di
distribuirle nei vari passaggi: così si capisce a colpo d'occhio come si
comporta il sistema, e si può verificare senza dover interrogare un modello.

Tutta questa parte è stata provata con agenti finti, che rispondono in modo
prestabilito. Sembra un dettaglio ma ci ha permesso di verificare ogni
percorso in pochi secondi e senza spendere nulla.

### Mercoledì 26 agosto — pomeriggio

Ci siamo accorti di un'incoerenza tra i nostri stessi documenti: il piano di
valutazione era stato rivisto in corso d'opera, ma due decisioni precedenti
facevano ancora riferimento all'impostazione vecchia. Le abbiamo aggiornate.

È il tipo di errore che non si vede finché non si rileggono i documenti in
fila, e che avrebbe fatto una brutta impressione in sede di valutazione.

### Mercoledì 26 agosto — sera

Scritte le istruzioni vere e proprie per i tre agenti — il controllo iniziale,
il generatore e il valutatore — traducendo in indicazioni operative le regole
che avevamo definito nei documenti. Le abbiamo messe in file separati dal
codice e numerati per versione, così da poter dire con precisione quale
formulazione ha prodotto quali risultati.

Poi abbiamo collegato gli agenti al flusso e aggiunto il componente che
elabora tutte le Pull Request di un file, una alla volta e in ordine di data,
salvando alla fine un resoconto con i requisiti prodotti e la storia dei
tentativi.

Con questo il sistema è completo dall'inizio alla fine: si dà in pasto il file
delle Pull Request e si ottengono i requisiti. Manca solo la chiave di accesso
al servizio per poterlo eseguire davvero.

### Mercoledì 26 agosto — notte

Abbiamo attivato l'accesso al servizio e fatto girare il sistema per la prima
volta sulle Pull Request vere. Una giornata sola, ma è quella in cui abbiamo
imparato di più.

**Il primo tentativo è fallito subito.** Alcuni parametri che passavamo al
modello — quelli che regolano quanto le risposte sono variabili — non esistono
più: il fornitore li ha rimossi. Il problema tecnico si è risolto in pochi
minuti, ma la conseguenza è seria e riguarda la tesi: avevamo previsto di
azzerare la variabilità fissando uno di quei parametri, e non è più possibile.
La variabilità ora va **misurata** ripetendo le esecuzioni, non eliminata. In
un certo senso il lavoro della tutor su questo tema diventa ancora più
centrale per noi.

**Poi il sistema ha funzionato.** Nove Pull Request elaborate dall'inizio alla
fine, requisiti generati, valutati, alcuni riscritti dopo il feedback. Costo
di un'esecuzione completa: quattro centesimi con il modello economico.

**E abbiamo scoperto i problemi veri.** Il valutatore proponeva al generatore
una formulazione e al giro successivo la bocciava, contraddicendosi. Il
controllo iniziale scartava Pull Request da cui un requisito si poteva
ricavare, e ne accettava altre praticamente identiche. Ne è nata una lunga
discussione fra noi, e con un collega, su una questione di fondo: fino a che
punto possiamo pretendere che una Pull Request descriva il comportamento del
sistema? La conclusione è che non possiamo pretendere il **meccanismo** —
quale libreria, quale tecnica — perché quello è già implementazione. Ma
possiamo pretendere che il comportamento sia identificabile. Abbiamo scritto
questa distinzione nei documenti di progetto: è probabilmente la decisione più
importante presa oggi.

**Abbiamo rifatto tutte le istruzioni degli agenti.** Dopo aver letto le linee
guida ufficiali su come si scrivono istruzioni efficaci per questi modelli, le
abbiamo riscritte da zero: sezioni ben separate, una procedura da seguire in
ordine invece di principi sparsi che il modello poteva applicare a piacere,
più esempi e tutti diversi fra loro, e una spiegazione del perché accanto a
ogni regola.

Ci siamo anche accorti di un errore nostro che avrebbe potuto falsare tutti i
risultati: negli esempi delle istruzioni avevamo messo pezzi delle stesse Pull
Request su cui poi misuravamo. Il modello le riconosceva invece di ragionare.
Le abbiamo sostituite con esempi inventati e aggiunto un controllo automatico
che d'ora in poi impedisce che succeda di nuovo.

**Infine abbiamo confrontato due modelli** sullo stesso identico materiale: uno
economico e uno molto più capace. Concordano su sei Pull Request su nove. Sulle
altre tre decidono diversamente — e il modello più capace motiva meglio, ma
"meglio" secondo noi non è ancora una misura.

Ed è il punto in cui ci siamo fermati. Abbiamo modificato le istruzioni tre
volte in una sera, ogni volta con una buona ragione, ogni volta ottenendo
risultati diversi. Alla fine una sola Pull Request su nove riceve lo stesso
esito in tutte le prove. Il problema non è più tecnico: **non sappiamo quale
sia la risposta giusta**, quindi non possiamo dire se una modifica migliora le
cose o le sposta soltanto.

Il prossimo passo è quindi deciderlo noi, caso per caso, sulle nove Pull
Request del campione: è il gold standard previsto dal piano di valutazione, e
da stasera è diventato la cosa più urgente da fare.

---

## 27 agosto — Le correzioni, e finalmente un confronto pulito

### Giovedì 27 agosto — mattina

Siamo partiti dai tre difetti che ieri sera ci avevano fermato, e li abbiamo
affrontati uno per uno.

**Il primo controllo non lo fa più un modello.** All'ingresso della pipeline
c'era un agente il cui compito era dire «questa Pull Request contiene abbastanza
informazione per andare avanti?». Discutendone ci siamo accorti che era la
scelta sbagliata: un modello, per rispondere a quella domanda, deve immaginarsi
il requisito che non ha ancora davanti, e sbaglia in entrambe le direzioni.
Lo abbiamo sostituito con un controllo banale e deterministico — corpo vuoto,
oppure meno di cinquanta caratteri fra titolo e descrizione — e abbiamo
restituito il giudizio vero a chi il requisito ce l'ha sotto gli occhi, cioè al
valutatore. Costa zero, dà sempre lo stesso risultato, e non pretende di sapere
cose che non può sapere.

La soglia dei cinquanta caratteri è arbitraria e lo abbiamo scritto: è un
numero di comodo che andrà calibrato quando avremo il gold standard.

**Il valutatore ora si ricorda cosa ha già detto.** Ieri lo avevamo visto
chiedere una correzione, riceverla, e poi al giro dopo chiederne una opposta:
ogni volta ripartiva da zero. Adesso gli passiamo i tentativi precedenti con i
suoi stessi giudizi, e la regola è semplice: se il problema è stato risolto non
si ripete, se è rimasto si può insistere. Non gli abbiamo tolto la severità,
gli abbiamo tolto la smemoratezza. Da quel momento non è più capitato che una
Pull Request esaurisse i tre tentativi a vuoto.

**Il generatore può dire "non ci riesco".** Prima era costretto a scrivere una
frase anche quando la Pull Request non ne conteneva una: e allora se la
inventava, oppure produceva testo confuso. Ora può fermarsi e spiegare perché.
La cosa che ci piace di più è cosa succede dopo: il caso passa comunque al
valutatore, che può dargli ragione — e la Pull Request si chiude — oppure
dissentire, spiegandogli perché un requisito c'è davvero e da dove partire. È
diventato un dialogo in due direzioni invece che una catena di montaggio.

### Giovedì 27 agosto — pomeriggio

Con il codice fermo e le istruzioni ferme, abbiamo finalmente potuto fare la
cosa che ieri non era possibile: cambiare **una sola variabile alla volta**.

Abbiamo lanciato il sistema cinque volte sullo stesso identico materiale,
cambiando solo quale modello scrive i requisiti e quale li giudica. Tre
modelli: uno economico, uno intermedio, uno molto capace. I risultati vanno da
tre a sette requisiti accettati su nove — quindi la scelta del modello sposta
gli esiti più di qualunque modifica alle istruzioni fatta finora.

Ma le tre cose che abbiamo imparato sono più interessanti del punteggio.

**La prima.** Il giro di revisione — il generatore scrive, il valutatore
critica, il generatore corregge — è la ragione per cui abbiamo costruito due
agenti invece di uno. Ebbene: **non si accende quasi mai.** Se i due modelli
sono uguali, il secondo approva il primo e il giro non parte. Se il giudice è
più debole dell'autore, idem. Serve una differenza di capacità fra i due, e
nemmeno troppo grande: quando il giudice è molto più forte, l'autore capisce la
critica ma non è capace di scrivere di meglio.

**La seconda, che non ci aspettavamo.** Lo stesso modello è molto più severo
quando giudica che quando scrive. Una frase che aveva accettato senza obiezioni
— l'aveva scritta lui — l'ha poi bocciata, definendola «circolare», quando gli
è arrivata da un altro modello. Non è un errore: è che nessuno l'aveva mai
guardata con occhio critico, perché chi l'aveva scritta era la stessa persona
che doveva criticarla. È l'argomento più concreto che abbiamo trovato per usare
**due modelli diversi**, ed è anche quello che dicono i lavori accademici che
avevamo letto a luglio.

**La terza.** La configurazione che accetta più requisiti non è quella che
produce i requisiti migliori. Mettendo il modello più capace ovunque se ne
ottengono sette su nove, ma passano al primo colpo e nessuno li corregge.
Mettendo il modello intermedio a scrivere e quello capace a giudicare se ne
ottengono sei, però tre sono passati attraverso una correzione — e sono
visibilmente più precisi. Ne abbiamo preso uno come esempio: la prima versione
diceva che il sistema deve «proteggere da input malevoli che potrebbero
compromettere l'applicazione»; il giudice ha fatto notare che è una definizione
circolare, perché descrive l'input attraverso il danno che dovrebbe evitare. La
seconda versione dice esattamente cosa il sistema non deve fare con quel
contenuto. È tutta un'altra cosa.

Abbiamo scritto tutto questo in un documento a parte, con gli esempi veri, così
fra un mese ci si capisce ancora qualcosa.

**Una nota sui costi**, perché è controintuitiva: la configurazione migliore è
anche la più cara, e non di poco. Non perché usi il modello più costoso — anzi,
usa quello intermedio per metà del lavoro — ma perché **un giudice che ha
qualcosa da correggere scrive il doppio**. Le correzioni si pagano. Sessantacinque
centesimi per nove Pull Request: sostenibile ora, da tenere d'occhio quando le
Pull Request saranno mille.

**Dove ci siamo fermati.** Sempre allo stesso punto di ieri, ed è giusto così:
tutti i giudizi di qualità qui sopra sono nostri, a occhio. Finché non
compiliamo le schede del gold standard — ognuno la sua, senza guardare cosa ha
prodotto il sistema — non possiamo dire se quella configurazione è davvero
migliore o se semplicemente ci piace di più. Le schede sono pronte da stamattina.
Tocca a noi.

### Giovedì 27 agosto — sera

Prima di chiudere ci è venuto un dubbio, e per fortuna l'abbiamo tolto subito.

Tutte e cinque le prove del pomeriggio giravano sulle stesse nove Pull Request.
E se quei risultati dipendessero dalle nove Pull Request invece che dai modelli?

Abbiamo preso un secondo progetto — quarantasei Pull Request scritte da persone
vere, non da un programma automatico come metà di quelle di prima — e abbiamo
rilanciato il sistema **senza cambiare nulla**: stesso codice, stesse istruzioni,
stesso modello economico.

Il risultato ci ha ribaltato una conclusione. Sulle nove Pull Request di prima
quel modello accettava un requisito su tre; su queste quarantasei ne accetta
tre su quattro. **Il materiale in ingresso sposta i risultati più del modello.**

Il motivo, guardandolo, è ovvio: in quel primo gruppo cinque Pull Request su nove
erano generate da uno strumento di sicurezza automatico e dicevano «è stato
rilevato un problema e le modifiche necessarie sono state applicate» senza mai
dire *quali*. Su un testo così, rifiutare è la risposta giusta. Non era il
modello a essere severo: era il materiale a non dire niente.

Il difetto però non è sparito, si è spostato. Prima rifiutava troppo, adesso
accetta troppo: fra i requisiti approvati ce ne sono cinque che secondo le nostre
stesse regole non dovrebbero passare — uno descrive come è scritto il codice
invece di cosa fa il programma, un altro parla di uno strumento di sviluppo e non
del prodotto, un altro ancora è una frase vera per definizione e quindi vuota.

E poi il regalo della serata. In quelle quarantasei ce ne sono cinque
praticamente gemelle: stesso titolo nella forma, stessa lunghezza, stesso
modulo compilato allo stesso modo. Le abbiamo trovate per caso, ed è
l'esperimento controllato migliore che potessimo desiderare, perché non l'abbiamo
costruito noi. **Hanno ricevuto quattro esiti diversi nella stessa esecuzione.** E
su due di esse il valutatore ha scritto due frasi che si contraddicono
apertamente: su una dice che quel tipo di componente non ha un comportamento
osservabile, sull'altra dice che il comportamento si deduce dal nome stesso del
componente.

Non lo consideriamo un bug da correggere in fretta. È il fenomeno che stiamo
studiando, colto in flagrante, e la tabella di quei cinque casi è la cosa più
convincente da portare alla tutor.

Un effetto pratico immediato, però, c'è: le schede del gold standard che avevamo
preparato la mattina sono tarate sulle nove Pull Request sbagliate. Vanno rifatte
sulle quarantasei. Meglio scoprirlo adesso che dopo averle compilate.

---

## 28 agosto — La memoria

### Venerdì 28 agosto

Fino a ieri il sistema aveva un difetto che nessuno di noi aveva notato perché
era ovvio: **ogni esecuzione ripartiva da zero**. Produceva i requisiti, scriveva
il suo resoconto, e finiva lì. Il giorno dopo non ricordava nulla.

Oggi abbiamo costruito la memoria. Tecnicamente è un database, ma la cosa
comoda è che è **un file solo**: niente da installare, niente servizio da
avviare, lo copi come una foto e lo apri con un programmino gratuito per
guardarci dentro come fosse un foglio di calcolo. Per una tesi è perfetto,
perché il risultato del lavoro diventa un allegato che si può consegnare.

La memoria serve a due cose diverse, e abbiamo fatto solo la prima.

**La prima è l'archivio.** I requisiti approvati adesso restano. Ognuno porta con
sé da quale Pull Request nasce, quando quella Pull Request è stata aperta, quando
noi l'abbiamo salvato, e il testo completo da cui è stato ricavato. Quest'ultima
cosa l'abbiamo voluta apposta: apri il file e capisci da solo perché quel
requisito dice quello che dice, senza dover andare a cercare altrove.

**La seconda è dare contesto al valutatore**: prima di giudicare una frase nuova,
mostrargli quelle simili già approvate, così può accorgersi di un doppione o di
una contraddizione. Questa l'abbiamo lasciata spenta di proposito, per tre motivi
che abbiamo preferito affrontare prima invece che dopo.

Il primo è che per capire che due frasi dicono la stessa cosa con parole diverse
serve uno strumento in più, e va scelto quale.

Il secondo riguarda le istruzioni del valutatore. Rileggendole con calma
abbiamo visto che una sezione dedicata c'è già, e dice la cosa giusta: confronta
il requisito nuovo con quelli vecchi, segnala doppioni o contraddizioni, ma non
bocciare una frase solo perché somiglia a un'altra — due Pull Request diverse
possono legittimamente produrre requisiti vicini. Quello che manca è che quella
sezione non compare nell'elenco ordinato di controlli che il valutatore segue
per decidere: è un'istruzione che sta lì di lato, e non sappiamo se la userebbe
davvero. Prima di accendere il recupero vogliamo agganciarla alla procedura.

Il terzo è più sottile e riguarda la tesi. Con la memoria accesa il sistema
diventa **dipendente dall'ordine**: valutando la quarantesima Pull Request si
porta dietro quello che hanno prodotto le trentanove precedenti. È realistico —
nella vita vera i requisiti si accumulano — ma significa che due esecuzioni sullo
stesso materiale in ordine diverso possono dare risultati diversi. Va scritto nel
piano di valutazione prima di vedere i numeri, non dopo.

Alla fine abbiamo fatto una prova piccola, cinque Pull Request, quattro centesimi.
Tre requisiti approvati, tre righe salvate. Abbiamo aperto il file e controllato
riga per riga che ci fosse tutto.

E lì è saltata fuori un'altra conferma, non cercata: sulle stesse cinque Pull
Request, con lo stesso modello e le stesse istruzioni di ieri, **due hanno
cambiato esito**. Una che ieri era stata scartata oggi è stata approvata, e
viceversa. Non abbiamo toccato niente che possa spiegarlo. È esattamente il
fenomeno di ieri sera, e adesso sappiamo che non era un caso isolato di
un'esecuzione: è il comportamento normale del sistema, e va misurato ripetendo
le prove.

---

## 29 agosto — La regola che mancava

### Sabato 29 agosto

Oggi abbiamo risolto il caso dei cinque componenti gemelli, quello che ci aveva
colpito l'altra sera: cinque Pull Request praticamente identiche, quattro esiti
diversi.

Il problema, riguardandolo con calma, non era che il sistema sbagliasse. Era che
gli avevamo chiesto di rispondere a una domanda su cui **non avevamo mai deciso
noi**: se una Pull Request dice soltanto «ho fatto un componente tab», il fatto
che tutti sappiano cos'è un tab basta per scrivere un requisito?

Abbiamo deciso di no. Il motivo che ci ha convinti è semplice: la frase che ne
uscirebbe — «il sistema permette di passare da un pannello all'altro» — è vera
di *qualunque* programma che abbia le schede. Non dice niente su questo
programma. È la definizione della parola. E soprattutto, se il modello riempie
i buchi con quello che sa già lui, quello che misuriamo non è più quanto si
capisce dalle Pull Request, ma quanto ne sa il modello — e la domanda della
tesi si svuota.

La scelta però non è ovvia, e l'abbiamo scritta come tale: una persona
competente, leggendo «ho fatto un tab», qualcosa lo capirebbe lo stesso. Per
questo l'abbiamo messa fra le domande da fare alla tutor, con tutti e due i
ragionamenti e con l'indicazione di quanto costerebbe cambiare idea. Poco: si
cancellano tre paragrafi.

**La parte interessante è stata trovare da dove passava l'errore.** Nelle
istruzioni c'era già una regola che diceva, più o meno: togli dal requisito i
nomi tecnici; se non resta niente, allora quel nome era il punto della Pull
Request ed è giusto tenerlo. Scritta così, applicata a «ho fatto un tab», quella
regola **autorizzava** proprio il caso che volevamo escludere. Non era una
dimenticanza: era una porta lasciata aperta. Adesso la regola distingue i due
casi, in base a cosa dice davvero il testo.

**Poi abbiamo riletto tutte le istruzioni dei due agenti da capo**, cercando
altre contraddizioni. Ne sono uscite quattro cose piccole ma vere: mancava
completamente un esempio di come si dice «non ce la faccio» (c'erano sette
esempi e tutti e sette scrivevano un requisito); una frase della procedura era
scritta in modo ambiguo e poteva essere letta al contrario; un controllo
automatico verificava tre casi su quattro; e abbiamo aggiunto un controllo che
si accorge se i passi della procedura vengono numerati male, perché l'ordine in
cui vanno applicati è sostanza e non forma.

**Infine, due correzioni a cose che avevamo scritto noi nei giorni scorsi.**
Avevamo annotato che il valutatore non sa cosa farsene dei requisiti recuperati
dalla memoria: falso, una sezione dedicata c'era già e dice la cosa giusta.
E avevamo scritto che seguire uno degli schemi di frase è consigliato: in realtà
nel documento di progetto e nelle istruzioni è obbligatorio. Le abbiamo corrette
entrambe, lasciando scritto che si trattava di una rettifica — un diario che si
riscrive di nascosto non serve a niente.

---

## 30 agosto — La memoria comincia a servire a qualcosa

### Domenica 30 agosto — mattina

Prima di tutto abbiamo sistemato una cosa banale ma che ci stava rallentando: il
modo in cui il sistema racconta quello che sta facendo mentre gira. Le prove le
facciamo leggendo il terminale, e finora era un muro di righe tutte uguali, con
le motivazioni degli agenti stampate su righe lunghissime.

Adesso ogni fase è numerata e separata, il testo va a capo, le obiezioni del
valutatore sono contate («problema 1 di 3») e si vede quanto costa ogni singola
chiamata invece del solo totale finale. Provandolo abbiamo anche scoperto che il
costo per chiamata risultava sempre «non disponibile», perché il fornitore
restituisce il nome del modello con la data attaccata e il nostro listino aveva
solo il nome. Sistemato.

### Domenica 30 agosto — pomeriggio

Poi la cosa vera della giornata: **abbiamo finito la memoria.**

Fino a ieri il sistema archiviava i requisiti approvati ma non li faceva vedere a
nessuno. Adesso, prima di giudicare un requisito nuovo, il valutatore riceve
quelli già approvati e può accorgersi che è un doppione, che ne contraddice uno,
o che è una versione più precisa di un altro. È esattamente quello che la
proposta di stage chiede al database di permettere.

**Un solo file invece di tanti.** Prima ogni esecuzione ne creava uno nuovo.
Adesso è uno solo, e ogni requisito porta scritto da quale esecuzione viene: il
recupero filtra su quello, quindi ogni prova si comporta come se partisse da zero
pur restando tutto in un unico file da aprire e sfogliare. Serviva, perché se una
prova vedesse i risultati di quella precedente, confrontare due modelli non
direbbe più niente.

**Niente embedding, per ora.** La decisione di progetto prevedeva uno strumento
che misura quanto due frasi si somigliano, per scegliere quali requisiti mostrare.
Discutendone ci siamo accorti che a questa scala non serve: i requisiti sono
poche decine e si possono mostrare **tutti**. E c'è di più — quello strumento
distingue male una frase dal suo contrario, mentre metà dei nostri requisiti dice
«il sistema **non** deve...», e riconoscere una contraddizione è esattamente
distinguere una cosa dal suo opposto. Il modello che legge il testo quel «non» lo
vede. Abbiamo scritto la scelta con tutte e due le facce e l'abbiamo messa fra le
domande per la tutor.

**E poi il regalo.** Nel nostro campione ci sono due Pull Request con titolo e
corpo **identici parola per parola** — il dataset contiene lo stesso cambiamento
due volte. Ce ne eravamo accorti giorni fa e l'avevamo usato per misurare quanto
il sistema si ripete. Oggi è diventato il caso di prova perfetto: se la memoria
funziona, elaborando la seconda il sistema deve tirare fuori la prima.

Ha funzionato. Il valutatore ha scritto:

> *Questo requisito duplica un requisito già validato della Pull Request #6870,
> che esprime lo stesso comportamento con parole leggermente diverse.*

Due cose ci hanno fatto piacere. La prima è che ha **nominato la Pull Request**,
non ha detto genericamente «è un doppione»: così l'affermazione si può
controllare. La seconda è che l'ha **approvato lo stesso**. Somigliare a un
requisito esistente non è un difetto — due Pull Request diverse possono
legittimamente portare alla stessa cosa — ed era la regola che avevamo scritto
nelle istruzioni un'ora prima.

E il controllo opposto, quello che di solito ci si dimenticherebbe: le Pull
Request che hanno visto requisiti vecchi **senza** esserne parenti non si sono
inventate niente. Una ha segnalato una somiglianza spiegando perché in realtà è
un caso diverso; le altre due hanno taciuto. Se avesse trovato parentele
dappertutto, la funzionalità sarebbe stata peggio che inutile.

**Un difetto scoperto per caso.** Una Pull Request su nove è andata in errore. Il
generatore aveva prodotto una risposta corretta e poi aveva continuato a
ragionare da solo — «aspetta, ripensandoci...» — e il nostro codice, leggendo la
risposta, si portava dietro anche quel pezzo e non la capiva più. Non c'entrava
con il lavoro di oggi: era un difetto che avevamo da sempre e che oggi ci è
costato un caso. Corretto.

Alla fine tutto questo è costato **dieci centesimi**.

### Domenica 30 agosto — sera

Abbiamo provato il sistema con la memoria accesa, due volte: prima con il
modello economico, poi con quello intermedio. E le due prove ci hanno detto cose
diverse, tutte e due utili.

**Con il modello economico è andata male.** Un solo requisito approvato su nove.
Guardando il perché, il valutatore aveva cominciato a pretendere di sapere
**come** era stato fatto il fix: «non sappiamo se hanno validato l'input, se
hanno cambiato metodo, se hanno tolto la funzione». Ma il nostro documento di
progetto dice esattamente il contrario — che non sapere la tecnica **non** è un
motivo per scartare una Pull Request — e porta come esempio proprio uno dei casi
che il sistema ha rifiutato.

**Con il modello intermedio quel problema è sparito del tutto.** Zero casi su
nove. Quindi non erano le istruzioni a essere sbagliate: era il modello piccolo
che applica una regola alla lettera anche dove non c'entra. È la stessa cosa che
avevamo visto il 27 agosto con un'altra regola.

**Ma abbiamo trovato un errore vero, e l'avevo fatto io ieri.** La regola che
avevamo scritto — «il nome di una cosa non basta a dire cosa fa» — si mangiava
per sbaglio un caso diverso: le Pull Request che cambiano un'impostazione
predefinita. Sono cose che sembrano uguali ma non lo sono. «Ho fatto un
componente tab» non dice niente di verificabile; «l'impostazione adesso vale X
invece di Y» è un fatto sul sistema, e si controlla: prendi il programma, non
tocchi niente, guardi quale valore usa.

Il bello è che nel documento avevamo già scritto un esempio identico
classificandolo come **estraibile**. Quindi la regola contraddiceva il nostro
stesso esempio. Corretta, con un'eccezione esplicita e un esempio in più nelle
istruzioni.

**La memoria invece ha funzionato bene**, e con una sorpresa. Oltre a riconoscere
i doppioni — e a registrarli come osservazione senza bocciare, che era la regola
che volevamo — a un certo punto ha fatto una cosa che non avevamo previsto: ha
usato i requisiti già approvati come **metro di misura**. Accettando un
requisito, ha scritto che «rispecchia il livello di generalità di quelli già
accettati». Cioè si è servito della memoria per **restare coerente con sé stesso**
lungo tutto il lotto. Nessuno gliel'aveva chiesto, ed è probabilmente la cosa più
interessante uscita oggi.

**Due cose pratiche da sistemare.** Una Pull Request si è persa perché la
risposta del valutatore ha sbattuto contro il limite di lunghezza — con la
memoria attiva scrive di più, perché deve confrontare. Limite alzato, per la
seconda volta in tre giorni.

E abbiamo capito un limite del modo «memoria che si accumula»: va usato **una
volta sola** su uno stesso gruppo di Pull Request. Rilanciandolo, la memoria si
riempie di versioni diverse dello stesso caso — prodotte dal sistema stesso in
esecuzioni precedenti — e lui le scambia per doppioni veri. Scritto
nell'avvertenza del comando e nel documento.

---

## Situazione a fine agosto

Cosa c'è:

- lo stato dell'arte, diviso in quattro aree;
- sette decisioni di progetto documentate, tenute aggiornate man mano che le
  prove ci facevano cambiare idea;
- lo script che prepara i dati, con la sua piccola interfaccia;
- lo schema interattivo del flusso di lavoro;
- il sistema funzionante dal file di ingresso ai requisiti generati, provato
  sulle Pull Request reali con tutte le combinazioni dei tre modelli;
- un controllo d'ingresso che non usa modelli e costa zero;
- due agenti che si parlano davvero: il secondo ricorda cosa ha già detto, e il
  primo può dichiarare di non riuscire invece di inventare;
- il conteggio dei consumi e la stima dei costi per ogni esecuzione;
- **la memoria, completa**: i requisiti approvati non si perdono più, restano in
  un unico file che si apre e si legge, e vengono mostrati al valutatore quando
  giudica una Pull Request successiva, così può accorgersi di doppioni e
  contraddizioni;
- **due gruppi di Pull Request** su cui provare il sistema, uno piccolo e uno di
  quarantasei scritte da persone;
- un documento che spiega cosa cambia al cambiare dei modelli, con gli esempi
  veri e la verifica sul secondo gruppo;
- duecentoventuno controlli automatici che verificano tutto senza costi.

Cosa manca:

- il gold standard: decidere noi, caso per caso, quale sia l'esito corretto per
  le quarantasei Pull Request — è la cosa che blocca tutto il resto, perché
  senza non possiamo dire se una modifica migliora o solo cambia. Le schede
  preparate il 27 vanno rifatte: erano tarate sul gruppo sbagliato;
- ripetere le esecuzioni più volte, ora che la variabilità non si può più
  spegnere, per capire quanto delle differenze fra modelli sia vera differenza
  e quanto sia rumore — e abbiamo visto due volte che ce n'è parecchia;
- confrontare il sistema **con e senza memoria**: accendere il recupero cambia
  quello che il valutatore legge su ogni Pull Request, quindi sono due
  condizioni da misurare separatamente, non una migliore dell'altra;
- decidere una regola su un punto che il sistema oggi risolve a caso: il nome
  di un componente conosciuto basta da solo a stabilire cosa il sistema deve
  fare, oppure no?
- il modo per consultare la memoria dall'esterno, cioè il pezzo che la proposta
  di stage nomina due volte e che è l'ultimo rimasto;
- l'esecuzione delle prove finali e la raccolta dei risultati.

Prossimo passo concreto: **compilare le schede del gold standard**, ognuno la
propria, senza guardare cosa ha prodotto il sistema. È un lavoro noioso di
un paio di giorni, ed è l'unico che trasforma tutte le impressioni raccolte
finora in qualcosa di misurabile.
