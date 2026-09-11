# 108 — Best DEV board research lock (synthesize R1–R7 + integrity)

**Stance:** Research lock. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ arm. **This PR does not arm.**
**Capital:** Kaje **HOLD** from live (~€240 parked) — capital prep only; not sleeve arm ([`107`](./107-eur200-capital-readiness-2026-09-12.md) governs readiness).
**Panel:** [`54`](./54-rise-panel-v1.md) R1–R7 = DEV/eliminate-only (paused for new family tips per [`106`](./106-research-governance-board.md)).
**SHADOW:** Do **not** invent SHADOW dates ([`101`](./101-shadow-contiguous-methodology.md)). Contiguous unseen lock is still pending.
**P4a:** **screening only** ([`100`](./100-p4a-screening-p4b-7d.md)). Do **not** start P4a metrics until 24h capture ends. Do **not** pick an HFT instrument.
**Accounting:** citations from [`91`](./91-rise-panel-accounting-v2.md) / first-score notes — **no re-run**, no invented metrics.

Code: `atlas.paper.rise_panel.DEV_BOARD` / `dev_board_card()`.

---

## Why this lock

Integrity sprint ([`90`](./90-evaluation-integrity-audit.md)–[`94`](./94-core-r1-lock.md)) + accounting_v2 ([`91`](./91-rise-panel-accounting-v2.md)) + first scores CORE-R1 ([`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md)) and SCALP-R2 ([`99`](./99-rise-panel-scalp-r2-dt-4h-regime-1h.md)) leave a clear **research** board. This note freezes that board so later work cannot quietly swap M1 for #71, promote CORE-R1 from a rise-biased V2 PASS, or treat Soft PASS as arm.

**Soft PASS ≠ arm. HALTED. not_a_forecast.**

---

## Best DEV board (LOCKED — not live)

| Sleeve | Role on board | Candidate id | Research sleeve € | Citation |
|--------|---------------|--------------|------------------:|----------|
| **Mid** | **primary** | `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40` (**#71** BreakoutV1+EMA12/21 **4H**) | 40 | [`72`](./72-mid-long-strengthen.md) / [`72b`](./72b-mid-breakout-ema1221-promote.md) / [`93`](./93-frozen-mid-scalp-candidates.md) |
| **Scalp** | **provisional DEV** | `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20` (**S1** Dual Thrust + RVOL>1 **1H**) | 20 | [`87`](./87-rise-panel-scalp-s1-rvol-1h.md) / [`93`](./93-frozen-mid-scalp-candidates.md) |
| **Core** | **CASH** | allocation `cash` — C0 EMA baseline is **reference only**; CORE-R1 **not promoted**; Donchian family **stopped** | 0 (CASH valid) | [`105`](./105-portfolio-core-major.md) / [`94`](./94-core-r1-lock.md) / [`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md) |

Constants: `DEV_BOARD`, `MID_PRIMARY_CANDIDATE_ID`, `SCALP_PROVISIONAL_DEV_ID`, `CORE_DEV_ALLOCATION="cash"`, `CORE_R1_PROMOTED=False`, `CORE_DONCHIAN_FAMILY_STOPPED=True`.

**Not on the board as primary:** Mid M1 (robustness comparator only), Scalp R2 (FAIL/eliminated), Core C1/C2 Donchian (FAIL / family stopped), CORE-R1 (V2 PASS DEV-only — **no promote**).

---

## Measured synthesis (cite only — do not re-score)

Numbers below are **copied from existing phase1 notes**. Do not treat this table as a new panel run.

### Mid / Scalp (board + comparators)

| Candidate | OLD soft | V2 gate | OLD panel € | V2 term € | Honesty / role | Source |
|-----------|:--------:|:-------:|------------:|----------:|----------------|--------|
| Mid **#71** Breakout+EMA1221 4H €40 | PASS | PASS | 97.2663 | 97.1317 | **DEV primary** | [`91`](./91-rise-panel-accounting-v2.md), [`72`](./72-mid-long-strengthen.md) |
| Mid **M1** #71+ADX>20 4H €40 | PASS | PASS | 74.6942 | 74.6109 | **PASS-but-worse** vs #71; comparator only | [`86`](./86-rise-panel-mid-m1-adx-4h.md), [`91`](./91-rise-panel-accounting-v2.md) |
| Scalp **S1** DT+RVOL>1 1H €20 | PASS | PASS | 32.6400 | 32.5631 | **PASS-and-better** vs #83 (Δ panel net **+1.4637**); provisional DEV | [`87`](./87-rise-panel-scalp-s1-rvol-1h.md), [`91`](./91-rise-panel-accounting-v2.md) |
| Scalp **S0** #83 Dual Thrust 1H €20 | PASS | PASS | 31.1763 | 31.0774 | S0 reference | [`91`](./91-rise-panel-accounting-v2.md) |
| Scalp **R2** DT+RVOL+4H EMA regime | FAIL | **FAIL** | 12.1679 | 12.0531 | **eliminated**; no RVOL grind | [`99`](./99-rise-panel-scalp-r2-dt-4h-regime-1h.md) |

Mid #71 OLD soft: exp>0 **5**/7 · median exp € **2.1531** · median trades **7.0** ([`72`](./72-mid-long-strengthen.md) / [`91`](./91-rise-panel-accounting-v2.md)).  
M1: exp>0 **6**/7 but panel net **−22.5721** vs #71 — more positive-exp windows is **not** a post-hoc swap ([`86`](./86-rise-panel-mid-m1-adx-4h.md), [`93`](./93-frozen-mid-scalp-candidates.md)).

### Core (cash on board)

| Candidate | OLD soft | V2 gate | OLD panel € | V2 term € | Honesty / role | Source |
|-----------|:--------:|:-------:|------------:|----------:|----------------|--------|
| Core **C0** EMA12/30 1D €140 | FAIL | PASS | 363.9983 | 362.6547 | **baseline reference**; V2 often forced-close dominated (7/7) | [`91`](./91-rise-panel-accounting-v2.md), [`54`](./54-rise-panel-v1.md) |
| **CORE-R1** EMA+ATR14×3 trail 1D €140 | FAIL | PASS | 223.4550 | 222.5514 | V2 PASS **DEV only**; **promote=False**; completed median exp still negative | [`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md) |
| Core **C1** Donchian 40/20 1D €140 | FAIL | PASS | 208.1348 | 207.2313 | honesty **FAIL** vs C0; audit/reference | [`88`](./88-rise-panel-core-c1-donchian40-20-1d.md), [`91`](./91-rise-panel-accounting-v2.md) |
| Core **C2** Donchian40/20+EMA50/200 | FAIL | **FAIL** | 74.4898 | 73.9999 | **FAIL**; Donchian family **STOPPED** (no C3/C4) | [`89`](./89-rise-panel-core-c2-donchian40-20-ema50-200-1d.md), [`94`](./94-core-r1-lock.md) |

CORE-R1 vs C0 (cite [`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md)): V2 terminal panel Δ **−140.1033**; median completed exp Δ **+0.3081** (still negative absolute); worst DD slightly better; participation not eliminated. **Still not a promote.** Core sleeve on this board remains **CASH** ([`105`](./105-portfolio-core-major.md): unvalidated → 0 / CASH is valid).

