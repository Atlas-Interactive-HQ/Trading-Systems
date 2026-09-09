"""EMA persist-2 entry: asymmetric entry, immediate exit, never short, no trade client."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.okx.client import OkxEeaClient
from atlas.paper.ema_eval import EmaBookSettings, walk_long_flat
from atlas.paper.ema_persist2_eval import PERSIST2_SOURCE, run_ema_persist2_eval
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.types import Bar
from atlas.strategy.ema_persist2 import EmaPersist2EntryV1, EmaPersist2Params
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendV1

DAY = 24 * 60 * 60 * 1000
START = 1_598_918_400_000
SYM = "BTC-USDT"


def dbar(i: int, c: float, h: float | None = None, lo: float | None = None) -> Bar:
    ts = START + i * DAY
    hi = h if h is not None else c + 0.5
    low = lo if lo is not None else c - 0.5
    return Bar(SYM, ts, ts + DAY, c, hi, low, c, 1.0, True, "test")


def test_label_persist2_locked():
    s = EmaPersist2EntryV1()
    assert s.label == "ema_12_30_persist2_entry_v1"
    assert s.warmup_bars() == 31


def test_rejects_persist_sweeps():
    with pytest.raises(ValueError, match="locked"):
        EmaPersist2EntryV1(EmaPersist2Params(entry_persist=3))


def test_never_short_on_dump():
    s = EmaPersist2EntryV1()
    falling = [dbar(i, 200.0 - i) for i in range(50)]
    assert s.desired_state(falling) == FLAT


def test_single_day_ema_long_stays_flat():
    """One bar of EMA12>EMA30 is not enough — need persist=2."""
    s = EmaPersist2EntryV1(EmaPersist2Params(fast=3, slow=5, entry_persist=2))
    # Build flat then one up-day that flips EMA long for only the last bar.
    bars = [dbar(i, 100.0 - i * 0.5) for i in range(8)]
    bars.append(dbar(8, 130.0))
    # Baseline EMA may or may not be long; persist2 must still require 2 consecutive.
    # Force two consecutive longs next test; here ensure first flip alone is flat if only 1 day.
    # Walk: after gentle down, one spike — prior bar was not EMA-long.
    assert s.desired_state(bars) == FLAT


def test_two_consecutive_ema_long_enters():
    s = EmaPersist2EntryV1(EmaPersist2Params(fast=3, slow=5, entry_persist=2))
    bars = []
    px = 100.0
    for i in range(12):
        px *= 1.05
        bars.append(dbar(i, px))
    assert EmaTrendV1.__new__(EmaTrendV1)  # import used
    from atlas.strategy.ema_trend import EmaTrendParams

    base = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    assert base.desired_state(bars) == LONG
    assert base.desired_state(bars[:-1]) == LONG
    assert s.desired_state(bars) == LONG


def test_immediate_exit_on_ema_cross_under():
    s = EmaPersist2EntryV1(EmaPersist2Params(fast=3, slow=5, entry_persist=2))
    bars = []
    px = 100.0
    for i in range(12):
        px *= 1.05
        bars.append(dbar(i, px))
    assert s.desired_state(bars) == LONG
    # Sharp dump: exit on first bar where EMA fast <= slow (no exit persist).
    for j in range(8):
        px *= 0.85
        bars.append(dbar(12 + j, px))
    assert s.desired_state(bars) == FLAT


def test_signal_fills_next_open_not_close(monkeypatch: pytest.MonkeyPatch):
    seen: list[tuple[str, float]] = []

    def spy(price: float, buy_sell: str, slippage_bps: float) -> float:
        seen.append((buy_sell, float(price)))
        return float(price)

    monkeypatch.setattr("atlas.paper.ema_eval.apply_slippage", spy)
    s = EmaPersist2EntryV1(EmaPersist2Params(fast=3, slow=5, entry_persist=2))
    bars = []
    px = 100.0
    for i in range(14):
        px *= 1.05
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
    t0 = win.start_ms - 40 * DAY
    bars = []
    px = 10000.0
    for i in range(200):
        px = px * 1.002
        ts = t0 + i * DAY
        bars.append(Bar(SYM, ts, ts + DAY, px * 0.999, px * 1.02, px * 0.98, px, 1.0, True, "test"))
    bundle = run_ema_persist2_eval(
        cfg,
        asset=SYM,
        windows="2022-h1",
        data_dir=tmp_path,
        bars_by_window={"2022-h1": bars},
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert bundle["source"] == PERSIST2_SOURCE
    assert bundle["entry_persist"] == 2
    assert bundle["samples_persist2"][0]["ok"] is True
    assert bundle["pass_gate"]["do_not_promote"] is True
    assert (tmp_path / "reports" / f"ema_persist2_{SYM}_2022-h1.json").is_file()
    assert not (tmp_path / "ema" / "state.json").exists()


def test_source_files_have_no_trade_client():
    root = Path(__file__).resolve().parents[2]
    for rel in (
        "src/atlas/strategy/ema_persist2.py",
        "src/atlas/paper/ema_persist2_eval.py",
        "scripts/run_ema_persist2_eval.py",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        assert "OkxEeaClient" not in text
        assert "place-demo-orders" not in text
        assert "allow_trade" not in text
