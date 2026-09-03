"""Named calendar windows: research MD labels, skip empty xperp, 2020 parse."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from atlas.common.config import load_config
from atlas.paper.md import parse_okx_candle_row
from atlas.paper.named_windows import (
    NAMED_SOURCE,
    OMS_SPOT_INST,
    RESEARCH_SPOT_MD,
    XPERP_MD,
    parse_windows_arg,
    run_named_replay,
    run_named_shadow,
    spot_research_md,
    xperp_named_status,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "named" / "okx_2020_candles.jsonl"
BAR_MS = 15 * 60 * 1000
H1 = 60 * 60 * 1000
START = 1_598_918_400_000  # 2020-09-01 00:00 UTC


def _rows() -> list[list[str]]:
    out: list[list[str]] = []
    for line in FIXTURE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("{"):
            continue
        out.append(json.loads(line))
    return out


def test_2020_fixture_parses_closed_bars():
    rows = _rows()
    assert FIXTURE.stat().st_size < 20_000
    parsed = [
        parse_okx_candle_row(r, symbol=RESEARCH_SPOT_MD, bar="15m", source="test") for r in rows
    ]
    closed = [b for b in parsed if b is not None]
    assert any(str(r[8]) == "0" for r in rows if len(r) >= 9)
    assert closed
    assert all(b.closed for b in closed)
    assert all(b.ts_open_ms >= START for b in closed)
    assert closed[0].symbol == RESEARCH_SPOT_MD


def test_spot_research_md_is_labeled_not_oms_usd():
    meta = spot_research_md()
    assert meta["md_inst_id"] == RESEARCH_SPOT_MD == "DOGE-USDT"
    assert meta["oms_inst_id"] == OMS_SPOT_INST == "DOGE-USD"
    assert meta["research_md"] is True
    assert meta["orderable"] is False
    assert "DOGE-USD" in meta["label"]
    assert meta["md_inst_id"] != OMS_SPOT_INST


def test_xperp_named_is_unavailable():
    st = xperp_named_status()
    assert st["status"] == "unavailable"
    assert st["md_inst_id"] == XPERP_MD
    assert "invented" in st["label"] or "skipped" in st["label"]


def test_parse_windows_arg():
    wins = parse_windows_arg("2020-09,2023-09")
    assert [w.id for w in wins] == ["2020-09", "2023-09"]
    assert wins[0].start_ms == START
    with pytest.raises(ReplayError, match="unknown"):
        parse_windows_arg("2019-01")


def _b15(i: int, c: float = 0.0032) -> Bar:
    ts = START + i * BAR_MS
    return Bar(RESEARCH_SPOT_MD, ts, ts + BAR_MS, c, c + 0.00002, c - 0.00002, c, 1.0, True, "test")


def test_empty_xperp_skips_not_crash(tmp_path: Path):
    cfg = load_config()
    bars = [_b15(i) for i in range(40)]
    h1: list[Bar] = []
    summary = run_named_replay(
        cfg,
        windows="2020-09",
        venue="both",
        data_dir=tmp_path,
        bars_by_window={"2020-09": {"spot": (bars, h1)}},
        try_research_perp=False,
        now_ms=START + 40 * BAR_MS,
    )
    assert summary["place_orders"] is False
    assert summary["source"] == NAMED_SOURCE
    xlegs = [lg for w in summary["windows"] for lg in w["legs"] if lg.get("venue") == "xperp"]
    assert xlegs
    assert xlegs[0]["status"] == "unavailable"
    spot = [lg for w in summary["windows"] for lg in w["legs"] if lg.get("venue") == "spot"]
    assert spot and spot[0]["md_inst_id"] == RESEARCH_SPOT_MD


def test_empty_spot_window_skips_not_fake(tmp_path: Path):
    cfg = load_config()
    summary = run_named_replay(
        cfg,
        windows="2020-09",
        venue="spot",
        data_dir=tmp_path,
        bars_by_window={"2020-09": {"spot": ([], [])}},
        try_research_perp=False,
        now_ms=START,
    )
    spot = summary["windows"][0]["legs"][0]
    assert spot["status"] == "skipped"
    assert spot["n_signals"] == 0
    assert summary["place_orders"] is False


def test_named_does_not_request_doge_usd(tmp_path: Path):
    """Named fetch must ask for DOGE-USDT, never silently use OMS DOGE-USD."""
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        inst = request.url.params.get("instId") or ""
        seen.append(inst)
        return httpx.Response(
            200, json={"code": "0", "msg": "", "data": []}
        )

    with respx.mock:
        respx.get(url__regex=r".*/api/v5/market/history-candles.*").mock(side_effect=handler)
        cfg = load_config()
        client = httpx.Client()
        run_named_replay(
            cfg,
            windows="2020-09",
            venue="spot",
            data_dir=tmp_path,
            client=client,
            try_research_perp=False,
            pause_s=0.0,
            now_ms=START,
        )
    assert seen
    assert all(inst == RESEARCH_SPOT_MD for inst in seen)
    assert OMS_SPOT_INST not in seen


def test_named_shadow_empty_does_not_crash(tmp_path: Path):
    cfg = load_config()
    summary = run_named_shadow(
        cfg,
        windows="2023-09",
        venue="spot",
        data_dir=tmp_path,
        bars_by_window={"2023-09": {"spot": ([], [])}},
        try_research_perp=False,
        now_ms=START,
    )
    assert summary["place_orders"] is False
    assert summary["windows"][0]["n_would_place"] == 0
    assert summary["ok"] is False
