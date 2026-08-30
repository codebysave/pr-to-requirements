# Il dataset e l'evidenza in ingresso

**Materiale per la tesi — bozza di capitolo**
Deriva da: `docs/design/decisions/06-PullRequest-Dataset-with-runner.md` (Decisione 3.6)
Progetto PR-to-Requirements · Università degli Studi di Milano-Bicocca

---

## 1. Il problema

Un sistema che ricostruisce requisiti da Pull Request deve essere valutato su Pull
Request reali. Questo pone tre questioni distinte, che vanno decise separatamente
perché rispondono a esigenze diverse:

1. **da dove provengono i dati** — quale sorgente, con quali garanzie di
   provenienza e riproducibilità;
2. **quali dati vengono forniti agli agenti** — una Pull Request contiene molto più
   della sua descrizione, e includere tutto non è necessariamente meglio;
3. **come i dati entrano nel sistema** — con quale contratto, e quanto il sistema
   dipenda dalla sorgente specifica.

La terza questione è architetturale prima che sperimentale: legare il sistema alla
struttura di un dataset particolare renderebbe impossibile riusarlo su un altro
senza riscriverlo.

---

## 2. La sorgente: PR4Code

Come sorgente di casi reali il progetto adotta **PR4Code**, il dataset presentato
in Donato, Mariani, Micucci e Riganelli (2026).

PR4Code contiene **13.339 Pull Request reali provenienti da GitHub**, estratte da
1.055 repository:

| Linguaggio | Pull Request |
|---|---|
| Java | 4.508 |
| Python | 8.831 |
| **Totale** | **13.339** |

Per ciascuna Pull Request il dataset conserva informazioni testuali e informazioni
sulla storia di sviluppo: identificativo e titolo, descrizione (`body`), stato e
branch, sequenza e messaggi dei commit, file modificati, numero di righe aggiunte e
rimosse, patch e diff, versioni dei file prima e dopo la modifica, e ulteriori
metadati.

La struttura è quindi **considerevolmente più ricca** di quella che la prima
configurazione sperimentale utilizza. Questo è deliberato: consente di ampliare
l'evidenza in configurazioni successive senza cambiare sorgente (§5).

La scelta di PR4Code offre inoltre un vantaggio metodologico: è un dataset
pubblicato e documentato, il che rende la selezione del campione ricostruibile da
terzi.

---

## 3. Il campione iniziale

Il primo ciclo sperimentale non utilizza tutte le 13.339 Pull Request. La
configurazione iniziale seleziona **un singolo repository** e, al suo interno, un
numero limitato di Pull Request.

La scelta di partire da un solo progetto ha ragioni operative precise:

- riduce l'eterogeneità e rende i risultati interpretabili;
- consente di comprendere il dominio del repository, condizione necessaria per
  annotare manualmente il riferimento;
- rende ispezionabili a mano i singoli casi;
- **permette di verificare il comportamento della memoria** su una sequenza di Pull
  Request appartenenti allo stesso progetto, che è la condizione in cui il recupero
  storico ha senso;
- consente di individuare i difetti della pipeline prima di estendere l'esperimento.

La scelta non implica che il sistema sia progettato per un solo repository.

### 3.1 I due corpus effettivamente utilizzati

La sperimentazione ha impiegato due campioni, e il confronto fra i due si è
rivelato uno dei risultati del lavoro.

| Corpus | Pull Request | Caratteristiche |
|---|---|---|
| `scrapy/scrapy` | 9 | 5 su 9 generate da uno strumento automatico di analisi della sicurezza, con testo di base identico |
| `All-Hands-AI/OpenHands` | 46 | scritte da persone, media 1.422 caratteri fra titolo e corpo |

Il primo campione è stato usato per la messa a punto del sistema e per il confronto
fra modelli. Si è però rivelato **non rappresentativo**: la presenza di cinque Pull
Request generate automaticamente, con una descrizione che dichiara l'esistenza di
una vulnerabilità e la sua correzione senza specificarne la natura, abbassa
artificialmente il tasso di estraibilità.

Il secondo campione, introdotto in un secondo momento, ha permesso di misurare
l'entità dell'effetto: **a parità di modello, di istruzioni e di codice, il tasso di
accettazione passa dal 33% al 74%.** Il dato è discusso nel capitolo 4 e ha una
conseguenza diretta sulla costruzione del riferimento annotato (capitolo 7), che va
condotta sul secondo corpus.

---

## 4. L'evidenza fornita agli agenti

Nella prima configurazione l'evidenza è **volontariamente limitata** a due campi:

```
titolo della Pull Request
+
corpo della Pull Request
```

La limitazione non deriva da un limite della sorgente. Serve a isolare una domanda
precisa:

