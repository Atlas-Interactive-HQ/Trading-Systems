"""Session VWAP — UTC day reset, typical=(H+L+C)/3. Research only. not_a_forecast.

Formula (documented for #134 cell J):
  typical = (high + low + close) / 3
  Within each UTC calendar day (reset at 00:00Z):
    VWAP = cumsum(typical * volume) / cumsum(volume)
  If cum volume == 0 → None for that bar.
Causal: uses only bars of the same UTC day up to and including i. No lookahead.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from atlas.paper.types import Bar, q


def _utc_day_key(ts_open_ms: int) -> str:
    return datetime.fromtimestamp(ts_open_ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%d"
    )


def session_vwap_series(bars: Sequence[Bar]) -> list[float | None]:
    """Per-bar session VWAP with UTC day reset."""
    out: list[float | None] = [None] * len(bars)
    day: str | None = None
    cum_pv = 0.0
    cum_v = 0.0
    for i, b in enumerate(bars):
        key = _utc_day_key(int(b.ts_open_ms))
        if key != day:
            day = key
            cum_pv = 0.0
            cum_v = 0.0
        typical = (float(b.high) + float(b.low) + float(b.close)) / 3.0
        vol = float(b.volume)
        if vol < 0:
            out[i] = None
            continue
        cum_pv += typical * vol
        cum_v += vol
        if cum_v <= 0:
            out[i] = None
        else:
            out[i] = q(cum_pv / cum_v)
    return out


__all__ = ["session_vwap_series"]
