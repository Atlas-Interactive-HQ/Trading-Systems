# 85 — Layer B 4h capture + VAMP-1s checkpoint (2026-09-11)

**Status:** metrics checkpoint · **paper / schema only**  
**Lane:** Scalp-HFT Layer B (continuous capture → 1s VAMP-5)  
**Forecast status:** `not_a_forecast`  
**Soft PASS:** **N/A** (no strategy PnL / expectancy / soft-promote claim)  
**Live:** **HALTED** (≤€20 practice unrelated; no OMS; no private WS)  
**Config:** `config/default.yaml` **untouched**  
**Upstream:** [`78`](./78-scalp-hft-layer-b-capture.md) capture · [`79`](./79-scalp-hft-vamp-pipeline.md) VAMP pipeline · [`84`](./84-atlas-trading-vnext-ladders.md) vNext ladders  
**Next:** vNext **HFT ladder** (Layer B corpus gate) — no green/red HFT claim from this note alone

---

## 1. Capture process

| Item | Value |
|------|-------|
| Process | **gone** (PID `976149` not running; no `run_okx_public` / capture procs) |
| Cmd (started) | `python scripts/run_okx_public.py --capture --ws-only --duration-sec 14400 --inst-id DOGE-USD_UM_XPERP-310404` |
| Started | 2026-09-11T05:01:12Z (07:01:12 CEST) |
| Planned duration | 14400 s (4h) |
| Day dir span (incl. prior ~04:49 smoke) | ~2026-09-11T04:49:20Z → ~09:01:11Z UTC (~4.20 h wall) |
| End log | `logs/okx_public_capture_4h_20260911T050112Z.log` **missing** on box (`logs/` dir absent at checkpoint); collector `gap_count` / end JSON **not recoverable from disk** |
| Reconnect markers in raw | `ws_error.jsonl` **2** lines, both `is_gap=true` `gap_reason=ws_reconnect` (~07:41Z, ~07:58Z UTC) |
| Channel `is_gap` on books5/trades/mark/funding | **0** |

Raw JSONL remains **gitignored** under `data/raw/okx_eea/`.

---

## 2. Raw line counts (`data/raw/okx_eea/2026-09-11/`)

| File | Lines |
|------|------:|
| `ws_books5.jsonl` | 12118 |
| `ws_trades.jsonl` | 548 |
| `ws_mark-price.jsonl` | 71932 |
| `ws_funding-rate.jsonl` | 251 |
| `ws_error.jsonl` (sidecar) | 2 |
| REST sidecar `mark_price.jsonl` / `funding_rate.jsonl` | 477 / 477 |

---

## 3. VAMP 1s replay (metrics schema only)

```bash
python scripts/replay_scalp_hft_vamp1s.py --date 2026-09-11
```

Input: `data/raw/okx_eea/2026-09-11/ws_books5.jsonl` · inst `DOGE-USD_UM_XPERP-310404` · `paper_only=true`.

| Metric | Count |
|--------|------:|
| `n_samples_1s` | 15109 |
| `n_vamp_valid` | 15109 |
| `n_vamp_z_valid` | 14442 |
| `n_ema12_ready` | 15098 |
| `n_ema21_ready` | 15089 |
| `n_seconds_with_update` | 6398 |
| `n_seconds_stale_carry` (`book_stale`) | 8711 |
| **stale fraction** (`n_seconds_stale_carry / n_samples_1s`) | **8711 / 15109 ≈ 0.5765** |

**Schema columns (metrics only):** `ts_s`, `inst_id`, `mid`, `vamp5`, `vamp_edge_bps`, `vamp_z`, `ema12`, `ema21`, `best_bid`, `best_ask`, `book_stale`, `n_bid_levels`, `n_ask_levels`, `vamp_valid`.

Local outputs (gitignored): `results/scalp_hft_v1/layer_b_samples/vamp1s_DOGE-USD_UM_XPERP-310404_2026-09-11.{csv,parquet}`.

Ingest notes (not PnL): `n_book_events=12113`, `seq_id_non_monotonic=0`, `seq_id_skips=10040` (books5 thinned — expected per [`79`](./79-scalp-hft-vamp-pipeline.md)).

---

## 4. Explicit non-claims

- **Soft PASS:** N/A — no strategy, fills, expectancy, or soft-promote.
- **Live:** HALTED — no arm / OMS / private endpoints.
- **HFT green/red:** forbidden without Layer B scored ladder per [`77`](./77-scalp-hft-v1-eval-plan.md) / [`84`](./84-atlas-trading-vnext-ladders.md).
- **Next work:** vNext **HFT ladder** on this corpus (still metrics / paper-sim path only until lock).

