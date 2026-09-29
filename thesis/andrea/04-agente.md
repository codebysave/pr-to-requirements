# L'agente

**Materiale per la tesi — bozza di capitolo, in corso**
Corrisponde al capitolo 4 dell'indice (`thesis/00-indice.md`).
Progetto PR-to-Requirements · Università degli Studi di Milano-Bicocca

---

## 4.1 Che cos'è un agente basato su LLM

Il termine *agente* precede di decenni i modelli linguistici. Nel manuale di
riferimento dell'intelligenza artificiale, Russell e Norvig (2021) chiamano
agente qualsiasi entità che percepisce il proprio ambiente attraverso dei
sensori e agisce su di esso attraverso degli attuatori, e la valutano in base
a quanto le sue azioni la avvicinano a un obiettivo. La definizione è
volutamente ampia: la soddisfano un termostato e un robot autonomo. La sua
utilità sta nello spostare l'attenzione dal modo in cui l'entità è costruita
al ciclo che la caratterizza: percepire, decidere, agire, percepire di nuovo.

Un modello linguistico, preso da solo, non rientra in questo schema. È una
funzione che riceve un testo e ne restituisce un altro: non conserva nulla da
una chiamata alla successiva, non ha obiettivi propri e non produce effetti al
di fuori del testo che genera. Si parla di **agente basato su LLM** quando
attorno al modello si costruisce ciò che gli manca per chiudere il ciclo: un
ruolo e degli obiettivi, espressi nelle istruzioni che il modello riceve
(§4.2); la possibilità di agire, tramite strumenti che il modello può
richiedere e il cui risultato gli viene restituito (§4.3); una memoria che
sopravvive alla singola chiamata (§4.4); e un ciclo che riporta l'esito di
ogni azione in ingresso alla decisione successiva (§4.5). Il modello fa da
motore decisionale, mentre percezione e azione passano attraverso il testo che
entra e quello che esce. Questa scomposizione è consolidata nella letteratura,
che descrive tali agenti come composti da moduli di profilo, memoria,
pianificazione e azione (Wang et al., 2024), e trova un esempio influente in
ReAct (Yao et al., 2023), in cui il modello alterna passi di ragionamento e
azioni su strumenti esterni.

Non esiste tuttavia una definizione condivisa, e il termine designa in pratica
oggetti molto diversi: dalla singola chiamata a un modello con un ruolo
assegnato, fino a sistemi che scelgono da soli i passi da compiere e il
momento in cui fermarsi. Anthropic (2024) propone di distinguerli in base a
chi governa il flusso: sono *workflow* i sistemi in cui modelli e strumenti
sono orchestrati da percorsi di codice predefiniti, sono *agenti* quelli in
cui il modello dirige dinamicamente il proprio processo e l'uso degli
strumenti. Più che due categorie separate, sono i due estremi di uno spettro,
e il grado di autonomia concesso al modello è una scelta di progetto, non una
proprietà intrinseca dell'agente.

In questo lavoro si adotta una definizione operativa, volutamente modesta: per
**agente** si intende un componente basato su un modello linguistico, a cui
sono assegnati un ruolo e delle istruzioni e, dove necessario, strumenti e
memoria, che restituisce un'uscita interpretabile dal resto del sistema. Gli
agenti di PR-to-Requirements, il generatore e il valutatore (capitoli 10 e
11), sono agenti in questo senso, ma non decidono il flusso in cui sono
inseriti: il controllo appartiene a una macchina a stati deterministica
(§7.3). È una scelta consapevole, di cui la §4.6 discute le ragioni.

---

## Note aperte

- **Registro:** impersonale ("si adotta", "in questo lavoro"). Da confermare
  se è il registro voluto per l'intera tesi.
- **Riferimenti da verificare:** Russell & Norvig (*AIMA*, 4a ed., 2021),
  Yao et al. (2023, ReAct), Wang et al. (2024, survey sugli agenti LLM),
  Anthropic (2024, *Building effective agents*). Citati a memoria, non
  controllati: nessuno è ancora in `docs/sota`, vanno aggiunti alla
  bibliografia e verificati anno ed edizione.
- **Figura possibile:** diagramma del ciclo percezione → decisione → azione,
  con il modello al centro.
- **Rimandi:** §4.2–4.6, §7.3, capp. 10–11, secondo la numerazione
  dell'indice attuale (`thesis/00-indice.md`). Da aggiornare se l'indice
  cambia.
- **Prossima sezione da scrivere:** 4.2, Ruolo, istruzioni e comportamento.
