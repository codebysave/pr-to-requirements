# Decisione 3.2 — Scelta dell'LLM

**Fase:** 3 — Design del sistema
**Stato:** Approvata (configurazione iniziale; parametri sperimentali da calibrare)
**Autori:** Andrea, Marco
**Data:** Agosto 2026

---

## 1. Contesto

Il sistema PR4Requirements si basa su due agenti — Requirement Generation Agent e
Requirement Assessment Agent — entrambi realizzati mediante Large Language Models. La
scelta del modello (o dei modelli) da utilizzare condiziona la qualità dei requisiti
generati, il costo del progetto, la riproducibilità degli esperimenti e la struttura
del codice.

Con questa decisione definiamo quale modello adottare nella fase di sviluppo, come gestire
la scelta del modello nella fase sperimentale, e quali vincoli di riproducibilità
rispettare. Non fissiamo in modo definitivo i parametri di generazione, che vanno calibrati
empiricamente.

---

## 2. Vincoli e criteri

La scelta è guidata da quattro criteri.

**Costo.** Durante lo sviluppo eseguiamo la pipeline molte volte al giorno per il
debugging; un modello costoso in questa fase produrrebbe una spesa elevata senza valore
aggiunto, perché la maggior parte delle esecuzioni serve solo a verificare che il codice
funzioni. Contenere il costo delle chiamate in fase di sviluppo è quindi un criterio di
progetto, distinto dalla scelta del modello per gli esperimenti finali.

**Qualità dell'output.** Il Generation Agent deve produrre requisiti ben formati e
fedeli all'evidenza; l'Assessment Agent deve applicare una rubrica di valutazione. La
qualità del modello incide direttamente sul risultato.

**Riproducibilità.** Un esperimento è scientificamente valido solo se altri (o noi stessi
in un secondo momento) possono ripeterlo e ottenere gli stessi risultati. Con gli LLM
questo è meno ovvio che con un programma tradizionale: lo stesso modello, ricevendo la
stessa identica richiesta, può produrre risposte diverse. Questa variabilità dipende da due
fattori. Il primo è la *configurazione*: parametri come la temperatura regolano quanto le
risposte del modello sono deterministiche o variabili. Il secondo è la *versione del
modello*: i fornitori aggiornano i modelli nel tempo, e la stessa richiesta a distanza di
mesi può dare risultati differenti. Un lavoro della tutor (Donato et al., 2025b) documenta
proprio questa variabilità degli output al variare della configurazione e tra repliche
della stessa richiesta. La conseguenza pratica è che, per ogni esperimento, dobbiamo
registrare con precisione quale modello, quale versione e quali parametri abbiamo usato,
ed eseguire ogni configurazione più volte per misurare quanto i risultati oscillano.

**Flessibilità architetturale.** Il sistema non deve essere legato a un singolo modello
o fornitore: cambiare modello deve essere una questione di configurazione, non di
riscrittura del codice.

---

## 3. Opzioni valutate

| Opzione | Descrizione | Vantaggi | Svantaggi |
|---|---|---|---|
| **A — Modelli proprietari via API** | Claude, GPT, Gemini | Qualità elevata, nessuna infrastruttura | Costo; riproducibilità limitata dagli aggiornamenti lato fornitore |
| **B — Modelli open source in locale** | Llama, Qwen, Mistral | Gratuiti, riproducibili con versione fissa | Richiedono hardware adeguato (GPU); qualità un gradino sotto i migliori proprietari |
| **C — Modelli open source via API di terzi** | Together, Groq, OpenRouter | Riproducibili, senza hardware, costo contenuto | Dipendenza da un intermediario |

---

## 4. Decisione

**4.1 Fornitore e modello iniziale.** Nella fase di sviluppo adottiamo l'opzione A con un
modello proprietario economico della famiglia Claude di Anthropic (fascia *Haiku*),
utilizzato per entrambi gli agenti. Questo ci permette di sviluppare e testare la pipeline
contenendo i costi.

**4.2 Modello configurabile per agente.** Progettiamo il sistema in modo che il modello
possa essere selezionato **separatamente per ciascun agente** tramite configurazione. Nella
fase di sviluppo usiamo lo stesso modello economico per entrambi gli agenti; nella fase
sperimentale potremo testare combinazioni diverse (stesso modello per entrambi,
modello più capace per entrambi, oppure combinazioni miste), rendendo la scelta del modello
una variabile dell'esperimento anziché un valore fisso cablato nel codice.

**4.3 Astrazione nel codice.** Mediamo l'accesso all'LLM tramite un livello di astrazione che
disaccoppia la logica degli agenti dal fornitore specifico. Cambiare modello o fornitore
non deve richiedere modifiche agli agenti, ma solo alla configurazione. Con questa scelta
manteniamo aperta la possibilità di introdurre modelli open source (opzioni B o C) in una
fase successiva.

**4.4 Parametri di generazione fissati e versionati.** Per ogni esecuzione sperimentale
fissiamo e riportiamo: nome ed esatta **versione** del modello (es. l'identificativo
completo con data), temperatura, top-p, e ogni altro parametro rilevante. Eseguiamo la
stessa configurazione in più repliche per controllare il non-determinismo.

