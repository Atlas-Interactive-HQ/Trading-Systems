"""Dashboard v0: read-only journals, empty-state, no secrets, no orders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atlas.common.config import load_config
from atlas.dashboard.app import create_app
from atlas.dashboard.reader import bundled_fixtures_dir, load_snapshot, redact

ROOT = Path(__file__).resolve().parents[2]


def test_redact_masks_secret_keys():
    raw = {
        "api_key": "SUPERSECRETKEYVALUE",
        "nested": {"passphrase": "SUPERSECRETPASSPHRASE", "side": "long"},
        "ok-access-sign": "abc",
    }
    out = redact(raw)
    assert out["api_key"] == "***"
    assert out["nested"]["passphrase"] == "***"
    assert out["nested"]["side"] == "long"
    assert out["ok-access-sign"] == "***"
    blob = json.dumps(out)
    assert "SUPERSECRET" not in blob


def test_empty_journals_boot(tmp_path: Path):
    snap = load_snapshot(tmp_path, cfg=load_config())
    assert snap.overview.empty is True
    assert snap.overview.paper_equity_eur == 200.0
    assert snap.overview.mode == "idle"
    assert snap.overview.killed is False
    assert snap.oms.empty is True
    assert snap.signals == []
    assert snap.health.secrets_loaded is False
    ids = {i.id: i.status for i in snap.health.items}
    assert ids["live_blocked"] == "ok"
    assert ids["secrets"] == "ok"
    assert ids["journals"] == "warn"
    assert snap.health.status in {"ok", "warn"}
    assert snap.health.status != "fail"


def test_fixtures_snapshot_has_spot_and_xperp():
    snap = load_snapshot(bundled_fixtures_dir(), cfg=load_config(), using_fixtures=True)
    assert snap.overview.empty is False
    assert snap.overview.mode == "signal-only"
    assert snap.overview.mode_label == "alleen signalen"
    assert snap.overview.kill_status == "vrij"
    assert snap.overview.last_session_ok is True
    assert snap.latest_by_venue["spot"] is not None
    assert snap.latest_by_venue["xperp"] is not None
    assert snap.latest_by_venue["spot"].side == "long"
    assert snap.latest_by_venue["xperp"].side == "short"
    venues = {s.venue for s in snap.signals}
    assert "spot" in venues and "xperp" in venues
    assert any(r.kind == "skip" for r in snap.oms.orders)
    payload = json.dumps(snap.as_dict())
    assert "api_key" not in payload.lower() or "***" in payload
    assert "/home/box/agent-data" not in payload
    assert "SUPERSECRET" not in payload


def test_secret_in_journal_is_masked(tmp_path: Path):
    day = tmp_path / "oms" / "2026-09-02"
    day.mkdir(parents=True)
    (day / "decisions.jsonl").write_text(
        json.dumps(
            {
                "kind": "breakout_signal",
                "venue": "spot",
                "symbol": "DOGE-USD",
                "side": "long",
                "stop": 0.1,
                "reason": "breakout_long",
                "api_key": "SUPERSECRETKEYVALUE",
                "ts_ms": 1788350460000,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    snap = load_snapshot(tmp_path, cfg=load_config())
    blob = json.dumps(snap.as_dict())
    assert "SUPERSECRETKEYVALUE" not in blob
    assert snap.signals[0].side == "long"


def test_secret_filename_is_not_read(tmp_path: Path):
    oms = tmp_path / "oms" / "2026-09-02"
    oms.mkdir(parents=True)
    (oms / "okx-eea-demo.json").write_text(
        json.dumps({"api_key": "SUPERSECRETKEYVALUE", "kind": "breakout_signal"}),
        encoding="utf-8",
    )
    snap = load_snapshot(tmp_path, cfg=load_config())
    blob = json.dumps(snap.as_dict())
    assert "SUPERSECRETKEYVALUE" not in blob
    assert snap.signals == []


def test_live_allow_trade_fails_health(tmp_path: Path):
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(
        "okx:\n  modes:\n    live:\n      simulated_trading: false\n      allow_trade: true\n",
        encoding="utf-8",
    )
    snap = load_snapshot(tmp_path / "data", cfg=load_config(cfg_path))
    item = next(i for i in snap.health.items if i.id == "live_blocked")
    assert item.status == "fail"
    assert snap.health.status == "fail"


def test_app_empty_and_fixtures_routes():
    empty = create_app(data_dir=Path("/tmp/atlas-dashboard-empty-missing"), use_fixtures=False)
    c = TestClient(empty)
    r = c.get("/")
    assert r.status_code == 200
    assert "PAPER" in r.text
    assert "geen live" in r.text.lower() or "Geen live" in r.text or "geen live" in r.text
    assert "Nog geen journals" in r.text or "geen sessie" in r.text.lower() or "idle" in r.text.lower() or "Geen journals" in r.text or "leeg" in r.text.lower()

    app = create_app(use_fixtures=True)
    c = TestClient(app)
    for path in ("/", "/signals", "/oms", "/health"):
        resp = c.get(path)
        assert resp.status_code == 200, path
        assert "api_key" not in resp.text.lower() or "***" in resp.text
        assert "SUPERSECRET" not in resp.text
    sig = c.get("/signals")
    assert "DOGE-USD" in sig.text
    assert "xperp" in sig.text
    oms = c.get("/oms")
    assert "signal_only" in oms.text or "skip" in oms.text
    health = c.get("/api/health").json()
    assert health["secrets_loaded"] is False
    assert "/home/box/agent-data" not in json.dumps(health)
    snap = c.get("/api/snapshot").json()
    assert snap["overview"]["mode"] == "signal-only"
    assert snap["overview"]["paper_equity_eur"] == 200.0


def test_app_rejects_writes_and_has_no_order_routes():
    app = create_app(use_fixtures=True)
    c = TestClient(app)
    post = c.post("/oms", json={"place": True})
    assert post.status_code == 405
    assert post.json()["error"] == "read_only"
    missing = c.get("/trade/order")
    assert missing.status_code == 404
    paths = {getattr(r, "path", None) for r in app.routes}
    joined = " ".join(str(p) for p in paths)
    assert "place" not in joined
    assert "/order" not in joined


def test_replay_journals_mode(tmp_path: Path):
    day = tmp_path / "2026-09-02"
    day.mkdir()
    (day / "events.jsonl").write_text(
        json.dumps(
            {
                "kind": "historical_replay_end",
                "source": "historical-replay",
                "ok": True,
                "place_orders": False,
                "dry_run": True,
                "mode": "historical-replay",
                "run_id": "replay-ui",
                "ts_ms": 1788350580000,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (day / "decisions.jsonl").write_text(
        json.dumps(
            {
                "kind": "breakout_signal",
                "source": "historical-replay",
                "venue": "spot",
                "symbol": "DOGE-USD",
                "side": "long",
                "stop": 0.14,
                "reason": "donchian_break_up|oneh_ok",
                "ts_ms": 1788350460000,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    snap = load_snapshot(tmp_path, cfg=load_config(), using_replay=True)
    assert snap.overview.mode == "historical-replay"
    assert snap.using_replay is True
    assert snap.signals[0].venue == "spot"
    app = create_app(data_dir=tmp_path, use_replay=True)
    html = TestClient(app).get("/").text
    assert "historical-replay" in html
    assert "PAPER" in html


def test_shadow_journals_mode(tmp_path: Path):
    day = tmp_path / "2026-09-02"
    day.mkdir()
    (day / "events.jsonl").write_text(
        json.dumps(
            {
                "kind": "shadow_replay_end",
                "source": "shadow-replay",
                "ok": True,
                "place_orders": False,
                "n_would_place": 4,
                "n_blocked_by_reason": {"one_position": 12, "kill": 3, "no_signal": 80},
                "run_id": "shadow-ui",
                "ts_ms": 1788350580000,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (day / "decisions.jsonl").write_text(
        json.dumps(
            {
                "kind": "would_place",
                "source": "shadow-replay",
                "venue": "spot",
                "symbol": "DOGE-USD",
                "allowed": True,
                "place_orders": False,
                "ts_ms": 1788350460000,
            }
        )
        + "\n"
        + json.dumps(
            {
                "kind": "blocked",
                "blocked_reason": "one_position",
                "source": "shadow-replay",
                "venue": "spot",
                "ts_ms": 1788350470000,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    snap = load_snapshot(tmp_path, cfg=load_config(), using_shadow=True)
    assert snap.overview.mode == "shadow-replay"
    assert snap.overview.n_would_place == 4
    assert snap.overview.blocked_by.get("one_position") == 12
    html = TestClient(create_app(data_dir=tmp_path, use_shadow=True)).get("/").text
    assert "would-place" in html.lower() or "Would-place" in html
    assert "one_position=12" in html
    assert "€" in html  # paper scale, not a PnL hero from research


def test_named_window_journals_mode(tmp_path: Path):
    day = tmp_path / "2026-09-03"
    day.mkdir()
    (day / "events.jsonl").write_text(
        json.dumps(
            {
                "kind": "named_window_replay_end",
                "source": "named-window",
                "ok": True,
                "place_orders": False,
                "window_ids": ["2020-09", "2023-09"],
                "window_id": "2020-09,2023-09",
                "run_id": "named-ui",
                "ts_ms": 1788370000000,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    snap = load_snapshot(tmp_path, cfg=load_config(), using_replay=True)
    assert snap.overview.mode == "named-window"
    assert "2020-09" in snap.overview.named_window_ids
    html = TestClient(create_app(data_dir=tmp_path, use_replay=True)).get("/").text
    assert "named-window" in html
    assert "2020-09" in html


def test_static_css_and_no_docs():
    app = create_app(use_fixtures=True)
    c = TestClient(app)
    css = c.get("/static/app.css")
    assert css.status_code == 200
    assert "--surface-canvas" in css.text
    assert c.get("/docs").status_code == 404
    assert c.get("/openapi.json").status_code == 404
