# Decisione 3.6 — Dataset di Pull Request e costruzione del campione sperimentale

**Fase:** 3 — Design del sistema  
**Stato:** Proposta da validare  
**Autori:** Andrea, Marco  
**Data:** Agosto 2026

---

## 1. Contesto

PR-to-Requirements deve essere valutato su Pull Request reali, sufficientemente rappresentative di attività di sviluppo software e accompagnate da una descrizione testuale utilizzabile per la ricostruzione dei requisiti funzionali.

Per il primo ciclo di sperimentazione abbiamo deciso di utilizzare come sorgente **PR4Code**, il dataset presentato da Donato, Mariani, Micucci e Riganelli in *PR4Code: A Pull Requests Dataset for AI Code Generation*.

PR4Code contiene **13.339 Pull Request reali provenienti da GitHub**, suddivise tra:

- 4.508 Pull Request di progetti Java;
- 8.831 Pull Request di progetti Python.

Il dataset è costruito a partire da 1.055 repository GitHub e conserva, per ogni Pull Request, sia informazioni testuali sia informazioni relative alla sua storia di sviluppo e alle modifiche al codice.

PR4Code viene utilizzato come **sorgente di casi reali per la sperimentazione**, ma PR-to-Requirements non viene progettato in modo dipendente da questo dataset.

---

## 2. Obiettivi della scelta

La strategia relativa ai dati deve consentire di:

- iniziare la sperimentazione su un numero limitato e controllabile di Pull Request;
- utilizzare casi provenienti da un dataset reale e documentato;
- mantenere la prima analisi sufficientemente omogenea;
- separare il formato originale del dataset dal formato consumato dal workflow;
- permettere in seguito l'utilizzo di dataset differenti;
- poter ampliare progressivamente il numero di repository e Pull Request;
- mantenere separati i dati di input dal gold standard costruito per la valutazione.

---

## 3. Dataset sorgente: PR4Code

PR4Code è stato progettato come dataset di Pull Request reali per lo studio di task di sviluppo software e AI-driven code generation.

La sua struttura è più ricca rispetto alle informazioni che PR-to-Requirements utilizza nella prima configurazione sperimentale.

Per ogni Pull Request, il dataset mette a disposizione informazioni che permettono di ricostruire diversi livelli del task di sviluppo, tra cui:

- identificativo e titolo della Pull Request;
- descrizione testuale della Pull Request (`body`);
- stato e informazioni sul branch;
- storia e sequenza dei commit associati;
- descrizioni o messaggi a livello di commit;
- numero di commit;
- file modificati;
- numero di linee aggiunte e rimosse;
- patch e diff delle modifiche;
- informazioni aggregate sulle modifiche;
- versioni dei file prima e dopo la Pull Request;
- altri metadati utili a ricostruire il contesto dello sviluppo.

Il dataset è organizzato gerarchicamente per repository e Pull Request, con file JSON contenenti i metadati e artefatti relativi alle modifiche apportate.

La disponibilità di queste informazioni rende PR4Code utile anche per esperimenti futuri nei quali il requisito possa essere ricostruito utilizzando evidenza aggiuntiva rispetto alla sola descrizione della Pull Request.

---

## 4. Sottoinsieme iniziale

Per il primo ciclo di sperimentazione non utilizzeremo direttamente tutte le 13.339 Pull Request.

La prima configurazione prevede di selezionare:

```text
un singolo repository GitHub
        │
        ▼
un insieme limitato di Pull Request
        │
        ▼
campione sperimentale iniziale
```

La quantità esatta di Pull Request non viene fissata in questa decisione e potrà essere stabilita in funzione del tempo disponibile e delle esigenze di annotazione.

La scelta di partire da un singolo progetto ha principalmente uno scopo operativo e sperimentale:

- riduce l'eterogeneità iniziale;
- permette di comprendere meglio il dominio del repository;
- rende più semplice ispezionare manualmente i casi;
- facilita la costruzione e revisione del gold standard;
- permette di verificare il comportamento della memoria su una sequenza di Pull Request appartenenti allo stesso progetto;
- consente di individuare problemi della pipeline prima di estendere l'esperimento.

