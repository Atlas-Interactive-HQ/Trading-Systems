"""Shared types for Public-MD Scalp #136 L1/L2 1D EMA21-flip hold. Paper only.

L1 = #135 S2 / #134 G Keltner entry. L2 = #135 S3 / #134 C Donchian entry.
Exits: fixed entry SL · 1D close < EMA21 → next 1H open · ts504.
NO 1.5R. NO 4H EMA flip exit. NO ATR trail. NO S4/D/J.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import ema_series


@dataclass(frozen=True)
class Scalp136Signals:
    """Per-1H-bar causal series for the #136 walker.

    entry_ok: long entry on closed 1H (fill next open). Same as #135 S2/S3.
    regime_flip: 1D close < EMA21 mapped onto 1H (exit next 1H open).
    regime_flip_4h: 4H close < EMA21 mapped onto 1H — honesty/tests ONLY.
                    Walker MUST ignore this (NO 4H EMA flip exit).
    sl_ref: fixed entry SL (Keltner mid / Donchian mid).
    atr: unused for exits (no trail); kept for honesty vs parent.
    """

    entry_ok: list[bool]
    regime_flip: list[bool]
    regime_flip_4h: list[bool]
    sl_ref: list[float | None]
    atr: list[float | None]


TIME_STOP = 504  # ~3 weeks of 1H
EMA_4H = 21  # entry regime only
EMA_1D = 21  # exit regime only
ATR_N = 14
NO_R_TP = True
NO_SELLLINE_EXIT = True
NO_4H_EMA_FLIP_EXIT = True
NO_ATR_TRAIL = True

OFFICIAL_CELLS = ("L1", "L2")
OFFICIAL_FAMILIES = ("l1_keltner", "l2_donchian")
CELL_TO_FAMILY = {"L1": "l1_keltner", "L2": "l2_donchian"}
FAMILY_TO_CELL = {"l1_keltner": "L1", "l2_donchian": "L2"}
# Honesty parents (letters from #135)
CELL_TO_PARENT = {"L1": "S2_G", "L2": "S3_C"}

FORBIDDEN_CELLS = frozenset(
    {"S4", "S1", "S2", "S3", "A", "B", "D", "E", "F", "H", "I", "J"}
)


def map_htf_predicate_to_1h(
    bars_1h: Sequence[Bar],
    bars_htf: Sequence[Bar],
    *,
    ema_period: int,
    pred: str,
) -> list[bool]:
    """Map a closed-HTF EMA predicate onto each 1H bar — no lookahead.

    pred='gt' → close > EMA. pred='lt' → close < EMA (flip).
    For a closed 1H bar, use the last **closed** HTF bar with
    ts_close_ms <= 1H.ts_close_ms. In-progress HTF is never used.
    """
    n = len(bars_1h)
    if n == 0:
        return []
    closed_htf = [b for b in bars_htf if b.closed]
    if not closed_htf:
        return [False] * n
    closes = [float(b.close) for b in closed_htf]
    emas = ema_series(closes, ema_period)
    flag_at_htf: list[bool] = []
    for i, b in enumerate(closed_htf):
        ema = emas[i]
        if ema is None:
            flag_at_htf.append(False)
        elif pred == "gt":
            flag_at_htf.append(float(b.close) > float(ema))
        else:
            flag_at_htf.append(float(b.close) < float(ema))
    out: list[bool] = []
    j = -1
    for d in bars_1h:
        while j + 1 < len(closed_htf) and closed_htf[j + 1].ts_close_ms <= d.ts_close_ms:
            j += 1
        out.append(False if j < 0 else flag_at_htf[j])
    return out


def regime_ok_series_4h_ema21(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    *,
    ema_period: int = EMA_4H,
) -> list[bool]:
    """4H close > EMA(ema_period) mapped onto each 1H bar — entry filter."""
    return map_htf_predicate_to_1h(bars_1h, bars_4h, ema_period=ema_period, pred="gt")


def regime_flip_series_4h_ema21(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    *,
    ema_period: int = EMA_4H,
) -> list[bool]:
    """4H close < EMA(ema_period) — honesty/tests only. Walker ignores."""
    return map_htf_predicate_to_1h(bars_1h, bars_4h, ema_period=ema_period, pred="lt")


def regime_flip_series_1d_ema21(
    bars_1h: Sequence[Bar],
    bars_1d: Sequence[Bar],
    *,
    ema_period: int = EMA_1D,
) -> list[bool]:
    """1D close < EMA(ema_period) mapped onto each 1H bar — no lookahead.

    Signal on the 1H whose close is >= that 1D close; fill next 1H open.
    """
    return map_htf_predicate_to_1h(bars_1h, bars_1d, ema_period=ema_period, pred="lt")


__all__ = [
    "ATR_N",
    "CELL_TO_FAMILY",
    "CELL_TO_PARENT",
    "EMA_1D",
    "EMA_4H",
    "FAMILY_TO_CELL",
    "FORBIDDEN_CELLS",
    "NO_4H_EMA_FLIP_EXIT",
    "NO_ATR_TRAIL",
    "NO_R_TP",
    "NO_SELLLINE_EXIT",
    "OFFICIAL_CELLS",
    "OFFICIAL_FAMILIES",
    "Scalp136Signals",
    "TIME_STOP",
    "map_htf_predicate_to_1h",
    "regime_flip_series_1d_ema21",
    "regime_flip_series_4h_ema21",
    "regime_ok_series_4h_ema21",
]
