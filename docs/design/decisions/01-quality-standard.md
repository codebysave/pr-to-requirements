# Decisione 3.1 — Standard di qualità e forma dei requisiti

**Fase:** 3 — Design del sistema
**Stato:** Approvata
**Autori:** Andrea, Marco
**Data:** Agosto 2026

> **Nota sul copyright.** I criteri di qualità richiamati in questo documento
> costituiscono una rielaborazione operativa dei principi di Requirements Engineering,
> non una riproduzione del testo normativo di ISO/IEC/IEEE 29148:2018, che è protetto da
> copyright e non è liberamente riproducibile. Lo standard è usato come riferimento
> concettuale; le regole, le scale e gli esempi sono definizioni proprie del progetto.

---

## 1. Contesto

PR4Requirements ha l'obiettivo di ricostruire requisiti software funzionali a partire
dal contenuto testuale delle Pull Request e di valutarne automaticamente la qualità
tramite un **Requirement Assessment Agent**.

Perché il processo sia riproducibile e valutabile, è necessario definire in modo
esplicito:

- quale forma deve assumere un requisito generato;
- quali proprietà deve possedere per essere considerato di buona qualità;
- quali informazioni possono essere introdotte a partire dall'evidenza contenuta nella
  Pull Request;
- quando una Pull Request non contiene informazioni sufficienti per ricostruire un
  requisito funzionale.

Questa decisione costituisce quindi il riferimento comune per:

- il **Requirement Generation Agent**;
- il **Requirement Assessment Agent**;
- il codebook utilizzato per l'annotazione del dataset;
- la costruzione del gold standard;
- lo schema di persistenza dei requisiti;
- la successiva valutazione sperimentale.

---

## 2. Opzioni valutate e scelta

Il problema si articola su due livelli che vanno tenuti distinti: la **forma** del
requisito (la struttura sintattica) e la **qualità** del requisito (le proprietà che
deve possedere). A questi il nostro task aggiunge un terzo criterio, la **fedeltà
all'evidenza**, che nessuno standard generale fornisce.

Sono state considerate le principali alternative disponibili.

| Opzione | Livello coperto | Esito |
|---|---|---|
| **IEEE 830-1998** | Qualità | Scartato: ufficialmente superato e sostituito da ISO/IEC/IEEE 29148. |
| **ISO/IEC/IEEE 29148:2018** | Qualità | **Adottato** come riferimento normativo per la qualità. |
| **EARS (Mavin et al., 2009)** | Forma | **Adottato** (sottoinsieme) come convenzione sintattica di output. |
| **User Stories (agile)** | Forma | Scartato: troppo informale, non impone verificabilità né distinzione dei tipi di requisito. |

La scelta finale è un **approccio ibrido su tre livelli**:

1. **qualità del requisito**, basata su ISO/IEC/IEEE 29148:2018;
2. **forma sintattica**, normalizzata attraverso pattern derivati da EARS;
3. **fedeltà all'evidenza**, definita specificamente per il task PR-to-Requirements.

Questi livelli devono essere valutati separatamente. Un requisito può infatti essere
linguisticamente ben formato ma non supportato dalla Pull Request; allo stesso modo,
può rappresentare correttamente l'intento della PR ma essere ambiguo, non verificabile
o eccessivamente legato alla soluzione implementativa.

Questa decisione **raffina** l'orientamento preliminare del progetto (EARS + IEEE 830),
sostituendo IEEE 830 con il suo successore ufficiale ISO/IEC/IEEE 29148:2018.

### 2.1 Perché ISO/IEC/IEEE 29148:2018 e non IEEE 830

IEEE 830-1998 è ampiamente citato in letteratura, ma è **ufficialmente superato**:
ISO/IEC/IEEE 29148 lo sostituisce, insieme a IEEE 1233 e IEEE 1362. L'edizione corrente
dello standard è la 29148:2018 (edizione 2, riesaminata e confermata nel 2024). Adottare
IEEE 830 come riferimento primario in un lavoro del 2026 sarebbe una scelta debole e
facilmente contestabile. ISO 29148 offre inoltre una trattazione più ricca degli
attributi del requisito e della tracciabilità, elementi centrali per un sistema che deve
collegare ogni requisito alla PR di origine.

