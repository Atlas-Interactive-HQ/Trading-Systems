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
    ]
    assert all(r.not_a_forecast and r.soft_pass_neq_arm for r in rows)
    assert all(r.pre_registered and not r.post_hoc for r in rows)
    s1 = next(r for r in rows if r.trial_id == "TL-S1")
    assert s1.result["dev_panel_net_delta_eur_cited"] == 1.4637
    assert s1.score_commit.startswith("7f16b72")
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
