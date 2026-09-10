"""Mid DOGE-USDT 1H Donchian 20/10 long/flat — NO EMA.

TF-shift vs Mid #42 (1D) with SAME N 20/10. NOT a Donchian-N grind.
Research only. not_a_forecast. Never shorts. Never places orders. Do not param-grind.

LOCKED rule card (Kaje Mid #44):
  Bar: spot DOGE-USDT 1H (same calendar spans as #42/#43).
  Entry: close > prior 20-bar high (Donchian breakout up). Long only.
  Exit (NO EMA regime filter/exit; NO ATR knob):
    - close < prior 10-bar low (Donchian), fill next open via exit_hint; AND/OR
    - time stop 15 × 1H bars (engine; same bar-count as #42 TIME_STOP_BARS).
  Structural stop for 1.5% risk sizing / engine protective floor = prior 10-bar
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
TIME_STOP_BARS = 15  # same bar-count as #42; on 1H = 15 hours


@dataclass(frozen=True)
class MidDogeDonchian1hParams:
    entry_lookback: int = ENTRY_LOOKBACK
    exit_lookback: int = EXIT_LOOKBACK
    confirm_closed_only: bool = True
    sleeve: str = "mid"


class MidDogeDonchian1hV1:
    """Donchian 20/10 breakout long on DOGE-USDT 1H. Never emits short. No EMA.

    Engine interface mirrors MidDogeDonchianV1 (#42): on_closed_bar on primary
    stream (here 1H bars passed as the engine primary / bars_1d slot);
    bars_1h unused. No ATR stop / no TP — exits are Donchian / time only.
    """

    def __init__(self, params: MidDogeDonchian1hParams | None = None) -> None:
        self.params = params or MidDogeDonchian1hParams()
        p = self.params
        if p.entry_lookback < 1 or p.exit_lookback < 1:
            raise ValueError("Donchian lookbacks must be >= 1")

    @property
    def label(self) -> str:
        p = self.params
        return f"mid_doge_donchian_1h_{p.sleeve}_e{p.entry_lookback}_x{p.exit_lookback}"

    def warmup_bars(self) -> int:
        p = self.params
        return max(p.entry_lookback + 1, p.exit_lookback + 1) + 2

    def on_closed_bar(
        self,
        bars_1d: Sequence[Bar],
        bars_1h: Sequence[Bar] | None = None,
    ) -> Signal | None:
        # Primary stream is 1H for this trial (engine primary slot).
        _ = bars_1h
        bars = bars_1d
        p = self.params
        if not bars:
            return None
        last = bars[-1]
        if p.confirm_closed_only and not last.closed:
            return None
        need = self.warmup_bars()
        if len(bars) < need:
            return None
        for b in bars[-need:]:
            b.validate()

        ch_entry = donchian_prior(bars, p.entry_lookback)
        if ch_entry is None:
            return None
        prior_high, _ = ch_entry
        close = float(last.close)
        if close <= 0 or close <= float(prior_high):
            return None

        ch_exit = donchian_prior(bars, p.exit_lookback)
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
            reason="mid_doge_donchian_1h_breakout",
            bar_ts_ms=last.ts_close_ms,
            extras={
                "close": close,
                "prior_20_high": float(prior_high),
                "prior_10_low": float(prior_low),
                "entry_lookback": int(p.entry_lookback),
                "exit_lookback": int(p.exit_lookback),
                "sleeve": p.sleeve,
                "bar": "1H",
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
        inner: MidDogeDonchian1hV1,
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
    def params(self) -> MidDogeDonchian1hParams:
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
