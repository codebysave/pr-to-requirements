# L'architettura multi-agente e il ciclo di revisione

**Materiale per la tesi — bozza di capitolo**
Deriva da: `docs/design/decisions/05-Multi-agent-Architecture-with-runner.md` (Decisione 3.5)
Progetto PR4Requirements · Università degli Studi di Milano-Bicocca

---

## 1. Il problema

Ricostruire un requisito da una Pull Request e verificarne la qualità sono due
compiti diversi, e affidarli allo stesso componente porta a un difetto noto: un
modello linguistico interrogato sulla bontà del proprio output tende a
confermarlo. Huang et al. (2024) documentano il fenomeno, e la sperimentazione di
questo lavoro lo ha osservato direttamente (capitolo 4, §7.2).

L'architettura separa quindi i due ruoli in **due agenti distinti**:

- il **Requirement Generation Agent**, che produce un requisito funzionale
  candidato;
- il **Requirement Assessment Agent**, che lo valuta rispetto all'evidenza, ai
  criteri di qualità del capitolo 1 e, quando disponibile, alla memoria dei
  requisiti già validati.

La scelta architetturale centrale è però un'altra: **il sistema non è un insieme di
agenti autonomi che decidono liberamente il proprio comportamento, ma una macchina
a stati controllata**, in cui ogni passaggio, ogni diramazione e ogni condizione di
terminazione sono definiti esplicitamente al di fuori degli agenti.

La distinzione ha conseguenze pratiche. In un sistema ad agenti autonomi il flusso
dipende da decisioni prese dal modello a tempo di esecuzione, e non è né
riproducibile né osservabile in modo affidabile. Qui il modello decide soltanto
questioni **semantiche** — se un requisito sia fondato, come riformularlo — mentre
tutte le decisioni di **controllo** appartengono a componenti deterministiche.

---

## 2. Obiettivi

L'architettura deve garantire che:

- generazione e valutazione siano responsabilità distinte;
- ogni candidato sia valutato prima di poter essere persistito;
- il feedback del valutatore possa guidare una nuova generazione;
- il numero di iterazioni sia limitato e configurabile;
- un requisito non valido non venga accettato per il solo fatto di aver ottenuto un
  buon punteggio complessivo;
- gli effetti permanenti sulla memoria avvengano esclusivamente dopo `ACCEPT`;
- il comportamento sia riproducibile e osservabile;
- le decisioni di instradamento siano centralizzate;
- il sistema possa essere eseguito con memoria attiva o disattivata.

---

## 3. Il framework di orchestrazione

L'orchestrazione usa **LangGraph**. La scelta è motivata dalla natura del flusso,
che richiede uno stato condiviso, nodi con responsabilità diverse, instradamento
condizionale, un **ciclo** di revisione, condizioni esplicite di terminazione e
l'integrazione di componenti LLM con componenti deterministiche.

L'ultimo requisito esclude una semplice catena lineare: senza la possibilità di
tornare indietro a un passaggio precedente, il ciclo di revisione non è
esprimibile.

LangGraph è usato come **infrastruttura di controllo del flusso, non come
sostituto della logica applicativa**: i nodi delegano a componenti iniettati
dall'esterno, e l'instradamento resta in un modulo dedicato.

---

## 4. I due livelli di orchestrazione

Il sistema ha **due cicli annidati**, ed è utile tenerli distinti perché
appartengono a livelli architetturali diversi.

```text
Ciclo esterno — Pipeline Runner
   PR1 → PR2 → PR3 → … → PRn

Ciclo interno — LangGraph, per ciascuna PR
   Generazione → Recupero → Valutazione
                      │
                      └── REVISE → Generazione
```

### 4.1 Il Pipeline Runner

Il `PullRequestLoader` legge e valida un file contenente da una a *N* Pull Request,
mentre una singola esecuzione del grafo lavora sullo stato di **una sola Pull
Request**. Il **Pipeline Runner** colma questa distanza: riceve la collezione,
determina l'ordine di elaborazione, invoca il grafo separatamente per ciascuna Pull
Request, attende che raggiunga uno stato finale e solo allora passa alla successiva.

La responsabilità non è stata assegnata al Loader, che deve restare dedicato alla
lettura e alla validazione dell'input senza avviare workflow.

Il Runner **non è un agente** e non prende decisioni semantiche.

**L'ordine di elaborazione è cronologico**, dalla Pull Request più vecchia alla più
recente, quando è disponibile un riferimento temporale affidabile. La scelta
diventa sostanziale quando la memoria è attiva: una Pull Request successiva può
consultare requisiti validati da Pull Request precedenti, mentre una precedente non
deve poter recuperare requisiti provenienti dal futuro. Elaborare in ordine
arbitrario ricostruirebbe una storia mai avvenuta.

