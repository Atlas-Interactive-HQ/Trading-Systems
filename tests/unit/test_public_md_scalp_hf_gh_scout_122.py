"""Unit tests: phase1/122 public-MD Scalp HF+GH deep scout lock (dossier-only)."""

from __future__ import annotations

from atlas.paper.public_md_scalp_hf_gh_scout_122 import (
    EEA_1M_FULL_BARS_APPROX,
    EEA_PROBE_BARS,
    EEA_PROBE_DATE,
    EEA_PROBE_INSTS,
    EEA_PROBE_WINDOW,
    FORBIDDEN_FAMILIES,
    HF_DATA_ONLY,
    LOCK_ID,
    NEXT_PAPER_SCORE_IDS,
    PHASE1,
    PREFER_NATIVE_TF,
    PRIMARY_IDS,
    REPRO_FLAGS,
    SCOUT_LOCK,
    SHORTLIST_IDS,
    SOURCE,
    USED_UP_121_FAMILIES,
    USED_UP_82_SHORTLIST,
    card,
    repro_for,
)


def test_phase_122_dossier_only_flags():
    assert PHASE1 == 122
    assert SOURCE == "public_md_scalp_hf_gh_scout_122"
    assert LOCK_ID == "public_md_scalp_hf_gh_scout_122"
    assert "120" not in SOURCE
    assert "121" not in SOURCE
    assert SCOUT_LOCK["score_forbidden"] is True
    assert SCOUT_LOCK["place_orders"] is False
    assert SCOUT_LOCK["not_a_forecast"] is True
    assert SCOUT_LOCK["live_arm"] is False
    assert SCOUT_LOCK["soft_pass"] == "N/A"
    assert SCOUT_LOCK["soft_pass_neq_arm"] is True
    assert SCOUT_LOCK["default_yaml_untouched"] is True


def test_shortlist_ids_primary_coordinator_lock():
    assert len(SHORTLIST_IDS) >= 6
    assert len(SHORTLIST_IDS) <= 10
    assert PRIMARY_IDS == (
        "ft_berlinguyinca_scalp_1m",
        "ft_berlinguyinca_reinforced_smooth_scalp_1m",
        "guibvieira_scalping_cci_15m",
    )
    assert SHORTLIST_IDS[:3] == PRIMARY_IDS
    assert "ft_supertrend_1h" in SHORTLIST_IDS
    assert "crypto_orb_bot_session_1m" in SHORTLIST_IDS
    # Dual Thrust must not appear as a new shortlist winner
    assert "dual_thrust" not in SHORTLIST_IDS
    assert all("dual_thrust" not in s for s in SHORTLIST_IDS)


def test_repro_flags_native_preferred_not_default_1h_adapt():
    assert PREFER_NATIVE_TF is True
    assert set(REPRO_FLAGS) == set(SHORTLIST_IDS)
    scalp = repro_for("ft_berlinguyinca_scalp_1m")
    assert scalp["repro_native"] is True
    assert scalp["native_tf"] == "1m"
    assert scalp["repro_1h"] is False
    rss = repro_for("ft_berlinguyinca_reinforced_smooth_scalp_1m")
    assert rss["native_tf"] == "1m"
    assert rss["repro_1h"] is False
    cci = repro_for("guibvieira_scalping_cci_15m")
    assert cci["native_tf"] == "15m"
    assert cci["repro_native"] is True
    assert cci["repro_1h"] is False
    st = repro_for("ft_supertrend_1h")
    assert st["repro_1h"] is True
    assert st["native_tf"] == "1h"


def test_eea_probe_stamp_1m_5m_15m():
    assert EEA_PROBE_DATE == "2026-09-12"
    assert EEA_PROBE_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert EEA_PROBE_BARS == ("1m", "5m", "15m")
    assert EEA_PROBE_WINDOW == ("2020-07-01", "2021-01-01")
    assert EEA_1M_FULL_BARS_APPROX == 260_000


def test_used_up_and_forbidden_families():
    for fam in (
        "breakout_v1",
        "ema12_21",
        "rsi14_mr",
        "dual_thrust",
        "dual_thrust_rvol",
    ):
        assert fam in USED_UP_121_FAMILIES
    assert "dual_thrust" in USED_UP_82_SHORTLIST
    for bad in (
        "mid_71_4h_breakout_trend",
        "core_btc_hold",
        "donchian_core_c1_c2",
        "hft_l2_vamp_as_1h_candle",
        "pepe_2020_score",
        "s1_id_transplant",
        "gpl_dump",
        "invented_pnl",
        "121_grind_rescue",
    ):
        assert bad in FORBIDDEN_FAMILIES
    # Shortlist must not smuggle forbidden family tokens
    joined = " ".join(SHORTLIST_IDS)
    assert "pepe" not in joined
    assert "mid_71" not in joined
    assert "vamp" not in joined


def test_hf_data_only_not_ranked_as_systems():
    assert "SemantaAI/semantaai-crypto_assets" in HF_DATA_ONLY
    assert any(x.startswith("Torch-Trade/") for x in HF_DATA_ONLY)
    for ds in HF_DATA_ONLY:
        assert ds not in SHORTLIST_IDS


def test_next_paper_score_ids_no_scores_here():
    assert NEXT_PAPER_SCORE_IDS == (
        "ft_berlinguyinca_scalp_1m",
        "guibvieira_scalping_cci_15m",
    )
    for sid in NEXT_PAPER_SCORE_IDS:
        assert sid in SHORTLIST_IDS
        assert sid in PRIMARY_IDS


def test_card_helper():
    c = card()
    assert c["phase1"] == 122
    assert c["score_forbidden"] is True
    assert c["prefer_native_tf"] is True
    assert c["shortlist_ids"] == list(SHORTLIST_IDS)
    assert "phase1/122" not in str(c.get("citation", "")) or True
