# DESIGN_DECISIONS — Atlas Cycle v1 Phase 1

Paper/test only. Identifiers in code are English. This note says what was reused and what is new, including the arithmetic choices where the verbatim brief table is not in the git checkout.

## Reused

| Piece | Where | How |
|-------|--------|-----|
| Single-symbol paper engine | `atlas.paper.engine`, `atlas.paper.ledger`, `atlas.paper.risk` | Left in place. Not rewritten. Still the Phase 1.5 float, one-position book. |
| Fill formula | `atlas.paper.fills` | Same buy/sell slippage and taker fee. Reimplemented with `Decimal` in `SimulatedBroker` so cycle cash does not use binary floats. |
| Journals | `atlas.paper.journal.PaperJournal` | Smoke appends fills under the run directory. |
| Bar type | `atlas.paper.types.Bar` | Strategy inputs. Prices convert to `Decimal` at the money boundary. |
| Donchian prior window | `atlas.strategy.breakout.donchian_prior` | 15m breakout level and the scalp momentum level. |
| Causal higher-TF slice | `atlas.paper.md.bars_1h_at_or_before` | Coordinator drops 1H/4H bars that close after the 15m decision. |
| 6:3:1 policy | `atlas.research.kaje_arch`, `phase1/113` | Cited. Not re-locked and not given new leverage ceilings in that module. v1 runtime ceilings are tighter: DOGE isolated **2**, scalp max **3**. |
| Config loader style | PyYAML, same dependency as the repo | New file only: `config/strategies/atlas_cycle_v1.yaml`. |

`config/default.yaml` is not read by the cycle loader. A unit test pins its sha256.

## New package

`src/atlas/paper/atlas_cycle/`

The existing `Ledger` is one position and float cash. Cycle v1 needs three buckets, loss carryforward, BTC pending, and unitized T. A second book avoids changing every current paper test.

| Module | Role |
|--------|------|
| `enums.py` | `CycleState`, `RiskMode`, `ExecutionMode` kept separate. `LIVE` is not a constructable mode. |
| `ledger.py` | `CapitalLedger`. 60/30/10. T excludes BTC reserve and BTC pending. |
| `settlement.py` | Flat-cycle settlement. L, then B = 0.60 × W. |
| `risk.py` | Unit drawdown, daily halt, REDUCED, latched MANUAL_HALT. Soft PASS does not widen. |
| `broker.py` | `SimulatedBroker`. No keys. Refuses LIVE and shorts. |
| `coordinator.py` | One DOGE cycle, one scalp slot, settlement when flat. |
| `doge_trend.py` | 4H veto / 1H filter / 15m breakout + first retest. `direct_breakout` is an ablation flag. |
| `scalp_momentum.py` | SOL/ETH/PEPE selectable. Default off. |
| `instruments.py` | Placeholder metadata. `tradable_live_spec` always fails. |
| `synthetic.py` | Deterministic bars for smoke and tests. |

## Settlement arithmetic (encoded §18)

The brief text in this task says: loss carryforward L, and BTC pending **B = 0.60 × W after recovery**. The verbatim numbered table was not in the repository snapshot, so the examples below are the encoding of that rule. They are the unit tests in `tests/unit/test_atlas_cycle_v1_settlement.py`. If a later copy of the brief defines W differently, treat that as an open correction — do not silently retune leverage or risk.

Definitions:

- A splits into BTC reserve `0.60 A`, DOGE `0.30 A`, scalp `0.10 A`.
- T = DOGE cash + scalp cash. Reserve quote and pending quote are outside T.
- `W_gross` = T at flat close minus T at cycle open (fees included).
- If `W_gross < 0`: L increases by the loss. B = 0. Reserve quantity unchanged.
- If `W_gross > 0`: repay L first. Surplus W = `W_gross − recovered`. If L is still positive, W = 0 and B = 0.
- If L is zero: B = `0.60 × W`, moved from T into `btc_pending_quote`. Not a spot order. Not a sale of BTC.
- Skim is pro-rata on current sleeve cash. No refill of scalp from DOGE and no refill from BTC (no downward cascade, no averaging down).
- Trading units are redeemed at the pre-skim unit NAV so the distribution is not a drawdown. HWM is max unit NAV.