Prima di passare alla Pull Request successiva, quella corrente completa interamente
il proprio flusso, compresi eventuali tentativi di revisione e la persistenza.

### 4.2 Il grafo della singola Pull Request

```text
Pull Request
      │
      ▼
verifica di estraibilità ──── non estraibile ──→ FINE
      │
      ▼
Requirement Generation Agent
      │
      ├── rinuncia motivata ─────────┐
      ▼                              │
recupero dalla memoria               │
      │                              │
      ▼                              ▼
Requirement Assessment Agent ◄───────┘
      │
 ┌────┼─────────┬──────────────┬─────────────────┐
 ▼    ▼         ▼              ▼                 ▼
ACCEPT REVISE  REJECT   CONFIRM_NOT_EXTRACTABLE  limite raggiunto
 │      │        │              │                 │
 │      │        ▼              ▼                 ▼
 │      │      FINE           FINE       FAILED_VALIDATION
 │      │
 │      └──→ nuova generazione
 ▼
persistenza → FINE
```

---

## 5. I componenti

### 5.1 Agenti e componenti deterministiche

Non tutte le fasi sono modellate come agenti. Sono **deterministiche**: la verifica
di estraibilità, l'instradamento, il conteggio dei tentativi, il recupero dalla
memoria, la persistenza, il tracciamento e la gestione dello stato finale.

Sono **agenti**: la generazione del requisito e la sua valutazione — le sole due
attività che richiedono un giudizio semantico.

### 5.2 La verifica di estraibilità non è un terzo agente

La fase preliminare che stabilisce se una Pull Request contenga abbastanza
informazione è **una fase della pipeline, non un agente**, ed è implementata come
controllo deterministico: scarta soltanto le Pull Request prive di testo
sufficiente perché una qualsiasi valutazione sia possibile (corpo vuoto, oppure
titolo e corpo sotto una soglia di caratteri).

La scelta risponde a tre ragioni.

**Riproducibilità.** Un controllo sintattico dà sempre lo stesso esito; un modello
può cambiarlo fra un'esecuzione e l'altra.

**Informazione disponibile.** Il controllo decide *senza vedere il requisito*, che a
quello stadio non esiste ancora. Il giudizio semantico appartiene quindi a chi il
requisito ce l'ha davanti, cioè al valutatore.

**Costo.** Nullo, invece di una chiamata al modello per ogni Pull Request.

La conseguenza è che il giudizio sull'identificabilità di un comportamento si è
spostato **dentro** il ciclo: viene formulato dal generatore e verificato dal
valutatore (§7.4). La prima formulazione dell'architettura prevedeva un controllo
semantico preliminare; l'implementazione ha mostrato che collocarlo lì significava
chiedere a un modello di giudicare qualcosa che non poteva ancora vedere.

> **Nota metodologica.** La soglia di caratteri adottata è dichiarata nel codice e
> nella configurazione come **criterio di comodo da calibrare** sul riferimento
> annotato, non come valore fondato. È una delle questioni sottoposte alla tutor.

---

## 6. Lo stato condiviso

I nodi comunicano attraverso uno stato che viene aggiornato progressivamente:

```text
RequirementState
├── Pull Request        pr_id, repository, title, body
├── Estraibilità        esito, motivazione
├── Generazione         candidato corrente, numero del tentativo, eventuale rinuncia
├── Memoria             requisiti storici recuperati
├── Valutazione         decisione, feedback strutturato
├── Esito               stato finale, requisito accettato
└── Traccia             storico dei tentativi
```

Lo stato rappresenta il contesto della singola elaborazione. **Non viene passato
integralmente ai modelli**: ciascun agente riceve soltanto le informazioni
necessarie alla propria responsabilità. Il generatore, per esempio, non vede mai i
requisiti storici recuperati (§7.2).

---

## 7. Il ciclo

### 7.1 Prima generazione

Al primo passaggio il generatore riceve esclusivamente l'evidenza prevista
dall'esperimento — titolo e corpo — e produce un candidato secondo le regole del
capitolo 1. Non riceve alcun feedback, non essendocene ancora.

### 7.2 Il recupero avviene *dopo* la generazione

Quando la memoria è attiva, il recupero dei requisiti storici viene eseguito
**dopo** la generazione e **prima** della valutazione. La sequenza è intenzionale e
ha due motivazioni.

