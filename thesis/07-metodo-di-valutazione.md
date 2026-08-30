# Il metodo di valutazione

**Materiale per la tesi — bozza di capitolo**
Deriva da: `docs/design/decisions/07-Evaluation-System.md` (Decisione 3.7)
Progetto PR4Requirements · Università degli Studi di Milano-Bicocca

---

## 1. Il problema

Un sistema che ricostruisce requisiti produce enunciati in linguaggio naturale. Per
stabilire se funzioni occorre rispondere a una domanda che non ha una risposta
automatica: **che cosa significa che un requisito prodotto è corretto?**

La difficoltà è duplice. Non esiste una risposta di riferimento già disponibile —
il dataset delle Pull Request non contiene requisiti annotati — e non esiste una
misura testuale adeguata: due formulazioni diverse possono esprimere lo stesso
comportamento, e due formulazioni simili possono differire per un dettaglio che
rende una delle due non valida.

Il capitolo definisce il protocollo con cui il sistema viene misurato. Il vincolo
metodologico centrale è enunciato al §7 e attraversa tutto il resto: **il
componente che valuta all'interno del sistema non può essere il giudice delle
prestazioni del sistema.**

---

## 2. Obiettivi

La valutazione deve stabilire:

- se il sistema ricostruisce il comportamento funzionale corretto;
- se il requisito è supportato dall'evidenza della Pull Request;
- se vengono introdotte informazioni non supportate;
- se il requisito rispetta i criteri di qualità adottati (capitolo 1);
- se l'esito possa essere considerato valido o non valido;
- quale livello qualitativo raggiunga anche nei casi validi;
- quanto sia semanticamente coerente con il requisito umano di riferimento;
- con quale frequenza il sistema produca requisiti accettabili sul campione.

---

## 3. Il riferimento annotato

### 3.1 Che cos'è

Il dataset sorgente non contiene, per ciascuna Pull Request, un requisito
funzionale di riferimento. Il riferimento va quindi **costruito separatamente**.

Per ogni Pull Request del campione si annota:

```json
{
  "pr_id": "repo-101",
  "extractability": "EXTRACTABLE",
  "gold_requirement": "The system shall allow users to export reports in PDF format.",
  "annotation_notes": "The behaviour is explicitly described in the PR body."
}
```

e, per una Pull Request non estraibile:

```json
{
  "pr_id": "repo-102",
  "extractability": "NOT_EXTRACTABLE",
  "gold_requirement": null,
  "annotation_notes": "The PR does not contain enough evidence to reconstruct a functional requirement."
}
```

Il riferimento è la risposta a una domanda precisa:

> **Quale requisito funzionale è effettivamente supportato da questa Pull Request?**

### 3.2 Come viene costruito

Per ridurre la soggettività, il riferimento è costruito da **almeno due
annotatori** che lavorano **separatamente**, applicando i criteri del capitolo 1:
estraibilità, contenuto funzionale, livello di astrazione, informazioni supportate,
formulazione.

```text
Pull Request
     ├──► Annotatore A
     └──► Annotatore B
              │
              ▼
      confronto delle annotazioni
              │
              ▼
      risoluzione dei disaccordi
              │
              ▼
        riferimento definitivo
```

**I disaccordi non sono un incidente da minimizzare, ma un dato.** Il grado di
accordo fra due annotatori competenti misura quanto il compito sia intrinsecamente
ambiguo, e stabilisce inoltre un **limite superiore** per il sistema: non è
ragionevole attendersi che concordi con gli annotatori più di quanto gli annotatori
concordino fra loro. Senza questo numero, un accordo del 70% non è interpretabile —
non si sa se sia un buon risultato o uno scarso.

### 3.3 La separazione dall'input

Il riferimento è mantenuto in un file distinto da quello fornito al sistema. La
separazione è metodologica prima che organizzativa: evita che le informazioni di
riferimento possano essere accidentalmente fornite durante la generazione, il che
invaliderebbe la misura.

### 3.4 Una nota sulla scelta del campione

Il riferimento va costruito sul corpus che si intende usare per la valutazione
finale. La sperimentazione ha mostrato che questa scelta non è indifferente: a
parità di modello e di istruzioni, il tasso di accettazione varia sensibilmente fra
i due corpus disponibili (capitolo 2, §3.1). Le schede di annotazione preparate sul
primo corpus vanno quindi rifatte sul secondo.

---

