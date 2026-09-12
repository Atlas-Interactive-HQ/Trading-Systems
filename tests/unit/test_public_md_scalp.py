"""Unit tests for phase1/115 public-MD Scalp paper method lock."""

from __future__ import annotations

from atlas.paper.public_md_scalp import (
    DEMO_BLOCK,
    DEMO_PENDING_OPS,
    EXCLUDE,
    LOCK_ID,
    NOT_ON_EEA_THIS_PROBE,
    PATH_NAME,
    PRIMARY_BAR,
    PRIMARY_DUAL,
    PUBLIC_MD_SCALP_METHOD,
    PUBLIC_ONLY_OK,
    SECONDARY_DUAL,
    SPOT_ONLY_WATCH,
    card,
)


def test_lock_flags_method_only():
    assert LOCK_ID == "public_md_scalp_method"
    assert PATH_NAME == "public_md_scalp_paper_v1"
    assert PUBLIC_MD_SCALP_METHOD["id"] == LOCK_ID
    assert PUBLIC_MD_SCALP_METHOD["path_name"] == PATH_NAME
    assert PUBLIC_MD_SCALP_METHOD["live_arm"] is False
    assert PUBLIC_MD_SCALP_METHOD["soft_pass_neq_arm"] is True
    assert PUBLIC_MD_SCALP_METHOD["halted"] is True
    assert PUBLIC_MD_SCALP_METHOD["place_orders"] is False
    assert PUBLIC_MD_SCALP_METHOD["not_a_forecast"] is True
    assert PUBLIC_MD_SCALP_METHOD["score_forbidden"] is True
    assert PUBLIC_MD_SCALP_METHOD["s1_transplant"] is False
    assert PUBLIC_MD_SCALP_METHOD["demo_oms"] is False
    assert PUBLIC_MD_SCALP_METHOD["default_yaml_untouched"] is True
    assert PUBLIC_MD_SCALP_METHOD["signed_demo_oms"] is False
    assert PUBLIC_MD_SCALP_METHOD["live_post"] is False
    assert PUBLIC_MD_SCALP_METHOD["martingale"] is False
    assert PUBLIC_MD_SCALP_METHOD["size_up_on_loss"] is False
    assert PUBLIC_MD_SCALP_METHOD["mid_71_untouched"] is True
    assert PUBLIC_MD_SCALP_METHOD["core_cash_btc_hold_untouched"] is True
    assert PRIMARY_BAR == "1H"


def test_card_helper_matches_flags_and_universe():
    c = card()
    assert c["id"] == LOCK_ID
    assert c["live_arm"] is False
    assert c["soft_pass_neq_arm"] is True
    assert c["halted"] is True
    assert c["place_orders"] is False
    assert c["not_a_forecast"] is True
    assert c["score_forbidden"] is True
    assert c["s1_transplant"] is False
    assert c["demo_oms"] is False
    assert c["default_yaml_untouched"] is True
    assert c["primary_dual"] == [list(p) for p in PRIMARY_DUAL]
    assert c["secondary_dual"] == [list(p) for p in SECONDARY_DUAL]
    assert c["public_only_ok"] == [list(p) for p in PUBLIC_ONLY_OK]
    assert c["spot_only_watch"] == list(SPOT_ONLY_WATCH)
    assert c["exclude"] == list(EXCLUDE)
    assert c["demo_block"] == list(DEMO_BLOCK)
    assert "phase1/115" in c["citation"]


def test_verified_instid_strings():
    assert PRIMARY_DUAL == (
        ("PUMP-USDC", "PUMP-USD_UM_XPERP-310404"),
        ("TRUMP-USDC", "TRUMP-USD_UM_XPERP-310704"),
        ("WIF-USDC", "WIF-USD_UM_XPERP-310815"),
    )
    assert SECONDARY_DUAL == (
        ("SHIB-USDC", "SHIB-USD_UM_XPERP-310801"),
        ("BONK-USDC", "BONK-USD_UM_XPERP-310725"),
    )
    assert PUBLIC_ONLY_OK == (("PEPE-USDC", "PEPE-USD_UM_XPERP-310404"),)
    assert SPOT_ONLY_WATCH == ("BOME-USDC", "FLOKI-USDC")
    assert EXCLUDE == ("DOGE",)
    assert NOT_ON_EEA_THIS_PROBE == ("FARTCOIN", "BRETT", "POPCAT", "MOG")
    assert DEMO_BLOCK == ("PEPE", "PUMP", "TRUMP")
    assert DEMO_PENDING_OPS == ("WIF", "SHIB", "BONK")
    # No S1 / DOGE Dual Thrust transplant markers on meme pairs.
    for spot, xperp in PRIMARY_DUAL + SECONDARY_DUAL + PUBLIC_ONLY_OK:
        assert "DOGE" not in spot and "DOGE" not in xperp
        assert "dual_thrust" not in spot.lower()