**Motivazione metodologica.** Il compito del generatore è ricostruire il requisito
espresso dalla Pull Request nel modo più fedele possibile. Se i requisiti storici
gli venissero forniti prima, il modello potrebbe cercare di differenziare
artificialmente il nuovo requisito da quelli esistenti, oppure incorporare dettagli
presenti nella memoria ma non supportati dalla Pull Request corrente. **La memoria
serve a valutare il requisito ricostruito, non ad alterarne preventivamente il
contenuto.**

**Motivazione tecnica.** Prima della generazione, la query disponibile sarebbe il
testo della Pull Request, che contiene prosa discorsiva, motivazioni, descrizioni
di difetti e dettagli implementativi — materiale non direttamente confrontabile con
enunciati normalizzati. Dopo la generazione, il candidato è già espresso come
requisito e si trova quindi **nello stesso spazio concettuale** dei requisiti in
memoria. Il confronto è più diretto.

**Il recupero è deterministico**, eseguito dal workflow e non lasciato alla
decisione del modello. Questo garantisce che ogni candidato sia valutato nelle
stesse condizioni, che il numero di accessi alla memoria sia controllabile, che il
comportamento sia riproducibile e che il sistema possa essere eseguito con memoria
attiva o disattivata in modo controllato.

Il recupero **si ripete dopo ogni nuova generazione**, perché un requisito riscritto
può risultare affine a requisiti storici diversi.

### 7.3 La valutazione

Il valutatore riceve il testo della Pull Request, il candidato corrente, i criteri
di valutazione, i requisiti storici se disponibili, e lo storico dei tentativi già
effettuati con i propri verdetti (§9).

La decisione **non si basa su un punteggio aggregato**. Alcuni criteri sono
**condizioni necessarie**: un requisito non può essere accettato se contiene
affermazioni non supportate dall'evidenza, se non è fedele al comportamento
ricostruibile, o se non è un requisito funzionale nello scope stabilito.

Chiarezza, atomicità e verificabilità contribuiscono alla valutazione ma **non
compensano** una violazione di fedeltà. Il principio è:

```text
buona forma  ≠  requisito valido
```

### 7.4 Le quattro decisioni

**`ACCEPT`** — il candidato soddisfa i criteri necessari; esce dal ciclo e passa
alla persistenza.

**`REVISE`** — i problemi rilevati sono correggibili con l'evidenza già
disponibile: informazioni non supportate rimovibili, formulazione ambigua,
requisito non atomico, livello di astrazione errato. Viene prodotto feedback
strutturato e il controllo torna al generatore, se il limite non è raggiunto.

**`REJECT`** — condizione terminale: un'ulteriore riscrittura non è utile, perché
l'evidenza non consente di formulare un requisito senza introdurre assunzioni
arbitrarie. Resta distinto da `NOT_EXTRACTABLE`: `REJECT` riguarda **un candidato
prodotto e non riparabile**, `NOT_EXTRACTABLE` constata che **dalla Pull Request
non si ricava alcun requisito**.

**`CONFIRM_NOT_EXTRACTABLE`** — il caso descritto di seguito.

### 7.5 La rinuncia motivata e la sua verifica

Il generatore può constatare di non poter ricostruire un requisito senza
inventarlo. La constatazione, però, **non chiude da sola l'elaborazione**:
mancherebbe qualsiasi controllo sull'auto-esclusione, e la rinuncia diventerebbe una
scorciatoia davanti ai casi difficili.

La rinuncia viene quindi sottoposta al valutatore, che dispone di una quarta
decisione:

```text
Generation Agent
   │
   ├── candidato ─────────→ Assessment ──→ ACCEPT / REVISE / REJECT
   │
   └── rinuncia motivata ─→ Assessment ──→ CONFIRM_NOT_EXTRACTABLE
                                        └─ REVISE (dissenso motivato)
```

Con `CONFIRM_NOT_EXTRACTABLE` il valutatore concorda. Con `REVISE` dissente,
indicando **quale comportamento ritiene identificabile e in quale parte
dell'evidenza**: il generatore riceve così un'informazione che nel normale ciclo di
revisione non otterrebbe mai, perché il feedback ordinario presuppone un candidato
da correggere.

La rinuncia **non attraversa il recupero dalla memoria**, che presuppone un
candidato con cui confrontare. Quando il valutatore è disattivato non esiste chi
possa verificarla, e l'elaborazione si chiude come `NOT_EXTRACTABLE`.

*Evidenza empirica.* Nella verifica sul corpus OpenHands, tre delle quattro
attivazioni del ciclo di revisione sono partite da una rinuncia ribaltata dal
valutatore. In un caso il generatore aveva rinunciato ritenendo il cambiamento un
refactoring interno; il valutatore ha distinto il meccanismo dal comportamento che
esso abilita, e il requisito prodotto al secondo tentativo è stato accettato.

