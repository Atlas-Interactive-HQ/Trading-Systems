"""Unit tests for #149 regime-EMA21 dual-gate (no network, no invented trades)."""

from __future__ import annotations

from atlas.paper.public_md_scalp_149 import (
    CELL_R_MULTIPLE,
    CELL_REGIME_TF,
    CELL_RVOL_GATE,
    CELL_USE_TP,
    OFFICIAL_CELLS,
    PRIMARY_OOS_WINDOWS,
    STRESS_WINDOW,
    WINDOWS,
    dual_hard_pass_verdict,
    oos_primary_gate_counts,
    stress_note_counts,
    train_gate_counts,
)
from atlas.strategy.scalp_142_notebook import RISK_M2, RVOL_GATE


def test_official_cells_b4_b5_b4b_params() -> None:
    assert "B4" in OFFICIAL_CELLS and "B5" in OFFICIAL_CELLS
    assert CELL_R_MULTIPLE["B4"] == 4.0
    assert CELL_R_MULTIPLE["B5"] == 5.0
    assert CELL_R_MULTIPLE["B4b"] == 4.0
    assert CELL_REGIME_TF["B4"] == "1D"
    assert CELL_REGIME_TF["B5"] == "1D"
    assert CELL_REGIME_TF["B4b"] == "4H"
    for sid in ("B4", "B5", "B4b"):
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


def _n0_cell(*, bh: float) -> dict:
    return {
        "status": "MEASURED",
        "n_trades": 0,
        "n_zero": True,
        "terminal_liquidation_net_eur": 0.0,
        "bh_net_return_eur": bh,
        "completed_exp_positive": False,
        "term_ge_bh": 0.0 >= bh,
        "term_positive": False,
        "expectancy_after_costs_eur": None,
    }


def _pos_cell(*, exp_pos: bool, term: float, bh: float) -> dict:
    return {
        "status": "MEASURED",
        "n_trades": 3,
        "n_zero": False,
        "terminal_liquidation_net_eur": term,
        "bh_net_return_eur": bh,
        "completed_exp_positive": exp_pos,
        "term_ge_bh": term >= bh,
        "term_positive": term > 0,
        "expectancy_after_costs_eur": 1.0 if exp_pos else -1.0,
    }


def test_n0_term_zero_and_waives_exp() -> None:
    """n=0 → term=0; exp>0 waived; term≥BH if 0≥BH (bear BH)."""
    cells = [
        _n0_cell(bh=-11.0),
        _n0_cell(bh=-14.0),
        _n0_cell(bh=-12.0),
    ]
    g = oos_primary_gate_counts(cells)
    assert g["n_pairs_n0"] == 3
    assert g["full_pass"] is True
    assert g["verdict"] == "PASS"
    # bull BH with n=0 cannot count term≥BH
    cells_bull = [
        _n0_cell(bh=16.0),
        _n0_cell(bh=12.0),
        _n0_cell(bh=-1.0),
    ]
    g2 = oos_primary_gate_counts(cells_bull)
    assert g2["n_pairs_term_ge_bh"] == 1  # only DOGE-like BH<0
    assert g2["full_pass"] is False


def test_dual_requires_all_three_windows() -> None:
    train_pass = {"full_pass": True, "exp_pass": True, "verdict": "PASS"}
    oos_pass = {"full_pass": True, "exp_pass": True, "verdict": "PASS"}
    oos_fail = {"full_pass": False, "exp_pass": False, "verdict": "FAIL"}
    assert dual_hard_pass_verdict(train_pass, oos_pass, oos_pass) == "HARD_PASS"
    assert dual_hard_pass_verdict(train_pass, oos_pass, oos_fail) == "SOFT_NOTE"
    assert dual_hard_pass_verdict(train_pass, oos_fail, oos_pass) == "SOFT_NOTE"
    assert dual_hard_pass_verdict(train_pass, oos_fail, oos_fail) == "SOFT_NOTE"
    both_fail = {"full_pass": False, "exp_pass": False, "verdict": "FAIL"}
    assert dual_hard_pass_verdict(both_fail, both_fail, both_fail) == "FAIL"


def test_2021_stress_cannot_make_hard_pass() -> None:
    train_pass = {"full_pass": True, "exp_pass": True, "verdict": "PASS"}
    oos_fail = {"full_pass": False, "exp_pass": False, "verdict": "FAIL"}
    stress_looks_good = {
        "full_pass": False,
        "exp_pass": True,
        "verdict": "STRESS_NOTE_ONLY",
        "cannot_make_hard_pass": True,
    }
    assert (
        dual_hard_pass_verdict(
            train_pass, oos_fail, oos_fail, stress_gate=stress_looks_good
        )
        == "SOFT_NOTE"
    )
    note = stress_note_counts(
        [_pos_cell(exp_pos=True, term=5.0, bh=4.0)] * 3
    )
    assert note["verdict"] == "STRESS_NOTE_ONLY"
    assert note["full_pass"] is False
    assert note["cannot_make_hard_pass"] is True


def test_train_gate_n0_waive() -> None:
    cells = [
        _n0_cell(bh=-5.0),
        _pos_cell(exp_pos=True, term=10.0, bh=8.0),
        _pos_cell(exp_pos=True, term=12.0, bh=9.0),
    ]
    g = train_gate_counts(cells)
    assert g["full_pass"] is True
    assert g["n_pairs_n0"] == 1
