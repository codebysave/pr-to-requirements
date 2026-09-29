# Gold standard — appunti

Appunti di lavoro, non un capitolo. Promemoria del processo da ripetere
identico su ogni campione. File in `experiments/gold-standard/`.

Regola di fondo: i tre file "pattern" **non si compilano mai direttamente**.
Restano il regolamento riusabile; ogni campione genera i propri file compilati
a partire da quelli, con il suffisso del progetto.

---

## 1. Annotazione separata

Pattern: `annotazione-template.md` → produce le due schede individuali.

Ciascuno annota le stesse Pull Request guardando **solo l'evidenza**, senza
consultare l'altro. Per ognuna: estraibilità, requisito di riferimento se
estraibile, schema EARS, nota sul perché. Nessun confronto in questa fase.

## 2. Unificazione → Ground Truth

Pattern: `legenda-unificazione-requisiti.md` → produce il file di
unificazione.

Non si sceglie fra le due annotazioni, si ri-deriva dall'evidenza:

1. si classifica la divergenza (stesso requisito / stessa forma diversa
   formulazione / una eccede l'altra / comportamenti davvero diversi — in
   quest'ultimo caso si registra il disaccordo, non si forza un riferimento);
2. sulla forma decide la regola, non chi l'aveva scelta;
3. sull'ampiezza si tiene solo ciò che l'evidenza enuncia, si toglie ciò che
   viene da un nome di file, di libreria, o dalla nostra conoscenza del
   dominio — ogni scelta motivata per iscritto;
4. controllo finale: un solo obbligo per requisito.

In fondo, una volta sole e solo a unificazione conclusa: l'accordo fra le due
annotazioni **originali** (mai sul Ground Truth, farebbe 100% per
costruzione).

## 3. Confronto Ground Truth ↔ sistema

Pattern: `confronto-GT-sistema_template.md` → produce il file di confronto.

Solo qui guardiamo l'output del sistema. Si confronta il GT (non le schede
originali) con il requisito generato: corrispondenza semantica
(`MATCH`/`PARTIAL`/`NO_MATCH`) e rubrica a dieci criteri falsificabili,
applicata anche al Ground Truth stesso. Si guarda anche la traccia — tentativi,
revisioni, affermazioni non sostenute — non solo il requisito finale. Chiude
con l'analisi: esiti, metriche, dove sbaglia il sistema, conclusioni, limiti.

---

## Da fissare prima del prossimo campione

- Un requisito del sistema più specifico del GT: `MATCH`, `PARTIAL`, o difetto
  di fedeltà? Deciderlo prima di contare, non dopo.
- Come si registra un'incoerenza fra due Pull Request con evidenza identica.
- Un solo campione dice *come* il sistema sbaglia, non *quanto spesso*: serve
  ripetere il processo prima di parlare di frequenze.