Questa scelta non implica che il sistema sia destinato a funzionare su un solo repository.

---

## 5. Costruzione di un file JSON sperimentale

Le Pull Request selezionate dal repository vengono estratte dalla struttura originale di PR4Code e riaggregate in un **unico file JSON** utilizzato come input del primo ciclo sperimentale.

Il file contiene una collezione di record normalizzati, ad esempio:

```json
[
  {
    "id": "repo-pr-101",
    "repository": "owner/repository",
    "pr_number": 101,
    "title": "Add report export",
    "body": "Users can now export reports..."
  },
  {
    "id": "repo-pr-102",
    "repository": "owner/repository",
    "pr_number": 102,
    "title": "Fix report filtering",
    "body": "..."
  }
]
```

Il formato definitivo dei campi potrà essere esteso, ma il file deve mantenere almeno:

- un identificatore stabile;
- il repository di origine;
- il numero o identificativo della Pull Request;
- il titolo;
- il body.

Eventuali timestamp necessari per ordinamento cronologico, tracciabilità o retrieval storico possono essere conservati come metadati tecnici senza essere necessariamente forniti agli agenti come evidenza testuale.

Il file JSON rappresenta quindi un **dataset derivato per l'esperimento**, mentre il dataset PR4Code originale rimane invariato.

---

## 6. Evidenza utilizzata nella prima sperimentazione

Nella prima configurazione abbiamo deciso volontariamente di limitare l'evidenza fornita al sistema.

Il Generation Agent utilizza principalmente:

```text
PR title
+
PR body
```

Questa scelta permette di studiare in modo isolato una domanda precisa:

> fino a che punto è possibile ricostruire un requisito funzionale utilizzando la descrizione testuale della Pull Request?

Le altre informazioni disponibili in PR4Code non vengono considerate, nella prima configurazione, come documentazione utilizzabile dal Generator per costruire il requisito.

---

## 7. Informazioni volontariamente escluse nella prima fase

PR4Code permette di utilizzare una quantità di contesto molto più ampia rispetto a `title` e `body`.

Per la prima sperimentazione scegliamo tuttavia di **non fornire agli agenti**, come evidenza per la generazione del requisito:

- messaggi e descrizioni dei singoli commit;
- sequenza dei commit;
- commenti o informazioni testuali aggiuntive relative alla storia di sviluppo, quando disponibili;
- diff e patch del codice;
- cumulative diff della Pull Request;
- contenuto dei file modificati prima e dopo la modifica;
- lista dettagliata dei file modificati;
- numero di linee aggiunte, rimosse o modificate;
- URL e riferimenti ai file;
- informazioni sul branch;
- altri metadati tecnici non necessari alla configurazione iniziale.

Questa esclusione è **volontaria** e non deriva da un limite di PR4Code.

L'obiettivo è evitare, nel primo ciclo, di mescolare sorgenti di evidenza molto diverse e rendere più semplice interpretare i risultati.

In particolare, utilizzando inizialmente solo `title` e `body`, possiamo distinguere meglio:

- i casi in cui la descrizione della Pull Request è sufficiente;
- i casi in cui è troppo vaga o incompleta;
- le informazioni che il modello riesce effettivamente a ricostruire dal testo;
- gli eventuali casi in cui informazioni aggiuntive potrebbero essere necessarie.

---

## 8. Metadati tecnici ed evidenza per l'LLM

Viene mantenuta una distinzione tra:

```text
metadati necessari al workflow
              ≠
evidenza fornita all'LLM
```

Ad esempio, informazioni come:

```text
repository
pr_number
timestamp
```

possono essere conservate nel record normalizzato per:

- identificazione;
- tracciabilità;
- ordinamento;
- associazione con il gold standard;
- applicazione di filtri temporali nella memoria.

Questo non significa che tali informazioni debbano essere incluse nel prompt del Generation Agent.

La configurazione sperimentale stabilisce esplicitamente quali campi sono visibili agli agenti.

---

## 9. Formato di input atteso dal workflow

PR-to-Requirements non legge direttamente PR4Code o altri dataset nel loro formato originale.

