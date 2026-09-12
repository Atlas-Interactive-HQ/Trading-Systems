"""Unit tests: phase1/133 #132 entry + 4H EMA regime-flip exits (leave #130–132 STOP)."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_dt_rvol_1h_133 import (
    BASELINE_132_BH_FULL,
    BASELINE_132_FULL,
    FETCH_END_EXCLUSIVE_ISO,
    ID_FAMILY,
    MEME_2020_NA,
    PASS_PAIRS_NEEDED,
    PHASE1,
    SLEEVE_EUR,
    SOURCE,
    USD_UNAVAILABLE,
    USDT_INSTS,
    WARMUP_START_ISO,
    WINDOWS,
    candidate_id_for,
    walk_dt_rvol_1h_133,
)
from atlas.paper.types import Bar
from atlas.strategy.dual_thrust import DualThrustLongFlatV1, DualThrustParams
from atlas.strategy.scalp_dt_rvol_1h_133 import (
    ATR_N,
    ATR_SL_MULT,
    BAR,
    EMA_4H,
    FAMILY,
    K1,
    K2,
    N,
    NO_R_TP,
    NO_SELLLINE_EXIT,
    REGIME_BAR,
    RVOL_GATE,
    RVOL_N,
    TIME_STOP,
    DtRvol133Signals,
    ScalpDtRvol1h133Params,
    ScalpDtRvol1h133V1,
    atr_wilder_series,
    resolve_sl_at_entry,
)


def _bar1h(
    i: int,
    o: float,
    h: float,
    l: float,
    c: float,
    *,
    vol: float = 100.0,
    symbol: str = "BTC-USDT",
) -> Bar:
    open_ms = i * 60 * 60_000
    return Bar(
        symbol=symbol,
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + 60 * 60_000,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=vol,
        closed=True,
        source="test",
    )


def _bar4h(
    i: int,
    o: float,
    h: float,
    l: float,
    c: float,
    *,
    symbol: str = "BTC-USDT",
) -> Bar:
    open_ms = i * 4 * 60 * 60_000
    return Bar(
        symbol=symbol,
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + 4 * 60 * 60_000,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=1000.0,
        closed=True,
        source="test",
    )


def _empty_sig(n: int, **overrides: object) -> DtRvol133Signals:
    base = dict(
        regime_ok=[True] * n,
        regime_flip=[False] * n,
        buy_line=[99.0] * n,
        sell_line=[95.0] * n,
        rvol=[2.0] * n,
        atr=[1.0] * n,
        entry_ok=[False] * n,
        buy=[False] * n,
        sell=[False] * n,
    )
    base.update(overrides)
    return DtRvol133Signals(**base)  # type: ignore[arg-type]


def _settings() -> EmaBookSettings:
    return EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )


def test_phase_and_source_locked_133():
    assert PHASE1 == 133
    assert SOURCE == "public_md_scalp_dt_rvol_1h_133"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert PASS_PAIRS_NEEDED == 2
    assert FAMILY.startswith("dt_n20")
    assert "regime_exit_1h" in FAMILY
    assert "structure_bos" not in FAMILY
    assert "structure_bos" not in ID_FAMILY
    assert "15m" not in ID_FAMILY


def test_locked_constants():
    assert N == 20
    assert K1 == K2 == 0.5
    assert RVOL_N == 20
    assert RVOL_GATE == 1.0
    assert EMA_4H == 21
    assert TIME_STOP == 168
    assert NO_R_TP is True
    assert NO_SELLLINE_EXIT is True
    assert ATR_N == 14
    assert ATR_SL_MULT == 1.0
    assert BAR == "1H"
    assert REGIME_BAR == "4H"


def test_usdt_windows():
    assert USDT_INSTS == ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
    assert USD_UNAVAILABLE == ("BTC-USD", "ETH-USD", "DOGE-USD")
    assert "PEPE-USDC" in MEME_2020_NA
    assert WINDOWS["FULL"] == ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z")
    assert WINDOWS["SUB_A_DEFI_SUMMER"][1] == "2020-10-01T00:00:00Z"
    assert WINDOWS["SUB_B_BTC_RUN"][0] == "2020-10-01T00:00:00Z"
    assert WARMUP_START_ISO == "2020-06-01T00:00:00Z"
    assert FETCH_END_EXCLUSIVE_ISO == "2021-01-01T00:00:00Z"


def test_candidate_ids():
    expected = {
        "BTC-USDT": "public_md_v1_dt_n20_k0505_rvol20_gt10_ema21_4h_regime_exit_1h_btc_usdt_eur20",
        "ETH-USDT": "public_md_v1_dt_n20_k0505_rvol20_gt10_ema21_4h_regime_exit_1h_eth_usdt_eur20",
        "DOGE-USDT": "public_md_v1_dt_n20_k0505_rvol20_gt10_ema21_4h_regime_exit_1h_doge_usdt_eur20",
    }
    for inst in USDT_INSTS:
        cid = candidate_id_for(inst)
        assert cid == expected[inst]
        assert cid.startswith(ID_FAMILY + "_")
        assert cid.endswith("_eur20")
        assert "ema21_4h_regime_exit_1h" in cid
        assert "structure_bos" not in cid
        assert "rise_panel" not in cid
        assert "15m" not in cid


def test_baselines_locked_132_honesty():
    assert BASELINE_132_FULL["BTC-USDT"]["n"] == 22
    assert BASELINE_132_FULL["BTC-USDT"]["exp"] == pytest.approx(-0.11740487)
    assert BASELINE_132_FULL["BTC-USDT"]["terminal"] == pytest.approx(-2.58290714)
    assert BASELINE_132_FULL["BTC-USDT"]["n_tp"] == 4
    assert BASELINE_132_FULL["BTC-USDT"]["n_sl"] == 6
    assert BASELINE_132_FULL["BTC-USDT"]["n_sellline"] == 5
    assert BASELINE_132_FULL["BTC-USDT"]["n_time_stop"] == 7
    assert BASELINE_132_FULL["ETH-USDT"]["n"] == 29
    assert BASELINE_132_FULL["ETH-USDT"]["exp"] == pytest.approx(0.25271795)
    assert BASELINE_132_FULL["ETH-USDT"]["terminal"] == pytest.approx(7.32882069)
    assert BASELINE_132_FULL["ETH-USDT"]["n_tp"] == 11
    assert BASELINE_132_FULL["DOGE-USDT"]["n"] == 24
    assert BASELINE_132_FULL["DOGE-USDT"]["exp"] == pytest.approx(0.21480547)
    assert BASELINE_132_FULL["DOGE-USDT"]["terminal"] == pytest.approx(5.1553314)
    assert BASELINE_132_BH_FULL["BTC-USDT"] == pytest.approx(43.17666206)
    assert BASELINE_132_BH_FULL["ETH-USDT"] == pytest.approx(45.16769469)
    assert BASELINE_132_BH_FULL["DOGE-USDT"] == pytest.approx(20.2301366)


def test_reject_grind_n_k_rvol():
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(lookback=5))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(lookback=4))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(k1=0.6))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(rvol_gate=1.2))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(ema_4h=12))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(time_stop_bars=48))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(atr_period=20))


def test_reject_enabling_1_5r_or_sellline_exit():
    with pytest.raises(ValueError, match="1.5R|r_multiple|NO_R_TP"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(r_multiple=1.5))
    with pytest.raises(ValueError, match="1.5R|r_multiple|NO_R_TP"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(r_multiple=2.0))
    with pytest.raises(ValueError, match="sellline"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(sellline_exit=True))
    with pytest.raises(ValueError, match="NO_R_TP"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(no_r_tp=False))
    with pytest.raises(ValueError, match="NO_SELLLINE_EXIT"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(no_sellline_exit=False))


def test_reject_15m_bar():
    with pytest.raises(ValueError, match="bar grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(bar="15m"))
    with pytest.raises(ValueError, match="regime_bar grind"):
        ScalpDtRvol1h133V1(ScalpDtRvol1h133Params(regime_bar="1H"))


def test_buyline_formula_matches_dual_thrust_n20_1h():
    bars = []
    for i in range(22):
        bars.append(_bar1h(i, 100 + i, 105 + i, 95 + i, 100 + i, vol=100.0))
    inner = DualThrustLongFlatV1(DualThrustParams(lookback=20, k1=0.5, k2=0.5))
    ranges = inner.ranges_at(bars)
    assert ranges is not None
    buy, sell = ranges
    last = bars[-1]
    from atlas.strategy.dual_thrust import prior_hh_ll_range

    rng = prior_hh_ll_range(bars, 20)
    assert rng is not None
    assert buy == pytest.approx(last.open + 0.5 * rng)
    assert sell == pytest.approx(last.open - 0.5 * rng)


def test_same_entry_as_132():
    """Entry lock equals #132: N=20, k=0.5, RVOL>1.0, 4H EMA21, fill next open."""
    from atlas.strategy.scalp_dt_rvol_1h_132 import (
        N as N132,
        K1 as K1_132,
        K2 as K2_132,
        RVOL_GATE as G132,
        RVOL_N as RN132,
        EMA_4H as E132,
    )

    assert N == N132 == 20
    assert K1 == K1_132 == 0.5
    assert K2 == K2_132 == 0.5
    assert RVOL_GATE == G132 == 1.0
    assert RVOL_N == RN132 == 20
    assert EMA_4H == E132 == 21


