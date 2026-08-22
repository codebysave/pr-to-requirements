# Decisione 3.3 — Memoria persistente dei requisiti

**Fase:** 3 — Design del sistema  
**Stato:** Proposta da validare  
**Autori:** Andrea, Marco  
**Data:** Agosto 2026

---

## 1. Contesto

PR4Requirements deve mantenere una **memoria persistente dei requisiti funzionali validati**.

La memoria non ha soltanto una funzione di archiviazione: i requisiti già accettati devono poter essere recuperati e confrontati con un nuovo requisito candidato, così da supportare controlli di similarità e di coerenza storica.

La presente decisione riguarda esclusivamente:

- il backend utilizzato per la persistenza dei requisiti;
- la struttura minima dei dati memorizzati;
- le modalità di interrogazione del database;
- il supporto al retrieval semantico dei requisiti affini;
- la rappresentazione delle relazioni tra requisiti;
- il modo in cui il database viene esposto al resto del sistema tramite un livello di accesso controllato.

---

## 2. Requisiti della memoria persistente

La soluzione scelta deve consentire di:

- conservare in modo persistente i requisiti funzionali validati;
- assegnare a ogni requisito un identificatore univoco;
- mantenere le informazioni necessarie alla tracciabilità verso la Pull Request di origine;
- recuperare requisiti tramite identificatore e metadati;
- applicare filtri, ad esempio per repository o intervallo temporale;
- supportare il recupero dei requisiti semanticamente affini a un nuovo requisito candidato;
- rappresentare eventuali relazioni tra requisiti;
- garantire aggiornamenti consistenti tramite operazioni transazionali;
- consentire la creazione di copie o snapshot della memoria per gli esperimenti;
- mantenere un livello di complessità proporzionato alla scala iniziale del progetto.

Un requisito ulteriore è la **consistenza temporale**: quando il sistema deve ricostruire la memoria disponibile a un determinato istante, il retrieval deve poter essere limitato ai requisiti precedenti a quel momento.

---

## 3. Soluzioni considerate

| Soluzione | Vantaggi | Limiti |
|---|---|---|
| **File JSON / JSONL** | Molto semplice da creare e ispezionare; nessuna infrastruttura aggiuntiva | Query, aggiornamenti, vincoli e relazioni devono essere gestiti nel codice applicativo; meno adatto come memoria operativa strutturata |
| **SQLite** | Database relazionale locale in un singolo file; query SQL, vincoli, indici, transazioni e tabelle collegate; nessun server dedicato | La ricerca semantica vettoriale non è fornita nativamente nella configurazione standard e deve essere gestita dal livello di retrieval |
| **Vector database dedicato** | Ricerca vettoriale e indicizzazione semantica native | Introduce un componente infrastrutturale aggiuntivo che non è necessario nella prima scala sperimentale del progetto |
| **PostgreSQL + pgvector** | Persistenza relazionale robusta e supporto alla ricerca vettoriale; adatto a volumi e accessi concorrenti più elevati | Richiede un servizio database dedicato e una configurazione operativa più articolata rispetto alle esigenze iniziali del progetto |

---

## 4. Decisione

Per la prima implementazione di PR4Requirements viene adottato **SQLite** come backend della memoria persistente dei requisiti.

La scelta è motivata dal fatto che SQLite offre le funzionalità necessarie per una memoria strutturata senza introdurre un servizio database separato. In particolare consente di utilizzare:

- schema relazionale;
- chiavi primarie e vincoli;
- query e filtri SQL;
- indici sui metadati più utilizzati;
- transazioni per aggiornamenti consistenti;
- tabelle separate per rappresentare relazioni tra requisiti;
- un singolo file facilmente copiabile, inizializzabile e archiviabile per una specifica esecuzione sperimentale.

Rispetto a un file JSON, SQLite permette quindi di separare più chiaramente la logica di persistenza dalla logica applicativa e riduce la necessità di implementare manualmente operazioni di ricerca, aggiornamento e consistenza dei dati.

Un database vettoriale dedicato o PostgreSQL con `pgvector` restano alternative tecnicamente valide, ma nella prima fase introdurrebbero una complessità infrastrutturale non necessaria per il volume di requisiti previsto. La loro adozione potrà essere rivalutata qualora il numero di requisiti o i requisiti prestazionali rendano insufficiente la soluzione iniziale.

---

## 5. Politica di persistenza

La memoria persistente contiene **soltanto requisiti che hanno superato il processo di valutazione con esito `ACCEPT`**.

I requisiti ancora in fase di generazione o revisione non vengono inseriti nella memoria definitiva. Analogamente, un requisito con esito `REJECT` non viene persistito.

```text
Requisito candidato
        │
        ▼
Assessment
   │      │      │
ACCEPT  REVISE  REJECT
   │      │      │
   ▼      └──► nuova generazione
Persist           
```

Questa scelta evita che requisiti non validati vengano successivamente recuperati come conoscenza storica e influenzino altre valutazioni.

La scrittura nel database avviene quindi dopo l'accettazione, attraverso il componente di controllo della pipeline.

