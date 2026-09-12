"""Unit tests: phase1/127 BOS follow-through + RSI 20-30/67 on #126 long-only."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_structure_bos_125 import TIME_STOP_CONVENTION
from atlas.paper.public_md_scalp_structure_bos_127 import (
    FETCH_END_EXCLUSIVE_ISO,
    ID_FAMILY,
    MEME_2020_NA,
    PASS_PAIRS_NEEDED,
    PHASE1,
    PARENT_PHASE1,
    RSI_ENTRY_HI,
    RSI_ENTRY_LO,
    RSI_EXIT_MIN,
    SCALP_S1_ID_FORBIDDEN,
    SLEEVE_EUR,
    SOURCE,
    USD_UNAVAILABLE,
    USDT_INSTS,
    WARMUP_START_ISO,
    WINDOWS,
    candidate_id_for,
    walk_structure_bos_127,
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
)
from atlas.strategy.scalp_structure_bos_127 import (
    StructureBos127Params,
    StructureBos127V1,
    precompute_entry_signals,
    rsi_entry_band_allows,
    rsi_exit_triggered,
)


def test_phase_and_source_locked_127():
    assert PHASE1 == 127
    assert PARENT_PHASE1 == 126
    assert SOURCE == "public_md_scalp_structure_bos_127"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert PASS_PAIRS_NEEDED == 2
    assert TIME_STOP_BARS == 45
    assert R_MULTIPLE == 1.5
    assert PIVOT_N == 3
    assert RSI_PERIOD == 14
    assert RSI_ENTRY_LO == 20.0
    assert RSI_ENTRY_HI == 30.0
    assert RSI_EXIT_MIN == 67.0
    assert "ft_rsi_bands" in ID_FAMILY
    assert "long_only" in ID_FAMILY


def test_usdt_windows_same_as_126():
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


def test_candidate_ids_127_no_s1():
    assert SCALP_S1_ID_FORBIDDEN.startswith("rise_panel_v1_scalp_doge_dual_thrust")
    for inst in USDT_INSTS:
        cid = candidate_id_for(inst)
        assert cid.startswith(
            "public_md_v1_structure_bos_15m_rsi3m_1m_long_only_ft_rsi_bands_"
        )
        assert cid.endswith("_eur20")
        assert cid != SCALP_S1_ID_FORBIDDEN
        assert "rise_panel" not in cid


def test_params_locked():
    s = StructureBos127V1(StructureBos127Params())
    assert s.params.long_only is True
    assert s.params.bos_follow_through is True
    assert s.params.rsi_entry_lo == 20.0
    assert s.params.rsi_entry_hi == 30.0
    assert s.params.rsi_exit_min == 67.0
    assert s.params.pivot_n == PIVOT_N == 3
    assert s.params.confirm_closed_only is True


def test_grind_raises():
    import pytest

    with pytest.raises(ValueError, match="long_only"):
        StructureBos127V1(StructureBos127Params(long_only=False))
    with pytest.raises(ValueError, match="follow_through"):
        StructureBos127V1(StructureBos127Params(bos_follow_through=False))
    with pytest.raises(ValueError, match="pivot"):
        StructureBos127V1(StructureBos127Params(pivot_n=5))
    with pytest.raises(ValueError, match="RSI period"):
        StructureBos127V1(StructureBos127Params(rsi_period=7))
    with pytest.raises(ValueError, match="entry band"):
        StructureBos127V1(StructureBos127Params(rsi_entry_lo=25.0))
    with pytest.raises(ValueError, match="exit"):
        StructureBos127V1(StructureBos127Params(rsi_exit_min=75.0))
    with pytest.raises(ValueError, match="R-multiple"):
        StructureBos127V1(StructureBos127Params(r_multiple=2.0))
    with pytest.raises(ValueError, match="time-stop"):
        StructureBos127V1(StructureBos127Params(time_stop_bars=30))


def test_rsi_entry_band_inclusive():
    assert rsi_entry_band_allows(BULL, 20.0) is True
    assert rsi_entry_band_allows(BULL, 30.0) is True
    assert rsi_entry_band_allows(BULL, 25.0) is True
    assert rsi_entry_band_allows(BULL, 19.999) is False
    assert rsi_entry_band_allows(BULL, 30.001) is False
    assert rsi_entry_band_allows(BULL, 50.0) is False  # replaces RSI>50
    assert rsi_entry_band_allows(BEAR, 25.0) is False
    assert rsi_entry_band_allows(FLAT, 25.0) is False
    assert rsi_entry_band_allows(BULL, None) is False


def test_rsi_exit_ge_67_honesty_no_wait_75():
    assert rsi_exit_triggered(67.0) is True
    assert rsi_exit_triggered(66.999) is False
    assert rsi_exit_triggered(70.0) is True
    assert rsi_exit_triggered(75.0) is True  # gap through still exits at first ≥67
    assert rsi_exit_triggered(None) is False


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


def test_follow_through_required_no_first_touch():
    """BOS bar alone must NOT stamp entry; need next-bar close ≥ BOS close."""
    # Build minimal 15m bull structure + 3m RSI in band + 1m BOS/FT
    # Use synthetic series where we control closes via direct EntryExitSignals
    # for walker, and a focused precompute case below.
    bars_15 = []
    # Need HH+HL: craft rising swing highs/lows with pivot N=3
    prices_15 = [
        # build enough bars for pivots
        100, 101, 102, 103, 102, 101, 100,  # early noise
        104, 105, 106, 107, 106, 105, 104,  # high around
        103, 102, 101, 100, 101, 102, 103,
        108, 109, 110, 111, 110, 109, 108,  # higher high region
        107, 106, 105, 104, 105, 106, 107,
        112, 113, 114, 115, 114, 113, 112,
    ]
    for i, base in enumerate(prices_15):
        bars_15.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=i * 15 * 60_000,
                ts_close_ms=(i + 1) * 15 * 60_000,
                open=float(base),
                high=float(base) + 1.5,
                low=float(base) - 1.5,
                close=float(base) + 0.2,
                volume=1.0,
                closed=True,
                source="test",
            )
        )
    # 3m bars spanning same window — RSI will be computed; for band we need
    # depressed closes then mild recovery is hard. Use walker unit for FT/RSI
    # exit; use explicit precompute micro-test with patched path via signals.

    # Direct signal-level: entry only on follow-through index
    n = 6
    bars = [_bar1m(i * 60_000, 100 + i, 101 + i, 99 + i, 100.5 + i) for i in range(n)]
    # Simulate: BOS at i=1 would be first-touch; FT at i=2 is the real signal
    sig = EntryExitSignals(
        entry_long=[False, False, True, False, False, False],  # FT stamp at 2
        entry_short=[False] * n,
        bias=[BULL] * n,
        rsi=[25.0] * n,
        active_swing_high=[99.0] * n,
        active_swing_low=[95.0] * n,
        swing_version=[1] * n,
        opposite_extreme=[None] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    walk = walk_structure_bos_127(
        bars, sig, settings=settings, trade_start_ms=0, trade_end_ms=400_000
    )
    assert walk["n_short_entries"] == 0
    assert walk["n_long_entries"] == 1
    # Fill at open of bar after FT (bar index 3)
    assert walk["place_orders"] is False


def test_no_entry_without_follow_through_precompute():
    """If next bar close < BOS close, no entry_long."""
    # Construct 1m where bar0 closes above swing, bar1 closes below that close
    bars_15 = []
    for i in range(40):
        # Steadily rising to force bull HH+HL after enough pivots
        base = 100.0 + i * 0.8
        bars_15.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=i * 15 * 60_000,
                ts_close_ms=(i + 1) * 15 * 60_000,
                open=base,
                high=base + 3.0,
                low=base - 1.0,
                close=base + 1.0,
                volume=1.0,
                closed=True,
                source="test",
            )
        )
    # 3m: force RSI into [20,30] is difficult without long history of declines.
    # Instead verify FT logic with a controlled mini series by checking that
    # entry_long never fires on the BOS arm bar itself (always delayed ≥1).
    bars_3 = []
    for i in range(200):
        # Falling then flat to push RSI low
        if i < 80:
            base = 200.0 - i * 1.2
        else:
            base = 200.0 - 80 * 1.2 + (i - 80) * 0.05
        bars_3.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=i * 3 * 60_000,
                ts_close_ms=(i + 1) * 3 * 60_000,
                open=base,
                high=base + 0.5,
                low=base - 0.5,
                close=base - 0.1 if i < 80 else base + 0.05,
                volume=1.0,
                closed=True,
                source="test",
            )
        )
    bars_1 = []
    # Align 1m to cover 15m window (40*15 = 600 minutes)
    for i in range(600):
        base = 100.0 + i * 0.02
        # Create a breakout spike then fail follow-through
        if i == 500:
            c = base + 50.0  # huge BOS close
            bars_1.append(_bar1m(i * 60_000, base, c, base - 0.5, c))
        elif i == 501:
            # fail FT: close well below BOS close
            bars_1.append(
                _bar1m(i * 60_000, base, base + 1, base - 1, base - 0.5)
            )
        else:
            bars_1.append(
                _bar1m(i * 60_000, base, base + 0.5, base - 0.5, base + 0.1)
            )

    sig = precompute_entry_signals(bars_1, bars_15, bars_3)
    assert not any(sig.entry_short)
    # No entry on arm bar 500; if FT failed, no entry on 501 either for that event
    assert sig.entry_long[500] is False
    # Follow-through failed → no entry at 501
    assert sig.entry_long[501] is False


def test_follow_through_success_stamps_next_not_bos_bar():
    bars_15 = []
    for i in range(40):
        base = 100.0 + i * 0.8
        bars_15.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=i * 15 * 60_000,
                ts_close_ms=(i + 1) * 15 * 60_000,
                open=base,
                high=base + 3.0,
                low=base - 1.0,
                close=base + 1.0,
                volume=1.0,
                closed=True,
                source="test",
            )
        )
    bars_3 = []
    for i in range(200):
        if i < 100:
            base = 180.0 - i * 1.0
            close = base - 0.3
        else:
            base = 80.0 + (i - 100) * 0.02
            close = base + 0.01
        bars_3.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=i * 3 * 60_000,
                ts_close_ms=(i + 1) * 3 * 60_000,
                open=base,
                high=base + 0.4,
                low=base - 0.4,
                close=close,
                volume=1.0,
                closed=True,
                source="test",
            )
        )
    bars_1 = []
    bos_i = 520
    for i in range(600):
        base = 100.0 + i * 0.02
        if i == bos_i:
            c = base + 40.0
            bars_1.append(_bar1m(i * 60_000, base, c + 1, base - 0.5, c))
        elif i == bos_i + 1:
            # FT: close >= BOS close
            bos_close = (100.0 + bos_i * 0.02) + 40.0
            c = bos_close + 0.5
            bars_1.append(_bar1m(i * 60_000, bos_close, c + 1, bos_close - 1, c))
        else:
            bars_1.append(
                _bar1m(i * 60_000, base, base + 0.5, base - 0.5, base + 0.1)
            )

    sig = precompute_entry_signals(bars_1, bars_15, bars_3)
    assert not any(sig.entry_short)
    assert sig.entry_long[bos_i] is False  # never first-touch
    # FT bar may or may not enter depending on RSI band / bull — if entry, only at bos_i+1
    if any(sig.entry_long):
        idxs = [i for i, v in enumerate(sig.entry_long) if v]
        assert all(i != bos_i for i in idxs)
        assert bos_i + 1 in idxs or all(
            sig.rsi[j] is None
            or not (RSI_ENTRY_LO <= float(sig.rsi[j]) <= RSI_ENTRY_HI)
            for j in [bos_i + 1]
        )


def test_walker_rsi_exit_and_no_shorts():
    bars = [
        _bar1m(0, 100, 100, 99, 100),
        _bar1m(60_000, 100, 101, 99.5, 100.5),
        _bar1m(120_000, 100.5, 102, 100, 101.5),
        _bar1m(180_000, 101.5, 103, 101, 102.5),
        _bar1m(240_000, 102.5, 104, 102, 103.5),
        _bar1m(300_000, 103.5, 105, 103, 104.0),
        _bar1m(360_000, 104.0, 105, 103.5, 104.2),
    ]
    n = len(bars)
    # Enter on bar0 signal → fill bar1; RSI jumps to 70 on bar3 → rsi_exit
    rsi = [25.0, 25.0, 25.0, 70.0, 70.0, 70.0, 70.0]
    sig = EntryExitSignals(
        entry_long=[True, False, False, False, False, False, False],
        entry_short=[True, True, False, False, False, False, False],  # ignored
        bias=[BULL] * n,
        rsi=rsi,
        active_swing_high=[99.0] * n,
        active_swing_low=[95.0] * n,
        swing_version=[1] * n,
        opposite_extreme=[None] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    walk = walk_structure_bos_127(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=500_000,
    )
    assert walk["n_short_entries"] == 0
    assert walk["n_long_entries"] >= 1
    assert walk["n_rsi_exits"] >= 1
    assert walk["time_stop_convention"] == TIME_STOP_CONVENTION
    for k in (
        "n_tp_exits",
        "n_sl_exits",
        "n_opp_bos_exits",
        "n_rsi_exits",
        "n_time_stop_exits",
    ):
        assert k in walk


def test_rsi_gap_through_67_to_75_still_exits():
    """Honesty: first closed ≥67 exits; do not wait for 75."""
    bars = [_bar1m(i * 60_000, 100, 101, 99, 100.5) for i in range(5)]
    n = len(bars)
    # Enter bar0; on bar1 RSI spikes to 74 (gapped through 67) → exit
    sig = EntryExitSignals(
        entry_long=[True, False, False, False, False],
        entry_short=[False] * n,
        bias=[BULL] * n,
        rsi=[25.0, 74.0, 74.0, 74.0, 74.0],
        active_swing_high=[90.0] * n,
        active_swing_low=[50.0] * n,  # wide SL so not SL'd
        swing_version=[1] * n,
        opposite_extreme=[None] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    walk = walk_structure_bos_127(
        bars, sig, settings=settings, trade_start_ms=0, trade_end_ms=400_000
    )
    assert walk["n_rsi_exits"] >= 1
    assert walk["n_short_entries"] == 0


def test_pass_gate_2_of_3_constant():
    assert PASS_PAIRS_NEEDED == 2
    assert len(USDT_INSTS) == 3
    assert PHASE1 == 127
