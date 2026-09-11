"""Mid DOGE-USDT 4H BreakoutV1 + EMA12/21 + ADX(14)>20 — rise_panel Mid M1 (#86).

LOCKED Mid M1 (Atlas Trading vNext ladders #84). Strengthens #71 with ADX gate:
  Entry: BreakoutV1 break-up + ATR quiet AND EMA12 > EMA21 AND ADX14 > 20.
  Exit: BreakoutV1 channel exit OR EMA12 ≤ EMA21 OR ADX14 ≤ 20 → flat / no new long.
  Lookback=16; ATR SMA 14; min_atr_frac 0.001; EMA 12/21; ADX period 14 gate 20.
  Never short. Never places orders. not_a_forecast.
Sleeve Mid €40 (same as #71). Do NOT grind lookback / EMA / ATR / ADX / TF / costs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.adx import ADX_GATE_M1, ADX_PERIOD, wilder_adx_series
from atlas.strategy.breakout import BreakoutParams, BreakoutV1, donchian_prior, sma_atr
from atlas.strategy.ema_trend import FLAT, LONG, ema_series

LOOKBACK = 16
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5
MIN_ATR_FRAC = 0.001
EMA_FAST = 12
EMA_SLOW = 21
ADX_PERIOD_LOCKED = ADX_PERIOD  # 14
ADX_GATE = ADX_GATE_M1  # 20.0
BAR = "4H"
FAMILY = "breakout_v1_ema1221_adx14_gt20_long_regime_4h"
SLEEVE = "mid"


def _sma_atr_tail(bars: Sequence[Bar], period: int) -> float | None:
    need = period + 1
    if period < 1 or len(bars) < need:
        return None
    return sma_atr(bars[-need:], period)


@dataclass(frozen=True)
class MidDogeBreakoutEma1221AdxParams:
    lookback: int = LOOKBACK
    atr_period: int = ATR_PERIOD
    atr_stop_mult: float = ATR_STOP_MULT
    min_atr_frac: float = MIN_ATR_FRAC
    ema_fast: int = EMA_FAST
    ema_slow: int = EMA_SLOW
    adx_period: int = ADX_PERIOD_LOCKED
    adx_gate: float = ADX_GATE
    oneh_filter: str = "off"
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class MidDogeBreakoutEma1221AdxV1:
    """BreakoutV1 + EMA12/21 + ADX14>20 long-regime on DOGE-USDT 4H Mid (M1)."""

    def __init__(self, params: MidDogeBreakoutEma1221AdxParams | None = None) -> None:
        self.params = params or MidDogeBreakoutEma1221AdxParams()
        p = self.params
        if p.lookback != LOOKBACK:
            raise ValueError(
                f"lookback grind forbidden: locked lookback={LOOKBACK}, got {p.lookback}"
            )
        if p.atr_period != ATR_PERIOD:
            raise ValueError(
                f"atr_period grind forbidden: locked atr_period={ATR_PERIOD}, got {p.atr_period}"
            )
        if p.atr_stop_mult != ATR_STOP_MULT:
            raise ValueError(
                f"atr_stop_mult grind forbidden: locked={ATR_STOP_MULT}, got {p.atr_stop_mult}"
            )
        if p.min_atr_frac != MIN_ATR_FRAC:
            raise ValueError(
                f"min_atr_frac grind forbidden: locked={MIN_ATR_FRAC}, got {p.min_atr_frac}"
            )
        if int(p.ema_fast) != EMA_FAST or int(p.ema_slow) != EMA_SLOW:
            raise ValueError(
                f"EMA period grind forbidden: locked ema{EMA_FAST}/{EMA_SLOW}, "
                f"got ema{p.ema_fast}/{p.ema_slow}"
            )
        if int(p.adx_period) != ADX_PERIOD_LOCKED:
            raise ValueError(
                f"ADX period grind forbidden: locked adx_period={ADX_PERIOD_LOCKED}, "
                f"got {p.adx_period}"
            )
        if float(p.adx_gate) != float(ADX_GATE):
            raise ValueError(
                f"ADX gate grind forbidden: locked adx_gate={ADX_GATE}, got {p.adx_gate}"
            )
        if p.oneh_filter != "off":
            raise ValueError("oneh_filter must be 'off' for 4H Breakout+EMA1221+ADX (M1)")
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked bar={BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
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
            f"mid_doge_breakout_ema1221_adx_4h_{p.sleeve}"
            f"_lb{p.lookback}_atr{p.atr_period}_ema{p.ema_fast}_{p.ema_slow}"
            f"_adx{p.adx_period}_gt{int(p.adx_gate)}_long_flat"
        )

    def warmup_bars(self) -> int:
        p = self.params
        # Wilder ADX first value at ~2*period - 1
        return max(self.inner.warmup_bars(), int(p.ema_slow) + 1, 2 * int(p.adx_period))

    def desired_state(self, bars: Sequence[Bar]) -> str:
        p = self.params
        if not bars:
            return FLAT
        closes = [float(b.close) for b in bars]
        ema_f = ema_series(closes, p.ema_fast)
        ema_s = ema_series(closes, p.ema_slow)
        adx_series = wilder_adx_series(bars, p.adx_period)
        state = FLAT
        for i in range(len(bars)):
            hist = bars[: i + 1]
            last = hist[-1]
            if p.confirm_closed_only and not last.closed:
                continue
            f = ema_f[i]
            s = ema_s[i]
            adx_v = adx_series[i][0]
            if f is None or s is None or adx_v is None:
                continue
            ema_bull = float(f) > float(s)
            ema_bear_or_flat = float(f) <= float(s)
            adx_ok = float(adx_v) > float(p.adx_gate)
            adx_fail = float(adx_v) <= float(p.adx_gate)
            if state == FLAT:
                if not ema_bull or not adx_ok:
                    continue
                ch = donchian_prior(hist, p.lookback)
                atr = _sma_atr_tail(hist, p.atr_period)
                if ch is None or atr is None:
                    continue
                prior_high, _prior_low = ch
                close = float(last.close)
                if close <= 0 or atr <= 0:
                    continue
                if atr / close < p.min_atr_frac:
                    continue
                if close > prior_high:
                    state = LONG
            else:
                if ema_bear_or_flat or adx_fail:
                    state = FLAT
                    continue
                ch = donchian_prior(hist, p.lookback)
                if ch is None:
                    continue
                _prior_high, prior_low = ch
                if float(last.close) < prior_low:
                    state = FLAT
            if state not in (LONG, FLAT):
                state = FLAT
        return state


__all__ = [
    "ADX_GATE",
    "ADX_PERIOD_LOCKED",
    "ATR_PERIOD",
    "ATR_STOP_MULT",
    "BAR",
    "EMA_FAST",
    "EMA_SLOW",
    "FAMILY",
    "FLAT",
    "LONG",
    "LOOKBACK",
    "MIN_ATR_FRAC",
    "SLEEVE",
    "MidDogeBreakoutEma1221AdxParams",
    "MidDogeBreakoutEma1221AdxV1",
]
