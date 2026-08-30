# Decisione 3.7 — Piano di valutazione dei requisiti generati

**Fase:** 3 — Design del sistema  
**Stato:** Proposta da validare  
**Autori:** Andrea, Marco  
**Data:** Agosto 2026

---

## 1. Contesto

Dopo aver definito il workflow completo di PR-to-Requirements, dobbiamo stabilire come valuteremo in maniera indipendente e riproducibile la qualità dei requisiti funzionali prodotti dal sistema.

La domanda principale a cui vogliamo rispondere è:

> **Il requisito funzionale prodotto da PR-to-Requirements rappresenta correttamente il comportamento ricostruibile dalla Pull Request ed è formulato con una qualità adeguata?**

Per rispondere a questa domanda abbiamo deciso di costruire la valutazione su tre elementi principali:

```text
Gold standard
      +
Rubrica di qualità basata sui criteri adottati nel progetto
      +
Valutazione umana
```

Non consideriamo sufficiente utilizzare l'Assessment Agent interno come unico valutatore finale, perché esso fa parte del sistema che stiamo valutando.

---

## 2. Prime prove sul workflow

Durante lo sviluppo abbiamo già eseguito alcune prove progressive del workflow, confrontando configurazioni via via più complete:

```text
Generation Agent
        ↓
Generation + Assessment
        ↓
Generation + Assessment + Memory
```

Da queste prove abbiamo osservato un miglioramento qualitativo progressivo degli output man mano che introducevamo l'Assessment Agent e successivamente la memoria.

In particolare:

- con il solo Generation Agent riuscivamo già a ottenere alcuni requisiti corretti, ma con una maggiore presenza di formulazioni incomplete, ambigue o contenenti dettagli non supportati;
- con l'introduzione dell'Assessment Agent abbiamo osservato una maggiore capacità di correggere questi problemi attraverso il ciclo di feedback e revisione;
- con l'aggiunta della memoria abbiamo introdotto anche la possibilità di valutare il requisito rispetto ai requisiti storici già validati, identificando duplicazioni, sovrapposizioni, refinement, sostituzioni e conflitti.

Queste prove ci hanno portato a mantenere come configurazione di riferimento il workflow completo:

```text
Generation Agent
        ↓
Assessment Agent
        ↓
Persistent Memory
```

Il piano di valutazione descritto in questa decisione riguarda quindi principalmente la qualità dei requisiti finali prodotti da questa configurazione.

### 2.1 La memoria è una condizione sperimentale, non un miglioramento assunto

> **Aggiornamento (30 agosto 2026).** Il recupero dei requisiti storici è stato
> implementato ed è ora attivo. Ne discendono tre conseguenze per il piano di
> valutazione.

**Il sistema diventa dipendente dall'ordine.** Valutando la quarantesima Pull
Request, l'Assessment Agent ha davanti i requisiti prodotti dalle trentanove
precedenti. Due esecuzioni sullo stesso materiale in ordine diverso possono
quindi dare risultati diversi. È realistico — nella pratica i requisiti si
accumulano — ma va dichiarato: le Pull Request sono elaborate in ordine
cronologico e la memoria è azzerata a ogni esecuzione (l'isolamento è garantito
dalla colonna `run_id`, si veda la Decisione 3.3 §13.1).

**`memory_enabled` acceso e spento sono due condizioni diverse**, non una
configurazione migliore e una peggiore. Il recupero cambia l'input del
valutatore su *ogni* Pull Request, comprese quelle che con la memoria non hanno
alcuna relazione: può quindi spostare esiti dove non dovrebbe. Il confronto fra
le due condizioni va eseguito e riportato, con le repliche necessarie a
distinguere l'effetto dal rumore.

**L'affermazione del §2 secondo cui la memoria ha prodotto un miglioramento
qualitativo va verificata, non citata.** È stata scritta prima che il recupero
esistesse in questo repository, e descrive quindi un'aspettativa di progetto.
La prima misura disponibile è l'esecuzione del 30 agosto
(`experiments/runs/run-20260830T112646Z.json`), che mostra che il meccanismo
**funziona** — il duplicato viene individuato e nominato, e nessuna relazione
viene inventata sulle Pull Request non correlate — ma una singola esecuzione,
senza gold standard, non sostiene alcuna affermazione sulla qualità.

---

## 3. Obiettivi della valutazione

Con la valutazione vogliamo stabilire:

- se il sistema ricostruisce il comportamento funzionale corretto;
- se il requisito è supportato dall'evidenza presente nella Pull Request;
- se vengono introdotte informazioni non supportate;
- se il requisito è formulato secondo i criteri di qualità adottati;
- se l'output può essere considerato `VALID` oppure `NOT_VALID`;
- quale livello qualitativo raggiunge il requisito anche nei casi validi;
- quanto il risultato prodotto sia semanticamente coerente con il requisito umano di riferimento;
- con quale frequenza il sistema produce requisiti accettabili sul campione sperimentale.

