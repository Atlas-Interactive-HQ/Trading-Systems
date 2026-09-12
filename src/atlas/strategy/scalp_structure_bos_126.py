"""Public-MD Scalp #126 — #125 long-only strengthen (15m-bull only).

LOCKED DELTA vs #125: long_only=True → trade ONLY when 15m structure is bull
(HH+HL). NO shorts. Flat when bear or unclear/mixed.

Everything else IDENTICAL to #125 — reuses atlas.strategy.scalp_structure_bos_125
(precompute + locks). Do NOT copy-paste grind. Do NOT edit 120–125.

Keep from #125: pivot N=3 · 3m RSI(14)>50 for long · 1m BOS · one entry/BOS ·
SL last swing low · TP 1.5R or opposite BOS · 45×1m time stop · confirm_closed_only.

Doctrine: loose/independent Scalp sleeve. Paper only. place_orders false.
not_a_forecast. Soft PASS N/A ≠ arm. No RSI/pivot/TF grind. No short-restore.
"""

from __future__ import annotations

from dataclasses import dataclass

from atlas.strategy.scalp_structure_bos_125 import (
    BAR_ENTRY,
    BAR_RSI,
    BAR_STRUCTURE,
    BEAR,
    BULL,
    FAMILY as FAMILY_125,
    FLAT,
    LONG,
    PIVOT_N,
    R_MULTIPLE,
    RSI_LONG_MIN,
    RSI_PERIOD,
    RSI_SHORT_MAX,
    SHORT,
    SLEEVE,
    TIME_STOP_BARS,
    Bias,
    EntryExitSignals,
    StructureBos125Params,
    StructureBos125V1,
    StructureState,
    SwingPoint,
    confirmed_swings,
    precompute_entry_signals as precompute_entry_signals_125,
    rsi_allows,
    structure_from_swings,
    structure_series,
)

FAMILY = "structure_bos_15m_rsi3m_1m_long_only"
PHASE_DELTA = "long_only_15m_bull"


@dataclass(frozen=True)
class StructureBos126Params:
    """#126 params = #125 locks + long_only flag (default True)."""

    pivot_n: int = PIVOT_N
    rsi_period: int = RSI_PERIOD
    rsi_long_min: float = RSI_LONG_MIN
    rsi_short_max: float = RSI_SHORT_MAX
    r_multiple: float = R_MULTIPLE
    time_stop_bars: int = TIME_STOP_BARS
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar_entry: str = BAR_ENTRY
    bar_structure: str = BAR_STRUCTURE
    bar_rsi: str = BAR_RSI
    long_only: bool = True  # LOCKED DELTA vs #125

    def as_125(self) -> StructureBos125Params:
        return StructureBos125Params(
            pivot_n=self.pivot_n,
            rsi_period=self.rsi_period,
            rsi_long_min=self.rsi_long_min,
            rsi_short_max=self.rsi_short_max,
            r_multiple=self.r_multiple,
            time_stop_bars=self.time_stop_bars,
            confirm_closed_only=self.confirm_closed_only,
            sleeve=self.sleeve,
            bar_entry=self.bar_entry,
            bar_structure=self.bar_structure,
            bar_rsi=self.bar_rsi,
        )


def apply_long_only(signals: EntryExitSignals) -> EntryExitSignals:
    """Zero all short entries — flat on bear / mixed; keep bull longs."""
    n = len(signals.entry_short)
    return EntryExitSignals(
        entry_long=list(signals.entry_long),
        entry_short=[False] * n,
        bias=list(signals.bias),
        rsi=list(signals.rsi),
        active_swing_high=list(signals.active_swing_high),
        active_swing_low=list(signals.active_swing_low),
        swing_version=list(signals.swing_version),
        opposite_extreme=list(signals.opposite_extreme),
    )


def precompute_entry_signals(
    bars_1m,
    bars_15m,
    bars_3m,
    *,
    params: StructureBos126Params | StructureBos125Params | None = None,
    long_only: bool | None = None,
) -> EntryExitSignals:
    """Reuse #125 precompute; when long_only (default True) strip all shorts."""
    if isinstance(params, StructureBos126Params):
        p126 = params
        p125 = params.as_125()
        lo = p126.long_only if long_only is None else bool(long_only)
    elif isinstance(params, StructureBos125Params):
        p125 = params
        lo = True if long_only is None else bool(long_only)
    else:
        p126 = StructureBos126Params()
        p125 = p126.as_125()
        lo = p126.long_only if long_only is None else bool(long_only)

    sig = precompute_entry_signals_125(bars_1m, bars_15m, bars_3m, params=p125)
    if lo:
        return apply_long_only(sig)
    return sig


class StructureBos126V1:
    """#126 lock-card shell — #125 + long_only flag."""

    def __init__(self, params: StructureBos126Params | None = None) -> None:
        self.params = params or StructureBos126Params()
        p = self.params
        # Reuse #125 grind locks via StructureBos125V1
        StructureBos125V1(p.as_125())
        if not p.long_only:
            raise ValueError(
                "phase1/126 locked long_only=True (strengthen vs #125); "
                "do not restore shorts here"
            )
        if p.bar_entry != BAR_ENTRY or p.bar_structure != BAR_STRUCTURE or p.bar_rsi != BAR_RSI:
            raise ValueError("TF grind forbidden: locked 15m / 3m / 1m")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}")
        if not p.confirm_closed_only:
            raise ValueError("confirm_closed_only locked True")

    @property
    def label(self) -> str:
        return (
            f"scalp_structure_bos_126_{self.params.sleeve}"
            f"_long_only_n{self.params.pivot_n}_rsi{self.params.rsi_period}"
            f"_r{self.params.r_multiple:g}_ts{self.params.time_stop_bars}"
        )


__all__ = [
    "BAR_ENTRY",
    "BAR_RSI",
    "BAR_STRUCTURE",
    "BEAR",
    "BULL",
    "FAMILY",
    "FAMILY_125",
    "FLAT",
    "LONG",
    "PHASE_DELTA",
    "PIVOT_N",
    "RSI_LONG_MIN",
    "RSI_PERIOD",
    "RSI_SHORT_MAX",
    "R_MULTIPLE",
    "SHORT",
    "SLEEVE",
    "TIME_STOP_BARS",
    "Bias",
    "EntryExitSignals",
    "StructureBos125Params",
    "StructureBos126Params",
    "StructureBos126V1",
    "StructureState",
    "SwingPoint",
    "apply_long_only",
    "confirmed_swings",
    "precompute_entry_signals",
    "precompute_entry_signals_125",
    "rsi_allows",
    "structure_from_swings",
    "structure_series",
]