### 2.2 Perché EARS accanto a ISO 29148

I due riferimenti operano su livelli complementari. ISO 29148 definisce *quali proprietà*
deve avere un buon requisito, ma non fornisce una forma concreta da produrre; EARS
fornisce *template sintattici* precisi, ma non giudica la qualità del contenuto. Insieme
coprono entrambi i livelli: EARS dà al generatore una struttura target e al valutatore
un controllo sintattico oggettivo, mentre ISO 29148 fornisce i criteri di qualità
sostanziale. La forma vincolata di EARS è inoltre particolarmente adatta a un LLM, che
produce testo più affidabile quando deve conformarsi a un pattern esplicito.

---

## 3. Riferimento per la qualità: ISO/IEC/IEEE 29148:2018

Il riferimento normativo principale adottato dal progetto è:

> **ISO/IEC/IEEE 29148:2018 — Systems and software engineering — Life cycle processes —
> Requirements engineering**

Lo standard viene utilizzato come base concettuale per definire le caratteristiche che
un requisito deve possedere. Nel contesto di PR4Requirements, tali caratteristiche
vengono tradotte in un insieme di criteri operativi adatti al task di ricostruzione
automatica da Pull Request.

### 3.1 Criteri di qualità considerati

Un requisito candidato deve essere valutato almeno rispetto alle seguenti dimensioni.

#### Correttezza

Il requisito deve rappresentare correttamente il comportamento richiesto al sistema.
Nel nostro contesto la correttezza è strettamente collegata alla Pull Request di origine:
il comportamento espresso non deve alterare il significato dell'evidenza disponibile.

#### Chiarezza

Il requisito deve essere espresso in modo comprensibile e diretto. Devono essere evitati
formulazioni vaghe, termini soggettivi, riferimenti non risolti e costruzioni che
consentano interpretazioni sostanzialmente differenti. Espressioni come *quickly*,
*appropriately*, *efficiently*, *if necessary* non sono accettabili quando il loro
significato non è definito dal contesto.

#### Non ambiguità

Il requisito deve avere una sola interpretazione ragionevole rispetto al comportamento
richiesto. L'Assessment Agent deve identificare formulazioni nelle quali il soggetto non
è chiaro, la condizione di attivazione è incerta, l'oggetto dell'azione non è
determinabile, oppure più comportamenti possono essere interpretati in modi differenti.

#### Singolarità / atomicità

Ogni requisito deve esprimere **un singolo obbligo principale**. Ad esempio:

> The system shall allow users to create, edit, and delete saved searches.

contiene più comportamenti indipendenti e dovrebbe, quando l'evidenza lo consente, essere
separato in requisiti distinti:

> The system shall allow users to create saved searches.
>
> The system shall allow users to edit saved searches.
>
> The system shall allow users to delete saved searches.

#### Verificabilità

Deve essere possibile determinare, attraverso osservazione, test, analisi o altro metodo
appropriato, se il requisito è soddisfatto. Un requisito come:

> The system shall provide a user-friendly search interface.

non è sufficientemente verificabile se il concetto di *user-friendly* non viene definito
attraverso criteri osservabili. Un requisito come:

> The system shall allow users to search documents by title.

descrive invece un comportamento verificabile.

#### Completezza

Il requisito deve contenere tutte le informazioni necessarie per rappresentare il
comportamento ricostruibile dalla Pull Request. Nel nostro task la completezza è
**relativa all'evidenza disponibile**. Il sistema non deve aggiungere informazioni
mancanti semplicemente per rendere il requisito più dettagliato. La mancanza di
un'informazione nella Pull Request non autorizza il Generator a inventarla.

#### Necessità

Ogni elemento presente nel requisito deve essere necessario per rappresentare il
comportamento richiesto. Dettagli non necessari, ridondanti o non supportati devono
essere evitati.

#### Fattibilità