---

## 4. Gold standard

PR4Code non contiene, per ogni Pull Request, un requisito funzionale di riferimento già annotato.

Per questo motivo abbiamo deciso di costruire separatamente il gold standard relativo al campione sperimentale.

Per ogni Pull Request annoteremo almeno:

```text
pr_id
extractability
gold_requirement
annotation_notes
```

Ad esempio:

```json
{
  "pr_id": "repo-101",
  "extractability": "EXTRACTABLE",
  "gold_requirement": "The system shall allow users to export reports in PDF format.",
  "annotation_notes": "The behavior is explicitly described in the PR body."
}
```

Per una Pull Request non estraibile:

```json
{
  "pr_id": "repo-102",
  "extractability": "NOT_EXTRACTABLE",
  "gold_requirement": null,
  "annotation_notes": "The PR does not contain enough evidence to reconstruct a functional requirement."
}
```

Il gold standard rappresenterà quindi la nostra risposta di riferimento alla domanda:

> **Quale requisito funzionale è effettivamente supportato da questa Pull Request?**

---

## 5. Costruzione del gold standard

Per ridurre il più possibile la soggettività, abbiamo deciso che il gold standard dovrà essere costruito da almeno due annotatori.

La procedura prevista è:

```text
Pull Request
     │
     ├──► Annotatore A
     │
     └──► Annotatore B
              │
              ▼
        confronto risultati
              │
              ▼
      risoluzione disaccordi
              │
              ▼
        Gold definitivo
```

Applicheremo gli stessi criteri già definiti nel progetto per stabilire:

- estraibilità;
- contenuto funzionale;
- livello di astrazione;
- informazioni supportate;
- formulazione del requisito.

In caso di disaccordo confronteremo le due annotazioni e definiremo una versione condivisa prima di utilizzare il caso nella valutazione.

Manterremo il gold separato dall'input fornito a PR-to-Requirements, in modo che non possa essere utilizzato accidentalmente durante la generazione.

---

## 6. Confronto tra requisito generato e gold

Non confronteremo il requisito generato con il gold tramite uguaglianza testuale.

Due requisiti possono descrivere lo stesso comportamento pur utilizzando formulazioni differenti.

Ad esempio:

```text
Gold:
The system shall allow users to export reports as PDF.

Generated:
The system shall support exporting reports in PDF format.
```

Le due frasi sono diverse dal punto di vista lessicale, ma possono rappresentare lo stesso requisito.

Per questo motivo valuteremo soprattutto:

- corrispondenza del comportamento;
- corrispondenza dell'azione funzionale principale;
- assenza di dettagli aggiuntivi non supportati;
- assenza di parti funzionali rilevanti omesse.

Per rappresentare questo confronto potremo utilizzare una scala come:

```text
MATCH
PARTIAL_MATCH
NO_MATCH
```

oppure, in una forma più semplice:

```text
SEMANTICALLY_CORRECT
SEMANTICALLY_NOT_CORRECT
```

La scelta definitiva della scala verrà consolidata prima della valutazione finale.

---

## 7. Rubrica di qualità

Oltre al confronto con il gold, valuteremo ogni requisito generato attraverso una rubrica basata sui criteri adottati nella Decisione 3.1 e derivati dal framework ISO/IEC/IEEE 29148.

Per ogni criterio assegneremo un esito:

```text
PASS
FAIL
```

La prima versione della rubrica comprende:

| Criterio | Domanda di valutazione |
|---|---|
| **Functional** | Il requisito descrive un comportamento funzionale del sistema? |
| **Evidence fidelity** | Il contenuto è supportato dalla PR? |
| **Necessary / supported** | Ogni informazione presente è necessaria o giustificata dall'evidenza? |
| **Atomic / singular** | Il requisito esprime un solo comportamento principale? |
| **Unambiguous** | La formulazione evita interpretazioni alternative rilevanti? |
| **Clear** | Il requisito è comprensibile e formulato in modo diretto? |
| **Complete relative to evidence** | Esprime quanto necessario senza introdurre dettagli non supportati? |
| **Verifiable** | È possibile stabilire se il comportamento richiesto è stato soddisfatto? |
| **Feasible** | Il comportamento descritto è ragionevolmente realizzabile nel contesto disponibile? |
| **Consistent** | Non introduce contraddizioni evidenti con l'evidenza o con il contesto noto? |
| **Correct abstraction** | Descrive il comportamento richiesto senza scendere inutilmente nei dettagli implementativi? |
| **Traceable** | È possibile ricondurre il requisito alla Pull Request da cui è stato ricostruito? |

