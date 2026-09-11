"""Core-R1 — DOGE 1D EMA12/30 long/flat + ATR14 trailing stop 3.0 (LOCKED).

Research only. not_a_forecast. Never places orders. Never short.
config/default.yaml untouched. No Donchian / ADX / ATR-multiplier sweep.

Rule card (phase1/94):
  Entry: closed EMA12 > EMA30. Signal close → next open.
  Normal exit: EMA12 <= EMA30.
  Protection: SMA-ATR(14) trailing stop, multiplier 3.0, on causally known
    closed bars only (peak close since entry − 3.0×ATR).
  After ATR stop while EMA still bullish: require a fresh EMA12-above-EMA30
    transition before re-entry.
  Max one position; no pyramid / avg / martingale.

Do NOT score on R1–R7 until this lock is committed. Soft PASS ≠ Core-arm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import sma_atr
from atlas.strategy.ema_trend import FLAT, LONG, ema_series

FAST = 12
SLOW = 30
ATR_PERIOD = 14
ATR_TRAIL_MULT = 3.0  # locked once — no alt multipliers on R1–R7
BAR = "1D"
FAMILY = "ema12_30_atr14_trail3_long_flat_1d"
SLEEVE = "core"
LADDER_ID = "CORE-R1"


@dataclass(frozen=True)
class CoreR1EmaAtrTrailParams:
    fast: int = FAST
    slow: int = SLOW
    atr_period: int = ATR_PERIOD
    atr_trail_mult: float = ATR_TRAIL_MULT
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class CoreR1EmaAtrTrailV1:
    """EMA12/30 long/flat with locked ATR14×3.0 trailing stop (Core-R1).

    Path-dependent desired_state (same pattern as Mid #71). Never short.
    Rejects EMA / ATR / TF / sleeve sweeps.
    """

    def __init__(self, params: CoreR1EmaAtrTrailParams | None = None) -> None:
        self.params = params or CoreR1EmaAtrTrailParams()
        p = self.params
        if p.fast != FAST or p.slow != SLOW:
            raise ValueError(
                f"EMA grind forbidden: locked {FAST}/{SLOW}, got {p.fast}/{p.slow}"
            )
        if p.atr_period != ATR_PERIOD:
            raise ValueError(
                f"atr_period grind forbidden: locked {ATR_PERIOD}, got {p.atr_period}"
            )
        if p.atr_trail_mult != ATR_TRAIL_MULT:
            raise ValueError(
                f"atr_trail_mult grind forbidden: locked {ATR_TRAIL_MULT}, "
                f"got {p.atr_trail_mult}"
            )
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked bar={BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"core_r1_ema{p.fast}_{p.slow}_atr{p.atr_period}"
            f"_trail{p.atr_trail_mult}_{p.sleeve}_{p.bar}"
        )

    def warmup_bars(self) -> int:
        return max(self.params.slow, self.params.atr_period + 1)

    def desired_state(self, bars: Sequence[Bar]) -> str:
        p = self.params
        if not bars:
            return FLAT
        closes = [float(b.close) for b in bars]
        ema_f = ema_series(closes, p.fast)
        ema_s = ema_series(closes, p.slow)
        state = FLAT
        need_fresh_cross = False
        prev_bull: bool | None = None
        peak_close: float | None = None

        for i in range(len(bars)):
            last = bars[i]
            if p.confirm_closed_only and not last.closed:
                continue
            f, s = ema_f[i], ema_s[i]
            if f is None or s is None:
                continue
            ema_bull = float(f) > float(s)
            close = float(last.close)
            atr = sma_atr(bars[: i + 1], p.atr_period)

            if state == LONG:
                if peak_close is None or close > peak_close:
                    peak_close = close
                if not ema_bull:
                    state = FLAT
                    peak_close = None
                    need_fresh_cross = False
                elif (
                    atr is not None
                    and atr > 0
                    and peak_close is not None
                    and close <= peak_close - float(p.atr_trail_mult) * float(atr)
                ):
                    state = FLAT
                    peak_close = None
                    # Still bullish at stop → block until a new 12>30 transition.
                    need_fresh_cross = bool(ema_bull)
            else:
                fresh = prev_bull is False and ema_bull
                if ema_bull and (not need_fresh_cross or fresh):
                    state = LONG
                    peak_close = close
                    need_fresh_cross = False

            prev_bull = ema_bull
            if state not in (LONG, FLAT):
                state = FLAT
        return state


__all__ = [
    "ATR_PERIOD",
    "ATR_TRAIL_MULT",
    "BAR",
    "FAMILY",
    "FAST",
    "FLAT",
    "LADDER_ID",
    "LONG",
    "SLEEVE",
    "SLOW",
    "CoreR1EmaAtrTrailParams",
    "CoreR1EmaAtrTrailV1",
]
