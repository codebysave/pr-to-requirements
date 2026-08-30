# La memoria persistente dei requisiti validati

**Materiale per la tesi — bozza di capitolo**
Deriva da: `docs/design/decisions/03-memory-persistence-requirements.md` (Decisione 3.3)
Progetto PR4Requirements · Università degli Studi di Milano-Bicocca

---

## 1. Il problema

La proposta di stage richiede che i requisiti validati siano conservati in un
database persistente che «funge da *long-term memory* e consente di verificare
duplicazioni o incoerenze con i requisiti già generati».

La formulazione contiene **due funzioni distinte**, che conviene tenere separate
perché hanno rischi e vincoli diversi.

**Archivio.** I requisiti accettati si accumulano e costituiscono l'esito del
sistema nel tempo. Senza, ogni esecuzione ripartirebbe da zero e nulla
sopravviverebbe: il sistema sarebbe uno script che produce un rapporto, non un
sistema che accumula conoscenza. Alla fine del lavoro, **il database è il
risultato**: N requisiti funzionali, ciascuno tracciabile alla Pull Request da cui
è stato ricostruito.

**Contesto per la valutazione.** Prima di giudicare un candidato, il sistema
recupera i requisiti già validati e li mette a disposizione del valutatore, che può
così riconoscere duplicazioni, sovrapposizioni e contraddizioni.

La prima funzione non altera il comportamento degli agenti; la seconda sì. La
distinzione, che nel progetto si traduce in **due interruttori indipendenti**,
attraversa tutto il capitolo.

---

## 2. I requisiti della soluzione

La memoria deve consentire di: conservare in modo persistente i requisiti
validati; assegnare a ciascuno un identificatore univoco; mantenere la
tracciabilità verso la Pull Request di origine; recuperare per identificatore e per
metadati; applicare filtri per repository e per intervallo temporale; recuperare i
requisiti affini a un candidato; rappresentare relazioni fra requisiti; garantire
aggiornamenti consistenti; consentire copie e istantanee per gli esperimenti;
mantenere una complessità proporzionata alla scala del progetto.

A questi si aggiunge un requisito meno ovvio, la **consistenza temporale**: quando
il sistema deve ricostruire la memoria disponibile a un determinato istante, il
recupero deve poter essere limitato ai requisiti anteriori a quel momento. È il
vincolo che distingue una simulazione realistica da una che mostra al sistema
informazioni che, nella storia del progetto, non esistevano ancora.

---

## 3. La scelta del backend

| Soluzione | Vantaggi | Limiti |
|---|---|---|
| **File JSON / JSONL** | semplice, ispezionabile, nessuna infrastruttura | query, aggiornamenti, vincoli e relazioni da gestire nel codice |
| **SQLite** | database relazionale in un singolo file; query, vincoli, indici, transazioni; nessun servizio | nessuna ricerca vettoriale nativa |
| **Database vettoriale dedicato** | ricerca semantica nativa | componente infrastrutturale non necessario a questa scala |
| **PostgreSQL + pgvector** | robusto, ricerca vettoriale, concorrenza | richiede un servizio dedicato e configurazione operativa |

La scelta adottata è **SQLite**.

Offre schema relazionale, vincoli, indici, query e transazioni senza introdurre un
servizio separato. Tre proprietà pesano in modo particolare in un contesto di tesi:

**È un singolo file.** Un esperimento diventa un allegato che si copia, si archivia
e si consegna. Con un database servito occorrerebbe spiegare come ricostruire il
servizio.

**Non aggiunge dipendenze.** Il modulo `sqlite3` fa parte della libreria standard
di Python: nessuna installazione, nessuna versione da gestire.

**Le transazioni proteggono la coerenza.** Una scrittura o va a buon fine
interamente o non avviene: non si producono righe parziali.

Un database vettoriale o PostgreSQL restano alternative tecnicamente valide, da
rivalutare se il numero di requisiti o i vincoli di prestazione lo rendessero
necessario.

---

## 4. La politica di persistenza

> La memoria contiene **soltanto requisiti che hanno superato la valutazione con
> esito `ACCEPT`**.

I requisiti in fase di generazione o revisione non vi entrano; un requisito
respinto nemmeno.

```text
Requisito candidato
        │
        ▼
   Valutazione
   │      │      │
ACCEPT REVISE REJECT
   │      │      │
   ▼      └──→ nuova generazione
Persistenza
```

