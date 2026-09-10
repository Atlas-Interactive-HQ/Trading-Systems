"""Mid BTC-USDT 1D Donchian long-only + EMA12/30 regime.

NEW family vs Mid daily pullback (#38 FAIL). Research only. not_a_forecast.
Never shorts. Never places orders. Do not param-grind.

LOCKED rule card (Kaje 2026-09-10):
  Bar: spot BTC-USDT 1D.
  Regime: NEW entries only if EMA12 > EMA30 on the signal day (closed).
  Entry: close > prior 20-day high (Donchian breakout up). Long only.
  Exit (no ATR knob this trial):
    - close < prior 10-day low (Donchian), fill next open via exit_hint; AND/OR
    - EMA12 ≤ EMA30 (regime flat), fill next open via exit_hint; AND/OR
    - time stop 15 trading days (engine).
  Structural stop for 1.5% risk sizing / engine protective floor = prior 10-day
  low at signal (NOT an ATR stop; NOT a dual knob). Soft Donchian exit trails
  via updated prior 10-low on later closes.
  Fill: signal close → next open.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, Side, Signal
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.ema_trend import ema_series

LONG = "long"
FLAT = "flat"

ENTRY_LOOKBACK = 20
EXIT_LOOKBACK = 10
EMA_FAST = 12
EMA_SLOW = 30
TIME_STOP_BARS = 15


@dataclass(frozen=True)
class MidBtcDonchianEmaParams:
    ema_fast: int = EMA_FAST
    ema_slow: int = EMA_SLOW
    entry_lookback: int = ENTRY_LOOKBACK
    exit_lookback: int = EXIT_LOOKBACK
    confirm_closed_only: bool = True
    sleeve: str = "mid"


def regime_state(bars: Sequence[Bar], *, fast: int = EMA_FAST, slow: int = EMA_SLOW) -> str:
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


class MidBtcDonchianEmaV1:
    """Donchian 20/10 breakout long gated by EMA12/30. Never emits short.

    Engine interface mirrors MidDailyPullbackV1: on_closed_bar on 1D stream;
    bars_1h unused. No ATR stop / no TP — exits are Donchian / regime / time.
    """

    def __init__(self, params: MidBtcDonchianEmaParams | None = None) -> None:
        self.params = params or MidBtcDonchianEmaParams()
        p = self.params
        if p.ema_fast < 1 or p.ema_slow < 1:
            raise ValueError("EMA periods must be >= 1")
        if p.ema_fast >= p.ema_slow:
            raise ValueError("fast EMA period must be < slow")
        if p.entry_lookback < 1 or p.exit_lookback < 1:
            raise ValueError("Donchian lookbacks must be >= 1")

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"mid_btc_donchian_ema_{p.sleeve}_"
            f"e{p.entry_lookback}_x{p.exit_lookback}_"
            f"ema{p.ema_fast}_{p.ema_slow}"
        )

    def warmup_bars(self) -> int:
        p = self.params
        return max(p.ema_slow, p.entry_lookback + 1, p.exit_lookback + 1) + 2

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
        e12, e30 = ema12[-1], ema30[-1]
        if e12 is None or e30 is None:
            return None

        ch_entry = donchian_prior(bars_1d, p.entry_lookback)
        if ch_entry is None:
            return None
        prior_high, _ = ch_entry
        close = float(last.close)
        if close <= 0 or close <= float(prior_high):
            return None

        ch_exit = donchian_prior(bars_1d, p.exit_lookback)
        if ch_exit is None:
            return None
        _, prior_low = ch_exit
        stop = float(prior_low)
        # Structural sizing / protective floor only — not ATR.
        if stop <= 0 or stop >= close:
            return None

        return Signal(
            symbol=last.symbol,
            side=Side.LONG,
            stop=stop,
            reason="mid_btc_donchian_breakout",
            bar_ts_ms=last.ts_close_ms,
            extras={
                "close": close,
                "ema12": float(e12),
                "ema30": float(e30),
                "prior_20_high": float(prior_high),
                "prior_10_low": float(prior_low),
                "entry_lookback": int(p.entry_lookback),
                "exit_lookback": int(p.exit_lookback),
                "sleeve": p.sleeve,
                "regime": LONG,
                "bar": "1D",
                "atr_stop": False,
                "take_profit": 0.0,
                "structural_stop": "prior_10_low_at_entry",
            },
        )

    def exit_hint(
        self,
        position_side: Side,
        bars_1d: Sequence[Bar],
    ) -> str | None:
        """Exit next open on Donchian 10-low close break or EMA regime flat."""
        if position_side is not Side.LONG or not bars_1d:
            return None
        last = bars_1d[-1]
        if self.params.confirm_closed_only and not last.closed:
            return None
        if regime_state(
            bars_1d, fast=self.params.ema_fast, slow=self.params.ema_slow
        ) != LONG:
            return "regime_flat"
        ch = donchian_prior(bars_1d, self.params.exit_lookback)
        if ch is None:
            return None
        _prior_high, prior_low = ch
        if float(last.close) < float(prior_low):
            return "donchian_exit"
        return None


class TradeWindowGate:
    """Suppress NEW entries outside [trade_start_ms, trade_end_ms). Exits still work."""

    def __init__(
        self,
        inner: MidBtcDonchianEmaV1,
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
    def params(self) -> MidBtcDonchianEmaParams:
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