> Fino a che punto è possibile ricostruire un requisito funzionale utilizzando la
> sola descrizione testuale della Pull Request?

### 4.1 Che cosa viene escluso, e perché

Non vengono forniti agli agenti, come evidenza per la generazione: messaggi e
sequenza dei commit; diff e patch del codice; contenuto dei file prima e dopo la
modifica; elenco dei file modificati; statistiche sulle righe; informazioni sul
branch; ulteriori metadati tecnici.

L'esclusione è deliberata e ha uno scopo sperimentale: mescolare fin dall'inizio
sorgenti di evidenza molto diverse renderebbe i risultati difficili da
interpretare. Con la sola descrizione testuale è invece possibile distinguere:

- i casi in cui la descrizione è sufficiente;
- i casi in cui è troppo vaga o incompleta;
- ciò che il modello ricostruisce effettivamente dal testo, rispetto a ciò che
  aggiunge dalla propria conoscenza del dominio;
- i casi in cui informazioni aggiuntive sarebbero effettivamente necessarie.

Quest'ultimo punto è la ragione metodologica più forte: **la restrizione è la
condizione che rende misurabile il fenomeno che il lavoro studia.** Fornendo anche
il codice modificato, un requisito corretto non direbbe più nulla su quanta
informazione le descrizioni delle Pull Request contengano.

### 4.2 Metadati tecnici ed evidenza non coincidono

Il sistema conserva informazioni che **non** vengono mostrate agli agenti:

| Campo | Uso nel sistema | Fornito agli agenti |
|---|---|---|
| `id` | identificazione, tracciabilità | no |
| `repository` | filtro del recupero dalla memoria | no |
| `pr_number` | tracciabilità, riferimento nei report | no |
| `timestamp` | ordinamento cronologico, filtro temporale della memoria | no |
| `title` | evidenza | **sì** |
| `body` | evidenza | **sì** |

La distinzione è operativa e verificabile: il messaggio inviato al modello contiene
soltanto titolo e corpo. Il `timestamp`, per esempio, è indispensabile al
funzionamento della memoria — determina quali requisiti storici siano disponibili
al momento della valutazione — ma non compare mai nel prompt.

---

## 5. Il contratto di ingresso

Il sistema **non legge PR4Code**, né alcun altro dataset nel formato originale.
Accetta un unico formato normalizzato, definito dal progetto:

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

Dal punto di vista del sistema **non è rilevante da dove provengano i dati**: la
sorgente può essere PR4Code, un altro dataset o un file costruito manualmente. La
sola condizione è che i dati siano stati portati nel formato previsto.

Il confine architetturale è quindi:

```text
qualunque sorgente di Pull Request
            │
            ▼
   normalizzazione (esterna al sistema)
            │
            ▼
       sample.json
            │
      ──────┼──────  confine di PR-to-Requirements
            │
            ▼
   PullRequestLoader  →  validazione
            │
            ▼
     Pipeline Runner  →  una Pull Request alla volta
            │
            ▼
        workflow
```

### 5.1 L'adapter della sorgente

La conversione da PR4Code al formato normalizzato è affidata a uno **script di
preprocessing** che seleziona il repository, sceglie le Pull Request, estrae i
campi necessari e produce il file.

Lo script è un *adapter della sorgente* e **non fa parte del sistema**. Se in
futuro si usasse un dataset con struttura diversa, andrebbe adattato lo script; il
workflow resterebbe invariato.

### 5.2 Il Loader e la validazione

Il `PullRequestLoader` legge il file normalizzato e costruisce i record usati dal
workflow. Non conosce PR4Code e non sa quale dataset sia stato usato in origine.

La validazione è **deliberatamente severa**: il file deve essere JSON valido; ogni
Pull Request deve avere identificatore, repository, numero, titolo e corpo; i tipi
devono corrispondere; le date devono essere rappresentate in modo coerente. Un file
non conforme non viene caricato parzialmente: il sistema si ferma con un errore di
validazione.

La severità è una scelta di progetto. Un caricamento tollerante produrrebbe record
incompleti che fallirebbero più avanti, in punti dove la causa non è più
riconoscibile.

Il contratto è quindi esplicito:

> **PR-to-Requirements accetta Pull Request già normalizzate secondo uno schema noto e
> stabile.**

### 5.3 Separazione fra caricamento ed elaborazione

Il Loader carica e valida l'intera collezione ma **non esegue il workflow**.
L'elaborazione è affidata a un componente distinto, il **Pipeline Runner**, che
prende una Pull Request alla volta, avvia un'esecuzione del grafo, attende che
raggiunga uno stato finale e solo allora passa alla successiva (capitolo 3).

La separazione mantiene distinte due responsabilità che verrebbero facilmente
confuse: la validazione dell'input e l'orchestrazione delle elaborazioni.