---

## 5. Motivazione

**Perché un modello economico in sviluppo.** Durante la costruzione della pipeline la
maggior parte delle chiamate serve al debugging e non alla valutazione della qualità.
Usare un modello economico in questa fase ci permette di ridurre i costi senza penalizzare
il lavoro; la qualità del modello diventa rilevante solo nella fase sperimentale finale.

**Perché il modello configurabile per agente e non fisso.** I due agenti hanno compiti
diversi. Il Generation Agent produce testo strutturato; l'Assessment Agent applica una
rubrica di valutazione. La letteratura sul pattern generator–critic (Wang et al., 2025)
indica che il valore della revisione dipende dall'avere un *critic distinto* che
apporti un vantaggio informativo, e Huang et al. (2024) mostrano che la semplice
auto-revisione senza nuova informazione può non migliorare o addirittura peggiorare
l'output. Questa distinzione è di **ruolo e di contesto informativo**, non necessariamente
di modello: la letteratura non prescrive l'uso di modelli diversi per i due agenti. Rendiamo
però il modello configurabile per agente per poter *verificare sperimentalmente* se e
quanto la scelta del modello per ciascun ruolo influisca sulla qualità, trasformando una
possibile variabile confondente in un fattore controllato e misurabile.

**Perché l'astrazione dal fornitore.** Come per la sorgente dei dati, disaccoppiamo il
codice dal modello specifico per rendere il sistema robusto ai cambiamenti (nuove versioni,
cambio di fornitore, introduzione di modelli open source) e per poter eseguire in fase
sperimentale confronti tra modelli senza riscrivere gli agenti.

**Perché fissare e versionare i parametri.** È un requisito di riproducibilità
scientifica, motivato direttamente da un lavoro della tutor (Donato et al., 2025b) che
documenta la variabilità degli output LLM al variare di configurazione e replica. Senza
il congelamento e la ripetizione, i nostri esperimenti non sarebbero confrontabili né
replicabili.

---

## 6. Implicazioni operative

**Sul codice.** Prevediamo un modulo/servizio LLM con un'interfaccia unica usata da
entrambi gli agenti, che riceve da configurazione il modello e i parametri. Non inseriamo
mai la chiave API nel codice né la versioniamo: la gestiamo tramite variabile d'ambiente
(coerentemente con `.env` già presente in `.gitignore`).

**Sulla configurazione.** Usiamo un file di configurazione che definisce, per ciascun agente,
modello e parametri. Versioniamo questo file per documentare la configurazione usata, mentre
manteniamo le credenziali fuori dal repository.

**Sulla fase sperimentale (Decisione 3.7).** La configurazione di riferimento del progetto
è il workflow completo (Generation Agent + Assessment Agent + memoria persistente),
adottata al termine delle prove progressive svolte durante lo sviluppo. La valutazione
definita nella Decisione 3.7 riguarda quindi la qualità dei requisiti prodotti da questa
configurazione, misurata rispetto al gold standard, alla rubrica di qualità e alla
valutazione umana. Manteniamo costante la scelta del modello all'interno di una stessa
campagna di valutazione per non introdurre confondenti; un eventuale confronto tra modelli
diversi costituisce un'analisi separata e va documentato come tale.

**Sui costi.** Teniamo traccia del costo per esecuzione (token in ingresso e uscita,
numero di chiamate) come metrica di valutazione, oltre alla qualità: un sistema più
costoso a parità di qualità è un risultato rilevante.

---

## 7. Nota pratica sull'accesso alle API

L'accesso alle API di Anthropic richiede un account con credito e una chiave API. Conserviamo
la chiave come variabile d'ambiente locale e non la inseriamo mai nel codice, nei commit o
nei log. In caso di passaggio futuro a modelli open source, l'astrazione descritta al punto
4.3 ci consente di aggiungere un nuovo backend senza modificare gli agenti.

---

## 8. Limiti e revisioni future

- Abbiamo scelto il modello iniziale per contenere i costi in sviluppo; rivaluteremo la
  scelta del modello per gli esperimenti finali in base ai risultati e al budget disponibile.
- Manteniamo aperta la possibilità di introdurre modelli open source (per massimizzare la
  riproducibilità o ridurre i costi sugli esperimenti su larga scala), resa praticabile
  dall'astrazione dal fornitore.
- Calibreremo i parametri di generazione (temperatura, top-p) e il numero di repliche per
  configurazione nella fase sperimentale; non li fissiamo in questa decisione.

---

## 9. Riferimenti

- Donato, B., Mariani, L., Micucci, D., & Riganelli, O. (2025b). Studying How
  Configurations Impact Code Generation in LLMs: The Case of ChatGPT. *ICPC 2025*,
  442–453.
- Wang, Q., Anikina, T., Feldhus, N., Ostermann, S., Möller, S., & Schmitt, V. (2025).
  Cross-Refine. *COLING 2025*, 1150–1167.
- Huang, J., et al. (2024). Large Language Models Cannot Self-Correct Reasoning Yet.
  *ICLR 2024*.
- Madaan, A., et al. (2023). Self-Refine: Iterative Refinement with Self-Feedback.
  *NeurIPS 2023*.
