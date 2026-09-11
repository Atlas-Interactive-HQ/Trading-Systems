# 86 — rise_panel_v1 Mid **M1**: #71 + **ADX(14)>20** 4H €40

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**; Mid/Scalp **HALTED**; Soft PASS ≠ Mid-arm. Plan: [`84-atlas-trading-vnext.md`](./84-atlas-trading-vnext.md).
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change).
**Compare:** Mid M0=#71 [`72-mid-long-strengthen.md`](./72-mid-long-strengthen.md). **No** ADX/EMA/lookback grind. Branch: `research/atlas-trading-vnext-84`.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1`: median_trades≥1 AND ≥5/7 exp>0 AND panel_net>0.
Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

---

## A. LOCKED Mid M0 baseline (#71)

**mid_m0_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40`

### M0 per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 4 | 5.9898 | 23.9590 | 15.7249 | 0.4583 | 30.7232 | 19.7678 |
| R2 | 7 | 0.9778 | 6.0916 | 18.3218 | 0.4659 | 18.5427 | 35.0187 |
| R3 | 6 | 4.5693 | 27.4157 | 14.7537 | 0.2944 | 24.3395 | 19.8179 |
| R4 | 8 | -0.0323 | 1.9067 | 7.9935 | 0.4304 | 12.2152 | 9.1820 |
| R5 | 7 | -0.8389 | 6.6592 | 16.5075 | 0.3919 | 16.1254 | 13.7988 |
| R6 | 7 | 2.3090 | 16.1628 | 21.8963 | 0.4710 | 14.0932 | 36.1697 |
| R7 | 7 | 2.1531 | 15.0714 | 7.1590 | 0.4556 | 25.4916 | 12.4650 |

**Panel summary (Mid M0 #71 re-score):**
- windows with exp>0: **5**/7 · net>0: **7**/7
- median expectancy €/trade: **2.1531**
- median_trades: **7.0**
- panel net €: **97.2663**
- worst DD €: **21.8963**
- soft_promote: **PASS** (`soft_promote_v1`)

---

## B. LOCKED Mid M1 family (BEFORE scoring)

**Family:** `breakout_v1_ema1221_adx14_gt20_long_regime_4h`  
**mid_m1_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_adx14_gt20_4h_eur40`  
**compare_to:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40`

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- BreakoutV1 lookback **16** + ATR quiet + EMA**12**/**21** (same as #71).
- **ADX gate (locked once):** Wilder **ADX(14) > 20**.
- **Long entry:** BreakoutV1 break-up + ATR quiet **AND** EMA12>EMA21 **AND** ADX>20.
- **Flat/exit:** channel exit **OR** EMA12≤EMA21 **OR** ADX≤20. Never short.
- Fill: next-open. Size: Mid €40. Costs: 5+5 bps.
- **No** ADX threshold / period / EMA / lookback / TF grind on FAIL.

---

## C. Harness

- Script: `scripts/run_rise_panel_mid_m1_adx_4h_eval.py`
- Module: `atlas.paper.rise_panel_mid_m1_adx_4h_eval`
- Strategy: `atlas.strategy.mid_doge_breakout_ema1221_adx_4h`
- Unit tests: `tests/unit/test_rise_panel_mid_m1_adx_4h.py`

---

## D. Results — Mid M1 ADX on same 7

**mid_m1_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_adx14_gt20_4h_eur40`

### M1 per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 6 | 0.9113 | 5.4678 | 11.9659 | 0.2681 | 30.7232 | 19.7678 |
| R2 | 4 | 2.0790 | 8.3162 | 15.4893 | 0.3351 | 18.5427 | 35.0187 |
| R3 | 4 | 6.5473 | 26.1894 | 14.4853 | 0.1852 | 24.3395 | 19.8179 |
| R4 | 6 | 0.6390 | 3.4465 | 6.2360 | 0.2875 | 12.2152 | 9.1820 |
| R5 | 8 | -0.9932 | -0.1448 | 18.0892 | 0.3315 | 16.1254 | 13.7988 |
| R6 | 6 | 4.9049 | 29.4295 | 20.0209 | 0.3804 | 14.0932 | 36.1697 |
| R7 | 9 | 0.2211 | 1.9896 | 6.5096 | 0.2444 | 25.4916 | 12.4650 |

**Panel summary (Mid M1):**
- windows with exp>0: **6**/7 · net>0: **6**/7
- median expectancy €/trade: **0.9113**
- median_trades: **6.0**
- panel net €: **74.6942**
- worst DD €: **20.0209**

### Soft promote (Mid M1): **PASS** (`soft_promote_v1`)

- median_trades=6.0 (ok=True, min>=1)
- exp>0: 6/7 (need ≥5; ok=True)
- panel_net €=74.6942 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs Mid #71 (M0): **PASS-but-worse**

### Honesty deltas vs Mid M0 #71 (M1 − M0)

| Metric | Mid M0 #71 €40 | Mid M1 ADX €40 | Δ |
|--------|---------------:|---------------:|--:|
| median exp € | 2.1531 | 0.9113 | -1.2418 |
| panel net € | 97.2663 | 74.6942 | -22.5721 |
| median_trades | 7.0000 | 6.0000 | -1.0000 |
| n exp>0 / 7 | 5 | 6 | 1 |
| soft promote | PASS | **PASS** | — |
| honesty | — | **PASS-but-worse** | promote_as_better=False |

---

## E. Soft PASS ≠ arm

soft_promote **PASS**. Paper only. **Soft PASS ≠ Mid-arm**. Mid/Scalp HALTED. Live ≤€20. `not_a_forecast: true`. `place_orders: false`.

