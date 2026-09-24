# Phase 2 — DOGE-only, Variant A

**As-of:** 2026-09-24. **LIVE HOLD.** `place_orders` stays false. Scalp stays disabled. Leverage stays 2x isolated on DOGE. `config/default.yaml` is untouched.

This is a research design. The numbers below are a deterministic synthetic walk. They are **INSUFFICIENT_EVIDENCE** for a real-market edge. Holdout was computed and is **not** a PASS.

## What ran

- Variant A: one DOGE cycle, scalp cash stays cash, no adds.
- Same exits, same sizing, same costs. The two entry modes are separate runs.
- Primary: first retest after a 15m breakout, then a confirm bar.
- Ablation: direct breakout entry on bar `b`, stop at `min(low of b-2..b) - 0.25 * ATR_b`.
- Costs (labeled assumption): taker 5 bps each side, DOGE slippage 5 bps each side, funding unknown.
- 30s intent TTL is not observable on 15m OHLC. The decision is the close of the signal bar. The fill is that close plus adverse slippage (`ttl_observable: false`). The signal rules were left as specified.
- Paper `min_qty` / `qty_step` are `"1"`. That is a step assumption, not an OKX `minSz`.

## Data provenance

Series: `synthetic_doge_regimes` in `src/atlas/paper/atlas_cycle/synthetic.py`.

- 16,000 closed 15m bars, UTC-aligned, seed path starts at price 100 with drift 0.001 and a 0.40 range.
- Planted episodes every 400 bars from index 4200. Even episodes rally into `max_hold`. Odd episodes gap through the protective stop.
- `fetch_okx_history_candles` exists in the repo and was **not** called. No paid feed. No public-cache download.
- Label: **synthetic exploration**. This is not a 1m market cache and not real-market OOS.

Chronological split by bar index: dev `[0, 8000)`, val `[8000, 12000)`, holdout `[12000, 16000)`. A cycle is tagged by its entry index. Selection may look at dev and val. Phase 2 does not treat holdout as a pass.

Warm-up in the yaml is 250 closed 4H bars, so the dev half is mostly warm-up. Signals start after that warm-up.

## Result

Evidence: **INSUFFICIENT_EVIDENCE**.

- OOS cycles (val + holdout, both modes): **40**, under the 200-cycle floor.
- Bootstrap 95% interval of OOS cycle PnL (1,000 resamples, seed 20260924) crosses 0 for both modes.
- Val preference on this sample: `direct_breakout` (less negative val expectancy).
- `selection_used: false`. The preference was recorded and was not applied.
- Frozen entry stays **`first_retest`** in `config/strategies/atlas_cycle_v1.yaml`.
- `holdout_pass_claimed: false`.

Signals were not loosened to manufacture more trades.

### Primary — `first_retest`

| Slice | Cycles | Expectancy | PF | Win rate | Max DD | Fees |
|-------|--------|------------|----|----------|--------|------|
| dev | 10 | -1.95115015 | 0.47768269 | 0.50000000 | 0.05893922 | 2.97430245 |
| val | 10 | -0.79689688 | 0.45417384 | 0.50000000 | 0.02454994 | 1.37623505 |
| holdout | 10 | -0.84065838 | 0.43270195 | 0.50000000 | 0.02614038 | 1.59504256 |

OOS cycles 20. Bootstrap interval **-1.67194376** to **0.23619264** (crosses 0). Whole-run max DD on unitized trading NAV **0.09970840**. Fees **5.94558006**. Skip reasons: none on this series.

### Ablation — `direct_breakout`

| Slice | Cycles | Expectancy | PF | Win rate | Max DD | Fees |
|-------|--------|------------|----|----------|--------|------|
| dev | 10 | -0.24439294 | 0.92438045 | 0.50000000 | 0.02105163 | 3.46071414 |
| val | 10 | -0.37567744 | 0.88607264 | 0.50000000 | 0.02414233 | 4.11713663 |
| holdout | 10 | -0.40031817 | 0.85106667 | 0.50000000 | 0.02467015 | 3.79259042 |

OOS cycles 20. Bootstrap interval **-2.86873873** to **2.31914182** (crosses 0). Whole-run max DD **0.04033529**. Fees **11.37044119**. Skip reasons: none on this series.

Expectancy is quote PnL per completed cycle on the unitized trading book (deposit A = 1000, T starts at 400). Max DD is the peak-to-trough drop of unit NAV (`T / units`) inside that slice, and the whole-run figure is the peak over the full walk. Fees are taker fees on the fills in that slice. Win rate counts cycles with PnL above 0.

Variant A settlement skimmed BTC-pending from DOGE cash only. Scalp cash stayed at its opening balance on this walk. BTC reserve quantity was unchanged.

## What this does not say

A higher val expectancy on 10 synthetic cycles is not a reason to switch the frozen entry. Real-market OOS remains **INSUFFICIENT_EVIDENCE**. Forward paper remains **PENDING_FORWARD_EVIDENCE**. Nothing here arms live trading.
