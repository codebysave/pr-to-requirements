# Requisiti funzionali: forma, qualità e fedeltà all'evidenza

**Materiale per la tesi — bozza di capitolo**
Deriva da: `docs/design/decisions/01-quality-standard.md` (Decisione 3.1)
Progetto PR4Requirements · Università degli Studi di Milano-Bicocca

> **Nota sul copyright.** I criteri di qualità richiamati in questo capitolo sono
> una rielaborazione operativa dei principi di *Requirements Engineering*, non una
> riproduzione del testo normativo di ISO/IEC/IEEE 29148:2018, che è protetto da
> copyright. Lo standard è usato come riferimento concettuale; regole, scale ed
> esempi sono definizioni proprie del progetto.

---

## 1. Il problema

Un sistema che ricostruisce automaticamente requisiti funzionali deve rispondere a
una domanda preliminare: **che cosa si intende per requisito funzionale ben
formato**, e come si decide se un particolare enunciato lo sia.

La domanda non è retorica. I due agenti che compongono il sistema — quello che
scrive il requisito e quello che lo valuta — devono condividere la stessa
definizione operativa, altrimenti il ciclo di revisione non converge: il primo
produce ciò che il secondo respinge, indefinitamente. La stessa definizione deve
inoltre valere per l'annotazione manuale che costituisce il riferimento della
valutazione sperimentale, altrimenti sistema e riferimento misurano cose diverse.

Il problema si articola su **tre livelli distinti**, che vanno tenuti separati
perché un requisito può soddisfarne uno e violarne un altro:

| Livello | Domanda | Riferimento adottato |
|---|---|---|
| **Forma** | come è scritta la frase? | EARS (Mavin et al., 2009) |
| **Qualità** | quali proprietà possiede? | ISO/IEC/IEEE 29148:2018 |
| **Fedeltà** | dice solo ciò che l'evidenza sostiene? | definito dal progetto |

Il terzo livello è specifico di questo lavoro. Gli standard di *Requirements
Engineering* presuppongono che il requisito sia elicitato da un committente; qui
il requisito viene **ricostruito** da un testo preesistente e limitato, e la
misura in cui l'enunciato ecceda l'evidenza disponibile diventa il criterio
centrale.

---

## 2. La scelta dei riferimenti

### 2.1 Qualità: ISO/IEC/IEEE 29148:2018 e non IEEE 830

IEEE 830-1998 è ampiamente citato in letteratura ma è **ufficialmente superato**:
ISO/IEC/IEEE 29148 lo sostituisce, insieme a IEEE 1233 e IEEE 1362. L'edizione
corrente è la 29148:2018, riesaminata e confermata nel 2024.

Adottare IEEE 830 come riferimento primario in un lavoro del 2026 sarebbe una
scelta debole e facilmente contestabile. ISO 29148 offre inoltre una trattazione
più ricca degli **attributi del requisito** e della **tracciabilità**, elementi
centrali per un sistema che deve collegare ogni requisito prodotto alla Pull
Request da cui è stato ricostruito.

### 2.2 Forma: EARS come convenzione sintattica

I due riferimenti operano su livelli complementari. ISO 29148 definisce *quali
proprietà* debba avere un buon requisito, ma non fornisce una forma concreta da
produrre; EARS fornisce *template sintattici* precisi, ma non giudica la qualità
del contenuto.

Insieme coprono entrambi i livelli: EARS dà al generatore una struttura obiettivo
e al valutatore un controllo sintattico oggettivo, ISO 29148 fornisce i criteri
di qualità sostanziale.

Alla forma vincolata si aggiunge una motivazione tecnica: un modello linguistico
produce output più affidabile quando deve conformarsi a un pattern esplicito
anziché generare prosa libera.

### 2.3 Opzioni scartate

Le *user stories* della tradizione agile sono state considerate e scartate: la
forma «come *ruolo*, voglio *funzionalità*, così da *beneficio*» è troppo
informale per il compito, non impone verificabilità e non distingue i tipi di
requisito.

---

## 3. I criteri di qualità

Un requisito candidato viene valutato rispetto a dieci dimensioni, derivate dai
principi di ISO 29148 e tradotte in criteri applicabili al compito specifico.

**Correttezza.** Il comportamento espresso non deve alterare il significato
dell'evidenza disponibile.

