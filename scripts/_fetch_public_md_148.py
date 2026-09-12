#!/usr/bin/env python3
"""Fetch OKX EEA history-candles for #148 OOS_2022 + OOS_2023. Paper only.

Never invents bars. Public GET only. Writes results/public_md_148_cache/{oos_2022,oos_2023}/.
Warmup months included in fetch for pivots/ATR/RVOL.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
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

LOCK = threading.Lock()
CACHE_ROOT = _ROOT / "results" / "public_md_148_cache"

WINDOWS = {
    "oos_2022": {
        "trade": ("2022-01-01T00:00:00Z", "2022-07-01T00:00:00Z"),
        "warmup_start": "2021-11-01T00:00:00Z",
    },
    "oos_2023": {
        "trade": ("2023-01-01T00:00:00Z", "2023-07-01T00:00:00Z"),
        "warmup_start": "2022-11-01T00:00:00Z",
    },
}

INSTS = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
BARS = ("1m", "15m", "1H", "4H")


def iso_ms(iso: str) -> int:
    return int(parse_exchange_ts_ms(iso))


def ms_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def month_chunks(start_ms: int, end_ms: int, days: int = 14) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    cur = start_ms
    step = days * 24 * 60 * 60 * 1000
    while cur < end_ms:
        nxt = min(cur + step, end_ms)
        out.append((cur, nxt))
        cur = nxt
    return out


def fetch_page_retry(client, inst, bar, after, retries=8):
    delay = 0.5
    last = None
    for attempt in range(retries):
        try:
            return fetch_okx_history_candles_page(
                client,
                inst,
                bar,
                rest_base=OKX_REST,
                after=after,
                limit=OKX_HISTORY_LIMIT_MAX,
            )
        except httpx.HTTPStatusError as exc:
            last = exc
            if exc.response is not None and exc.response.status_code == 429:
                time.sleep(delay)
                delay = min(delay * 1.8, 12.0)
                continue
            raise
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            last = exc
            time.sleep(delay)
            delay = min(delay * 1.8, 12.0)
    raise last  # type: ignore[misc]


def fetch_chunk(client: httpx.Client, inst: str, bar: str, start_ms: int, end_ms: int):
    after = int(end_ms)
    collected = []
    pages = 0
    while pages < 2000:
        page, raw_n = fetch_page_retry(client, inst, bar, after)
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
        time.sleep(0.06)
    bars = [b for b in collected if b.closed and start_ms <= b.ts_open_ms < end_ms]
    return bars, pages


def fetch_inst_bar(
    inst: str,
    bar: str,
    *,
    fetch_start: int,
    fetch_end: int,
    out_dir: Path,
):
    path = out_dir / f"{inst}_{bar}.jsonl"
    t0 = time.time()
    if path.is_file() and path.stat().st_size > 10_000:
        bars = load_jsonl_candles(path, symbol=inst, bar=bar)
        trade = [b for b in bars if fetch_start <= b.ts_open_ms < fetch_end]
        expected_min = {
            "1m": int((fetch_end - fetch_start) / 60_000 * 0.95),
            "15m": int((fetch_end - fetch_start) / 900_000 * 0.95),
            "1H": int((fetch_end - fetch_start) / 3_600_000 * 0.95),
            "4H": int((fetch_end - fetch_start) / 14_400_000 * 0.90),
        }[bar]
        if len(trade) >= expected_min:
            print(
                f"CACHE_OK {inst} {bar} n={len(bars)} trade={len(trade)}",
                flush=True,
            )
            return {
                "inst": inst,
                "bar": bar,
                "n": len(bars),
                "status": "cache",
                "secs": 0.0,
                "first_iso": ms_iso(bars[0].ts_open_ms) if bars else None,
                "last_iso": ms_iso(bars[-1].ts_open_ms) if bars else None,
                "trade_n": len(trade),
            }

    print(
        f"FETCH_START {inst} {bar} {ms_iso(fetch_start)}->{ms_iso(fetch_end)}",
        flush=True,
    )
    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
    all_bars = []
    try:
        chunks = month_chunks(fetch_start, fetch_end, days=10 if bar == "1m" else 30)
        for a, b in chunks:
            chunk_bars, pages = fetch_chunk(client, inst, bar, a, b)
            all_bars.extend(chunk_bars)
            with LOCK:
                print(
                    f"  {inst} {bar} chunk {ms_iso(a)}->{ms_iso(b)} "
                    f"n={len(chunk_bars)} pages={pages} total={len(all_bars)}",
                    flush=True,
                )
        bars = merge_bars(all_bars)
        if not bars:
            raise RuntimeError(f"empty fetch {inst} {bar}")
        persist_candles(path, bars)
        dt = time.time() - t0
        print(
            f"FETCH_DONE {inst} {bar} n={len(bars)} "
            f"first={ms_iso(bars[0].ts_open_ms)} last={ms_iso(bars[-1].ts_open_ms)} "
            f"secs={dt:.1f}",
            flush=True,
        )
        trade = [b for b in bars if fetch_start <= b.ts_open_ms < fetch_end]
        return {
            "inst": inst,
            "bar": bar,
            "n": len(bars),
            "status": "fetched",
            "secs": dt,
            "first_iso": ms_iso(bars[0].ts_open_ms),
            "last_iso": ms_iso(bars[-1].ts_open_ms),
            "trade_n": len(trade),
        }
    finally:
        client.close()


def run_window(key: str) -> list[dict]:
    spec = WINDOWS[key]
    out = CACHE_ROOT / key
    out.mkdir(parents=True, exist_ok=True)
    # Fetch from warmup_start through trade end so pivots/ATR have lookback
    fetch_start = iso_ms(spec["warmup_start"])
    fetch_end = iso_ms(spec["trade"][1])
    results: list[dict] = []
    for bar in ("4H", "1H", "15m", "1m"):
        with ThreadPoolExecutor(max_workers=1) as ex:
            futs = [
                ex.submit(
                    fetch_inst_bar,
                    inst,
                    bar,
                    fetch_start=fetch_start,
                    fetch_end=fetch_end,
                    out_dir=out,
                )
                for inst in INSTS
            ]
            for fut in as_completed(futs):
                r = fut.result()
                r["window"] = key
                results.append(r)
                print("RESULT", r, flush=True)
    return results


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="#148 public MD fetch 2022+2023 (paper)")
    p.add_argument(
        "--window",
        choices=("oos_2022", "oos_2023", "both"),
        default="both",
    )
    args = p.parse_args(argv)
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    all_results: list[dict] = []
    keys = ("oos_2022", "oos_2023") if args.window == "both" else (args.window,)
    for key in keys:
        all_results.extend(run_window(key))
    manifest = CACHE_ROOT / "fetch_manifest.json"
    manifest.write_text(json.dumps(all_results, indent=2) + "\n")
    print("WROTE", manifest, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
