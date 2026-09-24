# MODULE_STATUS — Atlas Cycle v1

**As-of:** 2026-09-24. **LIVE HOLD.** `place_orders: false`.

ON means the paper path runs under BACKTEST or PAPER. OFF means the yaml and the loader keep that path from arming. Code that exists for a counterfactual test is still OFF in the configured system.

| Module | State | Where | What that means |
|--------|-------|-------|-----------------|
| DOGE paper path | ON | `src/atlas/paper/atlas_cycle/doge_trend.py`, coordinator DOGE sleeve | Variant A. `entry_frozen: first_retest`. Warm-up 250 closed 4H bars. Paper and backtest only. Edge gate G7 is **INSUFFICIENT_EVIDENCE**. |
| Capital ledger | ON | `ledger.py`, `money.py` | Decimal quote. T excludes BTC reserve and BTC pending. |
| Settlement | ON | `settlement.py` | After a flat cycle, loss carryforward then B = 0.60×W. Pending is an internal balance. It is not a live order. |
| Portfolio risk | ON | `risk.py` | 1% cycle, 0.5% REDUCED, 3% daily halt, 5% / 10% drawdown. Soft pass does not widen. |
| Simulated broker | ON | `broker.py` | PAPER and BACKTEST fills with labeled fee and slippage. |
| Cycle coordinator | ON | `coordinator.py` | One DOGE cycle. Configured variant A. Scalp slot stays unused while the switch is off. |
| Scalp strategy | OFF | `scalp_momentum.py`, yaml `scalp.enabled: false`, `freeze: SCALP_OFF` | Research code remains for tests and the Phase 3 counterfactual. The configured system does not take scalp entries. |
| Adds funded by scalp profit | OFF | Variant C is in-memory only | Yaml variant is A. Unrealized scalp PnL cannot fund an add. |
| Adds from pre-reserved cash | OFF | Variant D is a diagnostic script path | Not the configured variant. |
| LIVE execution | OFF | `parse_execution_mode`, every runner | The string LIVE raises before a fill. Scripts exit 2. |
| BTC auto-buy, live | OFF | No order client in `atlas_cycle` | Settlement may compute `btc_pending`. Nothing sends a BTC buy. The reserve cannot be sold. |
| Legacy PEPE management | OFF | No PEPE order client | The open live position and its OCO are not read or amended. Paper PEPE is a different simulated instrument and is not armed. |
| News, LLM, ML in the decision | OFF | Not imported by the cycle package | Decisions are closed-bar rules only. |
| Auto coin rotation, shorts, martingale, averaging down | OFF | Loader rejects them | One long DOGE cycle. One scalp slot, and that slot is switched off. |

Configured file: `config/strategies/atlas_cycle_v1.yaml`. `config/default.yaml` is not this module's config and is not edited by this package.