Il workflow accetta invece un **unico formato di input normalizzato**, definito dal progetto. Per la prima sperimentazione questo formato è rappresentato da un file JSON contenente una collezione di Pull Request con i campi necessari all'esecuzione.

Un record può essere rappresentato, ad esempio, come:

```json
{
  "id": "repo-123",
  "repository": "owner/repository",
  "pr_number": 123,
  "timestamp": "2025-03-01T10:00:00Z",
  "title": "Add PDF export",
  "body": "Users can now export reports as PDF."
}
```

Dal punto di vista del workflow, **non è importante da dove provengano questi dati**.

La sorgente può essere PR4Code, un altro dataset, un'esportazione personalizzata o un file costruito manualmente. La condizione necessaria è che, prima dell'avvio del workflow, i dati siano stati portati nel formato JSON previsto da PR-to-Requirements.


Il file JSON normalizzato può contenere **una o più Pull Request**. Il `PullRequestLoader` legge e valida l'intera collezione e costruisce i relativi `PullRequestRecord`, ma non esegue direttamente il workflow. Come definito nella **Decisione 3.5**, l'elaborazione delle PR viene affidata a un **Pipeline Runner** deterministico, che prende una PR alla volta, avvia una nuova esecuzione LangGraph, attende che la PR corrente raggiunga uno stato finale e soltanto dopo passa alla successiva.

```text
sample.json
    │
    │ contiene 1..N Pull Request
    ▼
PullRequestLoader
    │
    ▼
[PullRequestRecord 1, ..., PullRequestRecord N]
    │
    ▼
Pipeline Runner
    │
    │ una PR alla volta
    ▼
LangGraph
```

In questo modo manteniamo separati il **caricamento e la validazione dell'input**, responsabilità del Loader, dall'**orchestrazione delle elaborazioni successive**, responsabilità del Runner.

Il confine architetturale è quindi il seguente:

```text
qualunque sorgente di Pull Request
            │
            ▼
preparazione / normalizzazione dei dati
            │
            ▼
      sample.json
            │
      ──────┼──────  inizio di PR-to-Requirements
            │
            ▼
  PullRequestLoader
            │
            ▼
      workflow
```

Tutto ciò che avviene prima della produzione del file JSON normalizzato è esterno al workflow agentico.

---

## 10. Ruolo del Loader

Una volta disponibile il file JSON normalizzato, PR-to-Requirements utilizza un **loader generico** per caricare le Pull Request.

Il loader non deve conoscere la struttura interna di PR4Code e non deve sapere quale dataset sia stato utilizzato in origine.

Il suo compito è più semplice:

```text
sample.json
    │
    ▼
PullRequestLoader
    │
    ├── legge il JSON
    ├── controlla che la struttura sia valida
    ├── verifica la presenza dei campi richiesti
    └── costruisce i record usati dal workflow
    │
    ▼
PullRequestRecord
```

Il loader può quindi controllare, ad esempio, che:

- il file sia un JSON valido;
- ogni Pull Request abbia un identificatore;
- `title` e `body` siano presenti nel formato atteso;
- `repository` e `pr_number` abbiano il tipo corretto;
- gli eventuali campi temporali siano rappresentati in modo coerente.

Se il file non rispetta lo schema previsto, il workflow non procede e viene restituito un errore di validazione.

Questa scelta rende esplicito il contratto di input del sistema:

> **PR-to-Requirements accetta Pull Request già normalizzate secondo uno schema noto e stabile.**

Di conseguenza, il workflow rimane indipendente dal dataset sorgente pur mantenendo un formato di ingresso controllato e facilmente validabile.

---

## 11. Preparazione del campione e possibile estensione futura

### 11.1 Preparazione del campione nella prima sperimentazione

Nel primo ciclo sperimentale utilizziamo PR4Code come sorgente.

PR4Code ha una struttura propria, più ricca del formato minimo richiesto dal workflow. Per questo viene utilizzato uno **script di preprocessing** che:

- legge la struttura originale di PR4Code;
- seleziona il repository scelto per l'esperimento;
- seleziona il numero di Pull Request desiderato;
- estrae i campi necessari, come identificatore, repository, numero della PR, titolo e body;
- ignora, nella configurazione iniziale, i metadati che non vogliamo fornire al workflow;
- produce il file `sample.json` nel formato richiesto da PR-to-Requirements.

