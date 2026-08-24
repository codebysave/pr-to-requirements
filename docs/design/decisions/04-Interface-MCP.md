# Decisione 3.4 — Interfaccia MCP per l'accesso alla memoria persistente

**Fase:** 3 — Design del sistema  
**Stato:** Proposta da validare  
**Autori:** Andrea, Marco  
**Data:** Agosto 2026

---

## 1. Contesto

PR4Requirements utilizza una memoria persistente dei requisiti funzionali validati, progettata nella Decisione 3.3.

Gli agenti e gli altri componenti della pipeline non devono accedere direttamente al backend di persistenza né conoscere query SQL, struttura fisica del database o dettagli del retrieval semantico.

Per questo viene introdotto un **server MCP (Model Context Protocol)** che espone un insieme limitato di operazioni attraverso cui il sistema può consultare e aggiornare la memoria.

MCP viene quindi utilizzato come **livello standardizzato di accesso alla memoria**, non come database e non come implementazione del retrieval.

```text
Componenti di PR4Requirements
            │
            │ MCP
            ▼
        MCP Server
            │
            ├──► RequirementRepository
            │          │
            │          ▼
            │        SQLite
            │
            └──► RequirementRetriever
                       │
                       ├── embedding
                       ├── similarità
                       └── ranking
```

La presente decisione definisce:

- il ruolo del server MCP nel sistema;
- le operazioni esposte;
- la separazione tra operazioni di lettura e scrittura;
- i contratti di input e output dei tool;
- le responsabilità del server rispetto a persistenza e retrieval;
- il trasporto iniziale utilizzato;
- i principali criteri di testabilità e gestione degli errori.

Il funzionamento completo del workflow tra Generator, Assessment Agent e controller viene invece definito nella Decisione 3.5.

---

## 2. Obiettivi dell'interfaccia MCP

L'interfaccia MCP deve garantire che:

- gli agenti non eseguano direttamente query SQL;
- il backend di persistenza rimanga nascosto ai componenti agentici;
- le operazioni disponibili siano poche, esplicite e coerenti con il dominio dei requisiti;
- le operazioni di lettura siano separate da quelle che modificano la memoria;
- i tool abbiano input e output strutturati;
- gli errori siano distinguibili da risultati validi ma vuoti;
- il server possa essere testato indipendentemente dagli agenti;
- un eventuale cambio futuro del backend non richieda di modificare il contratto MCP.

---

## 3. Alternative considerate

Sono state considerate tre modalità principali per esporre ai componenti agentici le operazioni necessarie ad accedere alla memoria.

In nessuna delle alternative si assume che il modello LLM possa comunicare autonomamente con SQLite, API o altri strumenti esterni. L'accesso avviene sempre attraverso **funzioni, tool o componenti applicativi messi a disposizione dal runtime che ospita l'agente**. La differenza tra le alternative riguarda quindi il modo in cui tale interfaccia viene progettata e standardizzata.

| Soluzione | Descrizione | Vantaggi | Limiti |
|---|---|---|---|
| **Funzioni/tool applicativi custom** | Il framework agentico espone funzioni Python o tool definiti dall'applicazione; tali funzioni invocano `RequirementRepository` e, indirettamente, il database | Soluzione semplice e con pochi componenti intermedi | L'interfaccia tra agente e memoria è proprietaria e maggiormente legata all'implementazione applicativa |
| **API applicativa custom** | Un servizio applicativo espone operazioni sulla memoria tramite un'API definita dal progetto; l'agente vi accede attraverso un apposito tool o adapter | Separa il servizio di memoria dal resto dell'applicazione e permette esecuzioni su processi distinti | Richiede la progettazione e manutenzione di un protocollo/API specifico del progetto e del relativo adapter lato agente |
| **MCP Server** | Le capacità della memoria vengono esposte come tool MCP attraverso un server dedicato | Utilizza un protocollo standardizzato, mantiene separati agenti, retrieval e persistenza e rende esplicito il contratto dei tool | Introduce un componente aggiuntivo da implementare, configurare e testare |

### Decisione

PR4Requirements utilizza un **server MCP dedicato** come punto di accesso alla memoria persistente.

Il server non contiene direttamente la logica completa del sistema, ma delega le operazioni ai componenti responsabili:

- `RequirementRepository` per lettura e scrittura strutturata;
- `RequirementRetriever` per ricerca semantica, ranking e recupero dei requisiti affini.

---

## 4. Primitive MCP utilizzate

La prima implementazione utilizza principalmente **MCP Tools**.

Le operazioni necessarie a PR4Requirements sono infatti azioni parametrizzate, ad esempio:

- cercare requisiti semanticamente affini;
- recuperare un requisito;
- recuperare relazioni già registrate;
- persistire un requisito validato.

Le primitive MCP `Resources` e `Prompts` non sono necessarie per il caso d'uso iniziale e non vengono introdotte nella prima versione.

La loro eventuale adozione potrà essere valutata in seguito soltanto se emergerà un caso d'uso concreto.

---

## 5. Tool MCP principali

