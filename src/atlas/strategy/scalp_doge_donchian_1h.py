"""Scalp DOGE-USDT 1H Donchian 20/10 long/flat — rise_panel Scalp #61.

LOCKED Scalp #61. Canonical paper Donchian (Mid #44 / DonchianLongFlatV1 spirit):
  Entry: closed close > prior 20-bar high (breakout up). Long only.
  Exit: closed close < prior 10-bar low → flat.
  No EMA filter. Never short. Never places orders. not_a_forecast.
Sleeve Scalp €20. Do not grind Donchian N / TF / costs on FAIL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.donchian_trend import (
    ENTRY_LOOKBACK as CANON_ENTRY,
    EXIT_LOOKBACK as CANON_EXIT,
    DonchianLongFlatV1,
    DonchianTrendParams,
)
from atlas.strategy.ema_trend import FLAT, LONG

ENTRY_LOOKBACK = CANON_ENTRY  # 20
EXIT_LOOKBACK = CANON_EXIT  # 10
BAR = "1H"
FAMILY = "donchian20_10_long_flat_1h"
SLEEVE = "scalp"


@dataclass(frozen=True)
class ScalpDogeDonchian1hParams:
    entry_lookback: int = ENTRY_LOOKBACK
    exit_lookback: int = EXIT_LOOKBACK
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class ScalpDogeDonchian1hV1:
    """Donchian 20/10 long/flat on DOGE-USDT 1H for Scalp sleeve.

    Thin Scalp wrapper around canonical DonchianLongFlatV1 (same entry/exit
    confirms as Mid #44 paper rule). Used with walk_long_flat (signal close →
    next open). Full-sleeve sizing at Scalp €20 is applied by the eval harness.
    Rejects lookback / TF / sleeve sweeps (no grind on FAIL).
    """

    def __init__(self, params: ScalpDogeDonchian1hParams | None = None) -> None:
        self.params = params or ScalpDogeDonchian1hParams()
        p = self.params
        if p.entry_lookback != ENTRY_LOOKBACK or p.exit_lookback != EXIT_LOOKBACK:
            raise ValueError(
                f"lookback grind forbidden: locked entry={ENTRY_LOOKBACK} "
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
            f"scalp_doge_donchian_1h_{p.sleeve}"
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
    "LONG",
    "SLEEVE",
    "ScalpDogeDonchian1hParams",
    "ScalpDogeDonchian1hV1",
]
