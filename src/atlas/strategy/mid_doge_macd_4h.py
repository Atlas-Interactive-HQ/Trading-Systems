"""Mid DOGE-USDT 4H MACD(12,26,9) long/flat — rise_panel Mid #68.

LOCKED Mid #68. Canonical MACD paper rule: long on MACD×signal cross-up;
flat on cross-down. Never short. No RSI. No daily-bull. No EMA grind.
Research only. not_a_forecast. Never places orders.
Do not grind MACD periods / TF / costs on FAIL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.macd_trend import (
    DEFAULT_FAST,
    DEFAULT_SIGNAL,
    DEFAULT_SLOW,
    FLAT,
    LONG,
    MacdTrendParams,
    MacdTrendV1,
)

FAST = DEFAULT_FAST  # 12
SLOW = DEFAULT_SLOW  # 26
SIGNAL = DEFAULT_SIGNAL  # 9
BAR = "4H"
FAMILY = "macd12269_long_flat_4h"
SLEEVE = "mid"


@dataclass(frozen=True)
class MidDogeMacd4hParams:
    fast: int = FAST
    slow: int = SLOW
    signal: int = SIGNAL
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class MidDogeMacd4hV1:
    """MACD(12,26,9) long/flat on DOGE-USDT 4H for Mid sleeve. Never emits short.

    Used with walk_long_flat (signal close → next open). Full-sleeve sizing
    at Mid €40 is applied by the eval harness, not here.
    Rejects period / TF / sleeve sweeps (no grind on FAIL). No daily-bull / RSI.
    Distinct from Breakout #65, EMA12/21 #67, RSI MR #66, Donchian #64, EMA12/30 archive.
    """

    def __init__(self, params: MidDogeMacd4hParams | None = None) -> None:
        self.params = params or MidDogeMacd4hParams()
        p = self.params
        if p.fast != FAST or p.slow != SLOW or p.signal != SIGNAL:
            raise ValueError(
                f"period grind forbidden: locked MACD({FAST},{SLOW},{SIGNAL}), "
                f"got ({p.fast},{p.slow},{p.signal})"
            )
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked bar={BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
        self._inner = MacdTrendV1(
            MacdTrendParams(
                fast=p.fast,
                slow=p.slow,
                signal=p.signal,
                confirm_closed_only=p.confirm_closed_only,
            )
        )

    @property
    def label(self) -> str:
        p = self.params
        return f"mid_doge_macd_4h_{p.sleeve}_{p.fast}_{p.slow}_{p.signal}"

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
    "SIGNAL",
    "SLEEVE",
    "SLOW",
    "MidDogeMacd4hParams",
    "MidDogeMacd4hV1",
]