## 4. Il confronto con il riferimento

**Il confronto non avviene per uguaglianza testuale.** Due requisiti possono
descrivere lo stesso comportamento con formulazioni diverse:

```text
Riferimento:  The system shall allow users to export reports as PDF.
Generato:     The system shall support exporting reports in PDF format.
```

Si valutano invece: la corrispondenza del comportamento; la corrispondenza
dell'azione funzionale principale; l'assenza di dettagli aggiuntivi non supportati;
l'assenza di parti funzionali rilevanti omesse.

La scala può essere a tre livelli (`MATCH`, `PARTIAL_MATCH`, `NO_MATCH`) oppure
binaria; la scelta definitiva va consolidata prima della valutazione finale.

> **Il punto non è opinabile, ed è confermato dai dati.** Il campione contiene due
> Pull Request con titolo e corpo identici byte per byte. Su sedici esecuzioni, le
> due hanno prodotto la **stessa formulazione soltanto 2 volte su 14** in cui
> entrambe sono state accettate, pur ricevendo lo **stesso esito 15 volte su 16**.
> Un confronto testuale misurerebbe quindi soprattutto la variabilità lessicale del
> modello, non la correttezza del requisito.

---

## 5. La rubrica di qualità

Ogni requisito generato viene valutato su dodici criteri derivati dal capitolo 1,
con esito **`PASS` / `FAIL`**.

| Criterio | Domanda |
|---|---|
| **Functional** | descrive un comportamento funzionale del sistema? |
| **Evidence fidelity** | il contenuto è supportato dalla Pull Request? |
| **Necessary / supported** | ogni informazione è necessaria o giustificata dall'evidenza? |
| **Atomic / singular** | esprime un solo comportamento principale? |
| **Unambiguous** | evita interpretazioni alternative rilevanti? |
| **Clear** | è comprensibile e formulato in modo diretto? |
| **Complete relative to evidence** | esprime quanto necessario senza aggiungere dettagli non supportati? |
| **Verifiable** | è possibile stabilire se il comportamento è soddisfatto? |
| **Feasible** | il comportamento è ragionevolmente realizzabile? |
| **Consistent** | non contraddice l'evidenza o il contesto noto? |
| **Correct abstraction** | evita dettagli implementativi non necessari? |
| **Traceable** | è riconducibile alla Pull Request di origine? |

I criteri possono essere affinati durante la preparazione, ma vanno **fissati prima
della valutazione finale**: modificarli dopo aver visto i risultati
comprometterebbe la misura.

---

## 6. Condizioni necessarie e punteggio

### 6.1 Le condizioni necessarie

Non tutti i criteri hanno lo stesso peso. Alcuni sono **obbligatori** perché un
requisito possa essere considerato valido:

```text
Functional            → PASS obbligatorio
Evidence fidelity     → PASS obbligatorio
Unsupported claims    → assenti
Atomic / singular     → PASS obbligatorio
Unambiguous           → PASS obbligatorio
Verifiable            → PASS obbligatorio
```

Il fallimento di uno solo di essi comporta `NOT_VALID`, indipendentemente dagli
altri:

```text
Clear                PASS
Atomic               PASS
Correct abstraction  PASS
Evidence fidelity    FAIL
                     ──────
                     NOT_VALID
```

La scelta impedisce che **una buona forma compensi un errore sostanziale**. È lo
stesso principio che governa la decisione dell'agente valutatore all'interno del
sistema (capitolo 3, §7.3), applicato qui alla valutazione esterna.

### 6.2 Il punteggio di qualità

Accanto alla classificazione binaria si mantiene un punteggio descrittivo:
assegnando `PASS = 1` e `FAIL = 0`,

```text
quality_score = criteri superati / criteri totali
```

Le due informazioni restano **separate**:

```text
Validità   → VALID / NOT_VALID
Qualità    → punteggio complessivo
```

Un requisito può avere un punteggio alto e risultare comunque non valido, se
fallisce una condizione necessaria. Il punteggio è una misura descrittiva, non un
sostituto della validità.

---

## 7. La regola anti-circolarità

> **Il Requirement Assessment Agent non può essere la fonte della valutazione
> finale.**

L'agente produce già, durante l'esecuzione, decisioni `ACCEPT`, `REVISE` e
`REJECT`. Utilizzarle come prova della qualità del sistema significherebbe far
giudicare il sistema a una sua componente.

