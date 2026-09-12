"""Unit tests: phase1/125 structure + RSI + BOS locks and helpers."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_structure_bos_125 import (
    BAR_ENTRY,
    FETCH_END_EXCLUSIVE_ISO,
    ID_FAMILY,
    MEME_2020_NA,
    PASS_PAIRS_NEEDED,
    PHASE1,
    SCALP_S1_ID_FORBIDDEN,
    SLEEVE_EUR,
    SOURCE,
    TIME_STOP_CONVENTION,
    USD_UNAVAILABLE,
    USDT_INSTS,
    WARMUP_START_ISO,
    WINDOWS,
    candidate_id_for,
    walk_structure_bos,
)
from atlas.paper.types import Bar
from atlas.strategy.scalp_structure_bos_125 import (
    BEAR,
    BULL,
    FLAT,
    LONG,
    PIVOT_N,
    R_MULTIPLE,
    RSI_PERIOD,
    SHORT,
    TIME_STOP_BARS,
    EntryExitSignals,
    StructureBos125Params,
    StructureBos125V1,
    confirmed_swings,
    precompute_entry_signals,
    rsi_allows,
    structure_from_swings,
)


def test_phase_and_source_locked_125():
    assert PHASE1 == 125
    assert SOURCE == "public_md_scalp_structure_bos_125"
    assert "120" not in SOURCE
    assert BAR_ENTRY == "1m"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert PASS_PAIRS_NEEDED == 2
    assert TIME_STOP_BARS == 45
    assert R_MULTIPLE == 1.5
    assert PIVOT_N == 3
    assert RSI_PERIOD == 14
    assert "next_open" in TIME_STOP_CONVENTION


def test_usdt_insts_usd_and_meme_na():
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert USD_UNAVAILABLE == ("BTC-USD", "ETH-USD", "DOGE-USD")
    assert "PEPE-USDC" in MEME_2020_NA


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


def test_candidate_ids_and_no_s1_transplant():
    assert SCALP_S1_ID_FORBIDDEN.startswith("rise_panel_v1_scalp_doge_dual_thrust")
    for inst in USDT_INSTS:
        cid = candidate_id_for(inst)
        assert cid.startswith("public_md_v1_structure_bos_15m_rsi3m_1m_")
        assert cid.endswith("_eur20")
        assert cid != SCALP_S1_ID_FORBIDDEN
        assert "rise_panel" not in cid
        assert "#71" not in cid


def test_strategy_params_locked():
    s = StructureBos125V1(StructureBos125Params())
    assert s.params.pivot_n == PIVOT_N == 3
    assert s.params.rsi_period == RSI_PERIOD == 14
    assert float(s.params.r_multiple) == float(R_MULTIPLE) == 1.5
    assert int(s.params.time_stop_bars) == TIME_STOP_BARS == 45
    assert s.params.confirm_closed_only is True
    assert s.params.bar_structure == "15m"
    assert s.params.bar_rsi == "3m"
    assert s.params.bar_entry == "1m"


def test_pivot_confirm_and_hh_hl_vs_lh_ll():
    # Build 15m-like bars with clear pivots. N=3 needs 7 bars around pivot.
    # Construct: swing low at i=3, swing high at i=10, higher low at i=17, higher high at i=24
    def mk(ts: int, h: float, l: float, c: float) -> Bar:
        return Bar(
            symbol="BTC-USDT",
            ts_open_ms=ts,
            ts_close_ms=ts + 15 * 60_000,
            open=c,
            high=h,
            low=l,
            close=c,
            volume=1.0,
            closed=True,
            source="test",
        )

    bars: list[Bar] = []
    # flat-ish lead-in then a clear low (HL pattern building)
    prices = [
        # 0..2 left of first low
        (10, 9, 9.5),
        (10, 9, 9.5),
        (10, 9, 9.5),
        # 3 swing low
        (9.2, 8.0, 8.5),
        # 4..6 right of low
        (9.5, 8.5, 9.0),
        (9.8, 8.8, 9.2),
        (10.0, 9.0, 9.5),
        # 7..9 left of high
        (10.5, 9.5, 10.0),
        (11.0, 10.0, 10.5),
        (11.5, 10.5, 11.0),
        # 10 swing high
        (12.5, 11.0, 12.0),
        # 11..13 right
        (12.0, 10.8, 11.5),
        (11.5, 10.5, 11.0),
        (11.0, 10.2, 10.6),
        # 14..16 left of higher low
        (10.8, 10.0, 10.4),
        (10.6, 9.9, 10.2),
        (10.5, 9.8, 10.1),
        # 17 higher low (>8.0)
        (10.2, 9.0, 9.5),
        # 18..20 right
        (10.4, 9.2, 9.8),
        (10.6, 9.4, 10.0),
        (10.8, 9.6, 10.2),
        # 21..23 left of higher high
        (11.2, 10.0, 10.8),
        (11.8, 10.5, 11.2),
        (12.2, 11.0, 11.8),
        # 24 higher high (>12.5)
        (13.5, 12.0, 13.0),
        # 25..27 right confirm
        (13.0, 11.8, 12.5),
        (12.5, 11.5, 12.0),
        (12.2, 11.2, 11.8),
    ]
    for i, (h, l, c) in enumerate(prices):
        bars.append(mk(i * 15 * 60_000, h, l, c))

    swings = confirmed_swings(bars, pivot_n=3)
    assert any(s.kind == "low" for s in swings)
    assert any(s.kind == "high" for s in swings)
    # After last bar confirmed, expect bull HH+HL if we have 2h+2l
    st = structure_from_swings(swings, asof_confirm_index=len(bars) - 1)
    assert st.n_confirmed_highs >= 2
    assert st.n_confirmed_lows >= 2
    assert st.bias == BULL
    assert st.last_swing_high is not None and st.prior_swing_high is not None
    assert st.last_swing_high > st.prior_swing_high
    assert st.last_swing_low is not None and st.prior_swing_low is not None
    assert st.last_swing_low > st.prior_swing_low

    # Bear: reverse the construction briefly via structure_from_swings with LH+LL
    # Build synthetic SwingPoints
    from atlas.strategy.scalp_structure_bos_125 import SwingPoint

    bear_swings = [
        SwingPoint("high", 0, 3, 12.0, 0),
        SwingPoint("low", 1, 4, 10.0, 1),
        SwingPoint("high", 2, 5, 11.0, 2),  # LH
        SwingPoint("low", 3, 6, 9.0, 3),  # LL
    ]
    st_b = structure_from_swings(bear_swings, asof_confirm_index=6)
    assert st_b.bias == BEAR

    # Mixed: HH + LL
    mixed = [
        SwingPoint("high", 0, 3, 10.0, 0),
        SwingPoint("low", 1, 4, 8.0, 1),
        SwingPoint("high", 2, 5, 11.0, 2),  # HH
        SwingPoint("low", 3, 6, 7.0, 3),  # LL
    ]
    assert structure_from_swings(mixed, asof_confirm_index=6).bias == FLAT


def test_rsi_gate():
    assert rsi_allows(BULL, 51.0) == (True, False)
    assert rsi_allows(BULL, 50.0) == (False, False)
    assert rsi_allows(BULL, 49.0) == (False, False)
    assert rsi_allows(BEAR, 49.0) == (False, True)
    assert rsi_allows(BEAR, 50.0) == (False, False)
    assert rsi_allows(FLAT, 80.0) == (False, False)
    assert rsi_allows(BULL, None) == (False, False)


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


def test_one_entry_per_bos_and_walker_exits():
    # Minimal synthetic: 5 bars; force entry long on bar0 via signals
    bars = [
        _bar1m(0, 100, 100, 99, 100),
        _bar1m(60_000, 100, 101, 99.5, 100.5),
        _bar1m(120_000, 100.5, 110, 100, 109),  # TP path
        _bar1m(180_000, 109, 109, 108, 108.5),  # exit fill
        _bar1m(240_000, 108.5, 109, 108, 108.8),
    ]
    n = len(bars)
    sig = EntryExitSignals(
        entry_long=[True, False, False, False, False],
        entry_short=[False] * n,
        bias=[BULL] * n,
        rsi=[60.0] * n,
        active_swing_high=[99.0] * n,
        active_swing_low=[95.0] * n,  # SL; R=entry-95; 1.5R TP
        swing_version=[1] * n,
        opposite_extreme=[None] * n,
    )
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
    assert walk["n_long_entries"] >= 1
    assert walk["n_trades"] >= 1
    assert walk.get("place_orders") is False
    assert walk["time_stop_convention"] == TIME_STOP_CONVENTION

    # One-entry-per-BOS: same swing_version should only fire once in precompute
    # Build tiny multi-TF: rising 15m for structure + 3m for RSI + 1m BOS
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
    # Make a few distinct swings by dipping/spiking
    # (precompute may yield 0 entries on this smooth series — just length-check)
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
    sig2 = precompute_entry_signals(bars_1, bars_15, bars_3)
    assert len(sig2.entry_long) == len(bars_1)
    assert len(sig2.entry_short) == len(bars_1)
    # If multiple longs fire, swing_version at those indices must be unique
    long_idxs = [i for i, v in enumerate(sig2.entry_long) if v]
    vers = [sig2.swing_version[i] for i in long_idxs]
    assert len(vers) == len(set(vers))


def test_pass_gate_2_of_3_constant():
    assert PASS_PAIRS_NEEDED == 2
    assert len(USDT_INSTS) == 3
    assert ID_FAMILY.endswith("_long_short")


def test_no_grind_raises():
    import pytest

    with pytest.raises(ValueError, match="pivot"):
        StructureBos125V1(StructureBos125Params(pivot_n=5))
    with pytest.raises(ValueError, match="RSI"):
        StructureBos125V1(StructureBos125Params(rsi_period=7))
    with pytest.raises(ValueError, match="R-multiple"):
        StructureBos125V1(StructureBos125Params(r_multiple=2.0))
    with pytest.raises(ValueError, match="time-stop"):
        StructureBos125V1(StructureBos125Params(time_stop_bars=30))
