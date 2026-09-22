# Legenda di unificazione dei requisiti

**Progetto:** PR-to-Requirements — costruzione del gold standard
**A che cosa serve:** le regole da applicare quando due annotazioni indipendenti
della stessa Pull Request, **entrambe valide**, devono diventare un unico
requisito di riferimento (*Ground Truth*).
**Riferimenti:** Decisione 3.1 (forma e qualità), Decisione 3.7 (piano di valutazione).
**Stato:** working document · **Ultimo aggiornamento:** _______________

---

## Principio generale

Non si sceglie fra le due annotazioni: si **ri-deriva dall'evidenza**.

Le due schede non sono due opzioni da votare, sono due **input** che delimitano
lo spazio delle letture valide. Il requisito unificato è quello che le regole
condivise producono avendo davanti entrambe.

Ne segue l'unico vincolo che tiene in piedi tutto il resto: **ogni unificazione
deve essere ri-percorribile**. Chi legge deve poter partire dalle due
annotazioni, applicare queste regole e ottenere lo stesso risultato.

---

## Precondizione

Le due annotazioni devono essere state prodotte **in modo indipendente** e
**prima** dell'unificazione.

L'unificazione è una fase separata e datata. Le schede originali **non si
modificano**: restano agli atti esattamente come sono state scritte, anche dove
l'unificazione conclude che una delle due eccedeva.

---

## Passo 1 — Classificare la divergenza

Prima di decidere qualsiasi cosa, si stabilisce **di che tipo** è la differenza
fra le due annotazioni.

| | Tipo | Che cosa cambia | Dove si risolve |
|---|---|---|---|
| **D0** | nessuna | le due annotazioni coincidono | il GT è quel requisito, si salta al Passo 5 |
| **D1** | forma | stesso comportamento, schema EARS o formulazione diversi | Passo 2 |
| **D2** | ampiezza | uno copre strettamente più dell'altro | Passo 3 |
| **D3** | contenuto | comportamenti **diversi** | non è un caso di unificazione |

**Sul D3.** Se le due annotazioni descrivono comportamenti diversi, non c'è nulla
da unificare: è un disaccordo vero. Si rilegge l'evidenza insieme; se il
disaccordo persiste, **si registra come tale e non si forza un Ground Truth**.
Un disaccordo registrato è un dato sull'evidenza; un Ground Truth forzato è un
riferimento inventato.

Una stessa Pull Request può presentare **D1 e D2 insieme**: si applicano
entrambi i passi, nell'ordine.

---

## Passo 2 — D1: la forma si deriva, non si negozia

### 2.1 Schema EARS — quale si sceglie, e perché

**La regola che li governa tutti.** Lo schema deve portare **esattamente le
condizioni che l'evidenza enuncia**: né una in più, né una in meno. Una
condizione in più restringe il requisito a casi che l'evidenza non pone; una in
meno afferma un comportamento più incondizionato di quanto l'evidenza sostenga.
Sono due infedeltà all'evidenza, in direzioni opposte.

Lo schema che ne esce è il Ground Truth **a prescindere da chi dei due lo aveva
scelto**: non vince un annotatore, decide la regola.

#### Primo taglio — c'è una condizione, e di che tipo?

| Che cosa dice l'evidenza | Schema |
|---|---|
| nessuna condizione: il comportamento vale sempre — o è un **divieto permanente** | **Ubiquitous** · `The system shall …` |
| un **evento puntuale** che fa scattare il comportamento | **Event-driven** · `When <trigger>, …` |
| uno **stato che dura**, e il comportamento vale per tutta la sua durata | **State-driven** · `While <state>, …` |
| una **condizione anomala o indesiderata**, e la reazione del sistema ad essa | **Unwanted behaviour** · `If <condition>, then …` |
| una **configurazione**: un valore predefinito, un'opzione, la presenza di un modulo | **Optional feature** · `Where <feature>, …` |

