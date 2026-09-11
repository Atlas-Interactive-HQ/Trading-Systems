"""Unit tests: CORE-R1 first-score harness locks + accounting_v2 deltas (no R1–R7 run)."""

from __future__ import annotations

from atlas.paper.accounting_v2 import (
    ACCOUNTING_V2_GATE,
    ACCOUNTING_V2_MEDIAN_TRIPS_MIN,
    ACCOUNTING_V2_MIN_EXP_POS,
    ACCOUNTING_VERSION,
)
from atlas.paper.cascade import CORE_START_EUR
from atlas.paper.rise_panel import BASELINE_ID, CORE_DONCHIAN_FAMILY_STOPPED, CORE_R1_ID
from atlas.paper.rise_panel_accounting_v2_eval import CANDIDATES
from atlas.paper.rise_panel_core_r1_ema_atr_trail_1d_eval import (
    CORE_C0_ID,
    CORE_C0_KEY,
    CORE_R1_KEY,
    CORE_R1_SPEC,
    LOCK_NOTE,
    completed_panel_summary,
    deltas_vs_core_c0,
    render_results_markdown,
)
from atlas.strategy.core_doge_ema_atr_trail_1d import (
    ATR_PERIOD,
    ATR_TRAIL_MULT,
    BAR,
    FAMILY,
    FAST,
    LADDER_ID,
    SLEEVE,
    SLOW,
)


def test_ids_and_lock_unchanged():
    assert CORE_C0_ID == BASELINE_ID == "rise_panel_v1_core_doge_ema12_30_1d_eur140"
    assert CORE_R1_ID == "rise_panel_v1_core_r1_doge_ema12_30_atr14_trail3_1d_eur140"
    assert CORE_R1_SPEC["candidate_id"] == CORE_R1_ID
    assert CORE_R1_SPEC["id"] == CORE_R1_KEY
    assert CORE_R1_SPEC["bar"] == "1D"
    assert CORE_R1_SPEC["pad_days"] == 40
    assert float(CORE_R1_SPEC["equity"]) == CORE_START_EUR == 140.0
    assert CORE_DONCHIAN_FAMILY_STOPPED is True
    assert LADDER_ID == "CORE-R1"
    assert FAMILY == "ema12_30_atr14_trail3_long_flat_1d"
    assert FAST == 12 and SLOW == 30
    assert ATR_PERIOD == 14 and ATR_TRAIL_MULT == 3.0
    assert BAR == "1D" and SLEEVE == "core"
    assert LOCK_NOTE == "phase1/94-core-r1-lock.md"


def test_accounting_v2_gate_not_rewritten():
    """Do not create green by changing the v2 gate after seeing results."""
    assert ACCOUNTING_VERSION == "rise_panel_accounting_v2"
    assert ACCOUNTING_V2_GATE == "rise_panel_accounting_v2"
    assert ACCOUNTING_V2_MIN_EXP_POS == 5
    assert ACCOUNTING_V2_MEDIAN_TRIPS_MIN == 1


def test_default_accounting_v2_audit_candidates_exclude_core_r1():
    """#91 audit of UNCHANGED strategies stays 7; CORE-R1 is a separate first score."""
    ids = [c["id"] for c in CANDIDATES]
    assert CORE_C0_KEY in ids
    assert CORE_R1_KEY not in ids
    assert "core_r1_ema_atr_trail" not in ids
    assert len(ids) == 7


def test_completed_panel_summary_uses_realized_only():
    rows = [
        {
            "completed_round_trips": 0,
            "n_trades": 0,
            "expectancy_completed_eur": None,
            "realized_net_eur": 0.0,
            "max_dd_eur": 10.0,
            "time_in_market": 0.5,
            "n_entries": 1,
            "open_position_at_end": True,
            "forced_window_close": True,
        },
        {
            "completed_round_trips": 2,
            "n_trades": 2,
            "expectancy_completed_eur": -3.0,
            "realized_net_eur": -6.0,
            "max_dd_eur": 20.0,
            "time_in_market": 0.4,
            "n_entries": 3,
            "open_position_at_end": False,
            "forced_window_close": False,
        },
    ]
    s = completed_panel_summary(rows)
    assert s["median_completed_round_trips"] == 1.0
    assert s["n_expectancy_completed_gt_0"] == 0
    assert s["median_expectancy_completed_eur"] == -3.0
    assert s["panel_realized_net_eur"] == -6.0
    assert s["worst_dd_eur"] == 20.0
    assert s["sum_n_entries"] == 4
    assert s["n_forced_window_close"] == 1
    assert s["not_a_new_gate"] is True


