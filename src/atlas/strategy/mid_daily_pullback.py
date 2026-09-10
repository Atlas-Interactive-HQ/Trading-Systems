"""Mid daily EMA pullback long — low-frequency sleeve alongside Core EMA.

Research only. not_a_forecast. Never shorts. Never places orders.

LOCKED (Kaje 2026-09-10):
  Bar: DOGE-USDT 1D (same family as Core EMA).
  Regime: NEW entries only if EMA12 > EMA30 on the signal day (closed).
  Entry: pullback reclaim — low ≤ EMA12 within the bar OR prior bar close < EMA12,
         AND signal close > EMA12 AND close > EMA30. Long only.
  Stop: entry_ref − 1.5 × ATR(14, daily); TP +2R; time stop 10 trading days.
  Regime exit: flatten if EMA12 ≤ EMA30 on a later close (fill next open).
  Fill: signal close → next open (EMA family).

Decision at closed bar; engine fills next open. ATR = SMA of true range
(same as BreakoutV1 / PullbackLongV1). Same bars + params → same Signal (or None).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, Side, Signal, q
from atlas.strategy.breakout import sma_atr
from atlas.strategy.ema_trend import ema_series

LONG = "long"
FLAT = "flat"


@dataclass(frozen=True)
class MidDailyPullbackParams:
    ema_fast: int = 12
    ema_slow: int = 30
    atr_period: int = 14
    atr_stop_mult: float = 1.5
    tp_r_multiple: float = 2.0
    confirm_closed_only: bool = True
    sleeve: str = "mid"


def regime_state(bars: Sequence[Bar], *, fast: int = 12, slow: int = 30) -> str:
    """EMA12 vs EMA30 on the last closed bar. Insufficient history → flat."""
    if len(bars) < slow:
        return FLAT
    last = bars[-1]
    if not last.closed:
        return FLAT
    closes = [float(b.close) for b in bars]
    f_s = ema_series(closes, fast)
    s_s = ema_series(closes, slow)
    f, s = f_s[-1], s_s[-1]
    if f is None or s is None:
        return FLAT
    return LONG if f > s else FLAT


class MidDailyPullbackV1:
    """Daily pullback long gated by same-day EMA12/30. Never emits short.

    Engine interface mirrors BreakoutV1 / PullbackLongV1: on_closed_bar receives
    the decision bar stream (here: 1D). bars_1h is unused.
    """

    def __init__(self, params: MidDailyPullbackParams | None = None) -> None:
        self.params = params or MidDailyPullbackParams()
        p = self.params
        if p.ema_fast < 1 or p.ema_slow < 1:
            raise ValueError("EMA periods must be >= 1")
        if p.ema_fast >= p.ema_slow:
            raise ValueError("fast EMA period must be < slow")
        if p.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if p.atr_stop_mult <= 0 or p.tp_r_multiple <= 0:
            raise ValueError("atr_stop_mult and tp_r_multiple must be > 0")

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"mid_daily_pullback_{p.sleeve}_atr{p.atr_stop_mult}_tp{p.tp_r_multiple}R"
        )

    def warmup_bars(self) -> int:
        p = self.params
        return max(p.ema_slow, p.atr_period + 1) + 2

    def on_closed_bar(
        self,
        bars_1d: Sequence[Bar],
        bars_1h: Sequence[Bar] | None = None,
    ) -> Signal | None:
        _ = bars_1h
        p = self.params
        if not bars_1d:
            return None
        last = bars_1d[-1]
        if p.confirm_closed_only and not last.closed:
            return None
        need = self.warmup_bars()
        if len(bars_1d) < need:
            return None
        for b in bars_1d[-need:]:
            b.validate()

        if regime_state(bars_1d, fast=p.ema_fast, slow=p.ema_slow) != LONG:
            return None

        closes = [float(b.close) for b in bars_1d]
        ema12 = ema_series(closes, p.ema_fast)
        ema30 = ema_series(closes, p.ema_slow)
        e12 = ema12[-1]
        e30 = ema30[-1]
        if e12 is None or e30 is None:
            return None
        close = float(last.close)
        if close <= 0:
            return None
        # Reclaim: close back above EMA12 and above EMA30
        if close <= float(e12) or close <= float(e30):
            return None

        # Pullback: low touched EMA12 this bar OR prior close was below its EMA12
        touched = float(last.low) <= float(e12)
        prior_below = False
        if len(bars_1d) >= 2:
            prior_e12 = ema12[-2]
            if prior_e12 is not None and float(bars_1d[-2].close) < float(prior_e12):
                prior_below = True
        if not (touched or prior_below):
            return None

        atr = sma_atr(bars_1d, p.atr_period)
        if atr is None or atr <= 0:
            return None

        stop_dist = float(atr) * float(p.atr_stop_mult)
        stop = close - stop_dist
        take_profit = close + float(p.tp_r_multiple) * stop_dist
        if stop <= 0 or take_profit <= close:
            return None

        return Signal(
            symbol=last.symbol,
            side=Side.LONG,
            stop=float(stop),
            reason="mid_daily_pullback_reclaim",
            bar_ts_ms=last.ts_close_ms,
            extras={
                "atr": float(atr),
                "close": close,
                "ema12": float(e12),
                "ema30": float(e30),
                "stop_dist": stop_dist,
                "take_profit": float(take_profit),
                "tp_r_multiple": float(p.tp_r_multiple),
                "atr_stop_mult": float(p.atr_stop_mult),
                "sleeve": p.sleeve,
                "regime": LONG,
                "pullback_touched": touched,
                "pullback_prior_below": prior_below,
                "bar": "1D",
            },
        )

    def exit_hint(
        self,
        position_side: Side,
        bars_1d: Sequence[Bar],
    ) -> str | None:
        """Exit when EMA12 ≤ EMA30 on a later closed bar (regime flat)."""
        if position_side is not Side.LONG or not bars_1d:
            return None
        if regime_state(
            bars_1d, fast=self.params.ema_fast, slow=self.params.ema_slow
        ) != LONG:
            return "regime_flat"
        return None


class TradeWindowGate:
    """Suppress NEW entries outside [trade_start_ms, trade_end_ms). Exits still work."""

    def __init__(
        self,
        inner: MidDailyPullbackV1,
        *,
        trade_start_ms: int,
        trade_end_ms: int,
    ) -> None:
        self.inner = inner
        self.trade_start_ms = int(trade_start_ms)
        self.trade_end_ms = int(trade_end_ms)

    @property
    def label(self) -> str:
        return self.inner.label

    @property
    def params(self) -> MidDailyPullbackParams:
        return self.inner.params

    def warmup_bars(self) -> int:
        return self.inner.warmup_bars()

    def on_closed_bar(
        self,
        bars_1d: Sequence[Bar],
        bars_1h: Sequence[Bar] | None = None,
    ) -> Signal | None:
        if not bars_1d:
            return None
        last = bars_1d[-1]
        if not (self.trade_start_ms <= last.ts_open_ms < self.trade_end_ms):
            return None
        return self.inner.on_closed_bar(bars_1d, bars_1h)

    def exit_hint(self, position_side: Side, bars_1d: Sequence[Bar]) -> str | None:
        return self.inner.exit_hint(position_side, bars_1d)
