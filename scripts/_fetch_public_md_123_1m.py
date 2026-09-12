#!/usr/bin/env python3
"""Fetch OKX EEA 1m history-candles for phase1/123 — cache under results/."""
from __future__ import annotations

import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from atlas.common.time import parse_exchange_ts_ms
from atlas.paper.md import (
    OKX_HISTORY_LIMIT_MAX,
    OKX_REST,
    USER_AGENT,
    fetch_okx_history_candles_page,
    load_jsonl_candles,
    merge_bars,
    persist_candles,
)

INSTS = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
START = parse_exchange_ts_ms("2020-06-01T00:00:00Z")
END = parse_exchange_ts_ms("2021-01-01T00:00:00Z")
FULL_START = parse_exchange_ts_ms("2020-07-01T00:00:00Z")
CACHE = _ROOT / "results" / "public_md_123_cache"
CACHE.mkdir(parents=True, exist_ok=True)
LOCK = threading.Lock()

CHUNKS: list[tuple[int, int]] = []
cur = START
while cur < END:
    nxt = min(cur + 30 * 24 * 60 * 60 * 1000, END)
    CHUNKS.append((cur, nxt))
    cur = nxt


def fetch_chunk(client: httpx.Client, inst: str, start_ms: int, end_ms: int):
    after = int(end_ms)
    collected = []
    pages = 0
    while pages < 600:
        page, raw_n = fetch_okx_history_candles_page(
            client,
            inst,
            "1m",
            rest_base=OKX_REST,
            after=after,
            limit=OKX_HISTORY_LIMIT_MAX,
        )
        pages += 1
        if raw_n == 0 and not page:
            break
        collected.extend(page)
        if not page:
            break
        oldest = min(b.ts_open_ms for b in page)
        if oldest <= start_ms:
            break
        if raw_n < OKX_HISTORY_LIMIT_MAX:
            break
        if oldest >= after:
            break
        after = oldest
        time.sleep(0.015)
    bars = [b for b in collected if b.closed and start_ms <= b.ts_open_ms < end_ms]
    return bars, pages


def fetch_inst(inst: str):
    path = CACHE / f"{inst}_1m.jsonl"
    if path.is_file() and path.stat().st_size > 5_000_000:
        try:
            bars = load_jsonl_candles(path, symbol=inst, bar="1m")
            bars = [b for b in bars if START <= b.ts_open_ms < END]
            trade = [b for b in bars if FULL_START <= b.ts_open_ms < END]
            if (
                len(trade) > 200_000
                and bars
                and bars[0].ts_open_ms <= FULL_START
                and bars[-1].ts_open_ms >= END - 60_000
            ):
                print(f"CACHE_OK {inst} n={len(bars)} trade={len(trade)}", flush=True)
                return inst, len(bars), len(trade), 0.0
        except Exception as exc:  # noqa: BLE001
            print(f"CACHE_BAD {inst}: {exc}", flush=True)
    t0 = time.time()
    print(f"FETCH_START {inst}", flush=True)
    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
    all_bars = []
    try:
        for a, b in CHUNKS:
            chunk_bars, pages = fetch_chunk(client, inst, a, b)
            all_bars.extend(chunk_bars)
            with LOCK:
                print(
                    f"  {inst} chunk {a}->{b} n={len(chunk_bars)} "
                    f"pages={pages} total={len(all_bars)}",
                    flush=True,
                )
        bars = merge_bars(all_bars)
        bars = [b for b in bars if START <= b.ts_open_ms < END]
        persist_candles(path, bars)
        trade = [b for b in bars if FULL_START <= b.ts_open_ms < END]
        dt = time.time() - t0
        print(f"FETCH_DONE {inst} n={len(bars)} trade={len(trade)} secs={dt:.1f}", flush=True)
        if len(trade) < 200_000:
            print(f"FAIL_CLOSED {inst} trade={len(trade)}", flush=True)
        return inst, len(bars), len(trade), dt
    finally:
        client.close()


def main() -> int:
    print(f"CHUNKS n={len(CHUNKS)}", flush=True)
    results = []
    # Sequential instruments — steadier vs shared 20/2s public limit
    for inst in INSTS:
        results.append(fetch_inst(inst))
    print("ALL_FETCH_DONE", results, flush=True)
    bad = [r for r in results if r[2] < 200_000]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
