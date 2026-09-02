# 06 — Assumptions That Can Make a Backtest Falsely Profitable

**Purpose:** Exhaustive checklist of ways research can look good while real paper/live expectancy after costs is poor or negative.  
**Atlas rule:** Never claim guaranteed profit; measure expectancy **after costs**. Challenge any backtest that ignores items below.

---

## 1. Look-ahead & information leakage

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 1.1 | Using bar high/low/close before bar is closed | Perfect foresight entries/exits | `closed=true` only; decision at `bar_close_ts` |
| 1.2 | Features built with centered windows / future peeks | Same | Causal windows only; unit tests |
| 1.3 | Funding / mark known before publish time | Avoids funding bleed | Join only info available at decision time |
| 1.4 | Using final revised candles instead of as-of | Cleaner than live | Prefer trade-built bars; freeze as-of snapshots |
| 1.5 | Label leakage (e.g. “next day direction” in train features) | Classic ML leak | Strict time splits; purge gaps |
| 1.6 | Regime label computed with future bars | Trades only easy regimes | Causal regime; delay if needed |
| 1.7 | Stop distance set using future adverse excursion | Unrealistically tight risk | Stops from prior ATR/structure only |

---

## 2. Fill & microstructure fantasy

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 2.1 | Fill at mid or last trade for marketable orders | Free half-spread | Adverse touch + buffer |
| 2.2 | Always fill limit orders at touch without queue | Phantom maker edge | Fill probability model; or assume taker for breakouts |
| 2.3 | Ignore partial fills | Full size at best price | Partial fill + leftover cancel |
| 2.4 | Ignore rejects / disconnects during volatility | Trades through chaos cleanly | Stress: no fill / gap through stop |
| 2.5 | Stop fills at exact stop price in gaps | No slippage on wicks | Gap-through model (esp. alts/memes) |
| 2.6 | Using MBO perfection without latency | Unrealistic queue priority | Non-HFT: don’t claim MBO edge |
| 2.7 | Same-bar entry and favorable exit | Intrabar foresight | Enforce sequencing rules |

---

## 3. Fees, funding, borrow, and other costs

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 3.1 | Zero fees | Instant edge | Venue fee schedule (**UNVERIFIED** until cited); assume taker until proven |
| 3.2 | Maker fees while modeling taker urgency | Fee arbitrage illusion | Match liquidity flag to order type |
| 3.3 | Ignoring funding on perps | Silent drain on holds | Apply funding at timestamps |
| 3.4 | Wrong funding period/sign | Systematic bias | Validate vs raw prints |
| 3.5 | Ignoring settlement / delivery quirks | Rare but real | Status gates |
| 3.6 | Ignoring FX if equity in EUR vs USDT PnL | Translation noise as “alpha” | Explicit ccy model |

---

## 4. Leverage, margin, liquidation

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 4.1 | Unlimited leverage | Oversized winners | Cap ≤2x default, 5x paper hard |
| 4.2 | No liquidation engine | Survives 50% adverse moves | Isolated margin sim; fail if unknown |
| 4.3 | Cross-margin netting fantasy | Hides concentration | One position; isolated preferred |
| 4.4 | Ignoring maintenance margin steps | Late liquidation surprise | Use venue tiers when verified |
| 4.5 | Auto-deleveraging / insurance events ignored | Fat-tail loss missing | Scenario stress |

---

## 5. Position sizing & path dependence

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 5.1 | Fixed notional ignoring stop distance | Fake Sharpe | Risk-budget sizing formula |
| 5.2 | Sizing on future equity peak | Volatility scaling leak | Causal equity |
| 5.3 | Martingale / average-down in backtest | Recovers in-sample | **Forbidden** by L9 |
| 5.4 | Multiple correlated positions | Diversification mirage | One directional position |
| 5.5 | No daily kill | One lucky day hides ruin | 5% daily kill in sim |
| 5.6 | Reinvesting paper fantasy beyond €200 without costs | Scale mirage | Report at €200 scale |

---

## 6. Liquidity, alts, memes, wicks

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 6.1 | Infinite liquidity at BBO | Full fills on thin alts | `liquidity_cap`; ADV/spread gates |
| 6.2 | Backtest on survivor memes only | Selection bias | Pre-commit universe rules; include delisteds if possible |
| 6.3 | Ignoring halt / status | Trades during auction | Status stream required |
| 6.4 | Treating wick as fillable size | Absorbs fake depth | Size vs volume fraction |
| 6.5 | Weekend/news gaps on CEX perps | Stops not filled fairly | Gap stress tests |
| 6.6 | Using illiquid periods for training, liquid for test (or reverse) | Regime cherry-pick | Calendar integrity |

---

## 7. Data quality & stitching

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 7.1 | Silent gap skip (missing crash bars) | Removes losses | Gap ledger; fail on holes |
| 7.2 | Duplicate trades double-counting volume signals | Fake breakouts | Dedupe |
| 7.3 | Timezone mix (UTC vs local) | Shifted signals | UTC only |
| 7.4 | ms vs s timestamp bug | Aligned to wrong bars | CLK tests |
| 7.5 | Mixing venues’ clocks without care | Lead-lag illusion | Per-venue then align carefully |
| 7.6 | Survivorship in instrument list | Only winners remain | Static historical lists |

---

## 8. Research process / statistics

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 8.1 | Endless parameter search without holdout | Curve fit | Locked config_hash; holdout / walk-forward |
| 8.2 | Tiny sample (< hundreds independent trades) | Noise as edge | Minimum trade count; error bars |
| 8.3 | Ignoring multiple testing | “Best of N” bias | Deflated Sharpe / pre-registration |
| 8.4 | Optimizing in-sample kill switches | Avoids real pain | Fixed risk rules L2–L4 |
| 8.5 | Reporting before costs only | Marketing number | Expectancy after costs only |
| 8.6 | Picking lucky start date | Path cherry-pick | Multiple origins; full period |
| 8.7 | Confusing paper latency with backtest zero-latency | Fill timing bias | Add decision-to-send delay |

---

## 9. Execution policy mismatches

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 9.1 | Backtest allows ranging + breakout when prod disables ranging | Extra trades | Mirror L5 flags in research |
| 9.2 | Hedging / flip without fees | Free reversals | Model close+open costs |
| 9.3 | Assuming shorting always allowed | Venue/account limits | Status + account flags |
| 9.4 | Ignoring one-position constraint | Overlapping winners | Enforce in replay risk engine |

---

## 10. Psychological / ops (still “false profitability”)

| # | Assumption / bug | Why it inflates PnL | Mitigation |
|---|------------------|---------------------|------------|
| 10.1 | Ignoring downtime (bot off during crash) | Missed compulsory exit | Force flat on halt/stale |
| 10.2 | Discretionary override by assistant/human mid-test | Unreproducible alpha | Assistants ≠ traders; log only |
| 10.3 | Live keys before reconciliation | One bug wipes “edge” | Paper→live gate |

---

## 11. Atlas mandatory cost stack for any reported expectancy

A result may be discussed only if the run includes, at minimum:

1. Fees (taker-conservative default)  
2. Funding  
3. Adverse spread / slippage model  
4. Risk sizing + daily kill + leverage caps  
5. One-position constraint  
6. Causal bars + no lookahead joins  
7. Gap / untradeable handling  

Otherwise label result **INVALID FOR DECISION**.

---

## 12. Reminder

False profitability is the default outcome of crypto perp research until proven otherwise under this checklist. Goal remains **measured expectancy after costs**, never guaranteed profit.