**Chiarezza.** Vanno evitate formulazioni vaghe, termini soggettivi e riferimenti
non risolti. Espressioni come *quickly*, *appropriately*, *efficiently*, *if
necessary* non sono accettabili quando il contesto non ne definisce il
significato.

**Non ambiguità.** Il requisito deve ammettere una sola interpretazione
ragionevole. Sono difetti tipici: soggetto non chiaro, condizione di attivazione
incerta, oggetto dell'azione non determinabile.

**Singolarità.** Ogni requisito esprime **un solo obbligo principale**. La frase

> The system shall allow users to create, edit, and delete saved searches.

contiene tre comportamenti verificabili in modo indipendente e, quando l'evidenza
lo consente, va separata in tre requisiti distinti.

**Verificabilità.** Deve essere possibile determinare per osservazione o test se
il requisito è soddisfatto. *«The system shall provide a user-friendly search
interface»* non lo è, se *user-friendly* non viene definito in termini osservabili.

**Completezza relativa all'evidenza.** Il requisito contiene tutte le informazioni
funzionali ricostruibili dalla Pull Request — e **solo quelle**. La mancanza di
un'informazione nel testo non autorizza a inventarla per rendere il requisito più
dettagliato. È il punto in cui questo progetto si discosta dalla nozione
tradizionale di completezza, che è assoluta.

**Necessità.** Ogni elemento presente deve essere necessario a rappresentare il
comportamento richiesto.

**Fattibilità.** Il requisito non deve descrivere comportamenti manifestamente
impossibili. La valutazione è limitata dal contesto accessibile agli agenti, che
non vedono il codice.

**Consistenza.** Il requisito non deve contraddire inutilmente altri requisiti già
validati per lo stesso progetto. La verifica avviene attraverso il recupero dalla
memoria persistente (capitolo 5).

**Tracciabilità.** Ogni requisito è collegabile all'evidenza da cui è stato
ricostruito: Pull Request di origine, testo usato come input, versione del
requisito, esito della valutazione.

---

## 4. La distinzione fra comportamento e meccanismo

Il rischio principale di un sistema che ricostruisce requisiti dal testo di una
Pull Request è produrre requisiti che descrivono **la soluzione tecnica adottata**
invece del comportamento richiesto.

Data la Pull Request

> Replace the old authentication handler with the new OAuth middleware to fix
> authenticated users being redirected to the login page.

la formulazione

> The system shall use the new OAuth middleware.

descrive una scelta implementativa. Il comportamento funzionale sottostante è
invece

> The system shall allow authenticated users to access protected resources without
> being redirected to the login page.

La scelta della libreria resta una decisione dell'implementazione, che può
realizzare il requisito in molti modi diversi.

### 4.1 Criterio operativo

Il valutatore applica una domanda esplicita:

> «Il requisito descrive un comportamento che il sistema deve garantire, oppure sta
> prescrivendo una particolare implementazione?»

Nel secondo caso l'esito appropriato è **`REVISE`, non `REJECT`**. È una
distinzione importante per il funzionamento del sistema: si tratta di un difetto
di **formulazione**, non di **fondatezza**. La Pull Request può contenere un
requisito valido che il generatore ha semplicemente espresso al livello di
astrazione sbagliato; classificarla come non estraibile farebbe perdere un caso
legittimo.

### 4.2 Il *removal test*

Come verifica pratica si adotta un criterio meccanico: **si rimuove dal requisito
il nome della libreria, della funzione o del modulo.**

- Se la frase residua esprime ancora un comportamento, quel nome era dettaglio
  implementativo e va eliminato.
- Se non resta nulla di significativo, occorre distinguere due casi
  (§9.2): il cambiamento tecnico può essere esso stesso l'oggetto della Pull
  Request, e allora nominarlo è legittimo; oppure il testo si limitava a nominare
  un artefatto senza dire cosa faccia, e allora non c'è requisito da scrivere.

### 4.3 Osservabilità per librerie e framework

Il criterio di osservabilità va calibrato sul tipo di software analizzato. Molti
progetti presenti nei dataset di Pull Request — incluso quello usato nella prima
sperimentazione — sono **librerie o framework**, privi di un'interfaccia rivolta a
un utente finale.

