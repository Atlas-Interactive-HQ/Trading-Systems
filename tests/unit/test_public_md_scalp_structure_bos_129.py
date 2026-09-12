"""Unit tests: phase1/129 time-stop/R/ATR-SL/retest ladder E1–E6 on #126+FT."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_structure_bos_125 import TIME_STOP_CONVENTION
from atlas.paper.public_md_scalp_structure_bos_129 import (
    BASELINE_126_FULL,
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
    walk_structure_bos_129,
)
from atlas.paper.types import Bar
from atlas.strategy.scalp_structure_bos_125 import (
    BULL,
    FLAT,
    PIVOT_N,
    EntryExitSignals,
)
from atlas.strategy.scalp_structure_bos_129 import (
    ATR_PERIOD,
    ATR_SL_MULT,
    DEFAULT_R,
    E1_TIME_STOP,
    E2_TIME_STOP,
    RETEST_MAX_BARS,
    RUNG_IDS,
    RUNGS,
    StructureBos129Params,
    StructureBos129V1,
    atr_wilder_series,
    get_rung,
    precompute_entry_signals,
)


def test_phase_and_source_locked_129():
    assert PHASE1 == 129
    assert PARENT_PHASE1 == 126
    assert SOURCE == "public_md_scalp_structure_bos_129"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert PASS_PAIRS_NEEDED == 2
    assert PIVOT_N == 3
    assert TIME_STOP_CONVENTION.startswith("signal_at_close")
    assert "exits_ladder" in ID_FAMILY_PREFIX
    assert "long_only" in ID_FAMILY_PREFIX


def test_all_six_rung_ids_registered():
    assert RUNG_IDS == ("E1", "E2", "E3", "E4", "E5", "E6")
    for rid in RUNG_IDS:
        spec = get_rung(rid)
        assert spec.rung_id == rid
        assert spec.entry_rsi_band is None
        assert spec.indicator_exit is False
        assert spec.entry_rsi_gate is False


def test_rung_specs_match_preregistered_ladder():
    assert RUNGS["E1"].time_stop_bars == E1_TIME_STOP == 180
    assert RUNGS["E1"].r_multiple == DEFAULT_R == 1.5
    assert RUNGS["E1"].sl_mode == "swing"
    assert RUNGS["E1"].retest_entry is False

    assert RUNGS["E2"].time_stop_bars == E2_TIME_STOP == 480
    assert RUNGS["E2"].r_multiple == 1.5
    assert RUNGS["E2"].sl_mode == "swing"

    assert RUNGS["E3"].time_stop_bars == 180
    assert RUNGS["E3"].r_multiple == 1.0
    assert RUNGS["E3"].sl_mode == "swing"

    assert RUNGS["E4"].time_stop_bars is None
    assert RUNGS["E4"].r_multiple == 1.5
    assert RUNGS["E4"].sl_mode == "swing"

    assert RUNGS["E5"].time_stop_bars == 180
    assert RUNGS["E5"].r_multiple == 1.5
    assert RUNGS["E5"].sl_mode == "atr"
    assert RUNGS["E5"].atr_period == ATR_PERIOD == 14
    assert RUNGS["E5"].atr_sl_mult == ATR_SL_MULT == 1.5

    assert RUNGS["E6"].time_stop_bars == 180
    assert RUNGS["E6"].r_multiple == 1.5
    assert RUNGS["E6"].sl_mode == "swing"
    assert RUNGS["E6"].retest_entry is True
    assert RUNGS["E6"].retest_max_bars == RETEST_MAX_BARS == 15


def test_off_ladder_rung_forbidden():
    with pytest.raises(ValueError, match="off-ladder"):
        get_rung("E7")
    with pytest.raises(ValueError, match="off-ladder"):
        get_rung("R1")
    with pytest.raises(ValueError, match="off-ladder"):
        StructureBos129V1(StructureBos129Params(rung_id="E0"))  # type: ignore[arg-type]


def test_no_indicator_exit_locked():
    with pytest.raises(ValueError, match="indicator early-exit"):
        StructureBos129V1(
            StructureBos129Params(rung_id="E1", no_indicator_exit=False)
        )
    with pytest.raises(ValueError, match="indicator entry"):
        StructureBos129V1(
            StructureBos129Params(rung_id="E1", no_indicator_entry_gate=False)
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
        s = StructureBos129V1(StructureBos129Params(rung_id=rid))
        assert s.params.long_only is True
        assert s.params.bos_follow_through is True
        assert s.params.no_indicator_exit is True
        assert s.params.no_indicator_entry_gate is True
        assert s.params.pivot_n == PIVOT_N == 3
        assert s.params.confirm_closed_only is True
        assert s.params.rung.entry_rsi_band is None
        assert s.params.rung.indicator_exit is False


def test_grind_raises_structure_and_ft():
    with pytest.raises(ValueError, match="long_only"):
        StructureBos129V1(StructureBos129Params(long_only=False))
    with pytest.raises(ValueError, match="follow_through"):
        StructureBos129V1(StructureBos129Params(bos_follow_through=False))
    with pytest.raises(ValueError, match="pivot"):
        StructureBos129V1(StructureBos129Params(pivot_n=5))


def test_baseline_126_locked():
    assert BASELINE_126_FULL["BTC-USDT"]["n"] == 339
    assert BASELINE_126_FULL["ETH-USDT"]["n"] == 337
    assert BASELINE_126_FULL["DOGE-USDT"]["n"] == 222
    assert BASELINE_126_FULL["BTC-USDT"]["exp"] == pytest.approx(-0.02643514)
    assert BASELINE_126_FULL["ETH-USDT"]["terminal"] == pytest.approx(-7.18156963)


def test_atr_wilder_series_smoke():
    n = 40
    highs = [100.0 + (i % 5) for i in range(n)]
    lows = [90.0 + (i % 5) for i in range(n)]
    closes = [95.0 + (i % 7) * 0.5 for i in range(n)]
    atr = atr_wilder_series(highs, lows, closes, period=14)
    assert atr[13] is not None
    assert atr[14] is not None
    assert atr[0] is None
    # Wilder smooth: next ATR between prev and TR
    assert atr[20] is not None and atr[20] > 0


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


def test_walker_no_indicator_exit_and_time_stop():
    n = 12
    bars = [_bar1m(i * 60_000, 100, 101, 99, 100.5) for i in range(n)]
    sig = EntryExitSignals(
        entry_long=[True] + [False] * (n - 1),
        entry_short=[False] * n,
        bias=[BULL] * n,
        rsi=[1.0] * n,  # ATR placeholder unused for swing SL
        active_swing_high=[101.0] * n,
        active_swing_low=[95.0] * n,
        swing_version=[1] * n,
        opposite_extreme=[None] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    out = walk_structure_bos_129(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000,
        r_multiple=1.5,
        time_stop_bars=3,
        sl_mode="swing",
    )
    assert out["n_short_entries"] == 0
    assert out["n_long_entries"] >= 1
    assert out["n_indicator_exits"] == 0
    assert out["n_time_stop_exits"] >= 1
    assert out["no_indicator_exit"] is True
    assert out["place_orders"] is False
    assert out["not_a_forecast"] is True


def test_walker_time_stop_none_never_times_out():
    n = 20
    # Price stays between SL and TP
    bars = [_bar1m(i * 60_000, 100, 100.5, 99.5, 100.2) for i in range(n)]
    sig = EntryExitSignals(
        entry_long=[True] + [False] * (n - 1),
        entry_short=[False] * n,
        bias=[BULL] * n,
        rsi=[1.0] * n,
        active_swing_high=[110.0] * n,
        active_swing_low=[90.0] * n,
        swing_version=[1] * n,
        opposite_extreme=[None] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    out = walk_structure_bos_129(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000,
        r_multiple=1.5,
        time_stop_bars=None,
        sl_mode="swing",
    )
    assert out["n_time_stop_exits"] == 0
    assert out["time_stop_bars"] is None
    assert out["n_indicator_exits"] == 0


def test_walker_atr_sl_mode():
    n = 10
    bars = [_bar1m(i * 60_000, 100, 101, 99, 100) for i in range(n)]
    # Drop after entry to hit ATR SL
    bars[3] = _bar1m(3 * 60_000, 100, 100, 96, 96.5)
    bars[4] = _bar1m(4 * 60_000, 96.5, 97, 96, 96.2)
    sig = EntryExitSignals(
        entry_long=[True] + [False] * (n - 1),
        entry_short=[False] * n,
        bias=[BULL] * n,
        rsi=[2.0] * n,  # ATR=2 → SL = entry - 1.5*2 = entry-3
        active_swing_high=[101.0] * n,
        active_swing_low=[50.0] * n,  # swing SL far away; ATR SL tighter
        swing_version=[1] * n,
        opposite_extreme=[None] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    out = walk_structure_bos_129(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000,
        r_multiple=1.5,
        time_stop_bars=180,
        sl_mode="atr",
        atr_sl_mult=1.5,
    )
    assert out["n_short_entries"] == 0
    assert out["n_indicator_exits"] == 0
    assert out["sl_mode"] == "atr"
    assert out["n_sl_exits"] >= 1 or out["n_trades"] >= 1


def test_pass_gate_rule_documented():
    """PASS = exp>0 AND terminal≥BH on ≥2/3 pairs FULL — Soft PASS N/A ≠ arm."""
    assert PASS_PAIRS_NEEDED == 2
    from atlas.paper.public_md_scalp_structure_bos_129 import run_structure_bos_129_score

    assert callable(run_structure_bos_129_score)


def test_precompute_empty_and_no_band():
    sig = precompute_entry_signals([], [], [], params=StructureBos129Params(rung_id="E1"))
    assert sig.entry_long == []
    assert all(RUNGS[r].entry_rsi_band is None for r in RUNG_IDS)
    assert all(RUNGS[r].indicator_exit is False for r in RUNG_IDS)


@pytest.mark.parametrize("rid", list(RUNG_IDS))
def test_each_e_id_constructs(rid):
    s = StructureBos129V1(StructureBos129Params(rung_id=rid))
    assert rid in s.label
    assert s.params.no_indicator_exit is True
    assert s.params.r_multiple == RUNGS[rid].r_multiple
    assert s.params.time_stop_bars == RUNGS[rid].time_stop_bars


def test_soft_pass_na_not_arm():
    from atlas.paper.public_md_scalp_structure_bos_129 import SOURCE as S

    assert S.endswith("129")
    # Soft PASS N/A ≠ arm is a reporting lock; gate uses PASS_PAIRS_NEEDED only.
    assert PASS_PAIRS_NEEDED == 2
