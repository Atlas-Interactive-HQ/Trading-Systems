"""Public-MD Scalp #127 — #126 + BOS follow-through + RSI 20–30 / ≥67.

BASE = #126 long-only (15m bull HH+HL only; no shorts; flat bear/unclear).

LOCKED DELTAS vs #126 (no grind):
  1) Stricter BOS: (a) closed 1m close > active 15m swing high AND
     (b) NEXT closed 1m close ≥ that BOS bar's close (follow-through).
     No first-touch / wick-only. Fill = open of bar after follow-through.
  2) 3m RSI(14) Wilder ENTRY band: long only if RSI ∈ [20, 30] inclusive
     on the 3m bar in force at the signal (replaces RSI>50).
  3) RSI EXIT: close long when 3m RSI ≥ 67 (first closed 3m ≥67; do not
     wait for 75 if RSI gaps through).

Keep: SL = last 15m swing low · TP 1.5R OR RSI-exit OR opposite BOS,
whichever first · 45×1m time stop · one entry per BOS/FT event · no re-entry
until new 15m swing · confirm_closed_only · €20 · 5+5 bps · no martingale ·
no leverage.

Reuse structure helpers from scalp_structure_bos_125. Do NOT edit 120–126.
Paper only. place_orders false. not_a_forecast. Soft PASS N/A ≠ arm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder
from atlas.strategy.scalp_structure_bos_125 import (
    BAR_ENTRY,
    BAR_RSI,
    BAR_STRUCTURE,
    BEAR,
    BULL,
    FLAT,
    LONG,
    PIVOT_N,
    R_MULTIPLE,
    RSI_PERIOD,
    SHORT,
    SLEEVE,
    TIME_STOP_BARS,
    Bias,
    EntryExitSignals,
    StructureState,
    SwingPoint,
    _map_htf_index,
    confirmed_swings,
    structure_from_swings,
    structure_series,
)

FAMILY = "structure_bos_15m_rsi3m_1m_long_only_ft_rsi_bands"
PHASE_DELTA = "bos_follow_through_rsi_entry_20_30_exit_67"
FAMILY_126 = "structure_bos_15m_rsi3m_1m_long_only"

# LOCKED #127 RSI band / exit (replaces #125/#126 RSI>50 entry)
RSI_ENTRY_LO = 20.0
RSI_ENTRY_HI = 30.0
RSI_EXIT_MIN = 67.0


@dataclass(frozen=True)
class StructureBos127Params:
    """#127 locks = #126 long-only + follow-through + RSI band/exit."""

    pivot_n: int = PIVOT_N
    rsi_period: int = RSI_PERIOD
    rsi_entry_lo: float = RSI_ENTRY_LO
    rsi_entry_hi: float = RSI_ENTRY_HI
    rsi_exit_min: float = RSI_EXIT_MIN
    r_multiple: float = R_MULTIPLE
    time_stop_bars: int = TIME_STOP_BARS
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar_entry: str = BAR_ENTRY
    bar_structure: str = BAR_STRUCTURE
    bar_rsi: str = BAR_RSI
    long_only: bool = True
    bos_follow_through: bool = True


def rsi_entry_band_allows(bias: Bias, rsi: float | None) -> bool:
    """Long-only: bull + RSI ∈ [20, 30] inclusive. Else False."""
    if bias != BULL or rsi is None:
        return False
    v = float(rsi)
    return RSI_ENTRY_LO <= v <= RSI_ENTRY_HI


def rsi_exit_triggered(rsi: float | None) -> bool:
    """True when closed 3m RSI ≥ 67 (honesty: gap through 67–75 still exits)."""
    if rsi is None:
        return False
    return float(rsi) >= RSI_EXIT_MIN


