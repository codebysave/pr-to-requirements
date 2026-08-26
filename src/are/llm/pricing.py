"""Stima dei costi delle chiamate LLM (Decisione 3.2, §6).

Il progetto tiene traccia del costo per esecuzione come metrica di valutazione,
accanto alla qualità: un sistema più costoso a parità di risultati è
un'informazione rilevante.

I token consumati sono un dato oggettivo restituito dal fornitore; il costo in
dollari è invece una stima basata sul listino, che può cambiare nel tempo. Per
questo i due valori restano distinti e la tabella dei prezzi riporta la data di
riferimento.
"""

from __future__ import annotations

from dataclasses import dataclass

# Prezzi in dollari per milione di token, listino Anthropic aggiornato al
# 2026-08-26. Da verificare periodicamente su https://www.anthropic.com/pricing
PRICING_REFERENCE_DATE = "2026-08-26"

_PRICE_PER_MILLION: dict[str, tuple[float, float]] = {
    # modello: (input, output)
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-opus-4-7": (5.00, 25.00),
    "claude-opus-4-6": (5.00, 25.00),
}


@dataclass(frozen=True, slots=True)
class UsageStats:
    """Consumo cumulato di un client LLM."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def __add__(self, other: UsageStats) -> UsageStats:
        return UsageStats(
            calls=self.calls + other.calls,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
        )

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def estimate_cost_usd(model: str, usage: UsageStats) -> float | None:
    """Stima il costo in dollari del consumo indicato.

    Restituisce ``None`` quando il modello non è presente nel listino: meglio
    nessun valore che un valore inventato.
    """

    prices = _PRICE_PER_MILLION.get(model)
    if prices is None:
        return None
    input_price, output_price = prices
    return (usage.input_tokens * input_price + usage.output_tokens * output_price) / 1_000_000


def format_usage(model: str, usage: UsageStats) -> str:
    """Riga leggibile con chiamate, token e costo stimato."""

    cost = estimate_cost_usd(model, usage)
    costo = f"${cost:.4f}" if cost is not None else "n/d"
    return (
        f"{usage.calls} chiamate, "
        f"{usage.input_tokens:,} token in ingresso, "
        f"{usage.output_tokens:,} in uscita, costo stimato {costo}"
    ).replace(",", ".")
