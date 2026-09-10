"""Mid DOGE-USDT 1D BreakoutV1 long-only + same-bar EMA12/30 bull filter (#47).

Research only. not_a_forecast. Never places orders.

LOCKED (#47):
  - Reuse BreakoutV1 plumbing (Donchian 16 / ATR SMA14 / atr_stop_mult overlay).
  - Long-only: short breakouts are ignored (never short).
  - Bull filter: NEW longs only when closed-bar *same-bar* daily EMA12 > EMA30.
    Else no entry. (Same decision bar — TF is already 1D.)
  - oneh_filter: off on 1D (bull EMA is the regime layer; no separate 1h stub).
  - atr_stop_mult from research overlay (default 1.5 — do NOT mutate config/default.yaml).
  - Decision at closed 1D bar; engine fills next open (BreakoutV1 / PaperEngine).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, Side, Signal
from atlas.strategy.breakout import BreakoutParams, BreakoutV1
from atlas.strategy.ema_trend import ema_series

LONG = "long"
FLAT = "flat"

LOOKBACK = 16
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5
EMA_FAST = 12
EMA_SLOW = 30
TIME_STOP_BARS = 16  # lookback-aligned on 1D
BAR = "1D"
FAMILY = "breakout_v1_long_bull_ema12_30_1d"


@dataclass(frozen=True)
class MidDogeBreakout1dParams:
    """Research overlay — atr_stop_mult mirrors live default 1.5 unless labeled otherwise."""

    lookback: int = LOOKBACK
    atr_period: int = ATR_PERIOD
    atr_stop_mult: float = ATR_STOP_MULT  # research overlay; do not write into default.yaml
    min_atr_frac: float = 0.001
    oneh_filter: str = "off"  # locked off on 1D — bull EMA is the regime layer
    confirm_closed_only: bool = True
    ema_fast: int = EMA_FAST
    ema_slow: int = EMA_SLOW
    sleeve: str = "mid"


def same_bar_ema_bull(bars_1d: Sequence[Bar], *, fast: int = 12, slow: int = 30) -> str:
    """EMA12 vs EMA30 on the closed decision bar (includes last close). Fail closed → flat."""
    if not bars_1d:
        return FLAT
    last = bars_1d[-1]
    if not last.closed:
        return FLAT
    if len(bars_1d) < slow:
        return FLAT
    closes = [float(b.close) for b in bars_1d]
    f_s = ema_series(closes, fast)
    s_s = ema_series(closes, slow)
    f, s = f_s[-1], s_s[-1]
    if f is None or s is None:
        return FLAT
    return LONG if f > s else FLAT


class MidDogeBreakout1dV1:
    """BreakoutV1 long-only on 1D wrapped with same-bar EMA12/30 bull entry gate."""

    def __init__(self, params: MidDogeBreakout1dParams | None = None) -> None:
        self.params = params or MidDogeBreakout1dParams()
        p = self.params
        if p.ema_fast < 1 or p.ema_slow < 1 or p.ema_fast >= p.ema_slow:
            raise ValueError("ema_fast/ema_slow invalid")
        if p.atr_stop_mult <= 0:
            raise ValueError("atr_stop_mult must be > 0")
        if p.lookback < 1 or p.atr_period < 1:
            raise ValueError("lookback and atr_period must be >= 1")
        if p.oneh_filter != "off":
            raise ValueError("oneh_filter must be 'off' for Mid 1D breakout (#47)")
        self.inner = BreakoutV1(
            BreakoutParams(
                lookback_15m=p.lookback,
                atr_period=p.atr_period,
                atr_stop_mult=p.atr_stop_mult,
                min_atr_frac=p.min_atr_frac,
                oneh_filter="off",
                ranging=False,
                confirm_closed_only=p.confirm_closed_only,
            )
        )

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"mid_doge_breakout_1d_atr{p.atr_stop_mult}"
            f"_ema{p.ema_fast}_{p.ema_slow}_long_only"
        )

    def warmup_bars(self) -> int:
        p = self.params
        return max(self.inner.warmup_bars(), p.ema_slow) + 1

    def on_closed_bar(
        self,
        bars_1d: Sequence[Bar],
        bars_1h: Sequence[Bar] | None = None,
    ) -> Signal | None:
        _ = bars_1h  # unused; oneh_filter locked off
        p = self.params
        if not bars_1d:
            return None
        last = bars_1d[-1]
        if p.confirm_closed_only and not last.closed:
            return None

        # Same-bar bull gate — includes decision-bar close. Fail closed → no entry.
        if same_bar_ema_bull(bars_1d, fast=p.ema_fast, slow=p.ema_slow) != LONG:
            return None

        sig = self.inner.on_closed_bar(bars_1d, None)
        if sig is None:
            return None
        # Long-only: drop shorts.
        if sig.side is not Side.LONG:
            return None

        extras = dict(sig.extras or {})
        extras["bull_regime"] = LONG
        extras["bull_filter"] = "same_bar_ema"
        extras["daily_ema_fast"] = p.ema_fast
        extras["daily_ema_slow"] = p.ema_slow
        extras["long_only"] = True
        extras["bar"] = BAR
        extras["sleeve"] = p.sleeve
        return Signal(
            symbol=sig.symbol,
            side=sig.side,
            stop=sig.stop,
            reason=f"{sig.reason}|bull_ema{p.ema_fast}_{p.ema_slow}_same_bar",
            bar_ts_ms=sig.bar_ts_ms,
            extras=extras,
        )

    def exit_hint(
        self,
        position_side: Side,
        bars_1d: Sequence[Bar],
    ) -> str | None:
        """Reuse BreakoutV1 opposite-channel exit; never short so only LONG exits apply."""
        return self.inner.exit_hint(position_side, bars_1d)


class TradeWindowGate:
    """Suppress NEW entries outside [trade_start_ms, trade_end_ms). Exits still work."""

    def __init__(
        self,
        inner: MidDogeBreakout1dV1,
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
    def params(self) -> MidDogeBreakout1dParams:
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
