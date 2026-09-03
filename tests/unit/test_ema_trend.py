"""EMA long/flat: no lookahead, never short, fail-closed empty history, 1D bars."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from atlas.common.config import load_config
from atlas.dashboard.app import create_app
from atlas.okx.client import OkxEeaClient
from atlas.paper.ema_eval import (
    EmaBookSettings,
    buy_and_hold,
    interesting_bar,
    oos_stress_bar,
    run_ema_eval,
    walk_long_flat,
)
from atlas.paper.fills import apply_slippage
from atlas.paper.md import bar_ms, okx_bar
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1, ema_series

DAY = 24 * 60 * 60 * 1000
START = 1_598_918_400_000  # 2020-09-01 UTC
SYM = "BTC-USDT"


def dbar(i: int, c: float, o: float | None = None) -> Bar:
    ts = START + i * DAY
    ox = c if o is None else o
    hi = max(ox, c) + 0.5
    lo = min(ox, c) - 0.5
    return Bar(SYM, ts, ts + DAY, ox, hi, lo, c, 1.0, True, "test")


def test_okx_1d_bar_supported():
    assert okx_bar("1D") == "1D"
    assert okx_bar("1d") == "1D"
    assert bar_ms("1D") == DAY


def test_ema_series_deterministic():
    closes = [float(i) for i in range(1, 40)]
    a = ema_series(closes, 12)
    b = ema_series(closes, 12)
    assert a == b
    assert a[10] is None and a[11] is not None
    assert a[-1] is not None and a[-1] > a[11]


def test_desired_state_flat_until_warmup_never_short():
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    bars = [dbar(i, 100.0) for i in range(4)]
    assert s.desired_state(bars) == FLAT
    falling = [dbar(i, 100.0 - i) for i in range(20)]
    assert s.desired_state(falling) == FLAT  # not short
    rising = [dbar(i, 100.0 + i) for i in range(20)]
    assert s.desired_state(rising) == LONG


def test_signal_at_t_fills_t_plus_1_open_not_same_bar_close(monkeypatch: pytest.MonkeyPatch):
    """EMA cross on bar t close must fill at bar t+1 open (no lookahead)."""
    seen: list[tuple[str, float]] = []

    def spy(price: float, buy_sell: str, slippage_bps: float) -> float:
        seen.append((buy_sell, float(price)))
        return float(price)

    monkeypatch.setattr("atlas.paper.ema_eval.apply_slippage", spy)
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    bars = [dbar(i, 100.0) for i in range(8)]
    bars.append(dbar(8, 130.0, o=100.0))  # cross likely here; close 130
    bars.append(dbar(9, 131.0, o=101.0))  # next open 101
    bars += [dbar(i, 132.0) for i in range(10, 14)]
    walk_long_flat(
        bars,
        strategy=s,
        settings=EmaBookSettings(equity_eur=200.0, fee_rate=0.0, slippage_bps=0.0),
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
    )
    buys = [px for side, px in seen if side == "buy"]
    assert buys, "expected at least one long entry"
    opens = {b.open for b in bars}
    assert all(px in opens for px in buys)
    assert 130.0 not in buys  # signal-bar close must not be a fill ref


def test_walk_never_goes_short_on_dump():
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    bars = [dbar(i, 200.0 - i * 5) for i in range(40)]
    row = walk_long_flat(
        bars,
        strategy=s,
        settings=EmaBookSettings(fee_rate=0.0, slippage_bps=0.0),
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
    )
    assert row["n_short_signals"] == 0
    assert row["n_entries"] == 0
    assert row["end_equity_eur"] == pytest.approx(200.0)


def test_empty_history_fail_closed():
    s = EmaTrendV1()
    with pytest.raises(ReplayError, match="empty"):
        walk_long_flat(
            [],
            strategy=s,
            settings=EmaBookSettings(),
            trade_start_ms=0,
            trade_end_ms=1,
        )


def test_buy_and_hold_benchmark_uses_costs():
    bars = [dbar(i, 100.0 + i) for i in range(5)]
    bh = buy_and_hold(bars, settings=EmaBookSettings(fee_rate=0.001, slippage_bps=10.0))
    assert bh["n_trades"] == 1
    assert bh["fee_drag_eur"] > 0
    assert bh["time_in_market"] == 1.0


def test_run_ema_eval_injected_bars_no_okx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = load_config()

    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    win = parse_windows_arg("2020-09")[0]
    bars = []
    t0 = win.start_ms - 40 * DAY
    px = 10000.0
    n = int((win.end_ms_exclusive - (win.start_ms - 40 * DAY)) / DAY)
    for i in range(n):
        px = px * 1.002  # slow grind up so EMA12 > EMA30 after warmup
        ts = t0 + i * DAY
        bars.append(Bar(SYM, ts, ts + DAY, px, px + 10, px - 10, px, 1.0, True, "test"))
    bundle = run_ema_eval(
        cfg,
        asset=SYM,
        windows="2020-09",
        data_dir=tmp_path,
        neighbors=False,
        bars_by_window={"2020-09": bars},
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert bundle["samples"][0]["ok"] is True
    assert bundle["samples"][0]["holdout"]["n_short_signals"] == 0
    assert (tmp_path / "reports" / "ema_BTC-USDT_2020-09.json").is_file()
    assert bundle["interesting"]["not_a_pass_vs_breakout"] is True


def test_interesting_bar_requires_both_windows():
    def sample(sid, ret, dd, bh_dd):
        return {
            "ok": True,
            "sample_id": sid,
            "holdout": {
                "net_return_eur": ret,
                "max_dd_eur": dd,
                "buy_and_hold": {"max_dd_eur": bh_dd},
            },
        }

    a = interesting_bar(
        [
            sample("2020-09", 10.0, 20.0, 50.0),
            sample("2023-09", 5.0, 10.0, 40.0),
        ]
    )
    assert a["cleared"] is True
    b = interesting_bar(
        [
            sample("2020-09", 10.0, 20.0, 50.0),
            sample("2023-09", -1.0, 10.0, 40.0),
        ]
    )
    assert b["cleared"] is False
    c = interesting_bar(
        [
            sample("2020-09", 10.0, 80.0, 50.0),
            sample("2023-09", 5.0, 10.0, 40.0),
        ]
    )
    assert c["cleared"] is False


def test_eval_page_shows_ema_holdout_without_pnl_hero(tmp_path: Path):
    app = create_app(data_dir=tmp_path)
    app.state.reports_dir = tmp_path / "reports"
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "ema_BTC-USDT_2020-09.json").write_text(
        json.dumps(
            {
                "ok": True,
                "source": "ema-long-flat",
                "sample_id": "2020-09",
                "symbol": "BTC-USDT",
                "strategy": "ema_long_flat_v1_12_30",
                "md_label": "fixture",
                "holdout": {
                    "n_trades": 3,
                    "net_return_eur": 4.2,
                    "max_dd_eur": 12.0,
                    "time_in_market": 0.4,
                    "buy_and_hold": {"max_dd_eur": 40.0},
                },
            }
        ),
        encoding="utf-8",
    )
    html = TestClient(app).get("/eval").text
    assert "ema_long_flat" in html
    assert "2020-09" in html
    assert "PnL hero" not in html
    assert "would have made" not in html.lower()


def test_empty_injected_window_skips():
    cfg = load_config()
    bundle = run_ema_eval(
        cfg,
        asset=SYM,
        windows="2020-09",
        data_dir=Path("/tmp/ema-empty-test"),
        neighbors=False,
        bars_by_window={"2020-09": []},
    )
    assert bundle["samples"][0]["ok"] is False
    assert "empty" in str(bundle["samples"][0].get("error") or "").lower()
    assert bundle["place_orders"] is False


def _full_sample(sid: str, ret: float, dd: float, bh_ret: float, bh_dd: float) -> dict:
    return {
        "ok": True,
        "sample_id": sid,
        "full": {
            "net_return_eur": ret,
            "max_dd_eur": dd,
            "n_trades": 2,
            "buy_and_hold": {"net_return_eur": bh_ret, "max_dd_eur": bh_dd},
        },
    }


def test_oos_stress_bar_bear_and_chop_rules():
    clear = oos_stress_bar(
        [
            _full_sample("2022-bear", -40.0, 80.0, -100.0, 120.0),
            _full_sample("2023-chop", 5.0, 30.0, 10.0, 40.0),
        ]
    )
    assert clear["verdict"] == "CLEAR"
    assert clear["per_window"]["2022-bear"]["cleared"] is True
    assert clear["per_window"]["2023-chop"]["cleared"] is True
    # bear return not better than BH
    fail_bear = oos_stress_bar(
        [
            _full_sample("2022-bear", -110.0, 80.0, -100.0, 120.0),
            _full_sample("2023-chop", 5.0, 30.0, 10.0, 40.0),
        ]
    )
    assert fail_bear["verdict"] == "NOT CLEAR"
    # chop negative and not better than BH
    fail_chop = oos_stress_bar(
        [
            _full_sample("2022-bear", -40.0, 80.0, -100.0, 120.0),
            _full_sample("2023-chop", -20.0, 50.0, -10.0, 40.0),
        ]
    )
    assert fail_chop["verdict"] == "NOT CLEAR"
    # missing window fail closed
    missing = oos_stress_bar([_full_sample("2022-bear", -40.0, 80.0, -100.0, 120.0)])
    assert missing["verdict"] == "NOT CLEAR"


def test_thin_window_skips_holdout(tmp_path: Path):
    cfg = load_config()
    win = parse_windows_arg("2022-h1")[0]
    bars = []
    t0 = win.start_ms
    for i in range(25):  # < 60 full bars → holdout skipped
        ts = t0 + i * DAY
        px = 100.0 + i
        bars.append(Bar(SYM, ts, ts + DAY, px, px + 1, px - 1, px, 1.0, True, "test"))
    bundle = run_ema_eval(
        cfg,
        asset=SYM,
        windows="2022-h1",
        data_dir=tmp_path,
        neighbors=False,
        bars_by_window={"2022-h1": bars},
    )
    row = bundle["samples"][0]
    assert row["ok"] is True
    assert row["split"]["holdout_skipped"] is True
    assert row["holdout"] is None
    assert bundle["place_orders"] is False