---

## 8. Il feedback strutturato

Il feedback non è un commento libero. Ha una forma definita e direttamente
utilizzabile:

```json
{
  "decision": "REVISE",
  "issues": ["The requirement introduces a delivery channel not supported by the PR."],
  "unsupported_claims": ["The notification is sent by email"],
  "missing_information": [],
  "revision_instructions": [
    "Remove the unsupported reference to email.",
    "Preserve only the notification behaviour supported by the PR."
  ]
}
```

Al tentativo successivo il generatore riceve: l'evidenza originale, il requisito
precedente e il feedback strutturato. **Non riceve l'intera conversazione**: la
limitazione riduce la propagazione di informazione non necessaria e rende il ciclo
più controllabile.

Una regola vincola il valutatore a non proporre una formulazione sostitutiva, nemmeno
a titolo di esempio: scrivere il requisito è compito dell'altro agente, e una
formulazione suggerita di sfuggita rischia essa stessa di violare i criteri che il
valutatore applica.

---

## 9. Coerenza del valutatore con sé stesso

Il valutatore riceve lo **storico dei tentativi precedenti** con i propri verdetti.

La necessità è emersa dalle esecuzioni reali: senza storico, ogni chiamata partiva
da zero, e si osservava il valutatore chiedere una correzione, riceverla, e al giro
successivo chiederne una opposta. Il ciclo non convergeva.

La regola scritta nelle istruzioni è: **se il problema segnalato è stato risolto non
va ripetuto; se è rimasto, può essere riproposto.** Non è un divieto di insistere, è
un divieto di contraddirsi. È inoltre previsto che, se il candidato corrente è
sostanzialmente identico a uno già esaminato, il ciclo non stia convergendo e
l'esito appropriato sia `REJECT`.

*Effetto misurato.* Dopo l'introduzione dello storico, nessuna esecuzione ha più
prodotto `FAILED_VALIDATION` per esaurimento dei tentativi.

---

## 10. Il limite di tentativi e il suo superamento

Il ciclo non può proseguire indefinitamente. La configurazione adotta

```text
max_generation_attempts = 3
```

cioè una generazione iniziale e fino a due revisioni. Il valore contiene il costo
delle chiamate, la latenza e il rischio di cicli improduttivi; è configurabile e va
verificato empiricamente.

Se dopo l'ultimo tentativo il valutatore restituisce ancora `REVISE`, il requisito
**non viene accettato per esaurimento**. Lo stato finale è `FAILED_VALIDATION` e
nulla entra in memoria.

### 10.1 Nessuna promozione del «miglior candidato»

I candidati intermedi vengono conservati nei log per l'analisi, ma **quello con la
valutazione migliore non viene promosso automaticamente**:

```text
miglior candidato  ≠  requisito accettato
```

Un candidato può essere il migliore fra quelli prodotti e continuare a violare un
criterio necessario. Soltanto una decisione esplicita `ACCEPT` consente la
persistenza. È la traduzione operativa del principio del §7.3: la qualità relativa
non sostituisce le condizioni necessarie.

---

## 11. Instradamento centralizzato

Le transizioni fra i nodi non sono distribuite negli agenti né nei nodi stessi: sono
raccolte in un modulo dedicato, con funzioni del tipo `route_after_extractability`,
`route_after_generation`, `route_after_assessment`.

L'approccio evita che ogni nodo implementi autonomamente una porzione della macchina
a stati e rende possibile **testare le condizioni di instradamento senza invocare
alcun modello** — proprietà usata estensivamente nella verifica del sistema.

---

## 12. La persistenza avviene fuori dagli agenti

La scrittura nella memoria permanente non è responsabilità degli agenti:

```text
Assessment Agent → ACCEPT → Router → Controller → memoria
```

Né il generatore né il valutatore scrivono nel database. La politica garantisce che
`REVISE`, `REJECT` e `FAILED_VALIDATION` non contaminino la memoria, e che soltanto
requisiti esplicitamente validati entrino nel contesto storico delle elaborazioni
successive.

---

## 13. Gli stati finali

Ogni elaborazione termina con uno stato esplicito.

| Stato | Significato |
|---|---|
| `ACCEPTED` | è stato prodotto un requisito valido, persistito in memoria |
| `NOT_EXTRACTABLE` | dalla Pull Request non si ricava alcun requisito nello scope |
| `REJECTED` | è emersa una condizione terminale che rende inutile un'altra revisione |
| `FAILED_VALIDATION` | la Pull Request era estraibile, ma il ciclo non ha prodotto un candidato accettabile entro il limite |

