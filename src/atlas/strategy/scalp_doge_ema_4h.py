"""Scalp DOGE-USDT 4H EMA12/30 long/flat — same family as Mid baseline, Scalp €20 (#57).

LOCKED Scalp improve #57. Same EMA12/30 long/flat rule as Mid
`rise_panel_v1_mid_doge_ema12_30_4h_eur40` but sleeve **Scalp €20** (not Mid €40).
Research only. not_a_forecast. Never shorts. Never places orders.
Do not grind EMA periods / TF / costs on FAIL.
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
SLEEVE = "scalp"


@dataclass(frozen=True)
class ScalpDogeEma4hParams:
    fast: int = FAST
    slow: int = SLOW
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class ScalpDogeEma4hV1:
    """EMA12/30 long/flat on DOGE-USDT 4H for Scalp sleeve. Never emits short.

    Used with walk_long_flat (signal close → next open). Full-sleeve sizing
    at Scalp €20 is applied by the eval harness, not here.
    Rejects period / TF / sleeve sweeps (no grind on FAIL).
    """

    def __init__(self, params: ScalpDogeEma4hParams | None = None) -> None:
        self.params = params or ScalpDogeEma4hParams()
        p = self.params
        if p.fast != FAST or p.slow != SLOW:
            raise ValueError(
                f"period grind forbidden: locked fast={FAST} slow={SLOW}, got {p.fast}/{p.slow}"
            )
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked bar={BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
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
        return f"scalp_doge_ema_4h_{p.sleeve}_{p.fast}_{p.slow}"

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
    "SLEEVE",
    "SLOW",
    "ScalpDogeEma4hParams",
    "ScalpDogeEma4hV1",
]