L'interfaccia iniziale viene mantenuta intenzionalmente ridotta.

### 5.1 `search_requirements`

**Scopo**

Recuperare dalla memoria i requisiti semanticamente più affini a un requisito candidato.

**Input concettuale**

```text
candidate_text
repository_id?
before_timestamp?
top_k?
```

- `candidate_text`: testo del requisito candidato;
- `repository_id`: eventuale filtro sul repository;
- `before_timestamp`: eventuale limite temporale per evitare di recuperare requisiti futuri rispetto al caso analizzato;
- `top_k`: numero massimo di risultati da restituire.

**Output concettuale**

Per ogni risultato vengono restituiti almeno:

```text
requirement_id
statement
source_repository
source_pr_number
similarity_score
```

I risultati sono ordinati per rilevanza semantica.

Il tool non decide se due requisiti siano `DUPLICATE`, `OVERLAPS`, `REFINES` o `CONFLICTS`: restituisce evidenza utile al componente incaricato della valutazione.

Con memoria vuota viene restituita una lista vuota.

---

### 5.2 `get_requirement`

**Scopo**

Recuperare un requisito già memorizzato tramite il suo identificatore.

**Input**

```text
requirement_id
```

**Output**

Il requisito completo, comprensivo dei metadati previsti dallo schema della memoria.

Se l'identificatore non esiste, il server deve restituire un risultato esplicito di tipo `not found` e non un requisito vuoto o inventato.

---

### 5.3 `get_requirement_relations`

**Scopo**

Recuperare le relazioni già registrate per un requisito validato.

**Input**

```text
requirement_id
```

**Output**

Una lista di relazioni associate al requisito, ad esempio:

```text
DUPLICATE
OVERLAPS
REFINES
SUPERSEDES
CONFLICTS
```

Il tool restituisce relazioni già presenti nella memoria e non esegue autonomamente una nuova classificazione semantica.

---

### 5.4 `store_accepted_requirement`

**Scopo**

Persistire nella memoria un requisito che ha già concluso il processo di valutazione con esito `ACCEPT`.

Il nome del tool rende esplicita la politica definita nella Decisione 3.3: la memoria definitiva contiene soltanto requisiti validati.

**Input concettuale**

```text
statement
source_repository
source_pr_number
source_pr_timestamp?
evidence?
relations?
```

L'identificatore interno, la data di inserimento e gli eventuali dati derivati necessari alla memoria vengono gestiti dal livello applicativo.

**Output**

```text
requirement_id
created_at
```

eventualmente accompagnati dal record finale persistito.

Il tool non decide se il requisito debba essere accettato: riceve esclusivamente requisiti per i quali tale decisione è già stata presa dal workflow.

---

## 6. Tool non incluso nella prima interfaccia: `check_consistency`

Nella bozza iniziale era previsto un tool `check_consistency` incaricato di classificare direttamente un requisito come:

```text
NEW
DUPLICATE
OVERLAPS
REFINES
SUPERSEDES
CONFLICTS
```

Questa operazione non viene inclusa come tool MCP autonomo nella prima versione.

La motivazione è che una classificazione di questo tipo non rappresenta una semplice operazione di accesso alla memoria: richiede una valutazione semantica che appartiene alla logica dell'Assessment Agent.

Il server MCP fornisce quindi al sistema i requisiti rilevanti attraverso `search_requirements`, mentre la classificazione della relazione viene effettuata dal componente responsabile dell'assessment.

Questa scelta evita di duplicare o nascondere parte della logica di valutazione all'interno del server MCP.

---

## 7. Separazione tra lettura e scrittura

L'accesso alla memoria segue una politica esplicita.

### Operazioni di lettura

```text
search_requirements
get_requirement
get_requirement_relations
```

Queste operazioni possono essere utilizzate dai componenti autorizzati a consultare la memoria.

Nella configurazione iniziale, l'Assessment Agent utilizza la memoria in sola lettura per ottenere il contesto storico necessario alla valutazione.

### Operazioni di scrittura

```text
store_accepted_requirement
```

La scrittura permanente non viene affidata direttamente all'Assessment Agent o al Generation Agent.

Il tool viene invocato dal **controller della pipeline** soltanto dopo che il requisito ha ricevuto esito `ACCEPT`.

```text
Assessment
    │
    ▼
  ACCEPT
    │
    ▼
Controller
    │
    │ MCP
    ▼
store_accepted_requirement
    │
    ▼
RequirementRepository
    │
    ▼
SQLite
```

Questa separazione impedisce a requisiti ancora in fase di generazione, revisione o rifiuto di modificare la memoria storica.

---

## 8. Contratti strutturati dei tool

Ogni tool deve utilizzare input e output strutturati e validabili.

Ad esempio, una richiesta di retrieval può essere rappresentata concettualmente come:

```json
{
  "candidate_text": "The system shall allow users to export reports.",
  "repository_id": "owner/repository",
  "top_k": 5
}
```

e la risposta:

```json
{
  "results": [
    {
      "requirement_id": "FR-0021",
      "statement": "The system shall ...",
      "similarity_score": 0.91
    }
  ]
}
```

