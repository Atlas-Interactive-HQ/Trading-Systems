# 87 — rise_panel_v1 Scalp **S1**: #83 Dual Thrust + **RVOL>1** 1H €20

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**; Mid/Scalp **HALTED**; Soft PASS ≠ Scalp-arm. Plan: [`84-atlas-trading-vnext.md`](./84-atlas-trading-vnext.md).
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change).
**Compare:** Scalp S0=#83 [`83-rise-panel-scalp-dual-thrust-1h.md`](./83-rise-panel-scalp-dual-thrust-1h.md). **No** N/k/RVOL grind. Branch: `research/atlas-trading-vnext-84`.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1`: median_trades≥1 AND ≥5/7 exp>0 AND panel_net>0.
Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

---

## A. LOCKED Scalp S0 baseline (#83)

**scalp_s0_id:** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20`

### S0 per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 16 | 0.0278 | 0.4451 | 6.4872 | 0.6205 | 15.3616 | 10.6267 |
| R2 | 7 | 1.0729 | 6.5725 | 7.2502 | 0.5650 | 9.2713 | 17.5480 |
| R3 | 12 | 0.8463 | 10.1558 | 13.8215 | 0.4366 | 12.1697 | 13.4725 |
| R4 | 5 | -0.2980 | -0.6700 | 4.0964 | 0.1896 | 6.1076 | 4.9136 |
| R5 | 7 | 0.4974 | 11.0009 | 4.6419 | 0.4954 | 8.0627 | 6.9305 |
| R6 | 8 | 0.2086 | 1.6690 | 10.9765 | 0.5924 | 7.0466 | 18.0849 |
| R7 | 10 | 0.1958 | 2.0031 | 4.8612 | 0.2898 | 12.7458 | 7.0240 |

**Panel summary (Scalp S0 #83 re-score):**
- windows with exp>0: **6**/7 · net>0: **6**/7
- median expectancy €/trade: **0.2086**
- median_trades: **8.0**
- panel net €: **31.1763**
- worst DD €: **13.8215**
- soft_promote: **PASS** (`soft_promote_v1`)

---

## B. LOCKED Scalp S1 family (BEFORE scoring)

**Family:** `dual_thrust_n20_k0505_rvol_gt1_long_flat_1h`  
**scalp_s1_id:** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20`  
**compare_to:** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20`

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.
- Dual Thrust: N=**20**, k1=**0.5**, k2=**0.5** (same as #83).
- **RVOL gate (locked once):** `RVOL = volume / SMA(volume, 20)` ; require **RVOL > 1**.
- **Long entry:** Dual Thrust buy break **AND** RVOL>1. Long only.
- **Flat/exit:** Dual Thrust sell break (RVOL does **not** force flat). Never short.
- Fill: next-open. Size: Scalp €20. Costs: 5+5 bps.
- **No** N/k/RVOL lookback/threshold/TF grind on FAIL.

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_s1_rvol_1h_eval.py`
- Module: `atlas.paper.rise_panel_scalp_s1_rvol_1h_eval`
- Strategy: `atlas.strategy.scalp_doge_dual_thrust_rvol_1h`
- Unit tests: `tests/unit/test_rise_panel_scalp_s1_rvol_1h.py`

---

## D. Results — Scalp S1 RVOL on same 7

**scalp_s1_id:** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20`

### S1 per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 14 | 0.1395 | 1.9536 | 6.9658 | 0.6178 | 15.3616 | 10.6267 |
| R2 | 7 | 1.0729 | 6.5725 | 7.2502 | 0.5650 | 9.2713 | 17.5480 |
| R3 | 12 | 0.8463 | 10.1558 | 13.8215 | 0.4366 | 12.1697 | 13.4725 |
| R4 | 5 | -0.2980 | -0.6700 | 4.0964 | 0.1896 | 6.1076 | 4.9136 |
| R5 | 7 | 0.4974 | 11.0009 | 4.6419 | 0.4954 | 8.0627 | 6.9305 |
| R6 | 8 | 0.2086 | 1.6690 | 10.9765 | 0.5924 | 7.0466 | 18.0849 |
| R7 | 10 | 0.1958 | 1.9582 | 4.8612 | 0.2894 | 12.7458 | 7.0240 |

**Panel summary (Scalp S1):**
- windows with exp>0: **6**/7 · net>0: **6**/7
- median expectancy €/trade: **0.2086**
- median_trades: **8.0**
- panel net €: **32.6400**
- worst DD €: **13.8215**

### Soft promote (Scalp S1): **PASS** (`soft_promote_v1`)

- median_trades=8.0 (ok=True, min>=1)
- exp>0: 6/7 (need ≥5; ok=True)
- panel_net €=32.6400 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs Scalp #83 (S0): **PASS-and-better**

### Honesty deltas vs Scalp S0 #83 (S1 − S0)

| Metric | Scalp S0 #83 €20 | Scalp S1 RVOL €20 | Δ |
|--------|-----------------:|------------------:|--:|
| median exp € | 0.2086 | 0.2086 | 0.0000 |
| panel net € | 31.1763 | 32.6400 | 1.4637 |
| median_trades | 8.0000 | 8.0000 | 0.0000 |
| n exp>0 / 7 | 6 | 6 | 0 |
| soft promote | PASS | **PASS** | — |
| honesty | — | **PASS-and-better** | promote_as_better=True |

---

## E. Soft PASS ≠ arm

soft_promote **PASS**. Paper only. **Soft PASS ≠ Scalp-arm**. Mid/Scalp HALTED. Live ≤€20. `not_a_forecast: true`. `place_orders: false`.

