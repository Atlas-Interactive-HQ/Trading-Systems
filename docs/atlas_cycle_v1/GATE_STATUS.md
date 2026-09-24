# GATE_STATUS — Atlas Cycle v1

**As-of:** 2026-09-24 · Phase 4 final paper package. Scalp stays `SCALP_OFF`. Entry stays `first_retest`.
**LIVE HOLD.** A PASS below is a control or a unit behavior. It is not an arm. `PAPER_PASS ≠ live-arm`. Soft PASS ≠ arm.

Each gate has exactly one status:

- `PASS` — the control or the unit behavior holds. Not an edge and not a live arm.
- `FAIL` — the check ran, and that path is not allowed to proceed.
- `INSUFFICIENT_EVIDENCE` — measured on synthetic bars, or not measured on a real book. Not a pass.
- `PENDING_FORWARD_EVIDENCE` — needs a forward paper window that has not started.

`scripts/run_atlas_cycle_v1_gate_summary.py` prints this table. It exits 1 if a status is outside the four names, or if G6, G7, G8, G9, G10, G11, or G16 is marked `PASS`.

| Gate | Status | What it means | Evidence |
|------|--------|---------------|----------|
| G0 LIVE HOLD | PASS | Code refuses `execution_mode: LIVE` before a fill. Smoke, DOGE backtest, and Phase 3 exit 2. | `tests/unit/test_atlas_cycle_v1_gates.py`, `docs/atlas_cycle_v1/PAPER_RUNBOOK.md` |
| G1 `default.yaml` untouched | PASS | Sha256 `5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef`. The cycle loader rejects a file named `default.yaml`. | `tests/unit/test_atlas_cycle_v1_gates.py` |
| G2 Settlement §18 | PASS | Unit arithmetic for loss carryforward L and B = 0.60×W after recovery. Not a venue fill. | `tests/unit/test_atlas_cycle_v1_settlement.py`, `docs/atlas_cycle_v1/DESIGN_DECISIONS.md` |
| G3 BTC reserve never sold | PASS | Reserve quantity and quote stay unchanged across losses, skims, and an explicit sell call (the call raises). | `tests/unit/test_atlas_cycle_v1_gates.py`, `tests/unit/test_atlas_cycle_v1_phase3.py` |
| G4 Unitized risk | PASS | Daily 3% halt, 5% REDUCED, 10% latched MANUAL_HALT. Soft pass does not widen risk or leverage. | `tests/unit/test_atlas_cycle_v1_gates.py`, `docs/atlas_cycle_v1/DESIGN_DECISIONS.md` |
| G5 Money conservation | PASS | Seeded PnL path: total quote changes only by the applied PnL. Pending is a transfer inside the total. | `tests/unit/test_atlas_cycle_v1_settlement.py` |
| G6 Scalp edge | INSUFFICIENT_EVIDENCE | Paper min-size can pass under labeled assumptions (skip rate 0/9 at A in {200, 500, 1000}). Val scalp net is 0. OOS scalps 0 and OOS DOGE cycles 20, below 300 and 100. | `docs/atlas_cycle_v1/PHASE3_SCALP.md`, `docs/atlas_cycle_v1/PHASE3_ABCD.md` |
| G7 DOGE trend edge | INSUFFICIENT_EVIDENCE | Synthetic ablation: 20 OOS cycles per entry mode (40 combined), bootstrap intervals cross 0. Holdout is not a pass. Real-market OOS was not scored. | `docs/atlas_cycle_v1/PHASE2_DOGE.md` |
| G8 Instrument metadata | INSUFFICIENT_EVIDENCE | Public SWAP snapshot is stored for the size table. Every registry row is `listing_verified=false` and `min_sz` is empty. Live spec raises. | `src/atlas/paper/atlas_cycle/public_probe.py`, `src/atlas/paper/atlas_cycle/instruments.py` |
| G9 Fee tier / funding | INSUFFICIENT_EVIDENCE | Taker 5 bps and slippage 5/10 bps are labeled assumptions. Funding is unknown. | `docs/atlas_cycle_v1/FEASIBILITY.md` |
| G10 Live capital for the full system | FAIL | Free USDC 0.69 (upload, 2026-09-24) is below T = 0.40×A for A in {200, 500, 1000}. Leverage was not raised. | `docs/atlas_cycle_v1/FEASIBILITY.md`, `docs/atlas_cycle_v1/FINAL_COMPARISON.md` |
| G11 Forward paper | PENDING_FORWARD_EVIDENCE | No forward session and no multi-day journal. Elapsed forward days: 0. Smoke is synthetic and same-day. | `docs/atlas_cycle_v1/OPEN_EVIDENCE.md`, `scripts/run_atlas_cycle_v1_smoke.py` |
| G12 PEPE protection untouched | PASS | No path reads or amends the open legacy PEPE position or its OCO. Paper PEPE is a separate simulated instrument. | `docs/atlas_cycle_v1/CURRENT_STATE.md`, `docs/atlas_cycle_v1/MODULE_STATUS.md` |
| G13 Soft / paper ≠ arm | PASS | Soft pass cannot widen risk or leverage. Yaml keeps `place_orders: false` and `live_hold: true`. | `config/strategies/atlas_cycle_v1.yaml`, `tests/unit/test_atlas_cycle_v1_gates.py` |
| G14 Entry freeze discipline | PASS | Control only. `entry_frozen` is `first_retest`. Synthetic validation preferred `direct_breakout` and that preference was not applied. This PASS is not an edge. | `docs/atlas_cycle_v1/PHASE2_DOGE.md`, `config/strategies/atlas_cycle_v1.yaml` |
| G15 Scalp switch | PASS | Control only. `scalp.enabled` is false and `scalp.freeze` is `SCALP_OFF`. This PASS is not an edge. The evidence gate is G6. | `config/strategies/atlas_cycle_v1.yaml`, `docs/atlas_cycle_v1/PHASE3_SCALP.md` |
| G16 Real-market OHLCV | INSUFFICIENT_EVIDENCE | Scores use generated bars. `fetch_okx_history_candles` was not called. A public ticker snapshot is not a candle history. | `docs/atlas_cycle_v1/PHASE2_DOGE.md`, `docs/atlas_cycle_v1/PHASE3_SCALP.md` |

Upgrade conditions for G6, G7, G8, G9, G10, G11, and G16 are in `docs/atlas_cycle_v1/OPEN_EVIDENCE.md`. Meeting a size check or a unit test does not move those gates.

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

## Phase 3 test ids

Scalp stays off. These checks are the gates around a counterfactual that is not enabled in yaml.

| Id | Behavior |
|----|----------|
| P3-T01 | A scalp breakout is rejected with `doge_not_plus_1r` until DOGE unrealized reaches +1R versus the anchor fill. |
| P3-T02 | An open scalp (unrealized) cannot fund an add. Funding is realized scalp cash only. |
| P3-T03 | An add whose proposed stop is below the current stop is rejected. The stop does not widen. |
| P3-T04 | LIVE is refused before the Phase 3 script writes a report. |
| P3-T05 | BTC reserve quantity is unchanged by a scalp round-trip and by a rejected add. |
| P3-T06 | Two consecutive net-loss scalps reject the next scalp in that cycle. Settlement clears the streak. |
