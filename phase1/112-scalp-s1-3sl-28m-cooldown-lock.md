# 112 — Scalp S1: 3× consecutive SL → 28m delayed market entry (paper-first lock)

**Stance:** Research / ops lock only. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ arm. **This PR does not arm.**
**Base candidate (unchanged):** Scalp **S1** provisional DEV  
`rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20`  
([`87`](./87-rise-panel-scalp-s1-rvol-1h.md), [`93`](./93-frozen-mid-scalp-candidates.md), [`108`](./108-dev-board-research-lock.md)).
**Panel:** Do **not** score on R1–R7 in this PR. No invented PnL / panel numbers.

Code constants: `atlas.paper.rise_panel` — `SCALP_S1_3SL_28M_COOLDOWN` / id `scalp_s1_3sl_28m_cooldown`.

---

## Why this lock

Kaje paper-first rule for Scalp (system path, not discretionary martingale):

> After **3 consecutive Scalp stop-loss fills**, if the **same system signal** fires again → enforce a **28-minute timer**, then **market entry** with that delay.

This is a **re-entry delay** after a streak of SL exits — **not** averaging down, **not** size-up, **not** martingale. Position size stays the Scalp sleeve (€20 research / paper). Signal identity and S1 rule card stay frozen ([`87`](./87-rise-panel-scalp-s1-rvol-1h.md)).

**Soft PASS ≠ arm. HALTED. not_a_forecast.**

---

## Rule card (LOCKED — paper first)

| Field | Lock |
|-------|------|
| **lock_id** | `scalp_s1_3sl_28m_cooldown` |
| **Applies to** | Scalp sleeve, base candidate **S1** only (same system signal family as S1) |
| **Trigger** | **3 consecutive** Scalp **stop-loss fills** (completed exits tagged SL; wins / non-SL exits reset the consecutive counter) |
| **On next same system signal** | Start **28-minute** timer (venue/market clock); **do not** enter immediately |
| **After timer elapses** | **Market entry** allowed for that deferred same-signal intent (paper path first) |
| **Size** | Unchanged Scalp sleeve — **no** size-up / pyramid / average-down / martingale |
| **Not this lock** | Mid / Core sleeves; HFT lane; live-arm; R1–R7 re-score |

### Explicit non-goals

- Not a 28m **hard freeze** that cancels the signal forever — the locked behavior is **delay then market entry** for the same system signal.
- Not a second position while flat-from-SL is incomplete; max one Scalp position remains.
- Not a param grind (N/k/RVOL/TF unchanged from S1).
- Not live; paper-first only until a later explicit arm path under [`106`](./106-research-governance-board.md) / [`108`](./108-dev-board-research-lock.md).

---

## Relation to board

| Item | Status under this lock |
|------|-------------------------|
| Scalp **S1** provisional DEV | **Still** the board Scalp candidate ([`108`](./108-dev-board-research-lock.md)) |
| Mid **#71** primary | Untouched |
| Core **CASH** | Untouched |
| Soft PASS on S1 ([`87`](./87-rise-panel-scalp-s1-rvol-1h.md)) | Still **≠ arm** |

---

## What this PR does / does not

**Does**

- Pre-register the Kaje 3×SL → 28m delayed market-entry lock for Scalp S1 (paper-first).
- Freeze constants in `atlas.paper.rise_panel` (`scalp_s1_3sl_28m_cooldown`).
- Cite S1 / [`87`](./87-rise-panel-scalp-s1-rvol-1h.md) / [`108`](./108-dev-board-research-lock.md).

**Does not**

- Change `config/default.yaml`.
- Place orders / arm live / invent SHADOW dates.
- Score or re-score R1–R7; invent PnL or panel numbers.
- Average down, martingale, or change S1 Dual Thrust / RVOL gates.
- Promote Soft PASS to arm.

---

## Honesty / invalidation

- Lock-only ≠ implemented live router ≠ GREEN CANDIDATE.
- Soft PASS ≠ arm. HALTED.
- If a later PR implements this delay path, it must keep size flat (no martingale) and remain paper until governance arm criteria pass.
- Do not attach R1–R7 metrics to this note.

### Architecture overlay ([`113`](./113-kaje-architecture-2026-09-12.md))

This **3× consecutive SL → 28m delayed market entry** rule still applies to the **Scalp** sleeve **once a PEPE system exists**. S1 DOGE remains the research candidate until that system is locked. Do **not** invent PEPE params, `instId`, or expectancy here. Not martingale. Soft PASS ≠ arm.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED. lock-only.
