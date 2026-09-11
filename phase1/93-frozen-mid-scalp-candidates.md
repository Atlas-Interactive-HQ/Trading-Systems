# 93 — Frozen Mid / Scalp candidates (P2)

**Stance:** Research. `not_a_forecast: true`. Never places orders.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ arm.
**Panel:** R1–R7 remain DEV/eliminate-only.

---

## Mid — freeze

| Role | Id | Note |
|------|----|------|
| **Primary (frozen)** | `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40` | Mid **#71** BreakoutV1 + EMA12/21 4H €40 |
| Robustness comparator only | `rise_panel_v1_mid_doge_breakoutv1_ema1221_adx14_gt20_4h_eur40` | Mid **M1** ADX(14)>20 — more positive-exp windows but lower med exp / panel (see [`86`](./86-rise-panel-mid-m1-adx-4h.md)) |

**Next Mid score = unseen SHADOW only.** Do **not** run M2 / M3 / M4 on R1–R7.

Constants: `MID_PRIMARY_CANDIDATE_ID`, `MID_M1_ROLE = robustness_comparator_only`, `MID_NEXT_SCORE = unseen_SHADOW_only` in `atlas.paper.rise_panel`.

---

## Scalp — freeze

| Role | Id | Note |
|------|----|------|
| Provisional DEV | `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20` | **S1** Dual Thrust + RVOL>1 ([`87`](./87-rise-panel-scalp-s1-rvol-1h.md)) |
| S0 reference | `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20` | #83 |

Do **not** grind RVOL 1.25 / 1.5 on R1–R7 (that would be S2/S3 rescue).

---

## SCALP-R2 — registered before any score

**Hypothesis id:** `rise_panel_v1_scalp_r2_dual_thrust_4h_ema1221_regime`  
**Code:** `atlas.strategy.scalp_doge_dual_thrust_rvol_4h_regime_1h` (lock only).  
**This is a new regime hypothesis, not a threshold rescue.**

Rule card (LOCKED):

- 1H Dual Thrust N=20, k1=k2=0.5 + RVOL20>1 — **unchanged** from S1.
- Regime = **4H EMA12/21**.
- LONG only when EMA12>EMA21 **and** upper DT break **and** RVOL>1.
- SHORT only when EMA12<EMA21 **and** lower DT break **and** RVOL>1.
- Exit: opposite DT boundary **or** higher-TF regime reversal.
- Max one position. No pyramid / average-down / martingale.
- Signal close → next open. Sleeve Scalp €20. Costs 5+5 bps.

**Do not score on R1–R7 in this PR.** `walk_long_flat` cannot score this family (long **and** short; `desired_state` raises). A long/short walker must exist before any panel number is attached.

---

## Honesty / invalidation

- Freezing a candidate is not a GREEN CANDIDATE declaration.
- M1 is **not** promoted over #71 because it had more exp>0 windows — that would be post-hoc winner selection.
- SCALP-R2 must not be scored with the long-only walker (would silently drop shorts).
- Next evidence for Mid: contiguous unseen SHADOW, locked **before** scoring, then walk-forward, then forward paper.

`not_a_forecast: true`. `place_orders: false`.
