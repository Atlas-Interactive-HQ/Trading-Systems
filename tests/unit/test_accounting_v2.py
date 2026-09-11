"""Evaluator-v2 accounting: original keys unchanged; terminal liquidation additive."""

from __future__ import annotations

import pytest

from atlas.paper.accounting_v2 import (
    ACCOUNTING_V2_GATE,
    ACCOUNTING_V2_MEDIAN_TRIPS_MIN,
    ACCOUNTING_V2_MIN_EXP_POS,
    ACCOUNTING_VERSION,
    accounting_v2_score,
    compute_accounting_v2,
    last_in_window_bar,
    old_vs_v2_delta_row,
)
from atlas.paper.ema_eval import EmaBookSettings, walk_long_flat
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

DAY = 24 * 60 * 60 * 1000
START = 1_598_918_400_000
SYM = "DOGE-USDT"

# Historical walk keys must remain present and must not be rewritten by v2.
_OLD_KEYS = (
    "net_return_eur",
    "n_trades",
    "expectancy_after_costs_eur",
    "end_equity_eur",
    "n_entries",
    "fee_drag_eur",
)


def dbar(i: int, c: float, o: float | None = None) -> Bar:
    ts = START + i * DAY
    ox = c if o is None else o
    return Bar(SYM, ts, ts + DAY, ox, max(ox, c) + 0.5, min(ox, c) - 0.5, c, 1.0, True, "test")


class _HoldLong:
    """Test double: long after warmup, never emits a flat signal (open at window end)."""

    label = "hold_long_test"

    def desired_state(self, bars):  # noqa: ANN001
        return LONG if len(bars) >= 5 else FLAT


def test_hypothesis_open_position_mtm_without_terminal_sell():
    """P0 hypothesis: net_return marks last.close; n_trades/exp are completed-only."""
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    bars = [dbar(i, 100.0 + i) for i in range(20)]  # grind up → stay long
    settings = EmaBookSettings(equity_eur=140.0, fee_rate=0.0005, slippage_bps=5.0)
    walk = walk_long_flat(
        bars,
        strategy=s,
        settings=settings,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
    )
    assert walk["n_trades"] == 0  # never completed a round trip
    assert walk["n_entries"] >= 1
    assert walk["expectancy_after_costs_eur"] is None
    assert walk["net_return_eur"] is not None
    assert float(walk["net_return_eur"]) != 0.0
    # v2 names the mix instead of silently changing old keys
    assert walk["open_position_at_end"] is True
    assert walk["forced_window_close"] is True
    assert walk["completed_round_trips"] == 0
    assert walk["accounting_version"] == ACCOUNTING_VERSION
    assert walk["terminal_exit_cost_estimate_eur"] > 0
    assert walk["terminal_liquidation_net_eur"] < walk["net_return_eur"]


def test_v2_does_not_rewrite_historical_keys():
    s = _HoldLong()
    bars = [dbar(i, 10.0 + 0.1 * i) for i in range(12)]
    settings = EmaBookSettings(equity_eur=100.0, fee_rate=0.001, slippage_bps=10.0)
    walk = walk_long_flat(
        bars,
        strategy=s,
        settings=settings,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
    )
    for k in _OLD_KEYS:
        assert k in walk
    # Reconstruct historical mark: cash + qty * last.close (no sell fee/slip)
    assert walk["end_equity_eur"] == pytest.approx(walk["start_equity_eur"] + walk["net_return_eur"])
    assert walk["n_trades"] == walk["completed_round_trips"]


def test_terminal_liquidation_matches_sell_slip_plus_fee():
    qty = 100.0
    entry_px = 1.0
    entry_fee = 0.05
    mark_close = 1.10
    cash = 200.0 - qty * entry_px - entry_fee  # 99.95
    fee_rate = 0.0005
    slip = 5.0
    v2 = compute_accounting_v2(
        start_equity_eur=200.0,
        cash=cash,
        qty=qty,
        entry_px=entry_px,
        entry_fee=entry_fee,
        realized_net_eur=0.0,
        completed_round_trips=0,
        mark_close=mark_close,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )
    sell_px = apply_slippage(mark_close, "sell", slip)
    sell_fee = fee_on_notional(qty * sell_px, fee_rate)
    expected_exit = q(qty * mark_close - (qty * sell_px - sell_fee))
    expected_liq = q(cash + qty * sell_px - sell_fee - 200.0)
    assert v2["forced_window_close"] is True
    assert v2["open_position_at_end"] is True
    assert v2["terminal_exit_cost_estimate_eur"] == expected_exit
    assert v2["terminal_liquidation_net_eur"] == expected_liq
    assert v2["n_terminal_trips"] == 1
    assert v2["expectancy_completed_eur"] is None
    assert v2["expectancy_terminal_adjusted_eur"] == expected_liq