`NOT_EXTRACTABLE` può derivare dal controllo preliminare, quando il testo è
insufficiente, oppure dal ciclo, quando il generatore rinuncia e il valutatore
conferma.

La distinzione fra i quattro stati è utile sia al funzionamento sia all'analisi
sperimentale: `FAILED_VALIDATION` segnala un ciclo che non converge, `REJECTED` un
caso in cui l'evidenza non basta, e i due fenomeni hanno cause diverse.

---

## 14. Tracciamento

Per ogni esecuzione viene conservato lo storico delle iterazioni: per ciascun
tentativo il candidato prodotto, il verdetto ricevuto, l'eventuale rinuncia e i
requisiti storici mostrati.

Lo storico serve ad analizzare l'effetto del feedback, misurare il numero medio di
revisioni, individuare errori ricorrenti e confrontare configurazioni. Appartiene
ai log dell'esecuzione, **non alla memoria persistente dei requisiti validati**: è
la traccia di un processo, non conoscenza consolidata.

---

## 15. Configurabilità

I parametri principali restano esterni alla logica dei nodi:

```text
assessment_enabled          max_generation_attempts
memory_enabled              min_evidence_characters
generation_model            max_memory_requirements
assessment_model
```

La configurabilità consente di sviluppare la pipeline in modo incrementale mentre i
componenti vengono realizzati; di eseguire le prove progressive previste dal piano
di valutazione (solo generazione, generazione e valutazione, workflow completo); e
di isolare il comportamento di un singolo componente durante la diagnosi.

Rende inoltre **il modello una variabile dell'esperimento** anziché un valore
cablato nel codice — condizione che ha permesso il confronto fra configurazioni
descritto nel capitolo 4.

---

## 16. Testabilità

L'architettura è progettata perché ogni livello sia verificabile separatamente. In
particolare, **la logica di instradamento e il ciclo sono testabili senza invocare
alcun modello**, sostituendo agli agenti componenti simulati dietro le stesse
interfacce.

Le proprietà verificate comprendono: l'instradamento dopo ciascuna fase; il
conteggio dei tentativi; la terminazione con `FAILED_VALIDATION`; la corretta
propagazione del feedback; l'esecuzione del recupero a ogni iterazione; **l'assenza
di persistenza per gli stati non accettati**; l'elaborazione di tutte le Pull
Request del file; il passaggio alla successiva soltanto dopo lo stato finale della
corrente; il rispetto dell'ordine cronologico quando la memoria è attiva.

Questa proprietà ha un valore che va oltre la comodità: consente di verificare il
comportamento del sistema **a costo nullo e in modo deterministico**, isolando i
difetti di orchestrazione da quelli di giudizio semantico, che sono di natura
completamente diversa.

---

## 17. Limiti e questioni aperte

**Da consolidare:** lo schema definitivo dell'output strutturato del valutatore; i
criteri esatti che distinguono `REVISE` da `REJECT`; la policy per le relazioni con
la memoria (`DUPLICATE`, `OVERLAPS`, `REFINES`, `SUPERSEDES`, `CONFLICTS`);
l'eventuale impiego di punteggi numerici come informazione diagnostica, senza
sostituire le condizioni necessarie; la conferma empirica del valore
`max_generation_attempts = 3`.

**Errori tecnici e revisioni semantiche vanno distinti.** Un fallimento della
chiamata al modello o una risposta malformata non sono un tentativo di revisione.
L'implementazione li separa già negli esiti, ma la loro gestione — in particolare i
tentativi automatici in caso di errore temporaneo — non è consolidata.

**Il recupero rende il sistema dipendente dall'ordine.** Con la memoria attiva, la
valutazione di una Pull Request dipende da quelle già elaborate; due esecuzioni
sullo stesso materiale in ordine diverso possono differire. È realistico, ma rende
`memory_enabled` attivo e disattivo **due condizioni sperimentali distinte** da
riportare separatamente (capitolo 7).

---

## Riferimenti

- Huang, J. et al. (2024). *Large Language Models Cannot Self-Correct Reasoning
  Yet.* ICLR 2024.
- Wang, Q. et al. (2025). *Cross-Refine: Improving Natural Language Explanation
  Generation by Learning in Tandem.* COLING 2025.
- Madaan, A. et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.*
  NeurIPS 2023.
- Shinn, N. et al. (2023). *Reflexion: Language Agents with Verbal Reinforcement
  Learning.* NeurIPS 2023.