### Integrity / governance pointers (P0–P5 / #90–#97 + board)

| Doc | Lock |
|-----|------|
| [`90`](./90-evaluation-integrity-audit.md) | P0 audit — does not promote |
| [`91`](./91-rise-panel-accounting-v2.md) | accounting_v2 OLD vs V2 re-score (gate locked before score) |
| [`92`](./92-hft-staleness-semantics.md) | HFT health / stale split |
| [`93`](./93-frozen-mid-scalp-candidates.md) | Mid #71 primary + Scalp S1 provisional; SCALP-R2 registered |
| [`94`](./94-core-r1-lock.md) | CORE-R1 lock; Donchian stopped |
| [`95`](./95-hft-liquidity-gate-plan.md) / [`100`](./100-p4a-screening-p4b-7d.md) | P4a = **screening**; 24h ≠ instrument lock |
| [`96`](./96-hft-h1-ensemble-lock.md) | H1 ensemble lock (later economic PnL) |
| [`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md) | CORE-R1 first score — no promote |
| [`102`](./102-trial-ledger.md) | Trial ledger / multiplicity |
| [`106`](./106-research-governance-board.md) | A→F order; Soft PASS ≠ arm |

Starter ledger rows (citations only): `TL-INT85`, `TL-M1`, `TL-S1`, `TL-C1`, `TL-C2`, `TL-CORE-R1`, `TL-SCALP-R2` — plus this lock as `TL-DEV-BOARD` (not a new strategy score).

---

## What this PR does / does not

**Does**

- Freeze `DEV_BOARD` in `atlas.paper.rise_panel`.
- Document synthesis in this note (**#108**; **#107** remains €200 capital readiness).
- Append a ledger lock row that **cites** prior scores (no new PnL).

**Does not**

- Change `config/default.yaml`.
- Place orders / arm live / invent SHADOW dates.
- Re-run R1–R7 panels or invent metrics.
- Start P4a metrics or pick an HFT instrument.
- Promote CORE-R1, swap M1 for #71, or grind S2/S3 RVOL / C3 Donchian.
- Score Mid #71 / S1 on contiguous SHADOW (still pending step C/D).

---

## Honesty / invalidation

- Soft PASS / V2 PASS on rise windows ≠ GREEN CANDIDATE ≠ arm.
- Core CASH is intentional until SHADOW + portfolio green — not “Core lonely → fill €140”.
- If a later PR arms from this board without contiguous SHADOW + edge-vs-luck ([`103`](./103-edge-vs-luck-stress.md)), it violates [`106`](./106-research-governance-board.md).

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.