In questi casi l'osservatore è chi utilizza l'interfaccia pubblica del componente,
e ciò che osserva sono valori restituiti, eccezioni sollevate ed effetti a
runtime. Richiedere un'osservabilità di tipo applicativo porterebbe a scartare
requisiti funzionali legittimi soltanto perché il software non ha un utente umano
davanti.

---

## 5. La forma dei requisiti

I requisiti sono normalizzati in lingua inglese e usano **shall** per esprimere
l'obbligo. La struttura generale è

> **[Soggetto] shall [comportamento richiesto] [oggetto] [condizione o vincolo].**

con soggetto esplicito, verbo principale in forma attiva, comportamento
osservabile, un solo obbligo principale, condizioni espresse soltanto se
supportate dall'evidenza.

### 5.1 I cinque pattern EARS

Il progetto adotta cinque pattern, il cui uso è **obbligatorio** per il generatore.
La non conformità sintattica comporta `REVISE` e non `REJECT`, per la stessa
ragione esposta al §4.1.

| Pattern | Forma | Quando si usa |
|---|---|---|
| **Ubiquitous** | `The system shall <response>.` | comportamento incondizionato |
| **Event-driven** | `When <trigger>, the system shall <response>.` | attivato da un evento |
| **State-driven** | `While <state>, the system shall <response>.` | valido durante uno stato |
| **Unwanted behaviour** | `If <undesired condition>, then the system shall <response>.` | risposta a una condizione indesiderata |
| **Optional feature** | `Where <feature is present>, the system shall <response>.` | in presenza di una configurazione |

Gli ultimi due pattern si usano soltanto quando lo stato o la condizione siano
chiaramente ricostruibili dall'evidenza.

### 5.2 Il quinto pattern e la sua origine empirica

Il sottoinsieme iniziale comprendeva **quattro** pattern. Le prime esecuzioni sui
dati reali hanno mostrato che il **cambiamento di un valore predefinito** — caso
ricorrente nelle Pull Request di configurazione — non era rappresentabile
correttamente da nessuno dei quattro: la forma *ubiquitous* afferma un
comportamento incondizionato, mentre un valore predefinito vale soltanto finché
non viene sovrascritto.

Il pattern *optional feature* copre esattamente questo caso:

> Where the retry policy has not been overridden, the system shall retry failed
> requests using exponential backoff.

Scrivere lo stesso requisito come *«The system shall use exponential backoff»*
sarebbe scorretto, perché afferma incondizionatamente ciò che è sovrascrivibile.

L'episodio è metodologicamente rilevante e viene riportato come tale: la
convenzione sintattica non è stata fissata a priori e poi imposta ai dati, ma
**estesa in risposta a un caso che i dati hanno mostrato non rappresentabile**.

---

## 6. La fedeltà all'evidenza

È il vincolo caratteristico di questo lavoro. Ogni elemento semantico introdotto
nel requisito — attore, azione, oggetto, evento, stato, condizione, vincolo,
risultato — deve essere supportato dal titolo e dal corpo della Pull Request.

**Esempio conforme.** Data la Pull Request

> Users currently receive no confirmation after successfully resetting their
> password. Add a confirmation notification.

il requisito

> The system shall notify the user after a successful password reset.

rappresenta il comportamento descritto senza aggiungere nulla.

**Esempio non conforme.** Dalla stessa evidenza,

> The system shall send an email to the user's registered email address within five
> seconds after a successful password reset.

introduce tre elementi non supportati: il canale (email), il destinatario
(indirizzo registrato) e il vincolo temporale (cinque secondi). Il requisito va
respinto **benché sia grammaticalmente corretto, non ambiguo e verificabile**: è
il caso che mostra perché i tre livelli del §1 vadano valutati separatamente.

---

## 7. Che cosa è un requisito funzionale

Il sistema considera requisito funzionale una dichiarazione che descrive un
comportamento, una capacità o una risposta che il sistema deve fornire o
garantire.

Non costituiscono il target: refactoring puramente tecnici, modifiche
infrastrutturali senza comportamento ricostruibile, aggiornamenti di dipendenze,
modifiche esclusivamente interne, requisiti puramente prestazionali.

### 7.1 Il test black-box come criterio operativo

La definizione precedente descrive che cosa sia un requisito funzionale ma non
consente di decidere i casi incerti. Si adotta quindi un criterio operativo:

