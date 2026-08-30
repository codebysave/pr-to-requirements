# Decisione 3.5 — Architettura degli agenti e loop di retry

**Fase:** 3 — Design del sistema  
**Stato:** Proposta da validare  
**Autori:** Andrea, Marco  
**Data:** Agosto 2026

---

## 1. Contesto

PR-to-Requirements utilizza due componenti agentici principali:

- **Requirement Generation Agent**, responsabile della produzione di un requisito funzionale candidato;
- **Requirement Assessment Agent**, responsabile della valutazione del requisito generato rispetto all'evidenza disponibile, ai criteri di qualità definiti per il progetto e, quando prevista, alla memoria persistente dei requisiti già validati.

La pipeline non viene progettata come un insieme di agenti autonomi che decidono liberamente il proprio comportamento, ma come una **macchina a stati controllata**, nella quale ogni passaggio, diramazione e condizione di terminazione è definito esplicitamente.

La presente decisione stabilisce:

- il framework di orchestrazione;
- i componenti agentici e non agentici;
- lo stato condiviso della pipeline;
- il ciclo `Generation → Assessment → Revision`;
- le condizioni `ACCEPT`, `REVISE`, `REJECT` e `CONFIRM_NOT_EXTRACTABLE`;
- il numero massimo di tentativi;
- la gestione del feedback;
- il comportamento al raggiungimento del limite;
- il ruolo della memoria persistente e di MCP durante il loop;
- la politica di persistenza del requisito finale;
- l'elaborazione di file contenenti più Pull Request tramite un runner applicativo;
- le informazioni da conservare per tracciabilità, debug e valutazione sperimentale.

---

## 2. Obiettivi dell'architettura

L'architettura deve garantire che:

- la generazione e la valutazione siano responsabilità distinte;
- ogni requisito candidato venga valutato prima di poter essere persistito;
- il feedback dell'Assessment Agent possa guidare una nuova generazione;
- il numero di iterazioni sia limitato e configurabile;
- un requisito non valido non venga accettato soltanto perché ha ottenuto un buon punteggio complessivo;
- gli effetti permanenti sulla memoria avvengano esclusivamente dopo `ACCEPT`;
- il comportamento della pipeline sia riproducibile e osservabile;
- le decisioni di routing siano centralizzate e non lasciate implicitamente agli agenti;
- il workflow possa essere eseguito sia con memoria attiva sia con memoria disattivata.

---

## 3. Framework di orchestrazione

Per l'orchestrazione della pipeline viene adottato **LangGraph**.

La scelta è motivata dalla natura del workflow, che richiede:

- uno stato condiviso;
- nodi con responsabilità differenti;
- routing condizionale;
- un ciclo di revisione;
- condizioni esplicite di terminazione;
- integrazione di componenti LLM e componenti deterministiche.

LangGraph viene utilizzato come infrastruttura di controllo del flusso, non come sostituto della logica applicativa.

Il comportamento previsto è rappresentato concettualmente come segue:

```text
File JSON normalizzato con 1..N Pull Request
          │
          ▼
PullRequestLoader
          │
          ▼
Lista di PullRequestRecord
          │
          ▼
Pipeline Runner
          │
          │ seleziona una PR alla volta
          ▼
Pull Request corrente
          │
          ▼
Verifica di estraibilità
     │             │
     │             └── NOT_EXTRACTABLE → END PR
     │
     ▼
Requirement Generation Agent
     │
     ▼
Requisito candidato
     │
     ▼
Recupero memoria
     │
     ▼
Requirement Assessment Agent
     │
 ┌───┼────────────┐
 │   │            │
 ▼   ▼            ▼
ACCEPT REVISE    REJECT
 │      │          │
 │      │          └────────────→ END PR
 │      │
 │      ▼
 │   limite raggiunto?
 │      │
 │   NO │ YES
 │      │
 │      └────────────→ FAILED_VALIDATION → END PR
 │
 │ NO
 └──────────────────→ Requirement Generation Agent

ACCEPT
   │
   ▼
Controller
   │
   │ MCP
   ▼
Persistenza
   │
   ▼
END PR
   │
   ▼
Pipeline Runner
   │
   ├── esiste un'altra PR? → sì → avvia nuova esecuzione LangGraph
   └── nessuna PR restante → END BATCH
```

---

## 4. Componenti della pipeline

