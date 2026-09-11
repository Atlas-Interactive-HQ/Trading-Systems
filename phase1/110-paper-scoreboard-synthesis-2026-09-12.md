# 110 — Paper scoreboard synthesis (2026-09-12)

**Stance:** Honesty cite. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. **This note does not arm.**
**Aligns with:** [`108`](./108-dev-board-research-lock.md) DEV board — Mid **#71** primary, Scalp **S1** provisional, Core **CASH**. **Do not contradict that lock.**
**Program:** [`109`](./109-three-month-program-2026-09-12.md) (3-month cadence). Capital HOLD ~€240 ([`107`](./107-eur200-capital-readiness-2026-09-12.md)).
**Accounting:** citations from [`91`](./91-rise-panel-accounting-v2.md) and first-score notes. **No re-run. No invented metrics / PnL.**

---

## How to read

- Every euro figure below is **copied** from an existing phase1 note. This file is **not** a new panel score.
- R1–R7 remain DEV/eliminate-only and **paused** for new family tips ([`106`](./106-research-governance-board.md)).
- Soft PASS / V2 PASS ≠ GREEN CANDIDATE ≠ arm.
- Prefer complete-trade expectancy when a V2 PASS is forced-window-close dominated ([`90`](./90-evaluation-integrity-audit.md), [`91`](./91-rise-panel-accounting-v2.md)).
- Best DEV board to **implement** (paper/system) is [`108`](./108-dev-board-research-lock.md). That is **not** a live-arm.

Scope of **measured** numbers in the tables: the accounting_v2 re-score set + CORE-R1 + SCALP-R2 + H0 health stamp — all already on `main`. Earlier rise_panel rungs (e.g. Mid #65, Scalp #63) stay in their own notes; this synthesis does **not** restate unread euros.

---

## Best DEV board to IMPLEMENT (paper / system — not live-arm)

Locked by [`108`](./108-dev-board-research-lock.md) / `atlas.paper.rise_panel.DEV_BOARD`. Repeated here so a later PR cannot quietly swap the board.

| Sleeve | Role | Id | Paper/system | Live-arm |
|--------|------|----|--------------|----------|
| **Mid** | **primary** | `#71` `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40` | Yes (observer / SHADOW-later) | **No** |
| **Scalp** | **provisional DEV** | **S1** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20` | Yes (margin of safety **small** until stress) | **No** |
| **Core** | **CASH** / no validated edge | allocation `cash` — C0 reference only; CORE-R1 **not promoted**; Donchian **stopped** | Cash book / no Core sleeve fill | **No** |
| **HFT** | **wait P4b** | no instrument | P4a screen only; then P4b 7d + markout ([`100`](./100-p4a-screening-p4b-7d.md), [`104`](./104-h1-markout-event-time.md)) | **No** |

**Not on the board as primary** (same as [`108`](./108-dev-board-research-lock.md)): Mid **M1** (comparator), Scalp **R2** (FAIL), Core **C1/C2** (FAIL / family stopped), **CORE-R1** (V2 PASS DEV-only, `promote=False`).

---

## Mid — #71 vs M1 (worse)

Cite [`72`](./72-mid-long-strengthen.md), [`86`](./86-rise-panel-mid-m1-adx-4h.md), [`91`](./91-rise-panel-accounting-v2.md). Same locked R1–R7. Sleeve Mid **€40**. Bar **4H**.

| Candidate | OLD soft | V2 gate | OLD panel € | V2 term € | OLD exp>0 | Honesty |
|-----------|:--------:|:-------:|------------:|----------:|----------:|---------|
| Mid **#71** BreakoutV1+EMA12/21 | PASS | PASS | 97.2663 | 97.1317 | 5/7 | **DEV primary** ([`108`](./108-dev-board-research-lock.md)) |
| Mid **M1** #71+ADX(14)>20 | PASS | PASS | 74.6942 | 74.6109 | 6/7 | **PASS-but-worse** vs #71 |

Honesty deltas M1 − #71 ([`86`](./86-rise-panel-mid-m1-adx-4h.md)): panel net **−22.5721**; median exp € **2.1531 → 0.9113** (**−1.2418**). M1 has **more** exp>0 windows (6 vs 5) and a **lower** panel — that is **not** a post-hoc swap for #71 ([`93`](./93-frozen-mid-scalp-candidates.md), [`108`](./108-dev-board-research-lock.md)).

#71 OLD soft ([`72`](./72-mid-long-strengthen.md)): median exp € **2.1531** · median trades **7.0** · worst DD € **21.8963**. Forced window closes under v2: **3**/7 ([`91`](./91-rise-panel-accounting-v2.md)). Soft PASS ≠ Mid-arm.

---

## Scalp — #83 → S1 (better small) → R2 FAIL

Cite [`83`](./83-rise-panel-scalp-dual-thrust-1h.md), [`87`](./87-rise-panel-scalp-s1-rvol-1h.md), [`91`](./91-rise-panel-accounting-v2.md), [`99`](./99-rise-panel-scalp-r2-dt-4h-regime-1h.md). Sleeve Scalp **€20**. Decision **1H**.

| Candidate | OLD soft | V2 gate | OLD panel € | V2 term € | Honesty |
|-----------|:--------:|:-------:|------------:|----------:|---------|
| Scalp **S0 / #83** Dual Thrust N20 k=0.5 | PASS | PASS | 31.1763 | 31.0774 | S0 reference |
| Scalp **S1** #83 + RVOL>1 | PASS | PASS | 32.6400 | 32.5631 | **PASS-and-better** vs #83; **provisional DEV** |
| Scalp **R2** S1 + 4H EMA12/21 regime | FAIL | **FAIL** | 12.1679 | 12.0531 | **eliminated**; no RVOL grind |

S1 − #83 ([`87`](./87-rise-panel-scalp-s1-rvol-1h.md)): panel-net Δ **+1.4637**; median exp **unchanged** at **0.2086**. [`103`](./103-edge-vs-luck-stress.md) / [`108`](./108-dev-board-research-lock.md): margin of safety is **small** until SHADOW + stress. Soft PASS ≠ Scalp-arm.

R2 − S1 ([`99`](./99-rise-panel-scalp-r2-dt-4h-regime-1h.md)): V2 terminal panel Δ **−20.5099**; exp_term_adj>0 **4**/7 (need ≥5) → v2 **FAIL**. Walker was `walk_long_short` (long **46** / short **39** entries). Archive. Do **not** grind RVOL 1.25/1.5.

---

## Core — EMA C0 vs C1/C2 FAIL vs CORE-R1 (trail cuts BH, no promote)

Cite [`54`](./54-rise-panel-v1.md), [`88`](./88-rise-panel-core-c1-donchian40-20-1d.md), [`89`](./89-rise-panel-core-c2-donchian40-20-ema50-200-1d.md), [`91`](./91-rise-panel-accounting-v2.md), [`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md). Sleeve Core **€140** is a **research size**, not a mandate to be long. [`108`](./108-dev-board-research-lock.md) board allocation = **CASH**.