La scelta evita che output non validati vengano successivamente recuperati come
conoscenza storica e influenzino altre valutazioni. La scrittura avviene inoltre
**fuori dagli agenti**, per iniziativa del controller della pipeline (capitolo 3,
§12): né il generatore né il valutatore possono modificare la memoria.

Una conseguenza va notata perché ha effetti pratici: **il database non registra le
Pull Request elaborate, ma solo quelle che hanno prodotto un requisito**. Delle
Pull Request classificate come non estraibili non resta traccia in memoria. Il dato
esiste nei rapporti di esecuzione, ma la memoria da sola non consente di sapere che
cosa sia già stato elaborato — limite rilevante per un'eventuale elaborazione
incrementale (§10).

---

## 5. Lo schema

### 5.1 La tabella dei requisiti

| Campo | Descrizione |
|---|---|
| `id` | identificatore interno del requisito |
| `statement` | testo finale del requisito validato |
| `source_repository` | repository della Pull Request di origine |
| `source_pr_number` | numero della Pull Request di origine |
| `source_pr_timestamp` | **data della Pull Request**, per l'ordinamento e il recupero storico |
| `evidence` | testo della Pull Request da cui il requisito è stato ricostruito |
| `created_at` | **data di inserimento** in memoria |
| `embedding` | rappresentazione vettoriale, se adottata |
| `embedding_model` | modello usato per produrla |
| `run_id` | esecuzione che ha prodotto la riga |

Quattro scelte meritano una motivazione.

**Due date distinte, e non è una ridondanza.** `source_pr_timestamp` è quando la
Pull Request è stata aperta; `created_at` è quando la riga è stata scritta. Il
filtro storico deve usare la **prima**: filtrare sulla seconda ricostruirebbe
l'ordine in cui le esecuzioni sono state lanciate, non la storia del progetto. Le
date sono normalizzate a UTC, così che l'ordinamento lessicografico delle stringhe
ISO coincida con quello cronologico anche fra fusi orari diversi.

**Nessun vincolo di unicità sulla coppia repository/numero.** Nella configurazione
corrente una Pull Request produce al più un requisito, ma inciderlo nello schema
costringerebbe a una migrazione se un giorno ne producesse due — possibilità
esplicitamente prevista fra le questioni aperte (capitolo 1, §13).

**L'evidenza viene conservata.** Il testo della Pull Request è salvato insieme al
requisito. Il costo è dell'ordine di poche decine di kilobyte; il beneficio è che
**il database è autosufficiente**: si legge un requisito e si vede da cosa nasce,
senza disporre del file di input. Per un allegato di tesi è la differenza fra un
artefatto leggibile e una tabella di stringhe.

**L'identificativo dell'esecuzione.** È l'unica aggiunta rispetto alla formulazione
originaria dello schema, e nasce dall'implementazione: in un database condiviso fra
più esecuzioni, senza di esso non si potrebbe sapere quale esecuzione abbia
prodotto quale requisito, né isolare le esecuzioni fra loro (§7).

### 5.2 La tabella delle relazioni

Le relazioni fra requisiti sono rappresentate separatamente, per non introdurre
strutture complesse nella riga del requisito. Le categorie previste sono
`DUPLICATE`, `OVERLAPS`, `REFINES`, `SUPERSEDES`, `CONFLICTS`.

**Stato dell'implementazione.** La tabella e le relative operazioni esistono, ma
**nessun componente della pipeline le alimenta**: le relazioni osservate dal
valutatore finiscono oggi nel rapporto di esecuzione, non nella tabella. Si tratta
di predisposizione, non di funzionalità, e va riportato come tale.

---

## 6. Il recupero dei requisiti affini

### 6.1 La soluzione progettata: recupero semantico

Il progetto prevedeva un recupero basato su **embedding**: una rappresentazione
numerica del significato di una frase, prodotta da un modello addestrato allo
scopo, tale che due frasi che esprimono lo stesso comportamento con parole diverse
producano rappresentazioni vicine. Si misura la distanza e si conservano i primi
*k* risultati.

La necessità è reale quando i requisiti sono molti. Un esempio dal corpus: due
Pull Request quasi gemelle hanno prodotto

> The system shall correctly map file store paths that contain a **tilde (~)
> character** when running in a nested Docker environment.

> The system shall properly resolve and mount file store paths containing **home
> directory references** in the Docker nested runtime.