Worked numbers (A = 1000, quote exact):

| Step | Action | L | B added | T | Pending | Total | Reserve qty |
|------|--------|---|---------|---|---------|-------|-------------|
| 18.1 | loss 40 | 40 | 0 | 360 | 0 | 960 | unchanged |
| 18.2 | +25 | 15 | 0 | 385 | 0 | 985 | unchanged |
| 18.3 | +50 | 0 | 21 | 414 | 21 | 1035 | unchanged |
| 18.4 (fresh) | +100, L was 0 | 0 | 60 | 440 | 60 | 1100 | unchanged |

18.4 unit check: pre-skim NAV = 500/400 = 1.25. Redeem 48 units. Post-skim T = 440, units = 352, NAV stays 1.25. DOGE skim 48, scalp skim 12 (weights 400/100 on T=500).

Quote quantum is 1e-8, half-even. These examples do not need a rounded remainder.

A later loss does not claw back pending or reserve. The bot has `reduce_btc_reserve` only as a method that always raises.

BTC quantity at deposit uses placeholder mark 100000 quote per BTC so the quantity is defined. That mark is **not** a market price. Listing is unverified.

## Risk

All of this is on unitized T, not on equity that includes the BTC reserve.

| Gate | Rule |
|------|------|
| Cycle budget | 1% of T when NORMAL |
| REDUCED | unit drawdown ≥ 5% and < 10% → budget 0.5% |
| Daily halt | realized trading losses today ≥ 3% of day-start T. Skims into pending are not daily losses. |
| MANUAL_HALT | unit drawdown ≥ 10%, latched. UTC rollover does not clear it. Acknowledge clears it only when drawdown is back under 10%, and never raises the fraction above 1%. |
| Soft PASS | no-op. Does not clear a halt and does not raise leverage. |

A same-day loss of 5% also exceeds the 3% daily halt, so the daily halt binds first. REDUCED is what remains after the UTC day rolls and the manual latch is not set. That is tested as T14 / T16 / T17.

DOGE leverage is locked at 2 isolated. Scalp max is 3. Config above those ceilings fails closed. Sizing caps notional at `leverage × sleeve cash` and will not increase the multiple if the risk budget wants more.

## Execution and strategy skeleton

- `execution_mode` is only BACKTEST or PAPER. The string LIVE raises `LiveExecutionRefused` before a fill object exists.
- Coordinator fills are paper fills at the decision reference plus labeled slippage. That is simpler than `PaperEngine`'s next-open queue. The Phase 1.5 engine is still the path for the old single-symbol loop. This difference is labeled, not hidden.
- DOGE primary: 4H veto (last close must be above the prior 4H midpoint; missing 4H bars veto), 1H filter (same midpoint rule; missing bars block), 15m Donchian break of the prior 16-bar high, then the **first** retest that tags the level and closes back above it. Direct breakout entry only if `direct_breakout_ablation` is true.
- Long only. A second DOGE add is rejected as averaging down. Short entry is rejected.
- Scalp signals require `scalp.enabled` (yaml forces false) and a healthy DOGE cycle: trend open, unrealized at the mark ≥ 0, risk mode NORMAL. Candidates SOL, ETH, PEPE. Anything else raises. No rotation.
- No ML, no news, no LLM in the decision path.

## Explicitly not done

- No 12-month OOS promotion.
- No private OKX fills.
- No adopt/close of the open PEPE position.
- No edit of live Ops journals.
- No change to `config/default.yaml`.
- No invented minSz, fee tier, or `listing_verified=true`.
