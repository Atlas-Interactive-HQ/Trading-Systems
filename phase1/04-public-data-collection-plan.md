# 04 — Public Market-Data Collection Plan (Kraken + OKX)

**Scope:** PUBLIC market data only. No private order/account credentials in this plan.  
**Paper equity context:** €200 scale plumbing; data pipeline must work before paper OMS.  
**Critical:** Public MD hosts and start symbols were preflighted 2026-09-01 (`07-venue-preflight-notes.md`). Remaining **UNVERIFIED**: legal redistribution rights, exact retail unlock matrices, and some channel edge-cases. **Paper OMS = OKX EEA demo** (later); Kraken Futures demo API **retired 2026-07-14** — public MD still on `futures.kraken.com`.

---

## 1. Objectives

1. Continuously collect public MD for **one liquid BTC perpetual** first (venue instrument id TBD after verification).  
2. Preserve **raw messages** append-only; normalize asynchronously to Parquet.  
3. Detect **gaps**, stale clocks, reconnect holes; support REST backfill where public history exists.  
4. Scale path to meme/AI/tech perps that pass liquidity/spread/funding gates — same collectors, config-driven symbols.  
5. UTC everywhere; stamp `receive_ts` at I/O boundary.

---

## 2. Venues (targets) — availability UNVERIFIED

| Venue | Intended product class | Public MD goal | Status |
|-------|------------------------|----------------|--------|
| Kraken Futures | BTC perpetual `PF_XBTUSD` (public MD) | WS + REST public books/trades/ticker/funding/status | **VERIFIED public hosts (2026-09-01):** REST `https://futures.kraken.com/derivatives/api/v3`, WS `wss://futures.kraken.com/ws/v1`. **Official Futures demo API retired 2026-07-14** — not used for paper OMS. Details: `07-venue-preflight-notes.md`. |
| OKX EEA | BTC `BTC-USDT-SWAP` + X-Perp discovery | WS + REST public | **VERIFIED public hosts:** REST `https://eea.okx.com`, public WS `wss://wseea.okx.com:8443/ws/v5/public`. **Paper OMS target (later) = OKX EEA demo** (not this public collector). See `07`. |
| Optional later | IB paper + CME Micros | Separate plan; redistribution rules strict | Deferred / **UNVERIFIED** |

**Legal note:** Collecting public market data for internal research is still subject to each venue’s ToS and applicable law. **UNVERIFIED** — read primary ToS before production deploy. No claim of license to redistribute datasets externally.

---

## 3. Channels to collect (logical)

Per symbol (neutral), map to venue channels after docs review:

| Logical stream | Why | Typical transport |
|----------------|-----|-------------------|
| Trades | Bar build, volume, toxicity | WS preferred; REST backfill |
| BBO / order book top (or L2 if cheap) | Spread gates, fill model | WS |
| Mark price | PnL / liq proximity | WS or REST ticker |
| Index price | Basis / regime | WS or REST |
| Funding rate + next funding time | Cost model | WS ticker and/or REST |
| Instrument status | Halt / settle gates | REST snapshot + WS status if any |
| Server time | Clock skew DQ | REST periodically |

Exact channel names/URLs: **UNVERIFIED** — cite official docs in `configs/collectors/*.yaml` comments when implemented.

---

## 4. Architecture per venue collector

```
WS primary loop ──► raw append (JSONL.zst) ──► normalize queue ──► Parquet
       │                                      ▲
       ├── sequence / heartbeat monitor       │
       └── on gap/reconnect ──► REST backfill ┘
REST periodic: funding, status, server time, snapshot reconcile
```

**Process model (ENGINEERING RECOMMENDATION):** one OS process (or container) per venue; multi-symbol multiplex on one WS connection where the venue allows.

---

## 5. Raw message preservation

