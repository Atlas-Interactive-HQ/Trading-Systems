"""Unit tests for Scalp-HFT 1s VAMP-5 pipeline (synthetic books; no network)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.scalp_hft.vamp import (
    EMA,
    BookTop5,
    RollingZScore,
    SAMPLE_COLUMNS,
    calculate_vamp,
    mid_from_book,
    parse_books5_levels,
    replay_books5_jsonl_to_1s,
    replay_books5_to_1s,
    vamp_edge_bps,
    write_samples_csv,
)


def _sym_book(
    mid: float = 100.0,
    *,
    spread: float = 0.02,
    bid_sizes: list[float] | None = None,
    ask_sizes: list[float] | None = None,
) -> BookTop5:
    """Build a synthetic top-5 around mid with optional size imbalance."""
    half = spread / 2.0
    bb = mid - half
    ba = mid + half
    bid_sizes = bid_sizes or [10, 10, 10, 10, 10]
    ask_sizes = ask_sizes or [10, 10, 10, 10, 10]
    bids = [(bb - i * 0.01, float(bid_sizes[i])) for i in range(5)]
    asks = [(ba + i * 0.01, float(ask_sizes[i])) for i in range(5)]
    return BookTop5(bids=bids, asks=asks)


def test_calculate_vamp_symmetric_equals_mid():
    book = _sym_book(100.0, spread=0.02)
    mid = mid_from_book(book)
    vamp = calculate_vamp(book)
    assert mid == pytest.approx(100.0)
    # Equal sizes → VAMP near mid (exact for symmetric levels)
    assert vamp == pytest.approx(mid)


def test_calculate_vamp_bid_heavy_above_mid():
    # More ask-side liquidity at low bids? Formula: Σ Pbid*Qask + Σ Pask*Qbid
    # Larger ask sizes pull toward bids → VAMP < mid when asks are thick.
    # Larger bid sizes pull toward asks → VAMP > mid when bids are thick.
    book = _sym_book(
        100.0,
        bid_sizes=[100, 100, 100, 100, 100],
        ask_sizes=[1, 1, 1, 1, 1],
    )
    mid = mid_from_book(book)
    vamp = calculate_vamp(book)
    assert vamp > mid


def test_calculate_vamp_ask_heavy_below_mid():
    book = _sym_book(
        100.0,
        bid_sizes=[1, 1, 1, 1, 1],
        ask_sizes=[100, 100, 100, 100, 100],
    )
    mid = mid_from_book(book)
    vamp = calculate_vamp(book)
    assert vamp < mid


def test_vamp_insufficient_depth_raises():
    book = BookTop5(bids=[(1.0, 1.0)], asks=[(1.1, 1.0)])
    with pytest.raises(ValueError, match="insufficient"):
        calculate_vamp(book)


def test_vamp_edge_bps_sign():
    assert vamp_edge_bps(100.1, 100.0) == pytest.approx(10.0)
    assert vamp_edge_bps(99.9, 100.0) == pytest.approx(-10.0)


def test_rolling_z_warmup_and_invalid_std():
    z = RollingZScore(window=5)
    assert z.update(1.0) is None
    assert z.update(1.0) is None
    assert z.update(1.0) is None
    assert z.update(1.0) is None
    # constant series → std 0 → INVALID (None)
    assert z.update(1.0) is None
    # introduce variance
    out = z.update(3.0)
    assert out is not None
    assert abs(out) > 0


def test_ema_warmup():
    ema = EMA(3)
    assert ema.update(1.0) is None
    assert ema.update(2.0) is None
    v = ema.update(3.0)
    assert v is not None
    assert v == pytest.approx(ema.value)


def test_parse_okx_books5_levels():
    bids = [["0.08", "10", "0", "1"], ["0.079", "5", "0", "1"],
            ["0.078", "5", "0", "1"], ["0.077", "5", "0", "1"],
            ["0.076", "5", "0", "1"]]
    asks = [["0.081", "10", "0", "1"], ["0.082", "5", "0", "1"],
            ["0.083", "5", "0", "1"], ["0.084", "5", "0", "1"],
            ["0.085", "5", "0", "1"]]
    book = parse_books5_levels(bids, asks)
    assert len(book.bids) == 5
    assert book.bids[0] == (0.08, 10.0)
    assert book.asks[0][0] == pytest.approx(0.081)


def test_replay_1s_closed_clock_and_stale_carry(tmp_path: Path):
    """Two updates 3s apart → filled seconds with book_stale on gaps."""
    t0 = 1_700_000_000_000  # ms
    events = [
        (t0 + 100, "TEST-INST", _sym_book(10.0)),
        (t0 + 3100, "TEST-INST", _sym_book(10.1)),
    ]
    samples = replay_books5_to_1s(events, z_window=60, ema_fast=12, ema_slow=21)
    secs = [s.ts_s for s in samples]
    assert secs == list(range(t0 // 1000, t0 // 1000 + 4))
    assert samples[0].book_stale is False
    assert samples[1].book_stale is True
    assert samples[2].book_stale is True
    assert samples[3].book_stale is False
    assert all(s.vamp_valid for s in samples)
    assert all(c in samples[0].to_row() for c in SAMPLE_COLUMNS)
    # z still warming (<60)
    assert all(s.vamp_z is None for s in samples)


def test_replay_jsonl_envelope(tmp_path: Path):
    path = tmp_path / "ws_books5.jsonl"
    base_ts = 1_789_102_161_000
    rows = []
    # subscribe noise
    rows.append(
        {
            "venue": "okx_eea",
            "channel": "ws_books5",
            "venue_instrument_id": "DOGE-USD_UM_XPERP-310404",
            "payload": {"event": "subscribe", "arg": {"channel": "books5"}},
            "receive_ts": base_ts,
        }
    )
    for i in range(5):
        mid = 0.08 + i * 0.0001
        book = _sym_book(mid, spread=0.0002)
        rows.append(
            {
                "venue": "okx_eea",
                "channel": "ws_books5",
                "venue_instrument_id": "DOGE-USD_UM_XPERP-310404",
                "exchange_ts": base_ts + i * 1000,
                "receive_ts": base_ts + i * 1000 + 50,
                "payload": {
                    "arg": {
                        "channel": "books5",
                        "instId": "DOGE-USD_UM_XPERP-310404",
                    },
                    "data": [
                        {
                            "asks": [[str(p), str(q), "0", "1"] for p, q in book.asks],
                            "bids": [[str(p), str(q), "0", "1"] for p, q in book.bids],
                            "instId": "DOGE-USD_UM_XPERP-310404",
                            "ts": str(base_ts + i * 1000),
                            "seqId": 100 + i,
                        }
                    ],
                },
            }
        )
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    samples = replay_books5_jsonl_to_1s([path], fill_missing_seconds=True)
    assert len(samples) == 5
    assert samples[0].inst_id == "DOGE-USD_UM_XPERP-310404"
    assert samples[0].mid == pytest.approx(0.08)
    out_csv = tmp_path / "out.csv"
    n = write_samples_csv(samples, out_csv)
    assert n == 5
    text = out_csv.read_text(encoding="utf-8")
    assert "vamp5" in text.splitlines()[0]
    assert "pnl" not in text.lower()


def test_z_becomes_valid_after_window():
    events = []
    t0 = 1_700_000_000_000
    for i in range(65):
        # alternate imbalance so edge has variance
        if i % 2 == 0:
            book = _sym_book(100.0, bid_sizes=[50] * 5, ask_sizes=[10] * 5)
        else:
            book = _sym_book(100.0, bid_sizes=[10] * 5, ask_sizes=[50] * 5)
        events.append((t0 + i * 1000, "X", book))
    samples = replay_books5_to_1s(events, z_window=60)
    assert len(samples) == 65
    assert samples[58].vamp_z is None  # 59th sample index 58 — still <60
    assert samples[59].vamp_z is not None
    assert samples[0].ema12 is None
    assert samples[11].ema12 is not None
    assert samples[20].ema21 is not None