Le firme definitive vengono consolidate durante l'implementazione, ma devono rispettare alcuni principi:

- nessun tool accetta query SQL arbitrarie;
- i parametri devono essere tipizzati;
- gli identificatori devono avere un formato coerente;
- i risultati devono essere machine-readable;
- i tool di retrieval devono restituire anche i punteggi necessari a interpretare il ranking;
- un errore non deve essere rappresentato come un risultato valido ma vuoto.

---

## 9. Gestione degli errori

Il server deve distinguere almeno i seguenti casi:

- memoria vuota;
- nessun requisito rilevante trovato;
- requisito richiesto inesistente;
- input non valido;
- errore durante il retrieval;
- errore nel calcolo dell'embedding;
- errore durante la persistenza;
- indisponibilità del backend.

In particolare:

> una lista vuota restituita correttamente da `search_requirements` non deve essere confusa con un fallimento del retrieval.

Gli errori devono essere propagati in forma strutturata e tracciabile, senza generare valori sostitutivi o risultati inventati.

---

## 10. Trasporto MCP

Per la prima implementazione locale viene adottato **stdio** come trasporto MCP.

Questa scelta mantiene semplice l'esecuzione del prototipo:

```text
PR4Requirements
      │
      │ stdio / MCP
      ▼
  MCP Server
      │
      ▼
Memoria persistente
```

Non è necessario esporre inizialmente il server sulla rete.

Qualora in futuro il server MCP debba essere eseguito come servizio remoto, potrà essere valutato un trasporto HTTP supportato dallo standard senza modificare la semantica dei tool definiti in questa decisione.

---

## 11. Implementazione e testabilità

Il server viene implementato in Python utilizzando l'SDK ufficiale MCP.

La logica dei tool deve rimanere sottile:

```text
Tool MCP
    │
    ├── validazione input
    ├── chiamata al componente applicativo
    ├── gestione errori
    └── serializzazione output
```

La persistenza e il retrieval restano responsabilità rispettivamente di `RequirementRepository` e `RequirementRetriever`.

Questo permette di testare separatamente:

1. la logica del repository;
2. la logica del retrieval;
3. il contratto dei tool MCP;
4. l'integrazione MCP → memoria;
5. l'utilizzo dei tool all'interno del workflow agentico.

Per i test del server può essere utilizzata una memoria temporanea o un database SQLite dedicato ai test, evitando dipendenze dallo stato reale della memoria sperimentale.

---

## 12. Confine tra MCP e logica agentica

Il server MCP non deve diventare un ulteriore agente nascosto.

Il suo compito è esporre in modo controllato le capacità della memoria.

```text
MCP
    → accesso standardizzato

RequirementRepository
    → persistenza e query strutturate

RequirementRetriever
    → retrieval semantico

Assessment Agent
    → interpretazione e valutazione delle relazioni

Controller
    → decisione di persistenza dopo ACCEPT
```

Il comportamento completo degli agenti, la sequenza delle invocazioni e il loop `ACCEPT / REVISE / REJECT` vengono documentati nella Decisione 3.5.

---

## 13. Punti da consolidare

Durante l'implementazione devono essere consolidati:

- gli schemi esatti di input e output dei tool;
- i nomi definitivi dei campi;
- il formato standard degli errori;
- timeout e politiche di retry;
- eventuale logging delle invocazioni MCP;
- la modalità con cui vengono persistite le relazioni individuate dall'Assessment Agent;
- l'eventuale necessità di un tool amministrativo `list_requirements`;
- l'eventuale introduzione futura di MCP Resources;
- l'eventuale passaggio da `stdio` a un trasporto remoto.

I parametri relativi al retrieval semantico, come modello di embedding, `top_k` e soglie di similarità, restano definiti e calibrati nell'ambito della Decisione 3.3 sulla memoria persistente.

---

## 14. Decisione riassuntiva

Per la prima implementazione viene adottata la seguente configurazione:

```text
Interfaccia memoria: MCP Server dedicato

Primitive MCP utilizzate:
    Tools

Tool principali:
    search_requirements
    get_requirement
    get_requirement_relations
    store_accepted_requirement

Accesso in lettura:
    Assessment Agent

Accesso in scrittura:
    Controller dopo ACCEPT

Persistenza:
    RequirementRepository → SQLite

Retrieval:
    RequirementRetriever → embedding + similarità + ranking

Trasporto iniziale:
    stdio
```

La scelta mantiene separati protocollo di accesso, persistenza, retrieval e logica agentica, evitando che gli agenti dipendano direttamente dal database e impedendo che requisiti non validati modifichino la memoria persistente.

---

## 15. Riferimenti interni

- Decisione 3.1 — Standard di qualità e forma dei requisiti.
- Decisione 3.3 — Memoria persistente dei requisiti.
- Decisione 3.5 — Architettura multi-agente e workflow.

## 16. Riferimenti tecnici

- Model Context Protocol — specifica ufficiale.
- MCP Python SDK — SDK ufficiale per client e server MCP.
