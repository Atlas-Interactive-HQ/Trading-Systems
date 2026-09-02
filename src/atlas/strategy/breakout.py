"""Breakout v1 — 15m Donchian L+S; ranging OFF; 1h filter is a stub.

Cadence (locked L5/L8): 15m execution, 1h regime layer. Long AND short.
Ranging / mean-reversion entries are disabled and will not be generated.

This is a *transparent* rule set for Phase-1.5 paper, not a claimed edge.
Expectancy after costs is measured on paper; never guaranteed profit.

Assumptions (read before changing rules)
---------------------------------------
1. Closed bars only. The latest bar in `bars_15m` must be closed. Features
   never use a partial bar. Channel uses *prior* N highs/lows (excludes the
   decision bar) so the close that breaks the channel is not in the window.
2. Decision at bar close; the engine fills entries/signal-exits at the *next*
   bar open + taker slippage. Stops/kills may fill inside the next bars.
3. Donchian lookback default 16 (= 4h of 15m). ATR stop uses SMA of true
   range (not Wilder), period 14, multiplier 1.5. Transparent over fancy.
4. Low ATR (ATR/close < min_atr_frac) → untradeable (quiet / ranging). We
   do **not** fade the range. Ranging strategies stay off.
5. 1h filter (`oneh_filter: stub`): require 1h close on the same side of the
   prior 1h Donchian midpoint as the 15m breakout. If 1h bars are missing or
   shorter than lookback → **no trade** (fail closed). This is a stub, not a
   researched regime classifier. Set `oneh_filter: off` only in unit tests.
6. One signal per call. Engine enforces one position globally; this module
   does not pyramid or average down.
7. Opposite-channel close is an *exit hint* (engine may flatten next open).
   No same-bar favorable exit at high/low (lookahead).
8. Prices are as provided (USDT/USD treated as EUR 1:1 by the paper ledger).
9. No funding, no queue, no partials — those live in the fill sim / later.
10. Same bars + same config → same Signal (or None). No wall-clock, no RNG.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, Side, Signal


@dataclass(frozen=True)
class BreakoutParams:
    lookback_15m: int = 16
    atr_period: int = 14
    atr_stop_mult: float = 1.5
    min_atr_frac: float = 0.001
    oneh_filter: str = "stub"  # stub | off
    oneh_lookback: int = 12
    ranging: bool = False  # locked off; True is ignored
    confirm_closed_only: bool = True


def _true_range(bar: Bar, prev_close: float) -> float:
    return max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close))


def sma_atr(bars: Sequence[Bar], period: int) -> float | None:
    if period < 1 or len(bars) < period + 1:
        return None
    trs: list[float] = []
    for i in range(1, len(bars)):
        trs.append(_true_range(bars[i], bars[i - 1].close))
    window = trs[-period:]
    if len(window) < period:
        return None
    return sum(window) / period


def donchian_prior(bars: Sequence[Bar], lookback: int) -> tuple[float, float] | None:
    """High/low of the `lookback` bars *before* the last bar."""
    if lookback < 1 or len(bars) < lookback + 1:
        return None
    window = bars[-(lookback + 1) : -1]
    if len(window) < lookback:
        return None
    return max(b.high for b in window), min(b.low for b in window)


class BreakoutV1:
    def __init__(self, params: BreakoutParams | None = None) -> None:
        self.params = params or BreakoutParams()
        if self.params.lookback_15m < 1 or self.params.atr_period < 1:
            raise ValueError("lookback and atr_period must be >= 1")
        if self.params.atr_stop_mult <= 0:
            raise ValueError("atr_stop_mult must be > 0")
        if self.params.oneh_filter not in ("stub", "off"):
            raise ValueError("oneh_filter must be 'stub' or 'off'")

    def warmup_bars(self) -> int:
        return max(self.params.lookback_15m, self.params.atr_period) + 1

    def on_closed_bar(
        self,
        bars_15m: Sequence[Bar],
        bars_1h: Sequence[Bar] | None = None,
    ) -> Signal | None:
        p = self.params
        if not bars_15m:
            return None
        last = bars_15m[-1]
        if p.confirm_closed_only and not last.closed:
            return None
        for b in bars_15m[-(p.lookback_15m + 2) :]:
            b.validate()

        ch = donchian_prior(bars_15m, p.lookback_15m)
        atr = sma_atr(bars_15m, p.atr_period)
        if ch is None or atr is None:
            return None
        upper, lower = ch
        close = last.close
        if close <= 0 or atr <= 0:
            return None
        if atr / close < p.min_atr_frac:
            return None  # untradeable: quiet / ranging. Do not fade.

        # Ranging strategies stay off even if someone flips the flag.
        _ = p.ranging

        side: Side | None = None
        reason = ""
        if close > upper:
            side = Side.LONG
            reason = "donchian_break_up"
        elif close < lower:
            side = Side.SHORT
            reason = "donchian_break_down"
        else:
            return None

        ok_1h, tag = self._oneh_ok(side, bars_1h)
        if not ok_1h:
            return None

        stop_dist = atr * p.atr_stop_mult
        if side is Side.LONG:
            stop = close - stop_dist
        else:
            stop = close + stop_dist
        if stop <= 0:
            return None
        # Keep stop on the correct side of close (ATR explosion guard).
        if side is Side.LONG and stop >= close:
            return None
        if side is Side.SHORT and stop <= close:
            return None

        return Signal(
            symbol=last.symbol,
            side=side,
            stop=float(stop),
            reason=f"{reason}|{tag}",
            bar_ts_ms=last.ts_close_ms,
            extras={
                "upper": upper,
                "lower": lower,
                "atr": atr,
                "close": close,
                "oneh": tag,
            },
        )

    def exit_hint(
        self,
        position_side: Side,
        bars_15m: Sequence[Bar],
    ) -> str | None:
        """Opposite-channel close. Engine executes next open (no lookahead)."""
        ch = donchian_prior(bars_15m, self.params.lookback_15m)
        if ch is None or not bars_15m:
            return None
        upper, lower = ch
        close = bars_15m[-1].close
        if position_side is Side.LONG and close < lower:
            return "opposite_breakout"
        if position_side is Side.SHORT and close > upper:
            return "opposite_breakout"
        return None

    def _oneh_ok(
        self, side: Side, bars_1h: Sequence[Bar] | None
    ) -> tuple[bool, str]:
        p = self.params
        if p.oneh_filter == "off":
            return True, "oneh_off"
        if not bars_1h:
            return False, "oneh_missing"
        if any(not b.closed for b in bars_1h[-p.oneh_lookback :]):
            return False, "oneh_open_bar"
        ch = donchian_prior(bars_1h, p.oneh_lookback)
        if ch is None:
            return False, "oneh_missing"
        upper, lower = ch
        mid = (upper + lower) / 2.0
        c = bars_1h[-1].close
        if side is Side.LONG and c < mid:
            return False, "oneh_countertrend"
        if side is Side.SHORT and c > mid:
            return False, "oneh_countertrend"
        return True, "oneh_align"