Le due frasi dicono la stessa cosa senza condividere le parole decisive: una
ricerca testuale non le accosterebbe mai.

### 6.2 La soluzione implementata: recupero esaustivo

L'implementazione adotta un **recupero esaustivo**: restituisce al valutatore
*tutti* i requisiti validati dello stesso progetto nati da Pull Request anteriori a
quella in esame, senza ordinarli per somiglianza.

La scelta è motivata da tre ragioni.

**A questa scala non c'è nulla da selezionare.** Un requisito occupa una trentina
di token: le poche decine prodotte dal corpus più grande aggiungono circa mille
token al messaggio del valutatore, che ne riceve già quasi quattromila — pochi
centesimi per esecuzione.

**La selezione semantica introdurrebbe tre elementi da difendere**: una dipendenza
esterna, una soglia arbitraria da calibrare, e una nozione di «stesso significato»
presa da un modello di terze parti addestrato su testo generico, che andrebbe
dichiarata fra le assunzioni della valutazione sperimentale.

**Gli embedding falliscono proprio dove servirebbero.** Distinguono male una frase
dal suo contrario — *«the system shall execute code from untrusted input»* e *«the
system shall **not** execute…»* sono quasi identici in quello spazio — mentre una
quota rilevante dei requisiti prodotti è in forma negativa, e **riconoscere una
contraddizione significa esattamente distinguere un requisito dal suo opposto**. Un
modello che legge il testo la negazione la vede.

Le colonne per gli embedding restano nello schema: l'adozione futura non richiederà
migrazioni. La scelta è sottoposta alla tutor, insieme al confronto fra un servizio
esterno e un modello locale.

### 6.3 I due filtri

Il recupero applica due filtri, che insieme costituiscono l'intero criterio di
selezione:

**Progetto.** I requisiti di un altro repository non sono pertinenti.

**Data.** Soltanto i requisiti nati da Pull Request **anteriori** a quella in
esame. Il filtro è **esclusivo**, e da questo deriva una proprietà utile non
progettata: una Pull Request non incontra mai il requisito prodotto per sé stessa in
un'esecuzione precedente, perché la data coincide. Il sistema non può copiarsi.

Un limite di sicurezza sul numero di requisiti restituiti impedisce che un archivio
cresciuto oltre le previsioni gonfi il messaggio senza che nessuno se ne accorga.
Non è un `top_k`: il recupero resta esaustivo, e se il limite scatta viene
segnalato.

---

## 7. Un solo database, esecuzioni isolate

Il database predefinito è un **unico file** condiviso da tutte le esecuzioni.
L'isolamento non è affidato al nome del file ma alla colonna `run_id`: il recupero
vi filtra sopra, e ogni esecuzione si comporta **come se partisse da una memoria
vuota**.

La scelta risponde a un vincolo sperimentale preciso. Se un'esecuzione vedesse i
requisiti prodotti da quella precedente partirebbe avvantaggiata, e il confronto fra
due configurazioni perderebbe significato.

In cambio si ottiene un solo artefatto da aprire, sfogliare e allegare, e il
confronto fra due esecuzioni diventa un'interrogazione anziché un raffronto fra
file.

Un parametro consente di rimuovere il filtro, restituendo il comportamento di una
memoria che si accumula davvero nel tempo — il modo previsto per l'uso reale, non
per gli esperimenti.

> **Avvertenza.** La modalità cumulativa va usata **una sola volta per corpus**.
> Rielaborando lo stesso insieme di Pull Request, la memoria si riempie di più
> varianti dello stesso caso, una per esecuzione, e il valutatore le incontra come
> duplicati genuini. In una prova, una Pull Request ha ricevuto tre requisiti
> «duplicati», due dei quali erano l'esito che il sistema stesso aveva prodotto per
> un'altra Pull Request in esecuzioni precedenti.

---

## 8. L'astrazione e l'accesso tramite MCP

L'accesso al database è incapsulato in due componenti distinti:

```text
PR4Requirements
       │
       ▼
RequirementRepository  →  persistenza, metadati, filtri, relazioni
RequirementRetriever   →  quali requisiti mostrare al valutatore
       │
       ▼
     SQLite
```

La separazione consente di sostituire il backend o la strategia di recupero senza
modificare la logica degli agenti. Nell'implementazione, gli agenti dipendono da
interfacce dichiarate nel workflow, non dal database.