La prima versione distingue chiaramente tra **agenti LLM** e **componenti deterministiche di orchestrazione**.

### 4.1 Requirement Generation Agent

È il componente responsabile della generazione del requisito funzionale candidato.

Riceve:

- titolo della Pull Request;
- body della Pull Request;
- eventuale requisito candidato precedente;
- eventuale feedback strutturato dell'Assessment Agent.

Produce:

- un requisito funzionale candidato;
- eventuali metadati necessari al workflow.

Il Generation Agent non decide se il proprio output sia valido e non persiste direttamente il requisito nella memoria finale.

---

### 4.2 Requirement Assessment Agent

È il componente responsabile della valutazione del requisito candidato.

La valutazione considera:

- aderenza all'evidenza disponibile;
- assenza di informazioni non supportate;
- natura funzionale del requisito;
- atomicità;
- chiarezza;
- verificabilità;
- livello di astrazione appropriato;
- eventuali relazioni con requisiti storici recuperati dalla memoria.

Produce una decisione tra:

```text
ACCEPT
REVISE
REJECT
CONFIRM_NOT_EXTRACTABLE
```

insieme a feedback strutturato e informazioni utili al routing.

---

### 4.3 Componenti non agentici

Non tutte le fasi della pipeline vengono modellate come agenti.

La prima architettura prevede componenti deterministiche per:

- verifica e instradamento dello stato;
- conteggio dei tentativi;
- recupero dalla memoria;
- chiamate MCP;
- persistenza;
- logging;
- gestione dello stato finale.

La verifica di estraibilità è una fase preliminare della pipeline e non un terzo agente autonomo. È stata implementata come **controllo deterministico**: scarta soltanto le Pull Request prive di testo sufficiente perché una qualsiasi valutazione sia possibile. La scelta risponde a tre ragioni: un controllo sintattico è riproducibile, mentre un modello può cambiare esito fra un'esecuzione e l'altra; il giudizio semantico richiede di vedere il requisito, che a questo stadio non esiste ancora; e il costo è nullo. Il giudizio sull'identificabilità di un comportamento appartiene quindi al ciclo, dove il generatore lo formula e il valutatore lo verifica (§10.4).


### 4.4 Pipeline Runner

Per gestire file di input che contengono più Pull Request introduciamo un componente deterministico chiamato **Pipeline Runner**.

Il Runner serve a risolvere un problema semplice ma importante: il `PullRequestLoader` può leggere e validare un file contenente `1..N` Pull Request, mentre una singola esecuzione del workflow LangGraph lavora sullo stato di **una sola PR alla volta**.

La responsabilità viene quindi separata nel modo seguente:

```text
PullRequestLoader
    ↓
legge e valida il file
    ↓
restituisce le PR normalizzate

Pipeline Runner
    ↓
prende una PR alla volta
    ↓
invoca LangGraph
    ↓
attende lo stato finale della PR
    ↓
passa alla PR successiva
```

Abbiamo deciso di non assegnare questa responsabilità al Loader, perché il Loader deve rimanere un componente dedicato alla lettura e alla validazione dell'input, senza avviare direttamente agenti o workflow.

Il Runner non è un agente LLM e non prende decisioni semantiche. È un livello applicativo molto semplice che:

- riceve la collezione di `PullRequestRecord` prodotta dal Loader;
- determina l'ordine di elaborazione;
- invoca il workflow LangGraph separatamente per ogni PR;
- aspetta che la PR corrente raggiunga uno stato finale;
- raccoglie il risultato dell'esecuzione;
- passa quindi alla PR successiva.

La prima implementazione sarà intenzionalmente semplice. Il Runner potrà coincidere con poche righe di orchestrazione nell'entry point dell'applicazione, ad esempio:

```python
pull_requests = loader.load(input_path)

for pr in pull_requests:
    result = graph.invoke(create_initial_state(pr))
    save_run_result(result)
```

Non è quindi necessario introdurre inizialmente un servizio o una classe complessa dedicata al batch processing.

Quando è disponibile un riferimento temporale affidabile, le PR vengono elaborate in **ordine cronologico**, dalla più vecchia alla più recente. Questa scelta è particolarmente importante quando la memoria persistente è attiva: una PR successiva può consultare requisiti validati da PR precedenti, mentre una PR storicamente precedente non deve poter recuperare requisiti provenienti dal futuro.

