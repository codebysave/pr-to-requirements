# Self-Refine: Iterative Refinement with Self-Feedback

- **Autori:** Aman Madaan et al.
- **Anno:** 2023
- **Venue:** NeurIPS 2023
- **DOI:** [10.52202/075280-2019](https://doi.org/10.52202/075280-2019)
- **Link ufficiale:** https://papers.neurips.cc/paper_files/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html
- **Accesso open/preprint/repository:** https://arxiv.org/abs/2303.17651
- **Nota accesso:** Paper ufficiale NeurIPS e preprint arXiv.

## Breve riassunto

Self-Refine propone un ciclo iterativo nel quale lo stesso LLM genera un primo output, produce feedback sul proprio risultato e lo riscrive sulla base di tale feedback. Non richiede training aggiuntivo né dati supervisionati: generator, critic e refiner coincidono nello stesso modello. Gli autori valutano l'approccio su diversi task e riportano miglioramenti rispetto alla generazione single-shot. Il contributo dimostra che una seconda fase di critica e revisione può essere utile, ma non dimostra di per sé il vantaggio di usare agenti realmente distinti.

## Uso nello stato dell'arte PR-to-Requirements

Nel progetto funziona come baseline fondamentale: permette di distinguere il beneficio della semplice auto-revisione dal beneficio specifico di un vero pattern Generator–Critic con ruoli separati.

## Base del riassunto

Riassunto basato sullo stato dell'arte fornito e sulla pagina ufficiale NeurIPS.
