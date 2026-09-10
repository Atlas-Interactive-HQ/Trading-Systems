"""Scalp DOGE-USDT 1H RSI(14) mean-reversion long/flat — rise_panel Scalp #59.

LOCKED Scalp improve #59. Different family vs EMA-twin (#55/#57/#58).
Reuses Wilder RSI helper from mid_doge_rsi_mr; Scalp rule card is NEW:
  Entry: RSI crosses up from ≤30 (prev ≤30 and curr >30).
  Exit: closed-bar RSI ≥70 → flat.
  No EMA filter. Never short. Never places orders. not_a_forecast.
Sleeve Scalp €20. Do not grind RSI period / thresholds / TF / costs on FAIL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder

RSI_PERIOD = 14
ENTRY_RSI = 30.0  # cross-up from ≤ this
EXIT_RSI = 70.0  # flat when RSI ≥ this
BAR = "1H"
FAMILY = "rsi14_mr_long_flat_1h"
SLEEVE = "scalp"


@dataclass(frozen=True)
class ScalpDogeRsiMr1hParams:
    rsi_period: int = RSI_PERIOD
    entry_rsi: float = ENTRY_RSI
    exit_rsi: float = EXIT_RSI
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class ScalpDogeRsiMr1hV1:
    """RSI(14) mean-reversion long/flat on DOGE-USDT 1H for Scalp sleeve.

    Used with walk_long_flat (signal close → next open). Full-sleeve sizing
    at Scalp €20 is applied by the eval harness, not here.

    State reconstructed from history each call:
      FLAT → LONG on cross-up from ≤entry_rsi
      LONG → FLAT when RSI ≥ exit_rsi
    No EMA regime filter.
    """

    def __init__(self, params: ScalpDogeRsiMr1hParams | None = None) -> None:
        self.params = params or ScalpDogeRsiMr1hParams()
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
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked bar={BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
        if not (0.0 < float(p.entry_rsi) < float(p.exit_rsi) < 100.0):
            raise ValueError("need 0 < entry_rsi < exit_rsi < 100")

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"scalp_doge_rsi_mr_1h_{p.sleeve}_rsi{p.rsi_period}"
            f"_e{p.entry_rsi:g}_x{p.exit_rsi:g}"
        )

    def warmup_bars(self) -> int:
        return int(self.params.rsi_period) + 3

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Causal long/flat from full prefix: cross-up entry, RSI≥70 exit."""
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
        state = FLAT
        entry = float(p.entry_rsi)
        exit_lvl = float(p.exit_rsi)
        for i in range(len(rsi_s)):
            cur = rsi_s[i]
            if cur is None:
                continue
            cur_f = float(cur)
            if state == FLAT:
                # Cross-up from ≤entry: need prior RSI ≤ entry and curr > entry
                # (covers "closes ≤30 then next bar >30")
                if i == 0:
                    continue
                prev = rsi_s[i - 1]
                if prev is None:
                    continue
                if float(prev) <= entry and cur_f > entry:
                    state = LONG
            else:
                if cur_f >= exit_lvl:
                    state = FLAT
        return state


__all__ = [
    "BAR",
    "ENTRY_RSI",
    "EXIT_RSI",
    "FAMILY",
    "FLAT",
    "LONG",
    "RSI_PERIOD",
    "SLEEVE",
    "ScalpDogeRsiMr1hParams",
    "ScalpDogeRsiMr1hV1",
]
