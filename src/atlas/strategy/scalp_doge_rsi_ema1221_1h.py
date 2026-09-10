"""Scalp DOGE-USDT 1H RSI(14) MR ∩ EMA12/21 long/flat — rise_panel Scalp #60.

LOCKED Scalp #60. ONE combined system (not sequential trials of #59 then EMA):
  Long only when EMA12 > EMA21 AND RSI(14) cross-up from ≤30 (same MR entry as #59).
  Flat/exit when RSI ≥70 OR EMA12 < EMA21.
  No shorting. EMA periods locked 12/21 (not 12/30).

Research only. not_a_forecast. Never places orders.
Do not grind RSI/EMA periods / thresholds / TF / costs on FAIL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, ema_series
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder

RSI_PERIOD = 14
ENTRY_RSI = 30.0  # cross-up from ≤ this
EXIT_RSI = 70.0  # flat when RSI ≥ this
EMA_FAST = 12
EMA_SLOW = 21  # locked 12/21 — NOT 12/30
BAR = "1H"
FAMILY = "rsi14_mr_ema1221_long_flat_1h"
SLEEVE = "scalp"


@dataclass(frozen=True)
class ScalpDogeRsiEma1221Params:
    rsi_period: int = RSI_PERIOD
    entry_rsi: float = ENTRY_RSI
    exit_rsi: float = EXIT_RSI
    ema_fast: int = EMA_FAST
    ema_slow: int = EMA_SLOW
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class ScalpDogeRsiEma1221V1:
    """Combined RSI(14) MR + EMA12/21 filter on DOGE-USDT 1H for Scalp sleeve.

    Used with walk_long_flat (signal close → next open). Full-sleeve sizing
    at Scalp €20 is applied by the eval harness, not here.

    State reconstructed from history each call:
      FLAT → LONG when EMA12>EMA21 AND RSI cross-up from ≤entry_rsi
      LONG → FLAT when RSI ≥ exit_rsi OR EMA12 < EMA21
    Never short.
    """

    def __init__(self, params: ScalpDogeRsiEma1221Params | None = None) -> None:
        self.params = params or ScalpDogeRsiEma1221Params()
        p = self.params
        if p.rsi_period != RSI_PERIOD:
            raise ValueError(
                f"period grind forbidden: locked rsi_period={RSI_PERIOD}, got {p.rsi_period}"
            )
        if float(p.entry_rsi) != float(ENTRY_RSI) or float(p.exit_rsi) != float(EXIT_RSI):
            raise ValueError(
                f"threshold grind forbidden: locked entry≤{ENTRY_RSI:g} cross-up / "
                f"exit≥{EXIT_RSI:g}, got entry={p.entry_rsi:g} exit={p.exit_rsi:g}"
            )
        if int(p.ema_fast) != EMA_FAST or int(p.ema_slow) != EMA_SLOW:
            raise ValueError(
                f"EMA period grind forbidden: locked ema{EMA_FAST}/{EMA_SLOW}, "
                f"got ema{p.ema_fast}/{p.ema_slow}"
            )
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked bar={BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
        if not (0.0 < float(p.entry_rsi) < float(p.exit_rsi) < 100.0):
            raise ValueError("need 0 < entry_rsi < exit_rsi < 100")
        if p.ema_fast < 1 or p.ema_slow < 1 or p.ema_fast >= p.ema_slow:
            raise ValueError("ema_fast/ema_slow invalid")

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"scalp_doge_rsi_ema1221_1h_{p.sleeve}_rsi{p.rsi_period}"
            f"_e{p.entry_rsi:g}_x{p.exit_rsi:g}_ema{p.ema_fast}_{p.ema_slow}"
        )

    def warmup_bars(self) -> int:
        p = self.params
        return max(int(p.ema_slow), int(p.rsi_period) + 3)

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Causal long/flat: RSI MR entry gated by EMA12>EMA21; exit on RSI≥70 or EMA bear."""
        p = self.params
        if not bars:
            return FLAT
        last = bars[-1]
        if p.confirm_closed_only and not last.closed:
            return FLAT
        need = self.warmup_bars()
        if len(bars) < need:
            return FLAT

        closes = [float(b.close) for b in bars]
        rsi_s = rsi_wilder(closes, p.rsi_period)
        ema_f = ema_series(closes, p.ema_fast)
        ema_s = ema_series(closes, p.ema_slow)
        state = FLAT
        entry = float(p.entry_rsi)
        exit_lvl = float(p.exit_rsi)
        for i in range(len(closes)):
            cur_rsi = rsi_s[i]
            f = ema_f[i]
            s = ema_s[i]
            if cur_rsi is None or f is None or s is None:
                continue
            cur_f = float(cur_rsi)
            ema_bull = float(f) > float(s)
            ema_bear = float(f) < float(s)
            if state == FLAT:
                if i == 0:
                    continue
                prev = rsi_s[i - 1]
                if prev is None:
                    continue
                # Combined entry: EMA12>EMA21 AND RSI cross-up from ≤30
                if ema_bull and float(prev) <= entry and cur_f > entry:
                    state = LONG
            else:
                # Exit: RSI≥70 OR EMA12 < EMA21
                if cur_f >= exit_lvl or ema_bear:
                    state = FLAT
        return state


__all__ = [
    "BAR",
    "EMA_FAST",
    "EMA_SLOW",
    "ENTRY_RSI",
    "EXIT_RSI",
    "FAMILY",
    "FLAT",
    "LONG",
    "RSI_PERIOD",
    "SLEEVE",
    "ScalpDogeRsiEma1221Params",
    "ScalpDogeRsiEma1221V1",
]