Il Runner introduce quindi un **ciclo esterno** distinto dal retry loop interno gestito da LangGraph:

```text
Ciclo esterno — Runner
PR1 → PR2 → PR3 → ... → PRn

Ciclo interno — LangGraph
Generation → Retrieval → Assessment
                    │
                    └── REVISE → Generation
```

Prima di passare alla PR successiva, la PR corrente completa interamente il proprio workflow, compresi eventuali retry, retrieval e persistenza successiva a `ACCEPT`.

Il Runner non modifica il `RequirementState` della PR corrente oltre alla normale inizializzazione dell'esecuzione e non sostituisce LangGraph nel routing interno. Il suo compito è esclusivamente coordinare le **esecuzioni successive del grafo**.

---

## 5. Stato condiviso

La pipeline utilizza uno stato condiviso che viene aggiornato progressivamente dai nodi.

Una struttura concettuale iniziale è:

```text
RequirementState
│
├── Pull Request
│   ├── pr_id
│   ├── repository_id
│   ├── title
│   └── body
│
├── Extractability
│   ├── extractability
│   └── extractability_reason
│
├── Generation
│   ├── candidate_requirement
│   └── generation_attempt
│
├── Memory
│   └── retrieved_requirements
│
├── Assessment
│   ├── assessment_decision
│   ├── assessment_feedback
│   ├── unsupported_claims
│   ├── missing_information
│   └── memory_relation
│
├── Final
│   ├── final_status
│   └── accepted_requirement
│
└── Trace
    └── iteration_history
```

Lo stato rappresenta il contesto corrente della singola elaborazione.

Il contenuto completo dello stato non viene necessariamente passato integralmente agli LLM: ogni agente riceve soltanto le informazioni necessarie alla propria responsabilità.

---

## 6. Verifica di estraibilità

Prima della generazione viene verificato se dalla Pull Request sia possibile ricostruire almeno un requisito funzionale supportato dall'evidenza disponibile.

Gli esiti principali sono:

```text
EXTRACTABLE
NOT_EXTRACTABLE
```

In caso di `NOT_EXTRACTABLE`, la pipeline termina senza invocare il Generation Agent e senza persistere alcun requisito.

In caso di `EXTRACTABLE`, il workflow procede alla generazione.

La policy dettagliata relativa ai casi funzionali, mixed, non funzionali e insufficientemente informativi viene documentata separatamente nei criteri sperimentali e nei punti aperti concordati con la tutor.

---

## 7. Primo tentativo di generazione

Al primo passaggio il Generation Agent riceve esclusivamente l'evidenza prevista dall'esperimento e produce un requisito candidato.

Il requisito deve essere formulato secondo le regole definite nella Decisione 3.1.

Il primo tentativo non contiene feedback precedente.

```text
PR
 │
 ▼
Generation Agent
 │
 ▼
Candidate Requirement v1
```

Il candidato non viene considerato definitivo fino al completamento dell'assessment.

---

## 8. Recupero della memoria dopo la generazione

Quando la memoria è attiva, il retrieval viene eseguito **dopo** che il Generation Agent ha prodotto un requisito candidato e **prima** dell'Assessment Agent.

Il flusso è:

```text
Pull Request
    │
    ▼
Generation Agent
    │
    ▼
Candidate Requirement
    │
    ▼
MCP search_requirements(...)
    │
    ▼
RequirementRetriever
    │
    ▼
Top-k requisiti affini
    │
    ▼
Assessment Agent
```

Questa sequenza è intenzionale.

Il compito del Generation Agent è ricostruire nel modo più fedele possibile il requisito espresso dalla Pull Request. Se i requisiti storici venissero forniti al Generator prima della generazione, il modello potrebbe essere influenzato dal contenuto della memoria e cercare di differenziare artificialmente il nuovo requisito oppure incorporare dettagli presenti nei requisiti precedenti ma non supportati dalla Pull Request corrente.

La memoria viene quindi utilizzata **per valutare il requisito ricostruito**, non per alterarne preventivamente il contenuto.

La presenza di un requisito storico equivalente non implica infatti che il candidato sia stato generato in modo errato. Un requisito può essere corretto rispetto alla Pull Request e risultare contemporaneamente `DUPLICATE`, `OVERLAPS`, `REFINES`, `SUPERSEDES` o `CONFLICTS` rispetto alla memoria.

