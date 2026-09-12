"""phase1/113 Kaje architecture lock — policy card only. No orders. No invented PnL."""

from __future__ import annotations

from pathlib import Path

from atlas.research.kaje_arch import (
    CASCADE_DIRECTION,
    CORE_ASSET,
    CORE_LEVERAGE,
    DEFAULT_YAML_UNTOUCHED,
    LIVE_ARM,
    LOCK_DATE,
    MID_ASSET,
    MID_LEVERAGE_CEILING_ISOLATED,
    PLACE_ORDERS,
    RATIO_CORE_MID_SCALP,
    SCALP_ASSET,
    SCALP_INST_ID,
    SCALP_LEVERAGE_CEILING_ISOLATED,
    SCALP_LISTING_VERIFIED,
    SCALP_PREVIOUSLY_DEFERRED,
    SCALP_SYSTEM_EXISTS,
    SOFT_PASS_NEQ_ARM,
    WEEKLY_REVIEW_AUTO_SWEEP,
    WEEKLY_REVIEW_LOCAL_TIME,
    WEEKLY_REVIEW_WEEKDAY,
    kaje_arch_card,
    refuse_invented_pepe_inst_id,
)


REPO = Path(__file__).resolve().parents[2]


def test_kaje_arch_lock_invariants():
    assert LOCK_DATE == "2026-09-12"
    assert RATIO_CORE_MID_SCALP == (6, 3, 1)
    assert CASCADE_DIRECTION == ("scalp", "mid", "btc")
    assert CORE_ASSET == "BTC"
    assert CORE_LEVERAGE == 1.0
    assert MID_ASSET == "DOGE"
    assert MID_LEVERAGE_CEILING_ISOLATED == 5.0
    assert SCALP_ASSET == "PEPE"
    assert SCALP_PREVIOUSLY_DEFERRED is True
    assert SCALP_INST_ID is None
    assert SCALP_LISTING_VERIFIED is False
    assert SCALP_SYSTEM_EXISTS is False
    assert SCALP_LEVERAGE_CEILING_ISOLATED == 10.0
    assert WEEKLY_REVIEW_WEEKDAY == "Monday"
    assert WEEKLY_REVIEW_LOCAL_TIME == "09:00"
    assert WEEKLY_REVIEW_AUTO_SWEEP is False
    assert SOFT_PASS_NEQ_ARM is True
    assert PLACE_ORDERS is False
    assert DEFAULT_YAML_UNTOUCHED is True
    assert LIVE_ARM is False

    card = kaje_arch_card()
    assert card["live_arm"] is False
    assert card["place_orders"] is False
    assert card["not_a_forecast"] is True
    assert card["default_yaml_untouched"] is True
    assert card["invented_pnl"] is False
    assert card["invented_inst_id"] is False
    assert card["scalp"]["fail_closed_until_listing"] is True
    assert card["scalp"]["inst_id"] is None
    assert card["core"]["research_promote"] is False
    assert card["weekly_review"]["needs_kaje_yes_for_sweeps"] is True
    assert card["arm_requires"] == ("ga live", "session-ja", "sleeve list")
    assert "phase1/113" in card["citation"]
    assert "phase1/112" in card["citation"]


def test_pepe_inst_id_fail_closed():
    refused = refuse_invented_pepe_inst_id("PEPE-USDT-I-MADE-THIS-UP")
    assert refused["accepted"] is False
    assert refused["fail_closed"] is True
    assert refused["inst_id"] is None
    assert refused["score_allowed"] is False
    assert refused["arm_allowed"] is False
    assert refused["place_orders"] is False

    also = refuse_invented_pepe_inst_id(None)
    assert also["fail_closed"] is True
    assert also["score_allowed"] is False


def test_default_yaml_untouched_on_disk():
    text = (REPO / "config" / "default.yaml").read_text(encoding="utf-8")
    assert "leverage_default: 2.0" in text
    assert "leverage_hard_cap: 5.0" in text
    assert "pepe_enabled: false" in text