Il requisito non deve descrivere comportamenti manifestamente impossibili o incompatibili
con le informazioni disponibili. La valutazione della fattibilità è tuttavia limitata dal
contesto accessibile agli agenti.

#### Consistenza

Il requisito non deve entrare inutilmente in contraddizione con altri requisiti già
validati relativi allo stesso progetto. La consistenza globale viene valutata attraverso
il recupero di requisiti storici dalla memoria persistente.

#### Tracciabilità

Ogni requisito deve essere collegabile all'evidenza dalla quale è stato ricostruito. Nel
sistema, la tracciabilità include almeno: Pull Request di origine; titolo e body
utilizzati come input; eventuali porzioni di testo considerate come evidenza; versione
del requisito; stato della valutazione.

---

## 4. Distinzione tra WHAT e HOW

PR4Requirements deve produrre requisiti che descrivano principalmente **che cosa il
sistema deve fare**, evitando di trasformare automaticamente una soluzione implementativa
in un requisito.

Esempio di Pull Request:

> Replace the old authentication handler with the new OAuth middleware to fix
> authenticated users being redirected to the login page.

Una formulazione eccessivamente implementativa sarebbe:

> The system shall use the new OAuth middleware.

Questa frase descrive principalmente una scelta tecnica. Il comportamento funzionale
sottostante può invece essere ricostruito come:

> The system shall allow authenticated users to access protected resources without being
> redirected to the login page.

Il Requirement Assessment Agent deve quindi distinguere, quando possibile, tra
comportamento richiesto, problema osservato, soluzione tecnica adottata e dettaglio
implementativo. Dettagli tecnici possono essere mantenuti nel requisito soltanto quando
costituiscono essi stessi un vincolo richiesto e sono esplicitamente supportati
dall'evidenza.

### 4.1 Criterio operativo

La distinzione viene applicata attraverso una domanda esplicita:

> «Il requisito descrive un comportamento che il sistema deve garantire, oppure sta
> prescrivendo una particolare implementazione?»

Se vale il secondo caso, l'esito appropriato è `REVISE` con l'istruzione di riformulare
il requisito in termini comportamentali, senza imporre librerie, funzioni o tecniche non
richieste. È importante notare che si tratta di un **difetto di formulazione, non di
fondatezza**: la Pull Request può contenere un requisito valido che il Generation Agent
ha semplicemente espresso al livello di astrazione sbagliato. Classificarlo come non
estraibile, o rifiutarlo, farebbe perdere un caso legittimo.

Il flusso desiderato è quindi:

```text
Pull Request
      ↓
che cosa deve garantire il sistema?
      ↓
requisito funzionale astratto e verificabile
```

e non:

```text
Pull Request
      ↓
frase tecnica ripresa dalla descrizione
      ↓
requisito che prescrive un'implementazione
```

La scelta della libreria o della tecnica resta una decisione dell'implementazione, che
può realizzare il requisito in molti modi diversi.

Come verifica pratica, adottiamo un test semplice: si rimuove dal requisito il nome
della libreria, della funzione o del modulo. Se la frase residua esprime ancora il
comportamento richiesto, quel nome era un dettaglio implementativo e va eliminato; se
non resta nulla di significativo, il cambiamento tecnico costituiva esso stesso
l'oggetto della Pull Request (tipicamente la modifica di un'impostazione predefinita) e
può essere mantenuto.

### 4.2 Comportamento osservabile per librerie e framework

Il criterio di osservabilità va calibrato sul tipo di software analizzato. Molti
progetti presenti nei dataset di Pull Request — incluso quello utilizzato nella prima
sperimentazione — sono librerie o framework, privi di un'interfaccia rivolta a un utente
finale.

In questi casi il comportamento osservabile è quello percepibile da chi utilizza
l'interfaccia pubblica del componente: valori restituiti, eccezioni sollevate, effetti a
runtime, contratto dell'API. La verificabilità va giudicata a quel livello. Richiedere
un'osservabilità di tipo applicativo porterebbe a scartare requisiti funzionali
legittimi soltanto perché il software non ha un utente umano davanti.

---

## 5. Forma dei requisiti

