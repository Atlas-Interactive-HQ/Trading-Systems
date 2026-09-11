# 102 — Trial ledger (multiplicity)

**Stance:** Research governance. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. No hyperopt. No post-hoc winners.
**Board:** part of step **A** ([`106`](./106-research-governance-board.md)). Future GREEN must read this before claiming a deflated edge.

---

## Why a ledger

Every scored hypothesis is a draw from a search. Soft PASS on a rise panel after many rungs is not the same evidence as a single pre-registered shot. **Future GREEN must account for trial count.**

This note registers the ledger. It does **not** invent a Deflated Sharpe Ratio or PBO number. DSR (Harvey / Liu / Zhu and the Bailey / López de Prado Deflated Sharpe line) and PBO (probability of backtest overfitting) are **conceptual references**: more trials → more of the apparent Sharpe is selection. Compute those statistics later on a complete census; do not invent deflated Sharpe in this PR.

---

## Schema

File: `research/trial_ledger.jsonl` (append-only JSONL).  
Code: `atlas.research.trial_ledger.TrialRecord` / `load_trial_ledger`.  
Schema version: `research.trial_ledger.v1`.

| Field | Type | Meaning |
|-------|------|---------|
| `trial_id` | string | Stable id (`TL-S1`, …) |
| `parent_trial` | string \| null | Prior rung or phase1 id |
| `family` | string | `mid` / `scalp` / `core` / `hft` / `integrity` / … |
| `hypothesis` | string | What was tested, in words |
| `parameters` | object | Locked card (no sweep leftovers) |
| `asset` | string | Research MD id |
| `timeframe` | string | Decision bar |
| `data_seen_before_lock` | string | What the authors had already seen |
| `dataset` | string | phase1 / panel citation |
| `lock_commit` | string \| null | Git SHA of the lock |
| `score_commit` | string \| null | Git SHA of the first score |
| `result` | object | Citations + honesty labels — **not** a new PnL table |
| `pass_fail` | string | Gate verdict as published |
| `pre_registered` | bool | Locked before score? |
| `post_hoc` | bool | Winner picked after seeing €? |
| `global_trial_count` | int | Sequence **within `count_scope`** |
| `family_trial_count` | int | Sequence within family, same scope |

Every row carries `not_a_forecast`, `place_orders: false`, `soft_pass_neq_arm`.  
`count_scope` for the starter file is `starter_mainline_v1`.

---

## Starter file is not a census

`research/trial_ledger.jsonl` backfills **named mainline** trials from existing phase1 docs / PR numbers. It is **not** a complete count of phase1/16–99.

Before any GREEN CANDIDATE declaration, expand the census to every scored hypothesis that touched the same families or the same data (including eliminated rungs). Use that full `global_trial_count` when discussing DSR/PBO. Do not treat starter `global_trial_count` (now **8** after `TL-DEV-BOARD` lock row) as the research-wide N.

---

## Starter rows (citations only — no invented PnL)

| trial_id | PR / phase1 | pass_fail (published) |
|----------|-------------|------------------------|
| `TL-INT85` | PR **#85** · [`90`](./90-evaluation-integrity-audit.md)–[`94`](./94-core-r1-lock.md) | `N/A_audit_does_not_promote` |
| `TL-M1` | PR **#81** · [`86`](./86-rise-panel-mid-m1-adx-4h.md) | `soft_PASS_but_worse` vs #71 |
| `TL-S1` | PR **#82** · [`87`](./87-rise-panel-scalp-s1-rvol-1h.md) | `soft_PASS_and_better` vs #83 |
| `TL-C1` | PR **#83** · [`88`](./88-rise-panel-core-c1-donchian40-20-1d.md) | `FAIL` |
| `TL-C2` | PR **#84** · [`89`](./89-rise-panel-core-c2-donchian40-20-ema50-200-1d.md) | `FAIL` (Donchian family stopped) |
| `TL-CORE-R1` | lock PR **#85** [`94`](./94-core-r1-lock.md) · score PR **#86** [`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md) | `v2_PASS_DEV_only` — not a promote |
| `TL-SCALP-R2` | lock PR **#85** [`93`](./93-frozen-mid-scalp-candidates.md) · score PR **#88** [`99`](./99-rise-panel-scalp-r2-dt-4h-regime-1h.md) | `FAIL` |
| `TL-DEV-BOARD` | [`108`](./108-dev-board-research-lock.md) | `N/A_research_lock_not_a_score` (Mid #71 + S1 + Core CASH) |

Result objects **cite** those notes. They do not restate panel € tables as a new score. Soft PASS ≠ arm.

S1’s published DEV Δ vs #83 is **€1.4637** panel net ([`87`](./87-rise-panel-scalp-s1-rvol-1h.md)). That number is a citation, not a re-score. [`103`](./103-edge-vs-luck-stress.md) treats the margin of safety as small until stress.

---

## Honesty / invalidation

- Do not add a row after seeing a number and mark `pre_registered: true`.
- Do not omit FAIL rungs to shrink N.
- Do not invent a deflated Sharpe, haircut, or PBO percentage here.
- `not_a_forecast: true`. `place_orders: false`.