def _bundle(*, v2_verdict: str, completed_exp: float | None, term_net: float, dd: float, entries: int):
    rows = [
        {
            "window_id": f"R{i}",
            "n_trades": 1 if completed_exp is not None else 0,
            "completed_round_trips": 1 if completed_exp is not None else 0,
            "n_terminal_trips": 2,
            "open_position_at_end": True,
            "forced_window_close": True,
            "net_return_eur": term_net / 7,
            "terminal_liquidation_net_eur": term_net / 7,
            "expectancy_after_costs_eur": completed_exp,
            "expectancy_completed_eur": completed_exp,
            "expectancy_terminal_adjusted_eur": 1.0 if v2_verdict == "PASS" else -1.0,
            "realized_net_eur": completed_exp or 0.0,
            "max_dd_eur": dd,
            "time_in_market": 0.4,
            "n_entries": entries,
        }
        for i in range(1, 8)
    ]
    return {
        "old_summary": {
            "panel_net_eur": term_net,
            "median_expectancy_eur": completed_exp,
            "median_trades": 1.0 if completed_exp is not None else 0.0,
            "n_exp_gt_0": 2 if v2_verdict == "FAIL" else 5,
        },
        "v2_summary": {
            "panel_terminal_liquidation_net_eur": term_net,
            "n_exp_terminal_adj_gt_0": 6 if v2_verdict == "PASS" else 3,
            "median_terminal_trips": 2.0,
            "n_forced_window_close": 7,
        },
        "accounting_v2": {"verdict": v2_verdict, "pass": v2_verdict == "PASS"},
        "soft_promote_v1_unchanged": {"verdict": "FAIL" if v2_verdict == "FAIL" else "PASS"},
        "completed_summary": completed_panel_summary(rows),
        "rows": rows,
        "deltas": [],
    }


def test_deltas_v2_fail_eliminates_and_never_promotes():
    c0 = _bundle(v2_verdict="PASS", completed_exp=-2.95, term_net=362.0, dd=88.0, entries=1)
    r1 = _bundle(v2_verdict="FAIL", completed_exp=-5.0, term_net=50.0, dd=90.0, entries=1)
    d = deltas_vs_core_c0(c0, r1)
    assert d["honesty_label"] == "FAIL"
    assert d["eliminate"] is True
    assert d["promote"] is False
    assert d["promote_as_better"] is False
    assert d["dev_eliminate_only"] is True
    assert d["soft_pass_ne_arm"] is True
    assert d["do_not_start_scalp_r2"] is True
    assert d["no_donchian"] is True
    assert d["honesty_is_not_a_gate"] is True
    assert d["gate"] == ACCOUNTING_V2_GATE


def test_deltas_v2_pass_better_completed_exp_still_no_promote():
    c0 = _bundle(v2_verdict="PASS", completed_exp=-2.95, term_net=362.0, dd=88.0, entries=1)
    r1 = _bundle(v2_verdict="PASS", completed_exp=1.5, term_net=200.0, dd=40.0, entries=2)
    d = deltas_vs_core_c0(c0, r1)
    assert d["honesty_label"] == "PASS-and-better-completed-exp"
    assert d["complete_exp_improved"] is True
    assert d["complete_exp_still_negative"] is False
    assert d["dd_improved"] is True
    assert d["participation_eliminated"] is False
    assert d["eliminate"] is False
    assert d["promote"] is False
    assert d["promote_as_better"] is False
    assert d["soft_pass_ne_core_arm"] is True


def test_deltas_v2_pass_but_worse_still_dev_only():
    c0 = _bundle(v2_verdict="PASS", completed_exp=2.0, term_net=362.0, dd=50.0, entries=1)
    r1 = _bundle(v2_verdict="PASS", completed_exp=-1.0, term_net=100.0, dd=80.0, entries=1)
    d = deltas_vs_core_c0(c0, r1)
    assert d["honesty_label"] == "PASS-but-worse"
    assert d["complete_exp_improved"] is False
    assert d["promote"] is False
    assert d["dev_eliminate_only"] is True


def test_participation_eliminated_when_no_entries():
    c0 = _bundle(v2_verdict="PASS", completed_exp=-2.0, term_net=362.0, dd=88.0, entries=1)
    r1 = _bundle(v2_verdict="FAIL", completed_exp=None, term_net=0.0, dd=0.0, entries=0)
    d = deltas_vs_core_c0(c0, r1)
    assert d["participation_eliminated"] is True
    assert d["eliminate"] is True
    assert d["promote"] is False


def test_tiny_negative_completed_exp_delta_is_flagged_not_edge():
    c0 = _bundle(v2_verdict="PASS", completed_exp=-2.95, term_net=362.0, dd=88.0, entries=1)
    r1 = _bundle(v2_verdict="PASS", completed_exp=-2.64, term_net=222.0, dd=84.0, entries=1)
    d = deltas_vs_core_c0(c0, r1)
    assert d["complete_exp_improved"] is True
    assert d["complete_exp_still_negative"] is True
    assert d["completed_exp_gt0_thin"] is True
    assert d["panel_net_worse"] is True
    assert d["promote"] is False
    md = render_results_markdown(c0, r1, deltas=d)
    assert "Do not read V2 PASS / tiny completed-exp Δ as complete-trade edge" in md
    assert "Soft PASS ≠ Core-arm" in md


def test_markdown_carries_hard_rules():
    c0 = _bundle(v2_verdict="PASS", completed_exp=-2.95, term_net=362.65, dd=88.0, entries=1)
    r1 = _bundle(v2_verdict="FAIL", completed_exp=-4.0, term_net=40.0, dd=70.0, entries=1)
    md = render_results_markdown(c0, r1)
    assert "DEV/eliminate-only" in md
    assert "Soft PASS ≠ Core-arm" in md
    assert "does not promote" in md
    assert "Do **not** start SCALP-R2" in md
    assert "94-core-r1-lock.md" in md
    assert CORE_R1_ID in md
    assert "No** ATR multiplier" in md or "No** ATR" in md or "No ATR" in md or "no ATR" in md.lower() or "**No** ATR" in md
    assert "do not rewrite it after seeing results" in md
    assert "config/default.yaml` **untouched**" in md
    assert "HALTED" in md
    assert "not_a_forecast" in md