Potremo affinare la rubrica durante la preparazione della sperimentazione, ma vogliamo fissare i criteri definitivi prima della valutazione finale del campione.

---

## 8. Hard gate e validità finale

Abbiamo deciso che non tutti i criteri debbano avere necessariamente lo stesso peso.

Alcune proprietà saranno considerate **obbligatorie** per poter classificare un requisito come valido.

La prima proposta di hard gate è:

```text
Functional                → PASS obbligatorio
Evidence fidelity         → PASS obbligatorio
Unsupported claims        → assenti
Atomic / singular         → PASS obbligatorio
Unambiguous               → PASS obbligatorio
Verifiable                → PASS obbligatorio
```

Se uno dei criteri obbligatori fallisce:

```text
FINAL VALIDITY = NOT_VALID
```

anche se il requisito ottiene buoni risultati sugli altri criteri.

Questa scelta ci permette di evitare che una buona forma compensi un errore sostanziale.

Ad esempio:

```text
Clear                PASS
Atomic               PASS
Correct abstraction  PASS
Evidence fidelity    FAIL
```

porta comunque a:

```text
NOT_VALID
```

---

## 9. Quality score

Oltre alla classificazione `VALID / NOT_VALID`, vogliamo mantenere la possibilità di associare al requisito un punteggio qualitativo.

Questo punteggio non sostituirà gli hard gate.

Una possibilità semplice consiste nell'assegnare:

```text
PASS = 1
FAIL = 0
```

a ogni criterio della rubrica e calcolare:

```text
quality_score =
numero di criteri PASS
/
numero totale di criteri
```

Il risultato potrà essere espresso, ad esempio, come:

```text
8/10
```

oppure:

```text
80%
```

In questo modo manterremo separate due informazioni:

```text
Validity
    → VALID / NOT_VALID

Quality
    → punteggio complessivo
```

Un requisito potrà quindi avere un punteggio qualitativo relativamente alto ma risultare comunque `NOT_VALID` se fallisce uno degli hard gate.

---

## 10. Valutazione umana

Almeno nella fase sperimentale iniziale, abbiamo deciso di utilizzare la valutazione umana come parte fondamentale del processo.

Revisioneremo manualmente gli output del sistema applicando:

- il gold standard;
- la rubrica di qualità;
- gli hard gate;
- la verifica di eventuali informazioni non supportate.

Quando possibile, effettueremo la valutazione in maniera indipendente tra i due annotatori.

Per ridurre possibili bias, durante la revisione del requisito finale non sarà necessario mostrare al valutatore:

- la decisione interna dell'Assessment Agent;
- il numero di retry effettuati;
- l'eventuale relazione con la memoria;
- altre informazioni interne al workflow che non servono a giudicare la qualità del requisito finale.

La valutazione umana si concentrerà quindi sul rapporto:

```text
Pull Request
      ↕
Generated Requirement
      ↕
Gold Requirement
```

---

## 11. Regola anti-circolarità

Abbiamo deciso che l'Assessment Agent interno non potrà essere utilizzato come unica fonte della valutazione finale.

L'Assessment Agent produce già durante il workflow decisioni come:

```text
ACCEPT
REVISE
REJECT
```

Utilizzare la stessa valutazione come prova finale della qualità del sistema significherebbe far giudicare il sistema da una sua stessa componente.

Per questo motivo manterremo separata la valutazione sperimentale:

```text
PR-to-Requirements
      │
      ▼
Generated Requirement
      │
      ▼
External Evaluation
      │
      ├── Gold standard
      ├── Human evaluation
      └── Quality rubric
```

Consideriamo quindi l'Assessment Agent parte del sistema sotto test, non il giudice definitivo delle proprie prestazioni.

---

## 12. Metriche principali

A partire dalle annotazioni raccolte calcoleremo metriche semplici e direttamente interpretabili.

### 12.1 Valid Requirement Rate

Calcoleremo la percentuale di requisiti generati che superano tutti gli hard gate:

```text
Valid Requirement Rate =
numero requisiti VALID
/
numero requisiti valutati
```

Ad esempio:

```text
72 requisiti VALID su 80
→ 90%
```

---

### 12.2 Pass rate per criterio

Per ogni proprietà della rubrica calcoleremo la percentuale di `PASS`.

Ad esempio:

```text
Evidence fidelity PASS    = ...
Atomicity PASS            = ...
Clarity PASS              = ...
Verifiability PASS        = ...
Correct abstraction PASS  = ...
```

