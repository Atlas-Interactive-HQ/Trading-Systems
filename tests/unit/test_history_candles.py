"""OKX history-candles parser + pagination. No live network."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from atlas.paper.md import (
    OKX_HISTORY_CANDLES_PATH,
    PaperDataError,
    fetch_okx_candles,
    fetch_okx_history_candles,
    parse_okx_candle_row,
    parse_okx_candles_payload,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "replay" / "okx_history_candles.jsonl"
BAR_MS = 15 * 60 * 1000


def _rows_from_fixture() -> list[list[str]]:
    rows: list[list[str]] = []
    for line in FIXTURE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("{"):
            continue
        rows.append(json.loads(line))
    return rows


def test_fixture_is_tiny():
    assert FIXTURE.stat().st_size < 50_000
    assert len(_rows_from_fixture()) <= 20


def test_closed_bar_only_drops_unconfirmed():
    rows = _rows_from_fixture()
    parsed = [
        parse_okx_candle_row(r, symbol="DOGE-USD", bar="15m", source="test") for r in rows
    ]
    closed = [b for b in parsed if b is not None]
    assert any(str(r[8]) == "0" for r in rows if len(r) >= 9)
    assert len(closed) == len(rows) - 1
    assert all(b.closed for b in closed)


def test_payload_fail_closed_on_bad_envelope():
    with pytest.raises(PaperDataError):
        parse_okx_candles_payload(["not", "an", "object"], symbol="DOGE-USD", bar="15m", source="t")
    with pytest.raises(PaperDataError):
        parse_okx_candles_payload(
            {"code": "50001", "msg": "fail", "data": []},
            symbol="DOGE-USD",
            bar="15m",
            source="t",
        )
    with pytest.raises(PaperDataError):
        parse_okx_candles_payload({"code": "0"}, symbol="DOGE-USD", bar="15m", source="t")


def test_empty_data_list_is_empty_not_fake():
    bars = parse_okx_candles_payload(
        {"code": "0", "msg": "", "data": []}, symbol="DOGE-USD", bar="15m", source="t"
    )
    assert bars == []


@respx.mock
def test_history_pagination_after_cursor_and_no_sim_header():
    base = "https://eea.okx.com"
    newer = [
        [str(1_700_000_000_000 + i * BAR_MS), "1", "1.1", "0.9", "1", "1", "0", "0", "1"]
        for i in range(10, 20)
    ]
    older = [
        [str(1_700_000_000_000 + i * BAR_MS), "1", "1.1", "0.9", "1", "1", "0", "0", "1"]
        for i in range(0, 10)
    ]
    seen_after: list[str | None] = []

    end_ms = 1_700_000_000_000 + 20 * BAR_MS

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("x-simulated-trading") in (None, "")
        after = request.url.params.get("after")
        seen_after.append(after)
        # First page: after=end_ms → newer 10–19. Next after=oldest of that page → 0–9.
        if after is None or after == str(end_ms):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": list(reversed(newer))})
        return httpx.Response(200, json={"code": "0", "msg": "", "data": list(reversed(older))})

    respx.get(url__regex=rf"{base}{OKX_HISTORY_CANDLES_PATH}.*").mock(side_effect=handler)
    client = httpx.Client()
    bars = fetch_okx_history_candles(
        client,
        "DOGE-USD",
        "15m",
        rest_base=base,
        start_ms=1_700_000_000_000,
        end_ms=end_ms,
        limit=10,
        pause_s=0.0,
        max_pages=5,
    )
    assert len(bars) == 20
    assert bars[0].ts_open_ms == 1_700_000_000_000
    assert bars[-1].ts_open_ms == 1_700_000_000_000 + 19 * BAR_MS
    assert all(b.closed for b in bars)
    assert seen_after[0] == str(1_700_000_000_000 + 20 * BAR_MS)
    assert seen_after[1] == str(newer[0][0])  # oldest of first page


@respx.mock
def test_market_candles_now_path_unchanged():
    respx.get(url__regex=r".*/api/v5/market/candles.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "0",
                "msg": "",
                "data": [
                    ["1700000000000", "1", "1.2", "0.9", "1.1", "5", "0", "0", "1"],
                    ["1700000900000", "1.1", "1.3", "1.0", "1.2", "5", "0", "0", "0"],
                ],
            },
        )
    )
    bars = fetch_okx_candles(httpx.Client(), "DOGE-USD", "15m", rest_base="https://eea.okx.com")
    assert len(bars) == 1
    assert bars[0].closed is True
