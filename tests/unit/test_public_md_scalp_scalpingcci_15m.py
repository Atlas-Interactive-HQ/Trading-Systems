"""Unit tests: phase1/124 public-MD Scalp guibvieira ScalpingCCI 15m lock constants."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_scalpingcci_15m import (
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
    walk_long_flat_roi_ladder_sl,
)
from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.scalping_cci_15m import (
    DAILY_FACTOR,
    EMA_PERIOD,
    HIGH_DAILY_EXIT_FRAC,
    ROI_LADDER,
    SHIFT_BARS,
    SL_FRAC,
    SOURCE_LICENSE,
    SOURCE_URL,
    ScalpingCci15mParams,
    ScalpingCci15mV1,
    causal_daily_levels,
    crossed_above,
    crossed_below,
    precompute_entry_exit_signals,
    roi_threshold_for_minutes,
)


def test_phase_and_source_locked_124_not_prior():
    assert PHASE1 == 124
    assert SOURCE == "public_md_scalp_scalpingcci_15m_124"
    for forbidden in ("120", "121", "122", "123"):
        assert forbidden not in SOURCE.split("_")[-1] or SOURCE.endswith("124")
    assert "120" not in SOURCE
    assert "121" not in SOURCE
    assert "122" not in SOURCE
    assert "123" not in SOURCE
    assert BAR == "15m"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert SL_FRAC == 0.04
    assert ROI_LADDER == (
        (0, 0.02),
        (10, 0.05),
        (20, 0.04),
        (60, 0.3),
        (120, 0.2),
    )


def test_native_15m_not_1h():
    assert BAR == "15m"
    s = ScalpingCci15mV1()
    assert s.params.bar == "15m"
    assert ID_FAMILY.endswith("_15m_long_flat")
    assert "1h" not in ID_FAMILY.lower()
    assert "1m" not in ID_FAMILY.lower()


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
        assert cid.startswith("public_md_v1_guibvieira_scalping_cci_15m_")
        assert cid.endswith("_eur20")
        assert cid != SCALP_S1_ID_FORBIDDEN
        assert "rise_panel" not in cid
        assert "#71" not in cid
        assert inst.lower().replace("-", "_") in cid


def test_gpl_citation_present():
    assert SOURCE_LICENSE == "GPL-3.0"
    assert "ScalpingCCI.py" in SOURCE_URL
    assert "guibvieira" in SOURCE_URL


def test_strategy_params_locked():
    s = ScalpingCci15mV1(ScalpingCci15mParams())
    assert s.params.ema_period == EMA_PERIOD == 20
    assert s.params.daily_factor == DAILY_FACTOR == 96
    assert s.params.shift_bars == SHIFT_BARS == 97
    assert float(s.params.high_daily_exit_frac) == float(HIGH_DAILY_EXIT_FRAC) == 0.98
    assert s.params.confirm_closed_only is True
    assert LONG == "long"
    assert FLAT == "flat"


def test_roi_ladder_lookup():
    assert roi_threshold_for_minutes(0) == 0.02
    assert roi_threshold_for_minutes(9) == 0.02
    assert roi_threshold_for_minutes(10) == 0.05
    assert roi_threshold_for_minutes(20) == 0.04
    assert roi_threshold_for_minutes(60) == 0.3
    assert roi_threshold_for_minutes(120) == 0.2
    assert roi_threshold_for_minutes(999) == 0.2


def test_cross_helpers_and_tc_formula():
    assert crossed_above(1.0, -1.0, 0.0, 0.0) is True
    assert crossed_below(-1.0, 1.0, 0.0, 0.0) is True
    # Synthetic day: high=10, low=8, close=9 → pivot=9, bc=9, tc=(9-9)/2=0
    bars = [
        Bar(
            symbol="BTC-USDT",
            ts_open_ms=1_593_561_600_000 + i * 900_000,
            ts_close_ms=1_593_561_600_000 + (i + 1) * 900_000,
            open=9.0,
            high=10.0,
            low=8.0,
            close=9.0,
            volume=1.0,
            closed=True,
            source="test",
        )
        for i in range(3)
    ]
    levels = causal_daily_levels(bars)
    assert levels["pivot"][0] == 9.0
    assert levels["bc"][0] == 9.0
    assert levels["tc"][0] == 0.0  # FILE: (pivot-bc)/2


def _bar(ts: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(
        symbol="BTC-USDT",
        ts_open_ms=ts,
        ts_close_ms=ts + 900_000,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=1.0,
        closed=True,
        source="test",
    )


def test_walk_roi_ladder_and_signals():
    # On 15m bars first close after fill is already ≥15m held → ROI rung 0.05 (FILE).
    bars = [
        _bar(0, 100, 100, 99, 100),
        _bar(900_000, 100, 101, 99.5, 100.5),  # fill open≈100 (+slip)
        _bar(1_800_000, 100.5, 107, 100, 105.5),  # +5.5% → hits 0.05 ROI rung
        _bar(2_700_000, 105.5, 106, 105, 105.2),
        _bar(3_600_000, 105.2, 106, 105, 105.5),
    ]
    entry = [True, False, False, False, False]
    exit_ = [False, False, False, False, False]
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    walk = walk_long_flat_roi_ladder_sl(
        bars,
        entry_sig=entry,
        exit_sig=exit_,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=5_000_000,
        sl_frac=0.04,
    )
    assert walk["n_entries"] >= 1
    assert walk["n_roi_exits"] >= 1
    assert walk["n_trades"] >= 1
    assert walk.get("place_orders") is False


def test_precompute_signals_length_matches_bars():
    bars = [
        _bar(1_593_561_600_000 + i * 900_000, 100 + i * 0.01, 101, 99, 100.5)
        for i in range(120)
    ]
    entry, exit_ = precompute_entry_exit_signals(bars)
    assert len(entry) == len(bars) == len(exit_)
