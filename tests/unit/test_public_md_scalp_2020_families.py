"""Unit tests: phase1/121 public-MD Scalp 2020 family compare lock constants."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.public_md_scalp_2020_families import (
    BAR,
    FAMILY_META,
    FAMILY_ORDER,
    FETCH_END_EXCLUSIVE_ISO,
    MEME_2020_NA,
    PHASE1,
    SCALP_S1_ID_FORBIDDEN,
    SLEEVE_EUR,
    SOURCE,
    USD_UNAVAILABLE,
    USDT_INSTS,
    WARMUP_START_ISO,
    WINDOWS,
    candidate_id_for,
    make_strategy,
)
from atlas.strategy.ema_trend import FLAT, LONG


def test_phase_and_source_locked_121_not_120():
    assert PHASE1 == 121
    assert SOURCE == "public_md_scalp_2020_families_121"
    assert "120" not in SOURCE
    assert BAR == "1H"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR


def test_usdt_insts_and_usd_unavailable():
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert USD_UNAVAILABLE == ("BTC-USD", "ETH-USD", "DOGE-USD")
    for u in USD_UNAVAILABLE:
        assert u.endswith("-USD")
        assert not u.endswith("-USDT")


def test_meme_2020_na_no_pepe_score_list():
    assert "PEPE-USDC" in MEME_2020_NA
    assert "PUMP-USDC" in MEME_2020_NA
    assert "TRUMP-USDC" in MEME_2020_NA
    assert "WIF-USDC" in MEME_2020_NA


def test_windows_locked():
    assert WINDOWS["FULL"] == ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z")
    assert WINDOWS["SUB_A_DEFI_SUMMER"] == (
        "2020-07-01T00:00:00Z",
        "2020-10-01T00:00:00Z",
    )
    assert WINDOWS["SUB_B_BTC_RUN"] == (
        "2020-10-01T00:00:00Z",
        "2021-01-01T00:00:00Z",
    )
    assert WARMUP_START_ISO == "2020-06-01T00:00:00Z"
    assert FETCH_END_EXCLUSIVE_ISO == "2021-01-01T00:00:00Z"


def test_family_order_and_new_2020_ids():
    assert FAMILY_ORDER == (
        "breakout_v1",
        "ema12_21",
        "rsi14_mr",
        "dual_thrust",
        "dual_thrust_rvol",
    )
    assert SCALP_S1_ID_FORBIDDEN == (
        "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
    )
    for fk in FAMILY_ORDER:
        meta = FAMILY_META[fk]
        assert meta["id_family"].startswith("public_md_v1_2020_")
        assert "rise_panel" not in meta["id_family"]
        for inst in USDT_INSTS:
            cid = candidate_id_for(fk, inst)
            assert cid.startswith("public_md_v1_2020_")
            assert cid.endswith("_eur20")
            assert cid != SCALP_S1_ID_FORBIDDEN
            assert "rise_panel" not in cid
            assert "#83" not in cid
            assert "#59" not in cid
            assert "#62" not in cid
            assert "#117" not in cid
            assert "#118" not in cid
            assert "#119" not in cid
            assert inst.lower().replace("-", "_") in cid


def test_strategies_construct():
    for fk in FAMILY_ORDER:
        s = make_strategy(fk)
        assert hasattr(s, "desired_state")
    assert LONG == "long"
    assert FLAT == "flat"


def test_breakout_params_locked():
    s = make_strategy("breakout_v1")
    assert s.params.lookback == 16
    assert s.params.atr_period == 14
    assert s.params.min_atr_frac == 0.001
    assert s.params.oneh_filter == "off"


def test_rsi_params_locked():
    s = make_strategy("rsi14_mr")
    assert s.params.rsi_period == 14
    assert s.params.entry_rsi == 30.0
    assert s.params.exit_rsi == 70.0


def test_dual_thrust_rvol_mechanism_not_s1_id():
    s = make_strategy("dual_thrust_rvol")
    assert s.params.lookback == 20
    assert s.params.k1 == 0.5
    assert s.params.k2 == 0.5
    cid = candidate_id_for("dual_thrust_rvol", "DOGE-USDT")
    assert cid != SCALP_S1_ID_FORBIDDEN
    assert "2020" in cid
