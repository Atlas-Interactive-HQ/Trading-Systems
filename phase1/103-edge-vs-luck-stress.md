# 103 — Edge-vs-luck + stress (registered, not scored)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. No hyperopt.
**Depends on:** contiguous SHADOW lock ([`101`](./101-shadow-contiguous-methodology.md)). **Not ready to score.**
**Families:** Mid **#71** ([`72`](./72-mid-long-strengthen.md)) and Scalp **S1** ([`87`](./87-rise-panel-scalp-s1-rvol-1h.md)).
**Board:** step **D** of [`106`](./106-research-governance-board.md).

---

## When this may run

1. SHADOW start/end are locked after the contamination audit ([`101`](./101-shadow-contiguous-methodology.md)).
2. The frozen Mid #71 and S1 cards are walked **once** on that interval (no param rescue).
3. Only then: placebo / block-bootstrap and the stress matrix below.

`classify_edge(..., shadow_locked=False)` returns `not_scored`. That is the state of this PR.

---

## Placebo / block-bootstrap (registered)

Framework id: `edge_vs_luck_placebo_block_bootstrap_v1`.

**Placebo timing:** keep the trade *duration* / holding structure; destroy the alignment between signal time and path (circular shift or random entry times inside the same SHADOW span, block-respecting). The placebo distribution is the expectancy-after-costs of those fake books.

**Block bootstrap:** resample SHADOW in contiguous blocks (block length locked once before the run; no search). Recompute expectancy-after-costs on each resample.

Do not tune block length or placebo count after seeing the percentile. No hyperopt.

### Verdict rule (locked)

Let `obs` = completed-trade expectancy after costs on SHADOW.  
Let `P90` / `P95` = 90th / 95th percentiles of the placebo (or block-bootstrap) expectancy distribution.

| Verdict | Rule |
|---------|------|
| **EDGE CONFIRMED** | `obs > P90` |
| **STRONG** | `obs > P95` |
| **INCONCLUSIVE** | `obs ≤ P90` |

Insufficient placebo draws or missing SHADOW → `insufficient_data` (fail closed).  
EDGE CONFIRMED ≠ arm. STRONG ≠ arm. Soft PASS ≠ arm.

Code: `atlas.research.edge_vs_luck.classify_edge`.

---

## Stress matrix (registered — not a new strategy)

Stressing #71 or S1 is **the same strategy** under a harsher world. It is not M2, not S2, not a new family, not a reason to grind RVOL.

| Id | What |
|----|------|
| `costs_1_5x` | PaperSettings fees+slip × **1.5** |
| `costs_2x` | fees+slip × **2** |
| `next_open_plus_1_bar` | Fill at the open **one bar later** than the locked next-open model |
| `adverse_slip` | Extra adverse touch on entry and exit (magnitude locked once before the run) |
| `block_bootstrap` | Same as the luck framework; report interval, not a new tip |
| `placebo_timing` | Same as the luck framework |
| `chronological_shadow` | The SHADOW walk itself (baseline for the stresses) |

Report all cells. Do not drop the cell that hurts. Do not promote a “stress-robust” variant that changed parameters.

Code: `atlas.research.edge_vs_luck.stress_plan` / `STRESS_MATRIX`.

---

## S1 margin of safety is small

S1 vs #83 on R1–R7 DEV: panel-net Δ **€1.4637** ([`87`](./87-rise-panel-scalp-s1-rvol-1h.md); cited, not re-scored). Median exp was unchanged. That is a **tiny** DEV increment on a €20 sleeve.

Until SHADOW + this matrix exist, treat S1’s margin of safety as **small**. Do not arm Scalp on Soft PASS. Do not grind RVOL 1.25/1.5 ([`93`](./93-frozen-mid-scalp-candidates.md)).

---

## Honesty / invalidation

- Do not score this framework in this PR.
- Do not run placebo on R1–R7 and call it SHADOW robustness.
- Do not invent percentile tables or a deflated Sharpe.
- `not_a_forecast: true`. `place_orders: false`.