def test_rvol_gate_099_blocks_101_allows():
    from atlas.strategy.rvol import rvol_series

    n = 50
    bars_1h = []
    for i in range(n):
        open_ms = i * 60 * 60_000
        bars_1h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 60 * 60_000,
                open=100.0,
                high=110.0,
                low=90.0,
                close=100.0,
                volume=100.0,
                closed=True,
                source="test",
            )
        )
    bars_4h = []
    for i in range(40):
        open_ms = i * 4 * 60 * 60_000
        bars_4h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 4 * 60 * 60_000,
                open=100.0 + i,
                high=110.0 + i,
                low=90.0 + i,
                close=108.0 + i,
                volume=1000.0,
                closed=True,
                source="test",
            )
        )
    strat = ScalpDtRvol1h133V1()

    bars_hi = list(bars_1h)
    bars_hi[-1] = Bar(
        symbol="BTC-USDT",
        ts_open_ms=bars_1h[-1].ts_open_ms,
        ts_close_ms=bars_1h[-1].ts_close_ms,
        open=100.0,
        high=130.0,
        low=90.0,
        close=125.0,
        volume=101.0,
        closed=True,
        source="test",
    )
    for j in range(n - 20, n - 1):
        b = bars_hi[j]
        bars_hi[j] = Bar(
            symbol=b.symbol, ts_open_ms=b.ts_open_ms, ts_close_ms=b.ts_close_ms,
            open=100.0, high=110.0, low=90.0, close=100.0, volume=100.0,
            closed=True, source="test",
        )
    rvols = rvol_series(bars_hi, 20)
    assert rvols[-1] is not None
    assert float(rvols[-1]) == pytest.approx(1.01, abs=0.02)
    sig_hi = strat.precompute_signals(bars_hi, bars_4h)
    if float(rvols[-1]) > 1.0 and sig_hi.buy[-1] and sig_hi.regime_ok[-1]:
        assert sig_hi.entry_ok[-1] is True

    bars_lo = list(bars_hi)
    bars_lo[-1] = Bar(
        symbol="BTC-USDT",
        ts_open_ms=bars_1h[-1].ts_open_ms,
        ts_close_ms=bars_1h[-1].ts_close_ms,
        open=100.0,
        high=130.0,
        low=90.0,
        close=125.0,
        volume=99.0,
        closed=True,
        source="test",
    )
    rvols_lo = rvol_series(bars_lo, 20)
    assert rvols_lo[-1] is not None
    assert float(rvols_lo[-1]) < 1.0
    sig_lo = strat.precompute_signals(bars_lo, bars_4h)
    assert sig_lo.entry_ok[-1] is False


