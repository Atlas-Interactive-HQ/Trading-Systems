"""live20 dashboard: parse fills, chart route 200, no trade client on the view path."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atlas.dashboard.app import create_app
from atlas.dashboard.live20_view import (
    LOCKED_INST,
    build_live20_page,
    derive_fills,
    journal_net_doge,
    load_live20_events,
    svg_price_chart,
)
from atlas.paper.md import bar_ms, okx_bar
from atlas.paper.types import Bar

DAY = 24 * 60 * 60 * 1000
ROOT = Path(__file__).resolve().parents[2]


def _write_events(tmp: Path) -> Path:
    day = tmp / "2026-09-04"
    day.mkdir(parents=True)
    rows = [
        {
            "source": "live20-roundtrip",
            "kind": "session_start",
            "instId": "DOGE-USDC",
            "ts_ms": 1788480000000,
            "seq": 1,
        },
        {
            "source": "live20-roundtrip",
            "kind": "intent",
            "side": "sell",
            "instId": "DOGE-USDC",
            "sz": "50",
            "px": 0.12,
            "ts_ms": 1788480001000,
            "seq": 2,
        },
        {
            "source": "live20-roundtrip",
            "kind": "sell_poll",
            "state": "filled",
            "side": "sell",
            "ordId": "SELL1",
            "avgPx": "0.119",
            "accFillSz": "50",
            "fee": "-0.001",
            "feeCcy": "USDC",
            "instId": "DOGE-USDC",
            "ts_ms": 1788480002000,
            "seq": 3,
        },
        {
            "source": "live20-roundtrip",
            "kind": "buy_poll",
            "state": "filled",
            "side": "buy",
            "ordId": "BUY1",
            "avgPx": "0.121",
            "accFillSz": "49",
            "fee": "-0.05",
            "feeCcy": "DOGE",
            "instId": "DOGE-USDC",
            "ts_ms": 1788480060000,
            "seq": 4,
        },
        {
            "source": "live20-roundtrip",
            "kind": "buy_poll",
            "state": "live",
            "avgPx": "0.5",
            "ts_ms": 1788480061000,
            "seq": 5,
        },
    ]
    (day / "events.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )
    return tmp


def test_okx_5m_bar_supported():
    assert okx_bar("5m") == "5m"
    assert bar_ms("5m") == 5 * 60 * 1000


def test_derive_fills_from_journals(tmp_path: Path):
    root = _write_events(tmp_path)
    events = load_live20_events(root)
    fills = derive_fills(events)
    assert len(fills) == 2
    assert fills[0].side == "sell" and fills[0].px == 0.119
    assert fills[1].side == "buy" and fills[1].px == 0.121
    assert fills[0].ord_id == "SELL1"
    net = journal_net_doge(fills)
    assert net == pytest.approx(-1.0)


def test_net_doge_sell_then_partial_buy():
    from atlas.dashboard.live20_view import Live20Fill

    fills = [
        Live20Fill(1, None, "sell", 0.12, 50.0, "a", None, None, LOCKED_INST, "sell_poll"),
        Live20Fill(2, None, "buy", 0.12, 49.0, "b", None, None, LOCKED_INST, "buy_poll"),
    ]
    assert journal_net_doge(fills) == -1.0


def test_svg_includes_fill_lines():
    bars = [
        Bar("DOGE-USDC", 1000 + i * 300_000, 1000 + (i + 1) * 300_000, 0.12, 0.13, 0.11, 0.12 + i * 0.0001, 1.0, True, "test")
        for i in range(8)
    ]
    from atlas.dashboard.live20_view import Live20Fill

    fills = [Live20Fill(1, None, "sell", 0.119, 50.0, "S", None, None, LOCKED_INST, "sell_poll")]
    svg = svg_price_chart(bars, fills)
    assert "live20-price" in svg
    assert "live20-fill-sell" in svg
    assert "sell 0.119" in svg


def test_chart_route_200_with_sample_events_no_invented_md(tmp_path: Path, monkeypatch):
    root = _write_events(tmp_path)

    def boom(*_a, **_k):
        raise AssertionError("must not hit network")

    monkeypatch.setattr("atlas.dashboard.live20_view.fetch_okx_candles", boom)
    view = build_live20_page(root, skip_fetch=True, bars=[], md_error="fail closed")
    assert view["n_fills"] == 2
    assert view["svg"] == ""
    assert view["place_orders"] is False

    app = create_app(data_dir=root, use_live20=True)
    app.state.live20_dir = root

    def no_fetch(inst, *, cache_root, **_k):
        return [], "offline"

    monkeypatch.setattr("atlas.dashboard.live20_view.load_public_candles", no_fetch)
    html = TestClient(app).get("/live20")
    assert html.status_code == 200
    assert "DOGE-USDC" in html.text
    assert "0.119" in html.text
    assert "SELL1" in html.text
    assert "geen orders" in html.text.lower() or "plaatst geen orders" in html.text.lower()
    assert "OkxEeaClient" not in html.text


def test_live20_view_source_has_no_trade_client():
    src = (ROOT / "src" / "atlas" / "dashboard" / "live20_view.py").read_text(encoding="utf-8")
    assert "OkxEeaClient" not in src
    assert "allow_trade" not in src


def test_cli_live20_exclusive():
    from atlas.dashboard.cli import main

    with pytest.raises(SystemExit, match="kies één"):
        main(["--live20", "--ema"])