Esiste inoltre una motivazione tecnica. Prima della generazione la query disponibile sarebbe costituita da `title` e `body` della Pull Request, che possono includere testo discorsivo, motivazioni, dettagli implementativi, descrizioni di bug e altre informazioni non direttamente confrontabili con i requisiti persistiti. Dopo la generazione, invece, il candidato è già espresso come requisito funzionale e si trova quindi nello stesso spazio concettuale dei requisiti presenti in memoria.

Il confronto:

```text
Candidate Requirement
        ↕
Historical Requirement
```

è pertanto più diretto del confronto:

```text
PR title + body
        ↕
Historical Requirement
```

Il retrieval viene eseguito dal workflow in modo deterministico, invece di lasciare all'LLM la decisione se consultare o meno la memoria. Questo garantisce che:

- ogni candidato venga valutato nelle stesse condizioni;
- il numero di chiamate alla memoria sia controllabile;
- il comportamento sia più riproducibile;
- sia possibile eseguire il workflow con memoria attiva o disattivata in modo controllato.

Il retrieval viene ripetuto dopo ogni nuova generazione, perché una revisione del requisito può modificare anche i requisiti semanticamente più affini.


## 9. Valutazione del requisito candidato

L'Assessment Agent riceve:

- titolo e body della Pull Request;
- requisito candidato corrente;
- criteri di assessment;
- requisiti storici recuperati, se la memoria è attiva.

La decisione non viene basata esclusivamente su un singolo punteggio aggregato.

Alcuni criteri costituiscono **condizioni necessarie** per l'accettazione.

In particolare, un requisito non può essere `ACCEPT` se:

- contiene affermazioni non supportate dall'evidenza;
- non è fedele al comportamento ricostruibile dalla Pull Request;
- non rappresenta un requisito funzionale nello scope stabilito;
- presenta problemi tali da impedirne un utilizzo affidabile come requisito validato.

Criteri quali chiarezza, atomicità e verificabilità possono contribuire alla valutazione, ma non compensano una violazione di grounding o fidelity.

La logica viene quindi progettata secondo il principio:

```text
buona forma
    ≠
requisito necessariamente valido
```

---

## 10. Decisioni dell'Assessment Agent

### 10.1 `ACCEPT`

`ACCEPT` indica che il requisito candidato soddisfa i criteri necessari per essere considerato valido nella configurazione corrente.

Il requisito può quindi uscire dal loop di revisione e passare alla fase di persistenza.

---

### 10.2 `REVISE`

`REVISE` indica che il requisito non è ancora accettabile, ma i problemi rilevati possono essere corretti utilizzando l'evidenza già disponibile.

Esempi:

- informazioni non supportate che possono essere rimosse;
- formulazione ambigua;
- requisito non sufficientemente atomico;
- livello di astrazione non corretto;
- comportamento espresso in modo incompleto ma correggibile.

In questo caso viene prodotto feedback strutturato e il controllo ritorna al Generation Agent, se il limite di tentativi non è stato raggiunto.

---

### 10.3 `REJECT`

`REJECT` rappresenta una condizione terminale.

Viene utilizzato quando un'ulteriore riscrittura non è considerata utile o appropriata.

Ad esempio, durante l'assessment può emergere che l'evidenza disponibile non consente realmente di formulare un requisito funzionale senza introdurre assunzioni arbitrarie.

In questo caso la pipeline termina senza una nuova generazione e senza persistenza.

`REJECT` viene mantenuto distinto da `NOT_EXTRACTABLE`:

- `REJECT` riguarda un candidato prodotto e non riparabile;
- `NOT_EXTRACTABLE` constata che dalla Pull Request non si ricava alcun requisito.

### 10.4 `CONFIRM_NOT_EXTRACTABLE`

La Decisione 3.1 (§11.10) prevede che il Generation Agent possa constatare di non
essere in grado di ricostruire un requisito senza inventarlo. La constatazione non chiude
però da sola l'elaborazione: verrebbe a mancare qualsiasi controllo sull'auto-esclusione,
e il generatore potrebbe usarla come scorciatoia davanti ai casi difficili.

La rinuncia viene quindi sottoposta al Requirement Assessment Agent, che dispone di una
quarta decisione:

