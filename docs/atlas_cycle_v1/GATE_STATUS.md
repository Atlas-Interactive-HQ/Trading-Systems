# GATE_STATUS — Atlas Cycle v1

**As-of:** 2026-09-24 · Phase 2 DOGE-only paper. Scalp still disabled.
**LIVE HOLD.** Een PASS hieronder is geen arm. `PAPER_PASS ≠ live-arm`. Soft PASS ≠ arm.

Statuses: `PASS` (control or unit behavior holds), `FAIL` (the check ran and the system is not allowed to proceed), `INSUFFICIENT_EVIDENCE` (not measured), `PENDING_FORWARD_EVIDENCE` (needs a forward paper window that does not exist yet).

| Gate | Status | What it means | Evidence |
|------|--------|---------------|----------|
| G0 LIVE HOLD | PASS | Code refuses `execution_mode: LIVE` before a fill. Smoke exits non-zero. | `tests/unit/test_atlas_cycle_v1_gates.py::test_t30_live_mode_refused_before_fill`, `test_smoke_script_paper_ok_and_live_nonzero` |
| G1 `default.yaml` untouched | PASS | Sha256 of `config/default.yaml` pinned. Cycle loader rejects a file named `default.yaml`. | `test_default_yaml_bytes_unchanged`, `test_cycle_config_loads_paper_and_refuses_default_name` |
| G2 Settlement §18 | PASS | Unit arithmetic for L and B=0.60×W after recovery. Not a venue fill. | `tests/unit/test_atlas_cycle_v1_settlement.py` |
| G3 BTC reserve never sold | PASS | Reserve qty/quote unchanged across losses, skims, and an explicit sell call (the call raises). | `test_t02_btc_reserve_cannot_be_sold_or_pledged`, conservation test, smoke |
| G4 Unitized risk | PASS | Daily 3% halt, 5% REDUCED after UTC roll, 10% latched MANUAL_HALT, soft pass does not widen. | `test_t14_daily_halt_at_three_percent`, `test_t16_reduced_halves_risk_and_soft_pass_does_not_widen`, `test_t17_manual_halt_latches_until_ack_below_ten_percent` |
| G5 Money conservation | PASS | Seeded PnL path: total quote changes only by the applied PnL. Pending is a transfer inside the total. | `test_money_conservation_seeded_pnl_path` |
| G6 Scalp feasibility | INSUFFICIENT_EVIDENCE | SOL/ETH/PEPE listings, minSz, fees, and any edge are unprobed. Scalp stays disabled. | `config/strategies/atlas_cycle_v1.yaml` (`scalp.enabled: false`), `instruments.py` TODOs, `test_t25_scalp_blocked_until_enabled_and_doge_healthy` |
| G7 DOGE trend edge | INSUFFICIENT_EVIDENCE | Variant A synthetic ablation: 40 OOS cycles, bootstrap CI crosses 0. Frozen entry stays `first_retest`. Holdout is not a PASS. Real-market OOS was not scored. | `docs/atlas_cycle_v1/PHASE2_DOGE.md`, `test_variant_a_ablation_is_insufficient_and_documented` |
| G8 Instrument metadata | INSUFFICIENT_EVIDENCE | Every registry row is `listing_verified=false`, minSz empty. Live spec raises. | `test_registry_placeholders_are_not_proven` |
| G9 Fee tier / funding | INSUFFICIENT_EVIDENCE | 5 bps taker, 5/10 bps slip are labeled assumptions. Funding unknown. | `FEASIBILITY.md`, broker assumption string |
| G10 Live capital for the full system | FAIL | Free USDC 0.69 (upload, 2026-09-24) is below T=0.40×A for A in {200, 500, 1000}. Leverage was not raised. | `classify_live_capital` → `INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM` |
| G11 Forward paper | PENDING_FORWARD_EVIDENCE | No forward session, no public-cache walk, no multi-week journal. Smoke is synthetic and same-day. | `scripts/run_atlas_cycle_v1_smoke.py` |
| G12 PEPE protection untouched | PASS | This PR has no path that reads or amends the open PEPE position or its OCO. | No PEPE order client in `atlas_cycle`. Legacy position excluded in `CURRENT_STATE.md`. |
| G13 Soft / paper ≠ arm | PASS | Soft pass cannot widen risk or leverage. Paper config keeps `place_orders: false` and `live_hold: true`. | `test_t16_reduced_halves_risk_and_soft_pass_does_not_widen`, yaml |

## Test id map (brief-style)

These are the behaviors implemented and named in tests. They are not a claim that a longer private test matrix was executed on a venue.

| Id | Behavior |
|----|----------|
| T01 | 60/30/10 on A ∈ {200, 500, 1000}; T = 0.40 A; BTC outside T |
| T02 | Bot cannot sell or pledge BTC; losses do not debit reserve or pending |
| T04 | A loss increases L and creates no BTC pending (example 18.1) |
| T07 | After L is cleared, B = 0.60 × W; a partial recovery leaves B at 0 (18.2–18.4) |
| T14 | Daily realized loss ≥ 3% of day-start T → DAILY_HALT |
| T16 | Unit DD ≥ 5% → REDUCED at half cycle risk, once the daily halt is not binding; soft pass does not widen |
| T17 | Unit DD ≥ 10% → latched MANUAL_HALT; ack does not clear it while DD stays ≥ 10% |
| T25 | Scalp signal only if enabled and the DOGE cycle is healthy; yaml default is disabled |
| T30 | LIVE execution refused before a fill; smoke process exits non-zero |

## Phase 2 test ids

These names match the DOGE brief. They sit beside the Phase 1 ids above; Phase 1 T01 is still the 60/30/10 split, and Phase 1 T04 is still the loss-carryforward example.

| Id | Behavior |
|----|----------|
| P2-T01 | Closed 15m candles only. An unclosed bar does not enter and does not move the indicator cursor. A longer suffix does not change earlier reasons. |
| P2-T03 | Stop active at the bar open is checked before any trail that uses that bar's high. A gap fills at the open; a pierce fills at the stop. |
| P2-T04 | `SKIP_MIN_SIZE` when the floored quantity is below the paper step. Quantity is never rounded up. A stop inside the 20% cost-of-2R cap is `SKIP_COST_2R`. |

## What would move a gate

- G6/G8/G9: a read-only instruments and fee probe, stored as data, with unknowns still labeled. Not a live order.
- G7: a pre-registered walk on public DOGE candles with at least 200 OOS cycles and a bootstrap interval that stays above 0, costs on. The synthetic ablation does not clear this. Do not loosen the signal to get there.
- G10: more free collateral or an explicit decision to run a smaller sleeve. Not a higher leverage.
- G11: a forward paper journal over unseen days. Until then the status stays **PENDING_FORWARD_EVIDENCE**.
