# Punti aperti da discutere con la tutor

**Progetto:** PR4Requirements  
**Stato:** Working document  
**Autori:** Andrea, Marco  
**Ultimo aggiornamento:** Agosto 2026  

---

## Scopo del documento

Questo documento raccoglie le **decisioni progettuali e metodologiche ancora aperte** che richiedono un confronto con la tutor prima di essere consolidate nel design definitivo di PR4Requirements.

Ogni punto rappresenta una questione da discutere e potrà successivamente essere:

- trasformato in una design decision dedicata;
- integrato nel codebook sperimentale;
- rimandato a un'estensione futura del progetto;
- escluso definitivamente dallo scope della tesi.

Le decisioni già consolidate non vengono mantenute in questo documento.

---

## 1. Gestione delle PR contenenti requisiti non funzionali o misti

### Questione aperta

PR4Requirements ha come target principale la ricostruzione di **requisiti funzionali**.

Nel dataset possono tuttavia essere presenti Pull Request che esprimono:

- esclusivamente requisiti funzionali;
- esclusivamente requisiti non funzionali;
- contemporaneamente aspetti funzionali e non funzionali (*mixed*);
- casi borderline, ad esempio requisiti di sicurezza che combinano un comportamento del sistema con proprietà qualitative.

È quindi necessario definire una policy chiara che stabilisca quando una PR debba essere considerata `EXTRACTABLE` e quando, invece, la pipeline debba interrompersi con `NOT_EXTRACTABLE`.

---

### Policy iniziale

Per la prima implementazione adottiamo una politica conservativa, ma non escludiamo automaticamente le PR *mixed*.

La regola provvisoria è:

> Una Pull Request viene classificata come `EXTRACTABLE` quando contiene almeno un requisito funzionale chiaramente identificabile e ricostruibile dal titolo e dal body.

Di conseguenza:

```text
Functional only
    ↓
EXTRACTABLE
    ↓
Requirement Generation
```

Le Pull Request contenenti **esclusivamente requisiti non funzionali** vengono invece considerate fuori dallo scope corrente:

```text
Non-functional only
    ↓
NOT_EXTRACTABLE
    ↓
STOP
```

Per le Pull Request *mixed* viene effettuata un'ulteriore verifica:

```text
Mixed Functional + Non-functional
            ↓
È presente una componente funzionale
chiaramente identificabile e separabile?
            ↓
        ┌───┴───┐
       YES      NO
        ↓        ↓
EXTRACTABLE   NOT_EXTRACTABLE
        ↓
Generate only
the Functional
Requirement
```

Pertanto, una PR *mixed* può essere considerata `EXTRACTABLE` se la componente funzionale può essere isolata senza introdurre assunzioni o alterare il significato dell'evidenza.

---

### Esempio di PR mixed estraibile

Pull Request:

> Add PDF report export and ensure that report generation completes within five seconds.

La PR contiene:

- una componente funzionale: **esportazione dei report in PDF**;
- una componente non funzionale: **vincolo temporale di cinque secondi**.

Poiché il comportamento funzionale è chiaramente identificabile e separabile, la PR viene classificata come:

> `EXTRACTABLE`

Il requisito generato, nello scope corrente, può essere:

> **The system shall allow users to export reports in PDF format.**

La componente relativa ai cinque secondi non viene inclusa nel requisito funzionale prodotto.

---

### Esempio di PR mixed non estraibile

Se gli aspetti funzionali e non funzionali risultano fortemente intrecciati e non è possibile ricostruire il requisito funzionale senza interpretazioni arbitrarie, la classificazione iniziale diventa:

> `NOT_EXTRACTABLE`

Il principio adottato è:

> **la presenza di informazioni non funzionali non rende automaticamente una PR non estraibile; ciò che conta è la possibilità di identificare con sufficiente affidabilità una componente funzionale autonoma e supportata dall'evidenza.**

---

### Informazione da preservare

Anche quando una PR *mixed* viene considerata `EXTRACTABLE`, è utile mantenere traccia del fatto che l'input contenesse anche informazioni non funzionali.

A livello concettuale, il sistema dovrebbe quindi poter distinguere almeno:

