# 83 — rise_panel_v1 Scalp: DOGE **1H Dual Thrust N=20 k1=k2=0.5** long/flat (€20)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. **Soft PASS ≠ Scalp-arm** (coordinator noon gate).
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare (EMA strongest refs):** Scalp 4H EMA [`57`](./57-rise-panel-scalp-improve-4h-ema.md); Scalp 1H EMA12/21 [`63`](./63-rise-panel-scalp-ema12-21-1h.md); provisional [`55`](./55-rise-panel-cascade-compound.md). Scout shortlist: [`82`](./82-scalp-hf-gh-scout-rise-panel.md) Dual Thrust card. **No** grind on FAIL. Branch: `research/rise-panel-scalp-dual-thrust-83`.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

---

## A. LOCKED compare targets (EMA 1H/4H honesty)

**scalp_provisional_id (#55):** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`  
(soft_promote **FAIL** — provisional stand-in)

- #55 snapshot (reported): exp>0 **4**/7 · median_trades=**18** · panel_net≈**€44.70**.

**scalp_4h_id (#57):** `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`  
(soft_promote **PASS** — EMA12/30 long/flat on **4H** — historically strongest Scalp EMA panel_net)

- #57 snapshot (reported): exp>0 **6**/7 · median_trades=**7** · panel_net≈**€41.81** · median exp≈**€1.05**.

**scalp_ema1221_1h_id (#63):** `rise_panel_v1_scalp_doge_ema12_21_1h_eur20`  
(soft_promote **PASS** — EMA12/21 long/flat on **1H** — strongest 1H EMA Scalp ref)

- #63 snapshot (reported): exp>0 **5**/7 · median_trades=**43** · panel_net≈**€29.42** · median exp≈**€0.06**.

### Provisional Scalp per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 18 | 0.6561 | 13.0156 | 5.0107 | 0.3528 | 15.3616 | 10.6267 |
| R2 | 12 | -0.0154 | 0.1815 | 3.2508 | 0.2074 | 9.2713 | 17.5480 |
| R3 | 10 | 1.7603 | 17.6026 | 7.8428 | 0.1806 | 12.1697 | 13.4725 |
| R4 | 16 | -0.0063 | 0.7810 | 3.1150 | 0.2527 | 6.1076 | 4.9136 |
| R5 | 21 | -0.1132 | 3.6889 | 7.0512 | 0.2976 | 8.0627 | 6.9305 |
| R6 | 22 | 0.2048 | 4.5066 | 10.2683 | 0.3284 | 7.0466 | 18.0849 |
| R7 | 18 | 0.2558 | 4.9258 | 3.2967 | 0.2977 | 12.7458 | 7.0240 |

**Panel summary (provisional Scalp re-score):**
- windows with exp>0: **4**/7 · net>0: **7**/7
- median expectancy €/trade: **0.2048**
- median_trades: **18.0**
- panel net €: **44.7022**
- worst DD €: **10.2683**
- soft_promote: **FAIL** (`soft_promote_v1`)

---

## B. LOCKED Scalp family (BEFORE scoring)

**ONE family only — NOT grinding N / k1 / k2 / TF / costs. Params locked once.**

**Family:** `dual_thrust_n20_k0505_long_flat_1h`  
**scalp_improve_id:** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20`  
**compare_to:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`, `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`, `rise_panel_v1_scalp_doge_ema12_21_1h_eur20`
**Formula lock:** Buy = open + k1×(HH−LL); Sell = open − k2×(HH−LL) over prior N (exclusive). Seed N=20 k1=k2=0.5 once.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.
- Dual Thrust: lookback **N=20**, **k1=0.5**, **k2=0.5** (classic seed).
- Range over prior N bars (exclusive): **HH−LL** (LOCKED).
- **Long:** closed-bar close > open + k1×Range. Long only.
- **Flat/exit:** closed-bar close < open − k2×Range. Never short.
- Insufficient history → flat. No EMA / RSI / ATR rescue.
- Fill: signal close → next open. Size: full Scalp sleeve €20 when long.
- Costs: PaperSettings 5+5 bps.
- **No** post-FAIL k/N/TF/cost grind.

### Why this family

Scout #82 ranked Dual Thrust as a distinct candle family vs Donchian #61 / BreakoutV1 #62. Classic seed N=20 k1=k2=0.5 locked once before scoring.

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_dual_thrust_1h_eval.py`
- Module: `atlas.paper.rise_panel_scalp_dual_thrust_1h_eval`
- Strategy: `atlas.strategy.scalp_doge_dual_thrust_1h` → `DualThrustLongFlatV1`
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1`; patterns from #61/#62
- Unit tests: `tests/unit/test_rise_panel_scalp_dual_thrust_1h.py`
- Branch: `research/rise-panel-scalp-dual-thrust-83`
- SHA: `e25fa5cf912bc64cdfc1da8b2d23ab1e8c66d996`

---

## D. Results — Scalp Dual Thrust 1H €20 on same 7

**scalp_improve_id:** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 16 | 0.0278 | 0.4451 | 6.4872 | 0.6205 | 15.3616 | 10.6267 |
| R2 | 7 | 1.0729 | 6.5725 | 7.2502 | 0.5650 | 9.2713 | 17.5480 |
| R3 | 12 | 0.8463 | 10.1558 | 13.8215 | 0.4366 | 12.1697 | 13.4725 |
| R4 | 5 | -0.2980 | -0.6700 | 4.0964 | 0.1896 | 6.1076 | 4.9136 |
| R5 | 7 | 0.4974 | 11.0009 | 4.6419 | 0.4954 | 8.0627 | 6.9305 |
| R6 | 8 | 0.2086 | 1.6690 | 10.9765 | 0.5924 | 7.0466 | 18.0849 |
| R7 | 10 | 0.1958 | 2.0031 | 4.8612 | 0.2898 | 12.7458 | 7.0240 |

**Panel summary (Scalp Dual Thrust 1H):**
- windows with exp>0: **6**/7 · net>0: **6**/7
- median expectancy €/trade: **0.2086**
- median_trades: **8.0**
- panel net €: **31.1763**
- worst DD €: **13.8215**

### Soft promote (Scalp Dual Thrust): **PASS** (`soft_promote_v1`)

- median_trades=8.0 (ok=True, min>=1)
- exp>0: 6/7 (need ≥5; ok=True)
- panel_net €=31.1763 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs provisional Scalp #55 (Dual Thrust − provisional)

| Metric | Provisional 1H €20 | Scalp Dual Thrust 1H €20 | Δ |
|--------|-------------------:|-------------------------:|--:|
| median exp € | 0.2048 | 0.2086 | 0.0038 |
| panel net € | 44.7022 | 31.1763 | -13.5259 |
| median_trades | 18.0000 | 8.0000 | -10.0000 |
| n exp>0 / 7 | 4 | 6 | 2 |
| soft promote | FAIL | **PASS** | — |

### Honesty deltas vs Scalp #57 4H EMA (Dual Thrust − 4H)

| Metric | Scalp 4H EMA €20 (#57) | Scalp Dual Thrust 1H €20 | Δ |
|--------|-----------------------:|-------------------------:|--:|
| median exp € | 1.0464 | 0.2086 | -0.8378 |
| panel net € | 41.8052 | 31.1763 | -10.6289 |
| median_trades | 7.0000 | 8.0000 | 1.0000 |
| n exp>0 / 7 | 6 | 6 | 0 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs Scalp #63 EMA12/21 1H (Dual Thrust − EMA 1H)

| Metric | Scalp EMA12/21 1H €20 (#63) | Scalp Dual Thrust 1H €20 | Δ |
|--------|----------------------------:|-------------------------:|--:|
| median exp € | 0.0620 | 0.2086 | 0.1466 |
| panel net € | 29.4160 | 31.1763 | 1.7603 |
| median_trades | 43.0000 | 8.0000 | -35.0000 |
| n exp>0 / 7 | 5 | 6 | 1 |
| soft promote | PASS | **PASS** | — |

---

## E. On PASS — still Soft PASS ≠ arm

soft_promote **PASS**. Paper only. **Soft PASS ≠ auto-arm** until coordinator noon gate. Mid #71 untouched. Live assume ≤€20. No Scalp live entries from this note.

---

## F. Mid #71 / Core readiness (honesty notes — measured only)

### Mid #71

- Research can verify from repo: Mid formal baseline = BreakoutV1+EMA12/21 4H €40 (`MID_BASELINE_ID` in `atlas.paper.rise_panel`; promote pointer [`72b-mid-breakout-ema1221-promote.md`](./72b-mid-breakout-ema1221-promote.md); source [`72-mid-long-strengthen.md`](./72-mid-long-strengthen.md)).
- soft_promote **PASS** already recorded — **Soft PASS ≠ Mid-arm**. Mid untouched this trial.

### Core

- Core EMA €140 remains Core baseline ([`54`](./54-rise-panel-v1.md); panel_net≈€363.9983, thin n).
- #69 Breakout / #70 Donchian / #73 Breakout+EMA1221 (doc [`80`](./80-rise-panel-core-breakout-ema1221-1d.md)) are soft **FAIL** / not better on panel_net — **do not invent soft PASS**. Noon Core-green for Research = **ops-ready narrative only**.

---


---

## E. Cascade compound (PASS → substitute Scalp, provisional_scalp=false)

Same cascade rules as phase1/55: window-end surplus-share 7:2:1, one-way Scalp→Mid→Core; PaperSettings 5+5 bps; next-open; place_orders false. Core / Mid walks unchanged on this harness path.

- **compound_id:** `rise_panel_v1_cascade_compound_721_scalp_dual_thrust_1h`
- **provisional_scalp:** `False`
- **Scalp system:** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20` (1H Dual Thrust N=20 k1=k2=0.5)
- combined net pre-cascade: **478.7850** €
- per-sleeve net (panel sum): Core **363.9983** · Mid **83.6104** · Scalp **31.1763** €

### Compare to EMA-board panel nets (#55 / #57 / #63)

| Sleeve | #55 (provisional) | #57 (4H) | #63 (EMA12/21) | #83 (Dual Thrust) | Δ vs #55 | Δ vs #57 | Δ vs #63 |
|--------|------------------:|---------:|---------------:|------------------:|---------:|---------:|---------:|
| Core | 363.9983 | 363.9983 | 363.9983 | 363.9983 | 0.0000 | 0.0000 | 0.0000 |
| Mid | 83.6104 | 83.6104 | 83.6104 | 83.6104 | 0.0000 | 0.0000 | 0.0000 |
| Scalp | 44.7022 | 41.8052 | 29.4160 | 31.1763 | -13.5259 | -10.6289 | 1.7603 |
| Combined | 492.3109 | 489.4139 | 477.0247 | 478.7850 | -13.5259 | -10.6289 | 1.7603 |

Reports: `data/reports/rise_panel_v1_cascade_compound_scalp_dual_thrust_1h.json`

## G. What this is not

- Not Scalp-arming / Mid-arming / Core rewrite. **Soft PASS ≠ arm.**
- Not live-raise / `ga live €200`. Live assume **≤€20**.
- Not a rewrite of R1–R7 or `soft_promote_v1`.
- Not a post-FAIL k search / Donchian twin grind.
- Not a forecast (`not_a_forecast: true`). `place_orders: false`.

