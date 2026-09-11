"""Relative volume (RVOL) — Scalp S1+ confirmation gate.

LOCKED S1 definition (once): RVOL = volume / SMA(volume, 20) on the decision bar;
gate RVOL > 1. Research only. not_a_forecast. No lookback/threshold grind on FAIL.
"""

from __future__ import annotations

from typing import Sequence

from atlas.paper.types import Bar

RVOL_LOOKBACK = 20
RVOL_GATE_S1 = 1.0


def sma_volume(bars: Sequence[Bar], lookback: int = RVOL_LOOKBACK) -> float | None:
    """Simple average of the last `lookback` bar volumes (includes current)."""
    if lookback < 1 or len(bars) < lookback:
        return None
    window = bars[-lookback:]
    vols = [float(b.volume) for b in window]
    if any(v < 0 for v in vols):
        return None
    return sum(vols) / lookback


def rvol_at(bars: Sequence[Bar], lookback: int = RVOL_LOOKBACK) -> float | None:
    """RVOL = last volume / SMA(volume, lookback). None if cold or SMA<=0."""
    sma = sma_volume(bars, lookback)
    if sma is None or sma <= 0:
        return None
    return float(bars[-1].volume) / sma


def rvol_series(
    bars: Sequence[Bar], lookback: int = RVOL_LOOKBACK
) -> list[float | None]:
    """Per-bar RVOL; None until `lookback` volumes available."""
    out: list[float | None] = []
    for i in range(len(bars)):
        out.append(rvol_at(bars[: i + 1], lookback))
    return out


__all__ = [
    "RVOL_GATE_S1",
    "RVOL_LOOKBACK",
    "rvol_at",
    "rvol_series",
    "sma_volume",
]