```text
Generation Agent
   │
   ├── requisito candidato ──→ Assessment ──→ ACCEPT / REVISE / REJECT
   │
   └── rinuncia motivata ────→ Assessment ──→ CONFIRM_NOT_EXTRACTABLE
                                            └ REVISE (dissenso motivato)
```

Con `CONFIRM_NOT_EXTRACTABLE` il valutatore concorda e lo stato finale diventa
`NOT_EXTRACTABLE`. Con `REVISE` dissente, indicando quale comportamento ritiene
identificabile e in quale parte dell'evidenza: il controllo torna al generatore, che
dispone così di un'informazione che nel normale ciclo di revisione non riceverebbe mai,
perché il feedback presuppone un candidato da correggere.

La rinuncia non attraversa il recupero dalla memoria, che presuppone un candidato da
confrontare. Quando il valutatore è disattivato non esiste chi possa verificarla e
l'elaborazione si chiude come `NOT_EXTRACTABLE`.

> **Nota sull'evoluzione del §6.** La verifica preliminare di estraibilità è stata
> implementata come controllo deterministico e non semantico: scarta soltanto le Pull
> Request prive di testo sufficiente. Il giudizio sul fatto che un comportamento sia
> identificabile si è quindi spostato all'interno del ciclo, dove viene formulato dal
> generatore e verificato dal valutatore. `NOT_EXTRACTABLE` non è più perciò un esito
> deciso esclusivamente prima della generazione.

---

## 11. Feedback strutturato

Il feedback dell'Assessment Agent deve essere strutturato e direttamente utilizzabile dal Generation Agent.

Non viene utilizzato un semplice commento libero come unico meccanismo di revisione.

Un output concettuale può essere:

```json
{
  "decision": "REVISE",
  "unsupported_claims": [
    "The notification is sent by email"
  ],
  "missing_information": [],
  "issues": [
    "The requirement introduces a delivery channel not supported by the PR."
  ],
  "revision_instructions": [
    "Remove the unsupported reference to email.",
    "Preserve only the notification behavior supported by the PR."
  ]
}
```

Il Generation Agent riceve al tentativo successivo:

```text
evidenza originale della PR
+
requisito precedente
+
feedback strutturato
```

Non è necessario passare all'agente l'intera conversazione o l'intero storico testuale delle iterazioni precedenti.

Questa scelta limita la propagazione di informazioni non necessarie e rende il comportamento del loop più controllabile.

---

## 12. Numero massimo di tentativi

Il loop non può proseguire indefinitamente.

Per la prima configurazione viene adottato:

```text
max_generation_attempts = 3
```

Il valore rappresenta il numero massimo complessivo di generazioni:

```text
Tentativo 1
    ↓
Assessment
    ↓
REVISE

Tentativo 2
    ↓
Assessment
    ↓
REVISE

Tentativo 3
    ↓
Assessment
```

Tre tentativi consentono una generazione iniziale e fino a due revisioni successive.

La scelta permette di introdurre un vero ciclo di miglioramento mantenendo controllati:

- costo delle chiamate LLM;
- latenza;
- rischio di loop improduttivi;
- complessità dell'esperimento.

Il valore viene mantenuto configurabile e potrà essere verificato nella fase sperimentale.

---

## 13. Superamento del limite di tentativi

Se l'Assessment Agent restituisce nuovamente `REVISE` dopo l'ultimo tentativo disponibile, il requisito non viene accettato automaticamente.

Lo stato finale diventa:

```text
FAILED_VALIDATION
```

Il significato è:

> la Pull Request era stata considerata estraibile, ma il loop Generator–Assessment non è riuscito a produrre un requisito accettabile entro il numero massimo di tentativi consentito.

Il flusso termina:

```text
ultimo tentativo
      │
      ▼
Assessment
      │
      ▼
REVISE
      │
      ▼
max attempts reached
      │
      ▼
FAILED_VALIDATION
      │
      ▼
END
```

Nessun requisito viene inserito nella memoria persistente.

---

## 14. Nessuna accettazione automatica del "miglior candidato"

Durante il loop può essere utile conservare i diversi candidati e i relativi risultati di assessment per analisi sperimentali.

Tuttavia, il requisito con il punteggio migliore tra quelli prodotti non viene automaticamente promosso a requisito valido.

In particolare:

```text
best candidate
    ≠
accepted requirement
```

Un candidato può risultare migliore degli altri e continuare a violare un criterio necessario, ad esempio introducendo informazioni non supportate.

