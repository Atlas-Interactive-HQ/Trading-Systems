"""Unit tests: phase1/126 long-only strengthen of #125."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_structure_bos_125 import (
    TIME_STOP_CONVENTION,
    walk_structure_bos,
)
from atlas.paper.public_md_scalp_structure_bos_126 import (
    FETCH_END_EXCLUSIVE_ISO,
    ID_FAMILY,
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
)
from atlas.paper.types import Bar
from atlas.strategy.scalp_structure_bos_125 import (
    BEAR,
    BULL,
    FLAT,
    PIVOT_N,
    R_MULTIPLE,
    RSI_PERIOD,
    TIME_STOP_BARS,
    EntryExitSignals,
    precompute_entry_signals as precompute_125,
)
from atlas.strategy.scalp_structure_bos_126 import (
    StructureBos126Params,
    StructureBos126V1,
    apply_long_only,
    precompute_entry_signals,
)


def test_phase_and_source_locked_126():
    assert PHASE1 == 126
    assert PARENT_PHASE1 == 125
    assert SOURCE == "public_md_scalp_structure_bos_126"
    assert "125" not in SOURCE or SOURCE.endswith("_126")
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert PASS_PAIRS_NEEDED == 2
    assert TIME_STOP_BARS == 45
    assert R_MULTIPLE == 1.5
    assert PIVOT_N == 3
    assert RSI_PERIOD == 14
    assert ID_FAMILY.endswith("_long_only")


def test_usdt_windows_same_as_125():
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert USD_UNAVAILABLE == ("BTC-USD", "ETH-USD", "DOGE-USD")
    assert "PEPE-USDC" in MEME_2020_NA
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


def test_candidate_ids_long_only_no_s1():
    assert SCALP_S1_ID_FORBIDDEN.startswith("rise_panel_v1_scalp_doge_dual_thrust")
    for inst in USDT_INSTS:
        cid = candidate_id_for(inst)
        assert cid.startswith("public_md_v1_structure_bos_15m_rsi3m_1m_long_only_")
        assert cid.endswith("_eur20")
        assert "long_short" not in cid
        assert cid != SCALP_S1_ID_FORBIDDEN
        assert "rise_panel" not in cid


def test_long_only_params_locked():
    s = StructureBos126V1(StructureBos126Params(long_only=True))
    assert s.params.long_only is True
    assert s.params.pivot_n == PIVOT_N == 3
    assert s.params.rsi_period == RSI_PERIOD == 14
    assert float(s.params.r_multiple) == float(R_MULTIPLE) == 1.5
    assert int(s.params.time_stop_bars) == TIME_STOP_BARS == 45
    assert s.params.confirm_closed_only is True
    assert s.params.bar_structure == "15m"
    assert s.params.bar_rsi == "3m"
    assert s.params.bar_entry == "1m"


def test_long_only_false_raises():
    import pytest

    with pytest.raises(ValueError, match="long_only"):
        StructureBos126V1(StructureBos126Params(long_only=False))


def test_no_grind_raises_via_125():
    import pytest

    with pytest.raises(ValueError, match="pivot"):
        StructureBos126V1(StructureBos126Params(pivot_n=5))
    with pytest.raises(ValueError, match="RSI"):
        StructureBos126V1(StructureBos126Params(rsi_period=7))
    with pytest.raises(ValueError, match="R-multiple"):
        StructureBos126V1(StructureBos126Params(r_multiple=2.0))
    with pytest.raises(ValueError, match="time-stop"):
        StructureBos126V1(StructureBos126Params(time_stop_bars=30))


def test_apply_long_only_zeros_shorts():
    n = 5
    sig = EntryExitSignals(
        entry_long=[True, False, True, False, False],
        entry_short=[False, True, True, False, True],
        bias=[BULL, BEAR, BULL, FLAT, BEAR],
        rsi=[60.0] * n,
        active_swing_high=[100.0] * n,
        active_swing_low=[90.0] * n,
        swing_version=[1, 2, 3, 4, 5],
        opposite_extreme=[None] * n,
    )
    out = apply_long_only(sig)
    assert out.entry_long == sig.entry_long
    assert out.entry_short == [False] * n
    assert any(sig.entry_short)  # original had shorts
    assert not any(out.entry_short)


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


def test_walker_no_short_trades_under_long_only_signals():
    """Same exits as #125 (TP/SL/opp_bos/time_stop) but zero short entries."""
    bars = [
        _bar1m(0, 100, 100, 99, 100),
        _bar1m(60_000, 100, 101, 99.5, 100.5),
        _bar1m(120_000, 100.5, 110, 100, 109),
        _bar1m(180_000, 109, 109, 108, 108.5),
        _bar1m(240_000, 108.5, 109, 108, 108.8),
    ]
    n = len(bars)
    # Even if short flags were present, long_only apply zeros them
    raw = EntryExitSignals(
        entry_long=[True, False, False, False, False],
        entry_short=[True, True, False, False, False],  # would be shorts in #125
        bias=[BULL] * n,
        rsi=[60.0] * n,
        active_swing_high=[99.0] * n,
        active_swing_low=[95.0] * n,
        swing_version=[1] * n,
        opposite_extreme=[None] * n,
    )
    sig = apply_long_only(raw)
    assert not any(sig.entry_short)
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    walk = walk_structure_bos(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=300_000,
    )
    assert walk["n_short_entries"] == 0
    assert walk["n_long_entries"] >= 1
    assert walk["n_trades"] >= 1
    assert walk.get("place_orders") is False
    assert walk["time_stop_convention"] == TIME_STOP_CONVENTION
    # Exit mix keys same as #125 walker
    for k in ("n_tp_exits", "n_sl_exits", "n_opp_bos_exits", "n_time_stop_exits"):
        assert k in walk


def test_precompute_long_only_never_emits_short():
    bars_15 = []
    for i in range(40):
        base = 100 + i * 0.5
        bars_15.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=i * 15 * 60_000,
                ts_close_ms=(i + 1) * 15 * 60_000,
                open=base,
                high=base + 2,
                low=base - 2,
                close=base + 0.5,
                volume=1.0,
                closed=True,
                source="test",
            )
        )
    bars_3 = []
    for i in range(200):
        base = 100 + i * 0.05
        bars_3.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=i * 3 * 60_000,
                ts_close_ms=(i + 1) * 3 * 60_000,
                open=base,
                high=base + 1,
                low=base - 1,
                close=base + 0.2,
                volume=1.0,
                closed=True,
                source="test",
            )
        )
    bars_1 = []
    for i in range(600):
        base = 100 + i * 0.01
        bars_1.append(_bar1m(i * 60_000, base, base + 0.5, base - 0.5, base + 0.1))

    sig125 = precompute_125(bars_1, bars_15, bars_3)
    sig126 = precompute_entry_signals(
        bars_1, bars_15, bars_3, params=StructureBos126Params(long_only=True)
    )
    assert len(sig126.entry_long) == len(bars_1)
    assert not any(sig126.entry_short)
    # Longs preserved from 125 (subset equality: 126 longs ⊆ 125 longs, equal here)
    assert sig126.entry_long == sig125.entry_long
    # 125 may have shorts; 126 must not
    if any(sig125.entry_short):
        assert sum(sig126.entry_short) == 0


def test_pass_gate_2_of_3_constant():
    assert PASS_PAIRS_NEEDED == 2
    assert len(USDT_INSTS) == 3
    assert ID_FAMILY.endswith("_long_only")
    # Soft PASS N/A ≠ arm is a documentation/runtime stamp, not arming
    assert PHASE1 == 126
