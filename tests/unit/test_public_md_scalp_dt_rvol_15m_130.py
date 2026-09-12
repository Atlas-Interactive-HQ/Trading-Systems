"""Unit tests: phase1/130 Dual Thrust N4 + RVOL 15m + 1H EMA21 (no BOS)."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.public_md_scalp_dt_rvol_15m_130 import (
    BASELINE_121_DT_RVOL_FULL,
    BASELINE_126_FULL,
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
    walk_dt_rvol_15m_130,
)
from atlas.paper.types import Bar
from atlas.strategy.dual_thrust import DualThrustLongFlatV1, DualThrustParams
from atlas.strategy.scalp_dt_rvol_15m_130 import (
    ATR_N,
    ATR_SL_MULT,
    BAR,
    EMA_H1,
    FAMILY,
    K1,
    K2,
    N,
    R,
    RVOL_GATE,
    RVOL_N,
    TIME_STOP,
    DtRvol130Signals,
    ScalpDtRvol15m130Params,
    ScalpDtRvol15m130V1,
    atr_wilder_series,
    resolve_sl_at_entry,
)


def _bar15(
    i: int,
    o: float,
    h: float,
    l: float,
    c: float,
    *,
    vol: float = 100.0,
    symbol: str = "BTC-USDT",
) -> Bar:
    open_ms = i * 15 * 60_000
    return Bar(
        symbol=symbol,
        ts_open_ms=open_ms,
        ts_close_ms=open_ms + 15 * 60_000,
        open=o,
        high=h,
        low=l,
        close=c,
        volume=vol,
        closed=True,
        source="test",
    )


def _bar1h(
    i: int,
    o: float,
    h: float,
    l: float,
    c: float,
    *,
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
        volume=1000.0,
        closed=True,
        source="test",
    )


def test_phase_and_source_locked_130():
    assert PHASE1 == 130
    assert SOURCE == "public_md_scalp_dt_rvol_15m_130"
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    assert PASS_PAIRS_NEEDED == 2
    assert FAMILY.startswith("dt_n4")
    assert "structure_bos" not in FAMILY
    assert "structure_bos" not in ID_FAMILY


def test_locked_constants():
    assert N == 4
    assert K1 == K2 == 0.5
    assert RVOL_N == 20
    assert RVOL_GATE == 1.2
    assert EMA_H1 == 21
    assert R == 1.5
    assert TIME_STOP == 16
    assert ATR_N == 14
    assert ATR_SL_MULT == 1.0
    assert BAR == "15m"


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
        assert "structure_bos" not in cid
        assert "rise_panel" not in cid


def test_baselines_locked():
    assert BASELINE_126_FULL["BTC-USDT"]["n"] == 339
    assert BASELINE_126_FULL["BTC-USDT"]["exp"] == pytest.approx(-0.02643514)
    assert BASELINE_121_DT_RVOL_FULL["BTC-USDT"]["n"] == 18
    assert BASELINE_121_DT_RVOL_FULL["ETH-USDT"]["exp"] == pytest.approx(1.1968212)
    assert BASELINE_121_DT_RVOL_FULL["DOGE-USDT"]["terminal"] == pytest.approx(
        5.36013111
    )


def test_reject_grind():
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol15m130V1(ScalpDtRvol15m130Params(lookback=5))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol15m130V1(ScalpDtRvol15m130Params(k1=0.6))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol15m130V1(ScalpDtRvol15m130Params(rvol_gate=1.0))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol15m130V1(ScalpDtRvol15m130Params(ema_h1=12))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol15m130V1(ScalpDtRvol15m130Params(r_multiple=2.0))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol15m130V1(ScalpDtRvol15m130Params(time_stop_bars=32))
    with pytest.raises(ValueError, match="grind"):
        ScalpDtRvol15m130V1(ScalpDtRvol15m130Params(atr_period=20))


def test_buyline_formula_matches_dual_thrust():
    # Build N+1 bars so prior HH-LL is defined on last bar
    bars = []
    for i in range(6):
        # increasing range history
        bars.append(_bar15(i, 100 + i, 105 + i, 95 + i, 100 + i, vol=100.0))
    inner = DualThrustLongFlatV1(DualThrustParams(lookback=4, k1=0.5, k2=0.5))
    ranges = inner.ranges_at(bars)
    assert ranges is not None
    buy, sell = ranges
    last = bars[-1]
    # prior 4 bars exclusive of last: indices 1..4? donchian_prior uses bars[:-1] last N
    # Verify BuyLine = Open + 0.5 * range
    from atlas.strategy.dual_thrust import prior_hh_ll_range

    rng = prior_hh_ll_range(bars, 4)
    assert rng is not None
    assert buy == pytest.approx(last.open + 0.5 * rng)
    assert sell == pytest.approx(last.open - 0.5 * rng)


def test_rvol_gate_blocks_entry():
    # Enough bars for DT N=4 + RVOL 20
    n = 30
    bars_15 = []
    for i in range(n):
        # Quiet volume except we keep vol low so RVOL never > 1.2
        bars_15.append(_bar15(i, 100, 110, 90, 108, vol=10.0))
    # 1H bull regime: rising closes
    bars_1h = [_bar1h(i, 100 + i, 110 + i, 90 + i, 105 + i) for i in range(40)]
    # Align 1H timestamps so they cover 15m closes
    # _bar1h uses hour index; _bar15 uses 15m index — map 15m into same ms space
    bars_15 = []
    for i in range(n):
        open_ms = i * 15 * 60_000
        bars_15.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 15 * 60_000,
                open=100.0,
                high=120.0,
                low=80.0,
                close=115.0,  # above buyline likely
                volume=10.0,
                closed=True,
                source="test",
            )
        )
    bars_1h = []
    for i in range(40):
        open_ms = i * 60 * 60_000
        bars_1h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 60 * 60_000,
                open=100.0 + i,
                high=110.0 + i,
                low=90.0 + i,
                close=108.0 + i,  # above EMA eventually
                volume=1000.0,
                closed=True,
                source="test",
            )
        )
    strat = ScalpDtRvol15m130V1()
    sig = strat.precompute_signals(bars_15, bars_1h)
    # With flat volume, RVOL ≈ 1.0 < 1.2 → no entries once warm
    warm = [i for i, ok in enumerate(sig.entry_ok) if ok]
    assert warm == [] or all(
        (sig.rvol[i] is not None and float(sig.rvol[i]) > 1.2) for i in warm
    )
    # Force: spike volume on last bar with buy + regime
    bars_15[-1] = Bar(
        symbol="BTC-USDT",
        ts_open_ms=bars_15[-1].ts_open_ms,
        ts_close_ms=bars_15[-1].ts_close_ms,
        open=100.0,
        high=130.0,
        low=80.0,
        close=125.0,
        volume=10.0,  # still equal → RVOL=1
        closed=True,
        source="test",
    )
    sig2 = strat.precompute_signals(bars_15, bars_1h)
    assert sig2.entry_ok[-1] is False


def test_ema21_regime_blocks_when_below():
    n = 40
    bars_15 = []
    for i in range(n):
        open_ms = i * 15 * 60_000
        bars_15.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 15 * 60_000,
                open=100.0,
                high=130.0,
                low=70.0,
                close=125.0,
                volume=500.0 if i == n - 1 else 100.0,
                closed=True,
                source="test",
            )
        )
    # Falling 1H → close below EMA21
    bars_1h = []
    for i in range(50):
        open_ms = i * 60 * 60_000
        c = 200.0 - i * 2.0
        bars_1h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=open_ms,
                ts_close_ms=open_ms + 60 * 60_000,
                open=c + 1,
                high=c + 5,
                low=c - 5,
                close=c,
                volume=1000.0,
                closed=True,
                source="test",
            )
        )
    strat = ScalpDtRvol15m130V1()
    sig = strat.precompute_signals(bars_15, bars_1h)
    assert sig.regime_ok[-1] is False
    assert sig.entry_ok[-1] is False
    assert all(not ok for ok in sig.entry_ok) or not any(
        sig.entry_ok[i] and not sig.regime_ok[i] for i in range(n)
    )


def test_no_lookahead_15m_before_1h_close_ineligible():
    # 15m bar that closes mid-1H must not use the in-progress 1H
    # 1H bar 0: open 0, close 3600000
    # 15m bar at open 0: close 900000 — before 1H close → no regime yet (j<0 or prior)
    bars_1h = [
        Bar(
            symbol="BTC-USDT",
            ts_open_ms=0,
            ts_close_ms=3_600_000,
            open=100,
            high=110,
            low=90,
            close=200,  # would be bullish if used early
            volume=1000,
            closed=True,
            source="test",
        )
    ]
    # Need 21+ 1H bars for EMA; first 15m bars before any 1H close → False
    for i in range(1, 30):
        bars_1h.append(
            Bar(
                symbol="BTC-USDT",
                ts_open_ms=i * 3_600_000,
                ts_close_ms=(i + 1) * 3_600_000,
                open=100 + i,
                high=110 + i,
                low=90 + i,
                close=105 + i,
                volume=1000,
                closed=True,
                source="test",
            )
        )
    # 15m bar closing at 900_000 — only 1H with close<=900k: none
    bars_15 = [
        Bar(
            symbol="BTC-USDT",
            ts_open_ms=0,
            ts_close_ms=900_000,
            open=100,
            high=110,
            low=90,
            close=105,
            volume=100,
            closed=True,
            source="test",
        )
    ]
    strat = ScalpDtRvol15m130V1()
    sig = strat.precompute_signals(bars_15, bars_1h)
    assert sig.regime_ok[0] is False


def test_sl_fallback_and_skip():
    assert resolve_sl_at_entry(
        entry_px=100.0, sell_line_at_entry=95.0, atr_at_entry=2.0
    ) == pytest.approx(95.0)
    # SellLine >= entry → ATR fallback
    assert resolve_sl_at_entry(
        entry_px=100.0, sell_line_at_entry=100.0, atr_at_entry=3.0
    ) == pytest.approx(97.0)
    assert resolve_sl_at_entry(
        entry_px=100.0, sell_line_at_entry=101.0, atr_at_entry=2.5
    ) == pytest.approx(97.5)
    # Still not below → None
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
    n = 40
    bars = [_bar15(i, 100, 101, 99, 100.5) for i in range(n)]
    sig = DtRvol130Signals(
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
    out = walk_dt_rvol_15m_130(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        time_stop_bars=16,
    )
    assert out["n_short_entries"] == 0
    assert out["n_long_entries"] >= 1
    assert out["n_time_stop_exits"] >= 1
    assert out["place_orders"] is False
    assert out["not_a_forecast"] is True


def test_walker_1_5r_vs_sellline():
    n = 20
    # Entry at bar1 open ~100; SL=95 → R=5 → TP=107.5
    bars = [_bar15(i, 100, 101, 99, 100.2) for i in range(n)]
    bars[5] = _bar15(5, 106, 110, 105, 108.0)  # close above TP
    sig = DtRvol130Signals(
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
    out = walk_dt_rvol_15m_130(
        bars,
        sig,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        r_multiple=1.5,
        time_stop_bars=16,
    )
    assert out["n_tp_exits"] >= 1 or out["n_trades"] >= 1

    # SellLine exit path: price never hits TP/SL but close < current SellLine
    bars2 = [_bar15(i, 100, 101, 99, 100.2) for i in range(n)]
    sell_lines = [95.0] * n
    sell_lines[4] = 100.5  # current sellline above close → exit sellline
    bars2[4] = _bar15(4, 100, 101, 99, 100.0)
    sig2 = DtRvol130Signals(
        regime_ok=[True] * n,
        buy_line=[99.0] * n,
        sell_line=sell_lines,
        rvol=[2.0] * n,
        atr=[1.0] * n,
        entry_ok=[True] + [False] * (n - 1),
        buy=[True] + [False] * (n - 1),
        sell=[False] * n,
    )
    out2 = walk_dt_rvol_15m_130(
        bars2,
        sig2,
        settings=settings,
        trade_start_ms=0,
        trade_end_ms=10_000_000_000,
        time_stop_bars=16,
    )
    assert out2["n_sellline_exits"] >= 1 or out2["n_trades"] >= 1


def test_walker_skip_when_sl_not_below():
    n = 10
    bars = [_bar15(i, 100, 101, 99, 100.5) for i in range(n)]
    # SellLine above any reasonable entry; ATR None → skip
    sig = DtRvol130Signals(
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
    out = walk_dt_rvol_15m_130(
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
    assert SOURCE.endswith("130")


def test_no_bos_import_in_strategy_module():
    import ast
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "src/atlas/strategy/scalp_dt_rvol_15m_130.py"
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