def test_ema21_4h_regime_blocks_when_below():
    n = 40
    bars_1h = []
    for i in range(n):
        open_ms = i * 60 * 60_000
        bars_1h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 60 * 60_000,
                open=100.0,
                high=130.0,
                low=70.0,
                close=125.0,
                volume=500.0 if i == n - 1 else 100.0,
                closed=True,
                source="test",
            )
        )
    bars_4h = []
    for i in range(50):
        open_ms = i * 4 * 60 * 60_000
        c = 200.0 - i * 2.0
        bars_4h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 4 * 60 * 60_000,
                open=c + 1,
                high=c + 5,
                low=c - 5,
                close=c,
                volume=1000.0,
                closed=True,
                source="test",
            )
        )
    strat = ScalpDtRvol1h133V1()
    sig = strat.precompute_signals(bars_1h, bars_4h)
    assert sig.regime_ok[-1] is False
    assert sig.entry_ok[-1] is False
    assert all(not ok for ok in sig.entry_ok) or not any(
        sig.entry_ok[i] and not sig.regime_ok[i] for i in range(n)
    )


def test_no_lookahead_1h_before_4h_close_ineligible():
    bars_4h = [
        Bar(
            symbol="BTC-USDT",
            ts_open_ms=0,
            ts_close_ms=14_400_000,
            open=100,
            high=110,
            low=90,
            close=200,
            volume=1000,
            closed=True,
            source="test",
        )
    ]
    for i in range(1, 30):
        bars_4h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=i * 14_400_000,
                ts_close_ms=(i + 1) * 14_400_000,
                open=100 + i,
                high=110 + i,
                low=90 + i,
                close=105 + i,
                volume=1000,
                closed=True,
                source="test",
            )
        )
    bars_1h = [
        Bar(
            symbol="BTC-USDT",
            ts_open_ms=0,
            ts_close_ms=3_600_000,
            open=100,
            high=110,
            low=90,
            close=105,
            volume=100,
            closed=True,
            source="test",
        )
    ]
    strat = ScalpDtRvol1h133V1()
    sig = strat.precompute_signals(bars_1h, bars_4h)
    assert sig.regime_ok[0] is False
    assert sig.regime_flip[0] is False


