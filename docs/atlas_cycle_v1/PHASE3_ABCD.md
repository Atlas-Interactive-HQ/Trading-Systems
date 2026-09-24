# Phase 3 — Variants A / B / C / D

**As-of:** 2026-09-24. **LIVE HOLD.** Same capital path, costs, and seed as the scalp note. `scalp.enabled` stays false in yaml. The B and C rows are in-memory counterfactuals on SOL. SOL is not frozen.

Evidence: **INSUFFICIENT_EVIDENCE**. Scalp freeze: **SCALP_OFF**. `selection_used: false`. `holdout_pass_claimed: false`. `entry_frozen` stays `first_retest`.

OOS DOGE cycles: **20** (floor 100). OOS scalps on the best coin: **0** (floor 300). Real-market OOS was not scored.

## What each variant is

- **A** — DOGE only. Scalp cash stays idle. No adds. This is the yaml variant.
- **B** — DOGE plus a SOL scalp. Scalp PnL stays in the scalp sleeve. No adds. Settlement still skims DOGE only.
- **C** — DOGE plus a SOL scalp, and one add funded only by realized scalp cash since the cycle opened. Unrealized scalp PnL is not funding. The runner waits for that cash and does not spend the one add on an earlier `add_unfunded` reject.
- **D** — Diagnostic. No scalp. One add funded from cash reserved at 20% of DOGE cash before the initial entry is sized. The reserve is not a transfer out of the scalp sleeve.

Adds use the current stop. A proposed stop below the current stop is rejected before the funding check. The stop only ratchets up. Permission to add does not move scalp cash into the DOGE sleeve.

## Paired results

Same 16,000-bar synthetic DOGE series as Phase 2. Scalp bars are aligned to those timestamps. Deposit A = 1000. Label: **synthetic exploration**.

| Variant | DOGE cycles | Scalps dev/val/holdout | Dev DOGE exp | Val DOGE exp | Holdout DOGE exp | Dev scalp net | Adds | Max DD | Fees | Halt latched at end |
|---------|-------------|------------------------|--------------|--------------|------------------|---------------|------|--------|------|---------------------|
| A | 30 | 0 / 0 / 0 | -1.95115015 | -0.79689688 | -0.84065838 | 0E-8 | 0 | 0.09970840 | 5.94558006 | yes |
| B | 30 | 4 / 0 / 0 | -2.03449454 | -0.79689688 | -0.84065838 | -0.83344392 | 0 | 0.10242976 | 6.09807753 | yes |
| C | 30 | 4 / 0 / 0 | -2.03449454 | -0.79689688 | -0.84065838 | -0.83344392 | 0 | 0.10242976 | 6.09807753 | yes |
| D | 30 | 0 / 0 / 0 | -1.89790447 | -0.79689688 | -0.84065838 | 0E-8 | 3 | 0.09882812 | 6.27935152 | no |

Variant A val expectancy **-0.79689688**, whole-run max DD **0.09970840**, and fees **5.94558006** match the Phase 2 primary row. The paired book did not rewrite that DOGE path.

Skip counts:

| Variant | Skips |
|---------|--------|
| A | none |
| B | `reduced` 17 |
| C | `SKIP_MIN_SIZE` 2, `reduced` 17 |
| D | `SKIP_MIN_SIZE` 12 |

`reduced` means a scalp breakout arrived while risk mode was already REDUCED (unit drawdown at least 5%). Those breaks are concentrated after development, which is why validation and holdout scalp counts are zero.

Variant C's two `SKIP_MIN_SIZE` rejects are the two development scalps that closed green. Realized scalp cash was still below one DOGE coin of stop distance, and quantity is never rounded up. The losing scalps left no funding, so they did not attempt an add.

Variant D filled 3 adds while the 20% reserve could still buy one DOGE coin, then skipped 12 later +1R windows on size. Dev DOGE expectancy is less negative than A on this sample. Val and holdout match A, because those adds were inside development. That is not a reason to enable adds.

## Drawdown and the halt

Max DD is the runner's peak-to-trough of unit NAV (`T / units`) over the whole walk, then quantized to 8 dp. A's figure is the Phase 2 number.

`manual_halt_latched` is PortfolioRisk's flag: unit drawdown versus the realized high-water mark at or above 10%. A, B, and C end latched. The trip on A is late in the series (after the entries that make up the 30 cycles), where the high-water mark sits a fraction above the runner's sampled peak, so the latch can fire while the printed max DD is still 0.09970840. D stays unlatched. No halt was acknowledged and none was cleared in order to keep trading.

B and C also cross a printed 10% runner drawdown. Their development DOGE expectancy is worse than A because scalp losses reduce T. Validation DOGE expectancy is unchanged on this sample.

## What this does not say

Twenty OOS DOGE cycles and zero OOS scalps are below the brief's floors. The table is a paired synthetic comparison, not a market ranking. **SCALP_OFF** stays the freeze. Variant A remains the configured path. Forward paper remains **PENDING_FORWARD_EVIDENCE**. Live capital for the full system remains **INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM**. Nothing here arms live trading.
