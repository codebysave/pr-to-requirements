# Can LLMs Generate User Stories and Assess Their Quality?

- **Autori:** Giovanni Quattrocchi; Liliana Pasquale; Paola Spoletini; Luciano Baresi
- **Anno:** 2026
- **Venue:** IEEE Transactions on Software Engineering
- **DOI:** [10.1109/TSE.2026.3670612](https://doi.org/10.1109/TSE.2026.3670612)
- **Link ufficiale:** https://doi.org/10.1109/TSE.2026.3670612
- **Accesso open/preprint o repository:** https://arxiv.org/abs/2507.15157
- **Nota accesso:** Preprint arXiv; è disponibile anche una copia istituzionale tramite Politecnico di Milano.

## Breve riassunto

Il paper studia sia la capacità degli LLM di generare user story sia la loro capacità di valutarne la qualità. Gli autori utilizzano dieci LLM e confrontano gli output con user story prodotte da studenti ed esperti. Per la valutazione semantica introducono un codebook con criteri espliciti, tra cui specificità della feature, chiarezza della motivazione, orientamento al problema, chiarezza linguistica e consistenza interna. Un risultato particolarmente importante è che l'accordo tra LLM e annotatori umani migliora quando al modello vengono fornite istruzioni operative precise ed esempi dettagliati. Il lavoro mostra quindi che un LLM può funzionare non solo come generatore, ma anche come evaluator, a condizione che la rubrica sia ben definita.

## Uso nello stato dell'arte PR-to-Requirements

È uno dei riferimenti più diretti per progettare il Requirement Assessment Agent: suggerisce di usare una rubrica esplicita, versionata e verificabile invece di un generico prompt del tipo 'controlla se il requisito è buono'.
