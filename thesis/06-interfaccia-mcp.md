# L'interfaccia MCP per l'accesso alla memoria

**Materiale per la tesi — bozza di capitolo**
Deriva da: `docs/design/decisions/04-Interface-MCP.md` (Decisione 3.4)
Progetto PR4Requirements · Università degli Studi di Milano-Bicocca

---

## 1. Il problema

Il sistema mantiene una memoria persistente dei requisiti validati (capitolo 5).
Resta da stabilire **come i componenti vi accedano**.

La risposta ingenua — chiamare direttamente il repository dal workflow — funziona,
ma lega ogni componente alla forma concreta della persistenza e rende
l'interfaccia proprietaria del progetto. La proposta di stage indica una risposta
diversa: il database deve essere «accessibile dagli agenti tramite **MCP**», e
l'obiettivo formativo dichiarato è studiare «come architetture *agent-based*
supportate dal MCP possano facilitare la ricostruzione e gestione dei requisiti».

MCP è quindi un elemento del lavoro, non un dettaglio realizzativo.

**Una precisazione necessaria.** MCP non è un database e non implementa la
persistenza né il recupero: è un **livello di accesso standardizzato** che sta
sopra i componenti che li realizzano.

```text
Componenti di PR4Requirements
            │
            │ MCP
            ▼
        Server MCP
            │
            ├──► RequirementRepository ──► SQLite
            │
            └──► RequirementRetriever
```

---

## 2. Che cos'è il Model Context Protocol

Un modello linguistico, da solo, produce testo: non può leggere un file né
interrogare un database. Perché possa farlo, l'ambiente che lo ospita deve mettergli
a disposizione delle **capacità**, dichiarandone il nome, i parametri e la forma
del risultato.

MCP standardizza questa dichiarazione. Un *server* MCP espone un insieme di
strumenti; un *client* li scopre e li invoca. Il vantaggio rispetto a
un'interfaccia costruita su misura è che il contratto è descritto una volta e
utilizzabile da qualunque client conforme, non soltanto dal programma che lo ha
scritto.

---

## 3. Obiettivi dell'interfaccia

L'interfaccia deve garantire che:

- gli agenti non eseguano direttamente interrogazioni SQL;
- il backend di persistenza resti nascosto ai componenti agentici;
- le operazioni disponibili siano poche, esplicite e coerenti con il dominio;
- le operazioni di lettura siano separate da quelle che modificano la memoria;
- gli strumenti abbiano ingresso e uscita strutturati;
- **gli errori siano distinguibili da risultati validi ma vuoti**;
- il server sia testabile indipendentemente dagli agenti;
- un cambio futuro del backend non richieda di modificare il contratto.

---

## 4. Le alternative considerate

Una precisazione preliminare vale per tutte e tre: **in nessun caso si assume che
il modello comunichi autonomamente con il database.** L'accesso avviene sempre
attraverso strumenti messi a disposizione dall'ambiente che ospita l'agente. La
differenza riguarda **come quell'interfaccia sia progettata e standardizzata**.

| Soluzione | Descrizione | Vantaggi | Limiti |
|---|---|---|---|
| **Funzioni applicative** | il framework espone funzioni che invocano il repository | poche parti intermedie | interfaccia proprietaria, legata all'implementazione |
| **API applicativa** | un servizio espone operazioni tramite un'API definita dal progetto | separa il servizio dal resto dell'applicazione, consente processi distinti | richiede di progettare e mantenere un protocollo proprio e il relativo adattatore |
| **Server MCP** | le capacità sono esposte come strumenti MCP | protocollo standardizzato, separazione netta, contratto esplicito | introduce un componente da implementare, configurare e testare |

**Scelta: un server MCP dedicato.** Il server non contiene la logica del sistema:
delega al `RequirementRepository` la lettura e la scrittura strutturate, e al
`RequirementRetriever` il recupero dei requisiti affini.

---

## 5. Le primitive utilizzate

MCP prevede diverse primitive. La prima implementazione utilizza soltanto i
**Tools**, perché le operazioni necessarie sono azioni parametrizzate: cercare
requisiti affini, recuperarne uno, recuperare le relazioni registrate, persistere
un requisito validato.

Le primitive *Resources* e *Prompts* non sono necessarie al caso d'uso e non
vengono introdotte. La loro adozione potrà essere valutata soltanto se emergerà un
caso concreto — criterio che vale come principio generale del progetto: non si
introducono componenti in previsione di un bisogno non ancora osservato.

---

## 6. Gli strumenti esposti

L'interfaccia è deliberatamente ridotta a quattro operazioni.

### 6.1 `search_requirements`

Recupera dalla memoria i requisiti da confrontare con un candidato.

```text
ingresso:  candidate_text, repository_id?, before_timestamp?, top_k?
uscita:    requirement_id, statement, source_repository,
           source_pr_number, similarity_score
```

Il parametro `before_timestamp` realizza la consistenza temporale del capitolo 5:
limita il recupero ai requisiti nati da Pull Request anteriori a quella in esame.