| Candidate | OLD soft | V2 gate | OLD panel € | V2 term € | Honesty / role |
|-----------|:--------:|:-------:|------------:|----------:|----------------|
| Core **C0** EMA12/30 1D | FAIL | PASS | 363.9983 | 362.6547 | **baseline reference**; V2 forced closes **7/7** |
| Core **C1** Donchian 40/20 | FAIL | PASS | 208.1348 | 207.2313 | honesty **FAIL** vs C0; eliminated |
| Core **C2** Donchian40/20+EMA50/200 | FAIL | **FAIL** | 74.4898 | 73.9999 | **FAIL**; Donchian family **STOPPED** (no C3/C4) |
| **CORE-R1** EMA12/30 + ATR14×3.0 trail | FAIL | PASS | 223.4550 | 222.5514 | V2 PASS **DEV only**; **promote=False** |

CORE-R1 vs C0 ([`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md)): V2 terminal panel Δ **−140.1033** (trail **cuts BH-like** open holds — expected, not a headline). Median completed exp **−2.9545 → −2.6465** (Δ **+0.3081**, still **negative**). Completed exp>0 still **2**/7. Forced closes **5**/7. Worst DD slightly better (**87.9988 → 84.5976**). Participation not eliminated. **Still not a promote.** Core on the DEV board remains **CASH** ([`105`](./105-portfolio-core-major.md), [`108`](./108-dev-board-research-lock.md)).

C0 OLD soft ([`54`](./54-rise-panel-v1.md)): exp>0 **2**/7 · median exp € **−2.9545** · median trades **1.0** — thin / BH-like. Do not read V2 PASS (forced 7/7) as complete-trade edge ([`91`](./91-rise-panel-accounting-v2.md)).

---

## Integrity — accounting_v2 forced-close honesty

Cite [`90`](./90-evaluation-integrity-audit.md), [`91`](./91-rise-panel-accounting-v2.md). Gate `rise_panel_accounting_v2` was locked **before** the re-score. This audit **does not promote**.

`walk_long_flat` historically mixed:

| Field | What it measured |
|-------|------------------|
| `net_return_eur` | Terminal MTM; open long at window end had **no** synthetic sell fee/slip |
| `n_trades` / expectancy | **Completed** round-trips only (`None` when `n_trades=0`) |

V2 adds terminal liquidation (same sell slip+fee as a normal exit) at last in-window close. Δ net is almost entirely that missing terminal sell (~few cents to ~€0.24). A V2 **PASS** that flips C0 / C1 FAIL→PASS because a forced close turns an open hold into `n_terminal_trips=1` is **one-interval dominated**, not complete-trade proof.

Forced window closes on the v2 re-score ([`91`](./91-rise-panel-accounting-v2.md)): C0 **7**/7 · #71 **3**/7 · M1 **2**/7 · #83 **4**/7 · S1 **3**/7 · C1 **5**/7 · C2 **3**/7. CORE-R1 first score: **5**/7 ([`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md)). SCALP-R2: **5**/7 ([`99`](./99-rise-panel-scalp-r2-dt-4h-regime-1h.md)).

