# 98 — H0 health-stale stamp (2026-09-11 Layer B corpus)

**Stance:** Research / health-only diagnostics. `not_a_forecast: true`. **NO HFT PnL.**
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. No OMS / private WS.
**Soft PASS:** **N/A** (no strategy PnL / expectancy / soft-promote claim).
**Semantics:** [`92`](./92-hft-staleness-semantics.md) — `carried_forward` ≠ `health_stale`.
**Corpus checkpoint:** [`85`](./85-layer-b-4h-capture-vamp-checkpoint.md) — same 2026-09-11 books5 capture; **85 numbers not rewritten**.
**Branch:** `research/h0-health-stale-98` from `main` after PR #86. **Not** SCALP-R2 (reserved **99**).
**Next:** No H1 until corpus quality gate. Diagnostics only.

---

## Measured (coordinator local re-run 2026-09-11; verified)

Artifact: [`results/accounting_v2/h0_health_stale_2026-09-11.json`](../results/accounting_v2/h0_health_stale_2026-09-11.json)  
Input: `data/raw/okx_eea/2026-09-11/ws_books5.jsonl` (gitignored raw) · inst `DOGE-USD_UM_XPERP-310404`.

| Metric | Value |
|--------|------:|
| `n_samples_1s` (`n`) | **15109** |
| `carried_forward` (old “stale” / feature carry) | **8711** (**57.65%**) |
| `health_stale` (`book_age_ms > 1000`) | **5926** (**39.22%**) |
| `n_reconnect` | **2** |
| `book_age_ms` median | **398** ms |
| `book_age_ms` p95 | **15498** ms (**≈15.5 s**) |

Trading health = `health_stale OR ts_rewind OR reconnect` — **not** `carried_forward` alone ([`92`](./92-hft-staleness-semantics.md)).

### Cite [`85`](./85-layer-b-4h-capture-vamp-checkpoint.md)

Phase1/85 reported the same capture with the **old** coarse label: `n_seconds_stale_carry` / `book_stale` = **8711 / 15109 ≈ 0.5765**. That is **`carried_forward`** (feature continuity), **not** the health-kill fraction. Do not treat the #85 stale-carry rate as `health_stale`.

### Cite [`92`](./92-hft-staleness-semantics.md)

| Field | Meaning |
|-------|---------|
| `carried_forward` | No new books5 in this 1s bucket; last book reused for features. |
| `book_stale` | Legacy alias of `carried_forward` (not `health_stale`). |
| `health_stale` | `book_age_ms > 1000` (KILL_LATENCY). |
| `book_age_ms` | decision clock − last valid books5 exchange ts. |

---

## Explicit non-claims

- **Soft PASS:** N/A — usable for **diagnostics only**.
- **No HFT PnL** / no green-red HFT claim / no soft-promote.
- **No H1** until corpus quality gate.
- **Live HALTED** (≤€20 practice unrelated).
- Does **not** rewrite historical counts in [`79`](./79-scalp-hft-vamp-pipeline.md) or [`85`](./85-layer-b-4h-capture-vamp-checkpoint.md).
- Does **not** start SCALP-R2 (that is **phase1/99**).

`not_a_forecast: true`. `place_orders: false`. `no_hft_pnl: true`.
