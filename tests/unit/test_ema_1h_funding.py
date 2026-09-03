"""1H EMA long/flat + funding: no lookahead, never short, incomplete flagged."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atlas.common.config import load_config
from atlas.dashboard.app import create_app
from atlas.okx.client import OkxEeaClient
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.ema_1h_eval import (
    EMA_1H_SOURCE,
    FUNDING_INTERVAL_MS,
    bull_holdout_bar,
    buy_and_hold_1h,
    oos_stress_bar_1h,
    run_ema_1h_eval,
    walk_long_flat_1h,
)
from atlas.paper.md import FUNDING_INTERVAL_MS as MD_INTERVAL
from atlas.paper.md import parse_okx_funding_row
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

HOUR = 60 * 60 * 1000
START = 1_704_067_200_000  # 2024-01-01 00:00 UTC (8h-aligned)
SYM = "BTC-USDT-SWAP"


def hbar(i: int, c: float, o: float | None = None) -> Bar:
    ts = START + i * HOUR
    ox = c if o is None else o
    hi = max(ox, c) + 0.5
    lo = min(ox, c) - 0.5
    return Bar(SYM, ts, ts + HOUR, ox, hi, lo, c, 1.0, True, "test")


def test_funding_interval_matches_md():
    assert FUNDING_INTERVAL_MS == MD_INTERVAL == 8 * HOUR


def test_parse_funding_row_uses_realized_not_invented():
    row = parse_okx_funding_row(
        {
            "instId": SYM,
            "fundingTime": str(START),
            "realizedRate": "0.0001",
            "fundingRate": "0.0002",
        },
        symbol=SYM,
    )
    assert row is not None
    assert row["realizedRate"] == pytest.approx(0.0001)
    assert parse_okx_funding_row({"fundingTime": START}, symbol=SYM) is None
    assert parse_okx_funding_row({"fundingTime": START, "realizedRate": "nope"}, symbol=SYM) is None


def test_1h_flat_not_short_on_dump():
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    bars = [hbar(i, 200.0 - i * 2) for i in range(40)]
    # funding prints exist; must not be applied while flat
    funding = {START + k * FUNDING_INTERVAL_MS: 0.01 for k in range(8)}
    row = walk_long_flat_1h(
        bars,
        strategy=s,
        settings=EmaBookSettings(fee_rate=0.0, slippage_bps=0.0),
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
        funding_by_ts=funding,
    )
    assert row["n_short_signals"] == 0
    assert row["n_entries"] == 0
    assert row["n_funding_applied"] == 0
    assert row["funding_drag_eur"] == 0.0
    assert row["end_equity_eur"] == pytest.approx(200.0)
    assert s.desired_state(bars) == FLAT


def test_1h_signal_fills_next_open_not_same_bar_close(monkeypatch: pytest.MonkeyPatch):
    seen: list[tuple[str, float]] = []

    def spy(price: float, buy_sell: str, slippage_bps: float) -> float:
        seen.append((buy_sell, float(price)))
        return float(price)

    monkeypatch.setattr("atlas.paper.ema_1h_eval.apply_slippage", spy)
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    bars = [hbar(i, 100.0) for i in range(8)]
    bars.append(hbar(8, 130.0, o=100.0))
    bars.append(hbar(9, 131.0, o=101.0))
    bars += [hbar(i, 132.0) for i in range(10, 14)]
    walk_long_flat_1h(
        bars,
        strategy=s,
        settings=EmaBookSettings(equity_eur=200.0, fee_rate=0.0, slippage_bps=0.0),
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
        funding_by_ts={},
    )
    buys = [px for side, px in seen if side == "buy"]
    assert buys, "expected at least one long entry"
    opens = {b.open for b in bars}
    assert all(px in opens for px in buys)
    assert 130.0 not in buys


def test_funding_applied_only_while_long():
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    # grind up so we go long after warmup, stay long
    bars = [hbar(i, 100.0 + i) for i in range(24)]
    settings = EmaBookSettings(equity_eur=200.0, fee_rate=0.0, slippage_bps=0.0)
    none = walk_long_flat_1h(
        bars,
        strategy=s,
        settings=settings,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
        funding_by_ts={},
    )
    assert none["n_entries"] >= 1
    # 1% funding at every 8h open — only while qty>0
    funding = {START + k * FUNDING_INTERVAL_MS: 0.01 for k in range(4)}
    paid = walk_long_flat_1h(
        bars,
        strategy=s,
        settings=settings,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
        funding_by_ts=funding,
    )
    assert paid["n_funding_applied"] >= 1
    assert paid["funding_drag_eur"] > 0
    assert paid["end_equity_eur"] < none["end_equity_eur"]
    assert paid["n_short_signals"] == 0
    # negative rate while long → receive (drag negative / equity up)
    recv = walk_long_flat_1h(
        bars,
        strategy=s,
        settings=settings,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
        funding_by_ts={t: -0.01 for t in funding},
    )
    assert recv["funding_drag_eur"] < 0
    assert recv["end_equity_eur"] > none["end_equity_eur"]


def test_incomplete_funding_flagged_not_invented():
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    bars = [hbar(i, 100.0 + i) for i in range(24)]
    settings = EmaBookSettings(equity_eur=200.0, fee_rate=0.0, slippage_bps=0.0)
    row = walk_long_flat_1h(
        bars,
        strategy=s,
        settings=settings,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
        funding_by_ts={},  # no prints at all
    )
    assert row["n_entries"] >= 1
    assert row["n_funding_missing"] >= 1
    assert row["funding_incomplete"] is True
    assert row["n_funding_applied"] == 0
    assert row["funding_drag_eur"] == 0.0


def test_complete_funding_not_flagged_when_all_prints_present():
    s = EmaTrendV1(EmaTrendParams(fast=3, slow=5))
    bars = [hbar(i, 100.0 + i) for i in range(24)]
    settings = EmaBookSettings(equity_eur=200.0, fee_rate=0.0, slippage_bps=0.0)
    # dense 8h prints covering the whole span
    funding = {START + k * FUNDING_INTERVAL_MS: 0.0001 for k in range(6)}
    row = walk_long_flat_1h(
        bars,
        strategy=s,
        settings=settings,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
        funding_by_ts=funding,
    )
    assert row["n_funding_missing"] == 0
    assert row["funding_incomplete"] is False
    assert row["n_funding_applied"] == row["n_funding_expected_while_long"]


def test_bh_funding_always_long_incomplete_without_prints():
    bars = [hbar(i, 100.0 + i) for i in range(16)]
    settings = EmaBookSettings(fee_rate=0.0, slippage_bps=0.0)
    bh = buy_and_hold_1h(bars, settings=settings, funding_by_ts={})
    assert bh["time_in_market"] == 1.0
    assert bh["funding_incomplete"] is True
    assert bh["n_funding_missing"] >= 1


def test_run_eval_injected_no_okx_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    cfg = load_config()
    win2 = parse_windows_arg("2022-h1")[0]
    t1 = (win2.start_ms // HOUR) * HOUR - 40 * HOUR
    bars2 = []
    px = 10000.0
    for i in range(200):
        px = px * 1.001
        ts = t1 + i * HOUR
        bars2.append(Bar(SYM, ts, ts + HOUR, px, px + 10, px - 10, px, 1.0, True, "test"))
    bundle = run_ema_1h_eval(
        cfg,
        asset=SYM,
        windows="2022-h1",
        data_dir=tmp_path,
        bars_by_window={"2022-h1": bars2},
        funding_rows=[],
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert bundle["source"] == EMA_1H_SOURCE
    assert bundle["samples"][0]["ok"] is True
    full = bundle["samples"][0]["full"]
    assert full["funding_incomplete"] is True
    assert full["decision_costs"] == "fee_slip_only"
    assert (tmp_path / "reports" / f"ema1h_{SYM}_2022-h1.json").is_file()


def test_bull_and_oos_bars_plain_verdict():
    bull = bull_holdout_bar(
        [
            {
                "ok": True,
                "sample_id": "2020-09",
                "holdout": {"net_return_eur": 1.0, "funding_incomplete": True},
            },
            {
                "ok": True,
                "sample_id": "2023-09",
                "holdout": {"net_return_eur": 2.0, "funding_incomplete": True},
            },
        ]
    )
    assert bull["verdict"] == "CLEAR"
    fail = bull_holdout_bar(
        [
            {
                "ok": True,
                "sample_id": "2020-09",
                "holdout": {"net_return_eur": -1.0},
            },
            {
                "ok": True,
                "sample_id": "2023-09",
                "holdout": {"net_return_eur": 2.0},
            },
        ]
    )
    assert fail["verdict"] == "NOT CLEAR"

    oos = oos_stress_bar_1h(
        [
            {
                "ok": True,
                "sample_id": "2022-bear",
                "full": {
                    "net_return_eur": -40.0,
                    "max_dd_eur": 80.0,
                    "buy_and_hold": {"net_return_eur": -100.0, "max_dd_eur": 120.0},
                },
            },
            {
                "ok": True,
                "sample_id": "2023-chop",
                "full": {
                    "net_return_eur": 5.0,
                    "max_dd_eur": 30.0,
                    "buy_and_hold": {"net_return_eur": 10.0, "max_dd_eur": 40.0},
                },
            },
        ]
    )
    assert oos["verdict"] == "CLEAR"


def test_eval_page_shows_1h_note_without_pnl_hero(tmp_path: Path):
    app = create_app(data_dir=tmp_path)
    app.state.reports_dir = tmp_path / "reports"
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "ema1h_BTC-USDT-SWAP_2022-bear.json").write_text(
        json.dumps(
            {
                "ok": True,
                "source": EMA_1H_SOURCE,
                "sample_id": "2022-bear",
                "symbol": SYM,
                "strategy": "ema_long_flat_v1_12_30",
                "bar": "1H",
                "full": {
                    "n_trades": 2,
                    "net_return_eur": -4.2,
                    "net_return_fee_only_eur": -4.2,
                    "funding_incomplete": True,
                    "max_dd_eur": 12.0,
                    "buy_and_hold": {"net_return_eur": -10.0, "max_dd_eur": 20.0},
                },
            }
        ),
        encoding="utf-8",
    )
    html = TestClient(app).get("/eval").text
    assert "1H" in html
    assert "funding" in html.lower()
    assert "PnL hero" not in html
    assert "would have made" not in html.lower()


def test_source_files_have_no_trade_client():
    root = Path(__file__).resolve().parents[2]
    mod = (root / "src" / "atlas" / "paper" / "ema_1h_eval.py").read_text(encoding="utf-8")
    script = (root / "scripts" / "run_ema_1h_funding_eval.py").read_text(encoding="utf-8")
    assert "OkxEeaClient" not in mod
    assert "OkxEeaClient" not in script
    assert "place-demo-orders" not in script