Lo strumento **non decide** se due requisiti siano duplicati, sovrapposti o in
conflitto: restituisce evidenza utile a chi deve valutarla. Con memoria vuota
restituisce una lista vuota, che è un risultato valido e non un errore.

### 6.2 `get_requirement`

Recupera un singolo requisito dal suo identificatore.

### 6.3 `get_requirement_relations`

Recupera le relazioni già registrate per un requisito.

### 6.4 `store_accepted_requirement`

Persiste un requisito che ha già concluso la valutazione con esito `ACCEPT`.

```text
ingresso:  statement, source_repository, source_pr_number,
           source_pr_timestamp?, evidence?, relations?
uscita:    requirement_id, created_at
```

Il nome dello strumento rende esplicita la politica del capitolo 5: **la memoria
contiene soltanto requisiti validati**. Lo strumento non decide se il requisito
debba essere accettato — riceve esclusivamente requisiti per i quali la decisione è
già stata presa.

---

## 7. Uno strumento deliberatamente escluso

La formulazione iniziale prevedeva un quinto strumento, `check_consistency`,
incaricato di classificare direttamente la relazione fra un candidato e la memoria
come `NEW`, `DUPLICATE`, `OVERLAPS`, `REFINES`, `SUPERSEDES` o `CONFLICTS`.

**Non è stato incluso.** Una classificazione di questo tipo non è un'operazione di
accesso alla memoria: richiede una valutazione semantica che appartiene alla logica
del Requirement Assessment Agent.

Includerla avrebbe significato spostare una porzione del giudizio dentro il server,
dove sarebbe stata meno visibile e non soggetta agli stessi criteri. Il server
fornisce quindi i requisiti rilevanti tramite `search_requirements`, e la
classificazione resta a chi valuta.

È l'applicazione concreta del principio del §11: **il server MCP non deve diventare
un agente nascosto.**

---

## 8. La separazione fra lettura e scrittura

L'accesso segue una politica esplicita.

**Operazioni di lettura** — `search_requirements`, `get_requirement`,
`get_requirement_relations` — sono utilizzabili dai componenti autorizzati a
consultare la memoria. Nella configurazione iniziale la memoria è consultata in
sola lettura per fornire il contesto storico alla valutazione.

**Operazione di scrittura** — `store_accepted_requirement` — non è affidata né al
generatore né al valutatore. Viene invocata dal **controller della pipeline**,
soltanto dopo che il requisito ha ricevuto esito `ACCEPT`:

```text
Assessment
    │
    ▼
  ACCEPT
    │
    ▼
Controller
    │ MCP
    ▼
store_accepted_requirement
    │
    ▼
RequirementRepository → SQLite
```

La separazione impedisce che requisiti ancora in generazione, in revisione o
rifiutati modifichino la memoria storica. È il presupposto della politica di
persistenza del capitolo 5, ed è realizzata come **vincolo strutturale** anziché
come regola di comportamento: gli agenti non hanno accesso allo strumento di
scrittura.

---

## 9. Contratti ed errori

### 9.1 Contratti strutturati

Ogni strumento ha ingresso e uscita strutturati e validabili. I principi:

- nessuno strumento accetta interrogazioni SQL arbitrarie;
- i parametri sono tipizzati;
- gli identificatori hanno un formato coerente;
- i risultati sono leggibili da un programma;
- gli strumenti di recupero restituiscono le informazioni necessarie a interpretare
  il risultato;
- **un errore non è rappresentato come un risultato valido ma vuoto.**

### 9.2 Gestione degli errori

Il server distingue almeno: memoria vuota; nessun requisito rilevante trovato;
requisito inesistente; ingresso non valido; errore durante il recupero; errore nel
calcolo dell'embedding; errore durante la persistenza; backend non disponibile.

Il principio operativo è:

> Una lista vuota restituita correttamente da `search_requirements` **non deve
> essere confusa** con un fallimento del recupero.

La distinzione ha una conseguenza sperimentale diretta. «Nessun requisito
pertinente» e «il recupero è fallito» portano a esiti identici nel comportamento
osservabile del sistema — il valutatore non riceve nulla — ma significano cose
opposte quando si analizzano i risultati. Confonderli renderebbe impossibile
accorgersi di un guasto.

Gli errori vanno propagati in forma strutturata e tracciabile, **senza generare
valori sostitutivi**: il sistema non deve mai inventare un risultato per proseguire.

---

## 10. Il trasporto

Per la prima implementazione locale si adotta **stdio**: il server viene eseguito
come processo figlio e comunica attraverso i flussi standard.

```text
PR4Requirements
      │ stdio / MCP
      ▼
  Server MCP
      │
      ▼
Memoria persistente
```

Non è necessario esporre il server sulla rete. Qualora dovesse essere eseguito come
servizio remoto, lo standard prevede un trasporto HTTP adottabile **senza
modificare la semantica degli strumenti** definiti in questo capitolo — proprietà
che rende la scelta iniziale non vincolante.

