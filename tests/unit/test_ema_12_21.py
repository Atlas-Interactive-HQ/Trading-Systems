"""EMA 12/21 vs 12/30 compare: not a new default, docs-only bars, no trade client."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.okx.client import OkxEeaClient
from atlas.paper.ema_12_21 import COMPARE_SOURCE, render_ema_12_21_markdown, run_ema_12_21_compare
from atlas.paper.ema_observer import ema_root, run_ema_paper_session
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.types import Bar
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

DAY = 24 * 60 * 60 * 1000
START = 1_598_918_400_000
SYM = "BTC-USDT"


def dbar(i: int, c: float) -> Bar:
    ts = START + i * DAY
    return Bar(SYM, ts, ts + DAY, c, c + 0.5, c - 0.5, c, 1.0, True, "test")


def test_12_21_label_and_warmup_not_30():
    s = EmaTrendV1(EmaTrendParams(fast=12, slow=21))
    assert s.label == "ema_long_flat_v1_12_21"
    assert s.warmup_bars() == 21
    bars = [dbar(i, 100.0 + i) for i in range(20)]
    assert s.desired_state(bars) == FLAT  # need 21 closes
    bars.append(dbar(20, 121.0))
    assert s.desired_state(bars) in (LONG, FLAT)


def test_12_21_never_short_on_dump():
    s = EmaTrendV1(EmaTrendParams(fast=12, slow=21))
    falling = [dbar(i, 200.0 - i) for i in range(40)]
    assert s.desired_state(falling) == FLAT


def test_compare_injected_no_okx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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
        bars.append(Bar(SYM, ts, ts + DAY, px * 0.999, px + 10, px - 10, px, 1.0, True, "test"))
    bundle = run_ema_12_21_compare(
        cfg,
        asset=SYM,
        windows="2022-h1",
        data_dir=tmp_path,
        bars_by_window={"2022-h1": bars},
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert bundle["docs_only"] is True
    assert bundle["do_not_promote"] is True
    assert bundle["source"] == COMPARE_SOURCE
    assert bundle["base"]["slow"] == 30
    assert bundle["alt"]["slow"] == 21
    assert bundle["interesting_12_21"]["do_not_promote"] is True
    assert bundle["oos_12_21"]["docs_only"] is True
    assert (tmp_path / "reports" / f"ema_compare_12_21_{SYM}_2022-h1.json").is_file()
    assert (tmp_path / "reports" / f"ema_compare_12_30_{SYM}_2022-h1.json").is_file()
    # must not clobber the 12/30 eval report name used by PR #11
    assert not (tmp_path / "reports" / f"ema_{SYM}_2022-h1.json").exists()


def test_observer_default_still_12_30_under_ema(tmp_path: Path):
    cfg = load_config()
    bars = [dbar(i, 100.0 + i * 0.5) for i in range(40)]
    public = run_ema_paper_session(cfg, data_dir=tmp_path, bars=bars)
    assert public["strategy"] == "ema_long_flat_v1_12_30"
    assert Path(public["journals"]["root"]) == tmp_path / "ema"
    decisions = Path(public["journals"]["decisions"])
    row = json.loads(decisions.read_text(encoding="utf-8").splitlines()[0])
    assert row["reason"] in ("ema12_gt_ema30", "ema12_le_ema30_flat")
    assert row.get("fast") == 12
    assert row.get("slow") == 30


def test_observer_12_21_can_use_ema21_subdir(tmp_path: Path):
    cfg = load_config()
    bars = [dbar(i, 100.0 + i * 0.5) for i in range(40)]
    public = run_ema_paper_session(
        cfg, data_dir=tmp_path, bars=bars, fast=12, slow=21, journal_subdir="ema21"
    )
    assert public["strategy"] == "ema_long_flat_v1_12_21"
    assert Path(public["journals"]["root"]) == tmp_path / "ema21"
    assert ema_root(tmp_path, "ema21") == tmp_path / "ema21"
    assert (tmp_path / "ema").exists() is False
    decisions = Path(public["journals"]["decisions"])
    row = json.loads(decisions.read_text(encoding="utf-8").splitlines()[0])
    assert row["reason"] in ("ema12_gt_ema21", "ema12_le_ema21_flat")
    assert row.get("fast") == 12
    assert row.get("slow") == 21


def test_ema_root_rejects_path_separators(tmp_path: Path):
    assert ema_root(tmp_path, "ema/../oms") == tmp_path / "ema"
    assert ema_root(tmp_path, "..") == tmp_path / "ema"
    assert ema_root(tmp_path, "") == tmp_path / "ema"


def test_markdown_docs_only_do_not_promote():
    md = render_ema_12_21_markdown(
        {
            "base": {"strategy": "ema_long_flat_v1_12_30"},
            "alt": {"strategy": "ema_long_flat_v1_12_21"},
            "interesting_12_30": {"cleared": False, "per_window": {}},
            "interesting_12_21": {"cleared": False, "per_window": {}},
            "oos_12_30": {"verdict": "CLEAR", "per_window": {}},
            "oos_12_21": {"verdict": "CLEAR", "per_window": {}},
            "windows": [],
        }
    )
    assert "Do not promote" in md
    assert "observer default remains 12/30" in md.lower() or "stays **12/30**" in md
    assert "not a new observer default" in md.lower()
    assert "ema_long_flat_v1_12_21" in md


def test_compare_source_files_have_no_trade_client():
    root = Path(__file__).resolve().parents[2]
    for rel in (
        "src/atlas/paper/ema_12_21.py",
        "scripts/run_ema_12_21_compare.py",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        assert "OkxEeaClient" not in text
        assert "place-demo-orders" not in text
        assert "allow_trade" not in text
