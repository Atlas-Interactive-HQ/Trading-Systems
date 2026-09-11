# 78 — Scalp-HFT Layer B capture plan (OKX EEA DOGE X-Perp)

**Status:** engineering plan + first collector hooks · **paper / public MD only**  
**Lane:** Scalp-HFT Layer B (continuous forward capture)  
**Forecast status:** `not_a_forecast`  
**Live execution:** forbidden (`place_orders` false; no private WS; no API keys)  
**Soft PASS:** N/A · Mid **#71** unchanged · Live ≤€20 practice (unrelated to this lane)  
**Config:** `config/default.yaml` **untouched** (CLI overrides only)  
**Companions:** [`75`](./75-scalp-hft-v1-design.md) · [`76`](./76-scalp-hft-v1-rule-card.md) · [`77`](./77-scalp-hft-v1-eval-plan.md) · `research/scalp_hft_v1.lock.json`

**Freeze note:** leave `lock.json` hash TODOs as-is until the **first Layer B scored paper run**. Do not invent PnL. Do **not** start Layer A scored HFT eval from this plan.

---

## 1. Goal

Continuously capture **public** OKX EEA market data for **DOGE X-Perp** sufficient to build a causal **1s VAMP-5** pipeline and later run **Layer B** forward paper-sim (execution economics). This closes the inventory gap called out in [`77`](./77-scalp-hft-v1-eval-plan.md) §3 (“continuous ~100ms books + trades + mark + funding … MISSING beyond single-day smoke”).

Out of scope here:

- Layer A scored R1–R7 HFT eval / fabricated metrics
- Live / demo order placement
- Mutating Mid #71 or `default.yaml`
- Freezing lock hashes (deferred)

---

## 2. Instrument discovery (instId)

| Role | instId | Source |
|------|--------|--------|
| **Layer B public MD (primary)** | `DOGE-USD_UM_XPERP-310404` | `config/default.yaml` → `okx.doge_demo.xperp.md_inst_id` + `venues.okx_eea.xperp_symbols`; README “Public vs demo X-Perp instId”; catalogue `data/reports/okx-eea-xperp-universe-2026-09-02.md` |
| Demo **order** listing (NOT for public MD) | `DOGE-USD_UM_XPERP-310516` | signed demo `account/instruments` — **refuse** for Layer B capture |
| Classic SWAP (proxy only) | `DOGE-USDT-SWAP` / `DOGE-USD-SWAP` | require `--allow-proxy-swap`; label **SYNTHETIC / PROXY** — not Layer B primary |
| Nonexistent | `DOGE-USDC-SWAP` | historically HTTP `51001` — always refuse |

**Live verification procedure (fail-closed, public REST, no auth):**

```bash
# From repo root, with venv
python - <<'PY'
import httpx
inst = "DOGE-USD_UM_XPERP-310404"
base = "https://eea.okx.com"
with httpx.Client(headers={"User-Agent": "atlas-trading/0.1 public-md"}, timeout=30) as c:
    for path, params in [
        ("/api/v5/market/ticker", {"instId": inst}),
        ("/api/v5/public/mark-price", {"instId": inst}),
        ("/api/v5/public/funding-rate", {"instId": inst}),
        ("/api/v5/public/instruments", {"instType": "FUTURES", "instId": inst}),
    ]:
        j = c.get(base + path, params=params).json()
        assert j.get("code") == "0" and j.get("data"), (path, j)
        print(path, "OK", {k: (j["data"][0] or {}).get(k) for k in
              ("instId","instType","state","ruleType","last","markPx","fundingRate")})
PY
```

**Verified on this box (2026-09-11 UTC):** ticker `code=0`, mark-price present, funding-rate present, instruments `state=live` `ruleType=xperp` `ctVal=10` `settleCcy=USD`.

Code constant: `LAYER_B_DOGE_XPERP_MD_INST` in `src/atlas/collectors/okx_eea_public.py`. Collector `verify_public_inst_ids()` probes ticker before WS subscribe when `--capture` runs.

---

## 3. Endpoints & channels

| Item | Value |
|------|-------|
| REST base | `https://eea.okx.com` |
| Public WS | `wss://wseea.okx.com:8443/ws/v5/public` |
| Docs | https://my.okx.com/docs-v5/en/#overview-websocket-overview |
| Auth | **none** (public only; `refuse_if_secrets_present`) |

### WS subscribe args (Layer B default)

```json
{
  "op": "subscribe",
  "args": [
    {"channel": "books5", "instId": "DOGE-USD_UM_XPERP-310404"},
    {"channel": "trades", "instId": "DOGE-USD_UM_XPERP-310404"},
    {"channel": "mark-price", "instId": "DOGE-USD_UM_XPERP-310404"},
    {"channel": "funding-rate", "instId": "DOGE-USD_UM_XPERP-310404"}
  ]
}
```

Constant: `LAYER_B_WS_CHANNELS = ("books5", "trades", "mark-price", "funding-rate")`.

