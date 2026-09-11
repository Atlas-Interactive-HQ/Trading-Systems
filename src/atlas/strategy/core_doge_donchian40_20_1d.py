"""Core DOGE-USDT 1D Donchian 40/20 long/flat — Atlas vNext Core C1 (#84).

LOCKED Core C1 from phase1/84-atlas-trading-vnext.md:
  Entry: closed close > prior 40-bar high (DonchianHigh40). Long only.
  Exit: closed close < prior 20-bar low (DonchianLow20) → flat.
  No EMA / ADX / ATR (those are C2–C4). Never short. Never places orders.
Sleeve Core €140 on 1D. Do not grind Donchian N / TF / costs on FAIL.
Honesty: #70 was Donchian 20/10 FAIL; C1 (40/20) may also fail (eliminate-only).
not_a_forecast. Soft PASS ≠ Core-arm. config/default.yaml untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.donchian_trend import DonchianLongFlatV1, DonchianTrendParams
from atlas.strategy.ema_trend import FLAT, LONG

ENTRY_LOOKBACK = 40  # locked C1 — High40
EXIT_LOOKBACK = 20  # locked C1 — Low20
BAR = "1D"
FAMILY = "donchian40_20_long_flat_1d"
SLEEVE = "core"
LADDER_ID = "C1"


@dataclass(frozen=True)
class CoreDogeDonchian40201dParams:
    entry_lookback: int = ENTRY_LOOKBACK
    exit_lookback: int = EXIT_LOOKBACK
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class CoreDogeDonchian40201dV1:
    """Donchian 40/20 long/flat on DOGE-USDT 1D for Core sleeve (vNext C1).

    Thin Core wrapper around DonchianLongFlatV1 with locked 40/20 lookbacks.
    Rejects lookback / TF / sleeve sweeps (no grind on FAIL). Distinct from
    Core EMA12/30 C0 (#54) and Core Donchian 20/10 (#70 FAIL).
    """

    def __init__(self, params: CoreDogeDonchian40201dParams | None = None) -> None:
        self.params = params or CoreDogeDonchian40201dParams()
        p = self.params
        if p.entry_lookback != ENTRY_LOOKBACK or p.exit_lookback != EXIT_LOOKBACK:
            raise ValueError(
                f"lookback grind forbidden: locked C1 entry={ENTRY_LOOKBACK} "
                f"exit={EXIT_LOOKBACK}, got {p.entry_lookback}/{p.exit_lookback}"
            )
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked bar={BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
        self._inner = DonchianLongFlatV1(
            DonchianTrendParams(
                entry_lookback=p.entry_lookback,
                exit_lookback=p.exit_lookback,
                confirm_closed_only=p.confirm_closed_only,
            )
        )

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"core_doge_donchian40_20_1d_{p.sleeve}"
            f"_e{p.entry_lookback}_x{p.exit_lookback}"
        )

    def warmup_bars(self) -> int:
        return self._inner.warmup_bars()

    def desired_state(self, bars: Sequence[Bar]) -> str:
        return self._inner.desired_state(bars)


__all__ = [
    "BAR",
    "ENTRY_LOOKBACK",
    "EXIT_LOOKBACK",
    "FAMILY",
    "FLAT",
    "LADDER_ID",
    "LONG",
    "SLEEVE",
    "CoreDogeDonchian40201dParams",
    "CoreDogeDonchian40201dV1",
]
