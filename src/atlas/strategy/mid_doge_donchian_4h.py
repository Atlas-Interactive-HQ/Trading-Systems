"""Mid DOGE-USDT 4H Donchian 20/10 long/flat — rise_panel Mid #64.

LOCKED Mid #64. Canonical paper Donchian (Mid #44 / DonchianLongFlatV1 / Scalp #61):
  Entry: closed close > prior 20-bar high (breakout up). Long only.
  Exit: closed close < prior 10-bar low → flat.
  No EMA filter. Never short. Never places orders. not_a_forecast.
Sleeve Mid €40 on 4H. Do not grind Donchian N / TF / costs on FAIL.
Do not re-grind EMA (Track A persist2 archived softer).
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
BAR = "4H"
FAMILY = "donchian20_10_long_flat_4h"
SLEEVE = "mid"


@dataclass(frozen=True)
class MidDogeDonchian4hParams:
    entry_lookback: int = ENTRY_LOOKBACK
    exit_lookback: int = EXIT_LOOKBACK
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class MidDogeDonchian4hV1:
    """Donchian 20/10 long/flat on DOGE-USDT 4H for Mid sleeve.

    Thin Mid wrapper around canonical DonchianLongFlatV1 (same entry/exit
    confirms as Scalp #61 / Mid #44 paper rule). Used with walk_long_flat
    (signal close → next open). Full-sleeve sizing at Mid €40 is applied by
    the eval harness. Rejects lookback / TF / sleeve sweeps (no grind on FAIL).
    """

    def __init__(self, params: MidDogeDonchian4hParams | None = None) -> None:
        self.params = params or MidDogeDonchian4hParams()
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
            f"mid_doge_donchian_4h_{p.sleeve}"
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
    "MidDogeDonchian4hParams",
    "MidDogeDonchian4hV1",
]