Il flusso è quindi:

```text
PR4Code
   │
   ▼
script di preprocessing
   │
   ▼
sample.json
   │
   ▼
PullRequestLoader
   │
   ▼
PR-to-Requirements
```

Lo script di preprocessing può essere considerato un **adapter della sorgente**, ma non fa parte del workflow agentico.

Se in futuro venisse utilizzato un dataset con una struttura diversa, la logica di preprocessing dovrebbe essere adattata a quella specifica struttura, in modo da produrre comunque lo stesso `sample.json`.

Il workflow, invece, non cambierebbe.

### 11.2 Possibile estensione verso una normalizzazione automatica

La scelta attuale richiede quindi che la normalizzazione del dataset avvenga prima dell'esecuzione di PR-to-Requirements.

In futuro, se si volesse costruire un sistema capace di ricevere direttamente dataset di Pull Request organizzati in modi differenti e convertirli automaticamente nel formato atteso, sarebbe necessario introdurre una componente aggiuntiva dedicata alla **costruzione del dataset normalizzato**.

Una possibile evoluzione potrebbe essere un agente o componente intelligente, ad esempio un **Dataset Builder Agent**, posto prima del workflow principale:

```text
Dataset di PR con struttura arbitraria
                │
                ▼
       Dataset Builder Agent
                │
                ├── identifica la struttura dei record
                ├── individua i campi equivalenti
                ├── estrae le Pull Request
                ├── normalizza nomi e formati
                └── valida il risultato
                │
                ▼
           sample.json
                │
                ▼
        PullRequestLoader
                │
                ▼
         PR-to-Requirements
```

Il compito di questa componente sarebbe trasformare sorgenti strutturate in modi differenti nel contratto di input standard richiesto da PR-to-Requirements.

Questa funzionalità **non viene inclusa nella prima versione del sistema**, perché introdurrebbe un ulteriore problema di interpretazione e normalizzazione dei dati che è separato dall'obiettivo principale dello stage, cioè la ricostruzione e valutazione dei requisiti funzionali.

La prima versione mantiene quindi un confine semplice:

```text
prima del workflow
→ preparazione del dataset nel formato standard

all'interno del workflow
→ caricamento, validazione ed elaborazione delle Pull Request
```


## 12. Espansione progressiva della sperimentazione

Il singolo repository rappresenta soltanto la prima fase.

Dopo aver verificato:

- corretto funzionamento del workflow;
- stabilità del loop Generator–Assessment;
- qualità del retrieval;
- corretto utilizzo della memoria;
- processo di costruzione del gold standard;

il campione potrà essere ampliato.

Una possibile progressione è:

```text
Fase iniziale
    │
    └── 1 repository
        + numero limitato di PR

                ↓

Estensione
    │
    └── più PR dello stesso repository

                ↓

Valutazione più ampia
    │
    └── più repository

                ↓

Esperimenti cross-project
```

L'estensione permette di verificare progressivamente quanto il comportamento osservato nel primo progetto generalizzi a domini e repository differenti.

---

## 13. Possibile estensione dell'evidenza

La decisione di utilizzare inizialmente solo `title` e `body` non viene considerata definitiva.

PR4Code mette a disposizione evidenza aggiuntiva che potrebbe essere utile per ricostruire requisiti nei casi in cui la descrizione della Pull Request sia insufficiente.

In una configurazione successiva potranno essere valutati, ad esempio:

```text
PR title + body
        +
commit messages
        +
modified files
        +
code diff
        +
altri metadati
```

L'introduzione di queste sorgenti deve avvenire in modo esplicito e controllato.

In particolare, sarà possibile confrontare configurazioni come:

```text
A — title + body

B — title + body + commit descriptions

C — title + body + code changes

D — contesto completo disponibile
```

In questo modo potremo misurare se e quanto l'aggiunta di documentazione tecnica migliori:

- estraibilità;
- correttezza del requisito;
- completezza rispetto all'evidenza;
- riduzione delle informazioni inventate.

