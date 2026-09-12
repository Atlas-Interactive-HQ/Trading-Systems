"""Shared types for Public-MD Scalp #138 C1/C2/C3 regime-hold. Paper only.

C1 = 4H EMA21 regime-hold (no channel). C2 = 1D EMA21 regime-hold (no channel).
C3 = #137 N2 / #135 S2 Keltner entry + slower 1D EMA50 flip exit.
Exits: fixed SL · HTF regime flip → next 1H open · NO time-stop.
NO 1.5R. NO ATR trail. NO S4/D/J.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.scalp_136_common import (  # re-use 136 helpers; do not edit 136
    ATR_N,
    EMA_4H,
    NO_ATR_TRAIL,
    NO_R_TP,
    NO_SELLLINE_EXIT,
    map_htf_predicate_to_1h,
    regime_flip_series_1d_ema21,
    regime_flip_series_4h_ema21,
    regime_ok_series_4h_ema21,
)

EMA_1D = 21  # C2 entry/exit
EMA_1D_SLOW = 50  # C3 exit only (slower than EMA21)
ATR_SL_MULT = 3.0  # C1/C2: SL = entry − 3×ATR14(1H)
NO_4H_EMA_FLIP_EXIT = False  # C1 intentionally uses 4H flip; C2/C3 do not

# Walker requires a numeric cap: FULL 1H trade bars = 4416, so use >> that.
TIME_STOP_DISABLED = 100_000
TIME_STOP = TIME_STOP_DISABLED
NO_TIME_STOP = True


@dataclass(frozen=True)
class Scalp138Signals:
    """Per-1H-bar causal series for the #138 walker.

    entry_ok: long entry on closed 1H (fill next open).
    regime_flip: active HTF flip exit mapped onto 1H (C1=4H EMA21 lt;
                 C2=1D EMA21 lt; C3=1D EMA50 lt).
    regime_flip_4h: 4H close < EMA21 — honesty/tests; walker uses only
                    regime_flip for the active cell exit.
    sl_ref: fixed absolute SL (Keltner mid for C3); None for C1/C2 ATR-SL.
    atr: ATR14(1H) for C1/C2 SL = entry − 3×ATR at fill.
    """

    entry_ok: list[bool]
    regime_flip: list[bool]
    regime_flip_4h: list[bool]
    sl_ref: list[float | None]
    atr: list[float | None]


OFFICIAL_CELLS = ("C1", "C2", "C3")
OFFICIAL_FAMILIES = ("c1_4h", "c2_1d", "c3_keltner_ema50")
CELL_TO_FAMILY = {
    "C1": "c1_4h",
    "C2": "c2_1d",
    "C3": "c3_keltner_ema50",
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


__all__ = [
    "ATR_N",
    "ATR_SL_MULT",
    "CELL_TO_FAMILY",
    "EMA_1D",
    "EMA_1D_SLOW",
    "EMA_4H",
    "FAMILY_TO_CELL",
    "FORBIDDEN_CELLS",
    "NO_4H_EMA_FLIP_EXIT",
    "NO_ATR_TRAIL",
    "NO_R_TP",
    "NO_SELLLINE_EXIT",
    "NO_TIME_STOP",
    "OFFICIAL_CELLS",
    "OFFICIAL_FAMILIES",
    "Scalp138Signals",
    "TIME_STOP",
    "TIME_STOP_DISABLED",
    "map_htf_predicate_to_1h",
    "regime_flip_series_1d_ema",
    "regime_flip_series_1d_ema21",
    "regime_flip_series_4h_ema21",
    "regime_ok_series_1d_ema",
    "regime_ok_series_4h_ema21",
]
