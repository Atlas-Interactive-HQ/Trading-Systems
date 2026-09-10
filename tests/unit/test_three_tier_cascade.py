"""Unit tests: one-way capital flow + halt on Mid/Scalp depletion."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import (
    CORE_START_EUR,
    MID_START_EUR,
    SCALP_START_EUR,
    TOTAL_START_EUR,
    CascadeLedger,
    RealizedTrade,
    replay_cascade_from_trades,
    utc_iso_week,
)


def test_start_allocation_7_2_1():
    led = CascadeLedger()
    assert led.core.equity_eur == CORE_START_EUR
    assert led.mid.equity_eur == MID_START_EUR
    assert led.scalp.equity_eur == SCALP_START_EUR
    assert led.total_equity_eur() == TOTAL_START_EUR
    assert TOTAL_START_EUR == 200.0


def test_one_way_weekly_transfer_scalp_to_mid_to_core():
    # Week 1 trades (2023-10-02 is Monday ISO week)
    # Scalp +5, Mid +3 → weekly sweep: scalp→mid 5, then mid pending 3+5=8 → core 8
    trades = [
        RealizedTrade("scalp", 1_696_204_800_000, 5.0),  # 2023-10-02
        RealizedTrade("mid", 1_696_204_800_000 + 60_000, 3.0),
    ]
    led = replay_cascade_from_trades(trades, final_ts_ms=1_696_204_800_000 + 86400_000)
    # After apply: scalp 25, mid 43; pending scalp 5, mid 3
    # Final weekly: scalp→mid 5 → scalp 20, mid 48 (pending mid still 3)
    # then mid→core 3 → mid 45, core 143. Inbound capital is not re-swept same week.
    assert led.scalp.equity_eur == pytest.approx(20.0)
    assert led.mid.equity_eur == pytest.approx(45.0)
    assert led.core.equity_eur == pytest.approx(143.0)
    assert led.total_upward_transferred_eur() == pytest.approx(8.0)
    assert all(t.source in ("scalp", "mid") for t in led.transfers)
    assert all(t.dest in ("mid", "core") for t in led.transfers)
    # No downward
    assert not any(t.source == "core" for t in led.transfers)
    assert not any(t.dest == "scalp" for t in led.transfers)


def test_min_transfer_threshold_skips_noise():
    trades = [RealizedTrade("scalp", 1_696_204_800_000, 0.50)]
    led = replay_cascade_from_trades(trades, final_ts_ms=1_696_204_800_000 + 1000)
    assert led.transfers == []
    assert led.scalp.equity_eur == pytest.approx(20.5)
    assert led.scalp.realized_profit_pending_eur == pytest.approx(0.50)


def test_losses_shrink_tier_no_downward_refill():
    led = CascadeLedger()
    led.apply_trade_pnl("mid", -10.0)
    assert led.mid.equity_eur == pytest.approx(30.0)
    assert led.core.equity_eur == CORE_START_EUR
    assert led.scalp.equity_eur == SCALP_START_EUR
    # Core cannot send capital down
    led.weekly_rebalance(ts_ms=1_696_204_800_000)
    assert led.mid.equity_eur == pytest.approx(30.0)


def test_depletion_halts_mid_and_scalp():
    led = CascadeLedger()
    led.apply_trade_pnl("scalp", -20.0)
    assert led.scalp.equity_eur == pytest.approx(0.0)
    assert led.scalp.halted is True
    assert led.scalp.can_enter() is False
    led.apply_trade_pnl("mid", -40.0)
    assert led.mid.halted is True
    assert led.mid.can_enter() is False
    # Core never auto-halts from this helper
    assert led.core.halted is False


def test_manual_inject_clears_halt_only():
    led = CascadeLedger()
    led.apply_trade_pnl("scalp", -20.0)
    assert led.scalp.halted
    led.scalp.manual_inject(5.0)
    assert led.scalp.halted is False
    assert led.scalp.equity_eur == pytest.approx(5.0)
    assert led.scalp.can_enter() is True


def test_no_downward_path_in_upward_order():
    from atlas.paper.cascade import UPWARD_ORDER

    assert UPWARD_ORDER == (("scalp", "mid"), ("mid", "core"))
    assert ("core", "mid") not in UPWARD_ORDER
    assert ("mid", "scalp") not in UPWARD_ORDER


def test_utc_iso_week_stable():
    # 2023-10-02 Monday
    assert utc_iso_week(1_696_204_800_000) == "2023-W40"
