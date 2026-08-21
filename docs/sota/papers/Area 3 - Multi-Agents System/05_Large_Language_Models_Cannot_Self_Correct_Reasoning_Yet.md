# Large Language Models Cannot Self-Correct Reasoning Yet

- **Autori:** Jie Huang; Xinyun Chen; Swaroop Mishra; Huaixiu Steven Zheng; Adams Wei Yu; Xinying Song; Denny Zhou
- **Anno:** 2024
- **Venue:** ICLR 2024
- **DOI:** non indicato / non necessario nella fonte ufficiale
- **Link ufficiale:** https://openreview.net/forum?id=IkmD3fKBPQ
- **Accesso open/preprint/repository:** https://arxiv.org/abs/2310.01798
- **Nota accesso:** Paper ufficiale ICLR su OpenReview e preprint arXiv.

## Breve riassunto

Gli autori esaminano criticamente la capacità degli LLM di correggere autonomamente il proprio ragionamento. Il focus è sulla self-correction intrinseca, cioè senza feedback esterno affidabile. Nei task studiati, il semplice invito a ricontrollare la risposta non porta sistematicamente a un miglioramento e in alcuni casi può persino peggiorare le prestazioni. Il lavoro distingue quindi tra revisione basata solo sulle capacità interne del modello e revisione che beneficia di segnali esterni o informazione aggiuntiva.

## Uso nello stato dell'arte PR-to-Requirements

Fornisce la principale contro-evidenza per il design del critic: l'Assessment Agent deve avere un vantaggio informativo, ad esempio rubrica esplicita, evidenze della PR e requisiti storici recuperati, invece di limitarsi a chiedere una generica autocorrezione.

## Base del riassunto

Riassunto basato sullo stato dell'arte fornito e sull'abstract ufficiale ICLR/OpenReview.