**Segnali testuali ricorrenti.** *«by default»*, *«unless overridden»*, *«if not
set»* → optional feature. *«when»*, *«after»*, *«upon»*, *«on <operazione>»* →
event-driven. *«while»*, *«during»*, *«as long as»* → state-driven. *«if»*,
*«invalid»*, *«fails»*, *«malicious»*, *«attacker»* riferiti alla **condizione**
(non alla conseguenza) → unwanted behaviour.

#### Le quattro confusioni che capitano davvero

**(a) Ubiquitous contro event-driven** — la divergenza più frequente fra noi due.

> **Test del trigger.** Si toglie la clausola `When …`. Se l'informazione che
> conteneva può essere riportata **sull'oggetto della risposta** senza perdere
> nulla, il trigger era una ripetizione: lo schema è **ubiquitous**.

*«When handling content provided by external sources, the system shall not
evaluate **it** as executable code»* — il trigger e l'oggetto della risposta sono
la stessa cosa. Spostandolo: *«The system shall not evaluate content provided by
external sources as executable code»*. Nulla è perduto → **ubiquitous**.

*«When a password reset completes successfully, the system shall notify the
user»* — il trigger (il reset) è un evento **diverso** dalla risposta
(notificare); toglierlo perde il momento → **event-driven**.

> **Corollario sui divieti.** Un requisito in forma `shall not` che vale in ogni
> istante è **ubiquitous** per natura: non esistendo un momento in cui non vale,
> non esiste un trigger che lo faccia scattare. Gran parte delle proprietà di
> sicurezza ricade qui.

**(b) Event-driven contro state-driven** — puntuale contro durevole.

`When` per ciò che **accade** in un istante; `While` per ciò in cui il sistema
**si trova** per un periodo, e per tutta la durata del quale il comportamento
deve valere.

> **Test della durata.** Chiedersi *«per quanto tempo?»*. Se la domanda ha senso,
> è uno stato; se la risposta è *«non dura, avviene»*, è un evento.

`While` ha una soglia più alta: la Decisione 3.1 §6.3 lo ammette **soltanto
quando lo stato è chiaramente ricostruibile dall'evidenza**. Uno stato dedotto
dal nome di un file, di un comando o di un modulo **non** è ricostruibile
dall'evidenza — è un'inferenza, e ricade sotto §9.2. In dubbio, `When`.

**(c) Event-driven contro unwanted behaviour** — normale contro anomalo.

La differenza non sta nella forma della condizione ma in **come l'evidenza la
presenta**: `If … then` richiede che la condizione sia essa stessa
**indesiderata** — un input non valido, un guasto, un tentativo di attacco.

> **L'errore più frequente:** mettere nella clausola `If` la **conseguenza**
> indesiderata invece della **condizione** indesiderata. Se ciò che non si vuole
> è l'esito che la risposta già vieta, allora la condizione è normale e lo
> schema è `When` — o ubiquitous.

Rileggere dati che il sistema stesso ha serializzato è un'operazione **normale**;
ciò che è indesiderato è che quella rilettura esegua codice, ed è esattamente
quello che la risposta vieta. Quindi `When … is read back, the system shall …
without executing …`, non `If … is read back, then …`.

**(d) Optional feature contro tutti gli altri** — la configurazione non è né un
evento né uno stato.

`Where` descrive un **fatto di assetto**: un'impostazione ha un certo valore, un
modulo è presente. Non accade in un istante (non è un evento) e non è una fase
del funzionamento (non è uno stato): vale finché qualcuno non lo cambia.

Caso chiuso una volta per tutte: **cambio di valore predefinito → optional
feature** (Dec. 3.1 §6.5) — `Where <impostazione> has not been overridden, the
system shall …`. In forma *ubiquitous* si afferma un comportamento
incondizionato mentre il default è sovrascrivibile; in forma `If … then` si
tratta come anomalia quella che è invece la configurazione normale.

#### Tie-break

Se dopo tutto questo due schemi restano entrambi difendibili:

