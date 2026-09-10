# 63 — rise_panel_v1 Scalp: DOGE **1H EMA12/21** long/flat (€20)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. Soft PASS ≠ Scalp-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md); Scalp 4H [`57-rise-panel-scalp-improve-4h-ema.md`](./57-rise-panel-scalp-improve-4h-ema.md); Scalp Donchian [`61-rise-panel-scalp-donchian20-10-1h.md`](./61-rise-panel-scalp-donchian20-10-1h.md); Scalp BreakoutV1 [`62-rise-panel-scalp-breakoutv1-1h.md`](./62-rise-panel-scalp-breakoutv1-1h.md); Scalp RSI MR [`59-rise-panel-scalp-rsi14-mr-1h.md`](./59-rise-panel-scalp-rsi14-mr-1h.md). **Plain EMA12/21** long/flat (NOT 12/30; no RSI; no daily-bull). Do not re-run #58/#60.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

---

## A. LOCKED compare targets

**scalp_provisional_id (#55):** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`  
(soft_promote **FAIL** — provisional stand-in)

- Rule: 1H EMA12/30 long/flat + daily EMA bull entry gate. Never short.
- Bar: DOGE-USDT **1H**. Sleeve: Scalp **€20**.
- #55 snapshot (reported): exp>0 **4**/7 · median_trades=**18** · panel_net≈**€44.70**.

**scalp_4h_id (#57):** `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`  
(soft_promote **PASS** — EMA12/30 long/flat on **4H**)

- #57 snapshot (reported): exp>0 **6**/7 · median_trades=**7** · panel_net≈**€41.81** · median exp≈**€1.05**.

**scalp_donchian_id (#61):** `rise_panel_v1_scalp_doge_donchian20_10_1h_eur20`  
(soft_promote **PASS** — Donchian 20/10 long/flat on **1H**)

- #61 snapshot (reported): exp>0 **6**/7 · median_trades=**29** · panel_net≈**€26.62** · cascade≈**€474.23**.

**scalp_breakout_id (#62):** `rise_panel_v1_scalp_doge_breakoutv1_1h_eur20`  
(soft_promote **PASS** — BreakoutV1 long/flat on **1H**)

- #62 snapshot (reported): exp>0 **5**/7 · median_trades=**26** · panel_net≈**€25.20** · cascade≈**€472.81**.

**scalp_rsi_mr_id (#59):** `rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20`  
(soft_promote **PASS** — RSI(14) MR long/flat on **1H**)

- #59 snapshot (reported): exp>0 **5**/7 · median_trades=**7** · panel_net≈**€18.24** · cascade≈**€465.85**.

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

**ONE family only — NOT grinding EMA periods / TF / costs. No RSI. No daily-bull.**

**Family:** `ema12_21_long_flat_1h`  
**scalp_improve_id:** `rise_panel_v1_scalp_doge_ema12_21_1h_eur20`  
**compare_to:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`, `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`, `rise_panel_v1_scalp_doge_donchian20_10_1h_eur20`, `rise_panel_v1_scalp_doge_breakoutv1_1h_eur20`, `rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20`
**Plain EMA12/21:** Mid/Scalp EMA long/flat family with periods **12/21** (NOT 12/30). Decision bar **1H**. No daily-bull. No RSI.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.
- EMA periods: **fast=12, slow=21** (NOT 12/30).
- **Long/flat:** closed-bar EMA12 > EMA21 → long; else flat. Never short.
- **No** daily-bull EMA filter / regime gate.
- **No** RSI / Donchian / ATR / Breakout knobs this trial.
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Scalp sleeve €20 when long.
- Costs: PaperSettings 5+5 bps.
- **No** EMA period / TF / cost grind on FAIL.

### Why this family

Provisional Scalp 1H+daily-bull (#55) soft FAIL (exp>0 4/7; best panel_net≈€44.70). Scalp #57 4H EMA12/30 soft PASS; #61 Donchian / #62 BreakoutV1 / #59 RSI MR also soft PASS. #58/#60 archived FAIL (do not re-run). This trial ports **plain EMA12/21** (TradingView-style twin, Mid 4H spirit without daily-bull) onto Scalp €20 / locked rise panel / 1H.

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_ema1221_1h_eval.py`
- Module: `atlas.paper.rise_panel_scalp_ema1221_1h_eval`
- Strategy: `atlas.strategy.scalp_doge_ema1221_1h` (thin wrapper around `EmaTrendV1` 12/21)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, cascade compound (#55 rules) on PASS only; patterns from #57/#61/#62
- Unit tests: `tests/unit/test_rise_panel_scalp_ema1221_1h.py`

---

## D. Results — Scalp EMA12/21 1H €20 on same 7

**scalp_improve_id:** `rise_panel_v1_scalp_doge_ema12_21_1h_eur20`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 39 | 0.2823 | 11.5376 | 4.7217 | 0.5394 | 15.3616 | 10.6267 |
| R2 | 50 | 0.0113 | 0.9444 | 10.3170 | 0.5161 | 9.2713 | 17.5480 |
| R3 | 47 | 0.1195 | 5.6142 | 8.4650 | 0.5139 | 12.1697 | 13.4725 |
| R4 | 44 | -0.0358 | -0.7610 | 3.4915 | 0.5298 | 6.1076 | 4.9136 |
| R5 | 41 | -0.0744 | 2.7864 | 7.6119 | 0.4968 | 8.0627 | 6.9305 |
| R6 | 41 | 0.1391 | 5.7012 | 9.7551 | 0.4909 | 7.0466 | 18.0849 |
| R7 | 43 | 0.0620 | 3.5931 | 4.1033 | 0.5769 | 12.7458 | 7.0240 |

**Panel summary (Scalp EMA12/21 1H):**
- windows with exp>0: **5**/7 · net>0: **6**/7
- median expectancy €/trade: **0.0620**
- median_trades: **43.0**
- panel net €: **29.4160**
- worst DD €: **10.3170**

### Soft promote (Scalp EMA12/21): **PASS** (`soft_promote_v1`)

- median_trades=43.0 (ok=True, min>=1)
- exp>0: 5/7 (need ≥5; ok=True)
- panel_net €=29.4160 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs provisional Scalp #55 (EMA12/21 − provisional)

| Metric | Provisional 1H €20 | Scalp EMA12/21 1H €20 | Δ |
|--------|------------------:|---------------------:|--:|
| median exp € | 0.2048 | 0.0620 | -0.1429 |
| panel net € | 44.7022 | 29.4160 | -15.2862 |
| median_trades | 18.0 | 43.0 | 25.0 |
| n exp>0 / 7 | 4 | 5 | 1 |
| soft promote | FAIL | **PASS** | — |

### Honesty deltas vs Scalp #57 4H (EMA12/21 − 4H)

| Metric | Scalp 4H €20 (#57) | Scalp EMA12/21 1H €20 | Δ |
|--------|------------------:|---------------------:|--:|
| median exp € | 1.0464 | 0.0620 | -0.9844 |
| panel net € | 41.8052 | 29.4160 | -12.3892 |
| median_trades | 7.0 | 43.0 | 36.0 |
| n exp>0 / 7 | 6 | 5 | -1 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs Scalp #61 Donchian (EMA12/21 − Donchian)

| Metric | Scalp Donchian 1H €20 (#61) | Scalp EMA12/21 1H €20 | Δ |
|--------|---------------------------:|---------------------:|--:|
| median exp € | 0.0661 | 0.0620 | -0.0041 |
| panel net € | 26.6195 | 29.4160 | 2.7965 |
| median_trades | 29.0 | 43.0 | 14.0 |
| n exp>0 / 7 | 6 | 5 | -1 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs Scalp #62 BreakoutV1 (EMA12/21 − Breakout)

| Metric | Scalp BreakoutV1 1H €20 (#62) | Scalp EMA12/21 1H €20 | Δ |
|--------|-----------------------------:|---------------------:|--:|
| median exp € | 0.0652 | 0.0620 | -0.0033 |
| panel net € | 25.2045 | 29.4160 | 4.2115 |
| median_trades | 26.0 | 43.0 | 17.0 |
| n exp>0 / 7 | 5 | 5 | 0 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs Scalp #59 RSI MR (EMA12/21 − RSI MR)

| Metric | Scalp RSI MR 1H €20 (#59) | Scalp EMA12/21 1H €20 | Δ |
|--------|-------------------------:|---------------------:|--:|
| median exp € | 0.5128 | 0.0620 | -0.4508 |
| panel net € | 18.2424 | 29.4160 | 11.1736 |
| median_trades | 7.0 | 43.0 | 36.0 |
| n exp>0 / 7 | 5 | 5 | 0 |
| soft promote | PASS | **PASS** | — |

---

## E. Cascade compound (PASS → substitute Scalp, provisional_scalp=false)

Same cascade rules as phase1/55: window-end surplus-share 7:2:1, one-way Scalp→Mid→Core; PaperSettings 5+5 bps; next-open; place_orders false.

- **compound_id:** `rise_panel_v1_cascade_compound_721_scalp_ema1221_1h`
- **provisional_scalp:** `False`
- **Scalp system:** `rise_panel_v1_scalp_doge_ema12_21_1h_eur20` (1H EMA12/21)
- combined net pre-cascade: **477.0247** €
- per-sleeve net (panel sum): Core **363.9983** · Mid **83.6104** · Scalp **29.4160** €

### Compare to #55 / #57 / #61 / #62 / #59 panel nets

| Sleeve | #55 (provisional) | #57 (4H) | #61 (Donchian) | #62 (Breakout) | #59 (RSI MR) | #63 (EMA12/21) | Δ vs #55 | Δ vs #57 | Δ vs #61 | Δ vs #62 | Δ vs #59 |
|--------|------------------:|---------:|---------------:|---------------:|-------------:|---------------:|---------:|---------:|---------:|---------:|---------:|
| Core | 363.9983 | 363.9983 | 363.9983 | 363.9983 | 363.9983 | 363.9983 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Mid | 83.6104 | 83.6104 | 83.6104 | 83.6104 | 83.6104 | 83.6104 | -0.0000 | -0.0000 | -0.0000 | -0.0000 | -0.0000 |
| Scalp | 44.7022 | 41.8052 | 26.6195 | 25.2045 | 18.2424 | 29.4160 | -15.2862 | -12.3892 | 2.7965 | 4.2115 | 11.1736 |
| Combined | 492.3109 | 489.4139 | 474.2282 | 472.8132 | 465.8511 | 477.0247 | -15.2862 | -12.3892 | 2.7965 | 4.2115 | 11.1736 |

Reports: `data/reports/rise_panel_v1_cascade_compound_scalp_ema1221_1h.json`

---

## What this is not

- Not an EMA 12/30 period twin grind (periods locked 12/21).
- Not a daily-bull EMA filter / RSI add-on.
- Not a change to R1–R7 window dates.
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Scalp-arming. Soft PASS ≠ Scalp-arm. Live ≤€20.
- Not a claim that past rise windows forecast the next bull.
- Not a re-run of archived #58/#60.
- Mid 4H stays Mid baseline.

`not_a_forecast: true`. `place_orders: false`.
