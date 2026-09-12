"""Shared types for Public-MD Scalp #140 E1/E2/E3 D3-seed / EMA variants. Paper only.

E1 = D3 long entry (1D close > EMA21) + FULL-window seed + dual EMA21∧EMA50 exit.
E2 = enter 1D close > EMA12; same D3 dual exit (EMA21∧EMA50).
E3 = enter 1D close > EMA21 (C2); exit only when 1D close < EMA50 AND < EMA100.
Long-only. NO SL. NO ts. NO shorts. n_sl=0 n_time_stop=0.
Do NOT edit phase1/120–139.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import ema_series
from atlas.strategy.scalp_136_common import map_htf_predicate_to_1h

EMA_1D = 21
EMA_1D_FAST_E2 = 12
EMA_1D_SLOW = 50
EMA_1D_XSlow = 100
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
class Scalp140Signals:
    """Per-1H-bar causal series for the #140 walker.

    entry_ok: long entry filter.
    regime_flip: exit when True (dual-EMA AND).
    seed_fired: True on the 1H decision bar that observed the FULL seed (E1 honesty).
    """

    entry_ok: list[bool]
    regime_flip: list[bool]
    seed_fired: list[bool]


OFFICIAL_CELLS = ("E1", "E2", "E3")
OFFICIAL_FAMILIES = ("e1_seed", "e2_ema12", "e3_ema50_100")
CELL_TO_FAMILY = {
    "E1": "e1_seed",
    "E2": "e2_ema12",
    "E3": "e3_ema50_100",
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
        "D1",
        "D2",
        "D3",
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
    ema_fast: int,
    ema_slow: int,
) -> list[bool]:
    """Exit only when 1D close < EMA_fast AND 1D close < EMA_slow (no lookahead)."""
    lt_fast = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=ema_fast)
    lt_slow = regime_flip_series_1d_ema(bars_1h, bars_1d, ema_period=ema_slow)
    return [a and b for a, b in zip(lt_fast, lt_slow, strict=True)]


def first_full_1d_seed_series(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_period: int = EMA_1D,
    full_start_ms: int,
    full_end_ms: int,
) -> list[bool]:
    """Seed: if first FULL-window 1D bar already has close > EMA, fire on its 1H.

    Do not wait for a fresh cross. Fail closed if EMA cold (ema is None).
    No lookahead: seed 1H is the bar whose ts_close_ms >= that 1D ts_close_ms
    (first such closed 1H); fill is next 1H open via the walker.
    """
    n = len(bars_1h)
    out = [False] * n
    if n == 0:
        return out
    closed_1d = [
        b
        for b in bars_1d
        if b.closed and full_start_ms <= b.ts_open_ms < full_end_ms
    ]
    if not closed_1d:
        return out
    first = closed_1d[0]
    # EMA over all closed 1D up to and including `first` (causal).
    closed_all = [b for b in bars_1d if b.closed and b.ts_close_ms <= first.ts_close_ms]
    if len(closed_all) < ema_period:
        return out
    closes = [float(b.close) for b in closed_all]
    emas = ema_series(closes, ema_period)
    ema_last = emas[-1]
    if ema_last is None:
        return out
    if not (float(first.close) > float(ema_last)):
        return out
    # Map onto first 1H whose close observes this 1D close (no lookahead).
    for i, d in enumerate(bars_1h):
        if d.ts_close_ms >= first.ts_close_ms:
            out[i] = True
            break
    return out


def entry_ok_with_seed(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_period: int,
    full_start_ms: int,
    full_end_ms: int,
) -> tuple[list[bool], list[bool]]:
    """D3-style level entry OR FULL seed. Returns (entry_ok, seed_fired)."""
    level = regime_ok_series_1d_ema(bars_1h, bars_1d, ema_period=ema_period)
    seed = first_full_1d_seed_series(
        bars_1h,
        bars_1d,
        ema_period=ema_period,
        full_start_ms=full_start_ms,
        full_end_ms=full_end_ms,
    )
    entry = [a or b for a, b in zip(level, seed, strict=True)]
    return entry, seed


__all__ = [
    "CELL_TO_FAMILY",
    "EMA_1D",
    "EMA_1D_FAST_E2",
    "EMA_1D_SLOW",
    "EMA_1D_XSlow",
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
    "Scalp140Signals",
    "TIME_STOP",
    "TIME_STOP_DISABLED",
    "dual_ema_exit_series",
    "entry_ok_with_seed",
    "first_full_1d_seed_series",
    "map_htf_predicate_to_1h",
    "regime_flip_series_1d_ema",
    "regime_ok_series_1d_ema",
]
