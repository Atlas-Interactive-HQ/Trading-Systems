"""Shared types for Public-MD Scalp #139 D1/D2/D3 1D hold variants. Paper only.

D1 = C2 #138 long-only without SL (isolate ATR3 drag).
D2 = always-in 1D EMA21 flip long/short, flip-in-place, no SL.
D3 = C2 long entry; exit only when 1D close < EMA21 AND < EMA50; no SL.
NO 1.5R. NO ATR trail. NO S4/D/J. n_time_stop must be 0.
Do NOT edit phase1/120–138.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_136_common import (  # reuse 136 helpers; do not edit 136
    map_htf_predicate_to_1h,
)

EMA_1D = 21
EMA_1D_SLOW = 50
# Walker requires a numeric cap: FULL 1H trade bars = 4416, so use >> that.
TIME_STOP_DISABLED = 100_000
TIME_STOP = TIME_STOP_DISABLED
NO_TIME_STOP = True
NO_R_TP = True
NO_SELLLINE_EXIT = True
NO_ATR_TRAIL = True
NO_SL = True

LONG = "long"
SHORT = "short"
FLAT = "flat"


@dataclass(frozen=True)
class Scalp139Signals:
    """Per-1H-bar causal series for the #139 walker.

    entry_ok: long entry filter (D1/D3) — 1D close > EMA21.
    regime_flip: exit when True (D1: close < EMA21; D3: close < EMA21 AND < EMA50).
    desired_side: D2 only — 'long' | 'short' | 'flat' (always-in EMA21 flip).
    """

    entry_ok: list[bool]
    regime_flip: list[bool]
    desired_side: list[str]


OFFICIAL_CELLS = ("D1", "D2", "D3")
OFFICIAL_FAMILIES = ("d1_c2_nosl", "d2_alwaysin", "d3_dual_ema")
CELL_TO_FAMILY = {
    "D1": "d1_c2_nosl",
    "D2": "d2_alwaysin",
    "D3": "d3_dual_ema",
}
FAMILY_TO_CELL = {v: k for k, v in CELL_TO_FAMILY.items()}

FORBIDDEN_CELLS = frozenset(
    {
        "S4",
        "S1",
        "S2",
        "S3",
        "L1",
        "L2",
        "N1",
        "N2",
        "C1",
        "C2",
        "C3",
        "A",
        "B",
        "D",
        "E",
        "F",
        "H",
        "I",
        "J",
    }
)


def regime_ok_series_1d_ema(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_period: int = EMA_1D,
) -> list[bool]:
    """1D close > EMA(ema_period) mapped onto each 1H bar — entry filter."""
    return map_htf_predicate_to_1h(bars_1h, bars_1d, ema_period=ema_period, pred="gt")


def regime_flip_series_1d_ema(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_period: int,
) -> list[bool]:
    """1D close < EMA(ema_period) mapped onto each 1H bar — no lookahead."""
    return map_htf_predicate_to_1h(bars_1h, bars_1d, ema_period=ema_period, pred="lt")


def dual_ema_exit_series(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_fast: int = EMA_1D,
    ema_slow: int = EMA_1D_SLOW,
) -> list[bool]:
    """Exit only when 1D close < EMA_fast AND 1D close < EMA_slow (no lookahead)."""
    lt_fast = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=ema_fast)
    lt_slow = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=ema_slow)
    return [a and b for a, b in zip(lt_fast, lt_slow, strict=True)]


def always_in_side_series_1d_ema21(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_period: int = EMA_1D,
) -> list[str]:
    """Always-in desired side from 1D EMA21: > → long; < → short; else hold prior.

    Equal close==EMA keeps previous desired (or flat until first strict signal).
    No lookahead: last closed 1D with close_ts ≤ decision 1H close_ts.
    """
    gt = regime_ok_series_1d_ema(bars_1h, bars_1d, ema_period=ema_period)
    lt = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=ema_period)
    out: list[str] = []
    prev = FLAT
    for g, l in zip(gt, lt, strict=True):
        if g and not l:
            prev = LONG
        elif l and not g:
            prev = SHORT
        # else equal / undefined → keep prev
        out.append(prev)
    return out


__all__ = [
    "CELL_TO_FAMILY",
    "EMA_1D",
    "EMA_1D_SLOW",
    "FAMILY_TO_CELL",
    "FLAT",
    "FORBIDDEN_CELLS",
    "LONG",
    "NO_ATR_TRAIL",
    "NO_R_TP",
    "NO_SELLLINE_EXIT",
    "NO_SL",
    "NO_TIME_STOP",
    "OFFICIAL_CELLS",
    "OFFICIAL_FAMILIES",
    "SHORT",
    "Scalp139Signals",
    "TIME_STOP",
    "TIME_STOP_DISABLED",
    "always_in_side_series_1d_ema21",
    "dual_ema_exit_series",
    "map_htf_predicate_to_1h",
    "regime_flip_series_1d_ema",
    "regime_ok_series_1d_ema",
]