---

## 6. Schema logico del database

La prima versione della memoria prevede almeno due entità logiche:

1. `requirements`, contenente i requisiti funzionali validati;
2. `requirement_relations`, contenente le eventuali relazioni tra requisiti.

### 6.1 Tabella `requirements`

| Campo | Descrizione |
|---|---|
| `id` | Identificatore univoco interno del requisito. |
| `statement` | Testo finale del requisito funzionale validato. |
| `source_repository` | Repository associato alla Pull Request di origine. |
| `source_pr_number` | Numero o identificatore della Pull Request di origine. |
| `source_pr_timestamp` | Riferimento temporale utilizzabile per ordinamento e retrieval storico. |
| `evidence` | Evidenza testuale associata al requisito, se prevista dal formato finale. |
| `created_at` | Data e ora di inserimento del requisito nella memoria. |
| `embedding` | Rappresentazione vettoriale del requisito, se viene deciso di persisterla. |
| `embedding_model` | Modello e/o versione utilizzati per produrre l'embedding. |

Non è necessario memorizzare nella tabella principale stati come `candidate` o `rejected`, perché il database rappresenta la **memoria dei requisiti già validati**.

L'eventuale storico completo delle revisioni del candidato appartiene al tracciamento dell'esecuzione e non alla memoria persistente utilizzata per il retrieval.

### 6.2 Tabella `requirement_relations`

Le relazioni tra requisiti vengono rappresentate separatamente per evitare di inserire strutture complesse nella riga del requisito.

| Campo | Descrizione |
|---|---|
| `source_requirement_id` | Primo requisito coinvolto nella relazione. |
| `target_requirement_id` | Secondo requisito coinvolto nella relazione. |
| `relation_type` | Tipo di relazione individuata. |
| `score` | Eventuale punteggio di similarità o confidenza associato. |
| `created_at` | Data di registrazione della relazione. |

Le categorie considerate comprendono, in via preliminare:

```text
DUPLICATE
OVERLAPS
REFINES
SUPERSEDES
CONFLICTS
```

La tassonomia definitiva verrà consolidata durante la fase sperimentale.

---

## 7. Interrogazione del database

SQLite viene utilizzato per le operazioni strutturate sulla memoria.

Le interrogazioni principali comprendono:

- recupero di un requisito tramite `id`;
- recupero dei requisiti appartenenti a uno specifico repository;
- selezione dei requisiti precedenti a un determinato istante;
- recupero delle relazioni associate a un requisito;
- inserimento di un nuovo requisito validato;
- inserimento o aggiornamento delle relazioni tra requisiti.

A livello concettuale, l'accesso può essere espresso tramite operazioni come:

```text
save_accepted(requirement)
get_by_id(requirement_id)
list_requirements(repository_id, before_timestamp)
get_relations(requirement_id)
save_relation(relation)
```

Queste operazioni vengono incapsulate in un componente dedicato, evitando che gli agenti o il resto della pipeline eseguano direttamente query SQL.

---

## 8. Retrieval dei requisiti semanticamente affini

Il retrieval semantico viene mantenuto **separato dalle normali query SQL**.

SQLite può filtrare i requisiti eleggibili, ma una query testuale o un confronto lessicale non è sufficiente per stabilire che due requisiti esprimano lo stesso comportamento con formulazioni differenti.

Per questo ogni requisito può essere associato a un **embedding**, cioè una rappresentazione vettoriale del suo significato.

Il flusso previsto è:

```text
Requisito candidato
        │
        ▼
Generazione embedding
        │
        ▼
Filtri SQL sui requisiti eleggibili
        │
        ▼
Recupero degli embedding
        │
        ▼
Calcolo della similarità
        │
        ▼
Ranking
        │
        ▼
Top-k requisiti più affini
```

Nella prima scala sperimentale non è necessario introdurre un indice vettoriale dedicato. Gli embedding dei requisiti eleggibili possono essere recuperati da SQLite e confrontati nel livello applicativo, ad esempio tramite **similarità del coseno**.

La separazione adottata è quindi:

```text
SQLite
    → persistenza, metadati, filtri, relazioni

Retrieval semantico
    → embedding, similarità, ranking, top-k
```

Il modello di embedding, il valore di `top_k` e le eventuali soglie di similarità rimangono parametri configurabili e da calibrare sperimentalmente.

---

## 9. Astrazione della persistenza

L'accesso a SQLite viene incapsulato dietro un componente `RequirementRepository`.

Il resto del sistema non dipende quindi direttamente dal database concreto.

```text
PR4Requirements
       │
       ▼
RequirementRepository
       │
       ▼
     SQLite
```

Il repository è responsabile delle operazioni di lettura e scrittura strutturate, mentre la ricerca semantica viene affidata a un componente separato, `RequirementRetriever`.

```text
RequirementRetriever
       │
       ├──► RequirementRepository
       │
       ├──► modello di embedding
       │
       └──► similarità + ranking
```

Questa separazione consente di sostituire in futuro SQLite o la strategia di retrieval senza modificare la logica degli agenti.