> Un requisito è funzionale se è possibile immaginare un **test black-box** che lo
> verifichi: un test che fallisce prima della modifica e passa dopo, **senza
> ispezionare il codice sorgente**.

Il criterio discrimina casi che in astratto restano ambigui. Una modifica alla
tipizzazione statica non lo supera, perché il test dovrebbe esaminare le
annotazioni nel sorgente anziché il comportamento del sistema; lo stesso vale per
la correzione di un commento o per una riorganizzazione interna a comportamento
invariato.

**Il criterio non coincide con la distinzione funzionale/non funzionale di ISO/IEC
25010.** Un intervento di sicurezza è classificato da quella norma come
caratteristica di qualità, ma può esprimere un comportamento funzionale quando
descrive la risposta del sistema a un input:

> *«Il sistema non deve eseguire codice arbitrario proveniente da input non
> attendibile»* è verificabile black-box, ed è quindi un requisito funzionale.
> *«Il codice deve essere sicuro»* non lo è.

La distinzione è rilevante nella pratica: una quota consistente delle Pull Request
dei corpus utilizzati riguarda correzioni di sicurezza, che sarebbero state escluse
da un criterio più rigido.

### 7.2 Il requisito descrive il sistema, non la modifica

Un requisito non contiene riferimenti al processo di sviluppo. Espressioni come
*this Pull Request*, *the patch*, *the fix*, *the remediation* descrivono
l'intervento, non il comportamento.

Formulazioni come *«The system shall remediate the vulnerability»* vanno respinte:
non dicono che cosa il sistema faccia. Il requisito deve essere comprensibile a
chi non ha mai visto la Pull Request da cui è stato ricostruito.

---

## 8. Pull Request non estraibili

Non tutte le Pull Request devono produrre un requisito. Il criterio generale è:

> Una Pull Request è **estraibile** quando le informazioni in essa contenute sono
> sufficienti a identificare **in modo non ambiguo almeno un comportamento
> richiesto al sistema**.

La formulazione è volutamente indipendente dalla tipologia: ciò che conta non è se
si tratti di una funzionalità, di una correzione o di un intervento di sicurezza,
ma se il testo permetta di stabilire *che cosa il sistema deve fare*.

L'inciso «in modo non ambiguo» impedisce al generatore di colmare le lacune. **Il
solo fatto che una modifica sia avvenuta non è evidenza di un comportamento**: una
Pull Request che dichiara di aver cambiato qualcosa senza indicare che cosa il
sistema debba fare consente di *immaginare* un requisito, non di *identificarlo*.

Resta non estraibile anche la Pull Request formulata in termini ipotetici
(«questo *potrebbe* essere pericoloso»), perché non afferma che un comportamento
fosse effettivamente errato.

---

## 9. Due criteri di confine

I due paragrafi seguenti trattano i casi che, nelle esecuzioni reali, si sono
rivelati più difficili da decidere. Entrambi sono stati formulati **dopo** aver
osservato il comportamento del sistema su dati veri.

### 9.1 Il criterio riguarda il comportamento, non il meccanismo

L'ignoranza della tecnica con cui una correzione è stata realizzata **non rende la
Pull Request non estraibile**: il meccanismo appartiene all'implementazione, che il
requisito non deve descrivere.

Una Pull Request dichiara che input non attendibile permetteva il caricamento di
codice arbitrario, e che il problema è stato corretto. Non è dato sapere se la
correzione validi, rifiuti o limiti l'input; nominare uno di questi meccanismi
introdurrebbe informazione non supportata. È invece fondato il requisito espresso
al livello di astrazione che l'evidenza sostiene:

> The system shall prevent the execution of arbitrary code originating from
> untrusted user input.

Ne discende la domanda che il valutatore deve porsi:

> «Questo requisito afferma soltanto ciò che la Pull Request permette di dedurre?»

e **non**

> «La Pull Request descrive esattamente come il sistema deve comportarsi in ogni
> situazione?»

La seconda domanda è irrealistica e produrrebbe un tasso di fallimento
artificialmente alto. Quando l'evidenza sostiene un comportamento soltanto a
livello astratto, **il requisito corretto è quello astratto**: non una formulazione
più specifica, e non un fallimento.