I requisiti generati vengono normalizzati in lingua inglese e utilizzano **shall** per
rappresentare un obbligo. La struttura generale è:

> **[Subject] shall [required behavior] [object] [condition or constraint].**

Esempio:

> The system shall allow authenticated users to reset their password.

La convenzione adottata prevede: soggetto esplicito; uso di **shall**; verbo principale
in forma attiva; comportamento osservabile; un solo obbligo principale; condizioni
espresse soltanto quando supportate dall'evidenza; assenza di dettagli non ricostruibili
dalla Pull Request.

---

## 6. Pattern EARS adottati

EARS viene utilizzato come riferimento sintattico per rendere più uniforme la
formulazione dei requisiti. Non tutti i pattern EARS devono necessariamente essere
utilizzati: il sottoinsieme iniziale adottato comprende **quattro** pattern, quelli
maggiormente compatibili con i requisiti funzionali ricostruiti dalle Pull Request.

### 6.1 Ubiquitous requirement

Utilizzato quando il comportamento richiesto non dipende da una condizione particolare.

> The system shall `<response>`.

Esempio: *The system shall allow users to export reports in PDF format.*

### 6.2 Event-driven requirement

Utilizzato quando il comportamento viene attivato da un evento.

> When `<trigger>`, the system shall `<response>`.

Esempio: *When a password reset is completed successfully, the system shall notify the
user.*

### 6.3 State-driven requirement

Utilizzato quando un comportamento deve essere garantito mentre il sistema si trova in
uno specifico stato.

> While `<state>`, the system shall `<response>`.

Esempio: *While a user session is authenticated, the system shall allow access to
protected resources.*

Questo pattern viene utilizzato soltanto quando lo stato è chiaramente ricostruibile
dall'evidenza.

### 6.4 Unwanted behavior

Utilizzato quando la Pull Request descrive esplicitamente una condizione indesiderata e
il comportamento che il sistema deve adottare in tale situazione.

> If `<undesired condition>`, then the system shall `<response>`.

Esempio: *If authentication fails, then the system shall reject the login attempt.*

---

## 7. Grounding sulla Pull Request

La fedeltà all'evidenza costituisce un vincolo fondamentale di PR4Requirements. Ogni
elemento semantico introdotto nel requisito deve essere supportato direttamente o
ragionevolmente ricostruibile dal titolo e dal body della Pull Request utilizzati come
input.

Gli elementi da controllare comprendono almeno: attore, azione, oggetto, evento, stato,
condizione, vincolo, risultato atteso.

### 7.1 Esempio corretto

Pull Request:

> Users currently receive no confirmation after successfully resetting their password.
> Add a confirmation notification.

Requisito:

> The system shall notify the user after a successful password reset.

Il requisito rappresenta il comportamento descritto senza introdurre dettagli ulteriori.

### 7.2 Esempio non accettabile

Dalla stessa Pull Request:

> The system shall send an email to the user's registered email address within five
> seconds after a successful password reset.

Sono stati introdotti elementi non supportati: il canale email, l'indirizzo registrato,
il limite di cinque secondi. Il requisito deve quindi essere rifiutato anche se è
grammaticalmente corretto e verificabile.

---

## 8. Requisiti funzionali

Il target primario di PR4Requirements è costituito dai **requisiti funzionali**. Nel
progetto consideriamo requisito funzionale una dichiarazione che descrive un
comportamento, una capacità o una risposta che il sistema deve fornire o garantire.

Esempi:

> The system shall allow users to delete saved searches.
>
> The system shall notify the user when report generation is completed.
>
> When authentication fails, the system shall reject the login attempt.
>
> The system shall allow administrators to disable a user account.

Non costituiscono invece il target principale del sistema: refactoring puramente tecnici;
modifiche infrastrutturali prive di comportamento funzionale ricostruibile; aggiornamenti
di dipendenze; modifiche esclusivamente interne; requisiti esclusivamente prestazionali;
quality constraints privi di un comportamento funzionale target.

---

## 9. PR non estraibili

