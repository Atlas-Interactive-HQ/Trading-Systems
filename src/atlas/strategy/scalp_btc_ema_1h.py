"""Scalp BTC-USDT 1H EMA12/30 long/flat + daily EMA12/30 bull entry gate (#50).

LOCKED Scalp #50. Same EMA12/30 long/flat spirit as Core / Mid #41 / Mid #45
but on **1H** bars at Scalp €20 for BTC, with **daily EMA12>EMA30 filter ON for new
longs** (bull focus — entry gate; mirrors #46 / #48 / PullbackLongV1). Reuses Scalp #48 harness.

Research only. not_a_forecast. Never shorts. Never places orders.
Do not grind EMA periods / TF / costs on FAIL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1
from atlas.strategy.pullback import daily_regime_state

FAST = 12
SLOW = 30
BAR = "1H"
FAMILY = "ema12_30_long_flat_1h_daily_bull"


@dataclass(frozen=True)
class ScalpBtcEma1hParams:
    fast: int = FAST
    slow: int = SLOW
    ema_fast_daily: int = FAST
    ema_slow_daily: int = SLOW
    confirm_closed_only: bool = True
    daily_bull_filter: bool = True  # ON for new longs (locked #50)
    sleeve: str = "scalp"
    bar: str = BAR


class ScalpBtcEma1hV1:
    """1H EMA12/30 long/flat with daily EMA bull entry gate. Never emits short.

    desired_state(bars_1h) returns the *1H* EMA state only. The daily bull
    filter is applied by the eval walk as an **entry gate for new longs**
    (while flat: enter only if 1H long AND daily bull; while long: exit when
    1H flips flat — daily flip alone does not force exit).
    """

    def __init__(
        self,
        params: ScalpBtcEma1hParams | None = None,
        *,
        daily_bars: Sequence[Bar] | None = None,
    ) -> None:
        self.params = params or ScalpBtcEma1hParams()
        p = self.params
        if p.fast < 1 or p.slow < 1 or p.fast >= p.slow:
            raise ValueError("fast/slow EMA invalid")
        if p.ema_fast_daily < 1 or p.ema_slow_daily < 1 or p.ema_fast_daily >= p.ema_slow_daily:
            raise ValueError("daily EMA periods invalid")
        self._daily: list[Bar] = list(daily_bars or [])
        self._inner = EmaTrendV1(
            EmaTrendParams(
                fast=p.fast,
                slow=p.slow,
                confirm_closed_only=p.confirm_closed_only,
            )
        )

    def set_daily_bars(self, daily_bars: Sequence[Bar]) -> None:
        self._daily = list(daily_bars)

    @property
    def label(self) -> str:
        p = self.params
        bull = "bull_on" if p.daily_bull_filter else "bull_off"
        return f"scalp_btc_ema_1h_{p.sleeve}_{p.fast}_{p.slow}_{bull}"

    def warmup_bars(self) -> int:
        return self._inner.warmup_bars()

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """1H EMA12/30 state only (daily gate applied in eval walk)."""
        return self._inner.desired_state(bars)

    def daily_bull(self, asof_ts_ms: int) -> bool:
        """True iff prior closed daily EMA12 > EMA30 (fail closed → False)."""
        p = self.params
        if not p.daily_bull_filter:
            return True
        return (
            daily_regime_state(
                self._daily,
                asof_ts_ms=asof_ts_ms,
                fast=p.ema_fast_daily,
                slow=p.ema_slow_daily,
            )
            == LONG
        )


__all__ = [
    "BAR",
    "FAMILY",
    "FAST",
    "FLAT",
    "LONG",
    "SLOW",
    "ScalpBtcEma1hParams",
    "ScalpBtcEma1hV1",
]
