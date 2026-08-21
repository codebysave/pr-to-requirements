# Semantically Enhanced Software Traceability Using Deep Learning Techniques

- **Autori / ente:** Jin Guo; Jinghui Cheng; Jane Cleland-Huang
- **Anno:** 2017
- **Venue / fonte:** IEEE/ACM 39th International Conference on Software Engineering (ICSE)
- **DOI:** [10.1109/ICSE.2017.9](https://doi.org/10.1109/ICSE.2017.9)
- **Link ufficiale:** https://doi.org/10.1109/ICSE.2017.9
- **Accesso open / repository:** https://arxiv.org/abs/1804.02438
- **Nota accesso:** Preprint open access su arXiv; metadati disponibili anche in repository istituzionali.

## Breve riassunto

Il paper propone un approccio di software traceability basato su deep learning per recuperare collegamenti tra artefatti software. Gli autori osservano che le tecniche tradizionali di information retrieval faticano quando gli artefatti esprimono lo stesso concetto con parole diverse. Per superare questo limite, utilizzano word embedding e reti neurali ricorrenti per apprendere rappresentazioni semantiche dei requisiti e degli altri artefatti. L'obiettivo è quindi recuperare relazioni concettualmente rilevanti anche in assenza di forte sovrapposizione lessicale. Il contributo è particolarmente importante per qualunque sistema che debba cercare artefatti semanticamente vicini in un corpus storico.

## Uso nello stato dell'arte PR-to-Requirements

È il principale fondamento del retrieval semantico della memoria di PR-to-Requirements. Un nuovo requisito candidato può essere confrontato con requisiti storici semanticamente affini anche quando il testo usa un vocabolario differente, recuperando un piccolo insieme di candidati da fornire all'Assessment Agent.