Queste metriche ci permetteranno di capire in quali aspetti il sistema è più forte e in quali incontra maggiori difficoltà.

---

### 12.3 Unsupported Claim Rate

Misureremo esplicitamente la percentuale di requisiti che introducono almeno un'informazione non supportata dalla Pull Request.

```text
Unsupported Claim Rate =
requisiti con almeno un unsupported claim
/
requisiti valutati
```

Consideriamo questa metrica particolarmente importante perché la fedeltà all'evidenza costituisce uno degli obiettivi principali del sistema.

---

### 12.4 Semantic correctness rispetto al gold

Misureremo la percentuale di requisiti il cui comportamento viene giudicato semanticamente corretto rispetto al gold standard.

A seconda della scala scelta potremo riportare:

```text
% SEMANTICALLY_CORRECT
```

oppure la distribuzione:

```text
MATCH
PARTIAL_MATCH
NO_MATCH
```

---

### 12.5 Quality score medio

Se adotteremo il punteggio qualitativo descritto nella Sezione 9, calcoleremo:

```text
quality score medio
mediana
distribuzione dei punteggi
```

Utilizzeremo questo valore come misura descrittiva e non come sostituto della validità finale.

---

## 13. Valutazione dell'estraibilità

Valuteremo separatamente anche la fase:

```text
EXTRACTABLE / NOT_EXTRACTABLE
```

Confronteremo il risultato prodotto dal sistema con l'annotazione presente nel gold standard.

Potremo quindi calcolare:

```text
Accuracy
Precision
Recall
F1-score
```

Questa valutazione è importante perché un errore nella classificazione di estraibilità può impedire la generazione di un requisito corretto oppure provocare la generazione di un requisito quando l'evidenza non è sufficiente.

---

## 14. Metriche automatiche supplementari

Potremo utilizzare anche metriche automatiche di similarità semantica tra requisito generato e gold come informazione aggiuntiva.

Ad esempio:

```text
embedding(generated_requirement)
        ↕
embedding(gold_requirement)
        ↓
cosine similarity
```

Non utilizzeremo però queste metriche da sole per decidere se un requisito è corretto.

Due requisiti semanticamente simili possono infatti differire per un dettaglio non supportato che rende l'output non valido.

Le metriche automatiche saranno quindi considerate **supplementari** rispetto al gold standard e alla valutazione umana.

---

## 15. Tracciabilità dei risultati

Per ogni requisito valutato conserveremo almeno:

```text
pr_id
generated_requirement
gold_requirement
semantic_match
criterion_results
unsupported_claims
final_validity
quality_score
human_notes
```

Questo ci permetterà di ricostruire successivamente:

- perché un requisito è stato classificato `VALID` o `NOT_VALID`;
- quali criteri sono falliti;
- quali tipi di errore sono più frequenti;
- come sono state calcolate le metriche aggregate.

---

## 16. Punti da consolidare

Prima della valutazione finale dovremo definire in modo definitivo:

- numero di Pull Request annotate;
- numero di annotatori;
- procedura di risoluzione dei disaccordi;
- insieme definitivo dei criteri della rubrica;
- criteri considerati hard gate;
- scala del confronto con il gold (`MATCH/PARTIAL_MATCH/NO_MATCH` oppure binaria);
- formula definitiva del quality score;
- eventuale misura dell'accordo tra annotatori;
- eventuale utilizzo di metriche automatiche supplementari;
- formato del file contenente i risultati della valutazione.

---

## 17. Decisione riassuntiva

Abbiamo deciso di valutare PR-to-Requirements attraverso il confronto tra l'output finale del sistema e una valutazione esterna costruita sul campione sperimentale.

Il piano adottato è:

```text
Campione di Pull Request
        │
        ▼
Gold standard umano
        │
        ▼
PR-to-Requirements
Generator + Assessment + Memory
        │
        ▼
Generated Requirement
        │
        ├── confronto con Gold
        ├── rubrica PASS / FAIL
        ├── hard gate
        └── valutazione umana
                │
                ▼
        VALID / NOT_VALID
                +
          Quality Score
```

Le metriche principali saranno:

```text
Valid Requirement Rate
Pass rate per criterio
Unsupported Claim Rate
Semantic correctness rispetto al gold
Quality score medio
```

La valutazione finale rimarrà indipendente dall'Assessment Agent interno al workflow e utilizzerà il gold standard e la revisione umana come riferimento principale.

---

## 18. Riferimenti interni

- Decisione 3.1 — Standard di qualità e forma dei requisiti.
- Decisione 3.5 — Architettura degli agenti e loop di retry.
- Decisione 3.6 — Dataset di Pull Request e costruzione del campione sperimentale.
