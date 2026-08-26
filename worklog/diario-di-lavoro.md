# Diario di lavoro — PR4Requirements

Diario dello stage di Andrea Saverino e Marco Saverino Salvatore.
Università degli Studi di Milano-Bicocca — tutor: Benedetta Donato.

Annotiamo qui, giorno per giorno, cosa abbiamo fatto, cosa abbiamo deciso e
dove ci siamo bloccati. È un racconto del lavoro, non una documentazione
tecnica: per quella ci sono i documenti di design in `docs/` e il registro
delle modifiche in `recap.md`.

---

## Settimana 1 — Avvio e inquadramento del problema

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

## Settimana 2 — Stato dell'arte

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

## Settimana 3 — Nascita del progetto

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
cartelle. Abbiamo dato al progetto il nome interno **PR4Requirements**, e al
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

## Settimana 4 — Stato dell'arte e prime decisioni

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

## Settimana 5 — Le decisioni di design

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

## Settimana 6 — Dal progetto al codice

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

---

## Situazione a fine agosto

Cosa c'è:

- lo stato dell'arte, diviso in quattro aree;
- sette decisioni di progetto documentate;
- lo script che prepara i dati, con la sua piccola interfaccia;
- lo schema interattivo del flusso di lavoro;
- il sistema funzionante dal file di ingresso ai requisiti generati;
- una serie di controlli automatici che verificano tutto senza costi.

Cosa manca:

- la chiave di accesso al servizio, per eseguire il sistema sui dati veri;
- la memoria dei requisiti già approvati e il modo per consultarla;
- la scelta definitiva del progetto e delle Pull Request da usare;
- il riferimento costruito a mano per la valutazione;
- l'esecuzione delle prove e la raccolta dei risultati.

Prossimo passo concreto: appena disponibile l'accesso al servizio, eseguire il
sistema su poche Pull Request per vedere che tipo di requisiti produce e
correggere le istruzioni degli agenti sulla base di quello che otteniamo.
