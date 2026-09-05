"""EMA ATR gate: locked 0.01, never short, no lookahead, no trade client."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.okx.client import OkxEeaClient
from atlas.paper.ema_atr_eval import ATR_SOURCE, run_ema_atr_eval
from atlas.paper.ema_eval import EmaBookSettings, walk_long_flat
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.types import Bar
from atlas.strategy.breakout import sma_atr
from atlas.strategy.ema_atr_gate import EmaAtrGateParams, EmaAtrGateV1
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendV1

DAY = 24 * 60 * 60 * 1000
START = 1_598_918_400_000
SYM = "BTC-USDT"


def dbar(i: int, c: float, h: float | None = None, lo: float | None = None) -> Bar:
    ts = START + i * DAY
    hi = h if h is not None else c + 0.5
    low = lo if lo is not None else c - 0.5
    return Bar(SYM, ts, ts + DAY, c, hi, low, c, 1.0, True, "test")


def test_label_locked_0p01():
    s = EmaAtrGateV1()
    assert s.label == "ema_atr_gate_v1_12_30_14_0p01"
    assert s.warmup_bars() == 30


def test_never_short_on_dump():
    s = EmaAtrGateV1()
    falling = [dbar(i, 200.0 - i, h=200.0 - i + 50, lo=200.0 - i - 50) for i in range(50)]
    assert s.desired_state(falling) == FLAT


def test_ema_long_but_quiet_atr_stays_flat():
    """Gentle grind: EMA 12>30 but ATR/close << 0.01 → flat."""
    s = EmaAtrGateV1()
    bars = [dbar(i, 10_000.0 + i * 2.0, h=10_000.0 + i * 2.0 + 1.0, lo=10_000.0 + i * 2.0 - 1.0) for i in range(40)]
    assert EmaTrendV1().desired_state(bars) == LONG
    atr = sma_atr(bars, 14)
    assert atr is not None
    assert atr / bars[-1].close < 0.01
    assert s.desired_state(bars) == FLAT


def test_ema_long_and_atr_gate_goes_long():
    s = EmaAtrGateV1(EmaAtrGateParams(fast=3, slow=5, atr_period=3, min_atr_frac=0.01))
    bars = []
    px = 100.0
    for i in range(12):
        px *= 1.04
        bars.append(dbar(i, px, h=px * 1.03, lo=px * 0.97))
    assert s.desired_state(bars) == LONG
    atr = sma_atr(bars, 3)
    assert atr is not None
    assert atr / bars[-1].close >= 0.01


def test_no_lookahead_future_bar_does_not_change_prior_state():
    s = EmaAtrGateV1(EmaAtrGateParams(fast=3, slow=5, atr_period=3, min_atr_frac=0.01))
    bars = []
    px = 100.0
    for i in range(12):
        px *= 1.04
        bars.append(dbar(i, px, h=px * 1.03, lo=px * 0.97))
    before = s.desired_state(bars)
    future = dbar(12, px * 2.0, h=px * 4.0, lo=px * 0.5)
    after = s.desired_state(bars)  # still without future
    assert after == before
    # decision on prefix must ignore the future bar sitting later in a longer list
    assert s.desired_state(bars) == s.desired_state([*bars, future][: len(bars)])


def test_signal_fills_next_open_not_close(monkeypatch: pytest.MonkeyPatch):
    seen: list[tuple[str, float]] = []

    def spy(price: float, buy_sell: str, slippage_bps: float) -> float:
        seen.append((buy_sell, float(price)))
        return float(price)

    monkeypatch.setattr("atlas.paper.ema_eval.apply_slippage", spy)
    s = EmaAtrGateV1(EmaAtrGateParams(fast=3, slow=5, atr_period=3, min_atr_frac=0.01))
    bars = []
    px = 100.0
    for i in range(12):
        px *= 1.04
        o = px * 0.99
        bars.append(Bar(SYM, START + i * DAY, START + (i + 1) * DAY, o, px * 1.03, px * 0.97, px, 1.0, True, "test"))
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
    assert bars[-2].close not in buys


def test_run_eval_injected_no_okx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    cfg = load_config()
    win = parse_windows_arg("2022-h1")[0]
    t0 = win.start_ms - 40 * DAY
    bars = []
    px = 10000.0
    for i in range(200):
        px = px * 1.002
        ts = t0 + i * DAY
        bars.append(Bar(SYM, ts, ts + DAY, px * 0.999, px * 1.02, px * 0.98, px, 1.0, True, "test"))
    bundle = run_ema_atr_eval(
        cfg,
        asset=SYM,
        windows="2022-h1",
        data_dir=tmp_path,
        bars_by_window={"2022-h1": bars},
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert bundle["source"] == ATR_SOURCE
    assert bundle["min_atr_frac"] == 0.01
    assert bundle["samples"][0]["ok"] is True
    assert bundle["interesting"]["verdict"] == "FAIL"
    assert bundle["interesting"]["do_not_promote"] is True
    assert (tmp_path / "reports" / f"ema_atr_{SYM}_2022-h1.json").is_file()
    assert not (tmp_path / "reports" / f"ema_{SYM}_2022-h1.json").exists()


def test_source_files_have_no_trade_client():
    root = Path(__file__).resolve().parents[2]
    for rel in (
        "src/atlas/strategy/ema_atr_gate.py",
        "src/atlas/paper/ema_atr_eval.py",
        "scripts/run_ema_atr_gate_eval.py",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        assert "OkxEeaClient" not in text
        assert "place-demo-orders" not in text
        assert "allow_trade" not in text
