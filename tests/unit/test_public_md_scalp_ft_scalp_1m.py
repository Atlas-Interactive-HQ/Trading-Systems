"""Unit tests: phase1/123 public-MD Scalp freqtrade Scalp.py 1m lock constants."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_ft_scalp_1m import (
    BAR,
    FETCH_END_EXCLUSIVE_ISO,
    ID_FAMILY,
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
    walk_long_flat_roi_sl,
)
from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.ft_scalp_1m import (
    ADX_GATE,
    EMA_PERIOD,
    ROI_FRAC,
    SL_FRAC,
    SOURCE_LICENSE,
    SOURCE_URL,
    STOCH_FASTD,
    STOCH_FASTK,
    FtScalp1mParams,
    FtScalp1mV1,
    crossed_above,
    precompute_entry_exit_signals,
    stochf_series,
)


def test_phase_and_source_locked_123_not_120_121_122():
    assert PHASE1 == 123
    assert SOURCE == "public_md_scalp_ft_scalp_1m_123"
    assert "120" not in SOURCE
    assert "121" not in SOURCE
    assert "122" not in SOURCE
    assert BAR == "1m"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert ROI_FRAC == 0.01
    assert SL_FRAC == 0.04


def test_native_1m_not_1h():
    assert BAR == "1m"
    s = FtScalp1mV1()
    assert s.params.bar == "1m"
    assert ID_FAMILY.endswith("_1m_long_flat")
    assert "1h" not in ID_FAMILY.lower()


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
    assert SCALP_S1_ID_FORBIDDEN == (
        "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
    )
    for inst in USDT_INSTS:
        cid = candidate_id_for(inst)
        assert cid.startswith("public_md_v1_ft_berlinguyinca_scalp_1m_")
        assert cid.endswith("_eur20")
        assert cid != SCALP_S1_ID_FORBIDDEN
        assert "rise_panel" not in cid
        assert "#71" not in cid
        assert inst.lower().replace("-", "_") in cid


def test_gpl_citation_present():
    assert "GPL-3.0" == SOURCE_LICENSE or SOURCE_LICENSE == "GPL-3.0"
    assert "berlinguyinca/Scalp.py" in SOURCE_URL
    assert "freqtrade-strategies" in SOURCE_URL


def test_strategy_params_locked():
    s = FtScalp1mV1(FtScalp1mParams())
    assert s.params.ema_period == EMA_PERIOD == 5
    assert s.params.stoch_fastk == STOCH_FASTK == 5
    assert s.params.stoch_fastd == STOCH_FASTD == 3
    assert float(s.params.adx_gate) == float(ADX_GATE) == 30.0
    assert s.params.confirm_closed_only is True
    assert LONG == "long"
    assert FLAT == "flat"


def test_stochf_and_cross_helpers():
    highs = [10.0, 11.0, 12.0, 11.5, 13.0, 14.0, 13.5, 15.0]
    lows = [9.0, 9.5, 10.0, 10.5, 11.0, 12.0, 12.5, 13.0]
    closes = [9.5, 10.5, 11.0, 11.0, 12.5, 13.0, 13.0, 14.5]
    fk, fd = stochf_series(highs, lows, closes, fastk_period=5, fastd_period=3)
    assert len(fk) == len(closes)
    assert fk[4] is not None
    assert fd[6] is not None
    assert crossed_above(31.0, 29.0, 30.0, 30.0) is True
    assert crossed_above(29.0, 28.0, 30.0, 30.0) is False


def _bar(ts: int, o: float, h: float, l: float, c: float) -> Bar:
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


def test_walk_roi_sl_and_signals():
    # Synthetic: enter bar0 signal → fill bar1 open=100; ROI at close 102 on bar2
    bars = [
        _bar(0, 100, 100, 99, 100),
        _bar(60_000, 100, 101, 99.5, 100.5),
        _bar(120_000, 100.5, 103, 100, 102),  # close +2% → ROI
        _bar(180_000, 102, 102, 101, 101.5),  # exit fill
        _bar(240_000, 101.5, 102, 101, 101.8),
    ]
    entry = [True, False, False, False, False]
    exit_ = [False, False, False, False, False]
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    walk = walk_long_flat_roi_sl(
        bars,
        entry_sig=entry,
        exit_sig=exit_,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=300_000,
        roi_frac=0.01,
        sl_frac=0.04,
    )
    assert walk["n_entries"] >= 1
    assert walk["n_roi_exits"] >= 1
    assert walk["n_trades"] >= 1
    assert walk.get("place_orders") is False


def test_precompute_signals_length_matches_bars():
    bars = [_bar(i * 60_000, 100 + i * 0.01, 101, 99, 100.5) for i in range(40)]
    entry, exit_ = precompute_entry_exit_signals(bars)
    assert len(entry) == len(bars) == len(exit_)
