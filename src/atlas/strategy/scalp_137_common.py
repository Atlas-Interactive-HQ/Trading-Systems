"""Shared types for Public-MD Scalp #137 N1/N2 1D EMA21-flip, NO time-stop. Paper only.

N1 = #136 L2 / #135 S3 Donchian entry. N2 = #136 L1 / #135 S2 Keltner entry.
Exits: fixed entry SL · 1D close < EMA21 → next 1H open · NO time-stop.
NO 1.5R. NO 4H EMA flip exit. NO ATR trail. NO S4/D/J.
"""

from __future__ import annotations

from atlas.strategy.scalp_136_common import (  # re-use 136 helpers; do not edit 136
    ATR_N,
    EMA_1D,
    EMA_4H,
    NO_4H_EMA_FLIP_EXIT,
    NO_ATR_TRAIL,
    NO_R_TP,
    NO_SELLLINE_EXIT,
    Scalp136Signals,
    map_htf_predicate_to_1h,
    regime_flip_series_1d_ema21,
    regime_flip_series_4h_ema21,
    regime_ok_series_4h_ema21,
)

# Alias for #137 naming (same signal dataclass shape as #136).
Scalp137Signals = Scalp136Signals

# Walker requires a numeric cap: FULL 1H trade bars = 4416, so use >> that.
# Time-stop must NOT fire in-window. Tests assert n_time_stop_exits == 0 on FULL.
TIME_STOP_DISABLED = 100_000
TIME_STOP = TIME_STOP_DISABLED  # locked: effectively no time-stop
NO_TIME_STOP = True

OFFICIAL_CELLS = ("N1", "N2")
OFFICIAL_FAMILIES = ("n1_donchian", "n2_keltner")
CELL_TO_FAMILY = {"N1": "n1_donchian", "N2": "n2_keltner"}
FAMILY_TO_CELL = {"n1_donchian": "N1", "n2_keltner": "N2"}
# Honesty parents
CELL_TO_PARENT = {"N1": "L2_136", "N2": "S2_135"}

FORBIDDEN_CELLS = frozenset(
    {
        "S4",
        "S1",
        "S2",
        "S3",
        "L1",
        "L2",
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
    "NO_TIME_STOP",
    "OFFICIAL_CELLS",
    "OFFICIAL_FAMILIES",
    "Scalp136Signals",
    "Scalp137Signals",
    "TIME_STOP",
    "TIME_STOP_DISABLED",
    "map_htf_predicate_to_1h",
    "regime_flip_series_1d_ema21",
    "regime_flip_series_4h_ema21",
    "regime_ok_series_4h_ema21",
]
