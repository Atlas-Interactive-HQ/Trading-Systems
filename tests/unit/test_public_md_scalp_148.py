"""Unit tests for #148 dual-gate Q4/Q5 (no network, no invented trades)."""

from __future__ import annotations

from atlas.paper.public_md_scalp_148 import (
    CELL_R_MULTIPLE,
    CELL_RVOL_GATE,
    CELL_USE_TP,
    OFFICIAL_CELLS,
    PRIMARY_OOS_WINDOWS,
    Q4_STRESS_2021_EXPECT,
    Q4_TRAIN_EXPECT,
    Q5_STRESS_2021_EXPECT,
    Q5_TRAIN_EXPECT,
    STRESS_WINDOW,
    WINDOWS,
    dual_hard_pass_verdict,
    oos_primary_gate_counts,
    stress_note_counts,
    train_gate_counts,
)
from atlas.strategy.scalp_142_notebook import RISK_M2, RVOL_GATE


def test_official_cells_q4_q5_params() -> None:
    assert OFFICIAL_CELLS == ("Q4", "Q5")
    assert CELL_R_MULTIPLE == {"Q4": 4.0, "Q5": 5.0}
    for sid in OFFICIAL_CELLS:
        assert CELL_USE_TP[sid] is True
        assert CELL_RVOL_GATE[sid] == float(RVOL_GATE) == 1.0
    assert RISK_M2 == 0.25
    assert WINDOWS["TRAIN"] == ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z")
    assert WINDOWS["STRESS_2021"] == (
        "2021-01-01T00:00:00Z",
        "2021-07-01T00:00:00Z",
    )
    assert WINDOWS["OOS_2022"] == ("2022-01-01T00:00:00Z", "2022-07-01T00:00:00Z")
    assert WINDOWS["OOS_2023"] == ("2023-01-01T00:00:00Z", "2023-07-01T00:00:00Z")
    assert PRIMARY_OOS_WINDOWS == ("OOS_2022", "OOS_2023")
    assert STRESS_WINDOW == "STRESS_2021"
    assert "n" in Q4_TRAIN_EXPECT["BTC-USDT"]
    assert "n" in Q5_STRESS_2021_EXPECT["DOGE-USDT"]
    assert Q4_TRAIN_EXPECT["BTC-USDT"]["n"] == 15
    assert Q4_STRESS_2021_EXPECT["BTC-USDT"]["n"] == 31


def test_dual_requires_both_2022_and_2023() -> None:
    """DUAL HARD_PASS requires TRAIN + BOTH primary OOS; one OOS alone insufficient."""
    train_pass = {
        "full_pass": True,
        "exp_pass": True,
        "verdict": "PASS",
    }
    oos_pass = {
        "full_pass": True,
        "exp_pass": True,
        "verdict": "PASS",
    }
    oos_fail = {
        "full_pass": False,
        "exp_pass": False,
        "verdict": "FAIL",
    }
    # both OOS + train → HARD_PASS
    assert (
        dual_hard_pass_verdict(train_pass, oos_pass, oos_pass) == "HARD_PASS"
    )
    # only 2022 → not HARD_PASS
    assert (
        dual_hard_pass_verdict(train_pass, oos_pass, oos_fail) == "SOFT_NOTE"
    )
    # only 2023 → not HARD_PASS
    assert (
        dual_hard_pass_verdict(train_pass, oos_fail, oos_pass) == "SOFT_NOTE"
    )
    # neither OOS → SOFT_NOTE if train exp-pass, else FAIL
    assert (
        dual_hard_pass_verdict(train_pass, oos_fail, oos_fail) == "SOFT_NOTE"
    )
    both_fail = {"full_pass": False, "exp_pass": False, "verdict": "FAIL"}
    assert dual_hard_pass_verdict(both_fail, both_fail, both_fail) == "FAIL"


def test_2021_stress_cannot_make_hard_pass() -> None:
    """STRESS_2021 is excluded from dual HARD_PASS even if it would 'pass'."""
    train_pass = {"full_pass": True, "exp_pass": True, "verdict": "PASS"}
    oos_fail = {"full_pass": False, "exp_pass": False, "verdict": "FAIL"}
    stress_looks_good = {
        "full_pass": False,  # stress_note_counts always sets False
        "exp_pass": True,
        "verdict": "STRESS_NOTE_ONLY",
        "cannot_make_hard_pass": True,
    }
    # Stress "pass" + train but missing both OOS → still not HARD_PASS
    assert (
        dual_hard_pass_verdict(
            train_pass, oos_fail, oos_fail, stress_gate=stress_looks_good
        )
        == "SOFT_NOTE"
    )
    # stress_note_counts never reports full_pass
    cells_pass_looking = [
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": True,
            "terminal_liquidation_net_eur": 10.0,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": True,
            "terminal_liquidation_net_eur": 20.0,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": True,
            "terminal_liquidation_net_eur": 30.0,
        },
    ]
    g = stress_note_counts(cells_pass_looking)
    assert g["full_pass"] is False
    assert g["cannot_make_hard_pass"] is True
    assert g["verdict"] == "STRESS_NOTE_ONLY"
    assert g["not_a_kill_gate"] is True


def test_oos_primary_requires_term_pos_and_bh() -> None:
    cells = [
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": True,
            "terminal_liquidation_net_eur": 5.0,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": True,
            "terminal_liquidation_net_eur": 3.0,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": False,
            "term_ge_bh": False,
            "terminal_liquidation_net_eur": -1.0,
        },
    ]
    g = oos_primary_gate_counts(cells)
    assert g["full_pass"] is True
    assert g["requires_term_pos"] is True
    assert g["verdict"] == "PASS"

    # exp ok but terminal not positive on enough pairs
    cells_soft = [
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": False,
            "terminal_liquidation_net_eur": -2.0,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": False,
            "terminal_liquidation_net_eur": -3.0,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": False,
            "term_ge_bh": False,
            "terminal_liquidation_net_eur": -4.0,
        },
    ]
    g2 = oos_primary_gate_counts(cells_soft)
    assert g2["exp_pass"] is True
    assert g2["full_pass"] is False
    assert g2["verdict"] == "SOFT"


def test_train_gate_no_term_pos_requirement() -> None:
    cells = [
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": True,
            "terminal_liquidation_net_eur": 100.0,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": True,
            "term_ge_bh": True,
            "terminal_liquidation_net_eur": 50.0,
        },
        {
            "status": "MEASURED",
            "completed_exp_positive": False,
            "term_ge_bh": False,
            "terminal_liquidation_net_eur": 1.0,
        },
    ]
    g = train_gate_counts(cells)
    assert g["full_pass"] is True
    assert g["gate_kind"] == "train"


def test_no_t2_and_no_r2_r3() -> None:
    assert "T2" not in OFFICIAL_CELLS
    assert "R2" not in OFFICIAL_CELLS
    assert "R3" not in OFFICIAL_CELLS
    assert all(CELL_USE_TP[s] for s in OFFICIAL_CELLS)
