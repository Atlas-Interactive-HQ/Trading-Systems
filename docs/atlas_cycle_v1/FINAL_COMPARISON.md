# FINAL_COMPARISON — Atlas Cycle v1 paper package

**As-of:** 2026-09-24. **LIVE HOLD.** Label: **synthetic exploration**. These walks are not real-market OOS. `fetch_okx_history_candles` was not called.

Evidence for an edge: **INSUFFICIENT_EVIDENCE**. Forward paper: **PENDING_FORWARD_EVIDENCE** (0 calendar days elapsed). Live full system: **FAIL** / **INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM**.

`entry_frozen` stays `first_retest`. `scalp.enabled` stays false. `scalp.freeze` stays `SCALP_OFF`. Deposit on the walks is simulated A = 1000. Sensitivity deposits {200, 500, 1000} are labels in yaml, not transfers.

## Recommendation

Ship the **DOGE-only paper candidate skeleton** (Variant A, `first_retest`) as the research path under LIVE HOLD.

The full system stays unshipped: no scalp arm, no profit-funded adds, no pre-reserved adds, no live orders, no BTC auto-buy. Variant A is a skeleton with passing controls and an unproven edge. It is not a live arm and not a holdout pass.

## DOGE entry ablation (Variant A)

Same exits, costs, and synthetic series. Modes are separate runs. Source: `docs/atlas_cycle_v1/PHASE2_DOGE.md`.

Costs, labeled assumption: taker 5 bps each side, DOGE slippage 5 bps each side, funding unknown. Paper quantity step is 1. Skip reasons on this series: none.

| Mode | Slice | Cycles | Expectancy | PF | Win rate | Max DD | Fees |
|------|-------|--------|------------|----|----------|--------|------|
| first_retest | dev | 10 | -1.95115015 | 0.47768269 | 0.50000000 | 0.05893922 | 2.97430245 |
| first_retest | val | 10 | -0.79689688 | 0.45417384 | 0.50000000 | 0.02454994 | 1.37623505 |
| first_retest | holdout | 10 | -0.84065838 | 0.43270195 | 0.50000000 | 0.02614038 | 1.59504256 |
| direct_breakout | dev | 10 | -0.24439294 | 0.92438045 | 0.50000000 | 0.02105163 | 3.46071414 |
| direct_breakout | val | 10 | -0.37567744 | 0.88607264 | 0.50000000 | 0.02414233 | 4.11713663 |
| direct_breakout | holdout | 10 | -0.40031817 | 0.85106667 | 0.50000000 | 0.02467015 | 3.79259042 |

`first_retest` whole-run max DD **0.09970840**, fees **5.94558006**. OOS cycles 20. Bootstrap 95% interval **-1.67194376** to **0.23619264** (crosses 0).

`direct_breakout` whole-run max DD **0.04033529**, fees **11.37044119**. OOS cycles 20. Bootstrap 95% interval **-2.86873873** to **2.31914182** (crosses 0).

Validation was less negative on `direct_breakout`. `selection_used` is false. The frozen entry stays `first_retest` because 20 OOS cycles per mode are under the 200-cycle floor and both intervals cross 0. Holdout was computed and is not a pass.

## Variants A / B / C / D

Same DOGE series, costs, and seed as Phase 2. Scalp bars are aligned synthetic paths. B and C use SOL in memory only. SOL is not frozen. Source: `docs/atlas_cycle_v1/PHASE3_ABCD.md`.

OOS DOGE cycles **20** (floor 100). OOS scalps **0** (floor 300).

| Variant | What it is | DOGE cycles | Scalps dev/val/holdout | Dev DOGE exp | Val DOGE exp | Holdout DOGE exp | Dev scalp net | Adds | Max DD | Fees | Halt at end |
|---------|------------|-------------|------------------------|--------------|--------------|------------------|---------------|------|--------|------|-------------|
| A | DOGE only, scalp cash idle | 30 | 0 / 0 / 0 | -1.95115015 | -0.79689688 | -0.84065838 | 0E-8 | 0 | 0.09970840 | 5.94558006 | latched |
| B | DOGE + SOL scalp, PnL stays cash | 30 | 4 / 0 / 0 | -2.03449454 | -0.79689688 | -0.84065838 | -0.83344392 | 0 | 0.10242976 | 6.09807753 | latched |
| C | B + add from realized scalp cash | 30 | 4 / 0 / 0 | -2.03449454 | -0.79689688 | -0.84065838 | -0.83344392 | 0 | 0.10242976 | 6.09807753 | latched |
| D | DOGE + add from pre-reserved cash, no scalp | 30 | 0 / 0 / 0 | -1.89790447 | -0.79689688 | -0.84065838 | 0E-8 | 3 | 0.09882812 | 6.27935152 | not latched |

Skips:

| Variant | Skips |
|---------|--------|
| A | none |
| B | `reduced` 17 |
| C | `SKIP_MIN_SIZE` 2, `reduced` 17 |
| D | `SKIP_MIN_SIZE` 12 |

`reduced` is a scalp breakout while risk mode was already REDUCED. That is why validation and holdout scalp counts are zero. Variant C never funded an add: realized scalp cash was below one DOGE coin. Variant D filled 3 development adds, then skipped later windows on size. Val and holdout DOGE expectancy match A. That sample does not enable adds.

Scalp candidate nets on the same book (development only; validation net 0): SOL −0.83344392, ETH −0.81182797, PEPE −0.69711500. Detail and the public size table: `docs/atlas_cycle_v1/PHASE3_SCALP.md`.

## Why the full system stays unshipped

- G6 and G7 are **INSUFFICIENT_EVIDENCE**.
- G10 is **FAIL** on live free USDC 0.69.
- G8 stays unverified (`listing_verified=false`).
- G11 has not started.
- B and C made development DOGE expectancy worse and produced no OOS scalps.
- D is a diagnostic, not a configured variant.

The configured yaml remains Variant A, scalp off, LIVE refused.
