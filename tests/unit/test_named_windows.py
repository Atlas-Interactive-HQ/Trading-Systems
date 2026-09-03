"""Named calendar windows: research MD labels, skip empty xperp, 2020 parse."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
import respx

from atlas.common.config import load_config
from atlas.paper.md import parse_okx_candle_row
from atlas.paper.named_windows import (
    NAMED_SOURCE,
    NAMED_WINDOWS,
    OMS_SPOT_INST,
    Q4_WINDOW_IDS,
    RESEARCH_SPOT_MD,
    XPERP_MD,
    calendar_month_spec,
    expand_window_ids,
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


def test_q4_month_bounds():
    """Oct 31 / Nov 30 / Dec 31 inclusive; exclusive end is the next day."""
    oct20 = parse_windows_arg("2020-10")[0]
    assert oct20.start == "2020-10-01"
    assert oct20.end == "2020-10-31"
    assert oct20.end_ms_exclusive == int(
        datetime(2020, 11, 1, tzinfo=timezone.utc).timestamp() * 1000
    )
    nov23 = parse_windows_arg("2023-11")[0]
    assert nov23.end == "2023-11-30"
    assert nov23.end_ms_exclusive == int(
        datetime(2023, 12, 1, tzinfo=timezone.utc).timestamp() * 1000
    )
    dec24 = parse_windows_arg("2024-12")[0]
    assert dec24.end == "2024-12-31"
    assert dec24.end_ms_exclusive == int(
        datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp() * 1000
    )
    spec = calendar_month_spec(2020, 10)
    assert spec["end"] == "2020-10-31"
    assert spec["id"] == "2020-10"


def test_existing_2020_09_is_not_calendar_september():
    """2020-09 stays the original Sep→Mar span, distinct from Q4 months."""
    w = parse_windows_arg("2020-09")[0]
    assert w.start == "2020-09-01"
    assert w.end == "2021-03-31"
    assert "2020-10" in NAMED_WINDOWS
    assert NAMED_WINDOWS["2020-10"]["end"] == "2020-10-31"


def test_unknown_month_id_fails_closed():
    with pytest.raises(ReplayError, match="unknown"):
        parse_windows_arg("2020-13")
    with pytest.raises(ReplayError, match="unknown"):
        parse_windows_arg("2021-10")
    with pytest.raises(ReplayError, match="unknown"):
        parse_windows_arg("2019-01")


def test_oos_stress_window_bounds():
    bear = parse_windows_arg("2022-bear")[0]
    assert bear.start == "2022-01-01" and bear.end == "2022-12-31"
    assert bear.end_ms_exclusive == int(
        datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000
    )
    h1 = parse_windows_arg("2022-h1")[0]
    assert h1.start == "2022-01-01" and h1.end == "2022-06-30"
    assert h1.end_ms_exclusive == int(
        datetime(2022, 7, 1, tzinfo=timezone.utc).timestamp() * 1000
    )
    chop = parse_windows_arg("2023-chop")[0]
    assert chop.start == "2023-01-01" and chop.end == "2023-08-31"
    assert chop.end_ms_exclusive == int(
        datetime(2023, 9, 1, tzinfo=timezone.utc).timestamp() * 1000
    )
    wins = parse_windows_arg("2022-bear,2023-chop,2020-09")
    assert [w.id for w in wins] == ["2022-bear", "2023-chop", "2020-09"]
    with pytest.raises(ReplayError, match="unknown"):
        parse_windows_arg("2022-bull")


def test_q4_token_expands_nine_months():
    ids = expand_window_ids("q4")
    assert ids == list(Q4_WINDOW_IDS)
    assert ids == [
        "2020-10",
        "2020-11",
        "2020-12",
        "2023-10",
        "2023-11",
        "2023-12",
        "2024-10",
        "2024-11",
        "2024-12",
    ]
    wins = parse_windows_arg("q4")
    assert [w.id for w in wins] == ids


def test_empty_q4_month_skips_not_crash(tmp_path: Path):
    cfg = load_config()
    summary = run_named_replay(
        cfg,
        windows="2024-10",
        venue="spot",
        data_dir=tmp_path,
        bars_by_window={"2024-10": {"spot": ([], [])}},
        try_research_perp=False,
        now_ms=START,
    )
    spot = summary["windows"][0]["legs"][0]
    assert spot["status"] == "skipped"
    assert spot["n_signals"] == 0
    assert summary["place_orders"] is False
    assert summary["windows"][0]["ok"] is False


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