---

## 10. Accesso tramite MCP

MCP non rappresenta il database e non implementa direttamente la persistenza.

Il suo ruolo è fornire un'interfaccia standardizzata attraverso la quale i componenti agentici possono interrogare la memoria.

```text
Agente / Controller
        │
        │ MCP
        ▼
    MCP Server
        │
        ▼
RequirementRepository / RequirementRetriever
        │
        ▼
      SQLite
```

Il server MCP può esporre operazioni quali:

```text
search_requirements(...)
get_requirement(...)
find_candidate_relations(...)
```

L'Assessment Agent può utilizzare queste operazioni in lettura per ottenere requisiti storici rilevanti.

Le operazioni che producono modifiche permanenti alla memoria vengono invece eseguite dal controller della pipeline soltanto dopo l'esito `ACCEPT`.

Questa separazione impedisce a un requisito ancora in revisione di modificare direttamente la memoria persistente e mantiene l'accesso al database controllato.

---

## 11. Riproducibilità e gestione della memoria

L'utilizzo di SQLite consente di trattare la memoria come un singolo artefatto persistente.

Per gli esperimenti è quindi possibile:

- inizializzare una memoria vuota;
- creare snapshot della memoria a uno specifico punto dell'esecuzione;
- duplicare il file per confrontare configurazioni differenti;
- conservare una copia del database associata a una determinata esecuzione;
- ricostruire una memoria rispettando l'ordine temporale dei requisiti.

Il file SQLite non deve necessariamente essere mantenuto sotto versionamento Git: può essere archiviato come artefatto dell'esperimento insieme alla configurazione che lo ha prodotto.

---

## 12. Limiti della scelta

SQLite è adatto alla scala iniziale del progetto, ma presenta alcuni limiti da tenere presenti.

In particolare:

- non offre nativamente, nella configurazione standard, un motore di retrieval vettoriale completo;
- non è pensato per scenari con numerosi writer concorrenti;
- il confronto esaustivo degli embedding diventa meno conveniente con collezioni molto grandi.

Questi limiti non risultano critici per la prima implementazione, in cui la memoria viene aggiornata da un singolo flusso controllato e il numero di requisiti consente un retrieval semantico gestito nel livello applicativo.

Se tali condizioni dovessero cambiare, l'astrazione `RequirementRepository` e la separazione del `RequirementRetriever` permettono di introdurre un backend differente senza riprogettare l'intera pipeline.

---

## 13. Parametri e dettagli della memoria da consolidare

La scelta di SQLite come backend persistente e la separazione tra `RequirementRepository` e `RequirementRetriever` definiscono l'architettura di base della memoria. Restano tuttavia alcuni aspetti che devono essere consolidati durante l'implementazione e la fase sperimentale.

### 13.1 Decisioni progettuali ancora da consolidare

Le seguenti scelte riguardano direttamente il funzionamento della memoria e, una volta definite, devono essere riportate in questa decisione di design:

- il modello di embedding utilizzato per rappresentare semanticamente i requisiti;
- se gli embedding debbano essere persistiti nel database oppure ricalcolati quando necessario;
- il formato con cui gli embedding vengono memorizzati in SQLite;
- i filtri applicati prima del confronto semantico, ad esempio repository e vincoli temporali;
- il riferimento temporale utilizzato per limitare il retrieval ai requisiti storicamente disponibili;
- la tassonomia definitiva delle relazioni tra requisiti;
- l'eventuale introduzione futura di un indice vettoriale dedicato;
- le politiche di inizializzazione, reset, backup e snapshot della memoria.

Questi aspetti fanno parte del design della memoria persistente perché determinano come i requisiti vengono rappresentati, conservati, filtrati e recuperati.

### 13.2 Parametri da calibrare sperimentalmente

Alcuni valori non devono essere fissati arbitrariamente in fase di design, ma possono essere determinati attraverso test e calibrazione sperimentale.

In particolare:

- il valore di `top_k`, cioè il numero di requisiti semanticamente affini restituiti dal retrieval;
- l'eventuale soglia minima di similarità;
- eventuali criteri aggiuntivi di ranking o selezione dei candidati.

Questi parametri restano configurabili. Una volta individuati i valori adottati per gli esperimenti, essi vengono riportati anche in questa decisione come configurazione della memoria, mentre la metodologia utilizzata per la calibrazione viene documentata nella parte sperimentale del progetto.

---

## 14. Decisione riassuntiva

Per la prima implementazione viene adottata la seguente soluzione:

```text
Backend persistente: SQLite
Persistenza: solo requisiti validati con esito ACCEPT
Accesso ai dati: RequirementRepository
Retrieval semantico: RequirementRetriever + embedding
Similarità: calcolata nel livello applicativo
Relazioni: tabella dedicata
Accesso agentico alla memoria: MCP Server
```

La scelta mantiene contenuta la complessità infrastrutturale, fornisce una memoria strutturata e transazionale e consente di introdurre il retrieval semantico senza legare l'architettura a un database vettoriale specifico.