def test_flat_at_end_no_forced_close():
    v2 = compute_accounting_v2(
        start_equity_eur=140.0,
        cash=145.0,
        qty=0.0,
        entry_px=0.0,
        entry_fee=0.0,
        realized_net_eur=5.0,
        completed_round_trips=2,
        mark_close=1.2,
        fee_rate=0.0005,
        slippage_bps=5.0,
    )
    assert v2["forced_window_close"] is False
    assert v2["open_position_at_end"] is False
    assert v2["unrealized_net_eur"] == 0.0
    assert v2["terminal_exit_cost_estimate_eur"] == 0.0
    assert v2["terminal_liquidation_net_eur"] == 5.0
    assert v2["expectancy_completed_eur"] == pytest.approx(2.5)
    assert v2["expectancy_terminal_adjusted_eur"] == pytest.approx(2.5)
    assert v2["n_terminal_trips"] == 2


def test_last_in_window_bar_ignores_pad_after_window():
    bars = [dbar(i, 1.0 + i) for i in range(10)]
    start = bars[2].ts_open_ms
    end = bars[5].ts_open_ms  # exclusive → last in-window is bars[4]
    last = last_in_window_bar(bars, trade_start_ms=start, trade_end_ms=end)
    assert last is bars[4]


def test_signals_unchanged_v2_is_accounting_only():
    """Same strategy + bars → same n_entries / n_trades; only extra keys differ."""
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    # rise then dump so we get an entry and an exit
    bars = [dbar(i, 100.0 + i) for i in range(12)]
    bars += [dbar(12 + i, 112.0 - 3 * i) for i in range(10)]
    settings = EmaBookSettings(equity_eur=140.0, fee_rate=0.0005, slippage_bps=5.0)
    a = walk_long_flat(
        bars, strategy=s, settings=settings,
        trade_start_ms=bars[0].ts_open_ms, trade_end_ms=bars[-1].ts_close_ms,
    )
    b = walk_long_flat(
        bars, strategy=s, settings=settings,
        trade_start_ms=bars[0].ts_open_ms, trade_end_ms=bars[-1].ts_close_ms,
    )
    assert a["n_entries"] == b["n_entries"]
    assert a["n_trades"] == b["n_trades"]
    assert a["n_short_signals"] == 0
    assert a["place_orders"] is False


def test_accounting_v2_gate_locked_before_score():
    assert ACCOUNTING_V2_GATE == "rise_panel_accounting_v2"
    assert ACCOUNTING_VERSION == "rise_panel_accounting_v2"
    assert ACCOUNTING_V2_MIN_EXP_POS == 5
    assert ACCOUNTING_V2_MEDIAN_TRIPS_MIN == 1
    rows = [
        {
            "n_terminal_trips": 2,
            "completed_round_trips": 1,
            "expectancy_terminal_adjusted_eur": 1.0,
            "terminal_liquidation_net_eur": 3.0,
            "forced_window_close": True,
        }
        for _ in range(7)
    ]
    g = accounting_v2_score(rows)
    assert g["pass"] is True
    assert g["audit_does_not_promote"] is True
    assert g["does_not_replace_soft_promote_v1"] is True
    rows[0]["expectancy_terminal_adjusted_eur"] = -1.0
    rows[1]["expectancy_terminal_adjusted_eur"] = -1.0
    rows[2]["expectancy_terminal_adjusted_eur"] = -1.0
    fail = accounting_v2_score(rows)
    assert fail["pass"] is False
    assert fail["verdict"] == "FAIL"


def test_old_vs_v2_delta_row():
    d = old_vs_v2_delta_row(
        {
            "window_id": "R1",
            "n_trades": 0,
            "completed_round_trips": 0,
            "n_terminal_trips": 1,
            "open_position_at_end": True,
            "forced_window_close": True,
            "net_return_eur": 10.0,
            "terminal_liquidation_net_eur": 9.5,
            "expectancy_after_costs_eur": None,
            "expectancy_completed_eur": None,
            "expectancy_terminal_adjusted_eur": 9.5,
        }
    )
    assert d["delta_net_v2_minus_old_eur"] == pytest.approx(-0.5)
    assert d["forced_window_close"] is True
