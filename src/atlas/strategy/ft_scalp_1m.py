"""Freqtrade berlinguyinca/Scalp.py — GPL-3.0 cited REIMPLEMENTATION (1m native).

SOURCE (do NOT copy the freqtrade file into src):
  https://github.com/freqtrade/freqtrade-strategies/blob/master/user_data/strategies/berlinguyinca/Scalp.py
  raw: https://raw.githubusercontent.com/freqtrade/freqtrade-strategies/master/user_data/strategies/berlinguyinca/Scalp.py
License: GPL-3.0 (freqtrade-strategies). This module is an original Atlas reimplementation
of the published rule card for research scoring — not a verbatim copy of the upstream file.

Locked rule card (phase1/123 — do not grind):
  TF: 1m NATIVE. Long/flat only. confirm_closed_only. Fill next-open.
  Indicators: EMA5(high), EMA5(low), STOCHF(5,3, SMA fastd), ADX(14).
  Entry: open < EMA5(low) AND ADX>30 AND fastk<30 AND fastd<30 AND fastk crosses above fastd.
  Exit (indicator): open >= EMA5(high) OR fastk crosses above 70 OR fastd crosses above 70.
  Locked exits also: ROI +1% from entry, SL −4% (honored in the paper walker, not here).
  Sleeve €20, one position, no martingale. Source text recommends ≥60 parallel trades —
  we do NOT do that (honesty: single €20 sleeve).

not_a_forecast. Never places orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.adx import ADX_PERIOD, wilder_adx_series
from atlas.strategy.ema_trend import FLAT, LONG, ema_series

BAR = "1m"
FAMILY = "ft_berlinguyinca_scalp_1m_long_flat"
SLEEVE = "scalp"
EMA_PERIOD = 5
STOCH_FASTK = 5
STOCH_FASTD = 3  # SMA of fastk (talib fastd_matype=0)
ADX_GATE = 30.0
STOCH_ENTRY_LVL = 30.0
STOCH_EXIT_LVL = 70.0
ROI_FRAC = 0.01  # +1% from entry (walker)
SL_FRAC = 0.04  # −4% from entry (walker)

SOURCE_URL = (
    "https://raw.githubusercontent.com/freqtrade/freqtrade-strategies/"
    "master/user_data/strategies/berlinguyinca/Scalp.py"
)
SOURCE_LICENSE = "GPL-3.0"
SOURCE_NOTE = (
    "Reimplementation of published Scalp.py rule card; upstream recommends "
    "≥60 parallel trades and ROI-led sells — Atlas scores single €20 sleeve + "
    "honors ROI +1% / SL −4% as locked exits on top of indicator exits."
)


@dataclass(frozen=True)
class FtScalp1mParams:
    ema_period: int = EMA_PERIOD
    stoch_fastk: int = STOCH_FASTK
    stoch_fastd: int = STOCH_FASTD
    adx_period: int = ADX_PERIOD
    adx_gate: float = ADX_GATE
    stoch_entry_lvl: float = STOCH_ENTRY_LVL
    stoch_exit_lvl: float = STOCH_EXIT_LVL
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


def stochf_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    fastk_period: int = STOCH_FASTK,
    fastd_period: int = STOCH_FASTD,
) -> tuple[list[float | None], list[float | None]]:
    """Fast stochastic %K / %D (SMA). Matches talib STOCHF(k,d,SMA)."""
    n = len(closes)
    fastk: list[float | None] = [None] * n
    fastd: list[float | None] = [None] * n
    if fastk_period < 1 or fastd_period < 1 or n < fastk_period:
        return fastk, fastd
    for i in range(fastk_period - 1, n):
        window_h = highs[i - fastk_period + 1 : i + 1]
        window_l = lows[i - fastk_period + 1 : i + 1]
        hh = max(window_h)
        ll = min(window_l)
        denom = hh - ll
        if denom <= 0:
            fastk[i] = 0.0
        else:
            fastk[i] = q(100.0 * (float(closes[i]) - ll) / denom)
    # %D = SMA of last fastd_period valid %K values
    for i in range(n):
        if i + 1 < fastk_period + fastd_period - 1:
            continue
        chunk = fastk[i - fastd_period + 1 : i + 1]
        if any(v is None for v in chunk):
            continue
        fastd[i] = q(sum(float(v) for v in chunk) / float(fastd_period))  # type: ignore[arg-type]
    return fastk, fastd


def crossed_above(curr: float | None, prev: float | None, level_or_other_curr: float | None, level_or_other_prev: float | None) -> bool:
    """True when series A crosses above series B (or a level encoded as equal curr/prev)."""
    if curr is None or prev is None or level_or_other_curr is None or level_or_other_prev is None:
        return False
    return float(prev) <= float(level_or_other_prev) and float(curr) > float(level_or_other_curr)


def compute_indicators(
    bars: Sequence[Bar],
    *,
    ema_period: int = EMA_PERIOD,
    stoch_fastk: int = STOCH_FASTK,
    stoch_fastd: int = STOCH_FASTD,
    adx_period: int = ADX_PERIOD,
) -> dict[str, list]:
    highs = [float(b.high) for b in bars]
    lows = [float(b.low) for b in bars]
    closes = [float(b.close) for b in bars]
    ema_high = ema_series(highs, ema_period)
    ema_low = ema_series(lows, ema_period)
    fastk, fastd = stochf_series(
        highs, lows, closes, fastk_period=stoch_fastk, fastd_period=stoch_fastd
    )
    adx_rows = wilder_adx_series(bars, adx_period)
    adx = [row[0] for row in adx_rows]
    return {
        "ema_high": ema_high,
        "ema_low": ema_low,
        "fastk": fastk,
        "fastd": fastd,
        "adx": adx,
    }


def precompute_entry_exit_signals(
    bars: Sequence[Bar],
    *,
    params: FtScalp1mParams | None = None,
) -> tuple[list[bool], list[bool]]:
    """O(n) entry/exit boolean series matching Scalp.py populate_*_trend."""
    p = params or FtScalp1mParams()
    n = len(bars)
    entry = [False] * n
    exit_ = [False] * n
    if n == 0:
        return entry, exit_
    ind = compute_indicators(
        bars,
        ema_period=p.ema_period,
        stoch_fastk=p.stoch_fastk,
        stoch_fastd=p.stoch_fastd,
        adx_period=p.adx_period,
    )
    ema_high = ind["ema_high"]
    ema_low = ind["ema_low"]
    fastk = ind["fastk"]
    fastd = ind["fastd"]
    adx = ind["adx"]
    entry_lvl = float(p.stoch_entry_lvl)
    exit_lvl = float(p.stoch_exit_lvl)
    adx_gate = float(p.adx_gate)

    for i in range(n):
        if p.confirm_closed_only and not bars[i].closed:
            continue
        o = float(bars[i].open)
        el = ema_low[i]
        eh = ema_high[i]
        fk = fastk[i]
        fd = fastd[i]
        ax = adx[i]
        fk_prev = fastk[i - 1] if i > 0 else None
        fd_prev = fastd[i - 1] if i > 0 else None

        # Entry
        if (
            el is not None
            and ax is not None
            and fk is not None
            and fd is not None
            and o < float(el)
            and float(ax) > adx_gate
            and float(fk) < entry_lvl
            and float(fd) < entry_lvl
            and crossed_above(fk, fk_prev, fd, fd_prev)
        ):
            entry[i] = True

        # Exit (indicator)
        cross_k70 = crossed_above(fk, fk_prev, exit_lvl, exit_lvl)
        cross_d70 = crossed_above(fd, fd_prev, exit_lvl, exit_lvl)
        if (eh is not None and o >= float(eh)) or cross_k70 or cross_d70:
            exit_[i] = True

    return entry, exit_


class FtScalp1mV1:
    """Long/flat Scalp 1m. Indicator path only; ROI/SL applied in paper walker."""

    def __init__(self, params: FtScalp1mParams | None = None) -> None:
        self.params = params or FtScalp1mParams()
        p = self.params
        if p.ema_period != EMA_PERIOD:
            raise ValueError(f"EMA grind forbidden: locked {EMA_PERIOD}, got {p.ema_period}")
        if p.stoch_fastk != STOCH_FASTK or p.stoch_fastd != STOCH_FASTD:
            raise ValueError(
                f"STOCH grind forbidden: locked ({STOCH_FASTK},{STOCH_FASTD}), "
                f"got ({p.stoch_fastk},{p.stoch_fastd})"
            )
        if p.adx_period != ADX_PERIOD or float(p.adx_gate) != float(ADX_GATE):
            raise ValueError(
                f"ADX grind forbidden: locked period={ADX_PERIOD} gate={ADX_GATE}, "
                f"got period={p.adx_period} gate={p.adx_gate}"
            )
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked {BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
        if not p.confirm_closed_only:
            raise ValueError("confirm_closed_only locked True")

    @property
    def label(self) -> str:
        return "ft_berlinguyinca_scalp_1m_long_flat_eur20"

    def warmup_bars(self) -> int:
        # ADX first valid ~ 2*14-1; stoch needs k+d; ema needs 5
        return max(2 * int(self.params.adx_period), self.params.stoch_fastk + self.params.stoch_fastd, self.params.ema_period) + 2

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Causal long/flat from indicator entry/exit only (no ROI/SL — walker)."""
        if not bars:
            return FLAT
        if self.params.confirm_closed_only and not bars[-1].closed:
            return FLAT
        if len(bars) < self.warmup_bars():
            return FLAT
        entry, exit_ = precompute_entry_exit_signals(bars, params=self.params)
        state = FLAT
        for i in range(len(bars)):
            if state == FLAT:
                if entry[i]:
                    state = LONG
            else:
                if exit_[i]:
                    state = FLAT
        return state


__all__ = [
    "ADX_GATE",
    "ADX_PERIOD",
    "BAR",
    "EMA_PERIOD",
    "FAMILY",
    "FLAT",
    "LONG",
    "ROI_FRAC",
    "SL_FRAC",
    "SLEEVE",
    "SOURCE_LICENSE",
    "SOURCE_NOTE",
    "SOURCE_URL",
    "STOCH_ENTRY_LVL",
    "STOCH_EXIT_LVL",
    "STOCH_FASTD",
    "STOCH_FASTK",
    "FtScalp1mParams",
    "FtScalp1mV1",
    "compute_indicators",
    "crossed_above",
    "precompute_entry_exit_signals",
    "stochf_series",
]
