"""HFT staleness split: carried_forward ≠ health_stale. No PnL."""

from __future__ import annotations

import pytest

from atlas.scalp_hft.health import sample_trading_unhealthy, summarize_trading_health
from atlas.scalp_hft.vamp import (
    HEALTH_STALE_MS,
    SAMPLE_COLUMNS,
    BookTop5,
    replay_books5_to_1s,
    summarize_samples,
)


def _sym_book(
    mid: float = 100.0,
    *,
    spread: float = 0.02,
    bid_sizes: list[float] | None = None,
    ask_sizes: list[float] | None = None,
) -> BookTop5:
    half = spread / 2.0
    bb = mid - half
    ba = mid + half
    bid_sizes = bid_sizes or [10, 10, 10, 10, 10]
    ask_sizes = ask_sizes or [10, 10, 10, 10, 10]
    bids = [(bb - i * 0.01, float(bid_sizes[i])) for i in range(5)]
    asks = [(ba + i * 0.01, float(ask_sizes[i])) for i in range(5)]
    return BookTop5(bids=bids, asks=asks)


def test_health_stale_threshold_is_existing_1000ms():
    assert HEALTH_STALE_MS == 1000


def test_carry_forward_under_1s_is_not_health_stale():
    """Book at +100ms; next 1s bucket carries it (age 900ms) — carry yes, health no."""
    t0 = 1_700_000_000_000
    events = [
        (t0 + 100, "X", _sym_book(10.0)),
        (t0 + 3100, "X", _sym_book(10.1)),
    ]
    samples = replay_books5_to_1s(events)
    assert [s.carried_forward for s in samples] == [False, True, True, False]
    assert samples[1].book_stale is True  # legacy alias of carried_forward
    assert samples[1].health_stale is False
    assert samples[1].book_age_ms == 900
    assert samples[2].health_stale is True  # age 1900 > 1000
    assert samples[2].book_age_ms == 1900
    assert samples[0].health_stale is False
    assert samples[3].health_stale is False


def test_trading_health_ignores_carried_forward_alone():
    t0 = 1_700_000_000_000
    events = [(t0 + 100, "X", _sym_book(10.0)), (t0 + 3100, "X", _sym_book(10.1))]
    samples = replay_books5_to_1s(events)
    # 900ms carry is feature-carry only
    assert sample_trading_unhealthy(samples[1]) is False
    assert samples[1].carried_forward is True
    # 1900ms carry is health-stale
    assert sample_trading_unhealthy(samples[2]) is True
    health = summarize_trading_health(samples)
    assert health.n_carried_forward == 2
    assert health.n_health_stale == 1
    assert health.n_trading_unhealthy == 1
    assert health.to_dict()["no_hft_pnl"] is True


def test_reconnect_marks_unhealthy_even_if_book_fresh():
    t0 = 1_700_000_000_000
    events = [(t0 + 50, "X", _sym_book(10.0))]
    samples = replay_books5_to_1s(events, fill_missing_seconds=False)
    sec = samples[0].ts_s
    assert samples[0].health_stale is False
    assert sample_trading_unhealthy(samples[0], reconnect_seconds={sec}) is True
    assert sample_trading_unhealthy(samples[0], reconnect_seconds=set()) is False


def test_seq_id_skip_is_not_a_health_gap():
    """books5 snapshots are self-contained — seq skips must not imply missing packets."""
    from atlas.scalp_hft.vamp import Books5IngestStats, extract_books5_from_envelope

    env = {
        "payload": {
            "data": [
                {
                    "bids": [["1", "1", "0", "1"]] * 5,
                    "asks": [["1.1", "1", "0", "1"]] * 5,
                    "instId": "X",
                    "ts": "1700000000000",
                    "seqId": 50,
                }
            ]
        }
    }
    extracted = extract_books5_from_envelope(env)
    assert extracted[0][3] == 50
    stats = Books5IngestStats()
    stats.seq_id_skips = 9
    d = stats.to_dict()
    assert "not treated as hard gaps" in d["seq_id_note"]


def test_sample_columns_include_health_fields():
    for col in ("carried_forward", "book_age_ms", "health_stale", "last_book_ts_ms", "ts_rewind"):
        assert col in SAMPLE_COLUMNS


def test_summarize_reports_health_not_just_carry():
    t0 = 1_700_000_000_000
    events = [(t0 + 100, "X", _sym_book(10.0)), (t0 + 3100, "X", _sym_book(10.1))]
    gap = summarize_samples(replay_books5_to_1s(events))
    assert gap.n_carried_forward == 2
    assert gap.n_health_stale == 1
    assert "NOT carried_forward alone" in gap.to_dict()["stale_policy"]
