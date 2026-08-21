# Studying How Configurations Impact Code Generation in LLMs: The Case of ChatGPT

- **Autori:** Benedetta Donato; Leonardo Mariani; Daniela Micucci; Oliviero Riganelli
- **Anno:** 2025
- **Venue:** ICPC 2025
- **DOI:** [10.1109/ICPC66645.2025.00055](https://doi.org/10.1109/ICPC66645.2025.00055)
- **Link ufficiale:** https://doi.org/10.1109/ICPC66645.2025.00055
- **Accesso open/preprint/repository:** https://arxiv.org/abs/2502.17450
- **Nota accesso:** Preprint open access su arXiv; metadati disponibili nel repository Milano-Bicocca.

## Breve riassunto

Il lavoro studia come differenti configurazioni di ChatGPT influenzino la generazione di codice. Gli autori analizzano parametri come temperature e top-p e considerano anche il numero di ripetizioni necessario per gestire la natura non deterministica degli LLM. Su 548 metodi Java vengono osservate differenze significative tra configurazioni, con un impatto particolarmente evidente di top-p, e vengono formulate raccomandazioni sperimentali per affrontare la variabilità degli output. Il messaggio metodologico è che una singola esecuzione non è sufficiente per caratterizzare in modo affidabile una configurazione LLM.

## Uso nello stato dell'arte PR-to-Requirements

Motiva l'esecuzione di più repliche e il controllo rigoroso di modello, versione, temperature, top-p, prompt e pipeline quando si confrontano le configurazioni sperimentali di PR-to-Requirements.

## Base del riassunto

Riassunto basato sullo stato dell'arte fornito e sull'abstract arXiv/repository istituzionale.