Non tutte le Pull Request devono produrre obbligatoriamente un requisito. Il criterio
generale adottato dal progetto è il seguente:

> Una Pull Request è considerata **estraibile** quando le informazioni in essa contenute
> sono sufficienti a identificare **in modo non ambiguo almeno un comportamento richiesto
> al sistema**.

La formulazione è volutamente indipendente dalla tipologia della Pull Request: ciò che
conta non è se si tratti di una funzionalità, di una correzione o di un intervento di
sicurezza, ma se il testo permetta di stabilire *che cosa il sistema deve fare*.

Applicato ai casi ricorrenti:

- una Pull Request di funzionalità è estraibile se descrive il comportamento richiesto;
- una correzione di difetto è estraibile se descrive quale comportamento deve essere
  corretto;
- un intervento di sicurezza è estraibile se descrive come il sistema deve comportarsi
  **dopo** la correzione, non soltanto quale vulnerabilità è stata individuata;
- una descrizione troppo vaga per determinare un comportamento specifico non è
  estraibile.

L'inciso «in modo non ambiguo» è essenziale: impedisce al Generation Agent di colmare le
lacune inventando un requisito che l'evidenza non sostiene. L'esistenza di una modifica
non costituisce di per sé evidenza di un comportamento: una Pull Request che dichiara
soltanto di aver cambiato qualcosa, senza indicare che cosa il sistema debba fare, non
consente di *identificare* un requisito, ma solo di *immaginarlo*.

### 9.1 Il criterio riguarda il comportamento, non il meccanismo

Il criterio va applicato al **comportamento richiesto**, non alla tecnica con cui è
stato realizzato. L'ignoranza del meccanismo non rende una Pull Request non estraibile:
il meccanismo appartiene all'implementazione, che il requisito non deve descrivere
(§4).

Esempio. Una Pull Request dichiara che input non attendibile permetteva il caricamento
di codice arbitrario, e che il problema è stato corretto. Non è dato sapere se la
correzione validi, rifiuti o limiti l'input: un requisito che nomini uno di questi
meccanismi introdurrebbe informazione non supportata. È invece fondato il requisito
espresso al livello di astrazione che l'evidenza sostiene:

> The system shall prevent the execution of arbitrary code originating from untrusted
> user input.

Ne discende un criterio operativo per il Requirement Assessment Agent, che deve
chiedersi:

> «Questo requisito afferma soltanto ciò che la Pull Request permette di dedurre?»

e **non**:

> «La Pull Request descrive esattamente come il sistema deve comportarsi in ogni
> situazione?»

La seconda domanda è irrealistica — una Pull Request non contiene quasi mai tutti i
dettagli — e renderebbe l'esito `FAILED_VALIDATION` eccessivamente frequente. Quando
l'evidenza sostiene un comportamento soltanto a un livello astratto, il requisito
corretto è quello astratto: non una formulazione più specifica, e non un fallimento.