1. vince quello la cui condizione è **scritta nel testo**, non dedotta;
2. a parità, quello che **non restringe** l'ambito del comportamento — una
   restrizione non sostenuta dall'evidenza è un elemento non fondato come
   qualunque altro;
3. la scelta si motiva in scheda.

### 2.2 Identificatori contro prosa

Regola, formulata come **obbligo** e non come permesso:

> Quando l'evidenza dichiara che il valore o il default di un'impostazione
> nominata è cambiato, e a quale valore, il requisito **deve** nominare
> quell'impostazione con il suo identificatore esatto.
> In ogni altro caso nessun nome di libreria, funzione, modulo o file può
> comparire nel requisito.

La ragione è la verificabilità: la prova di quel requisito è *«prendi il
sistema, non sovrascrivere nulla, guarda quale valore si applica»*, e non è
eseguibile se non si sa **quale** impostazione lasciare intatta. Per una
libreria l'osservatore è il chiamante dell'interfaccia pubblica, e
l'identificatore è precisamente ciò che il chiamante vede.

L'obbligo serve a togliere discrezionalità: è su questa libertà che due
annotatori divergono senza che nessuno dei due sbagli.

### 2.3 Nota — la convenzione vincola noi, non il sistema

Queste regole di forma disciplinano **come scriviamo il Ground Truth**. Non sono
un criterio con cui giudicare il sistema: il confronto con l'output del sistema
è **semantico**, e una riformulazione in prosa dello stesso identificatore non è
una divergenza.

---

## Passo 3 — D2: decisione motivata sull'ampiezza

È il passo in cui **decidiamo noi**, caso per caso, se un elemento vada tenuto o
tolto perché il requisito risulti il più aderente possibile all'evidenza. Non è
un automatismo, ed è per questo che **va motivato per iscritto ogni volta**.

### 3.1 La domanda da porsi

Si isola l'elemento **E** presente in una delle due annotazioni e assente
nell'altra — può essere un'aggiunta che *allarga* il comportamento o una
qualificazione che lo *restringe* — e si chiede:

> **Che cosa dice l'evidenza, esattamente, a proposito di E?**

Non *«E è plausibile?»*, non *«E è vero di questo tipo di sistema?»*: **che cosa
ne dice il testo della Pull Request**, che è l'unica evidenza disponibile.

### 3.2 Le uscite tipiche

| Situazione | Scelta | Criterio che la giustifica |
|---|---|---|
| l'evidenza **enuncia** E | si **tiene** E, e con esso l'annotazione che lo contiene | l'altra omette informazione che l'evidenza fornisce |
| l'evidenza **non enuncia** E — E viene dalla nostra conoscenza del dominio o dal nome di un file, di un modulo, di un comando | si **toglie** E | fedeltà all'evidenza · Dec. 3.1 §9.2: il nome di un artefatto non è evidenza del suo comportamento |
| **entrambe** le annotazioni aggiungono elementi non enunciati | si scende al **nucleo comune** | come sopra, applicato a tutte e due |
| il nucleo comune non è più verificabile | si **rianota** la Pull Request | un requisito non verificabile non è un riferimento |

La tabella elenca le uscite ricorrenti, non esaurisce i casi: se nessuna riga
descrive la situazione, si decide e si motiva.

### 3.3 Obbligo di motivazione

Per **ogni** requisito unificato in cui si è aggiunto o tolto qualcosa si scrive:

- **l'elemento** in discussione;
- **la scelta** fatta (tenuto / tolto / ridotto al nucleo comune);
- **la porzione di evidenza** su cui la scelta poggia — citata, non parafrasata;
- **una o due frasi** di motivazione.

Le motivazioni confluiscono nel **Registro delle scelte** in fondo a questo
documento, che diventa il sunto di come abbiamo interpretato l'evidenza — ed è
la parte che rende il gold standard difendibile davanti a un revisore.

---

## Passo 4 — Controllo: un solo obbligo

