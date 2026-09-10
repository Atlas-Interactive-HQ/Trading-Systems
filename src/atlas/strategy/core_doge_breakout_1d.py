"""Core DOGE-USDT 1D BreakoutV1 long/flat — rise_panel Core #69.

LOCKED Core #69. Canonical BreakoutV1 paper plumbing on 1D:
  Entry: closed close > prior lookback-high (Donchian break up) AND ATR/close
         >= min_atr_frac (BreakoutV1 quiet filter). Long only.
  Exit: closed close < prior lookback-low (BreakoutV1 opposite-channel hint).
  Lookback = 16 (BreakoutParams.lookback_15m default, applied on 1D decision bar).
  oneh_filter: off (decision TF is already 1D; no higher-TF stub).
  NO EMA filter — keep family distinct from Core EMA12/30 baseline (#54).
  Never short. Never places orders. not_a_forecast.
Sleeve Core €140. Do not grind lookback / ATR / TF / costs on FAIL.
ATR stop from Signal-path BreakoutV1 is NOT applied in walk_long_flat harness
(channel exit only — same rise_panel long/flat pattern as Mid #65 / Scalp #62).
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
BAR = "1D"
FAMILY = "breakout_v1_long_flat_1d"
SLEEVE = "core"


@dataclass(frozen=True)
class CoreDogeBreakout1dParams:
    lookback: int = LOOKBACK
    atr_period: int = ATR_PERIOD
    atr_stop_mult: float = ATR_STOP_MULT
    min_atr_frac: float = MIN_ATR_FRAC
    oneh_filter: str = "off"
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class CoreDogeBreakout1dV1:
    """BreakoutV1 long/flat on DOGE-USDT 1D for Core sleeve (no EMA filter).

    Thin Core wrapper around canonical BreakoutV1 channel + ATR quiet filter.
    Used with walk_long_flat (signal close → next open). Full-sleeve sizing at
    Core €140 is applied by the eval harness. Rejects lookback / TF / sleeve /
    oneh sweeps (no grind on FAIL). Distinct from Core EMA12/30 baseline.
    """

    def __init__(self, params: CoreDogeBreakout1dParams | None = None) -> None:
        self.params = params or CoreDogeBreakout1dParams()
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
            raise ValueError("oneh_filter must be 'off' for 1D BreakoutV1 (#69)")
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
            f"core_doge_breakout_1d_{p.sleeve}"
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
    "CoreDogeBreakout1dParams",
    "CoreDogeBreakout1dV1",
]
