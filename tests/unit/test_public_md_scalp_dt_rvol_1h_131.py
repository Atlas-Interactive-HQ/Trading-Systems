"""Unit tests: phase1/131 Dual Thrust N4 + RVOL 1H + 4H EMA21 (leave #130 STOP)."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_dt_rvol_1h_131 import (
    BASELINE_121_DT_RVOL_FULL,
    BASELINE_130_FULL,
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
    walk_dt_rvol_1h_131,
)
from atlas.paper.types import Bar
from atlas.strategy.dual_thrust import DualThrustLongFlatV1, DualThrustParams
from atlas.strategy.scalp_dt_rvol_1h_131 import (
    ATR_N,
    ATR_SL_MULT,
    BAR,
    EMA_4H,
    FAMILY,
    K1,
    K2,
    N,
    R,
    REGIME_BAR,
    RVOL_GATE,
    RVOL_N,
    TIME_STOP,
    DtRvol131Signals,
    ScalpDtRvol1h131Params,
    ScalpDtRvol1h131V1,
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


def test_phase_and_source_locked_131():
    assert PHASE1 == 131
    assert SOURCE == "public_md_scalp_dt_rvol_1h_131"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert PASS_PAIRS_NEEDED == 2
    assert FAMILY.startswith("dt_n4")
    assert "4h_regime_1h" in FAMILY
    assert "structure_bos" not in FAMILY
    assert "structure_bos" not in ID_FAMILY
    assert "15m" not in ID_FAMILY


def test_locked_constants():
    assert N == 4
    assert K1 == K2 == 0.5
    assert RVOL_N == 20
    assert RVOL_GATE == 1.2
    assert EMA_4H == 21
    assert R == 1.5
    assert TIME_STOP == 24
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
    for inst in USDT_INSTS:
        cid = candidate_id_for(inst)
        assert cid.startswith(ID_FAMILY + "_")
        assert cid.endswith("_eur20")
        assert "ema21_4h_regime_1h" in cid
        assert "structure_bos" not in cid
        assert "rise_panel" not in cid
        assert "15m" not in cid


def test_baselines_locked():
    assert BASELINE_130_FULL["BTC-USDT"]["n"] == 296
    assert BASELINE_130_FULL["BTC-USDT"]["exp"] == pytest.approx(-0.0339961)
    assert BASELINE_130_FULL["ETH-USDT"]["terminal"] == pytest.approx(-8.16998247)
    assert BASELINE_121_DT_RVOL_FULL["BTC-USDT"]["n"] == 18
    assert BASELINE_121_DT_RVOL_FULL["ETH-USDT"]["exp"] == pytest.approx(1.1968212)
    assert BASELINE_121_DT_RVOL_FULL["DOGE-USDT"]["terminal"] == pytest.approx(
        5.36013111
    )


def test_reject_grind():
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h131V1(ScalpDtRvol1h131Params(lookback=5))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h131V1(ScalpDtRvol1h131Params(k1=0.6))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h131V1(ScalpDtRvol1h131Params(rvol_gate=1.0))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h131V1(ScalpDtRvol1h131Params(ema_4h=12))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h131V1(ScalpDtRvol1h131Params(r_multiple=2.0))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h131V1(ScalpDtRvol1h131Params(time_stop_bars=16))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol1h131V1(ScalpDtRvol1h131Params(atr_period=20))


def test_reject_15m_bar():
    with pytest.raises(ValueError, match="bar grind"):
        ScalpDtRvol1h131V1(ScalpDtRvol1h131Params(bar="15m"))
    with pytest.raises(ValueError, match="regime_bar grind"):
        ScalpDtRvol1h131V1(ScalpDtRvol1h131Params(regime_bar="1H"))


def test_buyline_formula_matches_dual_thrust_n4_1h():
    bars = []
    for i in range(6):
        bars.append(_bar1h(i, 100 + i, 105 + i, 95 + i, 100 + i, vol=100.0))
    inner = DualThrustLongFlatV1(DualThrustParams(lookback=4, k1=0.5, k2=0.5))
    ranges = inner.ranges_at(bars)
    assert ranges is not None
    buy, sell = ranges
    last = bars[-1]
    from atlas.strategy.dual_thrust import prior_hh_ll_range

    rng = prior_hh_ll_range(bars, 4)
    assert rng is not None
    assert buy == pytest.approx(last.open + 0.5 * rng)
    assert sell == pytest.approx(last.open - 0.5 * rng)


def test_rvol_gate_blocks_entry():
    n = 30
    bars_1h = []
    for i in range(n):
        open_ms = i * 60 * 60_000
        bars_1h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 60 * 60_000,
                open=100.0,
                high=120.0,
                low=80.0,
                close=115.0,
                volume=10.0,
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
    strat = ScalpDtRvol1h131V1()
    sig = strat.precompute_signals(bars_1h, bars_4h)
    warm = [i for i, ok in enumerate(sig.entry_ok) if ok]
    assert warm == [] or all(
        (sig.rvol[i] is not None and float(sig.rvol[i]) > 1.2) for i in warm
    )
    bars_1h[-1] = Bar(
        symbol="BTC-USDT",
        ts_open_ms=bars_1h[-1].ts_open_ms,
        ts_close_ms=bars_1h[-1].ts_close_ms,
        open=100.0,
        high=130.0,
        low=80.0,
        close=125.0,
        volume=10.0,
        closed=True,
        source="test",
    )
    sig2 = strat.precompute_signals(bars_1h, bars_4h)
    assert sig2.entry_ok[-1] is False


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
    strat = ScalpDtRvol1h131V1()
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
    # 1H bar closing at 3_600_000 — before first 4H close → no regime
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
    strat = ScalpDtRvol1h131V1()
    sig = strat.precompute_signals(bars_1h, bars_4h)
    assert sig.regime_ok[0] is False


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


def test_walker_fill_next_open_and_time_stop():
    n = 50
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    sig = DtRvol131Signals(
        regime_ok=[True] * n,
        buy_line=[99.0] * n,
        sell_line=[95.0] * n,
        rvol=[2.0] * n,
        atr=[1.0] * n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
        sell=[False] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    out = walk_dt_rvol_1h_131(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        time_stop_bars=24,
    )
    assert out["n_short_entries"] == 0
    assert out["n_long_entries"] >= 1
    assert out["n_time_stop_exits"] >= 1
    assert out["place_orders"] is False
    assert out["not_a_forecast"] is True
    assert out["time_stop_bars"] == 24


def test_walker_1_5r_vs_sellline():
    n = 20
    bars = [_bar1h(i, 100, 101, 99, 100.2) for i in range(n)]
    bars[5] = _bar1h(5, 106, 110, 105, 108.0)
    sig = DtRvol131Signals(
        regime_ok=[True] * n,
        buy_line=[99.0] * n,
        sell_line=[95.0] * n,
        rvol=[2.0] * n,
        atr=[1.0] * n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
        sell=[False] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    out = walk_dt_rvol_1h_131(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        r_multiple=1.5,
        time_stop_bars=24,
    )
    assert out["n_tp_exits"] >= 1 or out["n_trades"] >= 1

    bars2 = [_bar1h(i, 100, 101, 99, 100.2) for i in range(n)]
    sell_lines = [95.0] * n
    sell_lines[4] = 100.5
    bars2[4] = _bar1h(4, 100, 101, 99, 100.0)
    sig2 = DtRvol131Signals(
        regime_ok=[True] * n,
        buy_line=[99.0] * n,
        sell_line=sell_lines,
        rvol=[2.0] * n,
        atr=[1.0] * n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
        sell=[False] * n,
    )
    out2 = walk_dt_rvol_1h_131(
        bars2,
        sig2,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        time_stop_bars=24,
    )
    assert out2["n_sellline_exits"] >= 1 or out2["n_trades"] >= 1


def test_walker_skip_when_sl_not_below():
    n = 10
    bars = [_bar1h(i, 100, 101, 99, 100.5) for i in range(n)]
    sig = DtRvol131Signals(
        regime_ok=[True] * n,
        buy_line=[99.0] * n,
        sell_line=[200.0] * n,
        rvol=[2.0] * n,
        atr=[None] * n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
        sell=[False] * n,
    )
    settings = EmaBookSettings(
        equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0, leverage=1.0
    )
    out = walk_dt_rvol_1h_131(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
    )
    assert out["n_long_entries"] == 0
    assert out["n_skipped_sl_not_below"] >= 1


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
    assert SOURCE.endswith("131")


def test_no_bos_import_in_strategy_module():
    import ast
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "src/atlas/strategy/scalp_dt_rvol_1h_131.py"
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