```text
PR4Requirements
      │
      ▼
requisito generato
      │
      ▼
valutazione esterna
      ├── riferimento annotato
      ├── valutazione umana
      └── rubrica di qualità
```

L'agente valutatore è quindi **parte del sistema sotto esame**, non il giudice
delle proprie prestazioni.

La regola ha una conseguenza concreta sull'implementazione, che vale la pena
rendere esplicita: la rubrica dei dodici criteri e le condizioni necessarie del §6
**non sono state introdotte nei prompt degli agenti**. Il sistema applica criteri
propri, più ristretti; la rubrica appartiene alla misura esterna. Se le due cose
coincidessero, il sistema risulterebbe conforme per costruzione.

---

## 8. La valutazione umana

Nella fase sperimentale la revisione manuale è parte essenziale del processo. Gli
esiti del sistema vengono esaminati applicando il riferimento annotato, la rubrica,
le condizioni necessarie e la verifica delle affermazioni non supportate. Quando
possibile, i due annotatori valutano in modo indipendente.

**Per ridurre distorsioni, al valutatore umano non vengono mostrate** la decisione
interna dell'agente, il numero di tentativi effettuati, l'eventuale relazione con
la memoria e le altre informazioni interne al flusso.

La ragione è diretta: sapere che il sistema ha impiegato tre tentativi, o che il suo
valutatore aveva sollevato obiezioni, influenzerebbe il giudizio su un requisito che
va valutato per quello che dice. La valutazione si concentra quindi sul solo
rapporto

```text
Pull Request  ↕  requisito generato  ↕  requisito di riferimento
```

---

## 9. Le metriche

### 9.1 Metriche principali

**Valid Requirement Rate** — percentuale di requisiti che superano tutte le
condizioni necessarie.

**Pass rate per criterio** — percentuale di `PASS` su ciascuna proprietà della
rubrica. Consente di individuare in quali aspetti il sistema è più solido e in
quali incontra difficoltà, informazione che la sola percentuale complessiva
nasconde.

**Unsupported Claim Rate** — percentuale di requisiti che introducono almeno
un'informazione non supportata. È particolarmente rilevante, perché la fedeltà
all'evidenza è l'obiettivo caratteristico del sistema.

**Semantic correctness** — percentuale di requisiti giudicati semanticamente
corretti rispetto al riferimento, o distribuzione sulla scala adottata.

**Quality score** — media, mediana e distribuzione dei punteggi, come misura
descrittiva.

### 9.2 Valutazione dell'estraibilità

La classificazione `EXTRACTABLE` / `NOT_EXTRACTABLE` viene valutata separatamente,
confrontando l'esito del sistema con l'annotazione, e consente di calcolare
accuratezza, precisione, richiamo e *F1*.

La valutazione separata è necessaria perché un errore in questa fase ha
conseguenze asimmetriche: classificare come non estraibile una Pull Request che lo
è impedisce la generazione di un requisito corretto; l'errore opposto produce un
requisito dove l'evidenza non lo sostiene.

### 9.3 Metriche automatiche supplementari

Metriche di similarità semantica fra requisito generato e riferimento possono
essere usate come informazione **aggiuntiva**, mai come criterio unico: due
requisiti semanticamente simili possono differire per un dettaglio non supportato
che rende l'esito non valido.

---

## 10. La variabilità come vincolo del protocollo

Un vincolo non previsto nella formulazione originaria si è imposto durante
l'implementazione.

**I parametri di campionamento non sono più disponibili.** Il piano prevedeva di
contenere la variabilità fissando la temperatura a zero. I parametri
`temperature`, `top_p` e `top_k` sono stati rimossi dall'interfaccia dei modelli
attuali. La variabilità non può quindi essere soppressa: **deve essere misurata**.

**La sua ampiezza è stata misurata**, e non è trascurabile:

| Osservazione | Risultato |
|---|---|
| Coppia di Pull Request identiche, su 16 esecuzioni — stesso esito | 15 su 16 |
| Coppia di Pull Request identiche — stessa formulazione | 2 su 14 |
| Riesecuzione della stessa configurazione a un giorno di distanza | 2 esiti su 5 cambiati |

Ne discendono tre vincoli per il protocollo:

1. **Ogni configurazione va eseguita in più repliche**, e le differenze vanno
   interpretate rispetto all'ampiezza della variabilità. Una differenza di uno o due
   requisiti su nove non è, di per sé, un risultato.
