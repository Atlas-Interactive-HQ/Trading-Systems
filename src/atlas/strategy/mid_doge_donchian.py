"""Mid DOGE-USDT 1D Donchian 20/10 long/flat — NO EMA.

NEW family vs Core EMA12/30 and vs phase1/39 BTC Donchian+EMA.
Research only. not_a_forecast. Never shorts. Never places orders. Do not param-grind.

LOCKED rule card (Kaje Mid #42):
  Bar: spot DOGE-USDT 1D.
  Entry: close > prior 20-day high (Donchian breakout up). Long only.
  Exit (NO EMA regime filter/exit; NO ATR knob):
    - close < prior 10-day low (Donchian), fill next open via exit_hint; AND/OR
    - time stop 15 trading days (engine; match mid_btc_donchian_ema TIME_STOP_BARS).
  Structural stop for 1.5% risk sizing / engine protective floor = prior 10-day
  low at signal (NOT an ATR stop). Soft Donchian exit trails via updated prior
  10-low on later closes.
  Fill: signal close → next open.
  Scalp OUT. Mid €40 sleeve.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, Side, Signal
from atlas.strategy.breakout import donchian_prior

ENTRY_LOOKBACK = 20
EXIT_LOOKBACK = 10
TIME_STOP_BARS = 15


@dataclass(frozen=True)
class MidDogeDonchianParams:
    entry_lookback: int = ENTRY_LOOKBACK
    exit_lookback: int = EXIT_LOOKBACK
    confirm_closed_only: bool = True
    sleeve: str = "mid"


class MidDogeDonchianV1:
    """Donchian 20/10 breakout long on DOGE-USDT 1D. Never emits short. No EMA.

    Engine interface mirrors MidBtcDonchianEmaV1 without regime filter/exit:
    on_closed_bar on 1D stream; bars_1h unused. No ATR stop / no TP —
    exits are Donchian / time only.
    """

    def __init__(self, params: MidDogeDonchianParams | None = None) -> None:
        self.params = params or MidDogeDonchianParams()
        p = self.params
        if p.entry_lookback < 1 or p.exit_lookback < 1:
            raise ValueError("Donchian lookbacks must be >= 1")

    @property
    def label(self) -> str:
        p = self.params
        return f"mid_doge_donchian_{p.sleeve}_e{p.entry_lookback}_x{p.exit_lookback}"

    def warmup_bars(self) -> int:
        p = self.params
        return max(p.entry_lookback + 1, p.exit_lookback + 1) + 2

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
            reason="mid_doge_donchian_breakout",
            bar_ts_ms=last.ts_close_ms,
            extras={
                "close": close,
                "prior_20_high": float(prior_high),
                "prior_10_low": float(prior_low),
                "entry_lookback": int(p.entry_lookback),
                "exit_lookback": int(p.exit_lookback),
                "sleeve": p.sleeve,
                "bar": "1D",
                "atr_stop": False,
                "take_profit": 0.0,
                "structural_stop": "prior_10_low_at_entry",
                "ema_regime": False,
            },
        )

    def exit_hint(
        self,
        position_side: Side,
        bars_1d: Sequence[Bar],
    ) -> str | None:
        """Exit next open on Donchian 10-low close break. No EMA regime exit."""
        if position_side is not Side.LONG or not bars_1d:
            return None
        last = bars_1d[-1]
        if self.params.confirm_closed_only and not last.closed:
            return None
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
        inner: MidDogeDonchianV1,
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
    def params(self) -> MidDogeDonchianParams:
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
