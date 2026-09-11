"""Core DOGE-USDT 1D Donchian 40/20 + EMA50/200 regime — Atlas vNext Core C2 (#84).

LOCKED Core C2 from phase1/84-atlas-trading-vnext.md:
  C1 base: Donchian entry High40 / exit Low20 long/flat.
  Regime: long only when EMA50 > EMA200; force flat when EMA50 ≤ EMA200.
  No ADX / ATR (those are C3–C4). Never short. Never places orders.
Sleeve Core €140 on 1D. Do not grind Donchian N / EMA / TF / costs on FAIL.
Rationale: pre-registered rung after C1 FAIL (#88); NOT rescue.
If FAIL → stop Core Donchian family (no C3).
not_a_forecast. Soft PASS ≠ Core-arm. config/default.yaml untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.ema_trend import FLAT, LONG, ema_series

ENTRY_LOOKBACK = 40  # locked C1/C2 — High40
EXIT_LOOKBACK = 20  # locked C1/C2 — Low20
EMA_FAST = 50  # locked C2 regime
EMA_SLOW = 200  # locked C2 regime
BAR = "1D"
FAMILY = "donchian40_20_ema50_200_regime_1d"
SLEEVE = "core"
LADDER_ID = "C2"


@dataclass(frozen=True)
class CoreDogeDonchian4020Ema502001dParams:
    entry_lookback: int = ENTRY_LOOKBACK
    exit_lookback: int = EXIT_LOOKBACK
    ema_fast: int = EMA_FAST
    ema_slow: int = EMA_SLOW
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class CoreDogeDonchian4020Ema502001dV1:
    """Donchian 40/20 long/flat + EMA50/200 regime on DOGE-USDT 1D (vNext C2).

    Entry: EMA50 > EMA200 AND close > prior 40-bar high. Long only.
    Exit: EMA50 ≤ EMA200 (force flat) OR close < prior 20-bar low.
    Rejects lookback / EMA / TF / sleeve sweeps (no grind on FAIL).
    Distinct from Core EMA12/30 C0 (#54), Donchian 20/10 (#70 FAIL),
    and C1 Donchian 40/20 alone (#88 FAIL).
    """

    def __init__(self, params: CoreDogeDonchian4020Ema502001dParams | None = None) -> None:
        self.params = params or CoreDogeDonchian4020Ema502001dParams()
        p = self.params
        if p.entry_lookback != ENTRY_LOOKBACK or p.exit_lookback != EXIT_LOOKBACK:
            raise ValueError(
                f"lookback grind forbidden: locked C2 entry={ENTRY_LOOKBACK} "
                f"exit={EXIT_LOOKBACK}, got {p.entry_lookback}/{p.exit_lookback}"
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

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"core_doge_donchian40_20_ema50_200_1d_{p.sleeve}"
            f"_e{p.entry_lookback}_x{p.exit_lookback}"
            f"_ema{p.ema_fast}_{p.ema_slow}"
        )

    def warmup_bars(self) -> int:
        p = self.params
        return max(p.ema_slow, p.entry_lookback + 1, p.exit_lookback + 1)

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Path-dependent long/flat: Donchian 40/20 + EMA50>EMA200 regime.

        No new long unless EMA bull. Force flat when EMA50 ≤ EMA200. Never short.
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
                    continue  # no new long outside EMA50>EMA200 regime
                ch = donchian_prior(hist, p.entry_lookback)
                if ch is None:
                    continue
                prior_high, _prior_low = ch
                if float(last.close) > prior_high:
                    state = LONG
            else:
                # Force flat on EMA regime fail OR Donchian Low20 exit
                if ema_bear_or_flat:
                    state = FLAT
                    continue
                ch = donchian_prior(hist, p.exit_lookback)
                if ch is None:
                    continue
                _prior_high, prior_low = ch
                if float(last.close) < prior_low:
                    state = FLAT
            if state not in (LONG, FLAT):
                state = FLAT
        return state


__all__ = [
    "BAR",
    "EMA_FAST",
    "EMA_SLOW",
    "ENTRY_LOOKBACK",
    "EXIT_LOOKBACK",
    "FAMILY",
    "FLAT",
    "LADDER_ID",
    "LONG",
    "SLEEVE",
    "CoreDogeDonchian4020Ema502001dParams",
    "CoreDogeDonchian4020Ema502001dV1",
]
