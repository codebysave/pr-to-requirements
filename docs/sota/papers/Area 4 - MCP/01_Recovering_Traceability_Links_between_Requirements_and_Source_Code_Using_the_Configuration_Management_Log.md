# Recovering Traceability Links between Requirements and Source Code Using the Configuration Management Log

- **Autori / ente:** Ryosuke Tsuchiya; Hironori Washizaki; Yoshiaki Fukazawa; Tadahisa Kato; Masumi Kawakami; Kentaro Yoshimura
- **Anno:** 2015
- **Venue / fonte:** IEICE Transactions on Information and Systems, E98-D(4), 852–862
- **DOI:** [10.1587/transinf.2014EDP7199](https://doi.org/10.1587/transinf.2014EDP7199)
- **Link ufficiale:** https://doi.org/10.1587/transinf.2014EDP7199
- **Accesso open / repository:** https://www.jstage.jst.go.jp/article/transinf/E98.D/4/E98.D_2014EDP7199/_article
- **Nota accesso:** Articolo free access su J-STAGE/IEICE, con PDF scaricabile.

## Breve riassunto

Gli autori affrontano il problema del recupero dei collegamenti di traceability tra requisiti e codice sorgente. Invece di basarsi soltanto sulla similarità testuale, propongono di usare il configuration management log come elemento intermedio per ricostruire relazioni tra requisiti e componenti del codice. Il metodo distingue inoltre gli elementi comuni a più prodotti da quelli specifici. Nell'esperimento riportato dagli autori, l'approccio semi-automatico recupera collegamenti validi con valori elevati di precision e recall e individua anche relazioni che non erano note agli ingegneri. Il punto concettuale centrale è che la storia del progetto può diventare una fonte attiva di contesto e non un semplice archivio passivo.

## Uso nello stato dell'arte PR-to-Requirements

Nel progetto PR-to-Requirements questo lavoro supporta l'idea di usare la memoria storica per recuperare informazioni relative a requisiti già emersi nel tempo. La memoria persistente viene quindi vista come una fonte di contesto storico utilizzabile per confrontare un nuovo requisito con quelli precedenti.
