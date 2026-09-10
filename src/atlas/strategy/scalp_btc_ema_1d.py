"""Scalp BTC-USDT 1D EMA12/30 long/flat — Mid #51 twin at Scalp €20.

LOCKED Scalp #53. Same EMA12/30 long/flat rule as Mid #51 / EmaTrendV1 /
walk_long_flat on **BTC-USDT 1D**, scaled to Scalp sleeve. Research only.
not_a_forecast. Never shorts. Never places orders. BTC = research-only for live.
Do not grind EMA periods / TF / asset / costs on FAIL.

Thin wrapper around EmaTrendV1 so the trial has an explicit Scalp #53 strategy
module; scoring lives in scalp_btc_ema_1d_eval (core_style_return gate).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

FAST = 12
SLOW = 30
BAR = "1D"
FAMILY = "ema12_30_long_flat_1d"


@dataclass(frozen=True)
class ScalpBtcEma1dParams:
    fast: int = FAST
    slow: int = SLOW
    confirm_closed_only: bool = True
    sleeve: str = "scalp"
    bar: str = BAR


class ScalpBtcEma1dV1:
    """EMA12/30 long/flat on BTC-USDT 1D. Never emits short.

    Used with walk_long_flat (signal close → next open). Full-sleeve sizing
    at Scalp €20 is applied by the eval harness, not here.
    """

    def __init__(self, params: ScalpBtcEma1dParams | None = None) -> None:
        self.params = params or ScalpBtcEma1dParams()
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
        return f"scalp_btc_ema_1d_{p.sleeve}_{p.fast}_{p.slow}"

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
    "ScalpBtcEma1dParams",
    "ScalpBtcEma1dV1",
]
