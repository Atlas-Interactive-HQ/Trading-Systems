# 62 — rise_panel_v1 Scalp: DOGE **1H BreakoutV1** long/flat (€20)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. Soft PASS ≠ Scalp-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md); Scalp 4H [`57-rise-panel-scalp-improve-4h-ema.md`](./57-rise-panel-scalp-improve-4h-ema.md); Scalp Donchian [`61-rise-panel-scalp-donchian20-10-1h.md`](./61-rise-panel-scalp-donchian20-10-1h.md); Scalp RSI MR [`59-rise-panel-scalp-rsi14-mr-1h.md`](./59-rise-panel-scalp-rsi14-mr-1h.md). **Canonical BreakoutV1** (lookback 16 / ATR quiet) — **no** daily-bull EMA filter. Do not re-run #58/#60.

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

**ONE family only — NOT grinding lookback / ATR / TF / costs. No daily-bull EMA.**

**Family:** `breakout_v1_long_flat_1h`  
**scalp_improve_id:** `rise_panel_v1_scalp_doge_breakoutv1_1h_eur20`  
**compare_to:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`, `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`, `rise_panel_v1_scalp_doge_donchian20_10_1h_eur20`, `rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20`
**Canonical BreakoutV1:** repo `BreakoutV1` / `BreakoutParams` lookback **16**, ATR SMA **14**, min_atr_frac **0.001**, atr_stop_mult **1.5** overlay (yaml untouched). Decision bar **1H**; `oneh_filter=off`. Long/flat channel exit (no Signal ATR-stop in walk_long_flat). **No** daily-bull EMA.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.
- BreakoutV1 Donchian lookback **16** (entry high / exit low same N).
- **Long:** closed-bar close > prior 16-bar high AND ATR(14)/close ≥ 0.001. Long only.
- **Flat/exit:** closed-bar close < prior 16-bar low. Never short.
- **No** daily-bull EMA filter / regime gate (distinct from EMA twins / #46).
- `oneh_filter: off` (decision TF is already 1H).
- Insufficient history → flat. Quiet ATR → no new long.
- Fill: signal close → next open. Size: full Scalp sleeve €20 when long.
- Costs: PaperSettings 5+5 bps.
- **No** RSI / EMA / ATR-mult rescue knobs this trial. **No** lookback / TF / cost grind on FAIL.

### Why this family

Provisional Scalp 1H+daily-bull (#55) soft FAIL (exp>0 4/7; best panel_net≈€44.70). Scalp #57 4H EMA soft PASS; Scalp #61 Donchian 20/10 soft PASS (panel≈€26.62); Scalp #59 RSI MR 1H soft PASS (panel≈€18.24). #58/#60 archived FAIL (do not re-run). This trial ports **canonical BreakoutV1** (lookback 16 + ATR quiet) onto Scalp €20 / locked rise panel / 1H — **without** daily-bull EMA so the family stays distinct from EMA twins.

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_breakout_1h_eval.py`
- Module: `atlas.paper.rise_panel_scalp_breakout_1h_eval`
- Strategy: `atlas.strategy.scalp_doge_breakout_1h` (thin wrapper around canonical `BreakoutV1` channel + ATR quiet)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, cascade compound (#55 rules) on PASS only; patterns from #57/#59/#61
- Unit tests: `tests/unit/test_rise_panel_scalp_breakout_1h.py`

---

## D. Results — Scalp BreakoutV1 1H €20 on same 7

**scalp_improve_id:** `rise_panel_v1_scalp_doge_breakoutv1_1h_eur20`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 23 | 0.5068 | 12.3675 | 4.8929 | 0.5059 | 15.3616 | 10.6267 |
| R2 | 29 | -0.0246 | -0.3668 | 9.1513 | 0.5076 | 9.2713 | 17.5480 |
| R3 | 25 | 0.2698 | 6.7455 | 7.7944 | 0.4981 | 12.1697 | 13.4725 |
| R4 | 30 | -0.0558 | -1.2251 | 3.6744 | 0.5316 | 6.1076 | 4.9136 |
| R5 | 33 | 0.0418 | 1.3782 | 8.7183 | 0.5957 | 8.0627 | 6.9305 |
| R6 | 26 | 0.0652 | 1.6965 | 8.8996 | 0.5385 | 7.0466 | 18.0849 |
| R7 | 26 | 0.1650 | 4.6087 | 5.5773 | 0.5537 | 12.7458 | 7.0240 |

**Panel summary (Scalp BreakoutV1 1H):**
- windows with exp>0: **5**/7 · net>0: **5**/7
- median expectancy €/trade: **0.0652**
- median_trades: **26.0**
- panel net €: **25.2045**
- worst DD €: **9.1513**

### Soft promote (Scalp BreakoutV1): **PASS** (`soft_promote_v1`)

- median_trades=26.0 (ok=True, min>=1)
- exp>0: 5/7 (need ≥5; ok=True)
- panel_net €=25.2045 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs provisional Scalp #55 (Breakout − provisional)

| Metric | Provisional 1H €20 | Scalp BreakoutV1 1H €20 | Δ |
|--------|------------------:|-----------------------:|--:|
| median exp € | 0.2048 | 0.0652 | -0.1396 |
| panel net € | 44.7022 | 25.2045 | -19.4977 |
| median_trades | 18.0 | 26.0 | 8.0 |
| n exp>0 / 7 | 4 | 5 | 1 |
| soft promote | FAIL | **PASS** | — |

### Honesty deltas vs Scalp #57 4H (Breakout − 4H)

| Metric | Scalp 4H €20 (#57) | Scalp BreakoutV1 1H €20 | Δ |
|--------|------------------:|-----------------------:|--:|
| median exp € | 1.0464 | 0.0652 | -0.9812 |
| panel net € | 41.8052 | 25.2045 | -16.6007 |
| median_trades | 7.0 | 26.0 | 19.0 |
| n exp>0 / 7 | 6 | 5 | -1 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs Scalp #61 Donchian (Breakout − Donchian)

| Metric | Scalp Donchian 1H €20 (#61) | Scalp BreakoutV1 1H €20 | Δ |
|--------|---------------------------:|-----------------------:|--:|
| median exp € | 0.0661 | 0.0652 | -0.0008 |
| panel net € | 26.6195 | 25.2045 | -1.4150 |
| median_trades | 29.0 | 26.0 | -3.0 |
| n exp>0 / 7 | 6 | 5 | -1 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs Scalp #59 RSI MR (Breakout − RSI MR)

| Metric | Scalp RSI MR 1H €20 (#59) | Scalp BreakoutV1 1H €20 | Δ |
|--------|-------------------------:|-----------------------:|--:|
| median exp € | 0.5128 | 0.0652 | -0.4476 |
| panel net € | 18.2424 | 25.2045 | 6.9621 |
| median_trades | 7.0 | 26.0 | 19.0 |
| n exp>0 / 7 | 5 | 5 | 0 |
| soft promote | PASS | **PASS** | — |

---

## E. Cascade compound (PASS → substitute Scalp, provisional_scalp=false)

Same cascade rules as phase1/55: window-end surplus-share 7:2:1, one-way Scalp→Mid→Core; PaperSettings 5+5 bps; next-open; place_orders false.

- **compound_id:** `rise_panel_v1_cascade_compound_721_scalp_breakout_1h`
- **provisional_scalp:** `False`
- **Scalp system:** `rise_panel_v1_scalp_doge_breakoutv1_1h_eur20` (1H BreakoutV1)
- combined net pre-cascade: **472.8132** €
- per-sleeve net (panel sum): Core **363.9983** · Mid **83.6104** · Scalp **25.2045** €

### Compare to #55 / #57 / #61 / #59 panel nets

| Sleeve | #55 (provisional) | #57 (4H) | #61 (Donchian) | #59 (RSI MR) | #62 (Breakout) | Δ vs #55 | Δ vs #57 | Δ vs #61 | Δ vs #59 |
|--------|------------------:|---------:|---------------:|-------------:|---------------:|---------:|---------:|---------:|---------:|
| Core | 363.9983 | 363.9983 | 363.9983 | 363.9983 | 363.9983 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Mid | 83.6104 | 83.6104 | 83.6104 | 83.6104 | 83.6104 | -0.0000 | -0.0000 | -0.0000 | -0.0000 |
| Scalp | 44.7022 | 41.8052 | 26.6195 | 18.2424 | 25.2045 | -19.4977 | -16.6007 | -1.4150 | 6.9621 |
| Combined | 492.3109 | 489.4139 | 474.2282 | 465.8511 | 472.8132 | -19.4977 | -16.6007 | -1.4150 | 6.9621 |

Reports: `data/reports/rise_panel_v1_cascade_compound_scalp_breakout_1h.json`

---

## What this is not

- Not a lookback / ATR / TF / cost grind.
- Not a daily-bull EMA filter / EMA-twin family.
- Not a change to R1–R7 window dates.
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Scalp-arming. Soft PASS ≠ Scalp-arm. Live ≤€20.
- Not a claim that past rise windows forecast the next bull.
- Not a re-run of archived #58/#60.
- Not Donchian 20/10 (#61) — BreakoutV1 lookback 16 + ATR quiet.
- Mid 4H stays Mid baseline.

`not_a_forecast: true`. `place_orders: false`.
