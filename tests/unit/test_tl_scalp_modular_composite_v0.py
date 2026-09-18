"""Unit tests: TL-SCALP-MODULAR-COMPOSITE-v0 lock + arms + M5 fail-closed."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.replay import ReplayError
from atlas.paper.tl_scalp_modular_composite_v0 import (
    ARMS,
    ARM_M1,
    ARM_M2,
    ARM_M3,
    ARM_M4,
    ARM_M5,
    CANDIDATE_ID,
    PAIRS,
    SCORED_END_EXCLUSIVE_ISO,
    SCORED_START_ISO,
    SHADOW_WINDOW,
    TRIAL_ID,
    WARMUP_START_ISO,
    WINDOW_ID,
    blocked_m5_row,
    m1_desired_state_series,
    m2_desired_state_series,
    m3_desired_state_series,
    m5_verdict_blocked,
    post_r7_15m_md_status,
    score_pair_arm,
    window_lock_card,
)
from atlas.paper.tl_scalp_3m_sah_v0_shadow import window_verdict
from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG

BAR_MS = 60 * 60 * 1000
START = 1_730_764_800_000  # 2024-11-05
SYM = "BTC-USDT"


def _bar(i: int, o: float, h: float, l: float, c: float, vol: float = 10.0) -> Bar:
    ts = START + i * BAR_MS
    return Bar(SYM, ts, ts + BAR_MS, o, h, l, c, vol, True, "test")


def test_window_and_arms_locked():
    assert TRIAL_ID == "TL-SCALP-MODULAR-COMPOSITE-v0"
    assert WINDOW_ID == "SHADOW_POST_R7_MAJORS_v0"
    assert WARMUP_START_ISO == "2024-11-05T00:00:00Z"
    assert SCORED_START_ISO == "2024-11-06T00:00:00Z"
    assert SCORED_END_EXCLUSIVE_ISO == "2026-09-18T00:00:00Z"
    assert SHADOW_WINDOW.length_days() >= 90.0
    assert PAIRS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert ARMS == (ARM_M1, ARM_M2, ARM_M3, ARM_M4, ARM_M5)
    assert "SAH-A" not in ARMS
    assert SCALP_START_EUR == 20.0
    assert CANDIDATE_ID.startswith("rise_panel_v1_scalp_doge_dual_thrust")


def test_window_lock_card_fields():
    card = window_lock_card()
    assert card["window_id"] == WINDOW_ID
    assert card["arms"] == list(ARMS)
    assert card["sah_a"] == "REJECT_forever"
    assert card["place_orders"] is False
    assert card["soft_ne_arm"] is True
    assert card["dual_hard_pass"] == "N/A_until_second_OOS_Coord_locked"
    assert "2/3" in card["pair_pass_rule"]


def test_m1_m2_m3_series_length():
    bars = [
        _bar(i, 1.0 + i * 0.01, 1.05 + i * 0.01, 0.95, 1.0 + i * 0.01, vol=50.0)
        for i in range(60)
    ]
    for fn in (m1_desired_state_series, m2_desired_state_series, m3_desired_state_series):
        wants = fn(bars)
        assert len(wants) == len(bars)
        assert all(w in (LONG, FLAT) for w in wants)


def test_unknown_arm_fail_closed():
    bars = [_bar(i, 100, 101, 99, 100) for i in range(30)]
    with pytest.raises(ReplayError, match="unknown arm"):
        score_pair_arm(
            bars,
            inst_id=SYM,
            arm="SAH-A",
            fee_rate=0.0005,
            slippage_bps=5.0,
        )


def test_m5_blocked_row_and_verdict():
    row = blocked_m5_row("BTC-USDT", "no 15m MD")
    assert row["blocked"] is True
    assert row["status"] == "BLOCKED"
    assert row["ok"] is False
    v = m5_verdict_blocked("no 15m MD")
    assert v["verdict"] == "BLOCKED"
    assert v["soft_ne_arm"] is True
    assert v["fail_closed"] is True


def test_post_r7_15m_probe_fail_closed():
    st = post_r7_15m_md_status()
    assert st["available"] is False
    assert set(st["missing_pairs"]) == set(PAIRS)
    assert st["reason"]


def test_window_verdict_2_of_3_rule():
    def row(exp_gt, term_ge):
        return {
            "ok": True,
            "exp_gt_0": exp_gt,
            "term_ge_bh": term_ge,
            "expectancy_completed_eur": 1.0 if exp_gt else -1.0,
        }

    v_pass = window_verdict([row(True, True), row(True, True), row(False, False)])
    assert v_pass["verdict"] == "Window_PASS"
    v_fail = window_verdict([row(False, False), row(False, False), row(False, False)])
    assert v_fail["verdict"] == "FAIL"
