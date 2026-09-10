"""Mid DOGE-USDT 1D RSI(14) mean-reversion long/flat.

NEW family vs Core EMA12/30, vs #42 Donchian, vs #41 core_style_return.
Research only. not_a_forecast. Never shorts. Never places orders. Do not param-grind.

LOCKED rule card (Kaje Mid #43):
  Bar: spot DOGE-USDT 1D.
  Entry: closed-bar RSI(14) < 30 → long. Long only.
  Exit: closed-bar RSI(14) > 50 → flat (fill next open via exit_hint).
  Structural stop for 1.5% risk sizing / engine protective floor = close − 10%
  at signal (NOT an ATR stop; NOT an RSI knob). Soft exit is RSI>50 only.
  NO time stop. NO take-profit.
  Fill: signal close → next open.
  Scalp OUT. Mid €40 sleeve.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, Side, Signal
RSI_PERIOD = 14
ENTRY_RSI = 30.0
EXIT_RSI = 50.0
# Engine requires int; hyp has NO time stop — keep inert (never fires in practice).
TIME_STOP_BARS = 10**9
# Fixed fraction below close for 1.5% risk sizing / protective floor only.
# (Prior N-day low is often ABOVE close on oversold dumps — unusable for long sizing.)
STRUCTURAL_STOP_FRAC = 0.10


def rsi_wilder(closes: Sequence[float], period: int = RSI_PERIOD) -> list[float | None]:
    """Wilder RSI series aligned to closes; None until first computable bar."""
    n = len(closes)
    out: list[float | None] = [None] * n
    if period < 1 or n < period + 1:
        return out

    def _rsi(avg_gain: float, avg_loss: float) -> float:
        if avg_loss <= 0.0 and avg_gain <= 0.0:
            return 50.0
        if avg_loss <= 0.0:
            return 100.0
        if avg_gain <= 0.0:
            return 0.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    gain_sum = 0.0
    loss_sum = 0.0
    for i in range(1, period + 1):
        d = float(closes[i]) - float(closes[i - 1])
        gain_sum += max(d, 0.0)
        loss_sum += max(-d, 0.0)
    avg_gain = gain_sum / period
    avg_loss = loss_sum / period
    out[period] = _rsi(avg_gain, avg_loss)

    for i in range(period + 1, n):
        d = float(closes[i]) - float(closes[i - 1])
        g = max(d, 0.0)
        loss = max(-d, 0.0)
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = _rsi(avg_gain, avg_loss)
    return out


@dataclass(frozen=True)
class MidDogeRsiMrParams:
    rsi_period: int = RSI_PERIOD
    entry_rsi: float = ENTRY_RSI
    exit_rsi: float = EXIT_RSI
    structural_stop_frac: float = STRUCTURAL_STOP_FRAC
    confirm_closed_only: bool = True
    sleeve: str = "mid"


class MidDogeRsiMrV1:
    """RSI(14) mean-reversion long on DOGE-USDT 1D. Never emits short.

    Engine interface mirrors MidDogeDonchianV1: on_closed_bar on 1D stream;
    bars_1h unused. No ATR stop / no TP — soft exit is RSI>50 only.
    """

    def __init__(self, params: MidDogeRsiMrParams | None = None) -> None:
        self.params = params or MidDogeRsiMrParams()
        p = self.params
        if p.rsi_period < 1:
            raise ValueError("rsi_period must be >= 1")
        if not (0.0 < p.entry_rsi < p.exit_rsi < 100.0):
            raise ValueError("need 0 < entry_rsi < exit_rsi < 100")
        if not (0.0 < p.structural_stop_frac < 1.0):
            raise ValueError("structural_stop_frac must be in (0, 1)")

    @property
    def label(self) -> str:
        p = self.params
        return f"mid_doge_rsi_mr_{p.sleeve}_rsi{p.rsi_period}_e{p.entry_rsi:g}_x{p.exit_rsi:g}"

    def warmup_bars(self) -> int:
        p = self.params
        return p.rsi_period + 3

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

        closes = [float(b.close) for b in bars_1d]
        rsi_s = rsi_wilder(closes, p.rsi_period)
        rsi = rsi_s[-1]
        if rsi is None:
            return None
        if float(rsi) >= float(p.entry_rsi):
            return None

        close = float(last.close)
        if close <= 0:
            return None

        stop = close * (1.0 - float(p.structural_stop_frac))
        # Structural sizing / protective floor only — soft exit is RSI>50.
        if stop <= 0 or stop >= close:
            return None

        return Signal(
            symbol=last.symbol,
            side=Side.LONG,
            stop=stop,
            reason="mid_doge_rsi_mr_oversold",
            bar_ts_ms=last.ts_close_ms,
            extras={
                "close": close,
                "rsi": float(rsi),
                "rsi_period": int(p.rsi_period),
                "entry_rsi": float(p.entry_rsi),
                "exit_rsi": float(p.exit_rsi),
                "structural_stop_frac": float(p.structural_stop_frac),
                "sleeve": p.sleeve,
                "bar": "1D",
                "atr_stop": False,
                "take_profit": 0.0,
                "structural_stop": "close_minus_10pct_at_entry",
                "time_stop": False,
                "ema_regime": False,
            },
        )

    def exit_hint(
        self,
        position_side: Side,
        bars_1d: Sequence[Bar],
    ) -> str | None:
        """Exit next open when closed-bar RSI(14) > 50."""
        if position_side is not Side.LONG or not bars_1d:
            return None
        last = bars_1d[-1]
        if self.params.confirm_closed_only and not last.closed:
            return None
        need = self.params.rsi_period + 1
        if len(bars_1d) < need:
            return None
        closes = [float(b.close) for b in bars_1d]
        rsi_s = rsi_wilder(closes, self.params.rsi_period)
        rsi = rsi_s[-1]
        if rsi is None:
            return None
        if float(rsi) > float(self.params.exit_rsi):
            return "rsi_exit"
        return None


class TradeWindowGate:
    """Suppress NEW entries outside [trade_start_ms, trade_end_ms). Exits still work."""

    def __init__(
        self,
        inner: MidDogeRsiMrV1,
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
    def params(self) -> MidDogeRsiMrParams:
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
