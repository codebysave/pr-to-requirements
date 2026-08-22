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

## Nuovi punti da aggiungere

Le successive questioni progettuali ancora aperte verranno aggiunte a questo documento mantenendo, quando applicabile, la stessa struttura:

1. **questione aperta**;
2. **policy o ipotesi iniziale**;
3. **esempi o casi limite**;
4. **alternative da discutere**;
5. **decisione finale**.
