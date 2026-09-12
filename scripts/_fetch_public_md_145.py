#!/usr/bin/env python3
"""Fetch OKX EEA history-candles for #145 W1 sleeve + W2 majors OOS. Paper only.

Never invents bars. Public GET only. Writes results/public_md_145_cache/{w1,w2}/.
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
CACHE_ROOT = _ROOT / "results" / "public_md_145_cache"

# W2 preferred trade window + warmup
W2_TRADE = ("2021-01-01T00:00:00Z", "2021-07-01T00:00:00Z")
W2_WARMUP_START = "2020-11-01T00:00:00Z"  # pivots/ATR/RVOL
W2_INSTS = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")

# W1 sleeve shared window (≥90d ending ≤2026-09-01) + warmup
W1_TRADE = ("2026-06-01T00:00:00Z", "2026-09-01T00:00:00Z")
W1_WARMUP_START = "2026-04-01T00:00:00Z"
W1_CANDIDATES = ("PEPE-USDT", "PUMP-USDT", "WIF-USDT", "TRUMP-USDT")

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


def load_warmup_2020(inst: str, bar: str, start_ms: int, end_ms: int):
    """Reuse 2020 caches only for warmup overlap if timestamps join."""
    paths = []
    if bar in ("1m", "15m"):
        paths.append(_ROOT / "results" / "public_md_125_cache" / f"{inst}_{bar}.jsonl")
    elif bar == "1H":
        paths.append(
            _ROOT / "data" / "paper" / "candles" / "public_md_121" / f"{inst}_1H.jsonl"
        )
    elif bar == "4H":
        paths.append(
            _ROOT / "data" / "paper" / "candles" / "public_md_131" / f"{inst}_4H.jsonl"
        )
    out = []
    for p in paths:
        if not p.is_file():
            continue
        bars = load_jsonl_candles(p, symbol=inst, bar=bar)
        out.extend([b for b in bars if start_ms <= b.ts_open_ms < end_ms])
    return merge_bars(out) if out else []


def fetch_inst_bar(
    inst: str,
    bar: str,
    *,
    fetch_start: int,
    fetch_end: int,
    out_dir: Path,
    reuse_warmup_to: int | None = None,
):
    path = out_dir / f"{inst}_{bar}.jsonl"
    t0 = time.time()
    if path.is_file() and path.stat().st_size > 10_000:
        bars = load_jsonl_candles(path, symbol=inst, bar=bar)
        trade = [b for b in bars if fetch_start <= b.ts_open_ms < fetch_end]
        # allow partial if covering trade window densely enough
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
            return inst, bar, len(bars), "cache", 0.0

    print(f"FETCH_START {inst} {bar} {ms_iso(fetch_start)}->{ms_iso(fetch_end)}", flush=True)
    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
    all_bars = []
    try:
        # optional warmup from 2020 caches (join before fetch_start)
        if reuse_warmup_to is not None:
            warm = load_warmup_2020(inst, bar, reuse_warmup_to, fetch_start)
            all_bars.extend(warm)
            with LOCK:
                print(
                    f"  WARMUP_2020 {inst} {bar} n={len(warm)} "
                    f"[{ms_iso(warm[0].ts_open_ms) if warm else '-'}.."
                    f"{ms_iso(warm[-1].ts_open_ms) if warm else '-'}]",
                    flush=True,
                )
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
        return inst, bar, len(bars), "fetched", dt
    finally:
        client.close()


def probe_spot_listing(inst: str) -> dict:
    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
    try:
        url = f"{OKX_REST}/api/v5/public/instruments"
        r = client.get(url, params={"instType": "SPOT", "instId": inst})
        r.raise_for_status()
        payload = r.json()
        rows = payload.get("data") or []
        if not rows:
            return {"inst_id": inst, "listed": False, "status": "NO_DATA"}
        row = rows[0]
        return {
            "inst_id": inst,
            "listed": True,
            "state": row.get("state"),
            "listTime": row.get("listTime"),
            "listTime_iso": ms_iso(int(row["listTime"])) if row.get("listTime") else None,
            "baseCcy": row.get("baseCcy"),
            "quoteCcy": row.get("quoteCcy"),
        }
    finally:
        client.close()


def measure_1m_span(inst: str) -> dict:
    """Measure first/last available 1m via history-candles (fail-closed facts)."""
    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
    try:
        # newest
        page, _ = fetch_okx_history_candles_page(
            client, inst, "1m", rest_base=OKX_REST, limit=OKX_HISTORY_LIMIT_MAX
        )
        if not page:
            return {"inst_id": inst, "status": "NO_DATA", "n_sample": 0}
        newest = max(b.ts_open_ms for b in page)
        # walk back aggressively to find listing-ish oldest (cap pages)
        after = newest
        oldest = newest
        pages = 0
        # Jump using listTime-ish: request after far past
        # Better: paginate with large jumps by setting after to successively older
        # For facts: sample at known anchors + paginate ~50 pages back from newest is not enough.
        # Use after=list-end anchors:
        anchors = [
            iso_ms("2026-09-01T00:00:00Z"),
            iso_ms("2026-06-01T00:00:00Z"),
            iso_ms("2026-01-01T00:00:00Z"),
            iso_ms("2025-07-01T00:00:00Z"),
            iso_ms("2025-01-01T00:00:00Z"),
            iso_ms("2024-01-01T00:00:00Z"),
            iso_ms("2023-05-01T00:00:00Z"),
        ]
        earliest_hit = None
        for a in anchors:
            p, raw = fetch_okx_history_candles_page(
                client, inst, "1m", rest_base=OKX_REST, after=a, limit=1
            )
            time.sleep(0.05)
            if p:
                earliest_hit = p[0].ts_open_ms
                break
        # From earliest_hit, page backward a bit to refine first candle near listing
        if earliest_hit is not None:
            after = earliest_hit
            first = earliest_hit
            for _ in range(30):
                p, raw_n = fetch_okx_history_candles_page(
                    client, inst, "1m", rest_base=OKX_REST, after=after, limit=OKX_HISTORY_LIMIT_MAX
                )
                pages += 1
                if not p:
                    break
                first = min(b.ts_open_ms for b in p)
                if raw_n < OKX_HISTORY_LIMIT_MAX:
                    break
                after = first
                time.sleep(0.12)
            oldest = first
        days = (newest - oldest) / (86400_000)
        return {
            "inst_id": inst,
            "status": "OK",
            "first_1m_open_iso": ms_iso(oldest),
            "last_1m_open_iso": ms_iso(newest),
            "span_days_approx": round(days, 2),
            "pages_refine": pages,
        }
    finally:
        client.close()


def run_w2() -> None:
    out = CACHE_ROOT / "w2"
    out.mkdir(parents=True, exist_ok=True)
    fetch_start = iso_ms(W2_TRADE[0])
    fetch_end = iso_ms(W2_TRADE[1])
    warm_start = iso_ms(W2_WARMUP_START)
    # Fetch order: higher TF first (fast), then 15m, then 1m
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
                    reuse_warmup_to=warm_start,
                )
                for inst in W2_INSTS
            ]
            for fut in as_completed(futs):
                print("RESULT", fut.result(), flush=True)


def run_w1(insts: tuple[str, ...] | None = None) -> None:
    out = CACHE_ROOT / "w1"
    out.mkdir(parents=True, exist_ok=True)
    targets = insts or W1_CANDIDATES
    fetch_start = iso_ms(W1_WARMUP_START)  # include warmup in fetch for sleeve (no 2020)
    fetch_end = iso_ms(W1_TRADE[1])
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
                    reuse_warmup_to=None,
                )
                for inst in targets
            ]
            for fut in as_completed(futs):
                print("RESULT", fut.result(), flush=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="#145 public MD fetch (paper)")
    p.add_argument("--window", choices=("w1", "w2", "both", "probe"), default="w2")
    p.add_argument("--w1-insts", default=",".join(W1_CANDIDATES))
    args = p.parse_args(argv)
    if args.window == "probe":
        facts = []
        for inst in W1_CANDIDATES:
            listing = probe_spot_listing(inst)
            span = measure_1m_span(inst) if listing.get("listed") else {"status": "NO_DATA"}
            facts.append({**listing, **{f"hist_{k}": v for k, v in span.items() if k != "inst_id"}})
            print(json.dumps(facts[-1], indent=2), flush=True)
        out = CACHE_ROOT / "w1_probe.json"
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(facts, indent=2) + "\n")
        print("WROTE", out)
        return 0
    if args.window in ("w2", "both"):
        run_w2()
    if args.window in ("w1", "both"):
        insts = tuple(x.strip() for x in args.w1_insts.split(",") if x.strip())
        run_w1(insts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