```text
FUNCTIONAL_ONLY
MIXED
NON_FUNCTIONAL_ONLY
```

separando questa informazione dalla decisione:

```text
EXTRACTABLE
NOT_EXTRACTABLE
```

Ad esempio:

```text
PR type: MIXED
Extractability: EXTRACTABLE
Functional component: identified
Non-functional evidence: present
```

Questa distinzione potrà essere utile anche in fase sperimentale per confrontare le prestazioni del sistema sulle PR puramente funzionali rispetto alle PR mixed.

---

### Policy provvisoria riassuntiva

| Tipo di PR | Policy iniziale |
|---|---|
| Functional only | `EXTRACTABLE` |
| Non-functional only | `NOT_EXTRACTABLE` |
| Mixed con FR chiaramente identificabile e separabile | `EXTRACTABLE` |
| Mixed con FR non separabile o ambiguo | `NOT_EXTRACTABLE` |

Per le PR *mixed* classificate come `EXTRACTABLE`, il Generator produce nella configurazione corrente **soltanto il requisito funzionale**.

---

### Da discutere con la tutor

Occorre stabilire se questa policy debba essere mantenuta o modificata.

In particolare, vogliamo discutere:

- se i requisiti esclusivamente non funzionali debbano rimanere definitivamente fuori scope;
- se per le PR *mixed* sia corretto estrarre soltanto la componente funzionale;
- quali criteri utilizzare per stabilire quando una componente funzionale sia sufficientemente **identificabile e separabile**;
- se in futuro debba essere possibile produrre separatamente anche il requisito non funzionale;
- se una singola Pull Request possa generare più requisiti;
- come trattare i casi borderline, in particolare i requisiti di sicurezza;
- se le categorie `FUNCTIONAL_ONLY`, `MIXED` e `NON_FUNCTIONAL_ONLY` debbano essere registrate esplicitamente nel dataset e nell'output della pipeline.

**Decisione definitiva:** _da definire con la tutor._

---


## 2. Gestione delle PR con contenuto testuale limitato

### Questione aperta

PR4Requirements utilizza, nella configurazione corrente, **titolo e body della Pull Request** come evidenza primaria per ricostruire un requisito funzionale.

Resta da stabilire come gestire le Pull Request che contengono una quantità di testo molto ridotta e che, di conseguenza, potrebbero non fornire informazioni sufficienti per ricostruire un requisito funzionale in modo affidabile.

La questione non riguarda soltanto il numero assoluto di caratteri, ma soprattutto la **quantità di informazione utile** presente nell'input.

Ad esempio, una PR molto breve può comunque esprimere chiaramente un comportamento funzionale, mentre una PR più lunga può risultare vaga, prevalentemente tecnica o dipendente da riferimenti esterni.

---

### Policy provvisoria

Per il momento non fissiamo una soglia minima rigida di caratteri per determinare automaticamente l'estraibilità.

La regola provvisoria è:

> Una Pull Request dovrebbe essere classificata come `EXTRACTABLE` soltanto quando titolo e body contengono evidenza sufficiente per ricostruire almeno un requisito funzionale senza introdurre informazioni non supportate.

Di conseguenza, la sola lunghezza testuale non dovrebbe determinare direttamente la classificazione:

```text
PR con pochi caratteri
        ↓
L'informazione disponibile è sufficiente
per ricostruire un requisito funzionale?
        ↓
    ┌───┴───┐
   YES      NO
    ↓        ↓
EXTRACTABLE  NOT_EXTRACTABLE
```

---

### Esempio di PR breve ma potenzialmente estraibile

Pull Request:

> Allow users to export invoices as PDF.

Anche se il testo è molto breve, il comportamento richiesto è chiaramente identificabile.

In questo caso la PR potrebbe essere classificata come:

> `EXTRACTABLE`

con un requisito funzionale del tipo:

> **The system shall allow users to export invoices in PDF format.**

---

### Esempio di PR con informazione insufficiente

Pull Request:

> Fix export issue.

In questo caso il testo non specifica quale comportamento debba essere garantito, quale operazione sia interessata o quale risultato sia atteso.

La classificazione più prudente sarebbe quindi:

> `NOT_EXTRACTABLE`