*Evidenza empirica del criterio.* Nell'esecuzione del 30 agosto 2026 il valutatore
della fascia meno capace ha violato questo criterio su quattro Pull Request su
nove, rifiutandole perché il meccanismo della correzione non era dichiarato. Il
modello della fascia intermedia, con le stesse istruzioni, non lo ha violato su
nessuna. Il caso è discusso nel capitolo 4.

### 9.2 Il nome di un artefatto non fonda il suo comportamento

Alcune Pull Request non descrivono alcun comportamento: si limitano a dichiarare
che un artefatto dal significato convenzionalmente noto è stato aggiunto. Il caso
tipico ha questa forma:

```text
Titolo: feat(ui): tab component
Corpo:  Implements tab component
```

Il criterio adottato è:

> Il significato convenzionale di un artefatto nominato **non costituisce
> evidenza**. Quando, rimosso il nome, l'evidenza non stabilisce più alcun
> comportamento osservabile, la Pull Request non è estraibile.

Tre ragioni lo motivano.

**Il requisito che ne deriverebbe non riguarda questo sistema.** La frase *«The
system shall allow users to switch between multiple content panels»* è vera di
qualunque software dotato di schede: è la definizione del termine, non un
requisito ricostruito da quella Pull Request.

**È una condizione di validità della misura sperimentale.** Il progetto misura
quanta informazione sui requisiti sia ricostruibile dal testo. Se il modello colma
le lacune con la propria conoscenza del dominio, la misura riguarda quella
conoscenza e non il contenuto delle Pull Request.

**È il caso complementare del *removal test*.** Quello stabilisce che, rimossi i
nomi, se resta un comportamento allora quei nomi erano dettaglio implementativo.
Qui non resta nulla: il comportamento apparente proveniva interamente dal nome.

#### Che cosa la regola non esclude

Restano estraibili le Pull Request che nominano un artefatto **e** dichiarano che
cosa cambia per un osservatore.

| Evidenza | Esito | Ragione |
|---|---|---|
| *Implements toast component* | non estraibile | soltanto il nome |
| *Add `--log-level` to CLI arguments* | estraibile | nomina un'interfaccia osservabile |
| *The default retry policy is changed to exponential backoff* | estraibile | dichiara quale valore predefinito cambia e in che cosa |

La distinzione decisiva è fra **«questa cosa ora esiste»**, che non fonda alcun
comportamento, e **«questa impostazione ora vale X»**, che è un'affermazione sul
sistema, verificabile senza conoscere il funzionamento interno di X.

*Origine empirica del criterio.* Nel corpus `All-Hands-AI/OpenHands` cinque Pull
Request strutturalmente identiche — stesso modulo compilato allo stesso modo,
circa 530 caratteri, titolo nella forma `feat(ui): <nome> component` — hanno
ricevuto **quattro esiti diversi in una sola esecuzione**, e il valutatore ha
motivato due di essi con affermazioni fra loro incompatibili. L'incoerenza non era
un difetto di implementazione: era l'assenza di un criterio. Il sistema non poteva
essere coerente su una domanda a cui il progetto non aveva ancora risposto.

**Stato della regola.** La policy è **provvisoria** e sottoposta al confronto con
la tutor. L'argomento contrario è legittimo e va riportato: un analista che legga
«implements tab component» inferirebbe comunque che l'utente potrà cambiare
pannello, e nessuno considererebbe arbitraria quell'inferenza. La scelta è quindi
prudenziale, e privilegia la validità della misura rispetto alla copertura del
dataset.

---

## 10. Pull Request miste

Una Pull Request può contenere insieme un comportamento funzionale, un vincolo
prestazionale e dettagli implementativi:

> Add PDF report export and ensure generation completes within five seconds.

Il comportamento funzionale ricostruibile è *«The system shall allow users to
export reports in PDF format»*; il limite dei cinque secondi è un vincolo
prestazionale. Nella configurazione corrente il target è il **solo requisito
funzionale**, purché la componente funzionale sia isolabile senza introdurre
assunzioni.

La gestione sistematica delle informazioni non funzionali è una delle questioni
aperte (§13).

---

## 11. Traduzione nei due agenti