def precompute_entry_signals(
    bars_1m: Sequence[Bar],
    bars_15m: Sequence[Bar],
    bars_3m: Sequence[Bar],
    *,
    params: StructureBos127Params | None = None,
) -> EntryExitSignals:
    """Causal long-only BOS + follow-through; RSI band at signal bar.

    Arm on bar i when closed 1m close > active 15m swing high (bull).
    Signal on bar i+1 when close ≥ BOS bar close AND RSI ∈ [20,30].
    Fill = open of bar after signal (walker next-open convention).
    One arm/attempt per swing_version; no shorts.
    """
    p = params or StructureBos127Params()
    if p.pivot_n != PIVOT_N:
        raise ValueError(f"pivot grind forbidden: locked N={PIVOT_N}, got {p.pivot_n}")
    if p.rsi_period != RSI_PERIOD:
        raise ValueError(
            f"RSI period grind forbidden: locked {RSI_PERIOD}, got {p.rsi_period}"
        )
    if float(p.r_multiple) != float(R_MULTIPLE):
        raise ValueError(
            f"R-multiple grind forbidden: locked {R_MULTIPLE}, got {p.r_multiple}"
        )
    if int(p.time_stop_bars) != TIME_STOP_BARS:
        raise ValueError(
            f"time-stop grind forbidden: locked {TIME_STOP_BARS}, got {p.time_stop_bars}"
        )
    if float(p.rsi_entry_lo) != float(RSI_ENTRY_LO) or float(p.rsi_entry_hi) != float(
        RSI_ENTRY_HI
    ):
        raise ValueError(
            f"RSI entry band grind forbidden: locked [{RSI_ENTRY_LO}, {RSI_ENTRY_HI}]"
        )
    if float(p.rsi_exit_min) != float(RSI_EXIT_MIN):
        raise ValueError(
            f"RSI exit grind forbidden: locked ≥{RSI_EXIT_MIN}, got {p.rsi_exit_min}"
        )
    if not p.long_only:
        raise ValueError("phase1/127 locked long_only=True")
    if not p.bos_follow_through:
        raise ValueError("phase1/127 locked bos_follow_through=True")

    n = len(bars_1m)
    entry_long = [False] * n
    entry_short = [False] * n
    bias_s: list[Bias] = [FLAT] * n
    rsi_s: list[float | None] = [None] * n
    ash: list[float | None] = [None] * n
    asl: list[float | None] = [None] * n
    sver: list[int] = [0] * n

    if n == 0:
        return EntryExitSignals(
            entry_long, entry_short, bias_s, rsi_s, ash, asl, sver, [None] * n
        )

    struct = structure_series(bars_15m, pivot_n=p.pivot_n)
    closes_3m = [float(b.close) for b in bars_3m]
    rsi_3m = rsi_wilder(closes_3m, p.rsi_period)

    # Consumed swing_version for long BOS attempts (arm consumes)
    last_long_bos_ver: int | None = None
    pending_bos_close: float | None = None
    pending_bos_ver: int | None = None
    pending_armed_at: int | None = None

    j15 = -1
    j3 = -1
    for i, bar in enumerate(bars_1m):
        if not bar.closed:
            continue
        decision_close = int(bar.ts_close_ms)
        j15 = _map_htf_index(decision_close, bars_15m, start_from=j15)
        j3 = _map_htf_index(decision_close, bars_3m, start_from=j3)
        if j15 < 0:
            continue
        st = struct[j15]
        bias_s[i] = st.bias
        ash[i] = st.last_swing_high
        asl[i] = st.last_swing_low
        sver[i] = st.swing_version
        rsi_val = rsi_3m[j3] if j3 >= 0 else None
        rsi_s[i] = None if rsi_val is None else q(float(rsi_val))
        c = float(bar.close)

        # --- follow-through on the bar immediately after arm ---
        if (
            pending_bos_close is not None
            and pending_armed_at is not None
            and i == pending_armed_at + 1
        ):
            same_ver = pending_bos_ver is not None and st.swing_version == pending_bos_ver
            ft_ok = c >= float(pending_bos_close)
            rsi_ok = rsi_entry_band_allows(st.bias, rsi_s[i])
            if same_ver and ft_ok and rsi_ok and st.bias == BULL:
                entry_long[i] = True
            # Clear one-shot arm (success or fail); version already consumed at arm
            pending_bos_close = None
            pending_bos_ver = None
            pending_armed_at = None
        elif pending_bos_close is not None and pending_armed_at is not None and i > pending_armed_at + 1:
            # Safety: stale arm
            pending_bos_close = None
            pending_bos_ver = None
            pending_armed_at = None

        # --- arm BOS: closed 1m close > active 15m swing high (bull only) ---
        if (
            pending_bos_close is None
            and st.bias == BULL
            and st.last_swing_high is not None
            and c > float(st.last_swing_high)
            and last_long_bos_ver != st.swing_version
        ):
            pending_bos_close = c
            pending_bos_ver = st.swing_version
            pending_armed_at = i
            last_long_bos_ver = st.swing_version  # one attempt per swing

    return EntryExitSignals(
        entry_long=entry_long,
        entry_short=entry_short,
        bias=bias_s,
        rsi=rsi_s,
        active_swing_high=ash,
        active_swing_low=asl,
        swing_version=sver,
        opposite_extreme=[None] * n,
    )


