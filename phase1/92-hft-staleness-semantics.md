# 92 — HFT staleness semantics (P1)

**Stance:** Research / metrics-only. `not_a_forecast: true`. **NO HFT PnL.**
**Config:** `config/default.yaml` **untouched**.
**Live:** HALTED. No OMS / private WS.
**Does not rewrite:** historical counts in [`79`](./79-scalp-hft-vamp-pipeline.md) or [`85`](./85-layer-b-4h-capture-vamp-checkpoint.md).

---

## Old meaning (too coarse)

VAMP 1s replay marked every 1s bucket **without a new books5 update** as `book_stale=true`. That bundled two different facts:

1. The book was **carried forward** for feature continuity (no new snapshot in this second).
2. The book was **too old to trade** (exchange ts more than the 1000 ms health threshold behind the decision clock).

A book that arrived 100 ms into second `t` and is reused at second `t+1` (age 900 ms) is a carry, **not** a health kill.

---

## Corrected fields

| Field | Meaning |
|-------|---------|
| `carried_forward` | No new books5 in this 1s bucket. Last book reused for feature continuity. |
| `book_stale` | **Legacy alias of `carried_forward`** (not `health_stale`) so old CSV columns stay comparable. |
| `book_age_ms` | `decision_ts_ms − last valid books5 exchange ts`. Decision ts = sample label / start of the 1s bucket (`ts_s * 1000`). |
| `health_stale` | `book_age_ms > 1000` (existing phase1/75 `KILL_LATENCY`). |
| `ts_rewind` | Exchange book timestamp went backwards vs the previous sample. |

Trading health = `health_stale OR ts_rewind OR reconnect_in_second`.
**Not** `carried_forward` alone.

`seqId` skips on books5 are **not** missing packets: snapshots are self-contained (already noted in ingest stats).

---

## H0 health-only re-run

```bash
python scripts/run_hft_h0_health.py
```

**This PR's H0 re-run (2026-09-11 agent box):** `python scripts/run_hft_h0_health.py` exited 2 with `insufficient_data` — no `data/raw/okx_eea/**/ws_books5.jsonl` (raw is gitignored). **No invented** `n_health_stale` / reconnect counts. Historical 79/85 tables stay as written.

When a real capture is present, report `n_carried_forward` vs `n_health_stale` vs `n_trading_unhealthy` under `results/accounting_v2/h0_health_only.json`. Still **no** HFT PnL.

---

## Honesty

- Feature carry remains useful; do not drop it.
- Do not treat a high stale-carry fraction from #85 as a health-kill fraction.
- No green/red HFT claim from this note.

`not_a_forecast: true`. `place_orders: false`.