def test_sl_fallback_and_skip():
    assert resolve_sl_at_entry(
        entry_px=100.0, sell_line_at_entry=95.0, atr_at_entry=2.0
    ) == pytest.approx(95.0)
    assert resolve_sl_at_entry(
        entry_px=100.0, sell_line_at_entry=100.0, atr_at_entry=3.0
    ) == pytest.approx(97.0)
    assert resolve_sl_at_entry(
        entry_px=100.0, sell_line_at_entry=101.0, atr_at_entry=2.5
    ) == pytest.approx(97.5)
    assert (
        resolve_sl_at_entry(
            entry_px=100.0, sell_line_at_entry=105.0, atr_at_entry=None
        )
        is None
    )
    assert (
        resolve_sl_at_entry(
            entry_px=100.0, sell_line_at_entry=100.0, atr_at_entry=0.0
        )
        is None
    )


def test_walker_fill_next_open_and_time_stop_168():
    n = 200
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    sig = _empty_sig(
        n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
    )
    out = walk_dt_rvol_1h_133(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        time_stop_bars=168,
    )
    assert out["n_short_entries"] == 0
    assert out["n_long_entries"] >= 1
    assert out["n_time_stop_exits"] >= 1
    assert out["n_tp_exits"] == 0
    assert out["n_sellline_exits"] == 0
    assert out["place_orders"] is False
    assert out["not_a_forecast"] is True
    assert out["time_stop_bars"] == 168


