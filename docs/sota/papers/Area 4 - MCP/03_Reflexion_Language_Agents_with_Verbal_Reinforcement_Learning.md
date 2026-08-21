# Reflexion: Language Agents with Verbal Reinforcement Learning

- **Autori / ente:** Noah Shinn; Federico Cassano; Ashwin Gopinath; Karthik Narasimhan; Shunyu Yao
- **Anno:** 2023
- **Venue / fonte:** NeurIPS 2023
- **DOI:** [10.48550/arXiv.2303.11366](https://doi.org/10.48550/arXiv.2303.11366)
- **Link ufficiale:** https://papers.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html
- **Accesso open / repository:** https://arxiv.org/abs/2303.11366
- **Nota accesso:** Paper ufficiale NeurIPS e preprint open access su arXiv.

## Breve riassunto

Reflexion introduce un meccanismo con cui un agente LLM può apprendere dai tentativi precedenti senza modificare i pesi del modello. Dopo l'esecuzione di un task, il feedback viene trasformato in una riflessione testuale che viene memorizzata in un buffer episodico e resa disponibile nei tentativi successivi. Questo permette all'agente di riutilizzare esperienza precedente nel proprio ragionamento. Gli autori mostrano miglioramenti su diversi task, inclusi coding e reasoning. Il contributo rilevante per questa area è quindi l'idea che una memoria esterna possa mantenere informazione utile tra iterazioni differenti.

## Uso nello stato dell'arte PR-to-Requirements

Nel documento Reflexion fornisce un antecedente concettuale della memoria persistente. PR-to-Requirements si differenzia però perché non vuole memorizzare semplici 'riflessioni' dell'LLM: la memoria dovrebbe contenere oggetti verificabili come requisito, PR di origine, stato di validazione, embedding e relazioni di duplicazione o conflitto.
