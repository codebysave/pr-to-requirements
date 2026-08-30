"""Presentazione a console del flusso di esecuzione.

Il log racconta che cosa sta succedendo *mentre* il sistema elabora una Pull
Request: quale fase è in corso, che cosa hanno prodotto i due agenti, con quale
esito e a quale costo. È scritto per essere letto durante l'esecuzione, quindi
privilegia la leggibilità rispetto alla compattezza.

Le funzioni restituiscono stringhe invece di scrivere direttamente: il livello
di dettaglio resta deciso da chi chiama, che conosce il proprio logger, e la
formattazione resta verificabile senza catturare l'output.

**Sui marcatori.** Il terminale Windows usa per impostazione predefinita la
codifica cp1252, che non rappresenta le emoji né i caratteri di disegno dei
riquadri: usarli non li renderebbe soltanto illeggibili, farebbe fallire la
scrittura della riga. I marcatori vengono quindi scelti all'importazione fra
quelli che la console dichiara di saper scrivere, con un ripiego in ASCII puro.
"""

from __future__ import annotations

import sys
import textwrap

WIDTH = 78

# Rientri delle tre profondità usate dal log.
_INDENT = " " * 5
_INDENT_DEEP = " " * 7


# I marcatori restano in ASCII puro. La console Windows dichiara cp1252, che
# rappresenterebbe il punto mediano e le virgolette angolari, ma lo stesso
# output attraversa anche pipe, file di log e terminali con codifiche diverse:
# in quel passaggio i byte cp1252 diventano caratteri di sostituzione. Il
# guadagno estetico non vale un log illeggibile a seconda di dove lo si guarda.
DOT = "|"  # separatore in linea
ARROW = ">>"  # esito di una fase
OK = "OK"  # la fase è passata
STOP = "!!"  # la fase ha fermato o rimandato indietro la Pull Request


def _thousands(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _rule(width: int, char: str = "-") -> str:
    return char * max(width, 0)


def _wrap(text: str, indent: str) -> str:
    """Manda a capo un testo lungo mantenendo il rientro.

    Le motivazioni degli agenti arrivano come singoli periodi di trecento
    caratteri: senza questo passaggio il terminale le spezza dove capita.
    """

    righe = textwrap.wrap(
        " ".join(text.split()),
        width=WIDTH - len(indent),
        break_long_words=False,
        break_on_hyphens=False,
    )
    return "\n".join(f"{indent}{riga}" for riga in righe) or f"{indent}{text}"


# ---------------------------------------------------------------------------
# Numerazione delle fasi
#
# Le fasi sono emesse da moduli diversi (il gate, i due agenti, il grafo) che
# non si conoscono fra loro. Un contatore qui evita di far transitare un
# dettaglio di presentazione attraverso lo stato del workflow, che descrive il
# dominio e non il log. La pipeline elabora una Pull Request alla volta in un
# solo thread, quindi un contatore di modulo è sufficiente.
# ---------------------------------------------------------------------------

_phase_counter = 0


def reset_phases() -> None:
    """Riparte da uno: da invocare all'inizio di ogni Pull Request."""

    global _phase_counter
    _phase_counter = 0


def pull_request_header(index: int, total: int, number: int, repository: str, title: str) -> str:
    reset_phases()
    intestazione = f" PR #{number}  {DOT}  {repository}  {DOT}  {index} di {total}"
    titolo = title if len(title) <= WIDTH - 2 else title[: WIDTH - 5] + "..."
    bordo = _rule(WIDTH, "=")
    return f"\n{bordo}\n{intestazione}\n {titolo}\n{bordo}"


def phase(name: str, detail: str | None = None) -> str:
    """Apre una fase numerata, chiusa a destra da un filetto."""

    global _phase_counter
    _phase_counter += 1
    etichetta = f" [{_phase_counter}] {name}"
    if detail:
        etichetta += f"  {DOT}  {detail}"
    riempimento = _rule(WIDTH - len(etichetta) - 1)
    return f"\n{etichetta} {riempimento}"


def note(text: str) -> str:
    """Riga di spiegazione: che cosa sta facendo il sistema in questa fase."""

    return _wrap(text, _INDENT)


def call(model: str, input_tokens: int, output_tokens: int, cost: float | None) -> str:
    """Riga di consuntivo della singola chiamata al modello."""

    prezzo = "n/d" if cost is None else f"${cost:.4f}".replace(".", ",")
    return (
        f"{_INDENT}{model}  {DOT}  {_thousands(input_tokens)} token in"
        f"  {DOT}  {_thousands(output_tokens)} out  {DOT}  {prezzo}"
    )


def result(text: str, marker: str = ARROW) -> str:
    """Esito di una fase, evidenziato dal marcatore."""

    return f"{_INDENT}{marker}  {text}"


def quoted(text: str) -> str:
    """Il testo di un requisito, a capo e fra virgolette."""

    return _wrap(f'"{text}"', _INDENT_DEEP)


def items(label: str, values: list[str]) -> str:
    """Elenco numerato ed etichettato delle voci di feedback.

    Il conteggio (``problema 1 di 3``) dice subito quante obiezioni sono state
    sollevate, informazione che un elenco puntato nasconde.
    """

    if not values:
        return ""
    blocchi: list[str] = []
    totale = len(values)
    for posizione, valore in enumerate(values, start=1):
        testa = f"{label} {posizione} di {totale}" if totale > 1 else label
        blocchi.append(f"\n{_INDENT}{testa}\n{_wrap(valore, _INDENT_DEEP)}")
    return "".join(blocchi)


def outcome(status: str, requirement: str | None = None, extra: str | None = None) -> str:
    etichetta = f" ESITO  {status}"
    riempimento = _rule(WIDTH - len(etichetta) - 1)
    righe = [f"\n{etichetta} {riempimento}"]
    if requirement:
        righe.append(quoted(requirement))
    if extra:
        righe.append(f"{_INDENT}{extra}")
    return "\n".join(righe)


def exchange(system: str, user_message: str, response: str) -> str:
    """Blocco di dettaglio con messaggio inviato e risposta grezza.

    Del prompt di sistema si riporta solo la dimensione: è lungo, identico a
    ogni chiamata e già leggibile nei file sotto `prompts/`.
    """

    def _prefissa(testo: str) -> list[str]:
        return [f"{_INDENT}|  {riga}" for riga in testo.splitlines()]

    apertura = f"{_INDENT}+-- messaggio inviato "
    chiusura = f"{_INDENT}+-- risposta ricevuta "
    fondo = f"{_INDENT}+"
    righe = [
        "",
        apertura + _rule(WIDTH - len(apertura)),
        f"{_INDENT}|  (prompt di sistema: {_thousands(len(system))} caratteri, "
        f"dai file in prompts/)",
        *_prefissa(user_message),
        chiusura + _rule(WIDTH - len(chiusura)),
        *_prefissa(response),
        fondo + _rule(WIDTH - len(fondo)),
    ]
    return "\n".join(righe)


def make_output_resilient() -> None:
    """Impedisce che un carattere non rappresentabile interrompa il log.

    Le risposte dei modelli contengono lineette lunghe, virgolette tipografiche
    e altri caratteri che cp1252 non rappresenta. Senza questa sostituzione la
    scrittura solleverebbe ``UnicodeEncodeError`` e la riga andrebbe persa nel
    mezzo di un'esecuzione lunga.
    """

    for flusso in (sys.stdout, sys.stderr):
        riconfigura = getattr(flusso, "reconfigure", None)
        if riconfigura is not None:
            try:
                riconfigura(errors="replace")
            except (ValueError, OSError):  # flusso non riconfigurabile
                continue