Resta invece non estraibile la Pull Request formulata in termini ipotetici («questo
*potrebbe* essere pericoloso», «*se* il contenuto provenisse dall'esterno»), perché non
afferma che un comportamento fosse effettivamente errato.

Il rischio da evitare è quindi:

```text
problema segnalato
      ↓
il modello immagina quale dovrebbe essere il comportamento
      ↓
requisito inventato
```

Esempio non estraibile:

> Refactor the parser to simplify the internal class hierarchy.

Se dalla descrizione non emerge alcun cambiamento funzionale osservabile, il sistema non
deve inventarne uno. Output atteso: `NOT_EXTRACTABLE`.

La possibilità di non generare un requisito è necessaria per evitare che il modello
trasformi automaticamente ogni modifica software in una nuova funzione del sistema.

Il criterio è applicato dalla verifica preliminare di estraibilità (Decisione 3.5, §6).
Quando la stessa insufficienza di evidenza emerge soltanto durante la valutazione, la
decisione appropriata è `REJECT` e non `REVISE`: nessuna riscrittura può fondare un
requisito su un'evidenza che non lo contiene.

---

## 10. Pull Request miste

Una Pull Request può contenere contemporaneamente un comportamento funzionale, un
requisito di performance, un vincolo di sicurezza e dettagli implementativi.

Esempio:

> Add PDF report export and ensure generation completes within five seconds.

Il comportamento funzionale ricostruibile è:

> The system shall allow users to export reports in PDF format.

Il limite temporale *generation completes within five seconds* costituisce invece un
vincolo prestazionale. Nella prima versione del progetto, il target primario rimane il
requisito funzionale. La gestione sistematica delle informazioni non funzionali deve
essere definita separatamente nel codebook di annotazione.

---

## 11. Requirement Generation Agent

Il Requirement Generation Agent deve produrre un requisito candidato rispettando le
seguenti regole:

1. identificare il comportamento funzionale espresso o ricostruibile dalla PR;
2. evitare di riassumere semplicemente l'implementazione;
3. produrre un requisito in lingua inglese;
4. utilizzare **shall**;
5. utilizzare, quando applicabile, uno dei pattern EARS adottati;
6. esprimere un solo obbligo principale;
7. mantenere il corretto livello di astrazione;
8. non introdurre informazioni non supportate;
9. preservare tutte le informazioni funzionali necessarie presenti nell'evidenza;
10. restituire `NOT_EXTRACTABLE` quando non è possibile ricostruire un requisito
    funzionale sufficientemente fondato.

---

## 12. Requirement Assessment Agent

Il Requirement Assessment Agent valuta il requisito candidato su tre livelli.

### 12.1 Gate di estraibilità

Prima della valutazione qualitativa deve essere verificato che: la Pull Request contenga
un comportamento funzionale ricostruibile; l'evidenza disponibile sia sufficiente; il
requisito prodotto rappresenti effettivamente tale comportamento. Se queste condizioni
non sono soddisfatte, il requisito non può essere accettato.

### 12.2 Qualità locale

Il requisito viene valutato rispetto a criteri quali: fidelity; functional relevance;
correctness; clarity; unambiguity; singularity / atomicity; verifiability; completeness
relative to evidence; necessity; correct abstraction; implementation independence.

La **fidelity all'evidenza** costituisce un requisito necessario per l'accettazione: un
requisito formalmente corretto ma contenente informazioni non supportate deve essere
rifiutato indipendentemente dagli altri punteggi.

### 12.3 Coerenza globale

Quando la memoria persistente è disponibile, il requisito viene confrontato con i
requisiti storici semanticamente rilevanti. Il sistema deve poter identificare almeno le
seguenti relazioni: `NEW`, `DUPLICATE`, `OVERLAPS`, `REFINES`, `SUPERSEDES`, `CONFLICTS`.

Questa fase consente di distinguere la qualità del singolo requisito dalla coerenza del
corpus complessivo.

---

## 13. Output della valutazione

L'Assessment Agent deve produrre un risultato strutturato e verificabile. La struttura
definitiva viene definita nella decisione dedicata alla rubrica di valutazione, ma deve
poter rappresentare almeno: esito dell'estraibilità; conformità alla forma prevista;
valutazione dei criteri di qualità; affermazioni non supportate; informazioni funzionali
mancanti; eventuali problemi di astrazione; relazioni con requisiti precedenti; istruzioni
di revisione; decisione finale di accettazione o rifiuto.

Il feedback deve essere sufficientemente specifico da poter essere utilizzato dal
Requirement Generation Agent in un successivo tentativo di generazione.

---

## 14. Persistenza e tracciabilità

Ogni requisito candidato o validato deve mantenere il collegamento con la propria origine.
Lo schema di persistenza deve poter rappresentare almeno: identificatore del requisito;
statement; Pull Request di origine; evidenza utilizzata; pattern sintattico; stato del
requisito; risultato dell'assessment; versione; eventuali relazioni con altri requisiti.

Gli output non validati non devono essere trattati come requisiti storici affidabili. La
politica di persistenza e aggiornamento della memoria viene definita nella relativa
decisione architetturale.

---

## 15. Valutazione sperimentale

I criteri utilizzati internamente dal Requirement Assessment Agent non costituiscono
automaticamente il gold standard della tesi. La valutazione scientifica del sistema deve
essere indipendente dal componente che produce l'assessment (regola anti-circolarità).

Il gold standard viene quindi costruito mediante annotazione separata, utilizzando un
codebook coerente con le definizioni adottate in questa decisione. Le eventuali scale
numeriche, soglie di accettazione, combinazioni dei punteggi e pesi dei singoli criteri
non sono considerate prescrizioni dello standard ISO e devono essere definite e validate
sperimentalmente.

---

## 16. Conseguenze della decisione

L'adozione di questa convenzione comporta che:

- Generator e Assessment Agent condividano la stessa definizione operativa di requisito
  funzionale;
- i requisiti abbiano una forma sufficientemente uniforme;
- ogni requisito sia tracciabile alla Pull Request di origine;
- la qualità linguistica non sia sufficiente senza fidelity all'evidenza;
- il sistema possa rifiutare PR non estraibili;
- i dettagli implementativi non vengano automaticamente trasformati in requisiti;
- la memoria persistente venga utilizzata per la coerenza cross-PR e non per determinare
  da sola la correttezza locale del requisito;
- la rubrica dell'Assessment Agent rimanga distinta dal protocollo di valutazione
  sperimentale.

---

## 17. Punti aperti da definire in fase sperimentale

La presente decisione definisce il framework iniziale di riferimento per la forma e la
qualità dei requisiti. Alcuni aspetti operativi verranno definiti e calibrati
progressivamente durante la fase sperimentale, sulla base dei risultati ottenuti sui dati
reali e del confronto con le annotazioni umane. In particolare, restano da determinare:

- il **codebook operativo** per la classificazione `EXTRACTABLE` / `NOT_EXTRACTABLE`;
- la **rubrica dettagliata del Requirement Assessment Agent**;
- le **scale di scoring** utilizzate per i singoli criteri di qualità;
- le eventuali **soglie di accettazione o rifiuto** del requisito candidato;
- l'eventuale utilizzo di **pesi differenti** per i criteri di valutazione;
- la **tassonomia definitiva delle relazioni** tra requisito candidato e requisiti già
  presenti nella memoria;
- il **formato strutturato dell'output** prodotto dai due agenti;
- il **protocollo di annotazione** per la costruzione e la validazione del gold standard.

Anche l'adeguatezza dei pattern EARS adottati dovrà essere verificata empiricamente. Se
durante i test una quota significativa di requisiti funzionali risultasse difficilmente
rappresentabile attraverso il sottoinsieme selezionato, la convenzione sintattica potrà
essere estesa o rilassata, mantenendo invariati i principi di qualità e grounding
definiti in questa decisione.

---

## 18. Riferimenti

- ISO/IEC/IEEE. (2018). *ISO/IEC/IEEE 29148:2018 — Systems and software engineering —
  Life cycle processes — Requirements engineering* (Edition 2). International
  Organization for Standardization. [Sostituisce IEEE 830-1998, IEEE 1233-1998,
  IEEE 1362-1998.]
- Mavin, A., Wilkinson, P., Harwood, A., & Novak, M. (2009). Easy Approach to
  Requirements Syntax (EARS). *17th IEEE International Requirements Engineering
  Conference (RE'09)*, 317–322.
- Washizaki, H., & Olszewska, J. I. (Eds.). (2024). *Guide to the Software Engineering
  Body of Knowledge (SWEBOK Guide), Version 4.0*. IEEE Computer Society. [Area:
  Software Requirements.]
- International Requirements Engineering Board (IREB). *CPRE Foundation Level Syllabus*.
- Wiegers, K., & Beatty, J. (2013). *Software Requirements* (3rd ed.). Microsoft Press.
- NASA. *NASA Systems Engineering Handbook* (Appendix C — How to Write a Good Requirement;
  Section 5.3 — Product Verification). [Guida operativa di supporto.]
- IEEE. (1998). *IEEE 830-1998 — Recommended Practice for Software Requirements
  Specifications*. [Predecessore storico, superato da ISO/IEC/IEEE 29148.]