Unico controllo su ciò che è uscito dai passi precedenti:

> **Il requisito unificato esprime un solo obbligo?**

Se l'unificazione ha prodotto **due requisiti in uno** — tipicamente due
comportamenti uniti da *and* o da *or* — è un **errore**. Non deve accadere: un
Ground Truth con due obblighi viola l'atomicità, cioè uno dei criteri con cui
giudichiamo tutto il resto.

In quel caso si etichetta l'esito come **ERRORE DI UNIFICAZIONE**, si torna al
Passo 3 e si sceglie, invece di sommare.

---

## Passo 5 — Tracciabilità dell'unificazione

Per ogni Pull Request si conserva:

- le **due annotazioni originali**, verbatim;
- il **tipo di divergenza** (D0 / D1 / D2 / D3);
- la **regola applicata** (Passo 2) e/o la **motivazione** (Passo 3);
- il **requisito unificato**;
- la **data** dell'unificazione e chi l'ha eseguita.

Se un revisore non può ri-percorrere il ragionamento partendo dalle due schede,
il gold standard non è un riferimento: è un'opinione.

---

## Passo 6 — In questa fase non si misura nulla

L'unificazione produce il **Ground Truth e nient'altro**.

In questa fase **non** si assegna `MATCH` / `PARTIAL_MATCH` / `NO_MATCH`, **non**
si compila la rubrica di qualità, **non** si guarda l'output del sistema.

Il confronto avviene dopo, ed è **fra il Ground Truth e il requisito prodotto dal
sistema**. Tenere separate le due fasi è ciò che impedisce che la conoscenza di
quello che il sistema ha scritto influenzi il riferimento con cui lo giudichiamo.

> **Nota.** Se in seguito si riporta anche l'accordo fra noi due annotatori,
> quello si calcola sulle **annotazioni originali**, mai sul Ground Truth: sul
> Ground Truth farebbe 100% per costruzione e non dimostrerebbe nulla.

---

## Scheda di unificazione

<!-- Duplicare questo blocco per ogni Pull Request da unificare. -->

### PR #____ — `____________-____________-pr-____`

**Evidenza rilevante** *(la porzione su cui poggia la decisione, citata)*

```text

```

**Le due annotazioni**

| | Annotatore 1 | Annotatore 2 |
|---|---|---|
| Schema EARS | | |
| Requisito | | |

**Passo 1 — Tipo di divergenza:** ☐ D0 ☐ D1 ☐ D2 ☐ D3 *(anche più di uno)*

**Passo 2 — Forma** *(se D1)*

- Schema derivato dall'evidenza: ______________
- Regola applicata: ______________
- Identificatore obbligatorio in questo caso? ☐ sì ☐ no — perché: ______________

**Passo 3 — Ampiezza** *(se D2)*

- Elemento in discussione (E): ______________
- Che cosa ne dice l'evidenza: ______________
- Scelta: ☐ tenuto ☐ tolto ☐ nucleo comune ☐ rianotare
- Motivazione:

```text

```

**Passo 4 — Un solo obbligo?** ☐ sì ☐ no → **ERRORE DI UNIFICAZIONE**, torna al Passo 3

**Requisito unificato (Ground Truth)**

```text

```

**Passo 5 — Data e autori dell'unificazione:** ______________

---

## Registro delle scelte (sunto del Passo 3)

Da compilare via via, una riga per ogni elemento discusso.

| PR | Elemento (E) | Scelta | Motivazione sintetica |
|---|---|---|---|
| #____ | | | |
| #____ | | | |
| #____ | | | |
| #____ | | | |
| #____ | | | |
| #____ | | | |

**Come si legge questo registro.** Non è un elenco di eccezioni: è il modo in
cui abbiamo interpretato l'evidenza quando l'evidenza non decideva da sola.
Letto tutto insieme, mostra se le nostre decisioni sono state coerenti fra loro
— e se non lo sono state, è qui che si vede.
