"""Sizing regime at would-place time: does the risk budget or the leverage cap bind?

Research helper for candidate docs. notional = min(risk_budget / stop_frac, leverage_cap × equity),
so a wider stop halves notional only where the risk budget binds; where the cap binds, notional stays
at the cap and € at risk per trade grows with the stop. Measured, never assumed. No orders.
"""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any, Mapping, Sequence

from atlas.paper.engine import PaperSettings
from atlas.paper.shadow import ShadowEngine
from atlas.paper.types import Bar


class _CaptureJournal:
    def __init__(self) -> None:
        self.rows: list[tuple[str, dict[str, Any]]] = []

    def append(self, channel: str, record: dict[str, Any], *, ts_ms: int | None = None) -> Path:
        self.rows.append((channel, dict(record)))
        return Path(".")

    def write_summary(self, summary: dict[str, Any], *, ts_ms: int) -> Path:
        return Path(".")

    def dir_for(self, ts_ms: int) -> Path:
        return Path(".")


def _mean(xs: Sequence[float]) -> float | None:
    return round(statistics.mean(xs), 4) if xs else None


def measure_sizing_regime(
    settings: PaperSettings,
    strategy: Any,
    bars_by_symbol: Mapping[str, Sequence[Bar]],
    bars_1h_by_symbol: Mapping[str, Sequence[Bar]],
    venue_by_symbol: Mapping[str, str],
    *,
    run_id: str = "sizing-regime",
) -> dict[str, Any]:
    """Run the shadow path once (full sample) and summarise would-place sizing decisions."""
    jr = _CaptureJournal()
    eng = ShadowEngine(settings, strategy, journal=jr, run_id=run_id, data_dir=".", venue_by_symbol=dict(venue_by_symbol))
    eng.run(dict(bars_by_symbol), dict(bars_1h_by_symbol), universe=list(bars_by_symbol))
    wp = [r for c, r in jr.rows if c == "decisions" and r.get("kind") == "would_place"]
    cap = float(settings.leverage_hard_cap)
    lev = [float(r["leverage"]) for r in wp]
    bound = [x >= cap - 1e-6 for x in lev]
    eur_at_risk = [abs(float(r["qty"]) * (float(r["ref_close"]) - float(r["stop"]))) for r in wp]
    budget = [float(r["risk_budget"]) for r in wp]
    notional = [float(r["notional"]) for r in wp]
    n = len(wp)
    return {
        "not_a_forecast": True,
        "place_orders": False,
        "n_would_place": n,
        "leverage_hard_cap": cap,
        "share_cap_bound": round(sum(bound) / n, 4) if n else None,
        "mean_notional_eur": _mean(notional),
        "median_notional_eur": round(statistics.median(notional), 4) if notional else None,
        "mean_eur_at_risk": _mean(eur_at_risk),
        "mean_risk_budget_eur": _mean(budget),
        "mean_eur_at_risk_cap_bound": _mean([e for e, b in zip(eur_at_risk, bound) if b]),
        "mean_eur_at_risk_budget_bound": _mean([e for e, b in zip(eur_at_risk, bound) if not b]),
        "atr_stop_mult": float(strategy.params.atr_stop_mult),
    }