- Path pattern (implemented Phase-1 scaffold): `data/raw/{venue}/{YYYY-MM-DD}/{channel}.jsonl` (UTC date). Optional later: channel/hour partitions + zstd.  
- Each line: `{ "receive_ts": …, "channel": …, "payload": <verbatim> }` or length-prefixed binary equivalent.  
- **Do not** mutate historical files; bad parses → quarantine + error log.  
- Retain raw ≥ research retention policy (recommend ≥ 90 days early; owner decision).  
- Content-hash optional every N messages for integrity audits.

---

## 6. Sequence, heartbeats, gap detection

| Mechanism | Behavior |
|-----------|----------|
| Venue sequence | If present, detect non-monotonic / skips → `collector.gap_detected` event |
| Local sequence | Always assign monotonic `local_seq` per stream for internal ordering |
| Heartbeat / ping | WS ping per venue guidance (**UNVERIFIED** intervals); treat missed pongs as reconnect |
| Stale data | If no trade/quote update beyond threshold (e.g. BTC > 60s during expected activity — **HYPOTHESIS** threshold) → degraded |
| Reconnect | Snapshot book/status via REST; mark gap interval `[last_good_ts, resume_ts)` in gap ledger |
| Backfill | Public REST trades/candles for gap window if API permits; mark `is_backfill=true` |

Gap ledger schema (minimal): `venue, channel, symbol, gap_start_ts, gap_end_ts, reason, backfill_status`.

---

## 7. Rate limits approach

**UNVERIFIED** exact numeric limits — read official rate-limit docs before coding.

**ENGINEERING RECOMMENDATION pattern:**

1. Central token-bucket / leaky-bucket per venue **and** per endpoint class (public WS subscribe vs REST).  
2. Prefer WS for high-frequency; REST for snapshots, funding history, time, gap fill.  
3. Exponential backoff + jitter on HTTP 429 / WS close; never spin reconnect.  
4. Global budget for multi-symbol: adding alts must not starve BTC stream (priority queue: BTC first).  
5. Cache instrument metadata; refresh on interval, not per message.  
6. Document assumed limits in config as comments with doc URL + retrieval date once verified.

---

## 8. Symbol scaling: BTC → alts

| Stage | Symbols | Collector change |
|-------|---------|------------------|
| A | 1× BTC perp | Full DQ bar; tune lag thresholds |
| B | + N meme/AI/tech perps | Same WS multiplex; config list; per-symbol gates |
| Gates before strategy use | Min ADV, max BBO spread bps, max \|funding\|, status=trading, DQ green | Fail closed → untradeable |

**Scaling costs:** bandwidth ≈ O(symbols × channels); normalize CPU; Parquet partitions per symbol. At non-HFT cadence, dozens of symbols are usually fine on one box — still validate disk & rate limits empirically.

**Position rule unchanged:** even with many symbols, **one directional position at a time** globally.

---

## 9. Normalization & bars

- Async workers read raw → emit `market.*` Parquet (see `03-data-schemas.md`).  
- 15m / 1h bars from trades (or venue candles if used — prefer trades for auditability).  
- Strategy may only consume `closed=true` bars.  
- Join funding onto bars by `funding_ts` without lookahead (use only funding known at bar close).

---

## 10. Security for public collection

- Public endpoints ideally need no secret; if a “public” key is required, treat as secret anyway (not in git/logs).  
- No withdrawal-capable keys in collector env.  
- Outbound allowlist firewall **ENGINEERING RECOMMENDATION**.

---

## 11. Acceptance criteria for “collection Phase 1 done”

1. ≥ 7 consecutive UTC days BTC raw + Parquet for at least one verified public venue feed.  
2. Gap ledger reviewed; unexplained gaps < agreed threshold.  
3. DQ suite (`05`) green or waivers documented.  
4. Replay of one day yields stable bar hashes.  
5. Primary-source citations filed for V1/V2/V7 (see `00-decisions-and-deltas.md`).

---

## 12. Explicit non-goals

- Private fill/order streams (later paper OMS).  
- Scraping authenticated web UIs.  
- Redistributing paid exchange data.  
- Live trading.
