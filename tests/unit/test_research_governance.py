"""Governance stubs: SHADOW, ledger, edge-vs-luck, markout, portfolio, board."""

from __future__ import annotations

from pathlib import Path

from atlas.research.edge_vs_luck import (
    EDGE_CONFIRMED_PERCENTILE,
    EDGE_STRONG_PERCENTILE,
    S1_DEV_PANEL_NET_DELTA_EUR,
    STRESS_MATRIX,
    classify_edge,
    stress_plan,
)
from atlas.research.governance import BOARD_ORDER, CURRENT_BOARD_STEP, board_card
from atlas.research.h1_markout import (
    ECONOMIC_PNL_GATE,
    MARKOUT_HORIZONS_MS,
    economic_pnl_allowed,
    markout_card,
)
from atlas.research.portfolio import (
    CASH_IS_VALID_ALLOCATION,
    CORE_MAJOR_V1,
    portfolio_card,
    sleeve_allocation,
)
from atlas.research.shadow_contiguous import (
    SHADOW_END_UTC,
    SHADOW_START_UTC,
    lock_shadow_interval,
    refuse_hand_picked_windows,
    shadow_lock_card,
)
from atlas.research.trial_ledger import (
    TRIAL_LEDGER_FIELDS,
    load_trial_ledger,
    multiplicity_note,
)


LEDGER = Path(__file__).resolve().parents[2] / "research" / "trial_ledger.jsonl"


def test_board_order_and_invariants():
    card = board_card()
    assert CURRENT_BOARD_STEP == "A"
    assert [s for s, _ in BOARD_ORDER] == ["A", "B", "C", "D", "E", "F"]
    assert card["p4a_may_lock_instrument"] is False
    assert card["this_pr_scores_strategies"] is False
    assert card["this_pr_selects_hft_instrument"] is False
    assert card["soft_pass_neq_arm"] is True
    assert card["r1_r7_dev_eliminate_only_paused"] is True
    assert card["default_yaml_untouched"] is True


def test_shadow_refuses_invented_dates_and_hand_picked_windows():
    assert SHADOW_START_UTC is None
    assert SHADOW_END_UTC is None
    card = shadow_lock_card()
    assert card["locked"] is False
    assert card["do_not_invent_shadow_dates"] is True
    assert card["hand_picked_rise_chop_down_forbidden_as_selection"] is True
    reject = refuse_hand_picked_windows(["S1", "F1", "D1"])
    assert reject["accepted"] is False
    assert reject["fail_closed"] is True
    locked = lock_shadow_interval("2025-01-01", "2025-03-31")
    assert locked["locked"] is False
    assert locked["start_utc"] is None
    assert locked["do_not_invent_shadow_dates"] is True


