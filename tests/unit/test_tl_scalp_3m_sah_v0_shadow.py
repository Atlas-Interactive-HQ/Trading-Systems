"""Unit tests: TL-SCALP-3M-SAH-v0 window ids + arm labels + fail-closed."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.replay import ReplayError
from atlas.paper.tl_scalp_3m_sah_v0_shadow import (
    ARMS,
    ARM_CTRL,
    ARM_SAH_A,
    ARM_SAH_B,
    CANDIDATE_ID,
    PAIRS,
    SAH_A_RISK_FRAC,
    SCORED_END_EXCLUSIVE_ISO,
    SCORED_START_ISO,
    SHADOW_WINDOW,
    TRIAL_ID,
    WARMUP_START_ISO,
    WINDOW_ID,
    s1_desired_state_series,
    sah_ranking,
    walk_sah_arm,
    window_lock_card,
    window_verdict,
)
from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG

BAR_MS = 60 * 60 * 1000
START = 1_730_764_800_000  # 2024-11-05
SYM = "BTC-USDT"


def _bar(i: int, o: float, h: float, l: float, c: float, vol: float = 10.0) -> Bar:
    ts = START + i * BAR_MS
    return Bar(SYM, ts, ts + BAR_MS, o, h, l, c, vol, True, "test")


def test_window_ids_locked():
    assert TRIAL_ID == "TL-SCALP-3M-SAH-v0"
    assert WINDOW_ID == "SHADOW_POST_R7_MAJORS_v0"
    assert WARMUP_START_ISO == "2024-11-05T00:00:00Z"
    assert SCORED_START_ISO == "2024-11-06T00:00:00Z"
    assert SCORED_END_EXCLUSIVE_ISO == "2026-09-18T00:00:00Z"
    assert SHADOW_WINDOW.length_days() >= 90.0
    assert PAIRS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert ARMS == (ARM_CTRL, ARM_SAH_A, ARM_SAH_B)
    assert SAH_A_RISK_FRAC == 0.05
    assert SCALP_START_EUR == 20.0
    assert CANDIDATE_ID.startswith("rise_panel_v1_scalp_doge_dual_thrust")


def test_window_lock_card_fields():
    card = window_lock_card()
    assert card["window_id"] == WINDOW_ID
    assert card["scored_start_utc"] == SCORED_START_ISO
    assert card["scored_end_exclusive_utc"] == SCORED_END_EXCLUSIVE_ISO
    assert card["arms"] == list(ARMS)
    assert card["sah_a_risk_frac"] == 0.05
    assert card["place_orders"] is False
    assert card["soft_ne_arm"] is True
    assert card["dual_hard_pass"] == "N/A_single_predeclared_window"


def test_arm_labels_and_unknown_fail_closed():
    bars = [_bar(i, 100, 101, 99, 100) for i in range(30)]
    wants = [FLAT] * 30
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    with pytest.raises(ReplayError, match="unknown arm"):
        walk_sah_arm(
            bars,
            wants=wants,
            settings=settings,
            trade_start_ms=START,
            trade_end_ms=START + 40 * BAR_MS,
            arm="SAH-Z",
        )


def test_s1_series_length_matches():
    bars = [_bar(i, 1.0 + i * 0.01, 1.05 + i * 0.01, 0.95, 1.0 + i * 0.01, vol=50.0) for i in range(40)]
    wants = s1_desired_state_series(bars)
    assert len(wants) == len(bars)
    assert all(w in (LONG, FLAT) for w in wants)


def test_window_verdict_pass_soft_fail():
    def row(exp_gt, term_ge):
        return {
            "ok": True,
            "exp_gt_0": exp_gt,
            "term_ge_bh": term_ge,
            "expectancy_completed_eur": 1.0 if exp_gt else -1.0,
        }

    v_pass = window_verdict([row(True, True), row(True, True), row(False, False)])
    assert v_pass["verdict"] == "Window_PASS"
    v_soft = window_verdict([row(True, False), row(True, False), row(False, False)])
    assert v_soft["verdict"] == "SOFT_NOTE"
    assert v_soft["soft_ne_arm"] is True
    v_fail = window_verdict([row(False, False), row(False, False), row(False, False)])
    assert v_fail["verdict"] == "FAIL"


def test_sah_ranking_orthogonal():
    by = {
        ARM_CTRL: [{"ok": True, "expectancy_completed_eur": 1.0}],
        ARM_SAH_A: [{"ok": True, "expectancy_completed_eur": 2.0}],
        ARM_SAH_B: [{"ok": True, "expectancy_completed_eur": 0.5}],
    }
    rk = sah_ranking(by)
    assert rk["SAH-A_gt_CTRL"] is True
    assert rk["SAH-B_gt_CTRL"] is False
    assert rk["does_not_arm"] is True
