"""EMA paper observer: flat not short, no lookahead, journal schema, no trade client."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atlas.common.config import load_config
from atlas.dashboard.app import create_app
from atlas.dashboard.reader import load_snapshot
from atlas.okx.client import OkxEeaClient
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.ema_observer import (
    EMA_OBSERVER_SOURCE,
    KIND_DECISION,
    KIND_FILL,
    KIND_STATE,
    advance_shadow,
    closed_bars_only,
    default_ledger,
    ema_root,
    run_ema_paper_session,
    snapshot_from_bars,
)
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

DAY = 24 * 60 * 60 * 1000
START = 1_704_067_200_000  # 2024-01-01 UTC
SYM = "BTC-USDT"
ROOT = Path(__file__).resolve().parents[2]


def dbar(i: int, c: float, o: float | None = None, *, closed: bool = True) -> Bar:
    ts = START + i * DAY
    ox = c if o is None else o
    hi = max(ox, c) + 0.5
    lo = min(ox, c) - 0.5
    return Bar(SYM, ts, ts + DAY, ox, hi, lo, c, 1.0, closed, "test")


def rising(n: int = 50) -> list[Bar]:
    px = 10000.0
    out: list[Bar] = []
    for i in range(n):
        px = px * 1.01
        out.append(dbar(i, px, o=px * 0.999))
    return out


def falling(n: int = 50) -> list[Bar]:
    px = 20000.0
    out: list[Bar] = []
    for i in range(n):
        px = px * 0.99
        out.append(dbar(i, px, o=px * 1.001))
    return out


def test_observer_flat_not_short_on_dump(tmp_path: Path):
    cfg = load_config()
    public = run_ema_paper_session(cfg, data_dir=tmp_path, bars=falling(), paper_shadow=True)
    assert public["desired"] == FLAT
    assert public["place_orders"] is False
    assert public["source"] == EMA_OBSERVER_SOURCE
    ledger = json.loads((tmp_path / "ema" / "state.json").read_text(encoding="utf-8"))
    assert ledger["pending"] in (None, FLAT)
    assert float(ledger["qty"]) == 0.0
    assert ledger.get("have") == FLAT


def test_desired_state_never_emits_short():
    s = EmaTrendV1(EmaTrendParams(fast=12, slow=30))
    snap = snapshot_from_bars(falling(), s)
    assert snap["desired"] == FLAT
    assert snap["desired"] != "short"


def test_no_lookahead_fill_at_next_open(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    seen: list[tuple[str, float]] = []

    def spy(price: float, buy_sell: str, slippage_bps: float) -> float:
        seen.append((buy_sell, float(price)))
        return float(price)

    monkeypatch.setattr("atlas.paper.ema_observer.apply_slippage", spy)
    cfg = load_config()
    bars = rising(45)
    # First session: last closed bar signals; no fill yet (next-open).
    first = run_ema_paper_session(
        cfg, data_dir=tmp_path, bars=bars[:-1], paper_shadow=True, run_id="ema-a"
    )
    assert first["n_fills"] == 0
    assert first["hypothetical_ledger"]["pending"] == LONG
    signal_close = bars[-2].close
    next_open = bars[-1].open
    assert signal_close != next_open
    second = run_ema_paper_session(
        cfg, data_dir=tmp_path, bars=bars, paper_shadow=True, run_id="ema-b"
    )
    assert second["n_fills"] == 1
    buys = [px for side, px in seen if side == "buy"]
    assert buys == [next_open]
    assert signal_close not in buys


def test_idempotent_same_last_bar_no_double_fill(tmp_path: Path):
    cfg = load_config()
    bars = rising(45)
    run_ema_paper_session(cfg, data_dir=tmp_path, bars=bars, paper_shadow=True, run_id="ema-1")
    again = run_ema_paper_session(
        cfg, data_dir=tmp_path, bars=bars, paper_shadow=True, run_id="ema-2"
    )
    assert again["n_fills"] == 0


def test_default_mode_no_ledger(tmp_path: Path):
    cfg = load_config()
    public = run_ema_paper_session(cfg, data_dir=tmp_path, bars=rising(), paper_shadow=False)
    assert public["paper_shadow"] is False
    assert (tmp_path / "ema" / "state.json").is_file() is False
    assert public["journals"]["state"] is None
    assert "hypothetical_ledger" not in public


def test_journals_under_data_ema_not_oms_or_shadow(tmp_path: Path):
    cfg = load_config()
    public = run_ema_paper_session(cfg, data_dir=tmp_path, bars=rising())
    root = Path(public["journals"]["root"])
    assert root == tmp_path / "ema"
    assert ema_root(tmp_path) == root
    decisions = Path(public["journals"]["decisions"])
    assert "oms" not in decisions.parts
    assert "shadow" not in decisions.parts
    assert decisions.parent.parent == root
    assert (tmp_path / "oms").exists() is False
    assert (tmp_path / "shadow").exists() is False
    lines = decisions.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[0])
    assert row["source"] == EMA_OBSERVER_SOURCE
    assert row["kind"] in (KIND_DECISION, KIND_STATE)
    assert row["place_orders"] is False
    assert row["not_a_forecast"] is True
    assert row["desired"] in (LONG, FLAT)
    assert "ema_fast" in row and "ema_slow" in row
    assert "last_close" in row
    assert "as_of_bar_ts_open_ms" in row
    assert row["desired"] != "short"


def test_journal_schema_and_session_events(tmp_path: Path):
    cfg = load_config()
    public = run_ema_paper_session(cfg, data_dir=tmp_path, bars=rising())
    events = Path(public["journals"]["events"])
    kinds = [json.loads(line)["kind"] for line in events.read_text(encoding="utf-8").splitlines()]
    assert "ema_paper_session_start" in kinds
    assert "ema_paper_session_end" in kinds
    for line in events.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        assert row["source"] == EMA_OBSERVER_SOURCE
        assert row["place_orders"] is False
        assert row["not_a_forecast"] is True


def test_no_trade_client_constructed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    cfg = load_config()
    public = run_ema_paper_session(cfg, data_dir=tmp_path, bars=rising())
    assert public["ok"] is True
    assert public["place_orders"] is False


def test_observer_source_files_have_no_trade_client():
    obs = (ROOT / "src" / "atlas" / "paper" / "ema_observer.py").read_text(encoding="utf-8")
    script = (ROOT / "scripts" / "run_ema_paper_session.py").read_text(encoding="utf-8")
    assert "OkxEeaClient" not in obs
    assert "OkxEeaClient" not in script
    assert "place-demo-orders" not in script
    assert "allow_trade" not in script


def test_open_bar_dropped_from_snapshot():
    bars = rising(40)
    open_last = dbar(40, 20000.0, closed=False)
    mixed = bars + [open_last]
    closed = closed_bars_only(mixed)
    assert open_last not in closed
    snap = snapshot_from_bars(mixed, EmaTrendV1())
    assert snap["as_of_bar_ts_open_ms"] == bars[-1].ts_open_ms


def test_advance_shadow_never_shorts():
    s = EmaTrendV1()
    settings = EmaBookSettings(fee_rate=0.0, slippage_bps=0.0)
    ledger = default_ledger(settings, symbol=SYM)
    ledger["pending"] = LONG
    bars = falling(40)
    fills = advance_shadow(bars, ledger, s, settings)
    assert all(f.get("side") in ("buy", "sell") for f in fills)
    assert ledger["qty"] == 0.0 or ledger["have"] == LONG
    assert ledger.get("pending") != "short"
    assert float(ledger["qty"]) >= 0.0


def test_dashboard_ema_mode_no_pnl_hero(tmp_path: Path):
    cfg = load_config()
    run_ema_paper_session(cfg, data_dir=tmp_path, bars=rising(), run_id="ema-ui")
    ema_dir = tmp_path / "ema"
    snap = load_snapshot(ema_dir, cfg=cfg, using_ema=True)
    assert snap.using_ema is True
    assert snap.overview.mode == "ema-paper-observer"
    assert snap.overview.paper_pnl is None
    assert snap.overview.ema_desired in (LONG, FLAT)
    assert snap.signals
    assert snap.signals[0].side in (LONG, FLAT)
    html = TestClient(create_app(data_dir=ema_dir, use_ema=True)).get("/").text
    assert "EMA observer" in html or "ema" in html.lower()
    assert "PnL hero" not in html
    assert "would have made" not in html.lower()
    eval_html = TestClient(create_app(data_dir=ema_dir, use_ema=True)).get("/eval").text
    assert "EMA paper observer" in eval_html
    assert "PnL hero" not in eval_html
    assert "geen orders" in eval_html.lower() or "Geen orders" in eval_html


def test_cli_ema_exclusive_with_replay():
    from atlas.dashboard.cli import main

    with pytest.raises(SystemExit, match="kies één"):
        main(["--ema", "--replay"])
    with pytest.raises(SystemExit, match="kies één"):
        main(["--ema", "--oms"])
    with pytest.raises(SystemExit, match="kies één"):
        main(["--ema", "--shadow"])


def test_fill_kind_tagged_hypothetical(tmp_path: Path):
    cfg = load_config()
    bars = rising(45)
    run_ema_paper_session(cfg, data_dir=tmp_path, bars=bars[:-1], paper_shadow=True, run_id="a")
    public = run_ema_paper_session(cfg, data_dir=tmp_path, bars=bars, paper_shadow=True, run_id="b")
    assert public["n_fills"] == 1
    events = Path(public["journals"]["events"])
    fills = [
        json.loads(line)
        for line in events.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("kind") == KIND_FILL
    ]
    assert fills
    assert fills[0]["hypothetical"] is True
    assert fills[0]["place_orders"] is False
    assert fills[0]["reason"] == "next_open"
    assert fills[0]["ref_price"] == q(bars[-1].open)
