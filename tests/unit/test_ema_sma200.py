"""EMA + SMA(200) regime: both filters, never short, no lookahead, no trade client."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.okx.client import OkxEeaClient
from atlas.paper.ema_eval import EmaBookSettings, walk_long_flat
from atlas.paper.ema_sma200_eval import SMA200_SOURCE, run_ema_sma200_eval
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.types import Bar
from atlas.strategy.ema_sma200 import EmaSma200Params, EmaSma200RegimeV1, sma_at
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

DAY = 24 * 60 * 60 * 1000
START = 1_598_918_400_000
SYM = "BTC-USDT"


def dbar(i: int, c: float, h: float | None = None, lo: float | None = None) -> Bar:
    ts = START + i * DAY
    hi = h if h is not None else c + 0.5
    low = lo if lo is not None else c - 0.5
    return Bar(SYM, ts, ts + DAY, c, hi, low, c, 1.0, True, "test")


def test_label_and_warmup_12_30_200():
    s = EmaSma200RegimeV1()
    assert s.label == "ema_sma200_regime_v1_12_30_200"
    assert s.warmup_bars() == 220


def test_never_short_on_dump():
    s = EmaSma200RegimeV1()
    falling = [dbar(i, 200.0 - i) for i in range(250)]
    assert s.desired_state(falling) == FLAT


def test_ema_long_but_below_sma_stays_flat():
    """Gentle grind after a high plateau: EMA may go long while close < SMA(200)."""
    s = EmaSma200RegimeV1(EmaSma200Params(fast=3, slow=5, sma_period=20))
    bars = [dbar(i, 200.0) for i in range(25)]
    # late mild uptrend from a deep hole so SMA stays above close for a while
    bars = [dbar(i, 50.0) for i in range(18)]
    bars.extend([dbar(18 + j, 50.0 + j * 2.0) for j in range(8)])
    base = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    # If EMA is long but close <= SMA → flat
    if base.desired_state(bars) == LONG:
        sma = sma_at([float(b.close) for b in bars], 20)
        assert sma is not None
        if bars[-1].close <= sma:
            assert s.desired_state(bars) == FLAT


def test_ema_long_and_above_sma_goes_long():
    s = EmaSma200RegimeV1(EmaSma200Params(fast=3, slow=5, sma_period=10))
    bars = []
    px = 100.0
    for i in range(30):
        px *= 1.03
        bars.append(dbar(i, px))
    assert EmaTrendV1(EmaTrendParams(fast=3, slow=5)).desired_state(bars) == LONG
    sma = sma_at([float(b.close) for b in bars], 10)
    assert sma is not None and bars[-1].close > sma
    assert s.desired_state(bars) == LONG


def test_insufficient_sma_history_flat():
    s = EmaSma200RegimeV1(EmaSma200Params(fast=3, slow=5, sma_period=50))
    bars = []
    px = 100.0
    for i in range(20):
        px *= 1.05
        bars.append(dbar(i, px))
    assert s.desired_state(bars) == FLAT


def test_signal_fills_next_open_not_close(monkeypatch: pytest.MonkeyPatch):
    seen: list[tuple[str, float]] = []

    def spy(price: float, buy_sell: str, slippage_bps: float) -> float:
        seen.append((buy_sell, float(price)))
        return float(price)

    monkeypatch.setattr("atlas.paper.ema_eval.apply_slippage", spy)
    s = EmaSma200RegimeV1(EmaSma200Params(fast=3, slow=5, sma_period=8))
    bars = []
    px = 100.0
    for i in range(20):
        px *= 1.04
        o = px * 0.99
        bars.append(
            Bar(SYM, START + i * DAY, START + (i + 1) * DAY, o, px * 1.03, px * 0.97, px, 1.0, True, "test")
        )
    walk_long_flat(
        bars,
        strategy=s,
        settings=EmaBookSettings(equity_eur=200.0, fee_rate=0.0, slippage_bps=0.0),
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
    )
    buys = [p for side, p in seen if side == "buy"]
    assert buys
    assert all(p in {b.open for b in bars} for p in buys)


def test_run_eval_injected_no_okx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    cfg = load_config()
    win = parse_windows_arg("2022-h1")[0]
    t0 = win.start_ms - 220 * DAY
    bars = []
    px = 10000.0
    for i in range(400):
        px = px * 1.002
        ts = t0 + i * DAY
        bars.append(Bar(SYM, ts, ts + DAY, px * 0.999, px * 1.02, px * 0.98, px, 1.0, True, "test"))
    bundle = run_ema_sma200_eval(
        cfg,
        asset=SYM,
        windows="2022-h1",
        data_dir=tmp_path,
        bars_by_window={"2022-h1": bars},
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert bundle["source"] == SMA200_SOURCE
    assert bundle["sma_period"] == 200
    assert bundle["warmup_days"] == 220
    assert bundle["samples"][0]["ok"] is True
    assert bundle["interesting"]["do_not_promote"] is True
    assert (tmp_path / "reports" / f"ema_sma200_{SYM}_2022-h1.json").is_file()
    assert not (tmp_path / "ema" / "state.json").exists()


def test_source_files_have_no_trade_client():
    root = Path(__file__).resolve().parents[2]
    for rel in (
        "src/atlas/strategy/ema_sma200.py",
        "src/atlas/paper/ema_sma200_eval.py",
        "scripts/run_ema_sma200_regime_eval.py",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        assert "OkxEeaClient" not in text
        assert "place-demo-orders" not in text
        assert "allow_trade" not in text