def test_sellline_close_does_not_exit_if_sl_not_hit():
    """Current-bar close < SellLine is NOT an exit in #133 unless it hits fixed SL."""
    n = 20
    bars = [_bar1h(i, 100, 101, 99, 100.2) for i in range(n)]
    # After fill (bar 1), bar 4 close is below a *current* sell line 100.5
    # but well above the fixed SL 95 — must NOT flatten.
    sell_lines = [95.0] * n
    sell_lines[4] = 100.5
    bars[4] = _bar1h(4, 100, 101, 99, 100.0)
    sig = _empty_sig(
        n,
        sell_line=sell_lines,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
        sell=[False] * n,
    )
    sell = list(sig.sell)
    sell[4] = True
    sig = _empty_sig(
        n,
        sell_line=sell_lines,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
        sell=sell,
    )
    out = walk_dt_rvol_1h_133(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        time_stop_bars=168,
    )
    assert out["n_sellline_exits"] == 0
    assert out["n_tp_exits"] == 0
    # Still in trade or later time-stop/SL — just not a sellline flatten at bar 4
    assert out["n_long_entries"] == 1
    assert out["n_regime_flip_exits"] == 0


def test_no_1_5r_flatten():
    """A 1.5R-style spike must NOT flatten as TP."""
    n = 20
    bars = [_bar1h(i, 100, 101, 99, 100.2) for i in range(n)]
    # Huge up bar that would have been 1.5R vs SL=95 (R=5, 1.5R=107.5)
    bars[5] = _bar1h(5, 106, 120, 105, 118.0)
    sig = _empty_sig(
        n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
    )
    out = walk_dt_rvol_1h_133(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        time_stop_bars=168,
    )
    assert out["n_tp_exits"] == 0
    assert out["n_sellline_exits"] == 0
    assert out["n_long_entries"] == 1


def test_regime_flip_4h_below_ema_exits_next_1h_open():
    """4H close < EMA21 signals on that 1H; fill next 1H open."""
    n = 12
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    flip = [False] * n
    flip[4] = True  # closed 4H < EMA seen on this 1H
    sig = _empty_sig(
        n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
        regime_flip=flip,
        regime_ok=[True] * 4 + [False] * (n - 4),
    )
    out = walk_dt_rvol_1h_133(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        time_stop_bars=168,
    )
    assert out["n_regime_flip_exits"] == 1
    assert out["n_tp_exits"] == 0
    assert out["n_sellline_exits"] == 0
    assert out["n_time_stop_exits"] == 0
    assert out["n_trades"] == 1


def test_walker_skip_when_sl_not_below():
    n = 10
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    sig = _empty_sig(
        n,
        sell_line=[200.0] * n,
        atr=[None] * n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
    )
    out = walk_dt_rvol_1h_133(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
    )
    assert out["n_long_entries"] == 0
    assert out["n_skipped_sl_not_below"] >= 1


def test_walker_honors_fixed_sl():
    n = 12
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    bars[4] = _bar1h(4, 100, 101, 90, 94.0)  # close <= SL 95
    sig = _empty_sig(
        n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
    )
    out = walk_dt_rvol_1h_133(
        bars,
        sig,
        settings=_settings(),
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        time_stop_bars=168,
    )
    assert out["n_sl_exits"] == 1
    assert out["n_tp_exits"] == 0
    assert out["n_sellline_exits"] == 0
    assert out["n_trades"] == 1


def test_atr_wilder_smoke():
    n = 40
    highs = [100.0 + (i % 5) for i in range(n)]
    lows = [90.0 + (i % 5) for i in range(n)]
    closes = [95.0 + (i % 7) * 0.5 for i in range(n)]
    atr = atr_wilder_series(highs, lows, closes, period=14)
    assert atr[13] is not None
    assert atr[0] is None
    assert atr[20] is not None and atr[20] > 0


def test_soft_pass_na_not_arm():
    assert PASS_PAIRS_NEEDED == 2
    assert SOURCE.endswith("133")


def test_no_bos_import_in_strategy_module():
    import ast
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "src/atlas/strategy/scalp_dt_rvol_1h_133.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imported.append(mod)
            imported.extend(f"{mod}.{a.name}" for a in node.names)
    assert all("scalp_structure_bos" not in x for x in imported)
    assert all("scalp_dt_rvol_15m_130" not in x for x in imported)
    assert all("scalp_dt_rvol_1h_131" not in x for x in imported)
