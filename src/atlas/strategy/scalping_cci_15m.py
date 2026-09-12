"""guibvieira ScalpingCCI — GPL-3.0 cited REIMPLEMENTATION (15m native).

SOURCE (do NOT copy the freqtrade file into src):
  https://github.com/guibvieira/freqtrade-crypto/blob/master/user_data/strategies/ScalpingCCI.py
  raw: https://raw.githubusercontent.com/guibvieira/freqtrade-crypto/master/user_data/strategies/ScalpingCCI.py
License: GPL-3.0. This module is an original Atlas reimplementation of the
published rule card for research scoring — not a verbatim copy of the upstream file.

Locked rule card (phase1/124 — FILE WINS over dossier paraphrase):
  TF: 15m NATIVE (ticker_interval='15'). Long/flat. confirm_closed_only. Fill next-open.
  Indicators: EMA20(close), MACD(12,26,9), daily resample ×96 (15m→1440m):
    pivot=(H+L+C)/3, bc=(H+L)/2, tc=(pivot-bc)/2  [FILE formula, not comment],
    high_daily=daily high. Causal running daily OHLC (no future bars within the day).
  Entry: close > EMA20 AND MACD crosses above signal AND close > pivot AND close > bc
    AND close > tc AND pivot > pivot.shift(97) AND bc > bc.shift(97)
    AND close > tc.shift(97)   # FILE: close vs tc.shift(97), not close.shift
  Exit (indicator): open >= 0.98 * high_daily OR MACD crosses below signal.
  Locked exits (walker): source ROI ladder + SL −0.04; Atlas 5+5 bps on top.
  ROI ladder (minutes→min profit): 0→0.02, 10→0.05, 20→0.04, 60→0.3, 120→0.2.
  Sleeve €20, one position, no martingale.
  Source text recommends ≥60 parallel trades — we do NOT do that.

not_a_forecast. Never places orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, ema_series
from atlas.strategy.macd_trend import (
    DEFAULT_FAST,
    DEFAULT_SIGNAL,
    DEFAULT_SLOW,
    macd_lines,
)

BAR = "15m"
FAMILY = "guibvieira_scalping_cci_15m_long_flat"
SLEEVE = "scalp"
EMA_PERIOD = 20
MACD_FAST = DEFAULT_FAST  # 12
MACD_SLOW = DEFAULT_SLOW  # 26
MACD_SIGNAL = DEFAULT_SIGNAL  # 9
DAILY_FACTOR = 96  # 15m × 96 = 1440m (daily)
SHIFT_BARS = 97
HIGH_DAILY_EXIT_FRAC = 0.98
SL_FRAC = 0.04

# Freqtrade minimal_roi (minutes since entry → required profit fraction)
ROI_LADDER: tuple[tuple[int, float], ...] = (
    (0, 0.02),
    (10, 0.05),
    (20, 0.04),
    (60, 0.3),
    (120, 0.2),
)

SOURCE_URL = (
    "https://raw.githubusercontent.com/guibvieira/freqtrade-crypto/"
    "master/user_data/strategies/ScalpingCCI.py"
)
SOURCE_LICENSE = "GPL-3.0"
SOURCE_NOTE = (
    "Reimplementation of published ScalpingCCI.py rule card; upstream recommends "
    "≥60 parallel trades and ROI-led sells — Atlas scores single €20 sleeve + "
    "honors source ROI ladder + SL −0.04 as locked exits on top of indicator exits. "
    "tc=(pivot-bc)/2 per FILE (comment's classic TC formula is NOT used). "
    "Entry close > tc.shift(97) per FILE (not close rising)."
)


@dataclass(frozen=True)
class ScalpingCci15mParams:
    ema_period: int = EMA_PERIOD
    macd_fast: int = MACD_FAST
    macd_slow: int = MACD_SLOW
    macd_signal: int = MACD_SIGNAL
    daily_factor: int = DAILY_FACTOR
    shift_bars: int = SHIFT_BARS
    high_daily_exit_frac: float = HIGH_DAILY_EXIT_FRAC
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


def roi_threshold_for_minutes(minutes_held: float) -> float:
    """Freqtrade minimal_roi lookup: largest key <= duration → threshold."""
    if minutes_held < 0:
        minutes_held = 0.0
    chosen = float(ROI_LADDER[0][1])
    for mins, roi in sorted(ROI_LADDER, key=lambda x: -x[0]):
        if minutes_held >= float(mins):
            return float(roi)
    return chosen


def crossed_above(
    curr: float | None,
    prev: float | None,
    other_curr: float | None,
    other_prev: float | None,
) -> bool:
    if curr is None or prev is None or other_curr is None or other_prev is None:
        return False
    return float(prev) <= float(other_prev) and float(curr) > float(other_curr)


def crossed_below(
    curr: float | None,
    prev: float | None,
    other_curr: float | None,
    other_prev: float | None,
) -> bool:
    if curr is None or prev is None or other_curr is None or other_prev is None:
        return False
    return float(prev) >= float(other_prev) and float(curr) < float(other_curr)


def _utc_day_key(ts_open_ms: int) -> int:
    """UTC calendar day id (days since epoch)."""
    return int(ts_open_ms) // 86_400_000


def causal_daily_levels(
    bars: Sequence[Bar],
) -> dict[str, list[float | None]]:
    """Running UTC-day OHLC → pivot/bc/tc/high_daily (causal; no future bars).

    Within a UTC day, each 15m bar sees OHLC aggregated from day-start through
    itself only. Matches live causality better than full-day lookahead merges.
    FILE formula: tc = (pivot - bc) / 2.
    """
    n = len(bars)
    pivot: list[float | None] = [None] * n
    bc: list[float | None] = [None] * n
    tc: list[float | None] = [None] * n
    high_daily: list[float | None] = [None] * n
    low_daily: list[float | None] = [None] * n

    day_high = 0.0
    day_low = 0.0
    day_close = 0.0
    day_open_set = False
    prev_day: int | None = None

    for i, b in enumerate(bars):
        day = _utc_day_key(int(b.ts_open_ms))
        h = float(b.high)
        l = float(b.low)
        c = float(b.close)
        if prev_day is None or day != prev_day:
            day_high = h
            day_low = l
            day_close = c
            day_open_set = True
            prev_day = day
        else:
            if h > day_high:
                day_high = h
            if l < day_low:
                day_low = l
            day_close = c
        if not day_open_set:
            continue
        p = (day_high + day_low + day_close) / 3.0
        bcv = (day_high + day_low) / 2.0
        tcv = (p - bcv) / 2.0  # FILE — not (pivot - bc) + pivot
        pivot[i] = q(p)
        bc[i] = q(bcv)
        tc[i] = q(tcv)
        high_daily[i] = q(day_high)
        low_daily[i] = q(day_low)

    return {
        "pivot": pivot,
        "bc": bc,
        "tc": tc,
        "high_daily": high_daily,
        "low_daily": low_daily,
    }


def compute_indicators(
    bars: Sequence[Bar],
    *,
    ema_period: int = EMA_PERIOD,
    macd_fast: int = MACD_FAST,
    macd_slow: int = MACD_SLOW,
    macd_signal: int = MACD_SIGNAL,
) -> dict[str, list]:
    closes = [float(b.close) for b in bars]
    ema20 = ema_series(closes, ema_period)
    macd, macdsignal = macd_lines(
        closes, fast=macd_fast, slow=macd_slow, signal=macd_signal
    )
    daily = causal_daily_levels(bars)
    return {
        "ema20": ema20,
        "macd": macd,
        "macdsignal": macdsignal,
        "pivot": daily["pivot"],
        "bc": daily["bc"],
        "tc": daily["tc"],
        "high_daily": daily["high_daily"],
        "low_daily": daily["low_daily"],
    }


def precompute_entry_exit_signals(
    bars: Sequence[Bar],
    *,
    params: ScalpingCci15mParams | None = None,
) -> tuple[list[bool], list[bool]]:
    """O(n) entry/exit boolean series matching ScalpingCCI populate_*_trend."""
    p = params or ScalpingCci15mParams()
    n = len(bars)
    entry = [False] * n
    exit_ = [False] * n
    if n == 0:
        return entry, exit_
    ind = compute_indicators(
        bars,
        ema_period=p.ema_period,
        macd_fast=p.macd_fast,
        macd_slow=p.macd_slow,
        macd_signal=p.macd_signal,
    )
    ema20 = ind["ema20"]
    macd = ind["macd"]
    macdsignal = ind["macdsignal"]
    pivot = ind["pivot"]
    bc = ind["bc"]
    tc = ind["tc"]
    high_daily = ind["high_daily"]
    shift = int(p.shift_bars)
    exit_frac = float(p.high_daily_exit_frac)

    for i in range(n):
        if p.confirm_closed_only and not bars[i].closed:
            continue
        c = float(bars[i].close)
        o = float(bars[i].open)
        e = ema20[i]
        m = macd[i]
        s = macdsignal[i]
        m_prev = macd[i - 1] if i > 0 else None
        s_prev = macdsignal[i - 1] if i > 0 else None
        pv = pivot[i]
        bcv = bc[i]
        tcv = tc[i]
        hd = high_daily[i]

        i_shift = i - shift
        pv_s = pivot[i_shift] if i_shift >= 0 else None
        bc_s = bc[i_shift] if i_shift >= 0 else None
        tc_s = tc[i_shift] if i_shift >= 0 else None

        if (
            e is not None
            and m is not None
            and s is not None
            and pv is not None
            and bcv is not None
            and tcv is not None
            and pv_s is not None
            and bc_s is not None
            and tc_s is not None
            and c > float(e)
            and crossed_above(m, m_prev, s, s_prev)
            and c > float(pv)
            and c > float(bcv)
            and c > float(tcv)
            and float(pv) > float(pv_s)
            and float(bcv) > float(bc_s)
            and c > float(tc_s)
        ):
            entry[i] = True

        macd_x_below = crossed_below(m, m_prev, s, s_prev)
        near_high = hd is not None and o >= exit_frac * float(hd)
        if near_high or macd_x_below:
            exit_[i] = True

    return entry, exit_


class ScalpingCci15mV1:
    """Long/flat ScalpingCCI 15m. Indicator path only; ROI/SL in paper walker."""

    def __init__(self, params: ScalpingCci15mParams | None = None) -> None:
        self.params = params or ScalpingCci15mParams()
        p = self.params
        if p.ema_period != EMA_PERIOD:
            raise ValueError(f"EMA grind forbidden: locked {EMA_PERIOD}, got {p.ema_period}")
        if (
            p.macd_fast != MACD_FAST
            or p.macd_slow != MACD_SLOW
            or p.macd_signal != MACD_SIGNAL
        ):
            raise ValueError(
                f"MACD grind forbidden: locked ({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL}), "
                f"got ({p.macd_fast},{p.macd_slow},{p.macd_signal})"
            )
        if p.daily_factor != DAILY_FACTOR:
            raise ValueError(
                f"daily_factor grind forbidden: locked {DAILY_FACTOR}, got {p.daily_factor}"
            )
        if p.shift_bars != SHIFT_BARS:
            raise ValueError(
                f"shift_bars grind forbidden: locked {SHIFT_BARS}, got {p.shift_bars}"
            )
        if float(p.high_daily_exit_frac) != float(HIGH_DAILY_EXIT_FRAC):
            raise ValueError(
                f"high_daily_exit_frac grind forbidden: locked {HIGH_DAILY_EXIT_FRAC}, "
                f"got {p.high_daily_exit_frac}"
            )
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked {BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
        if not p.confirm_closed_only:
            raise ValueError("confirm_closed_only locked True")

    @property
    def label(self) -> str:
        return "guibvieira_scalping_cci_15m_long_flat_eur20"

    def warmup_bars(self) -> int:
        # MACD needs slow+signal; EMA20; shift 97; ~1 day of 15m for daily levels
        return max(MACD_SLOW + MACD_SIGNAL, EMA_PERIOD, SHIFT_BARS) + DAILY_FACTOR + 2

    def desired_state(self, bars: Sequence[Bar]) -> str:
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
    "BAR",
    "DAILY_FACTOR",
    "EMA_PERIOD",
    "FAMILY",
    "FLAT",
    "HIGH_DAILY_EXIT_FRAC",
    "LONG",
    "MACD_FAST",
    "MACD_SIGNAL",
    "MACD_SLOW",
    "ROI_LADDER",
    "SHIFT_BARS",
    "SLEEVE",
    "SL_FRAC",
    "SOURCE_LICENSE",
    "SOURCE_NOTE",
    "SOURCE_URL",
    "ScalpingCci15mParams",
    "ScalpingCci15mV1",
    "causal_daily_levels",
    "compute_indicators",
    "crossed_above",
    "crossed_below",
    "precompute_entry_exit_signals",
    "roi_threshold_for_minutes",
]
