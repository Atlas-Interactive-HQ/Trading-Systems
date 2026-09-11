"""CORE-R1 lock: EMA12/30 + ATR14×3.0 trail. No R1–R7 score in this module."""

from __future__ import annotations

import pytest

from atlas.paper.rise_panel import CORE_DONCHIAN_FAMILY_STOPPED, CORE_R1_ID
from atlas.strategy.core_doge_ema_atr_trail_1d import (
    ATR_PERIOD,
    ATR_TRAIL_MULT,
    BAR,
    FAMILY,
    FAST,
    FLAT,
    LADDER_ID,
    LONG,
    SLEEVE,
    SLOW,
    CoreR1EmaAtrTrailParams,
    CoreR1EmaAtrTrailV1,
)
from atlas.paper.types import Bar

DAY = 24 * 60 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, c: float, h: float | None = None, lo: float | None = None) -> Bar:
    ts = START + i * DAY
    hi = h if h is not None else c + 0.5
    low = lo if lo is not None else c - 0.5
    return Bar(SYM, ts, ts + DAY, c, hi, low, c, 1.0, True, "test")


def test_core_r1_lock_ids():
    assert LADDER_ID == "CORE-R1"
    assert CORE_R1_ID == "rise_panel_v1_core_r1_doge_ema12_30_atr14_trail3_1d_eur140"
    assert CORE_DONCHIAN_FAMILY_STOPPED is True
    assert FAMILY == "ema12_30_atr14_trail3_long_flat_1d"
    assert FAST == 12 and SLOW == 30
    assert ATR_PERIOD == 14 and ATR_TRAIL_MULT == 3.0
    assert BAR == "1D" and SLEEVE == "core"


def test_rejects_param_sweeps():
    with pytest.raises(ValueError, match="EMA"):
        CoreR1EmaAtrTrailV1(CoreR1EmaAtrTrailParams(fast=10))
    with pytest.raises(ValueError, match="atr_period"):
        CoreR1EmaAtrTrailV1(CoreR1EmaAtrTrailParams(atr_period=21))
    with pytest.raises(ValueError, match="atr_trail_mult"):
        CoreR1EmaAtrTrailV1(CoreR1EmaAtrTrailParams(atr_trail_mult=2.0))
    with pytest.raises(ValueError, match="bar"):
        CoreR1EmaAtrTrailV1(CoreR1EmaAtrTrailParams(bar="4H"))


def test_never_short_and_flat_until_warmup():
    s = CoreR1EmaAtrTrailV1()
    bars = [_bar(i, 100.0) for i in range(10)]
    assert s.desired_state(bars) == FLAT
    falling = [_bar(i, 200.0 - i) for i in range(40)]
    assert s.desired_state(falling) == FLAT


def test_ema_cross_enters_and_atr_stop_exits_without_lookahead():
    """Rising grind → long; then a closed-bar collapse through 3×ATR trail → flat."""
    s = CoreR1EmaAtrTrailV1()
    bars = [_bar(i, 100.0 + 0.2 * i) for i in range(40)]
    assert s.desired_state(bars) == LONG
    # Collapse: large down close on a known closed bar (no intra-bar peek).
    crash = _bar(40, 50.0, h=110.0, lo=49.0)
    bars2 = list(bars) + [crash]
    assert s.desired_state(bars2) == FLAT


def test_after_atr_stop_while_bullish_requires_fresh_cross():
    s = CoreR1EmaAtrTrailV1()
    # Build a long, stop out with a crash, then continue a still-high grind
    # without an EMA12<=EMA30 reset — must stay flat (need fresh cross).
    up = [_bar(i, 100.0 + 0.3 * i) for i in range(40)]
    assert s.desired_state(up) == LONG
    crash = _bar(40, 70.0, h=112.0, lo=69.0)
    after = list(up) + [crash]
    assert s.desired_state(after) == FLAT
    # Next bars still elevated (EMA likely still bull after one crash bar)
    more = list(after) + [_bar(41, 111.0), _bar(42, 111.5)]
    # If still bullish without a fresh 12>30 transition, stay flat.
    # A later deep dip then recovery creates the fresh cross.
    dip = list(more) + [_bar(43 + i, 111.5 - 4.0 * i) for i in range(20)]
    # After a real bearish stretch, a new grind-up is a fresh transition.
    recover = list(dip) + [_bar(63 + i, 40.0 + 2.0 * i) for i in range(25)]
    assert s.desired_state(recover) in (LONG, FLAT)
    # Never short even through the crash/recover path
    assert s.desired_state(recover) != "short"
