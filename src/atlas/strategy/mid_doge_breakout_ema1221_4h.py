"""Mid DOGE-USDT 4H BreakoutV1 + EMA12/21 long-regime filter — rise_panel Mid #71.

LOCKED Mid #71 (doc phase1/72 — avoid clash with 71-codex-scalp-hft). Strengthens
Breakout #65 longs via EMA12>EMA21 regime gate (not size-up; not RSI):
  Entry: same BreakoutV1 channel break-up + ATR quiet as #65, AND EMA12 > EMA21.
  Exit: BreakoutV1 opposite-channel OR EMA12 ≤ EMA21 → flat / no new long.
  Lookback = 16; ATR SMA 14; min_atr_frac 0.001; oneh_filter off.
  Never short. Never places orders. not_a_forecast.
Sleeve Mid €40 (same as #65 — clean Δ). Do not grind lookback / EMA / ATR / TF / costs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import BreakoutParams, BreakoutV1, donchian_prior, sma_atr
from atlas.strategy.ema_trend import FLAT, LONG, ema_series

LOOKBACK = 16  # BreakoutParams.lookback_15m default (applied on 4H)
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5  # labeled research overlay; yaml untouched
MIN_ATR_FRAC = 0.001
EMA_FAST = 12
EMA_SLOW = 21  # locked 12/21 long-regime filter — NOT 12/30
BAR = "4H"
FAMILY = "breakout_v1_ema1221_long_regime_4h"
SLEEVE = "mid"


def _sma_atr_tail(bars: Sequence[Bar], period: int) -> float | None:
    """ATR SMA on last period+1 bars only (O(period))."""
    need = period + 1
    if period < 1 or len(bars) < need:
        return None
    return sma_atr(bars[-need:], period)


@dataclass(frozen=True)
class MidDogeBreakoutEma1221Params:
    lookback: int = LOOKBACK
    atr_period: int = ATR_PERIOD
    atr_stop_mult: float = ATR_STOP_MULT
    min_atr_frac: float = MIN_ATR_FRAC
    ema_fast: int = EMA_FAST
    ema_slow: int = EMA_SLOW
    oneh_filter: str = "off"
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class MidDogeBreakoutEma1221V1:
    """BreakoutV1 long/flat + EMA12/21 long-regime filter on DOGE-USDT 4H Mid.

    Same BreakoutV1 channel + ATR quiet as Mid #65, gated by EMA12 > EMA21:
      FLAT→LONG only when breakout entry AND EMA bull
      LONG→FLAT on channel exit OR EMA12 ≤ EMA21
    Used with walk_long_flat (signal close → next open). Mid €40 sizing in harness.
    Rejects lookback / EMA / ATR / TF / sleeve sweeps (no grind on FAIL).
    """

    def __init__(self, params: MidDogeBreakoutEma1221Params | None = None) -> None:
        self.params = params or MidDogeBreakoutEma1221Params()
        p = self.params
        if p.lookback != LOOKBACK:
            raise ValueError(
                f"lookback grind forbidden: locked lookback={LOOKBACK}, got {p.lookback}"
            )
        if p.atr_period != ATR_PERIOD:
            raise ValueError(
                f"atr_period grind forbidden: locked atr_period={ATR_PERIOD}, "
                f"got {p.atr_period}"
            )
        if p.atr_stop_mult != ATR_STOP_MULT:
            raise ValueError(
                f"atr_stop_mult grind forbidden: locked={ATR_STOP_MULT}, "
                f"got {p.atr_stop_mult}"
            )
        if p.min_atr_frac != MIN_ATR_FRAC:
            raise ValueError(
                f"min_atr_frac grind forbidden: locked={MIN_ATR_FRAC}, "
                f"got {p.min_atr_frac}"
            )
        if int(p.ema_fast) != EMA_FAST or int(p.ema_slow) != EMA_SLOW:
            raise ValueError(
                f"EMA period grind forbidden: locked ema{EMA_FAST}/{EMA_SLOW}, "
                f"got ema{p.ema_fast}/{p.ema_slow}"
            )
        if p.oneh_filter != "off":
            raise ValueError("oneh_filter must be 'off' for 4H Breakout+EMA1221 (#71)")
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
            f"mid_doge_breakout_ema1221_4h_{p.sleeve}"
            f"_lb{p.lookback}_atr{p.atr_period}_ema{p.ema_fast}_{p.ema_slow}_long_flat"
        )

    def warmup_bars(self) -> int:
        p = self.params
        return max(self.inner.warmup_bars(), int(p.ema_slow) + 1)

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Path-dependent long/flat: BreakoutV1 + EMA12>EMA21 long-regime gate.

        No new long unless EMA bull. Force flat when EMA12 ≤ EMA21. Never short.
        """
        p = self.params
        if not bars:
            return FLAT
        closes = [float(b.close) for b in bars]
        ema_f = ema_series(closes, p.ema_fast)
        ema_s = ema_series(closes, p.ema_slow)
        state = FLAT
        for i in range(len(bars)):
            hist = bars[: i + 1]
            last = hist[-1]
            if p.confirm_closed_only and not last.closed:
                continue
            f = ema_f[i]
            s = ema_s[i]
            if f is None or s is None:
                continue
            ema_bull = float(f) > float(s)
            ema_bear_or_flat = float(f) <= float(s)
            if state == FLAT:
                if not ema_bull:
                    continue  # no new long outside EMA long regime
                ch = donchian_prior(hist, p.lookback)
                atr = _sma_atr_tail(hist, p.atr_period)
                if ch is None or atr is None:
                    continue
                prior_high, _prior_low = ch
                close = float(last.close)
                if close <= 0 or atr <= 0:
                    continue
                if atr / close < p.min_atr_frac:
                    continue  # BreakoutV1 quiet / ranging — do not enter
                if close > prior_high:
                    state = LONG
            else:
                # Force flat on EMA regime fail OR BreakoutV1 channel exit
                if ema_bear_or_flat:
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
    "MidDogeBreakoutEma1221Params",
    "MidDogeBreakoutEma1221V1",
]
