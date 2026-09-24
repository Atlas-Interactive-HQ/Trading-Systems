# Phase 3 — Scalp candidates

**As-of:** 2026-09-24. **LIVE HOLD.** `place_orders` stays false. `scalp.enabled` stays false. `entry_frozen` stays `first_retest`. DOGE leverage stays 2x isolated. Scalp leverage ceiling stays 3x. `config/default.yaml` is untouched.

This is a research design. The walk below is deterministic and synthetic. It is **INSUFFICIENT_EVIDENCE**. Holdout was computed and is **not** a pass. No coin is frozen.

## Freeze

**SCALP_OFF.**

`selection_used: false`. `holdout_pass_claimed: false`.

DOGE-only (Variant A) remains a valid system outcome. SOL is the in-memory counterfactual for variants B and C. It is not a proven listing and it is not the yaml freeze.

Phase 2 left `entry_frozen` on `first_retest` after validation preferred `direct_breakout` on a thin sample. This phase does not flip that freeze.

## Why the scalp stays off

Floors from the brief: 300 OOS scalps and 100 OOS DOGE cycles. This walk has **0** OOS scalps and **20** OOS DOGE cycles.

Each candidate's validation scalp net is **0** (no validation fills). Development scalp net is negative for SOL, ETH, and PEPE. A non-positive validation net does not clear the selection rule, even before the count floors.

Tie-break (lowest median round-trip cost as a fraction of a gross 1.5R target, then p95, then SOL → ETH → PEPE) was not applied. There was no eligible coin.

Paper min-size can pass and still leave the scalp off. A size pass is not an edge.

## Candidates

Same rules for SOL, ETH, and PEPE. No other coin was tried. Long only. One scalp slot. At most 5 scalps per DOGE cycle. Two consecutive net-loss scalps stop further scalps in that cycle. The coordinator allows a scalp only when variant is B or C, the DOGE cycle is open, the stop has not been widened below the initial stop, risk mode is NORMAL, and DOGE unrealized is at least +1R versus the anchor fill.

The legacy live PEPE position is not read, adopted, or closed. Paper PEPE is the simulated `PEPE-USDT-SWAP` path only.

| Coin | Dev / val / holdout scalps | OOS scalps | Dev scalp net | Val scalp net | Median cost / 1.5R | p95 cost / 1.5R | Val DOGE expectancy |
|------|----------------------------|------------|---------------|---------------|--------------------|-----------------|---------------------|
| SOL | 4 / 0 / 0 | 0 | -0.83344392 | 0E-8 | 0.33366667 | 0.33366667 | -0.79689688 |
| ETH | 4 / 0 / 0 | 0 | -0.81182797 | 0E-8 | 0.33366667 | 0.33366667 | -0.79689688 |
| PEPE | 4 / 0 / 0 | 0 | -0.69711500 | 0E-8 | 0.34366667 | 0.42333333 | -0.79689688 |

Skip reason on every coin: `reduced` × 17. Those are breakouts that fired after unit drawdown had already put the book in REDUCED. Scalp entries require NORMAL, so validation and holdout recorded no fills. The signal was not loosened to manufacture the 300-scalp floor.

Development planted two winning scalps and two losing scalps inside DOGE cycles that were already past +1R. The net of those four is negative on every coin. PEPE's p95 cost is higher because the 1e-8 quote quantum is large next to the PEPE stop.

## Feasibility (paper size)

Public metadata, captured without API keys on 2026-09-24 from `https://eea.okx.com`:

- `GET /api/v5/public/instruments?instType=SWAP`
- `GET /api/v5/market/ticker`

Stored in `src/atlas/paper/atlas_cycle/public_probe.py` so this table does not need a network. `listing_verified` stays **false**. Registry `min_sz` stays empty. `tradable_live_spec` still raises. A public `state=live` is not an account permission and not a fee tier. Exchange max leverage on the payload (50 or 100) is not our ceiling.

| Coin | instId | minSz | ctVal | min coin | last | ticker ts |
|------|--------|-------|-------|----------|------|-----------|
| SOL | SOL-USDT-SWAP | 0.01 | 1 SOL | 0.01 | 115.5 | 1790236947268 |
| ETH | ETH-USDT-SWAP | 0.01 | 0.1 ETH | 0.001 | 2692.17 | 1790236947166 |
| PEPE | PEPE-USDT-SWAP | 0.1 | 10000000 PEPE | 1000000 | 0.000004409 | 1790236948370 |

**ASSUMPTION** (not a measured account tier): taker fee 5 bps each side, scalp slippage 10 bps each side, funding unknown and not credited. Stop distance in this table is **0.50% of the probed last**. Round-trip cost is `2 * 0.0005 + 2 * 0.001 = 0.003`, which is **0.40000000** of a gross 1.5R target at that stop. Scalp risk is 0.05% of cycle-open T. T = 0.40 × A. Scalp cash is 0.10 × A. Margin plus round-trip reserves must fit in 80% of scalp cash at 3x. Quantity is floored to the public lot and is never rounded up.

| Coin | A | Risk budget | Min risk at 0.50% stop | Can place | Skip |
|------|---|-------------|------------------------|-----------|------|
| SOL | 200 | 0.04000000 | 0.00577500 | yes | |
| SOL | 500 | 0.10000000 | 0.00577500 | yes | |
| SOL | 1000 | 0.20000000 | 0.00577500 | yes | |
| ETH | 200 | 0.04000000 | 0.01346085 | yes | |
| ETH | 500 | 0.10000000 | 0.01346085 | yes | |
| ETH | 1000 | 0.20000000 | 0.01346085 | yes | |
| PEPE | 200 | 0.04000000 | 0.02204500 | yes | |
| PEPE | 500 | 0.10000000 | 0.02204500 | yes | |
| PEPE | 1000 | 0.20000000 | 0.02204500 | yes | |

Paper skip rate on this table: **0 / 9**. That is a size check under the assumptions above. It is not a fill on a venue.

Live free USDC from the 2026-09-24 upload is 0.69, which is below T = 0.40 × A for every A in {200, 500, 1000}. Label: **INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM**. Leverage was not raised. DOGE-only remains the separate candidate when the full system cannot be funded.

The synthetic fills use the planted stop (about 0.6% after the 10 bps entry slip), so their measured cost / 1.5R is the median in the candidate table, not the 0.40 assumption.

## Data provenance

- DOGE path: `synthetic_doge_regimes`, 16,000 closed 15m bars. Same series as Phase 2.
- Scalp path: `synthetic_scalp_aligned`, same timestamps, price level taken from the public last above. Winner DOGE episodes plant one breakout at offset 28 (after +1R, before the DOGE max-hold exit) and either a 1.5R print or a gap through the stop. Loser DOGE episodes are a grind.
- `fetch_okx_history_candles` was **not** called. This is **synthetic exploration**. It is not real-market OOS.
- Split by entry index: dev `[0, 8000)`, val `[8000, 12000)`, holdout `[12000, 16000)`.
- Seed 20260924. Deposit A = 1000 for the walk. Costs from the yaml.

## What this does not say

A paper size pass is not a freeze. A negative development scalp net on four trades is not a proof that the rule loses on a market. Real-market OOS remains **INSUFFICIENT_EVIDENCE**. Forward paper remains **PENDING_FORWARD_EVIDENCE**. Nothing here arms live trading or touches the legacy PEPE position.