class StructureBos127V1:
    """#127 lock-card shell — long-only + follow-through + RSI bands."""

    def __init__(self, params: StructureBos127Params | None = None) -> None:
        self.params = params or StructureBos127Params()
        p = self.params
        if p.pivot_n != PIVOT_N:
            raise ValueError(f"pivot grind forbidden: locked N={PIVOT_N}")
        if p.rsi_period != RSI_PERIOD:
            raise ValueError(f"RSI period grind forbidden: locked {RSI_PERIOD}")
        if float(p.r_multiple) != float(R_MULTIPLE):
            raise ValueError(f"R-multiple grind forbidden: locked {R_MULTIPLE}")
        if int(p.time_stop_bars) != TIME_STOP_BARS:
            raise ValueError(f"time-stop grind forbidden: locked {TIME_STOP_BARS}")
        if float(p.rsi_entry_lo) != float(RSI_ENTRY_LO) or float(
            p.rsi_entry_hi
        ) != float(RSI_ENTRY_HI):
            raise ValueError(
                f"RSI entry band grind forbidden: locked [{RSI_ENTRY_LO}, {RSI_ENTRY_HI}]"
            )
        if float(p.rsi_exit_min) != float(RSI_EXIT_MIN):
            raise ValueError(f"RSI exit grind forbidden: locked ≥{RSI_EXIT_MIN}")
        if not p.long_only:
            raise ValueError(
                "phase1/127 locked long_only=True; do not restore shorts here"
            )
        if not p.bos_follow_through:
            raise ValueError("phase1/127 locked bos_follow_through=True")
        if p.bar_entry != BAR_ENTRY or p.bar_structure != BAR_STRUCTURE or p.bar_rsi != BAR_RSI:
            raise ValueError("TF grind forbidden: locked 15m / 3m / 1m")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}")
        if not p.confirm_closed_only:
            raise ValueError("confirm_closed_only locked True")

    @property
    def label(self) -> str:
        return (
            f"scalp_structure_bos_127_{self.params.sleeve}"
            f"_long_only_ft_rsi{int(self.params.rsi_entry_lo)}"
            f"-{int(self.params.rsi_entry_hi)}_x{int(self.params.rsi_exit_min)}"
            f"_n{self.params.pivot_n}_r{self.params.r_multiple:g}"
            f"_ts{self.params.time_stop_bars}"
        )


__all__ = [
    "BAR_ENTRY",
    "BAR_RSI",
    "BAR_STRUCTURE",
    "BEAR",
    "BULL",
    "FAMILY",
    "FAMILY_126",
    "FLAT",
    "LONG",
    "PHASE_DELTA",
    "PIVOT_N",
    "RSI_ENTRY_HI",
    "RSI_ENTRY_LO",
    "RSI_EXIT_MIN",
    "RSI_PERIOD",
    "R_MULTIPLE",
    "SHORT",
    "SLEEVE",
    "TIME_STOP_BARS",
    "Bias",
    "EntryExitSignals",
    "StructureBos127Params",
    "StructureBos127V1",
    "StructureState",
    "SwingPoint",
    "confirmed_swings",
    "precompute_entry_signals",
    "rsi_entry_band_allows",
    "rsi_exit_triggered",
    "structure_from_swings",
    "structure_series",
]
