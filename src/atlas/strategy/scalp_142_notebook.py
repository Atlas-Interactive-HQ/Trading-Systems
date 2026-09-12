"""Public-MD Scalp #142 — Kaje notebook June-2024 multi-TF stack (paper only).

LOCKED cells:
  M1 = long-only 4H range-low → 1H MSB → 15m confirm → 1m BOS; risk 20%; TP 2R
  M2 = same signals; risk 25% (leverage twin)
  M3 = short mirror; risk 20%

Pivots N=3 (confirm after i+3). No ATR trail. n_time_stop=0. Max 1 pos.
Soft PASS ≠ arm. not_a_forecast. Never places orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder
from atlas.strategy.rvol import RVOL_LOOKBACK, rvol_series
from atlas.strategy.scalp_structure_bos_125 import SwingPoint, confirmed_swings

PIVOT_N = 3
ATR_PERIOD = 14
RSI_PERIOD = 14
RVOL_N = RVOL_LOOKBACK  # 20
RVOL_GATE = 1.0  # require >= 1.0 at 15m confirm (harmony)
RANGE_ATR_FRAC = 0.25  # 4H "at range low/high" band
SL_ATR_FRAC = 0.1  # SL = 15m swing ± 0.1 * ATR14(15m)
R_MULTIPLE = 2.0
LEVERAGE_CAP = 10.0
RISK_M1 = 0.20
RISK_M2 = 0.25
RISK_M3 = 0.20

Side = Literal["long", "short"]
LONG: Side = "long"
SHORT: Side = "short"


def atr_wilder_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    period: int = ATR_PERIOD,
) -> list[float | None]:
    n = len(closes)
    out: list[float | None] = [None] * n
    if period < 1 or n == 0:
        return out
    trs: list[float] = []
    for i in range(n):
        h = float(highs[i])
        l = float(lows[i])
        if i == 0:
            tr = h - l
        else:
            pc = float(closes[i - 1])
            tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    if n < period:
        return out
    seed = sum(trs[:period]) / float(period)
    out[period - 1] = q(seed)
    prev = seed
    for i in range(period, n):
        prev = (prev * (period - 1) + trs[i]) / float(period)
        out[i] = q(prev)
    return out


def atr_from_bars(bars: Sequence[Bar], *, period: int = ATR_PERIOD) -> list[float | None]:
    return atr_wilder_series(
        [float(b.high) for b in bars],
        [float(b.low) for b in bars],
        [float(b.close) for b in bars],
        period=period,
    )


def _swings_by_confirm(
    swings: Sequence[SwingPoint],
) -> tuple[list[SwingPoint], list[SwingPoint]]:
    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]
    return highs, lows


def most_recent_asof(
    swings_sorted: Sequence[SwingPoint],
    *,
    asof_confirm_index: int,
) -> SwingPoint | None:
    """Latest swing with confirm_index <= asof (swings sorted by confirm_index)."""
    best: SwingPoint | None = None
    for s in swings_sorted:
        if s.confirm_index <= asof_confirm_index:
            best = s
        else:
            break
    return best


def build_asof_swing_price(
    n_bars: int,
    swings_sorted: Sequence[SwingPoint],
) -> list[float | None]:
    """Per-bar most recent confirmed swing price (confirm_index <= i)."""
    out: list[float | None] = [None] * n_bars
    j = 0
    last: float | None = None
    m = len(swings_sorted)
    for i in range(n_bars):
        while j < m and swings_sorted[j].confirm_index <= i:
            last = float(swings_sorted[j].price)
            j += 1
        out[i] = last
    return out


def build_asof_swing_index(
    n_bars: int,
    swings_sorted: Sequence[SwingPoint],
) -> list[int | None]:
    out: list[int | None] = [None] * n_bars
    j = 0
    last_i: int | None = None
    m = len(swings_sorted)
    for i in range(n_bars):
        while j < m and swings_sorted[j].confirm_index <= i:
            last_i = int(swings_sorted[j].index)
            j += 1
        out[i] = last_i
    return out


def map_htf_index(
    decision_close_ms: int,
    htf_bars: Sequence[Bar],
    *,
    start_from: int,
) -> int:
    """Largest j with htf_bars[j].ts_close_ms <= decision_close_ms; else -1."""
    j = start_from
    while j + 1 < len(htf_bars) and htf_bars[j + 1].ts_close_ms <= decision_close_ms:
        j += 1
    if j < 0 or j >= len(htf_bars):
        return -1
    if htf_bars[j].ts_close_ms > decision_close_ms:
        return -1
    return j


def first_bar_index_at_or_after(bars: Sequence[Bar], ts_open_ms: int, *, start: int = 0) -> int:
    j = max(0, start)
    n = len(bars)
    while j < n and bars[j].ts_open_ms < ts_open_ms:
        j += 1
    return j if j < n else n


@dataclass(frozen=True)
class NotebookSetup:
    """One armed setup that produced (or attempted) a 1m BOS entry signal."""

    side: Side
    msb_1h_index: int
    msb_1h_ts_close_ms: int
    confirm_15m_index: int
    confirm_15m_ts_close_ms: int
    range_line: float  # 15m swing used for confirm / SL anchor
    atr_15m_at_confirm: float
    sl_structural: float
    bos_1m_index: int  # signal bar (closed); fill at next open
    bos_1m_ts_open_ms: int
    local_1m_swing: float
    skipped: str | None  # none / rvol / div / no_bos / cancelled_opp_msb
    # For div diagnostics
    div_price_h1: float | None = None
    div_price_h2: float | None = None
    div_rsi_h1: float | None = None
    div_rsi_h2: float | None = None


@dataclass
class TfBundle:
    bars_4h: list[Bar]
    bars_1h: list[Bar]
    bars_15m: list[Bar]
    bars_1m: list[Bar]
    swings_4h_h: list[SwingPoint]
    swings_4h_l: list[SwingPoint]
    swings_1h_h: list[SwingPoint]
    swings_1h_l: list[SwingPoint]
    swings_15m_h: list[SwingPoint]
    swings_15m_l: list[SwingPoint]
    swings_1m_h: list[SwingPoint]
    swings_1m_l: list[SwingPoint]
    atr_4h: list[float | None]
    atr_15m: list[float | None]
    rvol_15m: list[float | None]
    rsi_15m: list[float | None]
    asof_1m_high: list[float | None]
    asof_1m_low: list[float | None]
    asof_15m_high: list[float | None]
    asof_15m_low: list[float | None]
    asof_15m_high_idx: list[int | None]
    asof_1h_high: list[float | None]
    asof_1h_low: list[float | None]
    # prior swing (second most recent) for MSB "break prior"
    prior_1h_high: list[float | None]
    prior_1h_low: list[float | None]


def _prior_asof_prices(
    n_bars: int,
    swings_sorted: Sequence[SwingPoint],
) -> tuple[list[float | None], list[float | None]]:
    """Return (most_recent, prior) swing prices as-of each bar confirm index."""
    recent: list[float | None] = [None] * n_bars
    prior: list[float | None] = [None] * n_bars
    j = 0
    last: float | None = None
    prev: float | None = None
    m = len(swings_sorted)
    for i in range(n_bars):
        while j < m and swings_sorted[j].confirm_index <= i:
            prev = last
            last = float(swings_sorted[j].price)
            j += 1
        recent[i] = last
        prior[i] = prev
    return recent, prior


def build_tf_bundle(
    bars_4h: list[Bar],
    bars_1h: list[Bar],
    bars_15m: list[Bar],
    bars_1m: list[Bar],
    *,
    pivot_n: int = PIVOT_N,
) -> TfBundle:
    s4 = confirmed_swings(bars_4h, pivot_n=pivot_n)
    s1 = confirmed_swings(bars_1h, pivot_n=pivot_n)
    s15 = confirmed_swings(bars_15m, pivot_n=pivot_n)
    s1m = confirmed_swings(bars_1m, pivot_n=pivot_n)
    s4h_h, s4h_l = _swings_by_confirm(s4)
    s1h_h, s1h_l = _swings_by_confirm(s1)
    s15h, s15l = _swings_by_confirm(s15)
    s1mh, s1ml = _swings_by_confirm(s1m)

    atr4 = atr_from_bars(bars_4h)
    atr15 = atr_from_bars(bars_15m)
    rvol15 = rvol_series(bars_15m, RVOL_N)
    rsi15 = rsi_wilder([float(b.close) for b in bars_15m], RSI_PERIOD)

    asof_1m_h = build_asof_swing_price(len(bars_1m), s1mh)
    asof_1m_l = build_asof_swing_price(len(bars_1m), s1ml)
    asof_15_h = build_asof_swing_price(len(bars_15m), s15h)
    asof_15_l = build_asof_swing_price(len(bars_15m), s15l)
    asof_15_h_idx = build_asof_swing_index(len(bars_15m), s15h)
    asof_1h_h, prior_1h_h = _prior_asof_prices(len(bars_1h), s1h_h)
    asof_1h_l, prior_1h_l = _prior_asof_prices(len(bars_1h), s1h_l)

    return TfBundle(
        bars_4h=bars_4h,
        bars_1h=bars_1h,
        bars_15m=bars_15m,
        bars_1m=bars_1m,
        swings_4h_h=s4h_h,
        swings_4h_l=s4h_l,
        swings_1h_h=s1h_h,
        swings_1h_l=s1h_l,
        swings_15m_h=s15h,
        swings_15m_l=s15l,
        swings_1m_h=s1mh,
        swings_1m_l=s1ml,
        atr_4h=atr4,
        atr_15m=atr15,
        rvol_15m=rvol15,
        rsi_15m=rsi15,
        asof_1m_high=asof_1m_h,
        asof_1m_low=asof_1m_l,
        asof_15m_high=asof_15_h,
        asof_15m_low=asof_15_l,
        asof_15m_high_idx=asof_15_h_idx,
        asof_1h_high=asof_1h_h,
        asof_1h_low=asof_1h_l,
        prior_1h_high=prior_1h_h,
        prior_1h_low=prior_1h_l,
    )


def _4h_range_low_context(
    bundle: TfBundle,
    *,
    j4: int,
    tagged_low: bool,
) -> tuple[bool, bool]:
    """Return (context_true, tagged_updated).

    at range low = 4H low within 0.25*ATR of most recent confirmed 4H swing low
    OR 4H close reclaims above that swing after tagging.
    """
    if j4 < 0:
        return False, tagged_low
    swing = most_recent_asof(bundle.swings_4h_l, asof_confirm_index=j4)
    atr = bundle.atr_4h[j4]
    if swing is None or atr is None or atr <= 0:
        return False, tagged_low
    bar = bundle.bars_4h[j4]
    band = RANGE_ATR_FRAC * float(atr)
    swing_px = float(swing.price)
    near = abs(float(bar.low) - swing_px) <= band or float(bar.low) <= swing_px + band
    if near or float(bar.low) <= swing_px:
        tagged_low = True
    reclaim = tagged_low and float(bar.close) > swing_px
    return (near or reclaim), tagged_low


def _4h_range_high_context(
    bundle: TfBundle,
    *,
    j4: int,
    tagged_high: bool,
) -> tuple[bool, bool]:
    if j4 < 0:
        return False, tagged_high
    swing = most_recent_asof(bundle.swings_4h_h, asof_confirm_index=j4)
    atr = bundle.atr_4h[j4]
    if swing is None or atr is None or atr <= 0:
        return False, tagged_high
    bar = bundle.bars_4h[j4]
    band = RANGE_ATR_FRAC * float(atr)
    swing_px = float(swing.price)
    near = abs(float(bar.high) - swing_px) <= band or float(bar.high) >= swing_px - band
    if near or float(bar.high) >= swing_px:
        tagged_high = True
    reclaim = tagged_high and float(bar.close) < swing_px
    return (near or reclaim), tagged_high


def _bearish_rsi_div_15m(bundle: TfBundle, *, asof_15: int) -> tuple[bool, dict]:
    """Price HH + RSI LH on last two confirmed 15m swing highs as-of asof_15.

    RSI taken at the swing bar index (pivot bar), not confirm bar.
    """
    highs = [
        s for s in bundle.swings_15m_h if s.confirm_index <= asof_15
    ]
    meta: dict = {
        "div_price_h1": None,
        "div_price_h2": None,
        "div_rsi_h1": None,
        "div_rsi_h2": None,
    }
    if len(highs) < 2:
        return False, meta
    h1, h2 = highs[-2], highs[-1]
    r1 = bundle.rsi_15m[h1.index] if h1.index < len(bundle.rsi_15m) else None
    r2 = bundle.rsi_15m[h2.index] if h2.index < len(bundle.rsi_15m) else None
    meta["div_price_h1"] = float(h1.price)
    meta["div_price_h2"] = float(h2.price)
    meta["div_rsi_h1"] = None if r1 is None else float(r1)
    meta["div_rsi_h2"] = None if r2 is None else float(r2)
    if r1 is None or r2 is None:
        return False, meta
    price_hh = float(h2.price) > float(h1.price)
    rsi_lh = float(r2) < float(r1)
    return (price_hh and rsi_lh), meta


def _bullish_rsi_div_15m(bundle: TfBundle, *, asof_15: int) -> tuple[bool, dict]:
    """Price LL + RSI HL on last two confirmed 15m swing lows (short skip)."""
    lows = [s for s in bundle.swings_15m_l if s.confirm_index <= asof_15]
    meta: dict = {
        "div_price_h1": None,
        "div_price_h2": None,
        "div_rsi_h1": None,
        "div_rsi_h2": None,
    }
    if len(lows) < 2:
        return False, meta
    l1, l2 = lows[-2], lows[-1]
    r1 = bundle.rsi_15m[l1.index] if l1.index < len(bundle.rsi_15m) else None
    r2 = bundle.rsi_15m[l2.index] if l2.index < len(bundle.rsi_15m) else None
    meta["div_price_h1"] = float(l1.price)
    meta["div_price_h2"] = float(l2.price)
    meta["div_rsi_h1"] = None if r1 is None else float(r1)
    meta["div_rsi_h2"] = None if r2 is None else float(r2)
    if r1 is None or r2 is None:
        return False, meta
    price_ll = float(l2.price) < float(l1.price)
    rsi_hl = float(r2) > float(r1)
    return (price_ll and rsi_hl), meta


def discover_setups(
    bundle: TfBundle,
    *,
    side: Side = LONG,
    trade_start_ms: int | None = None,
    trade_end_ms: int | None = None,
    rvol_gate: float | None = None,
) -> list[NotebookSetup]:
    """Event-driven setup discovery (no naive per-1m structure rebuild).

    rvol_gate: optional override of RVOL_GATE (default 1.0). Used by #144 T3
    at 0.8; omit/None keeps the locked #142/#143 threshold.
    """
    return _discover_setups_impl(
        bundle,
        side=side,
        trade_start_ms=trade_start_ms,
        trade_end_ms=trade_end_ms,
        rvol_gate=RVOL_GATE if rvol_gate is None else float(rvol_gate),
    )


def _discover_setups_impl(
    bundle: TfBundle,
    *,
    side: Side,
    trade_start_ms: int | None,
    trade_end_ms: int | None,
    rvol_gate: float = RVOL_GATE,
) -> list[NotebookSetup]:
    bars_1h = bundle.bars_1h
    bars_15 = bundle.bars_15m
    bars_1m = bundle.bars_1m
    out: list[NotebookSetup] = []

    j4 = -1
    tagged_low = False
    tagged_high = False

    searching = False
    msb_i = -1
    msb_close_ms = 0
    confirm_i = -1
    range_line = 0.0
    atr_c = 0.0
    sl_struct = 0.0
    confirmed = False
    i15_cursor = 0
    i1m_cursor = 0

    n1h = len(bars_1h)
    for i in range(n1h):
        bar = bars_1h[i]
        if not bar.closed:
            continue
        if trade_end_ms is not None and bar.ts_open_ms >= trade_end_ms:
            break

        j4 = map_htf_index(int(bar.ts_close_ms), bundle.bars_4h, start_from=j4)
        ctx_l, tagged_low = _4h_range_low_context(
            bundle, j4=j4, tagged_low=tagged_low
        )
        ctx_s, tagged_high = _4h_range_high_context(
            bundle, j4=j4, tagged_high=tagged_high
        )

        # Cancel search on opposite 1H MSB
        if searching:
            if side == LONG and i > 0:
                lvl = bundle.asof_1h_low[i - 1]
                if lvl is not None and float(bar.close) < float(lvl):
                    searching = False
                    confirmed = False
            elif side == SHORT and i > 0:
                lvl = bundle.asof_1h_high[i - 1]
                if lvl is not None and float(bar.close) > float(lvl):
                    searching = False
                    confirmed = False

        # Arm new MSB if not searching
        if not searching:
            in_win = True
            if trade_start_ms is not None and bar.ts_open_ms < trade_start_ms:
                in_win = False
            if in_win:
                if side == LONG and ctx_l and i > 0:
                    prior_h = bundle.asof_1h_high[i - 1]
                    if prior_h is not None and float(bar.close) > float(prior_h):
                        searching = True
                        confirmed = False
                        msb_i = i
                        msb_close_ms = int(bar.ts_close_ms)
                        confirm_i = -1
                        # 15m search starts after this 1H close
                        i15_cursor = first_bar_index_at_or_after(
                            bars_15, bar.ts_open_ms + 1, start=i15_cursor
                        )
                        # actually first 15m bar that closes after MSB close
                        while (
                            i15_cursor < len(bars_15)
                            and bars_15[i15_cursor].ts_close_ms <= msb_close_ms
                        ):
                            i15_cursor += 1
                elif side == SHORT and ctx_s and i > 0:
                    prior_l = bundle.asof_1h_low[i - 1]
                    if prior_l is not None and float(bar.close) < float(prior_l):
                        searching = True
                        confirmed = False
                        msb_i = i
                        msb_close_ms = int(bar.ts_close_ms)
                        confirm_i = -1
                        i15_cursor = first_bar_index_at_or_after(
                            bars_15, bar.ts_open_ms + 1, start=i15_cursor
                        )
                        while (
                            i15_cursor < len(bars_15)
                            and bars_15[i15_cursor].ts_close_ms <= msb_close_ms
                        ):
                            i15_cursor += 1

        if not searching:
            continue

        # Progress 15m confirm / 1m BOS up through this 1H bar's close
        # (and any 15m/1m that closed before next 1H). We process all 15m/1m
        # with ts_close <= current 1H close while searching; remaining handled
        # as 1H advances.
        horizon = int(bar.ts_close_ms)

        if not confirmed:
            while i15_cursor < len(bars_15) and bars_15[i15_cursor].ts_close_ms <= horizon:
                b15 = bars_15[i15_cursor]
                if side == LONG:
                    rl = bundle.asof_15m_low[i15_cursor]
                    if rl is not None and float(b15.close) >= float(rl):
                        # confirm
                        atrv = bundle.atr_15m[i15_cursor]
                        rvol = bundle.rvol_15m[i15_cursor]
                        if atrv is None or atrv <= 0:
                            i15_cursor += 1
                            continue
                        if rvol is None or float(rvol) < rvol_gate:
                            out.append(
                                NotebookSetup(
                                    side=side,
                                    msb_1h_index=msb_i,
                                    msb_1h_ts_close_ms=msb_close_ms,
                                    confirm_15m_index=i15_cursor,
                                    confirm_15m_ts_close_ms=int(b15.ts_close_ms),
                                    range_line=float(rl),
                                    atr_15m_at_confirm=float(atrv),
                                    sl_structural=float(rl) - SL_ATR_FRAC * float(atrv),
                                    bos_1m_index=-1,
                                    bos_1m_ts_open_ms=0,
                                    local_1m_swing=0.0,
                                    skipped="rvol",
                                )
                            )
                            searching = False
                            confirmed = False
                            i15_cursor += 1
                            break
                        # RSI div checked into entry (at BOS); store confirm now
                        confirm_i = i15_cursor
                        range_line = float(rl)
                        atr_c = float(atrv)
                        sl_struct = range_line - SL_ATR_FRAC * atr_c
                        confirmed = True
                        i1m_cursor = first_bar_index_at_or_after(
                            bars_1m, b15.ts_open_ms, start=i1m_cursor
                        )
                        while (
                            i1m_cursor < len(bars_1m)
                            and bars_1m[i1m_cursor].ts_close_ms
                            <= int(b15.ts_close_ms)
                        ):
                            i1m_cursor += 1
                        i15_cursor += 1
                        break
                else:  # SHORT
                    rh = bundle.asof_15m_high[i15_cursor]
                    if rh is not None and float(b15.close) <= float(rh):
                        atrv = bundle.atr_15m[i15_cursor]
                        rvol = bundle.rvol_15m[i15_cursor]
                        if atrv is None or atrv <= 0:
                            i15_cursor += 1
                            continue
                        if rvol is None or float(rvol) < rvol_gate:
                            out.append(
                                NotebookSetup(
                                    side=side,
                                    msb_1h_index=msb_i,
                                    msb_1h_ts_close_ms=msb_close_ms,
                                    confirm_15m_index=i15_cursor,
                                    confirm_15m_ts_close_ms=int(b15.ts_close_ms),
                                    range_line=float(rh),
                                    atr_15m_at_confirm=float(atrv),
                                    sl_structural=float(rh) + SL_ATR_FRAC * float(atrv),
                                    bos_1m_index=-1,
                                    bos_1m_ts_open_ms=0,
                                    local_1m_swing=0.0,
                                    skipped="rvol",
                                )
                            )
                            searching = False
                            confirmed = False
                            i15_cursor += 1
                            break
                        confirm_i = i15_cursor
                        range_line = float(rh)
                        atr_c = float(atrv)
                        sl_struct = range_line + SL_ATR_FRAC * atr_c
                        confirmed = True
                        i1m_cursor = first_bar_index_at_or_after(
                            bars_1m, b15.ts_open_ms, start=i1m_cursor
                        )
                        while (
                            i1m_cursor < len(bars_1m)
                            and bars_1m[i1m_cursor].ts_close_ms
                            <= int(b15.ts_close_ms)
                        ):
                            i1m_cursor += 1
                        i15_cursor += 1
                        break
                i15_cursor += 1

        if searching and confirmed:
            # 1m BOS until horizon or next cancel (cancel checked at 1H top)
            found = False
            while i1m_cursor < len(bars_1m) and bars_1m[i1m_cursor].ts_close_ms <= horizon:
                b1 = bars_1m[i1m_cursor]
                if side == LONG:
                    sh = bundle.asof_1m_high[i1m_cursor]
                    if sh is not None and float(b1.close) > float(sh):
                        # div check into entry on 15m as-of confirm (and any newer 15m)
                        j15_entry = map_htf_index(
                            int(b1.ts_close_ms), bars_15, start_from=confirm_i
                        )
                        div, meta = _bearish_rsi_div_15m(
                            bundle, asof_15=max(confirm_i, j15_entry)
                        )
                        if div:
                            out.append(
                                NotebookSetup(
                                    side=side,
                                    msb_1h_index=msb_i,
                                    msb_1h_ts_close_ms=msb_close_ms,
                                    confirm_15m_index=confirm_i,
                                    confirm_15m_ts_close_ms=int(
                                        bars_15[confirm_i].ts_close_ms
                                    ),
                                    range_line=range_line,
                                    atr_15m_at_confirm=atr_c,
                                    sl_structural=sl_struct,
                                    bos_1m_index=i1m_cursor,
                                    bos_1m_ts_open_ms=int(b1.ts_open_ms),
                                    local_1m_swing=float(sh),
                                    skipped="div",
                                    **meta,
                                )
                            )
                        else:
                            out.append(
                                NotebookSetup(
                                    side=side,
                                    msb_1h_index=msb_i,
                                    msb_1h_ts_close_ms=msb_close_ms,
                                    confirm_15m_index=confirm_i,
                                    confirm_15m_ts_close_ms=int(
                                        bars_15[confirm_i].ts_close_ms
                                    ),
                                    range_line=range_line,
                                    atr_15m_at_confirm=atr_c,
                                    sl_structural=sl_struct,
                                    bos_1m_index=i1m_cursor,
                                    bos_1m_ts_open_ms=int(b1.ts_open_ms),
                                    local_1m_swing=float(sh),
                                    skipped=None,
                                    **meta,
                                )
                            )
                        searching = False
                        confirmed = False
                        found = True
                        i1m_cursor += 1
                        break
                else:
                    slv = bundle.asof_1m_low[i1m_cursor]
                    if slv is not None and float(b1.close) < float(slv):
                        j15_entry = map_htf_index(
                            int(b1.ts_close_ms), bars_15, start_from=confirm_i
                        )
                        div, meta = _bullish_rsi_div_15m(
                            bundle, asof_15=max(confirm_i, j15_entry)
                        )
                        if div:
                            out.append(
                                NotebookSetup(
                                    side=side,
                                    msb_1h_index=msb_i,
                                    msb_1h_ts_close_ms=msb_close_ms,
                                    confirm_15m_index=confirm_i,
                                    confirm_15m_ts_close_ms=int(
                                        bars_15[confirm_i].ts_close_ms
                                    ),
                                    range_line=range_line,
                                    atr_15m_at_confirm=atr_c,
                                    sl_structural=sl_struct,
                                    bos_1m_index=i1m_cursor,
                                    bos_1m_ts_open_ms=int(b1.ts_open_ms),
                                    local_1m_swing=float(slv),
                                    skipped="div",
                                    **meta,
                                )
                            )
                        else:
                            out.append(
                                NotebookSetup(
                                    side=side,
                                    msb_1h_index=msb_i,
                                    msb_1h_ts_close_ms=msb_close_ms,
                                    confirm_15m_index=confirm_i,
                                    confirm_15m_ts_close_ms=int(
                                        bars_15[confirm_i].ts_close_ms
                                    ),
                                    range_line=range_line,
                                    atr_15m_at_confirm=atr_c,
                                    sl_structural=sl_struct,
                                    bos_1m_index=i1m_cursor,
                                    bos_1m_ts_open_ms=int(b1.ts_open_ms),
                                    local_1m_swing=float(slv),
                                    skipped=None,
                                    **meta,
                                )
                            )
                        searching = False
                        confirmed = False
                        found = True
                        i1m_cursor += 1
                        break
                i1m_cursor += 1
            del found

    return out


__all__ = [
    "ATR_PERIOD",
    "LEVERAGE_CAP",
    "LONG",
    "NotebookSetup",
    "PIVOT_N",
    "RANGE_ATR_FRAC",
    "RISK_M1",
    "RISK_M2",
    "RISK_M3",
    "RSI_PERIOD",
    "RVOL_GATE",
    "RVOL_N",
    "R_MULTIPLE",
    "SHORT",
    "SL_ATR_FRAC",
    "Side",
    "TfBundle",
    "atr_from_bars",
    "atr_wilder_series",
    "build_tf_bundle",
    "discover_setups",
    "map_htf_index",
]
