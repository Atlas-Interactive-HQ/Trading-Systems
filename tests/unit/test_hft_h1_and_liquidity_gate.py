"""H1 ensemble lock + liquidity-gate schema. No invented capture / no PnL."""

from __future__ import annotations

from atlas.scalp_hft.h1_ensemble import (
    H1_LOCK_ID,
    HORIZONS_S,
    MICRO_SCORE_THRESHOLD,
    confirmed_2of3,
    h1_side,
    lock_card,
    micro_score,
)
from atlas.scalp_hft.liquidity_gate import (
    KNOWN_XPERP_HINTS,
    LIQUIDITY_GATE_BASES,
    LiquidityGateMetrics,
    LiquidityGatePlan,
    resolve_liquidity_inst_ids,
    select_instrument,
)


def test_micro_score_equal_weight_no_optimize():
    assert micro_score(1.0, 2.0, 3.0) == 2.0
    assert micro_score(1.0, None, 3.0) is None
    assert MICRO_SCORE_THRESHOLD == 1.0
    assert HORIZONS_S == (1, 3, 5, 10)
    card = lock_card()
    assert card["lock_id"] == H1_LOCK_ID
    assert card["weight_optimize"] is False
    assert card["signal_only_first"] is True
    assert card["economic_pnl_before_signal_study_frozen"] is False
    assert card["no_hft_pnl_in_this_module"] is True


def test_h1_side_requires_health_and_confirmation():
    assert (
        h1_side(
            healthy=False,
            ema12=2.0,
            ema21=1.0,
            score=2.0,
            confirm_long=[True, True, True],
            confirm_short=[False, False, False],
        )
        == "flat"
    )
    assert (
        h1_side(
            healthy=True,
            ema12=2.0,
            ema21=1.0,
            score=2.0,
            confirm_long=[False, True, True],
            confirm_short=[False, False, False],
        )
        == "long"
    )
    assert (
        h1_side(
            healthy=True,
            ema12=1.0,
            ema21=2.0,
            score=-2.0,
            confirm_long=[False, False, False],
            confirm_short=[True, True, False],
        )
        == "short"
    )
    assert confirmed_2of3([True]) is False


def test_liquidity_gate_plan_does_not_invent_eth():
    assert LIQUIDITY_GATE_BASES == ("BTC", "ETH", "DOGE")
    assert KNOWN_XPERP_HINTS["ETH"] is None
    plan = LiquidityGatePlan().to_dict()
    assert plan["no_strategy_pnl"] is True
    assert plan["do_not_invent_capture_numbers"] is True
    # no rows → fail closed, no invented winner
    sel = select_instrument([])
    assert sel["fail_closed"] is True
    assert sel["selected"] is None
    assert "insufficient_data" in sel["reason"]


def test_resolve_liquidity_fail_closed_on_missing_eth():
    rows = [
        {
            "instId": "BTC-USD_UM_XPERP-310404",
            "uly": "BTC-USD",
            "ruleType": "xperp",
            "state": "live",
            "settleCcy": "USD",
        },
        {
            "instId": "DOGE-USD_UM_XPERP-310404",
            "uly": "DOGE-USD",
            "ruleType": "xperp",
            "state": "live",
            "settleCcy": "USD",
        },
    ]
    out = resolve_liquidity_inst_ids(rows)
    assert out["ok"] is False
    assert "ETH" in out["missing"]
    assert out["fail_closed"] is True
    assert out["do_not_invent_eth_instid"] is True


def test_select_uses_pre_registered_rule_not_pnl():
    rows = [
        LiquidityGateMetrics(
            inst_id="A",
            base="BTC",
            span_s=86400,
            trades_per_sec=2.0,
            books5_changes_per_sec=8.0,
            spread_bps_median=2.0,
            top5_depth_notional_median=1000.0,
            reconnect_count=1,
            book_age_ms_median=200.0,
            insufficient_data=False,
        ),
        LiquidityGateMetrics(
            inst_id="B",
            base="ETH",
            span_s=86400,
            trades_per_sec=3.0,
            books5_changes_per_sec=12.0,
            spread_bps_median=3.0,
            top5_depth_notional_median=800.0,
            reconnect_count=1,
            book_age_ms_median=150.0,
            insufficient_data=False,
        ),
        LiquidityGateMetrics(
            inst_id="C",
            base="DOGE",
            span_s=86400,
            trades_per_sec=1.0,
            books5_changes_per_sec=4.0,
            spread_bps_median=8.0,
            top5_depth_notional_median=200.0,
            reconnect_count=1,
            book_age_ms_median=400.0,
            insufficient_data=False,
        ),
    ]
    sel = select_instrument(rows)
    assert sel["fail_closed"] is False
    assert sel["selected"]["inst_id"] == "B"  # highest books5 changes/sec
    assert sel["no_strategy_pnl"] is True