---

## 11. Il confine fra MCP e logica agentica

> **Il server MCP non deve diventare un ulteriore agente nascosto.**

Il suo compito è esporre in modo controllato le capacità della memoria. La
ripartizione delle responsabilità è:

| Componente | Responsabilità |
|---|---|
| **MCP** | accesso standardizzato |
| **RequirementRepository** | persistenza e interrogazioni strutturate |
| **RequirementRetriever** | recupero dei requisiti affini |
| **Assessment Agent** | interpretazione e valutazione delle relazioni |
| **Controller** | decisione di persistenza dopo `ACCEPT` |

Il criterio pratico che ne discende è che **la logica degli strumenti deve restare
sottile**: validazione dell'ingresso, chiamata al componente applicativo, gestione
degli errori, serializzazione dell'uscita. Nient'altro.

La conseguenza progettuale è che i componenti sottostanti vanno costruiti **prima**
del server, e con firme compatibili con quelle degli strumenti. Se il retriever
accettasse soltanto un oggetto che rappresenta la Pull Request, lo strumento MCP —
che riceve parametri sciolti — dovrebbe fabbricarne uno per poterlo chiamare: sarebbe
esattamente la logica grassa che questo principio esclude. Nell'implementazione il
recupero espone quindi un'operazione con i parametri del contratto, oltre a quella
usata dal workflow.

---

## 12. Testabilità

La sottigliezza degli strumenti consente di verificare separatamente cinque livelli:

1. la logica del repository;
2. la logica del recupero;
3. il contratto degli strumenti MCP;
4. l'integrazione fra MCP e memoria;
5. l'uso degli strumenti all'interno del workflow.

L'ordine non è casuale: è anche l'**ordine in cui i componenti vanno realizzati**.
MCP è un involucro, e non si può verificare un involucro attorno a qualcosa che non
esiste. Se si costruisse prima il server e il recupero risultasse difettoso, non si
saprebbe distinguere un difetto del recupero da uno del trasporto.

Per i test del server può essere usata una memoria temporanea, evitando dipendenze
dallo stato reale della memoria sperimentale.

---

## 13. Stato dell'implementazione

Alla data di stesura, i componenti sottostanti — repository e recupero — sono
realizzati e verificati, mentre **il server MCP non è ancora implementato**: il
workflow accede direttamente ai due componenti.

La sostituzione è predisposta. Nel codice, il workflow dipende da interfacce
dichiarate (`MemoryRetriever`, `AcceptedRequirementStore`) e non
dall'implementazione concreta: un client MCP potrà prenderne il posto **senza
modifiche al grafo né agli agenti**.

Questa è la sola componente prevista dall'architettura che resta da realizzare, e
va dichiarata come tale.

---

## 14. Limiti e questioni aperte

**Da consolidare:** gli schemi esatti di ingresso e uscita degli strumenti; i nomi
definitivi dei campi; il formato standard degli errori; timeout e politiche di
ritentativo; l'eventuale registrazione delle invocazioni; la modalità con cui
persistere le relazioni individuate dal valutatore; l'eventuale strumento
amministrativo per elencare i requisiti; l'eventuale introduzione delle *Resources*;
l'eventuale passaggio a un trasporto remoto.

**Una divergenza dalla proposta di stage, da sottoporre alla tutor.** La proposta
indica che il database sia «accessibile **dagli agenti** tramite MCP». L'architettura
adottata (capitolo 3, §7.2) prevede invece che il recupero sia eseguito dal
**workflow in modo deterministico**, e non lasciato alla decisione del modello, per
quattro ragioni: ogni candidato viene valutato nelle stesse condizioni, il numero di
accessi è controllabile, il comportamento è riproducibile, e il sistema può essere
eseguito con memoria attiva o disattivata in modo controllato.

L'accesso resta quindi mediato: i requisiti recuperati raggiungono il valutatore,
ma è il workflow a decidere quando interrogare la memoria. La divergenza è motivata
— e le misure sulla variabilità (capitolo 4) la rafforzano — ma va dichiarata
esplicitamente e discussa.

**Una domanda metodologica connessa.** Se l'unico client del server è il workflow
stesso, MCP rischia di apparire un'indirezione su una chiamata di funzione. Le
risposte esistono — standardizza l'accesso per client futuri, impone la separazione
fra lettura e scrittura, è verificabile come contratto indipendente — ma la
dimostrazione più efficace sarebbe **un secondo client**: collegare il server a un
ambiente diverso e interrogare la memoria da lì renderebbe evidente, e non soltanto
argomentato, il beneficio dello standard.

---

## Riferimenti

- **Model Context Protocol** — specifica ufficiale.
- **MCP Python SDK** — SDK ufficiale per client e server.
- Decisione 3.1 — forma e qualità dei requisiti (capitolo 1).
- Decisione 3.3 — memoria persistente (capitolo 5).
- Decisione 3.5 — architettura multi-agente (capitolo 3).
