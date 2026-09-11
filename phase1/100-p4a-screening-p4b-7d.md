# 100 — P4a screening / P4b 7-day HFT liquidity lock (amendment to #95)

**Stance:** Research / capture governance. `not_a_forecast: true`. **NO strategy PnL. NO instrument selected in this PR.**
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm.
**Amends:** [`95-hft-liquidity-gate-plan.md`](./95-hft-liquidity-gate-plan.md). Does not rewrite METRIC_FIELDS.
**Board:** this note is registered under step **B** of [`106`](./106-research-governance-board.md). It is locked **before** P4a 24h metrics are used for instrument selection.

**Do not invent capture numbers.** Do not headline a 24h favourite. Do not default to DOGE because Layer B already exists there.

---

## Why this amendment exists

[`95`](./95-hft-liquidity-gate-plan.md) pre-registered a 24h simultaneous BTC+ETH+DOGE EEA X-Perp capture and a selection rule **before** numbers existed. That 24h job is now running:

| Item | Locked fact |
|------|-------------|
| Role | **P4a SCREENING ONLY** |
| Dir | `data/liqgate_v1` |
| Started | ~**2026-09-11 16:23 UTC** (Fri→Sat 24h intent) |
| Names | BTC + ETH + DOGE X-Perp **simultaneously** |
| Channels | `books5` · `trades` · `mark-price` · `funding-rate` (same as Layer B / #95) |
| Metrics | same `METRIC_FIELDS` as [`95`](./95-hft-liquidity-gate-plan.md) / `atlas.scalp_hft.liquidity_gate` |
| PnL | **none** |

A single Friday→Saturday day **cannot** lock the HFT instrument. Overnight US / weekend thinness / one spectacular hour would be enough to pick a name that is not the 7-day name. **P4a must not lock.**

---

## P4a — screening only

Allowed uses of the current 24h capture, **after** it finishes and is summarized without invention:

1. Confirm the three live instIds resolved (fail closed if any missing; do not invent ETH).
2. Confirm all four channels actually wrote.
3. Confirm the metric pipeline emits the locked `METRIC_FIELDS` (including P1 `n_health_stale` / `n_carried_forward` split).
4. Flag obvious dead names (`trades/sec == 0` or `books5 changes/sec == 0`) as **screening warnings**, not as a lock.

Forbidden:

- Calling `select_instrument` (or any ranking) and treating the winner as the HFT name.
- Using P4a ranks to start H1 economic work, queue sims, or DOGE-default.
- Inventing rates, spreads, depths, reconnects, or book-age numbers in docs.

Code: `atlas.scalp_hft.liquidity_gate.p4a_screen` always returns `selected=None`, `instrument_lock=False`. Even a complete 24h fixture cannot lock.

---

## P4b — 7 full calendar days (the only lock)

Final HFT instrument lock requires **P4b**:

| Constraint | Lock |
|------------|------|
| Span | **7 full calendar days** UTC (not 24h, not “about a week”) |
| Names | same three X-Perps **simultaneously** |
| Channels | same four: books5, trades, mark-price, funding-rate |
| Metrics | same `METRIC_FIELDS` as #95 |
| PnL | **none** — liquidity / health only |
| Start | after P4a screening is accepted as a pipeline check; do not reuse P4a as day 1 of a “7d” unless the board explicitly relabels a continuous capture that actually covers 7 full days |

If the 7d capture is incomplete, missing a name, or missing a channel: **no HFT instrument** (fail closed). Do not pad with P4a hours and call it P4b.

---

## Pre-registered P4b selection rule (NOW, before any P4a reveal)

Same eligibility as [`95`](./95-hft-liquidity-gate-plan.md), **scored on P4b pooled 7d**, plus stability. Registered before P4a numbers are used:

1. Resolve live BTC/ETH/DOGE X-Perp (fail closed if any missing). Do not invent ETH.
2. Capture 7 full calendar days simultaneously on the four channels.
3. **Eligible** (pooled 7d) iff `trades/sec > 0` AND `books5 changes/sec > 0` AND median `book_age_ms ≤ 1000` AND reconnect count is not worse than **2×** the three-name median.
4. Among eligible: highest `books5_changes_per_sec`; tie-break lower median spread bps, then higher median top-5 depth notional.
5. **Stability (P4b only) — winner must not be one spectacular night:**
   - Weekday **and** weekend pooled slices must each be eligible under (3) **and** must pick the same winner as pooled. If either slice is `insufficient_data` or shorter than 2×86400s → fail closed.
   - Session-named UTC blocks (non-overlapping labels, not claimed exchange hours): Asia `[00:00,08:00)`, EU `[08:00,16:00)`, US `[16:00,24:00)` UTC. Winner must rank first on **at least 2 of 3** blocks that can be scored. Fewer than 2 scorable blocks → fail closed.
   - Spectacular-night: drop the single UTC hour with the highest `books5_changes_per_sec` for the pooled winner; re-rank residual hour-sum rates. If the winner is no longer first → reject. Missing `by_utc_hour` rates → fail closed (cannot prove stability).
6. If none eligible or stability fails → **no HFT instrument** (fail closed). Do **not** fall back to the P4a 24h favourite. Do not default to DOGE.

`select_instrument_p4b([])` / missing slices → `insufficient_data`. That is the state of this PR.

Code: `atlas.scalp_hft.liquidity_gate.select_instrument_p4b`.

---

## Report schema (no numbers invented here)

Every P4b name reports **pooled + slices**. Empty template: `empty_p4b_report`.

| Slice | Key | Notes |
|-------|-----|-------|
| Pooled 7d | `pooled` | Eligibility + rank (step 3–4) |
| UTC hour 0–23 | `by_utc_hour` | Spectacular-night test |
| Weekday (Mon–Fri UTC) | `weekday` | Stability |
| Weekend (Sat–Sun UTC) | `weekend` | Stability |
| Asia block | `session_asia` | `[00:00,08:00)` UTC |
| EU block | `session_eu` | `[08:00,16:00)` UTC |
| US block | `session_us` | `[16:00,24:00)` UTC |

Each slice uses the same `METRIC_FIELDS` as #95. Values stay `null` / `insufficient_data: true` until a real 7d capture exists. **This document contains no capture rates.**

---

## Honesty / invalidation

- Soft PASS N/A — this gate is not a strategy score.
- Do not pick the instrument that would have made a paper H1 look green.
- Do not treat P4a screening warnings as a lock.
- H1 ([`96`](./96-hft-h1-ensemble-lock.md)) still waits on **P4b lock** + P1 health + multi-day Layer B. Markout ([`104`](./104-h1-markout-event-time.md)) is after the signal study and before economic PnL.
- `not_a_forecast: true`. `place_orders: false`.
