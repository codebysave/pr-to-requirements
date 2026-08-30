# Materiale per la tesi — indice

Progetto PR4Requirements · Andrea Saverino, Marco Saverino Salvatore
Università degli Studi di Milano-Bicocca · tutor: Benedetta Donato

---

## A che cosa serve questa cartella

I documenti raccolti qui sono **materiale preparatorio per la tesi**: riorganizzano
in forma espositiva il contenuto delle decisioni di progetto, aggiungendo i
risultati sperimentali via via ottenuti.

Non sostituiscono i documenti di `docs/design/decisions/`, che restano la
documentazione tecnica del progetto e la traccia di come le scelte siano state
prese. Il rapporto fra i due insiemi è il seguente:

| `docs/design/decisions/` | `thesis/` |
|---|---|
| registro delle decisioni | materiale espositivo |
| «abbiamo scelto X perché Y» | «il sistema fa X, e questa è la ragione» |
| aggiornamenti datati in coda | evoluzione integrata nel testo |
| destinatario: chi lavora al progetto | destinatario: chi legge la tesi |

Questi documenti **non sono la tesi**: sono la base da cui scriverla in prosa
continua, con una struttura di capitoli che va ancora concordata con la tutor.

---

## I documenti

| | Documento | Deriva da | Contenuto |
|---|---|---|---|
| **01** | [Requisiti: forma, qualità, fedeltà](01-requisiti-forma-qualita-evidenza.md) | Decisione 3.1 | che cos'è un requisito funzionale ben formato, i tre livelli di valutazione, i pattern EARS, i criteri di confine |
| **02** | [Il dataset e l'evidenza](02-dataset-ed-evidenza.md) | Decisione 3.6 | la sorgente PR4Code, i due corpus usati, perché l'evidenza è limitata a titolo e corpo, il contratto di ingresso |
| **03** | [L'architettura multi-agente](03-architettura-multi-agente.md) | Decisione 3.5 | i due agenti, la macchina a stati, il ciclo di revisione, le quattro decisioni, gli stati finali |
| **04** | [La scelta del modello linguistico](04-scelta-del-modello-linguistico.md) | Decisione 3.2 | locale contro remoto, aperto contro proprietario, le cinque configurazioni provate e i risultati |
| **05** | [La memoria persistente](05-memoria-persistente.md) | Decisione 3.3 | archivio e contesto, lo schema, il recupero esaustivo e perché non semantico, l'isolamento fra esecuzioni |
| **06** | [L'interfaccia MCP](06-interfaccia-mcp.md) | Decisione 3.4 | che cos'è MCP, i quattro strumenti, la separazione lettura/scrittura, lo stato dell'implementazione |
| **07** | [Il metodo di valutazione](07-metodo-di-valutazione.md) | Decisione 3.7 | il riferimento annotato, la rubrica, le condizioni necessarie, la regola anti-circolarità, le metriche |

Le cartelle `andrea/` e `marco/` sono destinate ai due elaborati individuali.

---

## Come questi documenti si collocano in una tesi

Una struttura consueta per una tesi di ingegneria del software, con la
corrispondenza al materiale disponibile:

| Capitolo | Contenuto | Materiale |
|---|---|---|
| 1. Introduzione | contesto, problema, obiettivo, contributo | **da scrivere** |
| 2. Stato dell'arte | cosa ha già prodotto la ricerca | `docs/sota/` — 29 schede in quattro aree |
| 3. Analisi del problema | che cos'è un requisito funzionale, i criteri | documento **01** |
| 4. Il dataset | sorgente, campione, evidenza | documento **02** |
| 5. Progettazione | architettura, modello, memoria, MCP | documenti **03**, **04**, **05**, **06** |
| 6. Implementazione | come è realizzato | codice, `recap.md` |
| 7. Valutazione | metodo e risultati | documento **07**, `experiments/` |
| 8. Discussione e limiti | cosa non funziona e perché | limiti dichiarati in ciascun documento |
| 9. Conclusioni | riepilogo e sviluppi futuri | **da scrivere** |

---

## Che cosa manca ancora

**Il riferimento annotato (*gold standard*).** È il passo che blocca il capitolo
sui risultati: senza, le osservazioni raccolte restano qualitative. Va costruito da
entrambi gli annotatori separatamente, sul corpus `OpenHands`.

**Il server MCP.** È l'unica componente prevista dall'architettura che resta da
realizzare (documento 06, §13).

**Le prove finali**, con le repliche necessarie a distinguere l'effetto dal rumore
(documento 07, §10) e il confronto fra memoria attiva e disattiva.

**Introduzione e conclusioni**, che si scrivono per ultime.

---

## Altro materiale disponibile nel repository

- `docs/sota/` — le schede dei 29 articoli, in quattro aree, e il documento
  assemblato dello stato dell'arte.
- `docs/meetings/open-questions-for-tutor-updated.md` — le questioni aperte, ognuna
  con la policy provvisoria adottata, l'argomento contrario e il costo di
  cambiarla.
- `experiments/analisi/confronto-modelli.md` — l'analisi estesa delle esecuzioni di
  confronto fra modelli, con le citazioni originali.
- `experiments/runs/` — i rapporti integrali di ogni esecuzione.
- `experiments/gold-standard/` — le schede di annotazione.
- `recap.md` — il registro cronologico delle modifiche al sistema.
- `worklog/diario-di-lavoro.md` — il diario di lavoro, non tecnico.