I candidati intermedi possono quindi essere conservati nel log dell'esecuzione, ma soltanto un requisito con decisione esplicita `ACCEPT` può essere persistito nella memoria definitiva.

---

## 15. Qualità del requisito e relazione con la memoria

La valutazione della qualità e la relazione con i requisiti storici vengono mantenute come due dimensioni concettualmente distinte.

### Decisione sul candidato

```text
ACCEPT
REVISE
REJECT
```

### Relazione con la memoria

```text
NEW
DUPLICATE
OVERLAPS
REFINES
SUPERSEDES
CONFLICTS
```

Un requisito può quindi essere, ad esempio:

```text
decision: ACCEPT
relation: NEW
```

oppure:

```text
decision: ACCEPT
relation: OVERLAPS
```

La presenza di una relazione storica non determina automaticamente l'esito del candidato.

La policy finale relativa a casi quali `DUPLICATE` o `CONFLICTS` viene consolidata nel comportamento dell'Assessment Agent e nella fase sperimentale.

---

## 16. Routing centralizzato

Le decisioni di transizione tra i nodi non vengono distribuite negli agenti.

Il routing viene mantenuto in un componente dedicato.

Concettualmente:

```text
route_after_extractability(state)

route_after_assessment(state)

route_after_revision_limit(state)
```

Questo approccio evita che ogni nodo implementi autonomamente parte della macchina a stati e rende più semplice:

- comprendere il workflow;
- testare le condizioni;
- modificare le policy;
- verificare che non esistano transizioni non previste.

---

## 17. Persistenza dopo `ACCEPT`

La scrittura nella memoria permanente avviene al di fuori della responsabilità degli agenti.

Il flusso è:

```text
Assessment Agent
       │
       ▼
     ACCEPT
       │
       ▼
     Router
       │
       ▼
   Controller
       │
       │ MCP
       ▼
store_accepted_requirement
       │
       ▼
Memoria persistente
```

Il Generation Agent e l'Assessment Agent non scrivono direttamente nel database.

Questa policy garantisce che:

- `REVISE` non contamini la memoria;
- `REJECT` non contamini la memoria;
- `FAILED_VALIDATION` non contamini la memoria;
- soltanto requisiti esplicitamente validati entrino nel contesto storico delle elaborazioni successive.

---

## 18. Stato finale della pipeline

Ogni elaborazione deve terminare con uno stato finale esplicito.

La prima tassonomia prevede:

```text
ACCEPTED
NOT_EXTRACTABLE
REJECTED
FAILED_VALIDATION
```

### `ACCEPTED`

È stato prodotto un requisito valido e il requisito può essere persistito.

### `NOT_EXTRACTABLE`

Dalla Pull Request non si ricava alcun requisito funzionale nello scope stabilito. L'esito può derivare dal controllo preliminare, quando il testo disponibile è insufficiente, oppure dal ciclo, quando il generatore constata di non poter ricostruire un requisito e il valutatore conferma con `CONFIRM_NOT_EXTRACTABLE` (§10.4).

### `REJECTED`

Durante il processo è emersa una condizione terminale che rende inutile un'altra revisione.

### `FAILED_VALIDATION`

La PR era stata considerata estraibile, ma il sistema non è riuscito a produrre un candidato accettabile entro il limite di tentativi.

Questa distinzione è utile sia per il comportamento del sistema sia per la successiva analisi sperimentale.

---

## 19. Tracciamento delle iterazioni

Per ogni esecuzione viene conservato uno storico delle iterazioni.

Ad esempio:

```text
iteration_history
│
├── attempt 1
│   ├── candidate
│   └── assessment
│
├── attempt 2
│   ├── candidate
│   └── assessment
│
└── attempt 3
    ├── candidate
    └── assessment
```

Lo storico serve a:

- analizzare l'effetto del feedback;
- misurare il numero medio di revisioni;
- individuare errori ricorrenti;
- confrontare configurazioni diverse;
- ricostruire il comportamento della pipeline.

Questo storico appartiene ai risultati e ai log dell'esecuzione e non alla memoria persistente dei requisiti validati.

---

## 20. Configurabilità

I principali parametri dell'architettura vengono mantenuti esterni alla logica dei nodi e configurabili.

Ad esempio:

```text
assessment_enabled
memory_enabled
max_generation_attempts
generator_model
assessment_model
```

