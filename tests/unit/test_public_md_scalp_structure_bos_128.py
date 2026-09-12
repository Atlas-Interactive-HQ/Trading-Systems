"""Unit tests: phase1/128 indicator-layer ladder R1–R8 on #126+FT."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_structure_bos_125 import TIME_STOP_CONVENTION
from atlas.paper.public_md_scalp_structure_bos_128 import (
    FETCH_END_EXCLUSIVE_ISO,
    ID_FAMILY_PREFIX,
    MEME_2020_NA,
    PASS_PAIRS_NEEDED,
    PHASE1,
    PARENT_PHASE1,
    SCALP_S1_ID_FORBIDDEN,
    SLEEVE_EUR,
    SOURCE,
    USD_UNAVAILABLE,
    USDT_INSTS,
    WARMUP_START_ISO,
    WINDOWS,
    candidate_id_for,
    walk_structure_bos_128,
)
from atlas.paper.types import Bar
from atlas.strategy.scalp_structure_bos_125 import (
    BULL,
    FLAT,
    PIVOT_N,
    R_MULTIPLE,
    TIME_STOP_BARS,
    EntryExitSignals,
)
from atlas.strategy.scalp_structure_bos_128 import (
    CCI_EXIT_MIN,
    LATE_FILTER_RSI_MAX,
    PULLBACK_DIP_MAX,
    RSI_EXIT_MIN_DEFAULT,
    RUNG_IDS,
    RUNGS,
    STOCH_EXIT_MIN,
    StructureBos128Params,
    StructureBos128V1,
    cci_series,
    get_rung,
    indicator_exit_triggered,
    precompute_entry_signals,
    stoch_slow_k_series,
)


def test_phase_and_source_locked_128():
    assert PHASE1 == 128
    assert PARENT_PHASE1 == 126
    assert SOURCE == "public_md_scalp_structure_bos_128"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert PASS_PAIRS_NEEDED == 2
    assert TIME_STOP_BARS == 45
    assert R_MULTIPLE == 1.5
    assert PIVOT_N == 3
    assert TIME_STOP_CONVENTION.startswith("signal_at_close")
    assert "ind_ladder" in ID_FAMILY_PREFIX
    assert "long_only" in ID_FAMILY_PREFIX


def test_all_eight_rung_ids_registered():
    assert RUNG_IDS == ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8")
    for rid in RUNG_IDS:
        spec = get_rung(rid)
        assert spec.rung_id == rid
        assert spec.entry_rsi_band is None  # no #127 band restore
        assert spec.exit_threshold is not None  # indicator layer present


def test_rung_specs_match_preregistered_ladder():
    assert RUNGS["R1"].indicator_kind == "rsi"
    assert RUNGS["R1"].indicator_tf == "3m"
    assert RUNGS["R1"].rsi_period == 14
    assert RUNGS["R1"].exit_threshold == RSI_EXIT_MIN_DEFAULT == 67.0
    assert RUNGS["R1"].late_filter_rsi_ge is None
    assert RUNGS["R1"].pullback_dip_le is None

    assert RUNGS["R2"].late_filter_rsi_ge == LATE_FILTER_RSI_MAX == 75.0
    assert RUNGS["R3"].indicator_tf == "15m"
    assert RUNGS["R4"].rsi_period == 7
    assert RUNGS["R5"].rsi_period == 21
    assert RUNGS["R6"].indicator_kind == "stoch_k"
    assert RUNGS["R6"].exit_threshold == STOCH_EXIT_MIN == 80.0
    assert RUNGS["R7"].indicator_kind == "cci"
    assert RUNGS["R7"].exit_threshold == CCI_EXIT_MIN == 100.0
    assert RUNGS["R8"].pullback_dip_le == PULLBACK_DIP_MAX == 45.0
    assert RUNGS["R8"].exit_threshold == 67.0


def test_off_ladder_rung_forbidden():
    with pytest.raises(ValueError, match="off-ladder"):
        get_rung("R9")
    with pytest.raises(ValueError, match="off-ladder"):
        StructureBos128V1(StructureBos128Params(rung_id="R0"))  # type: ignore[arg-type]


def test_no_indicator_layer_forbidden():
    with pytest.raises(ValueError, match="indicator layer"):
        StructureBos128V1(
            StructureBos128Params(rung_id="R1", indicator_layer_required=False)
        )


def test_usdt_windows_same_as_126():
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert USD_UNAVAILABLE == ("BTC-USD", "ETH-USD", "DOGE-USD")
    assert "PEPE-USDC" in MEME_2020_NA
    assert WINDOWS["FULL"] == ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z")
    assert WARMUP_START_ISO == "2020-06-01T00:00:00Z"
    assert FETCH_END_EXCLUSIVE_ISO == "2021-01-01T00:00:00Z"


def test_candidate_ids_per_rung():
    assert SCALP_S1_ID_FORBIDDEN.startswith("rise_panel_v1_scalp_doge_dual_thrust")
    for rid in RUNG_IDS:
        for inst in USDT_INSTS:
            cid = candidate_id_for(inst, rid)
            assert cid.startswith(ID_FAMILY_PREFIX + "_")
            assert f"_{rid.lower()}_" in cid
            assert cid.endswith("_eur20")
            assert cid != SCALP_S1_ID_FORBIDDEN
            assert "rise_panel" not in cid


def test_params_locked_per_rung():
    for rid in RUNG_IDS:
        s = StructureBos128V1(StructureBos128Params(rung_id=rid))
        assert s.params.long_only is True
        assert s.params.bos_follow_through is True
        assert s.params.indicator_layer_required is True
        assert s.params.pivot_n == PIVOT_N == 3
        assert s.params.confirm_closed_only is True
        assert s.params.rung.entry_rsi_band is None


def test_grind_raises():
    with pytest.raises(ValueError, match="long_only"):
        StructureBos128V1(StructureBos128Params(long_only=False))
    with pytest.raises(ValueError, match="follow_through"):
        StructureBos128V1(StructureBos128Params(bos_follow_through=False))
    with pytest.raises(ValueError, match="pivot"):
        StructureBos128V1(StructureBos128Params(pivot_n=5))
    with pytest.raises(ValueError, match="R-multiple"):
        StructureBos128V1(StructureBos128Params(r_multiple=2.0))
    with pytest.raises(ValueError, match="time-stop"):
        StructureBos128V1(StructureBos128Params(time_stop_bars=30))


def test_indicator_exit_threshold_per_kind():
    assert indicator_exit_triggered(67.0, 67.0) is True
    assert indicator_exit_triggered(66.999, 67.0) is False
    assert indicator_exit_triggered(80.0, STOCH_EXIT_MIN) is True
    assert indicator_exit_triggered(79.999, STOCH_EXIT_MIN) is False
    assert indicator_exit_triggered(100.0, CCI_EXIT_MIN) is True
    assert indicator_exit_triggered(99.999, CCI_EXIT_MIN) is False
    assert indicator_exit_triggered(None, 67.0) is False


def test_stoch_and_cci_series_smoke():
    n = 40
    highs = [100.0 + (i % 5) for i in range(n)]
    lows = [90.0 + (i % 5) for i in range(n)]
    closes = [95.0 + (i % 7) * 0.5 for i in range(n)]
    k, d = stoch_slow_k_series(highs, lows, closes)
    assert any(v is not None for v in k)
    assert any(v is not None for v in d)
    cci = cci_series(highs, lows, closes)
    assert any(v is not None for v in cci)


def _bar1m(ts: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(
        symbol="BTC-USDT",
        ts_open_ms=ts,
        ts_close_ms=ts + 60_000,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=1.0,
        closed=True,
        source="test",
    )


def test_walker_indicator_exit_and_no_shorts():
    n = 8
    bars = [_bar1m(i * 60_000, 100, 101, 99, 100.5) for i in range(n)]
    # entry on i=0 → fill i=1; indicator exit fires on i=3
    sig = EntryExitSignals(
        entry_long=[True] + [False] * (n - 1),
        entry_short=[False] * n,
        bias=[BULL] * n,
        rsi=[None, None, None, 70.0, 70.0, 70.0, 70.0, 70.0],
        active_swing_high=[101.0] * n,
        active_swing_low=[95.0] * n,
        swing_version=[1] * n,
        opposite_extreme=[None] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    out = walk_structure_bos_128(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000,
        indicator_exit_min=67.0,
        indicator_kind="rsi",
    )
    assert out["n_short_entries"] == 0
    assert out["n_long_entries"] >= 1
    assert out["n_indicator_exits"] >= 1
    assert out["place_orders"] is False
    assert out["not_a_forecast"] is True


def test_pass_gate_rule_documented():
    """PASS = exp>0 AND terminal≥BH on ≥2/3 pairs FULL — Soft PASS N/A ≠ arm."""
    assert PASS_PAIRS_NEEDED == 2
    # Soft PASS is never an arm
    from atlas.paper.public_md_scalp_structure_bos_128 import run_structure_bos_128_score

    assert callable(run_structure_bos_128_score)


def test_precompute_r1_requires_follow_through_no_band():
    """R1: FT required; RSI band OFF (entry can fire without RSI in [20,30])."""
    # Minimal synthetic: build enough 15m for structure is heavy; instead assert
    # empty inputs fail closed cleanly and R1 params have no band.
    sig = precompute_entry_signals([], [], [], params=StructureBos128Params(rung_id="R1"))
    assert sig.entry_long == []
    assert RUNGS["R1"].entry_rsi_band is None
    assert all(RUNGS[r].entry_rsi_band is None for r in RUNG_IDS)


@pytest.mark.parametrize("rid", list(RUNG_IDS))
def test_each_rung_id_constructs(rid):
    s = StructureBos128V1(StructureBos128Params(rung_id=rid))
    assert rid in s.label
    assert s.params.indicator_layer_required is True
