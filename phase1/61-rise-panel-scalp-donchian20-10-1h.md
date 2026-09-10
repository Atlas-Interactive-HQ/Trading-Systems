# 61 — rise_panel_v1 Scalp: DOGE **1H Donchian 20/10** long/flat (€20)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. Soft PASS ≠ Scalp-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md); Scalp 4H [`57-rise-panel-scalp-improve-4h-ema.md`](./57-rise-panel-scalp-improve-4h-ema.md); Scalp RSI MR [`59-rise-panel-scalp-rsi14-mr-1h.md`](./59-rise-panel-scalp-rsi14-mr-1h.md). **Canonical Donchian** (Mid #44 / `DonchianLongFlatV1`) — no EMA filter. Do not re-run #58/#60.

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

**ONE family only — NOT grinding Donchian N / TF / costs. No EMA filter.**

**Family:** `donchian20_10_long_flat_1h`  
**scalp_improve_id:** `rise_panel_v1_scalp_doge_donchian20_10_1h_eur20`  
**compare_to:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`, `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`, `rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20`
**Canonical Donchian:** Mid #44 / `DonchianLongFlatV1` paper rule on **1H** (entry break above 20-high; exit break below 10-low / flat). No EMA.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.
- Donchian: entry lookback **20**, exit lookback **10**.
- **Long:** closed-bar close > prior 20-bar high (exclusive lookback). Long only.
- **Flat/exit:** closed-bar close < prior 10-bar low. Never short.
- **No** EMA filter / regime gate. **No** ATR / time-stop knobs this trial.
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Scalp sleeve €20 when long.
- Costs: PaperSettings 5+5 bps.
- **No** RSI / EMA / ATR rescue knobs this trial. **No** Donchian-N / TF / cost grind on FAIL.

### Why this family

Provisional Scalp 1H+daily-bull (#55) soft FAIL (exp>0 4/7; best panel_net≈€44.70). Scalp #57 4H EMA soft PASS; Scalp #59 RSI MR 1H soft PASS (panel≈€18.24). #58/#60 archived FAIL (do not re-run). This trial ports the **canonical Donchian 20/10** paper rule (Mid #44 spirit, no EMA) onto Scalp €20 / locked rise panel / 1H.

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_donchian_1h_eval.py`
- Module: `atlas.paper.rise_panel_scalp_donchian_1h_eval`
- Strategy: `atlas.strategy.scalp_doge_donchian_1h` (thin wrapper around `DonchianLongFlatV1`)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, cascade compound (#55 rules) on PASS only; patterns from #57/#59
- Unit tests: `tests/unit/test_rise_panel_scalp_donchian_1h.py`

---

## D. Results — Scalp Donchian 20/10 1H €20 on same 7

**scalp_improve_id:** `rise_panel_v1_scalp_doge_donchian20_10_1h_eur20`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 25 | 0.4073 | 10.8605 | 5.6335 | 0.4013 | 15.3616 | 10.6267 |
| R2 | 28 | 0.0107 | 0.6759 | 6.7773 | 0.3777 | 9.2713 | 17.5480 |
| R3 | 30 | 0.1569 | 4.7083 | 7.4383 | 0.3940 | 12.1697 | 13.4725 |
| R4 | 33 | -0.0507 | -1.2246 | 3.3641 | 0.4093 | 6.1076 | 4.9136 |
| R5 | 36 | 0.0661 | 2.3782 | 5.4147 | 0.4071 | 8.0627 | 6.9305 |
| R6 | 28 | 0.0512 | 1.4347 | 9.5457 | 0.3569 | 7.0466 | 18.0849 |
| R7 | 29 | 0.2685 | 7.7865 | 2.4316 | 0.4176 | 12.7458 | 7.0240 |

**Panel summary (Scalp Donchian 20/10 1H):**
- windows with exp>0: **6**/7 · net>0: **6**/7
- median expectancy €/trade: **0.0661**
- median_trades: **29.0**
- panel net €: **26.6195**
- worst DD €: **9.5457**

### Soft promote (Scalp Donchian): **PASS** (`soft_promote_v1`)

- median_trades=29.0 (ok=True, min>=1)
- exp>0: 6/7 (need ≥5; ok=True)
- panel_net €=26.6195 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs provisional Scalp #55 (Donchian − provisional)

| Metric | Provisional 1H €20 | Scalp Donchian 1H €20 | Δ |
|--------|-------------------:|----------------------:|--:|
| median exp € | 0.2048 | 0.0661 | -0.1388 |
| panel net € | 44.7022 | 26.6195 | -18.0827 |
| median_trades | 18.0 | 29.0 | 11.0 |
| n exp>0 / 7 | 4 | 6 | 2 |
| soft promote | FAIL | **PASS** | — |

### Honesty deltas vs Scalp #57 4H (Donchian − 4H)

| Metric | Scalp 4H €20 (#57) | Scalp Donchian 1H €20 | Δ |
|--------|-------------------:|----------------------:|--:|
| median exp € | 1.0464 | 0.0661 | -0.9803 |
| panel net € | 41.8052 | 26.6195 | -15.1857 |
| median_trades | 7.0 | 29.0 | 22.0 |
| n exp>0 / 7 | 6 | 6 | 0 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs Scalp #59 RSI MR (Donchian − RSI MR)

| Metric | Scalp RSI MR 1H €20 (#59) | Scalp Donchian 1H €20 | Δ |
|--------|--------------------------:|----------------------:|--:|
| median exp € | 0.5128 | 0.0661 | -0.4468 |
| panel net € | 18.2424 | 26.6195 | 8.3771 |
| median_trades | 7.0 | 29.0 | 22.0 |
| n exp>0 / 7 | 5 | 6 | 1 |
| soft promote | PASS | **PASS** | — |

---

## E. Cascade compound (PASS → substitute Scalp, provisional_scalp=false)

Same cascade rules as phase1/55: window-end surplus-share 7:2:1, one-way Scalp→Mid→Core; PaperSettings 5+5 bps; next-open; place_orders false.

- **compound_id:** `rise_panel_v1_cascade_compound_721_scalp_donchian_1h`
- **provisional_scalp:** `False`
- **Scalp system:** `rise_panel_v1_scalp_doge_donchian20_10_1h_eur20` (1H Donchian 20/10)
- combined net pre-cascade: **474.2282** €
- per-sleeve net (panel sum): Core **363.9983** · Mid **83.6104** · Scalp **26.6195** €

### Compare to #55 / #57 / #59 panel nets

| Sleeve | #55 (provisional Scalp) | #57 (4H Scalp) | #59 (RSI MR) | #61 (Donchian) | Δ vs #55 | Δ vs #57 | Δ vs #59 |
|--------|------------------------:|---------------:|-------------:|---------------:|---------:|---------:|---------:|
| Core | 363.9983 | 363.9983 | 363.9983 | 363.9983 | 0.0000 | 0.0000 | 0.0000 |
| Mid | 83.6104 | 83.6104 | 83.6104 | 83.6104 | -0.0000 | -0.0000 | -0.0000 |
| Scalp | 44.7022 | 41.8052 | 18.2424 | 26.6195 | -18.0827 | -15.1857 | 8.3771 |
| Combined | 492.3109 | 489.4139 | 465.8511 | 474.2282 | -18.0827 | -15.1857 | 8.3771 |

Reports: `data/reports/rise_panel_v1_cascade_compound_scalp_donchian_1h.json`

---

## What this is not

- Not a Donchian-N / TF / cost grind.
- Not an EMA filter / regime add-on.
- Not a change to R1–R7 window dates.
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Scalp-arming. Soft PASS ≠ Scalp-arm. Live ≤€20.
- Not a claim that past rise windows forecast the next bull.
- Not a re-run of archived #58/#60.
- Mid 4H stays Mid baseline.

`not_a_forecast: true`. `place_orders: false`.
