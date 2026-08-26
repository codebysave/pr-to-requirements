from __future__ import annotations

from are.llm import UsageStats, estimate_cost_usd, format_usage


def test_usage_stats_sum() -> None:
    totale = UsageStats(calls=1, input_tokens=100, output_tokens=20) + UsageStats(
        calls=2, input_tokens=50, output_tokens=5
    )

    assert totale.calls == 3
    assert totale.input_tokens == 150
    assert totale.output_tokens == 25
    assert totale.total_tokens == 175


def test_estimates_cost_for_known_model() -> None:
    # Haiku 4.5: 1 dollaro per milione in ingresso, 5 in uscita.
    usage = UsageStats(calls=1, input_tokens=1_000_000, output_tokens=1_000_000)

    assert estimate_cost_usd("claude-haiku-4-5", usage) == 6.0


def test_estimates_small_usage() -> None:
    usage = UsageStats(calls=2, input_tokens=1000, output_tokens=200)

    cost = estimate_cost_usd("claude-haiku-4-5", usage)

    assert cost is not None
    assert abs(cost - 0.002) < 1e-9


def test_returns_none_for_unknown_model() -> None:
    usage = UsageStats(calls=1, input_tokens=1000, output_tokens=100)

    assert estimate_cost_usd("modello-sconosciuto", usage) is None


def test_format_usage_reports_cost_when_known() -> None:
    testo = format_usage("claude-haiku-4-5", UsageStats(3, 1500, 300))

    assert "3 chiamate" in testo
    assert "$" in testo


def test_format_usage_reports_unknown_cost() -> None:
    testo = format_usage("modello-sconosciuto", UsageStats(1, 10, 2))

    assert "n/d" in testo