poiché la generazione di un requisito funzionale richiederebbe di introdurre informazioni non presenti nell'evidenza disponibile.

---

### Possibile uso di una soglia minima

Un punto da chiarire con la tutor è se sia opportuno introdurre anche una **soglia quantitativa minima**, ad esempio basata sul numero complessivo di caratteri o token di `title + body`.

Una soglia di questo tipo potrebbe essere utilizzata:

- come filtro preliminare del dataset;
- come indicatore di possibile insufficienza informativa;
- come variabile da registrare per l'analisi sperimentale;
- oppure non essere utilizzata affatto, lasciando la decisione di estraibilità a una valutazione semantica del contenuto.

È importante evitare che una soglia puramente quantitativa produca errori nei casi in cui una PR molto breve sia comunque sufficientemente informativa.

---

### Da discutere con la tutor

Occorre stabilire:

- se debba esistere una soglia minima di caratteri o token per considerare una PR potenzialmente estraibile;
- se tale soglia debba essere un **hard filter** oppure soltanto un'indicazione preliminare;
- se la classificazione `EXTRACTABLE` / `NOT_EXTRACTABLE` debba dipendere principalmente dalla **sufficienza informativa** anziché dalla lunghezza del testo;
- come trattare PR brevi ma semanticamente molto chiare;
- come trattare PR lunghe ma vaghe, tecniche o dipendenti da riferimenti esterni;
- se la lunghezza di `title + body` debba essere registrata come metadato per successive analisi sperimentali;
- se sia utile confrontare le prestazioni del sistema su fasce di lunghezza differenti.

**Decisione definitiva:** _da definire con la tutor._

---

## 3. Gestione di una PR che contiene più requisiti funzionali atomici

### Questione aperta

Una singola Pull Request può descrivere **più comportamenti funzionali distinti**.

In questo caso non vogliamo forzare artificialmente la regola:

```text
1 PR = 1 requisito
```

perché potremmo ottenere un requisito composto, non atomico.

Ad esempio, una PR potrebbe introdurre due opzioni indipendenti:

```text
add --source
add --custom_path
```

Un unico requisito del tipo:

> The run command shall accept the `--source` and `--custom_path` options.

potrebbe risultare poco atomico, perché le due opzioni possono essere verificate separatamente.

---

### Ipotesi iniziale

La soluzione che vogliamo discutere è mantenere separati i compiti dei diversi componenti.

L'**Extractability Check** dovrebbe limitarsi a stabilire:

```text
La PR contiene almeno un requisito funzionale estraibile?

YES → EXTRACTABLE
NO  → NOT_EXTRACTABLE
```

Non dovrebbe quindi decidere in anticipo quanti requisiti contiene la PR.

Il **Generator** dovrebbe invece poter produrre **uno o più requisiti funzionali atomici**:

```text
PR
↓
Generator
↓
FR1
FR2
...
FRn
```

La regola sarebbe molto semplice:

> se due comportamenti possono essere verificati in modo indipendente, è ragionevole considerarli due requisiti distinti.

L'**Assessment Agent** avrebbe poi il compito di controllare sia i singoli requisiti sia l'insieme prodotto dal Generator.

In particolare dovrebbe verificare che:

- un requisito non contenga più comportamenti indipendenti;
- non manchi un comportamento funzionale chiaramente presente nella PR;
- non siano stati creati requisiti duplicati o inutilmente separati;
- ogni requisito sia effettivamente supportato dall'evidenza della PR.

Se la decomposizione non è corretta, l'Assessment può restituire `REVISE` indicando, ad esempio, di **dividere** un requisito composto oppure di **unire** requisiti separati inutilmente.

---

### Esempio semplice

Pull Request:

```text
Add --source and --custom_path options to the run command.
```

Possibile output del Generator:

```text
FR1: The run command shall accept the --source option.

FR2: The run command shall accept the --custom_path option.
```

L'Assessment verifica che entrambi siano:

- atomici;
- supportati dalla PR;
- non ridondanti;
- sufficienti a coprire il contenuto funzionale della PR.

Solo quando l'insieme è considerato valido, i requisiti accettati possono essere salvati separatamente nella memoria, mantenendo però la stessa Pull Request come origine.

