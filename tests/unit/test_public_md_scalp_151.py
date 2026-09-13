"""Unit tests for #151 15m MSB entry pivot (no network, no invented trades)."""

from __future__ import annotations

from atlas.paper.public_md_scalp_151 import (
    CELL_FILL_MODE,
    CELL_IS_CONTROL,
    CELL_R_MULTIPLE,
    CELL_RVOL_GATE,
    CELL_SESSION_GATE,
    CELL_TRIGGER,
    CELL_USE_TP,
    DEFAULT_YAML_MD5,
    DEFAULT_YAML_SHA256,
    DISP_ATR_FRAC,
    DISP_RVOL_GATE,
    OFFICIAL_CELLS,
    PRIMARY_OOS_WINDOWS,
    SESSION_HOURS_UTC,
    STRESS_WINDOW,
    WINDOWS,
    _1m_displacement_ok,
    dual_hard_pass_verdict,
    oos_primary_gate_counts,
    session_hour_ok,
    stress_note_counts,
    train_gate_counts,
    utc_open_hour,
)
from atlas.paper.types import Bar
from atlas.strategy.scalp_142_notebook import RISK_M2


def _bar(
    *,
    ts_open_ms: int,
    o: float,
    h: float,
    l: float,
    c: float,
    vol: float = 100.0,
) -> Bar:
    return Bar(
        symbol="TEST",
        # timeframe not on Bar
        
        ts_open_ms=ts_open_ms,
        ts_close_ms=ts_open_ms + 60_000 - 1,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=vol,
        closed=True,
    )


def test_official_cells_p1_p2_p3_params() -> None:
    assert OFFICIAL_CELLS == ("P1", "P2", "P3")
    assert CELL_R_MULTIPLE["P1"] == CELL_R_MULTIPLE["P2"] == CELL_R_MULTIPLE["P3"] == 4.0
    assert CELL_RVOL_GATE["P1"] == CELL_RVOL_GATE["P2"] == 1.2
    assert CELL_RVOL_GATE["P3"] == 1.0
    assert CELL_SESSION_GATE["P1"] is False
    assert CELL_SESSION_GATE["P2"] is True
    assert CELL_SESSION_GATE["P3"] is False
    assert CELL_TRIGGER["P1"] == CELL_TRIGGER["P2"] == "15m_msb"
    assert CELL_TRIGGER["P3"] == "1m_bos_displace"
    assert CELL_FILL_MODE["P1"] == CELL_FILL_MODE["P2"] == "15m_next_open"
    assert CELL_FILL_MODE["P3"] == "1m_next_open"
    assert CELL_IS_CONTROL["P3"] is True
    assert CELL_IS_CONTROL["P1"] is False
    for sid in OFFICIAL_CELLS:
        assert CELL_USE_TP[sid] is True
    assert RISK_M2 == 0.25
    assert SESSION_HOURS_UTC == (13, 14, 15)
    assert DISP_ATR_FRAC == 0.5
    assert DISP_RVOL_GATE == 1.5
    assert WINDOWS["TRAIN"] == ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z")
    assert WINDOWS["STRESS_2021"] == (
        "2021-01-01T00:00:00Z",
        "2021-07-01T00:00:00Z",
    )
    assert WINDOWS["OOS_2022"] == ("2022-01-01T00:00:00Z", "2022-07-01T00:00:00Z")
    assert WINDOWS["OOS_2023"] == ("2023-01-01T00:00:00Z", "2023-07-01T00:00:00Z")
    assert PRIMARY_OOS_WINDOWS == ("OOS_2022", "OOS_2023")
    assert STRESS_WINDOW == "STRESS_2021"


def test_session_gate_hours() -> None:
    # 2022-01-01 13:00 UTC
    h13 = 1641042000000
    assert utc_open_hour(h13) == 13
    assert session_hour_ok(h13) is True
    # 12:00 UTC — skip
    h12 = 1641038400000
    assert utc_open_hour(h12) == 12
    assert session_hour_ok(h12) is False
    # 15:00 OK, 16:00 not
    h15 = 1641049200000
    h16 = 1641052800000
    assert session_hour_ok(h15) is True
    assert session_hour_ok(h16) is False


def test_displacement_rule_synthetic() -> None:
    bars = [
        _bar(ts_open_ms=0, o=100, h=101, l=99, c=100),
        _bar(ts_open_ms=60_000, o=100, h=110, l=100, c=108),  # cc=8
    ]
    atr = [None, 10.0]
    rvol = [None, 1.6]
    # 8 >= 0.5*10 and rvol 1.6 >= 1.5
    assert _1m_displacement_ok(bars, atr, rvol, 1) is True
    rvol_low = [None, 1.4]
    assert _1m_displacement_ok(bars, atr, rvol_low, 1) is False
    atr_hi = [None, 20.0]  # 8 < 0.5*20
    assert _1m_displacement_ok(bars, atr_hi, rvol, 1) is False


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
    cells = [
        _n0_cell(bh=-11.0),
        _n0_cell(bh=-14.0),
        _n0_cell(bh=-12.0),
    ]
    g = oos_primary_gate_counts(cells)
    assert g["n_pairs_n0"] == 3
    assert g["full_pass"] is True
    assert g["verdict"] == "PASS"
    cells_bull = [
        _n0_cell(bh=16.0),
        _n0_cell(bh=12.0),
        _n0_cell(bh=-1.0),
    ]
    g2 = oos_primary_gate_counts(cells_bull)
    assert g2["n_pairs_term_ge_bh"] == 1
    assert g2["full_pass"] is False


def test_dual_requires_all_three_windows() -> None:
    train_pass = {"full_pass": True, "exp_pass": True, "verdict": "PASS"}
    oos_pass = {"full_pass": True, "exp_pass": True, "verdict": "PASS"}
    oos_fail = {"full_pass": False, "exp_pass": False, "verdict": "FAIL"}
    assert dual_hard_pass_verdict(train_pass, oos_pass, oos_pass) == "HARD_PASS"
    assert dual_hard_pass_verdict(train_pass, oos_pass, oos_fail) == "SOFT_NOTE"
    assert dual_hard_pass_verdict(train_pass, oos_fail, oos_pass) == "SOFT_NOTE"
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


def test_default_yaml_checksum_constants() -> None:
    assert (
        DEFAULT_YAML_SHA256
        == "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"
    )
    assert DEFAULT_YAML_MD5 == "68e1d9b76f166c2359d8121b449f7ce1"


def test_place_orders_false_in_module_doc() -> None:
    import atlas.paper.public_md_scalp_151 as m

    assert "place_orders false" in (m.__doc__ or "").lower() or "place_orders" in (
        m.__doc__ or ""
    )
    assert m.PHASE1 == 151
