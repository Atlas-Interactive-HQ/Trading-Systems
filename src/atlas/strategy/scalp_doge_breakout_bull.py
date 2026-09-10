"""Scalp DOGE-USDT 15m BreakoutV1 long-only + daily EMA12/30 bull filter (#46).

Research only. not_a_forecast. Never places orders.

LOCKED (#46):
  - Reuse BreakoutV1 plumbing (Donchian 16 / ATR SMA14 / oneh stub).
  - Long-only: short breakouts are ignored (never short).
  - Bull filter: NEW longs only when prior closed *daily* EMA12 > EMA30 on DOGE.
    Else flat / no entry (entry gate; mirrors PullbackLongV1 regime gate).
  - atr_stop_mult from research overlay (default 1.5 — do NOT mutate config/default.yaml).
  - Decision at closed 15m bar; engine fills next open (same as BreakoutV1 / ShadowEngine).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, Side, Signal
from atlas.strategy.breakout import BreakoutParams, BreakoutV1
from atlas.strategy.pullback import LONG, daily_regime_state


@dataclass(frozen=True)
class ScalpDogeBreakoutBullParams:
    """Research overlay — atr_stop_mult mirrors live default 1.5 unless labeled otherwise."""

    lookback_15m: int = 16
    atr_period: int = 14
    atr_stop_mult: float = 1.5  # research overlay; do not write into default.yaml
    min_atr_frac: float = 0.001
    oneh_filter: str = "stub"
    oneh_lookback: int = 12
    confirm_closed_only: bool = True
    ema_fast: int = 12
    ema_slow: int = 30
    sleeve: str = "scalp"


class ScalpDogeBreakoutBullV1:
    """BreakoutV1 long-only wrapped with daily EMA12/30 bull entry gate."""

    def __init__(
        self,
        params: ScalpDogeBreakoutBullParams | None = None,
        *,
        daily_bars: Sequence[Bar] | None = None,
    ) -> None:
        self.params = params or ScalpDogeBreakoutBullParams()
        p = self.params
        if p.ema_fast < 1 or p.ema_slow < 1 or p.ema_fast >= p.ema_slow:
            raise ValueError("ema_fast/ema_slow invalid")
        if p.atr_stop_mult <= 0:
            raise ValueError("atr_stop_mult must be > 0")
        self._daily: list[Bar] = list(daily_bars or [])
        self.inner = BreakoutV1(
            BreakoutParams(
                lookback_15m=p.lookback_15m,
                atr_period=p.atr_period,
                atr_stop_mult=p.atr_stop_mult,
                min_atr_frac=p.min_atr_frac,
                oneh_filter=p.oneh_filter,
                oneh_lookback=p.oneh_lookback,
                ranging=False,
                confirm_closed_only=p.confirm_closed_only,
            )
        )

    def set_daily_bars(self, daily_bars: Sequence[Bar]) -> None:
        self._daily = list(daily_bars)

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"scalp_doge_breakout_bull_atr{p.atr_stop_mult}"
            f"_ema{p.ema_fast}_{p.ema_slow}_long_only"
        )

    def warmup_bars(self) -> int:
        return self.inner.warmup_bars()

    def on_closed_bar(
        self,
        bars_15m: Sequence[Bar],
        bars_1h: Sequence[Bar] | None = None,
    ) -> Signal | None:
        p = self.params
        if not bars_15m:
            return None
        last = bars_15m[-1]
        if p.confirm_closed_only and not last.closed:
            return None

        # Daily bull gate — prior closed daily only. Fail closed → no entry.
        regime = daily_regime_state(
            self._daily,
            asof_ts_ms=last.ts_close_ms,
            fast=p.ema_fast,
            slow=p.ema_slow,
        )
        if regime != LONG:
            return None

        sig = self.inner.on_closed_bar(bars_15m, bars_1h)
        if sig is None:
            return None
        # Long-only: drop shorts.
        if sig.side is not Side.LONG:
            return None

        extras = dict(sig.extras or {})
        extras["bull_regime"] = LONG
        extras["daily_ema_fast"] = p.ema_fast
        extras["daily_ema_slow"] = p.ema_slow
        extras["long_only"] = True
        return Signal(
            symbol=sig.symbol,
            side=sig.side,
            stop=sig.stop,
            reason=f"{sig.reason}|bull_ema{p.ema_fast}_{p.ema_slow}",
            bar_ts_ms=sig.bar_ts_ms,
            extras=extras,
        )

    def exit_hint(
        self,
        position_side: Side,
        bars_15m: Sequence[Bar],
    ) -> str | None:
        """Reuse BreakoutV1 opposite-channel exit; never short so only LONG exits apply."""
        return self.inner.exit_hint(position_side, bars_15m)