---

## 6. Il gold standard è separato dall'input

PR4Code fornisce Pull Request e artefatti di sviluppo, ma **non è costruito come
riferimento di requisiti funzionali**. La valutazione richiede quindi un livello di
annotazione prodotto separatamente.

Per ogni Pull Request del campione il riferimento deve rappresentare almeno:

- se la Pull Request sia considerata `EXTRACTABLE` o `NOT_EXTRACTABLE`;
- quando estraibile, il requisito funzionale di riferimento;
- le note che motivano l'annotazione.

I due file restano **fisicamente separati**:

```text
sample.json                      gold.json
    ├── title                        ├── pr_id
    ├── body                         ├── extractability
    └── metadati tecnici             ├── gold_requirement
                                     └── annotation_notes
```

La separazione non è organizzativa ma metodologica: evita che le informazioni di
riferimento possano essere accidentalmente fornite al sistema durante la
generazione, il che invaliderebbe la misura.

---

## 7. Riproducibilità

Per ogni esperimento vanno registrati: dataset sorgente, repository selezionato,
criteri di selezione, identificativi delle Pull Request, versione del file
derivato, campi utilizzati come evidenza, filtri applicati, versione del
riferimento annotato.

Il dataset sorgente rimane immutato; i file derivati sono artefatti
dell'esperimento e devono poter essere ricostruiti dallo script di preprocessing.

Nell'implementazione, ogni esecuzione produce un report che registra il file di
input, la configurazione del workflow, i modelli nella loro versione datata, la
versione dei prompt e il consumo di token — così che una prova possa essere
rieseguita nelle stesse condizioni.

---

## 8. Espansione progressiva

Il singolo repository è la prima fase di una progressione:

```text
1 repository, poche Pull Request
        ↓
più Pull Request dello stesso repository
        ↓
più repository
        ↓
esperimenti cross-project
```

L'estensione permette di verificare quanto il comportamento osservato su un
progetto generalizzi ad altri domini. Il confronto fra i due corpus già effettuato
(§3.1) mostra che la questione non è teorica: gli esiti cambiano sensibilmente al
cambiare del materiale.

### 8.1 Estensione dell'evidenza

La restrizione a titolo e corpo non è definitiva. Una configurazione successiva può
introdurre in modo controllato le altre informazioni disponibili, confrontando:

```text
A — titolo + corpo
B — titolo + corpo + messaggi dei commit
C — titolo + corpo + modifiche al codice
D — contesto completo
```

Il confronto misurerebbe se e quanto l'evidenza aggiuntiva migliori estraibilità,
correttezza del requisito, completezza rispetto all'evidenza e riduzione delle
affermazioni inventate. È una delle direzioni sperimentali più promettenti che il
lavoro lascia aperte.

### 8.2 Normalizzazione automatica: un'estensione non inclusa

La configurazione attuale richiede che la normalizzazione avvenga prima
dell'esecuzione. Un sistema capace di ricevere dataset strutturati in modi
arbitrari e convertirli automaticamente richiederebbe un componente aggiuntivo —
concettualmente un *Dataset Builder Agent* posto a monte del workflow.

La funzionalità **non è inclusa**, perché introdurrebbe un problema di
interpretazione e normalizzazione dei dati distinto dall'obiettivo del lavoro, che
è la ricostruzione e la valutazione dei requisiti funzionali.

---

## 9. Limiti e questioni aperte

**Il campione è piccolo e, nel primo corpus, non rappresentativo.** Nove Pull
Request, di cui cinque generate automaticamente con lo stesso testo di base. Il
secondo corpus corregge il problema ma resta di 46 casi, tutti dallo stesso
progetto.

**Un solo linguaggio e un solo dominio.** Entrambi i corpus sono progetti Python di
ambito infrastrutturale. La generalizzazione ad altri linguaggi e domini non è
stata verificata.

**Da consolidare:** i criteri esatti di inclusione ed esclusione delle Pull
Request; il trattamento di quelle con corpo assente o scarsamente informativo; lo
schema JSON definitivo; la procedura di annotazione e di gestione dei disaccordi
fra annotatori; la quantità e la tipologia dei repository da aggiungere.

**Una questione emersa dai dati.** Il corpus OpenHands contiene Pull Request
generate da strumenti automatici e Pull Request scritte da persone. Se le prime
vadano incluse nel campione finale è una questione aperta: condividono lo stesso
testo di base e potrebbero distorcere la misura.

---

## Riferimenti

- Donato, B., Mariani, L., Micucci, D., & Riganelli, O. (2026). *PR4Code: A Pull
  Requests Dataset for AI Code Generation.* IEEE Access, 14, 108479–108491.
  DOI: 10.1109/ACCESS.2026.3713096.
