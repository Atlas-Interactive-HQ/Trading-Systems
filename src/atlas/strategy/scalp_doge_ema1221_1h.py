"""Scalp DOGE-USDT 1H EMA12/21 long/flat — rise_panel Scalp #63.

LOCKED Scalp #63. Same EMA long/flat family as Mid/Scalp EMA twins but periods
**12/21** (NOT 12/30). Plain long/flat like Mid 4H style — **no** daily-bull,
**no** RSI. Research only. not_a_forecast. Never shorts. Never places orders.
Do not grind EMA periods / TF / costs on FAIL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

FAST = 12
SLOW = 21
BAR = "1H"
FAMILY = "ema12_21_long_flat_1h"
SLEEVE = "scalp"


@dataclass(frozen=True)
class ScalpDogeEma1221Params:
    fast: int = FAST
    slow: int = SLOW
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class ScalpDogeEma1221V1:
    """EMA12/21 long/flat on DOGE-USDT 1H for Scalp sleeve. Never emits short.

    Used with walk_long_flat (signal close → next open). Full-sleeve sizing
    at Scalp €20 is applied by the eval harness, not here.
    Rejects period / TF / sleeve sweeps (no grind on FAIL). No daily-bull / RSI.
    """

    def __init__(self, params: ScalpDogeEma1221Params | None = None) -> None:
        self.params = params or ScalpDogeEma1221Params()
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
        return f"scalp_doge_ema1221_1h_{p.sleeve}_{p.fast}_{p.slow}"

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
    "ScalpDogeEma1221Params",
    "ScalpDogeEma1221V1",
]