Do **not** rewrite `soft_promote_v1` or historical phase1/54, 72, 83, 86, 87, 88, 89 tables.

---

## H0 — health-stale 39.2% vs carry 57.7%

Cite [`98`](./98-h0-health-stale-2026-09-11.md) (2026-09-11 Layer B corpus; [`92`](./92-hft-staleness-semantics.md) semantics). **No HFT PnL.** Soft PASS **N/A**.

| Metric | Value (measured) |
|--------|-----------------:|
| `n_samples_1s` | **15109** |
| `carried_forward` (old “stale” / feature carry) | **8711** (**57.65%** ≈ **57.7%**) |
| `health_stale` (`book_age_ms > 1000`) | **5926** (**39.22%** ≈ **39.2%**) |
| `n_reconnect` | **2** |
| `book_age_ms` median / p95 | **398** ms / **15498** ms |

[`85`](./85-layer-b-4h-capture-vamp-checkpoint.md) reported **8711 / 15109 ≈ 0.5765** as `n_seconds_stale_carry` — that is **`carried_forward`**, **not** `health_stale`. Do not treat the #85 carry rate as the health-kill fraction. Trading health = `health_stale OR ts_rewind OR reconnect` ([`92`](./92-hft-staleness-semantics.md)).

HFT stays **wait P4b** ([`100`](./100-p4a-screening-p4b-7d.md), [`108`](./108-dev-board-research-lock.md)): no instrument pick, no economic PnL before markout ([`104`](./104-h1-markout-event-time.md)).

---

## Ledger / multiplicity

Starter mainline rows already on `main` ([`102`](./102-trial-ledger.md)): `TL-INT85`, `TL-M1`, `TL-S1`, `TL-C1`, `TL-C2`, `TL-CORE-R1`, `TL-SCALP-R2`, `TL-DEV-BOARD`.

This pack appends citation rows only (no new PnL): `TL-H0` ([`98`](./98-h0-health-stale-2026-09-11.md)), `TL-109` (this program), `TL-110` (this synthesis). Starter N is **not** a complete census of phase1/16–99. Do not invent Deflated Sharpe / PBO.

---

## Honesty / invalidation

- If a later PR swaps M1 onto the board because it had more exp>0 windows, it **contradicts** [`108`](./108-dev-board-research-lock.md).
- If a later PR promotes CORE-R1 from V2 PASS / smaller DD, it **contradicts** [`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md) / [`108`](./108-dev-board-research-lock.md).
- If a later PR arms Mid/Scalp/Core/HFT from Soft PASS or from this scoreboard, it violates [`106`](./106-research-governance-board.md) / [`109`](./109-three-month-program-2026-09-12.md).
- Do not invent SHADOW dates or an HFT instrument here.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.
