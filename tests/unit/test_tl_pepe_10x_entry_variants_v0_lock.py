"""TL-PEPE-10X-ENTRY-VARIANTS-v0 lock + window + signal stubs.

No invented expectancy metrics. Soft ≠ arm.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.paper.replay import ReplayError
from atlas.paper.tl_pepe_10x_entry_variants_v0 import (
    ARMS,
    INST_ID,
    R_PRICE_PCT,
    SCORED_END_EXCLUSIVE_ISO,
    SCORED_START_ISO,
    SHADOW_WINDOW,
    SIZE_CT,
    SL_MULT,
    TP_3R_MULT,
    TP_5R_MULT,
    TP_LABEL_BY_ARM,
    TRIAL_ID,
    WARMUP_START_ISO,
    WINDOW_ID,
    entry_signal,
    indicator_bundle,
    walk_variant,
    window_lock_card,
)
from atlas.paper.types import Bar

BAR_MS = 60 * 60 * 1000
START = 1_775_016_000_000  # synthetic anchor near listing
SYM = INST_ID


def _bar(i: int, o: float, h: float, l: float, c: float, vol: float = 10.0) -> Bar:
    ts = START + i * BAR_MS
    return Bar(SYM, ts, ts + BAR_MS, o, h, l, c, vol, True, "test")


def test_trial_and_variant_ids_locked():
    assert TRIAL_ID == "TL-PEPE-10X-ENTRY-VARIANTS-v0"
    assert ARMS == ("E1", "E2", "E3", "E4")
    assert INST_ID == "PEPE-USD_UM_XPERP-310404"
    assert WINDOW_ID == "SHADOW_PEPE_XPERP_155_v0"


def test_window_lock_constants():
    assert WARMUP_START_ISO == "2026-04-01T04:00:00Z"
    assert SCORED_START_ISO == "2026-04-02T01:00:00Z"
    assert SCORED_END_EXCLUSIVE_ISO == "2026-09-18T00:00:00Z"
    assert SHADOW_WINDOW.length_days() >= 90.0
    card = window_lock_card()
    assert card["window_id"] == WINDOW_ID
    assert card["usdt_proxy"] is False
    assert card["listing_limited"] is True
    assert card["place_orders"] is False
    assert card["soft_ne_arm"] is True
    assert card["dual_hard_pass"] == "N/A_single_predeclared_window"
    assert card["size_ct"] == SIZE_CT == 225


def test_frozen_stop_tp_math_from_minus_2pct_r():
    entry = 1.0e-6
    sl = entry * SL_MULT
    tp3 = entry * TP_3R_MULT
    tp5 = entry * TP_5R_MULT
    assert abs((sl / entry - 1.0) * 100.0 - (-R_PRICE_PCT)) < 1e-9
    assert abs((tp3 / entry - 1.0) * 100.0 - 6.0) < 1e-9
    assert abs((tp5 / entry - 1.0) * 100.0 - 10.0) < 1e-9
    assert abs(6.0 / R_PRICE_PCT - 3.0) < 1e-12
    assert abs(10.0 / R_PRICE_PCT - 5.0) < 1e-12


def test_tp_assignment_per_variant():
    assert TP_LABEL_BY_ARM["E1"] == "TP_3R"
    assert TP_LABEL_BY_ARM["E2"] == "TP_5R"
    assert TP_LABEL_BY_ARM["E3"] == "TP_3R"
    assert TP_LABEL_BY_ARM["E4"] == "TP_5R"


def test_book_constraints():
    assert SIZE_CT == 225
    assert 179 <= SIZE_CT <= 300


def test_registry_json_scored_status():
    path = (
        Path(__file__).resolve().parents[2]
        / "phase1"
        / "registry"
        / "155-tl-pepe-10x-entry-variants-v0-preregister.json"
    )
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["id"] == TRIAL_ID
    assert data["status"] == "scored"
    assert data["expectancy_board_run"] is True
    assert data["risk_ack"] is True
    assert data["place_orders"] is False
    assert data["soft_ne_arm"] is True
    assert data["not_a_forecast"] is True
    assert data["no_edit_default_yaml"] is True
    assert data["no_s1_doge_transplant"] is True
    assert data["usdt_proxy"] is False
    assert data["sample_window"]["status"] == "LOCKED"
    assert data["sample_window"]["window_id"] == WINDOW_ID
    assert data["HARD_PASS"] == []
    assert "E4" in data["FAIL"]
    ids = [v["id"] for v in data["variants"]]
    assert ids == list(ARMS)


def test_unknown_arm_fail_closed():
    bars = [_bar(i, 1e-6, 1.1e-6, 0.9e-6, 1e-6) for i in range(40)]
    with pytest.raises(ReplayError, match="unknown arm"):
        walk_variant(
            bars,
            arm="E9",
            trade_start_ms=START + 25 * BAR_MS,
            trade_end_ms=START + 40 * BAR_MS,
            fee_rate=0.0005,
            slippage_bps=5.0,
        )


def test_e3_cross_definition_when_fires():
    bars = []
    px = 1.0e-6
    for i in range(50):
        if i < 30:
            c = px
        else:
            c = px * (1.0 + 0.01 * (i - 29))
        bars.append(_bar(i, c, c * 1.001, c * 0.999, c, vol=100.0 + i))
    ind = indicator_bundle(bars)
    fired = [i for i in range(len(bars)) if entry_signal("E3", i, bars, ind)]
    for i in fired:
        e12, e21 = ind["ema12"][i], ind["ema21"][i]
        p12, p21 = ind["ema12"][i - 1], ind["ema21"][i - 1]
        assert p12 is not None and p21 is not None
        assert float(p12) <= float(p21)
        assert float(e12) > float(e21)


def test_e1_gates_honest_when_true():
    bars = [_bar(i, 1e-6, 1.01e-6, 0.99e-6, 1e-6, vol=1.0) for i in range(40)]
    ind = indicator_bundle(bars)
    for i in range(len(bars)):
        if entry_signal("E1", i, bars, ind):
            e12, e21 = ind["ema12"][i], ind["ema21"][i]
            rsi, rvol = ind["rsi"][i], ind["rvol"][i]
            assert e12 is not None and e21 is not None
            assert float(e12) > float(e21)
            assert 45.0 <= float(rsi) <= 70.0
            assert float(rvol) >= 1.0
