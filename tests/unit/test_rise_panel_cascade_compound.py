"""Unit tests: rise_panel Track B surplus cascade compound helpers."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import (
    CORE_START_EUR,
    MID_START_EUR,
    SCALP_START_EUR,
    SHARE_CORE,
    SHARE_MID,
    SHARE_SCALP,
    TOTAL_START_EUR,
    CascadeLedger,
    apply_walk_ends_then_surplus,
    surplus_target_eur,
)
from atlas.paper.rise_panel import RISE_PANEL_V1, panel_windows
from atlas.paper.rise_panel_cascade_eval import (
    CASCADE_RULE,
    COMPOUND_ID,
    SCALP_CANDIDATE_ID,
    _compound_window_row,
    render_phase55_markdown,
)


def test_rise_windows_unchanged_from_54():
    wins = panel_windows()
    assert len(wins) == 7
    assert [w.id for w in wins] == ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]
    assert RISE_PANEL_V1[0].start == "2020-10-01"
    assert RISE_PANEL_V1[0].end == "2020-12-31"
    assert RISE_PANEL_V1[6].start == "2024-08-07"
    assert RISE_PANEL_V1[6].end == "2024-11-04"


def test_shares_721():
    assert SHARE_CORE == 0.70
    assert SHARE_MID == 0.20
    assert SHARE_SCALP == 0.10
    assert TOTAL_START_EUR == 200.0
    assert CORE_START_EUR + MID_START_EUR + SCALP_START_EUR == TOTAL_START_EUR


def test_surplus_share_rebalance_one_way_to_721():
    led = apply_walk_ends_then_surplus(
        core_end_eur=150.0,
        mid_end_eur=50.0,
        scalp_end_eur=30.0,
        ts_ms=1_696_204_800_000,
    )
    total = led.total_equity_eur()
    assert total == pytest.approx(230.0)
    assert led.scalp.equity_eur == pytest.approx(surplus_target_eur(total, "scalp"))
    assert led.mid.equity_eur == pytest.approx(surplus_target_eur(total, "mid"))
    assert led.core.equity_eur == pytest.approx(surplus_target_eur(total, "core"))
    assert led.transfers
    assert all(t.source in ("scalp", "mid") for t in led.transfers)
    assert not any(t.source == "core" for t in led.transfers)
    assert not any(t.dest == "scalp" for t in led.transfers)
    assert all(t.reason == "window_end_surplus_share_721" for t in led.transfers)


def test_surplus_no_transfer_when_already_at_or_below_target():
    # Exact 7:2:1 on 200
    led = apply_walk_ends_then_surplus(
        core_end_eur=140.0,
        mid_end_eur=40.0,
        scalp_end_eur=20.0,
        ts_ms=1_696_204_800_000,
    )
    assert led.transfers == []
    assert led.total_equity_eur() == pytest.approx(200.0)


def test_surplus_skips_below_min_transfer():
    # Scalp only 0.50 over target on 200.5 total → target scalp ~20.05; surplus < 1
    led = CascadeLedger()
    led.core.equity_eur = 140.0
    led.mid.equity_eur = 40.0
    led.scalp.equity_eur = 20.50
    done = led.surplus_share_rebalance(ts_ms=1_696_204_800_000)
    assert done == []


def test_compound_window_row_reports_transfers():
    w = RISE_PANEL_V1[0]
    core = {
        "ok": True,
        "end_equity_eur": 150.0,
        "net_return_eur": 10.0,
        "max_dd_eur": 5.0,
        "n_trades": 1,
        "expectancy_after_costs_eur": 1.0,
    }
    mid = {
        "ok": True,
        "end_equity_eur": 50.0,
        "net_return_eur": 10.0,
        "max_dd_eur": 4.0,
        "n_trades": 5,
        "expectancy_after_costs_eur": 2.0,
    }
    scalp = {
        "ok": True,
        "end_equity_eur": 30.0,
        "net_return_eur": 10.0,
        "max_dd_eur": 3.0,
        "n_trades": 10,
        "expectancy_after_costs_eur": 1.0,
    }
    row = _compound_window_row(window=w, core=core, mid=mid, scalp=scalp)
    assert row["ok"] is True
    assert row["n_transfers"] >= 1
    assert row["pre_cascade_end_eur"]["total"] == pytest.approx(230.0)
    assert row["post_cascade_end_eur"]["total"] == pytest.approx(230.0)
    assert row["transfer_sum_eur"] > 0


def test_ids_and_cascade_rule_documented():
    assert COMPOUND_ID == "rise_panel_v1_cascade_compound_721"
    assert SCALP_CANDIDATE_ID.startswith("rise_panel_v1_scalp_")
    assert CASCADE_RULE["ratio"] == "7:2:1"
    assert CASCADE_RULE["one_way"] is True
    assert "surplus" in CASCADE_RULE["name"]


def test_render_marks_provisional():
    bundle = {
        "provisional_scalp": True,
        "systems": {"scalp": {"id": SCALP_CANDIDATE_ID}},
        "scalp_soft_promote": {
            "verdict": "FAIL",
            "median_trades": 2,
            "n_expectancy_gt_0": 3,
            "panel_net_eur": -1.0,
        },
        "cascade_rule": CASCADE_RULE,
        "window_rows": [],
        "panel_narrative": {},
        "core_summary": {},
        "mid_summary": {},
        "scalp_summary": {},
    }
    md = render_phase55_markdown(bundle)
    assert "provisional_scalp: true" in md
    assert "PROVISIONAL" in md
    assert "default.yaml" in md