2. **Il confronto con il riferimento non può basarsi sull'uguaglianza testuale**
   (§4), perché la formulazione varia quasi sempre.
3. **Vanno registrati con precisione** modello, versione datata, versione dei prompt
   e configurazione di ogni esecuzione, poiché sono le sole contromisure rimaste.

---

## 11. Le condizioni sperimentali

### 11.1 Le configurazioni progressive

Il sistema può essere eseguito in configurazioni via via più complete:

```text
solo Generation
      ↓
Generation + Assessment
      ↓
Generation + Assessment + Memoria
```

La configurazione di riferimento per la valutazione finale è quella completa.

### 11.2 La memoria è una condizione, non un miglioramento assunto

L'attivazione del recupero dalla memoria **rende il sistema dipendente
dall'ordine**: valutando la *n*-esima Pull Request, l'agente ha davanti i requisiti
prodotti dalle precedenti. Due esecuzioni sullo stesso materiale in ordine diverso
possono differire.

Ne conseguono tre condizioni operative: le Pull Request vanno elaborate in ordine
cronologico; la memoria va azzerata all'inizio di ogni esecuzione sperimentale; e
**memoria attiva e disattiva costituiscono due condizioni sperimentali distinte**,
da confrontare e riportare separatamente, non una configurazione migliore e una
peggiore.

Il recupero cambia infatti l'ingresso del valutatore su *ogni* Pull Request,
comprese quelle che con la memoria non hanno alcuna relazione, e può quindi
spostare esiti dove non dovrebbe.

### 11.3 La scelta del modello è una variabile

Il modello è configurabile separatamente per i due agenti (capitolo 4). Le
configurazioni provate mostrano differenze rilevanti, ma con una sola replica
ciascuna: il confronto va ripetuto secondo il vincolo del §10.

---

## 12. Tracciabilità dei risultati

Per ogni requisito valutato si conserva:

```text
pr_id                    unsupported_claims
generated_requirement    final_validity
gold_requirement         quality_score
semantic_match           human_notes
criterion_results
```

La traccia consente di ricostruire perché un requisito sia stato classificato in un
modo, quali criteri siano falliti, quali tipi di errore ricorrano e come siano state
calcolate le metriche aggregate.

Sul versante del sistema, ogni esecuzione produce già un rapporto che registra file
di input, configurazione, modelli nella versione datata, versione dei prompt,
consumo di token, costo stimato e — per ogni tentativo — il candidato prodotto, il
verdetto ricevuto e i requisiti storici mostrati.

---

## 13. Stato e limiti

**Il riferimento annotato non è ancora stato costruito.** È il passo che blocca
l'intera valutazione: fino ad allora, ogni giudizio di qualità sui risultati resta
un'impressione documentata e non una misura. Le osservazioni riportate nel capitolo
4 vanno lette in questa luce.

**Le prove finora condotte sono di messa a punto**, non di valutazione. Hanno
prodotto osservazioni qualitative sul comportamento del sistema e sull'effetto della
scelta del modello, ma non misure rispetto a un riferimento.

**Un'affermazione da verificare.** La formulazione originaria del piano riportava di
aver osservato un miglioramento qualitativo progressivo con l'introduzione
dell'agente valutatore e poi della memoria. L'affermazione precede l'esistenza del
recupero dalla memoria nel sistema: è quindi un'aspettativa di progetto, non un
risultato, e va verificata o rimossa. La prima misura disponibile mostra che il
meccanismo **funziona** — il duplicato viene individuato e nominato, e nessuna
relazione viene inventata sulle Pull Request non correlate — ma una singola
esecuzione, senza riferimento annotato, non sostiene alcuna affermazione sulla
qualità.

**Da consolidare prima della valutazione finale:** il numero di Pull Request
annotate; il numero di annotatori; la procedura di risoluzione dei disaccordi;
l'insieme definitivo dei criteri e delle condizioni necessarie; la scala del
confronto con il riferimento; la formula del punteggio; la misura dell'accordo fra
annotatori; l'eventuale uso di metriche automatiche supplementari; il formato del
file dei risultati.

---

## Riferimenti interni

- Decisione 3.1 — forma e qualità dei requisiti (capitolo 1).
- Decisione 3.2 — scelta del modello (capitolo 4).
- Decisione 3.5 — architettura multi-agente (capitolo 3).
- Decisione 3.6 — dataset ed evidenza (capitolo 2).