| Channel | Role for VAMP / paper |
|---------|------------------------|
| `books5` | Top-5 bid/ask **px + sz** → VAMP-5 + mid on 1s clock |
| `trades` | Print tape for toxicity / bar sanity / fill realism later |
| `mark-price` | Risk / net margin ROI / liq-aligned mark (design §4) |
| `funding-rate` | Cost model (funding drag) |

**REST sidecar (optional, default on in `--capture`):** low-rate poll of `/api/v5/public/mark-price` and `/api/v5/public/funding-rate` (~every 30s) written as `mark_price` / `funding_rate` channels — backup if WS mark/funding is sparse.

**Not subscribed in v1 capture:** `books-l2-tbt` / `books50-l2-tbt` (VIP / contiguous-seq path; books5 is thinned). Revisit only if books5 proves insufficient for causal VAMP.

---

## 4. Seq / gap handling

| Stream | Policy |
|--------|--------|
| All frames | Monotonic `local_seq` via `SequenceTracker`; `receive_ts` stamped at I/O |
| `books5` / `bbo-tbt` | `seqId` may **skip** (thinned snapshots) — **not** treated as hard gaps. Collector records samples + non-monotonic regressions in `seq_health` summary |
| `books-l2-tbt` / `books50-l2-tbt` | Contiguous venue-seq gap → write `sequence_gap` with `is_gap=true` (not used in Layer B default channels) |
| WS disconnect | Write `ws_error` (`gap_reason=ws_reconnect`); exponential backoff reconnect; keep capturing until duration ends |
| WS `event=error` | Logged + raw `ws_error` line (`gap_reason=ws_error_event`) |
| Day boundary | `JsonlRawWriter` partitions by **UTC** `receive_ts` date automatically |

Fail-closed before capture: ticker probe must return `code=0` with data, else refuse.

---

## 5. Storage layout

Already implemented by `JsonlRawWriter`:

```
data/raw/okx_eea/{YYYY-MM-DD}/
  ws_subscribe.jsonl
  ws_books5.jsonl
  ws_trades.jsonl
  ws_mark-price.jsonl      # if WS channel delivers
  ws_funding-rate.jsonl    # if WS channel delivers
  mark_price.jsonl         # REST sidecar
  funding_rate.jsonl       # REST sidecar
  ws_error.jsonl           # reconnects / venue errors
  sequence_gap.jsonl       # only if L2-tbt subscribed
```

Envelope schema: `raw.envelope.v1` (`src/atlas/schemas/raw.py`) — venue, channel, `venue_instrument_id`, `exchange_ts`, `receive_ts`, `local_seq`, `ingest_run_id`, transport, gap flags, verbatim `payload`.

**Retention:** append-only; do not mutate historical JSONL. Recommend ≥90 days for Layer B research (owner decision). Compression (zstd) / Parquet normalize = later; not required for smoke.

**Disk note (this box):** `/` ~110G free; current `data/raw/okx_eea` ~1.2M. Continuous books5 on one symbol is modest vs disk — still monitor growth on long runs.

---

## 6. 1s VAMP resample pipeline (downstream of raw)

Not required to finish before smoke capture, but this is the **contract** raw must support:

1. **Ingest** `ws_books5` envelopes for `DOGE-USD_UM_XPERP-310404`.
2. Maintain last known top-5 bids/asks (px, sz). On each books5 update, refresh book state.
3. On each **closed UTC second** `t` (signal clock = 1s per design / lock):
   - `mid_t = (best_bid + best_ask) / 2`
   - `VAMP5_t` per design §5.2 / `research/scalp_hft_v1_sketch.py::calculate_vamp`
   - `vamp_edge_bps_t = 1e4 * (VAMP5 - mid) / mid`
   - Update EMA12/21 on `mid`; update 60s rolling z on edge
4. Carry forward last mark + funding as-of `t` (from WS or REST sidecar).
5. Emit `data/derived/okx_eea/{date}/vamp1s_DOGE-USD_UM_XPERP-310404.parquet` (or JSONL) — **future artifact**; path reserved, not implemented in this engineering step.

**Warmup:** 60s causal before any paper signal (eval plan §1). Missing book for a second → mark sample stale / skip trade (fail-closed), never invent depth.

---

## 7. Paper-sim gate (when capture is “enough”)

Layer B **scored paper** may start only when **all** hold:

| Gate | Criterion |
|------|-----------|
| Instrument | Live public MD on `310404` (ticker+mark+funding probe green) |
| Continuity | Multi-hour continuous capture with reconnect logs; no unexplained multi-minute blackouts during intended windows |
| Depth | `books5` lines contain usable bid/ask **sizes** for top 5 → causal VAMP reconstructible |
| Sidecars | Mark + funding present at least via WS **or** REST sidecar |
| Code freeze | Fill `research/scalp_hft_v1.lock.json` commit/manifest/fee TODOs **immediately before** first scored run (not now) |
| Labels | Results under `results/scalp_hft_v1/` with Layer B / forward-paper labeling; **no invented PnL** |
| Soft PASS | Remains **N/A** until Layer B economics exist |