Sopra questi due componenti è previsto il **server MCP** (capitolo 6), che espone la
memoria come capacità standardizzata:

```text
Controller / workflow
        │ MCP
        ▼
   Server MCP
        │
        ▼
Repository / Retriever
        │
        ▼
     SQLite
```

MCP **non rappresenta il database e non implementa la persistenza**: fornisce
un'interfaccia standardizzata attraverso cui la memoria viene interrogata. Nello
stato attuale dell'implementazione il workflow accede direttamente ai due
componenti; il passaggio attraverso MCP li sostituirà dietro le stesse interfacce.

---

## 9. Riproducibilità e gestione della memoria

Il fatto che la memoria sia un singolo file rende possibile: inizializzare una
memoria vuota; creare istantanee a un punto dell'esecuzione; duplicare il file per
confrontare configurazioni; conservare una copia associata a una determinata
esecuzione; ricostruire una memoria rispettando l'ordine temporale.

Il file non viene mantenuto sotto controllo di versione — è binario e cambia a ogni
esecuzione — ma **archiviato come artefatto dell'esperimento** insieme alla
configurazione che l'ha prodotto.

---

## 10. Verifica del funzionamento

Il corpus ha fornito un caso di verifica che non sarebbe stato possibile costruire
meglio: **due Pull Request con titolo e corpo identici byte per byte**, cioè lo
stesso cambiamento presente due volte nel dataset.

Con il recupero attivo, elaborando la seconda il sistema ha restituito il requisito
accettato per la prima, e il valutatore lo ha riconosciuto nominando la Pull Request
di origine — condizione che rende l'osservazione verificabile e non generica. La
decisione è rimasta `ACCEPT`: la relazione è stata **registrata, non trattata come
un difetto della frase**, che era il comportamento voluto.

Altrettanto importante è il controllo negativo: le Pull Request che hanno ricevuto
requisiti storici **senza esservi collegate** non hanno prodotto segnalazioni. Una ha
riportato una sovrapposizione spiegando perché il caso fosse distinto; altre, pur
avendo davanti fino a otto requisiti estranei, non ne hanno menzionato alcuno.

Un comportamento non previsto merita di essere riportato. In un caso il valutatore
ha usato la memoria come **riferimento di calibrazione del livello di astrazione**,
accettando un requisito perché «rispecchia il livello di generalità usato nei
requisiti di sicurezza già accettati». La memoria ha cioè contribuito alla coerenza
del corpus, non solo al riconoscimento di duplicati — un uso che il progetto non
aveva previsto.

---

## 11. Limiti e questioni aperte

**Il recupero rende il sistema dipendente dall'ordine.** Valutando la *n*-esima
Pull Request, il valutatore ha davanti i requisiti prodotti dalle precedenti: due
esecuzioni in ordine diverso possono differire. È realistico, ma rende la memoria
attiva e disattiva **due condizioni sperimentali distinte** (capitolo 7).

**Non esiste elaborazione incrementale.** Il sistema non ha nozione di «Pull Request
già elaborata». Rieseguendo su un insieme ampliato, quelle già trattate vengono
rielaborate, con un costo e una proliferazione di varianti. La soluzione non è
immediata, per la ragione del §4: la memoria contiene solo i requisiti accettati e
non sa quali Pull Request siano state elaborate. Occorrerebbe una tabella dedicata
al tracciamento, oppure la lettura dei rapporti di esecuzione precedenti.

**La tabella delle relazioni è vuota.** Nessun componente la alimenta.

**Da consolidare:** il modello di embedding, se e come persistere i vettori e in
quale formato; l'eventuale indice vettoriale; la tassonomia definitiva delle
relazioni; i parametri del recupero semantico (`top_k`, soglia di similarità),
qualora venisse adottato.

**Limiti di SQLite da tenere presenti** se le condizioni cambiassero: assenza di un
motore vettoriale nativo; scarsa adeguatezza a scenari con molti scrittori
concorrenti; confronto esaustivo degli embedding poco conveniente su collezioni
molto grandi. Nessuno di questi è critico nella configurazione attuale, in cui la
memoria è aggiornata da un unico flusso controllato.

---

## Riferimenti interni

- Decisione 3.1 — forma e qualità dei requisiti (capitolo 1).
- Decisione 3.4 — interfaccia MCP (capitolo 6).
- Decisione 3.5 — architettura degli agenti (capitolo 3).
- Decisione 3.7 — piano di valutazione (capitolo 7).
