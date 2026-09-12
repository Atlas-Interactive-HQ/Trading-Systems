"""Shared types for Public-MD Scalp #141 F1/F2/F3 sticky/hold variants. Paper only.

Shared ENTRY = E1/D3: 1D close > EMA21 OR seed if first FULL 1D bar already
close > EMA21 → fill next 1H open. Max 1. Long-only. NO SL. NO ts. NO shorts.
F1: hold-to-end (no regime exit; forced_end at window end).
F2: exit after 3 consecutive closed 1D bars with close < EMA21 → next 1H open.
F3: exit after 2 consecutive closed 1D bars each close < EMA21 AND < EMA50 → next 1H open.
Do NOT edit phase1/120–140. Read-only reuse of E1/D3 helper logic (copied, not imported from #140).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import ema_series
from atlas.strategy.scalp_136_common import map_htf_predicate_to_1h

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

F2_STICKY_N = 3
F3_STICKY_N = 2

LONG = "long"
SHORT = "short"
FLAT = "flat"


@dataclass(frozen=True)
class Scalp141Signals:
    """Per-1H-bar causal series for the #141 walker.

    entry_ok: long entry filter (E1/D3 + seed).
    regime_flip: sticky exit when True (F2/F3); always False for F1.
    seed_fired: True on the 1H decision bar that observed the FULL seed.
    """

    entry_ok: list[bool]
    regime_flip: list[bool]
    seed_fired: list[bool]


OFFICIAL_CELLS = ("F1", "F2", "F3")
OFFICIAL_FAMILIES = ("f1_holdend", "f2_sticky3", "f3_sticky_dual")
CELL_TO_FAMILY = {
    "F1": "f1_holdend",
    "F2": "f2_sticky3",
    "F3": "f3_sticky_dual",
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
        "E1",
        "E2",
        "E3",
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


def dual_ema_lt_predicate_1d(
    bars_1d: Sequence[Bar],
    *,
    ema_fast: int,
    ema_slow: int,
) -> list[bool]:
    """Per closed 1D bar: close < EMA_fast AND close < EMA_slow. Cold EMA → False."""
    closed = [b for b in bars_1d if b.closed]
    if not closed:
        return []
    closes = [float(b.close) for b in closed]
    ema_f = ema_series(closes, ema_fast)
    ema_s = ema_series(closes, ema_slow)
    out: list[bool] = []
    for i, b in enumerate(closed):
        ef, es = ema_f[i], ema_s[i]
        if ef is None or es is None:
            out.append(False)
        else:
            c = float(b.close)
            out.append(c < float(ef) and c < float(es))
    return out


def lt_ema_predicate_1d(
    bars_1d: Sequence[Bar],
    *,
    ema_period: int,
) -> list[bool]:
    """Per closed 1D bar: close < EMA. Cold EMA → False."""
    closed = [b for b in bars_1d if b.closed]
    if not closed:
        return []
    closes = [float(b.close) for b in closed]
    emas = ema_series(closes, ema_period)
    out: list[bool] = []
    for i, b in enumerate(closed):
        ema = emas[i]
        if ema is None:
            out.append(False)
        else:
            out.append(float(b.close) < float(ema))
    return out


def sticky_consecutive_from_1d_flags(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    day_flags: Sequence[bool],
    *,
    n_consec: int,
) -> list[bool]:
    """Map sticky consecutive True days onto 1H — no lookahead.

    day_flags aligns to closed 1D bars in time order. Exit True on/after the
    1D close that completes n_consec consecutive True days; resets on False.
    """
    n = len(bars_1h)
    if n == 0:
        return []
    closed_htf = [b for b in bars_1d if b.closed]
    if not closed_htf or len(day_flags) != len(closed_htf):
        return [False] * n
    consec = 0
    flag_at_htf: list[bool] = []
    for flag in day_flags:
        if flag:
            consec += 1
            flag_at_htf.append(consec >= int(n_consec))
        else:
            consec = 0
            flag_at_htf.append(False)
    out: list[bool] = []
    j = -1
    for d in bars_1h:
        while j + 1 < len(closed_htf) and closed_htf[j + 1].ts_close_ms <= d.ts_close_ms:
            j += 1
        out.append(False if j < 0 else flag_at_htf[j])
    return out


def sticky_lt_ema_exit_series(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_period: int,
    n_consec: int,
) -> list[bool]:
    """Exit after n_consec consecutive closed 1D bars with close < EMA."""
    day = lt_ema_predicate_1d(bars_1d, ema_period=ema_period)
    return sticky_consecutive_from_1d_flags(
        bars_1h, bars_1d, day, n_consec=n_consec
    )


def sticky_dual_ema_exit_series(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_fast: int,
    ema_slow: int,
    n_consec: int,
) -> list[bool]:
    """Exit after n_consec consecutive 1D bars each close < EMA_fast AND < EMA_slow."""
    day = dual_ema_lt_predicate_1d(bars_1d, ema_fast=ema_fast, ema_slow=ema_slow)
    return sticky_consecutive_from_1d_flags(
        bars_1h, bars_1d, day, n_consec=n_consec
    )


def first_full_1d_seed_series(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_period: int = EMA_1D,
    full_start_ms: int,
    full_end_ms: int,
) -> list[bool]:
    """Seed: if first FULL-window 1D bar already has close > EMA, fire on its 1H.

    Copied from #140 E1 helper logic (read-only; this file is new). Fail closed
    if EMA cold. No lookahead.
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
    "EMA_1D_SLOW",
    "F2_STICKY_N",
    "F3_STICKY_N",
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
    "Scalp141Signals",
    "TIME_STOP",
    "TIME_STOP_DISABLED",
    "dual_ema_lt_predicate_1d",
    "entry_ok_with_seed",
    "first_full_1d_seed_series",
    "lt_ema_predicate_1d",
    "map_htf_predicate_to_1h",
    "regime_flip_series_1d_ema",
    "regime_ok_series_1d_ema",
    "sticky_consecutive_from_1d_flags",
    "sticky_dual_ema_exit_series",
    "sticky_lt_ema_exit_series",
]
