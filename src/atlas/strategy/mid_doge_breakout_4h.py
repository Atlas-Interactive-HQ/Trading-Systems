"""Mid DOGE-USDT 4H BreakoutV1 long/flat — rise_panel Mid #65.

LOCKED Mid #65. Canonical BreakoutV1 paper plumbing on 4H:
  Entry: closed close > prior lookback-high (Donchian break up) AND ATR/close
         >= min_atr_frac (BreakoutV1 quiet filter). Long only.
  Exit: closed close < prior lookback-low (BreakoutV1 opposite-channel hint).
  Lookback = 16 (BreakoutParams.lookback_15m default, applied on 4H decision bar).
  oneh_filter: off (decision TF is already 4H; no higher-TF stub).
  NO EMA filter — keep family distinct from EMA Mid baseline and Donchian #64.
  Never short. Never places orders. not_a_forecast.
Sleeve Mid €40. Do not grind lookback / ATR / TF / costs on FAIL.
ATR stop from Signal-path BreakoutV1 is NOT applied in walk_long_flat harness
(channel exit only — same rise_panel long/flat pattern as Scalp #62).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import BreakoutParams, BreakoutV1, donchian_prior, sma_atr
from atlas.strategy.ema_trend import FLAT, LONG


def _sma_atr_tail(bars: Sequence[Bar], period: int) -> float | None:
    """ATR SMA on last period+1 bars only (O(period))."""
    need = period + 1
    if period < 1 or len(bars) < need:
        return None
    return sma_atr(bars[-need:], period)

LOOKBACK = 16  # BreakoutParams.lookback_15m default
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5  # labeled research overlay; yaml untouched
MIN_ATR_FRAC = 0.001
BAR = "4H"
FAMILY = "breakout_v1_long_flat_4h"
SLEEVE = "mid"


@dataclass(frozen=True)
class MidDogeBreakout4hParams:
    lookback: int = LOOKBACK
    atr_period: int = ATR_PERIOD
    atr_stop_mult: float = ATR_STOP_MULT
    min_atr_frac: float = MIN_ATR_FRAC
    oneh_filter: str = "off"
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class MidDogeBreakout4hV1:
    """BreakoutV1 long/flat on DOGE-USDT 4H for Mid sleeve (no EMA filter).

    Thin Mid wrapper around canonical BreakoutV1 channel + ATR quiet filter.
    Used with walk_long_flat (signal close → next open). Full-sleeve sizing at
    Mid €40 is applied by the eval harness. Rejects lookback / TF / sleeve /
    oneh sweeps (no grind on FAIL). Distinct from EMA Mid and Donchian #64.
    """

    def __init__(self, params: MidDogeBreakout4hParams | None = None) -> None:
        self.params = params or MidDogeBreakout4hParams()
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
        if p.oneh_filter != "off":
            raise ValueError("oneh_filter must be 'off' for 4H BreakoutV1 (#65)")
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked bar={BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
        # Canonical BreakoutV1 instance (oneh off; used for warmup / labels).
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
            f"mid_doge_breakout_4h_{p.sleeve}"
            f"_lb{p.lookback}_atr{p.atr_period}_long_flat"
        )

    def warmup_bars(self) -> int:
        return self.inner.warmup_bars()

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Path-dependent long/flat from BreakoutV1 channel + ATR quiet gate.

        No EMA filter. Never short. Quiet/ranging bars refuse NEW longs.
        """
        p = self.params
        state = FLAT
        if not bars:
            return FLAT
        for i in range(len(bars)):
            hist = bars[: i + 1]
            last = hist[-1]
            if p.confirm_closed_only and not last.closed:
                continue
            if state == FLAT:
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
    "FAMILY",
    "FLAT",
    "LONG",
    "LOOKBACK",
    "MIN_ATR_FRAC",
    "SLEEVE",
    "MidDogeBreakout4hParams",
    "MidDogeBreakout4hV1",
]