Questa scelta consente di eseguire il workflow in configurazioni diverse senza modificare il codice.

In particolare permette di:

- sviluppare e testare la pipeline in modo incrementale, mentre i componenti vengono realizzati progressivamente e la memoria persistente non è ancora disponibile;
- eseguire in modo controllato le prove progressive descritte nella Decisione 3.7 (solo Generation, Generation + Assessment, workflow completo);
- isolare il comportamento di un singolo componente durante il debug.

La configurazione di riferimento per la valutazione finale resta il workflow completo, come stabilito nella Decisione 3.7.

---

## 21. Testabilità

L'architettura viene progettata in modo che ogni livello possa essere testato separatamente.

Devono poter essere verificati almeno:

- routing dopo la verifica di estraibilità;
- routing `ACCEPT / REVISE / REJECT`;
- conteggio dei tentativi;
- terminazione con `FAILED_VALIDATION`;
- propagazione corretta del feedback;
- aggiornamento dello stato;
- chiamata al retrieval a ogni iterazione;
- assenza di persistenza per gli stati non accettati;
- persistenza esclusivamente dopo `ACCEPT`;
- elaborazione di tutte le PR presenti nel file di input;
- passaggio alla PR successiva soltanto dopo lo stato finale della PR corrente;
- rispetto dell'ordine temporale configurato quando la memoria storica è attiva.

La logica di routing deve poter essere testata senza necessariamente invocare un LLM reale.

---

## 22. Punti da consolidare

Restano da consolidare durante implementazione e sperimentazione:

- schema definitivo dell'output strutturato dell'Assessment Agent;
- criteri esatti che determinano `REVISE` rispetto a `REJECT`;
- criteri necessari per `ACCEPT`;
- policy finale per le relazioni `DUPLICATE`, `OVERLAPS`, `REFINES`, `SUPERSEDES` e `CONFLICTS`;
- eventuale impiego di punteggi numerici come informazioni diagnostiche, senza sostituire gli hard gate;
- conferma empirica del valore iniziale `max_generation_attempts = 3`;
- formato definitivo di `iteration_history`;
- gestione di errori tecnici temporanei delle chiamate LLM, che devono essere distinti dai tentativi di revisione semantica.

---

## 23. Decisione riassuntiva

Per la prima implementazione viene adottata la seguente architettura:

```text
Framework:
    LangGraph

Agenti LLM:
    Requirement Generation Agent
    Requirement Assessment Agent

Orchestrazione:
    Pipeline Runner per l'iterazione sulle PR
    LangGraph come macchina a stati controllata per la singola PR

Unità di esecuzione LangGraph:
    una Pull Request alla volta

Ordine del batch:
    cronologico quando è disponibile un timestamp affidabile
    e la memoria storica è attiva

Routing:
    centralizzato

Verifica preliminare:
    EXTRACTABLE / NOT_EXTRACTABLE

Loop:
    Generation
        ↓
    Memory Retrieval
        ↓
    Assessment
        ↓
    ACCEPT / REVISE / REJECT

Tentativi massimi:
    3 generazioni complessive
    valore configurabile

Feedback:
    strutturato

Dopo REVISE:
    feedback → nuova generazione

Dopo REJECT:
    terminazione

Dopo limite raggiunto:
    FAILED_VALIDATION

Persistenza:
    soltanto dopo ACCEPT

Accesso alla memoria:
    lettura tramite MCP durante assessment
    scrittura tramite controller dopo ACCEPT

Candidati intermedi:
    conservati nei log
    non persistiti nella memoria definitiva
```

La soluzione mantiene separate generazione, valutazione, routing, retrieval e persistenza, limita esplicitamente il ciclo di revisione e garantisce che soltanto requisiti effettivamente validati possano diventare parte della memoria storica del sistema.

Il `Pipeline Runner` completa questa separazione distinguendo l'orchestrazione **tra più Pull Request** dall'orchestrazione **interna alla singola Pull Request**: il Runner gestisce il ciclo esterno sul file di input, mentre LangGraph continua a gestire il workflow e gli eventuali retry della PR corrente.

---

## 24. Riferimenti interni

- Decisione 3.1 — Standard di qualità e forma dei requisiti.
- Decisione 3.3 — Memoria persistente dei requisiti.
- Decisione 3.4 — Interfaccia MCP per l'accesso alla memoria persistente.
