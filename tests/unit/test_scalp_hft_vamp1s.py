"""Unit tests for 1s VAMP-5 Layer B pipeline (synthetic books5; no live PnL)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from atlas.scalp_hft.vamp import (
    BookTop5,
    Books5IngestStats,
    EMA,
    RollingZScore,
    SAMPLE_COLUMNS,
    calculate_vamp,
    mid_from_book,
    parse_books5_levels,
    replay_books5_jsonl_to_1s,
    replay_books5_to_1s,
    summarize_samples,
    vamp_edge_bps,
    write_samples_csv,
)


def test_calculate_vamp_matches_design_formula():
    # Symmetric book → VAMP == mid
    book = BookTop5(
        bids=[(10.0, 1.0), (9.9, 2.0), (9.8, 3.0), (9.7, 4.0), (9.6, 5.0)],
        asks=[(10.1, 1.0), (10.2, 2.0), (10.3, 3.0), (10.4, 4.0), (10.5, 5.0)],
    )
    mid = mid_from_book(book)
    assert mid == pytest.approx(10.05)
    vamp = calculate_vamp(book)
    # Hand: Σ Pbid*Qask + Σ Pask*Qbid
    # = 10*1 + 9.9*2 + 9.8*3 + 9.7*4 + 9.6*5
    # + 10.1*1 + 10.2*2 + 10.3*3 + 10.4*4 + 10.5*5
    num = (
        10.0 * 1
        + 9.9 * 2
        + 9.8 * 3
        + 9.7 * 4
        + 9.6 * 5
        + 10.1 * 1
        + 10.2 * 2
        + 10.3 * 3
        + 10.4 * 4
        + 10.5 * 5
    )
    den = (1 + 2 + 3 + 4 + 5) * 2
    assert vamp == pytest.approx(num / den)
    edge = vamp_edge_bps(vamp, mid)
    assert edge == pytest.approx(10_000.0 * (vamp - mid) / mid)


def test_calculate_vamp_insufficient_depth():
    book = BookTop5(bids=[(1.0, 1.0)], asks=[(1.1, 1.0)])
    with pytest.raises(ValueError, match="insufficient depth"):
        calculate_vamp(book)


def test_parse_okx_books5_levels():
    bids = [["0.08", "10", "0", "1"], ["0.079", "20", "0", "2"],
            ["0.078", "30", "0", "1"], ["0.077", "40", "0", "1"],
            ["0.076", "50", "0", "1"]]
    asks = [["0.081", "11", "0", "1"], ["0.082", "21", "0", "1"],
            ["0.083", "31", "0", "1"], ["0.084", "41", "0", "1"],
            ["0.085", "51", "0", "1"]]
    book = parse_books5_levels(bids, asks)
    assert len(book.bids) == 5
    assert book.bids[0] == (0.08, 10.0)
    assert book.asks[0] == (0.081, 11.0)


def test_rolling_z_warmup_and_invalid():
    z = RollingZScore(window=4)
    assert z.update(1.0) is None
    assert z.update(1.0) is None
    assert z.update(1.0) is None
    # constant series → std 0 → INVALID (None)
    assert z.update(1.0) is None
    # introduce variance
    out = z.update(5.0)
    assert out is not None
    assert math.isfinite(out)


def test_ema_warmup():
    ema = EMA(3)
    assert ema.update(1.0) is None
    assert ema.update(2.0) is None
    v = ema.update(3.0)
    assert v is not None


def _envelope(ts_ms: int, bids, asks, *, seq_id: int = 1, local_seq: int = 1) -> dict:
    return {
        "venue": "okx_eea",
        "channel": "ws_books5",
        "venue_instrument_id": "DOGE-USD_UM_XPERP-310404",
        "exchange_ts": ts_ms,
        "receive_ts": ts_ms + 50,
        "local_seq": local_seq,
        "ingest_run_id": "test",
        "schema_version": "raw.envelope.v1",
        "transport": "ws",
        "is_gap": False,
        "gap_reason": None,
        "payload": {
            "arg": {"channel": "books5", "instId": "DOGE-USD_UM_XPERP-310404"},
            "data": [
                {
                    "asks": asks,
                    "bids": bids,
                    "instId": "DOGE-USD_UM_XPERP-310404",
                    "ts": str(ts_ms),
                    "seqId": seq_id,
                }
            ],
        },
    }


def _flat_levels(bid0: float, ask0: float, qty: float = 1.0):
    bids = [[f"{bid0 - i * 0.001:.6f}", str(qty), "0", "1"] for i in range(5)]
    asks = [[f"{ask0 + i * 0.001:.6f}", str(qty), "0", "1"] for i in range(5)]
    return bids, asks


def test_replay_carry_forward_marks_stale(tmp_path: Path):
    """Seconds without a book update carry last book with book_stale=True."""
    t0 = 1_700_000_000_000  # ms
    bids_a, asks_a = _flat_levels(100.0, 100.1)
    bids_b, asks_b = _flat_levels(100.2, 100.3)
    lines = [
        # subscribe control frame (skipped)
        json.dumps(
            {
                "venue": "okx_eea",
                "channel": "ws_books5",
                "venue_instrument_id": "DOGE-USD_UM_XPERP-310404",
                "exchange_ts": None,
                "receive_ts": t0,
                "local_seq": 1,
                "ingest_run_id": "test",
                "schema_version": "raw.envelope.v1",
                "transport": "ws",
                "is_gap": False,
                "gap_reason": None,
                "payload": {
                    "event": "subscribe",
                    "arg": {"channel": "books5", "instId": "DOGE-USD_UM_XPERP-310404"},
                },
            }
        ),
        json.dumps(_envelope(t0 + 100, bids_a, asks_a, seq_id=10, local_seq=2)),
        # gap: no update in second t0//1000 + 1
        json.dumps(
            _envelope(t0 + 2100, bids_b, asks_b, seq_id=20, local_seq=3)
        ),  # 2 seconds later
    ]
    path = tmp_path / "ws_books5.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ingest = Books5IngestStats()
    samples = replay_books5_jsonl_to_1s([path], ingest_stats=ingest)
    assert ingest.n_data_frames == 2
    assert ingest.n_subscribe_or_control == 1
    assert ingest.seq_id_skips >= 1  # 10 → 20

    secs = [s.ts_s for s in samples]
    assert secs == list(range(secs[0], secs[-1] + 1))
    assert len(samples) == 3  # sec0 update, sec1 stale, sec2 update
    assert samples[0].book_stale is False
    assert samples[1].book_stale is True
    assert samples[2].book_stale is False
    # stale second still has valid VAMP from carried book (not invented)
    assert samples[1].vamp_valid is True
    assert samples[1].mid == samples[0].mid

    gap = summarize_samples(samples)
    assert gap.n_seconds_stale_carry == 1
    assert gap.n_seconds_with_update == 2
    assert gap.n_vamp_valid == 3


def test_last_book_within_second_wins():
    t0 = 1_700_000_010_000
    bids_a, asks_a = _flat_levels(1.0, 1.1)
    bids_b, asks_b = _flat_levels(2.0, 2.1)
    events = [
        (t0 + 100, "X", parse_books5_levels(*_raw_from_flat(bids_a, asks_a))),
        (t0 + 500, "X", parse_books5_levels(*_raw_from_flat(bids_b, asks_b))),
    ]
    samples = replay_books5_to_1s(events, fill_missing_seconds=False)
    assert len(samples) == 1
    assert samples[0].best_bid == pytest.approx(2.0)


def _raw_from_flat(bids, asks):
    return bids, asks


def test_write_csv_schema(tmp_path: Path):
    book = BookTop5(
        bids=[(10.0 - i * 0.01, 1.0) for i in range(5)],
        asks=[(10.1 + i * 0.01, 1.0) for i in range(5)],
    )
    samples = replay_books5_to_1s(
        [(1_700_000_000_000, "DOGE-USD_UM_XPERP-310404", book)],
        fill_missing_seconds=False,
    )
    out = tmp_path / "vamp1s.csv"
    n = write_samples_csv(samples, out)
    assert n == 1
    header = out.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header == list(SAMPLE_COLUMNS)


def test_no_fill_gaps_option():
    t0 = 1_700_000_000_000
    b1 = parse_books5_levels(*_flat_levels(1.0, 1.1))
    b2 = parse_books5_levels(*_flat_levels(1.2, 1.3))
    samples = replay_books5_to_1s(
        [(t0, "X", b1), (t0 + 3000, "X", b2)],
        fill_missing_seconds=False,
    )
    assert len(samples) == 2
    assert all(not s.book_stale for s in samples)