```text
PR #X
├── FR1
└── FR2
```

---

### Da discutere con la tutor

Vogliamo quindi chiarire:

- se una singola PR possa produrre ufficialmente **uno o più requisiti funzionali atomici**;
- se sia corretto lasciare al Generator il compito di proporre il numero di requisiti;
- se l'Assessment debba verificare anche la **corretta decomposizione dell'insieme**, oltre alla qualità di ogni singolo requisito;
- se la persistenza debba avvenire soltanto quando l'intero insieme prodotto per quella PR è stato validato.

**Ipotesi iniziale:** il Generator propone `1..N` requisiti atomici e l'Assessment verifica che il numero e la decomposizione siano corretti.

**Decisione definitiva:** _da definire con la tutor._

---

## 4. Il nome di un artefatto conosciuto vale come evidenza?

### Questione aperta

Alcune Pull Request non descrivono un comportamento: si limitano a **nominare un artefatto il cui significato è convenzionalmente noto**.

Il caso reale che ha sollevato la questione è la Pull Request #9673 del corpus `All-Hands-AI/OpenHands`. Tolto il modulo con le caselle da spuntare, il contenuto integrale è:

```text
Titolo: feat(ui): tab component

Descrizione per l'utente finale: Implements tab component
Riassunto di cosa fa la PR:      Implements tab component
```

Tre parole, ripetute due volte. Nessuna indicazione su cosa il sistema debba fare.

Da questa evidenza si può scrivere un requisito come:

> The system shall allow users to select and switch between multiple content panels.

Ma quella frase **non proviene dalla Pull Request**: proviene da ciò che chi legge già sa di un componente *tab*. La domanda è se questa conoscenza convenzionale possa essere considerata parte dell'evidenza.

---

### Perché non è un caso isolato

Il corpus contiene **cinque Pull Request strutturalmente identiche** (`feat(ui): <nome> component`, circa 530 caratteri, stesso modulo compilato allo stesso modo): tab, select, toast, spinner, dialog.

Non avendo una regola, il sistema ha prodotto **quattro esiti diversi nella stessa esecuzione**:

| PR | Componente | Esito |
|---|---|---|
| #9590 | spinner | `NOT_EXTRACTABLE` |
| #9591 | dialog | `REJECTED` |
| #9632 | toast | `ACCEPTED`, con il nome del componente conservato |
| #9673 | tab | `ACCEPTED`, dopo due giri, con il nome rimosso |
| #9712 | select | `ACCEPTED`, dopo due giri, con il nome rimosso |

L'Assessment Agent ha inoltre motivato le proprie decisioni con due affermazioni **incompatibili fra loro**, nello stesso report.

Sulla #9591:

> *L'evidenza non stabilisce alcun comportamento richiesto. Descrive l'implementazione di un componente — un meccanismo — non cosa il sistema deve fare visto dall'esterno. Un componente dialog è un blocco costruttivo interno.*

Sulla #9673:

> *Il fatto che un componente tab sia stato implementato stabilisce il comportamento per riferimento a ciò che un componente del genere fa. Un requisito può essere fondato nella natura dell'artefatto, non solo in una descrizione esplicita.*

L'incoerenza non è un difetto di implementazione: è la conseguenza dell'assenza di un criterio. Il sistema non può essere coerente su una domanda a cui non abbiamo mai risposto.

---

### Policy provvisoria adottata

Per la configurazione corrente adottiamo la **risposta negativa**:

> Il significato convenzionale di un artefatto nominato **non costituisce evidenza**. Se, rimuovendo il nome dell'artefatto, l'evidenza non stabilisce più alcun comportamento osservabile, la Pull Request è `NOT_EXTRACTABLE`.

Le cinque Pull Request dell'esempio ricadono quindi tutte in `NOT_EXTRACTABLE`.

Tre ragioni motivano la scelta.

**1. Il requisito che ne deriverebbe non riguarda questo sistema.** La frase «il sistema deve permettere all'utente di passare fra più pannelli di contenuto» è vera di *qualunque* software dotato di schede. È la definizione del termine, non un requisito ricostruito da quella Pull Request: non trasporta informazione proveniente dall'evidenza.

