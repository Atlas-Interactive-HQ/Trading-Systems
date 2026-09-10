"""Mid DOGE-USDT 4H EMA12/30 long/flat — TF Mid ≠ 1D Core twin (#41).

LOCKED Mid #45. Same EMA12/30 long/flat rule as Core / mid_doge_ema_coregate (#41)
but on **4H** bars (not 1D). Research only. not_a_forecast. Never shorts.
Never places orders. Do not grind EMA periods / TF / costs on FAIL.

Thin wrapper around EmaTrendV1 so the trial has an explicit Mid #45 strategy
module; scoring lives in mid_doge_ema_4h_eval (core_style_return gate).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

FAST = 12
SLOW = 30
BAR = "4H"
FAMILY = "ema12_30_long_flat_4h"


@dataclass(frozen=True)
class MidDogeEma4hParams:
    fast: int = FAST
    slow: int = SLOW
    confirm_closed_only: bool = True
    sleeve: str = "mid"
    bar: str = BAR


class MidDogeEma4hV1:
    """EMA12/30 long/flat on DOGE-USDT 4H. Never emits short.

    Used with walk_long_flat (signal close → next open). Full-sleeve sizing
    at Mid €40 is applied by the eval harness, not here.
    """

    def __init__(self, params: MidDogeEma4hParams | None = None) -> None:
        self.params = params or MidDogeEma4hParams()
        p = self.params
        self._inner = EmaTrendV1(
            EmaTrendParams(
                fast=p.fast,
                slow=p.slow,
                confirm_closed_only=p.confirm_closed_only,
            )
        )

    @property
    def label(self) -> str:
        p = self.params
        return f"mid_doge_ema_4h_{p.sleeve}_{p.fast}_{p.slow}"

    def warmup_bars(self) -> int:
        return self._inner.warmup_bars()

    def desired_state(self, bars: Sequence[Bar]) -> str:
        return self._inner.desired_state(bars)


__all__ = [
    "BAR",
    "FAMILY",
    "FAST",
    "FLAT",
    "LONG",
    "SLOW",
    "MidDogeEma4hParams",
    "MidDogeEma4hV1",
]