Until then: capture + parser/unit tests only. **No** Layer A scored HFT eval kicked off from this workstream.

---

## 8. How to smoke-run (short)

Public only. From repo root with `.venv`:

```bash
# 30s Layer B capture (default inst + channels); verifies ticker then WS
python scripts/run_okx_public.py --capture --ws-only --duration-sec 30

# Explicit (same defaults)
python scripts/run_okx_public.py --capture --ws-only --duration-sec 30 \
  --inst-id DOGE-USD_UM_XPERP-310404 \
  --channels books5,trades,mark-price,funding-rate

# PROXY only (not Layer B primary) — classic SWAP
python scripts/run_okx_public.py --capture --ws-only --duration-sec 15 \
  --inst-id DOGE-USDT-SWAP --allow-proxy-swap \
  --channels books5,trades
```

Expect JSON summary with `ws.mode=ws_capture`, `paper_only=true`, `inst_ids=[DOGE-USD_UM_XPERP-310404]`, `by_channel` counts, `verified` ticker snapshot, `data_dir`. Inspect:

```bash
ls -la data/raw/okx_eea/$(date -u +%F)/
# look for ws_books5.jsonl / ws_trades.jsonl / …
```

Unit tests (no network): `pytest tests/unit/test_okx_layer_b_capture.py -q`

### Smoke evidence (this box, 2026-09-11 ~04:49 UTC / 06:49 Europe/Amsterdam)

```
python scripts/run_okx_public.py --capture --ws-only --duration-sec 20
→ verified DOGE-USD_UM_XPERP-310404 FUTURES last=0.08397
→ ws_frames=128  by_channel={ws_books5:26, ws_trades:1, ws_mark-price:99, ws_funding-rate:2}
→ seq_health books5_seq_samples=25, books5_seq_non_monotonic=0, gap_count=0
→ books5 payload: 5 bids + 5 asks with sizes (VAMP-reconstructible)
→ wrote data/raw/okx_eea/2026-09-11/{ws_books5,ws_trades,ws_mark-price,ws_funding-rate,…}.jsonl
```

B3 (WS mark/funding on X-Perp) cleared for this smoke — both channels delivered frames. REST sidecar also wrote `mark_price.jsonl` / `funding_rate.jsonl`.


---

## 9. Code touchpoints (this engineering step)

| Path | Change |
|------|--------|
| `src/atlas/collectors/okx_eea_public.py` | `LAYER_B_*` constants; `resolve_capture_inst_ids`; `verify_public_inst_ids`; `run_ws_capture` (channels, REST sidecar, seq_health); `run(..., ws_capture=)` |
| `scripts/run_okx_public.py` | `--capture` / `--ws-only` / `--inst-id` / `--channels` / `--allow-proxy-swap` |
| `tests/unit/test_okx_layer_b_capture.py` | allowlist fail-closed unit tests |
| `phase1/78-…` (this file) | plan |
| `config/default.yaml` | **untouched** |
| `research/scalp_hft_v1.lock.json` | **freeze TODOs left** |

---

## 10. Blockers / risks (explicit)

| ID | Blocker | Severity | Notes |
|----|---------|----------|-------|
| B1 | **Auth** | None for public MD | Public REST/WS need no keys. Secrets must stay absent (`refuse_if_secrets_present`). Demo order path is out of scope. |
| B2 | **instId live verification** | Cleared for smoke (2026-09-11) | Re-probe before long capture / scored paper; OKX may rotate listing ids. |
| B3 | **WS channel support for X-Perp mark/funding** | Watch | If WS `mark-price` / `funding-rate` error on X-Perp, REST sidecar covers; confirm in smoke `by_channel` / `ws_error`. |
| B4 | **books5 depth sufficiency** | Medium | Design prefers ~100ms L2; books5 is thinned top-5. May be enough for VAMP-5; if not, escalate to L2-tbt (possible VIP / rate limits — **UNVERIFIED**). |
| B5 | **Disk / retention** | Low now | 110G free on this box; long multi-day capture needs rotation/monitoring policy. |
| B6 | **deps** | Cleared | `websockets`, `httpx` in venv (`requirements.txt`). |
| B7 | **Auto-review / network policy** | Env-dependent | Public egress to `eea.okx.com` / `wseea.okx.com` required; if blocked, capture cannot run on that host. |
| B8 | **1s VAMP + paper-sim impl** | Open | Resample + paper OMS not built yet — capture-first. |
| B9 | **lock.json freeze** | Deferred by design | Fill hashes only before first Layer B scored paper run. |
| B10 | **Legal / ToS redistribution** | UNVERIFIED | Internal research use; no external dataset publish claim (see [`04`](./04-public-data-collection-plan.md)). |

---

## 11. Ops lock reminders

- Layer B only — do not push / open PR (coordinator owns PR #72 Mid RISK-UP).
- Do not invent PnL or fill `results/scalp_hft_v1/R*/` from this capture plan alone.
- Do not start Layer A scored HFT eval.
- Mid #71 unchanged; Soft PASS N/A; Live ≤€20; `not_a_forecast`.