**2. È una condizione di validità della domanda di ricerca.** Il progetto misura *quanta informazione sui requisiti è ricostruibile dalle Pull Request*. Se il modello colma le lacune dell'evidenza con la propria conoscenza generale del dominio, la misura riguarda la conoscenza del modello e non il contenuto delle Pull Request, e il risultato sperimentale perde significato.

**3. È coerente con un criterio già adottato.** La Decisione 3.1 contiene già il *removal test*: rimosso il nome di una libreria o di un modulo, se resta un comportamento allora quel nome era dettaglio implementativo. La regola qui proposta ne è il caso complementare: rimosso il nome, se **non** resta alcun comportamento, non c'è requisito da scrivere.

---

### Cosa la policy non esclude

La regola vieta di fondare un requisito **soltanto** sul nome. Non esclude le Pull Request che nominano un artefatto **e** indicano un punto di contatto osservabile.

Confronto fra due Pull Request del corpus, entrambe con il corpo quasi vuoto:

| PR | Contenuto utile | Esito secondo la policy |
|---|---|---|
| #9632 | «Implements toast component» | `NOT_EXTRACTABLE` — solo il nome |
| #9637 | «Add `--log-level` to CLI arguments» | `EXTRACTABLE` — nomina un'interfaccia osservabile |

Nel secondo caso l'evidenza dice *dove* il comportamento si manifesta: un'opzione della riga di comando è verificabile dall'esterno senza ricorrere a conoscenza convenzionale.

---

### L'argomento contrario, che riteniamo legittimo

Un analista dei requisiti che legge «implements tab component» inferirebbe comunque che l'utente potrà passare da un pannello all'altro, e nessuno considererebbe quell'inferenza arbitraria. Adottando la policy negativa si scarta informazione che una persona competente utilizzerebbe, e si classificano come non estraibili Pull Request che introducono funzionalità realmente visibili all'utente finale.

La scelta è quindi **prudenziale e non ovvia**: privilegia la validità della misura rispetto alla copertura del dataset.

---

### Reversibilità

La policy è deliberatamente localizzata, così da poter essere invertita rapidamente se la tutor ritiene preferibile la risposta positiva. L'inversione richiede la modifica di:

- un paragrafo della Decisione 3.1;
- il blocco `<definitions>` condiviso dai due prompt, dove il criterio si innesta accanto al *removal test* già presente;
- un passo della procedura del prompt di Assessment;
- un esempio per prompt.

Non sono coinvolti il grafo, il routing, gli agenti né la memoria persistente. L'effetto atteso dell'inversione, sul corpus attuale, è il passaggio delle cinque Pull Request da `NOT_EXTRACTABLE` a `EXTRACTABLE`, con requisiti espressi al livello di astrazione che l'artefatto nominato consente.

---

### Da discutere con la tutor

- se il significato convenzionale di un artefatto nominato debba essere considerato parte dell'evidenza oppure conoscenza esterna;
- se la risposta debba dipendere dal grado di standardizzazione del termine (un componente di interfaccia molto diffuso rispetto a un artefatto specifico di un dominio);
- se un requisito valido per qualunque sistema dotato di quell'artefatto debba comunque essere considerato un risultato utile della ricostruzione;
- quale delle due politiche renda più difendibile la validità della misura sperimentale;
- se la distinzione fra «nome soltanto» e «nome più punto di contatto osservabile» sia sufficientemente netta per essere applicata in modo ripetibile dagli annotatori del gold standard;
- se la classificazione di questi casi debba essere registrata come categoria a sé nel dataset, per poterne misurare separatamente l'impatto.

**Policy provvisoria:** il nome da solo non è evidenza; l'esito è `NOT_EXTRACTABLE`.

**Decisione definitiva:** _da definire con la tutor._

---

## Nuovi punti da aggiungere

Le successive questioni progettuali ancora aperte verranno aggiunte a questo documento mantenendo, quando applicabile, la stessa struttura:

1. **questione aperta**;
2. **policy o ipotesi iniziale**;
3. **esempi o casi limite**;
4. **alternative da discutere**;
5. **decisione finale**.
