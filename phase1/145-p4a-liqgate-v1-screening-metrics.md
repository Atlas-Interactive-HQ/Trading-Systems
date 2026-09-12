# 145 — P4a liqgate_v1 SCREENING metrics (2026-09-11→12)

**Stance:** Research / capture screening. `not_a_forecast: true`. **NO strategy PnL. NO instrument selected.**
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm · capital parked · HALTED practice caps unchanged by this note.
**Parents:** [`100`](./100-p4a-screening-p4b-7d.md) (P4a screening-only / P4b 7d lock) · [`95`](./95-hft-liquidity-gate-plan.md) (`METRIC_FIELDS`) · health split [`92`](./92-hft-staleness-semantics.md).
**Artifact:** [`results/accounting_v2/p4a_liqgate_v1_screening_2026-09-12.json`](../results/accounting_v2/p4a_liqgate_v1_screening_2026-09-12.json)
**Code gate:** `atlas.scalp_hft.liquidity_gate.p4a_screen` → `selected=None`, `instrument_lock=False`.

---

## Capture status (verified)

| Item | Measured |
|------|----------|
| Dir | `data/liqgate_v1` |
| Process | **not running** (finished) |
| Planned start | 2026-09-11T16:23:30Z (`started_unix` 1789143810) · duration **86400** s |
| Actual first `receive_ts` | **2026-09-11T16:23:36.291Z** |
| Actual last `receive_ts` | **2026-09-12T16:26:55.233Z** |
| Actual span | **86598.942** s (~24.06 h) — `looks_complete_approx_24h` |
| InstIds present | `BTC-USD_UM_XPERP-310404` · `ETH-USD_UM_XPERP-310404` · `DOGE-USD_UM_XPERP-310404` |
| Channels present | `books5` · `trades` · `mark-price` · `funding-rate` (all four wrote; matrix in JSON) |
| Global `ws_reconnect` | **5** (shared across names) |
| Other `is_gap` (non-reconnect) | **0** |
| Screening warnings (dead name) | **none** (`trades/sec>0` and `books5/sec>0` for all three) |

---

## SCREENING-ONLY metrics (measured)

Rates use per-instrument span = last−first `receive_ts`. Trade rate counts individual prints in `payload.data`. Books5 rate counts envelope updates. Spread/depth percentiles are **exact full-stream** over books5 updates. Depth = Σ `px*sz` over top-5 bids+asks (**no `ctVal` rescale** — contract units as published; cross-name depth is not USD-normalized). Health: 1s buckets on `receive_ts`; `book_age_ms = decision_ms − last books5 exchange_ts`; `health_stale` if `book_age_ms > 1000`; `carried_forward` if no books5 in that second (phase1/92 — these are **not** the same counter).

| Field | BTC | ETH | DOGE |
|-------|----:|----:|-----:|
| `span_s` | 86598.94 | 86598.917 | 86598.916 |
| `trades_per_sec` | 0.417118 | 0.514256 | 0.082668 |
| `n_trades` | 36122 | 44534 | 7159 |
| `books5_changes_per_sec` | 3.308343 | 5.026264 | 1.220292 |
| `n_books5_envelope_updates` | 286499 | 435269 | 105676 |
| `spread_bps_median` | 0.012942 | 0.039793 | 3.549246 |
| `spread_bps_p95` | 0.012978 | 0.904135 | 5.942830 |
| `top5_depth_notional_median` | 1332251775.60 | 9641020.32 | 722.83 |
| `top5_depth_notional_p95` | 2835504740.19 | 38790937.24 | 4983.44 |
| `reconnect_count` (global shared) | 5 | 5 | 5 |
| `gap_count` | 0 | 0 | 0 |
| `book_age_ms_median` | 299.0 | 293.0 | 995.0 |
| `book_age_ms_p95` | 2099.0 | 1592.0 | 7799.0 |
| `n_health_stale` | 12436 | 7887 | 41982 |
| `n_carried_forward` | 10879 | 6885 | 39721 |
| `health_n_buckets` | 86599 | 86598 | 86597 |

---

## Gate result

```text
p4a_screen → selected=None · instrument_lock=False
```

**P4a does not lock an HFT instrument.** Rankings / favourites from this 24h window are **not** a promote path (phase1/100). Soft PASS **N/A** (liquidity/health only).

---

## Explicit non-claims

- No HFT instrument pick · no DOGE default · no H1 economic start from these rates.
- No strategy PnL / expectancy / soft-promote.
- **P4b not started** by this note (7 full calendar days + slice stability remains the only lock).
- `config/default.yaml` untouched · `place_orders: false` · `not_a_forecast: true`.

`soft_pass_neq_arm`. Capital parked.
