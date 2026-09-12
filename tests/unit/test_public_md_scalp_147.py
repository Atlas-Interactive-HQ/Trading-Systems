"""Unit tests for #147 dual-gate TP R ladder (no network, no invented trades)."""

from __future__ import annotations

from atlas.paper.public_md_scalp_147 import (
    CELL_R_MULTIPLE,
    CELL_RVOL_GATE,
    CELL_USE_TP,
    OFFICIAL_CELLS,
    R4_OOS_EXPECT,
    R4_TRAIN_EXPECT,
    WINDOWS,
    dual_gate_verdict,
    window_gate_counts,
)
from atlas.strategy.scalp_142_notebook import RISK_M2, RVOL_GATE


def test_official_cells_r_ladder_params() -> None:
    assert OFFICIAL_CELLS == ("R2", "R3", "R4", "R5")
    assert CELL_R_MULTIPLE == {"R2": 2.0, "R3": 3.0, "R4": 4.0, "R5": 5.0}
    for sid in OFFICIAL_CELLS:
        assert CELL_USE_TP[sid] is True
        assert CELL_RVOL_GATE[sid] == float(RVOL_GATE) == 1.0
    assert RISK_M2 == 0.25
    assert WINDOWS["TRAIN"] == ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z")
    assert WINDOWS["OOS"] == ("2021-01-01T00:00:00Z", "2021-07-01T00:00:00Z")
    assert "n" in R4_TRAIN_EXPECT["BTC-USDT"]
    assert "n" in R4_OOS_EXPECT["BTC-USDT"]


def test_one_window_pass_cannot_be_hard_pass() -> None:
    """Dual HARD_PASS requires BOTH windows; one-window → SOFT_NOTE max."""
    train_pass = {
        "full_pass": True,
        "exp_pass": True,
        "n_pairs_exp_pos": 2,
        "n_pairs_term_ge_bh": 2,
        "verdict": "PASS",
    }
    oos_fail = {
        "full_pass": False,
        "exp_pass": False,
        "n_pairs_exp_pos": 1,
        "n_pairs_term_ge_bh": 0,
        "verdict": "FAIL",
    }
    assert dual_gate_verdict(train_pass, oos_fail) == "SOFT_NOTE"
    assert dual_gate_verdict(oos_fail, train_pass) == "SOFT_NOTE"
    # both full → HARD_PASS
    assert dual_gate_verdict(train_pass, train_pass) == "HARD_PASS"
    # neither exp → FAIL
    assert dual_gate_verdict(oos_fail, oos_fail) == "FAIL"


def test_window_gate_counts_soft_vs_pass() -> None:
    cells_soft = [
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": False,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": False,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": False,
            "term_ge_bh": False,
        },
    ]
    g = window_gate_counts(cells_soft)
    assert g["exp_pass"] is True
    assert g["full_pass"] is False
    assert g["verdict"] == "SOFT"

    cells_pass = [
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": True,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": True,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": False,
            "term_ge_bh": False,
        },
    ]
    g2 = window_gate_counts(cells_pass)
    assert g2["full_pass"] is True
    assert g2["verdict"] == "PASS"


def test_dual_soft_when_exp_both_but_not_full() -> None:
    train = {
        "full_pass": False,
        "exp_pass": True,
        "verdict": "SOFT",
    }
    oos = {
        "full_pass": False,
        "exp_pass": True,
        "verdict": "SOFT",
    }
    assert dual_gate_verdict(train, oos) == "SOFT_NOTE"


def test_no_t2_occupancy_in_official_cells() -> None:
    assert "T2" not in OFFICIAL_CELLS
    assert all(CELL_USE_TP[s] for s in OFFICIAL_CELLS)
