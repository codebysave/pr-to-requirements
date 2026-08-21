# Cross-Refine: Improving Natural Language Explanation Generation by Learning in Tandem

- **Autori:** Qianli Wang; Tatiana Anikina; Nils Feldhus; Simon Ostermann; Sebastian Möller; Vera Schmitt
- **Anno:** 2025
- **Venue:** COLING 2025
- **DOI:** non indicato / non necessario nella fonte ufficiale
- **Link ufficiale:** https://aclanthology.org/2025.coling-main.77/
- **Accesso open/preprint/repository:** https://aclanthology.org/2025.coling-main.77.pdf
- **Nota accesso:** Full text ufficiale open access su ACL Anthology.

## Breve riassunto

Cross-Refine separa esplicitamente i ruoli di generator e critic. Il generator produce una prima spiegazione, mentre un secondo LLM fornisce feedback e suggerimenti specifici; il generator usa poi queste indicazioni per raffinare l'output. Gli autori confrontano Cross-Refine con Self-Refine e riportano risultati migliori per il pattern a ruoli distinti. Le ablation mostrano inoltre che sia il feedback sia i suggerimenti concreti contribuiscono al miglioramento. Il messaggio principale è che il critic è più utile quando fornisce informazione strutturata e azionabile, invece di limitarsi a chiedere al modello di 'ricontrollare' il proprio output.

## Uso nello stato dell'arte PR-to-Requirements

È il pattern metodologicamente più vicino al loop Generator–Assessment Agent previsto da PR-to-Requirements e motiva un feedback strutturato con errori, mancanze e istruzioni precise di revisione.

## Base del riassunto

Riassunto basato sullo stato dell'arte fornito e sull'abstract ufficiale ACL Anthology.