La scelta dei metadati aggiuntivi da introdurre rimane quindi **aperta** e potrà diventare parte della sperimentazione.

---

## 14. Gold standard

PR4Code fornisce Pull Request e relativi artefatti di sviluppo, ma non è costruito come gold standard di requisiti funzionali ricostruiti.

Per valutare PR-to-Requirements è quindi necessario costruire un livello di annotazione separato.

Per ogni Pull Request del campione, il gold standard dovrà rappresentare almeno:

- se la Pull Request è considerata `EXTRACTABLE` o `NOT_EXTRACTABLE`;
- quando estraibile, il requisito funzionale di riferimento;
- eventuali note o motivazioni utili alla revisione dell'annotazione.

Il gold standard viene mantenuto separato dal file di input per evitare che le informazioni di riferimento possano essere utilizzate accidentalmente durante la generazione.

Concettualmente:

```text
sample.json
    │
    ├── title
    ├── body
    └── metadata tecnici

gold.json
    │
    ├── pr_id
    ├── extractability
    ├── gold_requirement
    └── annotation_notes
```

La procedura definitiva di annotazione, revisione tra annotatori e gestione dei disaccordi deve essere definita nella metodologia sperimentale.

---

## 15. Riproducibilità

Per ogni esperimento devono essere registrati:

- dataset sorgente;
- repository selezionato;
- criteri di selezione;
- identificativi delle Pull Request;
- versione del file JSON derivato;
- campi utilizzati come evidenza dagli agenti;
- eventuali filtri applicati;
- versione del gold standard.

Il dataset sorgente rimane immutato.

I file derivati vengono trattati come artefatti dell'esperimento e devono poter essere ricostruiti attraverso il loader e il sample builder.

---

## 16. Punti da consolidare

Restano da definire durante la preparazione dell'esperimento:

- repository scelto per il primo ciclo;
- numero iniziale di Pull Request;
- criteri esatti di inclusione ed esclusione;
- gestione delle Pull Request con body assente o scarsamente informativo;
- ordinamento cronologico del campione;
- schema JSON definitivo;
- procedura di annotazione del gold standard;
- modalità di gestione dei disaccordi tra annotatori;
- quantità e tipologia dei repository da aggiungere nelle fasi successive;
- eventuale introduzione di commit messages, code diff, file modificati o altri metadati come evidenza aggiuntiva.

---

## 17. Decisione riassuntiva

Per il primo ciclo di sperimentazione viene adottata la seguente strategia:

```text
Dataset sorgente:
    PR4Code

Campione iniziale:
    un singolo repository GitHub
    numero limitato di Pull Request

Formato sperimentale:
    unico file JSON derivato

Evidenza iniziale per la generazione:
    PR title
    PR body

Metadati tecnici conservabili:
    identificatore
    repository
    PR number
    timestamp se necessario

Informazioni non fornite inizialmente agli agenti:
    commit messages / commit history
    diff e patch
    file modificati
    contenuto pre/post modifica
    statistiche sulle modifiche
    branch e altri metadati tecnici

Architettura di caricamento:
    dataset-specific adapter
        ↓
    file JSON normalizzato con 1..N Pull Request
        ↓
    PullRequestLoader
        ↓
    collezione di PullRequestRecord
        ↓
    Pipeline Runner
        ↓
    una PR alla volta nel workflow LangGraph

Gold standard:
    costruito separatamente

Evoluzione:
    aumento progressivo delle PR
    introduzione di più repository
    possibile utilizzo futuro di metadati aggiuntivi
```

La scelta permette di iniziare con un esperimento controllato e interpretabile, senza vincolare PR-to-Requirements a PR4Code e senza escludere configurazioni future che sfruttino una porzione più ampia dell'informazione disponibile nelle Pull Request.

---

## 18. Riferimenti

B. Donato, L. Mariani, D. Micucci, O. Riganelli,  
**“PR4Code: A Pull Requests Dataset for AI Code Generation”**,  
*IEEE Access*, vol. 14, pp. 108479–108491, 2026.  
DOI: `10.1109/ACCESS.2026.3713096`.
