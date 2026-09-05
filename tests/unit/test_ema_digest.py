"""EMA week digest: local journals only, fail closed if a dir is missing, no trade client."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.okx.client import OkxEeaClient
from atlas.paper.ema_digest import (
    DIGEST_SOURCE,
    render_ema_week_digest,
    run_ema_week_digest,
    summarize_observer_dir,
)
from atlas.paper.ema_observer import EMA_OBSERVER_SOURCE


def _write_observer(root: Path, *, desired: str, have: str, qty: float, close: float, days: list[str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    state = {
        "source": EMA_OBSERVER_SOURCE,
        "desired": desired,
        "have": have,
        "pending": None,
        "n_entries": 1 if qty > 0 else 0,
        "cash": 50.0 if qty > 0 else 200.0,
        "qty": qty,
        "last_close": close,
        "place_orders": False,
        "not_a_forecast": True,
        "paper_shadow": True,
    }
    (root / "state.json").write_text(json.dumps(state) + "\n", encoding="utf-8")
    for i, day in enumerate(days):
        d = root / day
        d.mkdir(parents=True, exist_ok=True)
        row = {
            "source": EMA_OBSERVER_SOURCE,
            "kind": "ema_decision",
            "desired": desired,
            "have": have,
            "last_close": close,
            "strategy": "ema_long_flat_v1_12_30",
            "fast": 12,
            "slow": 30,
            "ts_ms": 1_700_000_000_000 + i,
            "seq": 1,
            "place_orders": False,
            "not_a_forecast": True,
        }
        (d / "decisions.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")


def test_digest_compares_both_dirs(tmp_path: Path):
    _write_observer(
        tmp_path / "ema",
        desired="long",
        have="long",
        qty=0.002,
        close=100_000.0,
        days=["2026-09-01", "2026-09-02"],
    )
    _write_observer(
        tmp_path / "ema21",
        desired="flat",
        have="flat",
        qty=0.0,
        close=100_000.0,
        days=["2026-09-02"],
    )
    bundle = run_ema_week_digest(tmp_path)
    assert bundle["ok"] is True
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert bundle["source"] == DIGEST_SOURCE
    assert bundle["base"]["desired"] == "long"
    assert bundle["base"]["have"] == "long"
    assert bundle["base"]["n_entries"] == 1
    assert bundle["base"]["n_journal_days"] == 2
    assert bundle["base"]["hypo_mark_equity"] == pytest.approx(50.0 + 0.002 * 100_000.0)
    assert bundle["alt"]["desired"] == "flat"
    assert bundle["alt"]["have"] == "flat"
    assert bundle["alt"]["n_journal_days"] == 1
    assert bundle["alt"]["hypo_mark_equity"] == pytest.approx(200.0)
    text = render_ema_week_digest(bundle)
    assert "12/30" in text
    assert "12/21" in text
    assert "not_a_forecast" in text


def test_missing_ema21_fail_closed(tmp_path: Path):
    _write_observer(
        tmp_path / "ema",
        desired="long",
        have="long",
        qty=0.0,
        close=1.0,
        days=["2026-09-01"],
    )
    bundle = run_ema_week_digest(tmp_path)
    assert bundle["ok"] is False
    assert bundle["alt"]["ok"] is False
    assert "missing" in str(bundle["alt"].get("error") or "")
    assert bundle["place_orders"] is False


def test_missing_ema_fail_closed(tmp_path: Path):
    _write_observer(
        tmp_path / "ema21",
        desired="flat",
        have="flat",
        qty=0.0,
        close=1.0,
        days=["2026-09-01"],
    )
    bundle = run_ema_week_digest(tmp_path)
    assert bundle["ok"] is False
    assert bundle["base"]["ok"] is False


def test_no_trade_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    _write_observer(tmp_path / "ema", desired="flat", have="flat", qty=0.0, close=1.0, days=["2026-09-01"])
    _write_observer(tmp_path / "ema21", desired="flat", have="flat", qty=0.0, close=1.0, days=["2026-09-01"])
    bundle = run_ema_week_digest(tmp_path)
    assert bundle["ok"] is True


def test_source_files_have_no_trade_client():
    root = Path(__file__).resolve().parents[2]
    for rel in ("src/atlas/paper/ema_digest.py", "scripts/run_ema_week_digest.py"):
        text = (root / rel).read_text(encoding="utf-8")
        assert "OkxEeaClient" not in text
        assert "place-demo-orders" not in text
        assert "allow_trade" not in text


def test_cli_json_and_missing_exit(tmp_path: Path):
    import importlib.util

    path = Path(__file__).resolve().parents[2] / "scripts" / "run_ema_week_digest.py"
    spec = importlib.util.spec_from_file_location("run_ema_week_digest", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _write_observer(tmp_path / "ema", desired="flat", have="flat", qty=0.0, close=1.0, days=["2026-09-01"])
    _write_observer(tmp_path / "ema21", desired="long", have="flat", qty=0.0, close=1.0, days=["2026-09-01"])
    code = mod.main(["--data-dir", str(tmp_path), "--json"])
    assert code == 0
    code2 = mod.main(["--data-dir", str(tmp_path / "nope")])
    assert code2 == 2


def test_summarize_missing_dir(tmp_path: Path):
    row = summarize_observer_dir(tmp_path / "ghost", label="12/30")
    assert row["ok"] is False