I criteri esposti sono recepiti nelle istruzioni dei due agenti, che condividono
un blocco di definizioni **identico parola per parola** — un vincolo verificato da
un test automatico. La ragione è diretta: quando le nozioni di «comportamento
richiesto» e di «evidenza» divergono fra generatore e valutatore, i due applicano
criteri diversi allo stesso requisito e il ciclo di revisione non converge.

**Il Requirement Generation Agent** identifica il comportamento ricostruibile,
sceglie il livello di astrazione che l'evidenza sostiene, lo esprime in uno dei
cinque pattern, e verifica prima di rispondere che ogni elemento risalga
all'evidenza. Può inoltre **dichiarare di non poter fondare alcun requisito**,
motivando la rinuncia.

**Il Requirement Assessment Agent** valuta su tre livelli: fondatezza
sull'evidenza, qualità locale rispetto ai criteri del §3, e coerenza con i
requisiti storici quando la memoria è attiva. La fedeltà all'evidenza è
**necessaria**: un requisito formalmente ineccepibile ma contenente affermazioni
non supportate viene respinto indipendentemente dagli altri criteri.

La procedura del valutatore è ordinata e il **primo passo che si applica decide**.
Non è un dettaglio realizzativo: senza un ordine, il modello sceglie
arbitrariamente quale criterio far prevalere quando più di uno è pertinente, e
l'esito diventa imprevedibile.

---

## 12. Separazione fra criteri interni e valutazione sperimentale

I criteri utilizzati internamente dall'Assessment Agent **non costituiscono il
riferimento della valutazione scientifica**. La valutazione del sistema deve
essere indipendente dal componente che produce l'assessment: usare quest'ultimo
per giudicare la qualità dell'output significherebbe far valutare il lavoro a una
sua parte.

Il riferimento viene quindi costruito mediante annotazione manuale separata,
secondo un codebook coerente con le definizioni di questo capitolo. Scale
numeriche, soglie e pesi non sono prescrizioni dello standard e vanno definiti e
validati sperimentalmente (capitolo 7).

---

## 13. Limiti e questioni aperte

Il capitolo definisce il quadro di riferimento; alcuni aspetti operativi restano
da consolidare sulla base dei dati.

**Da definire in fase sperimentale:** il codebook operativo per la classificazione
`EXTRACTABLE`/`NOT_EXTRACTABLE`; le scale di punteggio dei singoli criteri; le
eventuali soglie di accettazione; l'eventuale ponderazione differenziata dei
criteri; la tassonomia definitiva delle relazioni fra requisiti; il protocollo di
annotazione del riferimento.

**Sottoposto alla tutor:** il trattamento delle Pull Request miste e dei requisiti
non funzionali; la gestione delle Pull Request con contenuto testuale minimo; la
possibilità che una Pull Request generi più requisiti atomici; e il criterio del
§9.2 sul nome dell'artefatto.

**Verifica empirica dei pattern.** Se una quota significativa di requisiti
funzionali risultasse difficilmente rappresentabile attraverso i cinque pattern
adottati, la convenzione sintattica potrà essere estesa o rilassata, mantenendo
invariati i principi di qualità e di fedeltà. Una prima estensione è già avvenuta
in questo modo (§5.2), e costituisce il precedente metodologico.

---

## Riferimenti

- ISO/IEC/IEEE. (2018). *ISO/IEC/IEEE 29148:2018 — Systems and software engineering
  — Life cycle processes — Requirements engineering* (Ed. 2). [Sostituisce
  IEEE 830-1998, IEEE 1233-1998, IEEE 1362-1998.]
- Mavin, A., Wilkinson, P., Harwood, A., & Novak, M. (2009). Easy Approach to
  Requirements Syntax (EARS). *17th IEEE International Requirements Engineering
  Conference (RE'09)*, 317–322.
- ISO/IEC. (2011). *ISO/IEC 25010 — Systems and software engineering — Systems and
  software Quality Requirements and Evaluation (SQuaRE).*
- Washizaki, H., & Olszewska, J. I. (a cura di). (2024). *Guide to the Software
  Engineering Body of Knowledge (SWEBOK Guide), Version 4.0.* IEEE Computer Society.
- International Requirements Engineering Board (IREB). *CPRE Foundation Level
  Syllabus.*
- Wiegers, K., & Beatty, J. (2013). *Software Requirements* (3ª ed.). Microsoft Press.
- NASA. *NASA Systems Engineering Handbook*, Appendice C.