def test_trial_ledger_starter_loads_and_validates():
    required = {
        "trial_id",
        "parent_trial",
        "family",
        "hypothesis",
        "parameters",
        "asset",
        "timeframe",
        "data_seen_before_lock",
        "dataset",
        "lock_commit",
        "score_commit",
        "result",
        "pass_fail",
        "pre_registered",
        "post_hoc",
        "global_trial_count",
        "family_trial_count",
    }
    assert required <= set(TRIAL_LEDGER_FIELDS)
    rows = load_trial_ledger(LEDGER)
    ids = [r.trial_id for r in rows]
    assert ids == [
        "TL-INT85",
        "TL-M1",
        "TL-S1",
        "TL-C1",
        "TL-C2",
        "TL-CORE-R1",
        "TL-SCALP-R2",
        "TL-DEV-BOARD",
        "TL-H0",
        "TL-109",
        "TL-110",
        "TL-111",
        "TL-113",
        "TL-114",
    ]
    assert all(r.not_a_forecast and r.soft_pass_neq_arm for r in rows)
    assert all(r.pre_registered and not r.post_hoc for r in rows)
    s1 = next(r for r in rows if r.trial_id == "TL-S1")
    assert s1.result["dev_panel_net_delta_eur_cited"] == 1.4637
    assert s1.score_commit.startswith("7f16b72")
    h0 = next(r for r in rows if r.trial_id == "TL-H0")
    assert h0.pass_fail == "N/A_health_only"
    assert h0.result["health_stale_pct_cited"] == 39.22
    assert h0.result["carried_forward_pct_cited"] == 57.65
    assert h0.result["no_hft_pnl"] is True
    board = next(r for r in rows if r.trial_id == "TL-110")
    assert board.parent_trial == "TL-DEV-BOARD"
    assert board.parameters["core_allocation"] == "cash"
    assert board.parameters["hft"] == "wait_p4b"
    tl111 = next(r for r in rows if r.trial_id == "TL-111")
    assert tl111.parent_trial == "TL-109"
    assert tl111.family == "ops"
    assert tl111.pre_registered is True
    assert tl111.post_hoc is False
    assert tl111.pass_fail == "N/A_ops_ping_lock_not_a_score"
    assert tl111.parameters["ping_triggers"] == ["stop_loss_fill", "stop_release"]
    assert tl111.parameters["send"] is False
    assert tl111.parameters["live_arm"] is False
    assert "phase1/112" in tl111.parameters["does_not_re_lock"]
    assert tl111.place_orders is False
    assert tl111.result["invented_metrics"] is False
    tl113 = next(r for r in rows if r.trial_id == "TL-113")
    assert tl113.parent_trial == "TL-DEV-BOARD"
    assert tl113.family == "governance"
    assert tl113.pre_registered is True
    assert tl113.post_hoc is False
    assert tl113.pass_fail == "N/A_architecture_lock_not_a_score"
    assert tl113.parameters["ratio_core_mid_scalp"] == [6, 3, 1]
    assert tl113.parameters["core_asset"] == "BTC"
    assert tl113.parameters["mid_asset"] == "DOGE"
    assert tl113.parameters["scalp_asset"] == "PEPE"
    assert tl113.parameters["scalp_inst_id"] is None
    assert tl113.parameters["scalp_listing_verified"] is False
    assert tl113.parameters["live_arm"] is False
    assert tl113.parameters["default_yaml_untouched"] is True
    assert tl113.parameters["invent_pnl"] is False
    assert tl113.place_orders is False
    assert tl113.result["invented_inst_id"] is False
    tl114 = next(r for r in rows if r.trial_id == "TL-114")
    assert tl114.parent_trial == "TL-113"
    assert tl114.family == "governance"
    assert tl114.pre_registered is True
    assert tl114.post_hoc is False
    assert tl114.pass_fail == "N/A_universe_policy_lock_not_a_score"
    assert tl114.parameters["ratio_core_mid_scalp"] == [6, 3, 1]
    assert tl114.parameters["scalp_share_of_book"] == 0.10
    assert tl114.parameters["one_scalp_bucket"] is True
    assert tl114.parameters["multi_coin_watch"] is True
    assert tl114.parameters["preferred_if_demo_clear"] == "PEPE"
    assert tl114.parameters["pepe_demo_clear"] is False
    assert tl114.parameters["alternatives_ranked"] is False
    assert tl114.parameters["invent_expectancy"] is False
    assert tl114.parameters["invent_order_inst_id"] is False
    assert tl114.parameters["catalogue_clear_neq_demo_clear"] is True
    assert tl114.parameters["live_arm"] is False
    assert tl114.parameters["default_yaml_untouched"] is True
    assert tl114.place_orders is False
    assert tl114.result["invented_expectancy"] is False
    assert tl114.result["ranked_alternatives"] is False
    note = multiplicity_note(rows)
    assert note["invented_deflated_sharpe"] is False
    assert note["dsr_pbo"] == "conceptual_reference_only"


def test_edge_vs_luck_not_scored_until_shadow():
    assert EDGE_CONFIRMED_PERCENTILE == 90
    assert EDGE_STRONG_PERCENTILE == 95
    assert S1_DEV_PANEL_NET_DELTA_EUR == 1.4637
    assert "chronological_shadow" in STRESS_MATRIX
    pending = classify_edge(1.0, [0.0, 0.1, 0.2], shadow_locked=False)
    assert pending["verdict"] == "not_scored"
    plan = stress_plan()
    assert plan["scored"] is False
    assert plan["stress_is_not_a_new_strategy"] is True

    xs = [float(i) for i in range(101)]
    # obs 91 > p90 (90) and <= p95 (95) → EDGE_CONFIRMED
    assert classify_edge(91.0, xs, shadow_locked=True)["verdict"] == "EDGE_CONFIRMED"
    assert classify_edge(96.0, xs, shadow_locked=True)["verdict"] == "STRONG"
    assert classify_edge(90.0, xs, shadow_locked=True)["verdict"] == "INCONCLUSIVE"


def test_h1_markout_gate_and_no_rewrite():
    card = markout_card()
    assert card["rewrite_locked_1s_h1"] is False
    assert card["h1_clock_horizons_s"] == [1, 3, 5, 10]
    assert MARKOUT_HORIZONS_MS[0] == 100
    assert MARKOUT_HORIZONS_MS[-1] == 10_000
    assert ECONOMIC_PNL_GATE == (
        "signal_green",
        "markout_green",
        "queue_latency",
        "economic_paper_pnl",
    )
    blocked = economic_pnl_allowed(
        signal_green=True, markout_green=False, queue_latency_ok=True
    )
    assert blocked["allowed"] is False
    assert blocked["next"] == "markout_green"
    ok = economic_pnl_allowed(
        signal_green=True, markout_green=True, queue_latency_ok=True
    )
    assert ok["allowed"] is True


def test_portfolio_cash_and_core_major_not_scored():
    card = portfolio_card()
    assert card["strategy_green_is_not_portfolio_green"] is True
    assert card["cash_is_valid_allocation"] is True
    assert CORE_MAJOR_V1["scored"] is False
    assert CORE_MAJOR_V1["r1_r7_coin_pick_forbidden"] is True
    cash = sleeve_allocation(validated_edge=False)
    assert cash["allocation"] == 0.0
    assert cash["cash"] is True
    assert CASH_IS_VALID_ALLOCATION is True
