"""Mid DOGE-USDT 4H EMA12/21 long/flat — rise_panel Mid #67.

LOCKED Mid #67. Plain EMA long/flat with periods **12/21** (NOT 12/30 archive).
No RSI. No daily-bull unless required (not required here). Never short.
Research only. not_a_forecast. Never places orders.
Do not grind EMA periods / TF / costs on FAIL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

FAST = 12
SLOW = 21
BAR = "4H"
FAMILY = "ema12_21_long_flat_4h"
SLEEVE = "mid"


@dataclass(frozen=True)
class MidDogeEma1221Params:
    fast: int = FAST
    slow: int = SLOW
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class MidDogeEma1221V1:
    """EMA12/21 long/flat on DOGE-USDT 4H for Mid sleeve. Never emits short.

    Used with walk_long_flat (signal close → next open). Full-sleeve sizing
    at Mid €40 is applied by the eval harness, not here.
    Rejects period / TF / sleeve sweeps (no grind on FAIL). No daily-bull / RSI.
    Distinct from Mid EMA12/30 archive, Breakout #65, RSI MR #66, Donchian #64.
    """

    def __init__(self, params: MidDogeEma1221Params | None = None) -> None:
        self.params = params or MidDogeEma1221Params()
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
        return f"mid_doge_ema1221_4h_{p.sleeve}_{p.fast}_{p.slow}"

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
    "MidDogeEma1221Params",
    "MidDogeEma1221V1",
]
