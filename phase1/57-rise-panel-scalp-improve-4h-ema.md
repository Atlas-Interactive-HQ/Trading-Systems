# 57 — rise_panel_v1 Scalp improvement: DOGE **4H EMA12/30** long/flat (€20)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md)

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

---

## A. LOCKED provisional Scalp (#55) — compare target

**scalp_provisional_id:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`  
(soft_promote **FAIL** on rise_panel_v1 — provisional stand-in)

- Rule: 1H EMA12/30 long/flat + daily EMA bull entry gate. Never short.
- Bar: DOGE-USDT **1H**. Sleeve: Scalp **€20**.
- #55 snapshot (reported): exp>0 **4**/7 · median_trades=**18** · panel_net≈**€44.70**.

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

## B. LOCKED improvement family (BEFORE scoring)

**ONE family only — NOT grinding EMA 12/30 periods.**

**Family:** `ema12_30_long_flat_4h`  
**scalp_improve_id:** `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`  
**compare_to:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`
**Same family as Mid baseline:** `rise_panel_v1_mid_doge_ema12_30_4h_eur40` but Scalp **€20** (not Mid €40).

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- EMA periods: **fast=12, slow=30** (same as Mid baseline — no period grind).
- **Long/flat:** closed-bar EMA12 > EMA30 → long; else flat. Never short.
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Scalp sleeve €20 when long.
- Costs: PaperSettings 5+5 bps.
- **No** Donchian / ATR / RSI rescue knobs this trial. **No** EMA period / TF / cost grind on FAIL.

### Why this family

Provisional Scalp 1H+daily-bull failed soft_promote (exp>0 4/7). Mid baseline plain EMA12/30 **4H** already soft_promote PASS on the same locked rise panel. Porting that Mid family to Scalp €20 tests whether the 4H structure lifts Scalp through ≥5/7 exp>0 without inventing a new rule card.

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_improve_eval.py`
- Module: `atlas.paper.rise_panel_scalp_improve_eval`
- Strategy: `atlas.strategy.scalp_doge_ema_4h` (thin Scalp wrapper around `EmaTrendV1`)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, cascade compound (#55 rules) on PASS
- Unit tests: `tests/unit/test_rise_panel_scalp_improve.py`

---

## D. Results — Scalp improve (4H EMA12/30 €20) on same 7

**scalp_improve_id:** `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 5 | 1.3234 | 7.0835 | 10.6313 | 0.5670 | 15.3616 | 9.8839 |
| R2 | 5 | 1.3295 | 8.6341 | 11.6270 | 0.5412 | 9.2713 | 17.5093 |
| R3 | 15 | 0.4214 | 6.3217 | 10.4448 | 0.4519 | 12.1697 | 9.9090 |
| R4 | 10 | 0.1245 | 2.4023 | 3.2665 | 0.5238 | 6.1076 | 4.5910 |
| R5 | 11 | -0.3490 | 2.0957 | 9.6536 | 0.4890 | 8.0627 | 6.8994 |
| R6 | 7 | 1.1347 | 7.9430 | 14.9438 | 0.5960 | 7.0466 | 18.0849 |
| R7 | 7 | 1.0464 | 7.3248 | 4.7032 | 0.5815 | 12.7458 | 6.2325 |

**Panel summary (Scalp improve):**
- windows with exp>0: **6**/7 · net>0: **7**/7
- median expectancy €/trade: **1.0464**
- median_trades: **7.0**
- panel net €: **41.8052**
- worst DD €: **14.9438**

### Soft promote (Scalp improve): **PASS** (`soft_promote_v1`)

- median_trades=7.0 (ok=True, min>=1)
- exp>0: 6/7 (need ≥5; ok=True)
- panel_net €=41.8052 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Deltas vs provisional Scalp #55 (improve − provisional)

| Metric | Provisional 1H €20 | Scalp 4H €20 | Δ |
|--------|-------------------:|-------------:|--:|
| median exp € | 0.2048 | 1.0464 | 0.8416 |
| panel net € | 44.7022 | 41.8052 | -2.8970 |
| median_trades | 18.0 | 7.0 | -11.0 |
| n exp>0 / 7 | 4 | 6 | 2 |
| soft promote | FAIL | **PASS** | — |

---

## E. Cascade compound (PASS → substitute Scalp, provisional_scalp=false)

Same cascade rules as phase1/55: window-end surplus-share 7:2:1, one-way Scalp→Mid→Core; PaperSettings 5+5 bps; next-open; place_orders false.

- **compound_id:** `rise_panel_v1_cascade_compound_721_scalp4h`
- **provisional_scalp:** `false`
- **Scalp system:** `rise_panel_v1_scalp_doge_ema12_30_4h_eur20` (4H EMA12/30)
- combined net pre-cascade: **489.4139** €
- per-sleeve net (panel sum): Core **363.9983** · Mid **83.6104** · Scalp **41.8052** €

### Compare to #55 panel nets

| Sleeve | #55 (provisional Scalp) | #57 (4H Scalp) | Δ |
|--------|------------------------:|---------------:|--:|
| Core | 363.9983 | 363.9983 | 0.0000 |
| Mid | 83.6104 | 83.6104 | -0.0000 |
| Scalp | 44.7022 | 41.8052 | -2.8970 |
| Combined | 492.3109 | 489.4139 | -2.8970 |

Reports: `data/reports/rise_panel_v1_cascade_compound_scalp4h.json`

---

## What this is not

- Not an EMA 12/30 period grind.
- Not a change to R1–R7 window dates.
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
