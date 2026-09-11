# 88 — rise_panel_v1 Core **C1**: DOGE **1D Donchian 40/20** long/flat (€140)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**; Mid/Scalp **HALTED**; Soft PASS ≠ Core-arm. Plan: [`84-atlas-trading-vnext.md`](./84-atlas-trading-vnext.md).
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change).
**Compare:** Core C0 EMA12/30 [`54`](./54-rise-panel-v1.md). Honesty vs #70 Donchian20/10 FAIL [`70`](./70-rise-panel-core-donchian20-10-1d.md). **No** Donchian N / EMA / ADX / ATR grind. Branch: `research/vnext-core-c1-donchian40-20`. Base: main after PR #81+#82.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1`: median_trades≥1 AND ≥5/7 exp>0 AND panel_net>0.
Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

**Honesty:** Soft PASS ≠ Core-arm. Promote-as-better only if panel_net > Core EMA C0. C2 only if C1 not eliminated. #70 Donchian20/10 was FAIL — C1 may also fail.

---

## A. LOCKED Core C0 baseline (EMA12/30)

**core_c0_id:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`

(phase1/54 reference; soft_promote NOT applied for board rewrite — informational soft often FAIL; thin n / BH-like)

- Rule: closed-bar **EMA12 > EMA30** → long; else flat. Never short.
- Bar: DOGE-USDT **1D**. Sleeve: Core **€140**.
- Snapshot (#54): panel_net≈**€363.9983** · median_trades=**1.0** · exp>0 **2**/7 (VERIFY measured below — do not invent).

### Core C0 per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 0 | — | 100.9579 | 53.4298 | 0.5714 | 104.3781 | 54.2424 |
| R2 | 2 | -7.4986 | -16.6090 | 69.2569 | 0.4022 | 69.3232 | 113.9447 |
| R3 | 1 | -10.5166 | 82.0222 | 43.1498 | 0.3146 | 88.7868 | 52.9270 |
| R4 | 0 | — | 35.3467 | 14.4543 | 0.4111 | 41.4976 | 14.9763 |
| R5 | 1 | 1.5895 | 83.1141 | 32.5003 | 0.5333 | 85.9404 | 40.0347 |
| R6 | 1 | 26.3396 | 16.7226 | 87.9988 | 0.6154 | 36.2360 | 108.5424 |
| R7 | 0 | — | 62.4439 | 34.5043 | 0.4944 | 85.2900 | 38.4366 |

**Panel summary (Core C0 EMA — measured):**
- windows with exp>0: **2**/7 · net>0: **6**/7
- median expectancy €/trade: **-2.9545**
- median_trades: **1.0**
- panel net €: **363.9983**
- worst DD €: **87.9988**
- soft_promote (informational only): **FAIL** (`soft_promote_v1`) — NOT a board rewrite

---

## B. LOCKED Core C1 family (BEFORE scoring)

**ONE family only — Donchian 40/20 as locked in #84 §3 CORE. No EMA/ADX/ATR (C2–C4). No N/TF grind.**

**Family:** `donchian40_20_long_flat_1d`  
**core_c1_id:** `rise_panel_v1_core_doge_donchian40_20_1d_eur140`  
**compare_to:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`
**Locked:** `DonchianLongFlatV1` entry **40** / exit **20** (yaml untouched). Decision bar **1D**. Long/flat only.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1D**.
- Donchian entry lookback **40** / exit lookback **20**.
- **Long:** closed-bar close > prior 40-bar high. Long only.
- **Flat/exit:** closed-bar close < prior 20-bar low. Never short.
- **No** EMA / ADX / ATR (C2=EMA50/200; C3=ADX; C4=ATR trail).
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Core sleeve €140 when long.
- Costs: PaperSettings 5+5 bps.
- **No** Donchian N / TF / cost grind on FAIL. **No** EMA rescue.

### Why this family

Pre-registered Core ladder C1 from [`84`](./84-atlas-trading-vnext.md). #70 Donchian **20/10** soft FAIL / worse panel_net. C1 widens to **40/20** (entry High40 / exit Low20) as the honesty rung before C2+ regime/strength. Research value expected at C2+; do not hide a C1 FAIL.

---

## C. Harness

- Script: `scripts/run_rise_panel_core_c1_donchian_1d_eval.py`
- Module: `atlas.paper.rise_panel_core_c1_donchian_1d_eval`
- Strategy: `atlas.strategy.core_doge_donchian40_20_1d` (wrapper around `DonchianLongFlatV1` 40/20)
- Unit tests: `tests/unit/test_rise_panel_core_c1_donchian_1d.py`

---

## D. Results — Core C1 Donchian 40/20 1D €140 on same 7

**core_c1_id:** `rise_panel_v1_core_doge_donchian40_20_1d_eur140`

### C1 per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 0 | — | 41.7391 | 40.2987 | 0.4396 | 104.3781 | 54.2424 |
| R2 | 1 | -25.4819 | -25.4819 | 38.1311 | 0.2500 | 69.3232 | 113.9447 |
| R3 | 1 | -31.1945 | 22.9542 | 37.0296 | 0.2697 | 88.7868 | 52.9270 |
| R4 | 0 | — | 35.3467 | 14.4543 | 0.4111 | 41.4976 | 14.9763 |
| R5 | 1 | -1.0880 | 54.0712 | 31.6274 | 0.3889 | 85.9404 | 40.0347 |
| R6 | 1 | 29.9495 | 29.9495 | 74.7719 | 0.4835 | 36.2360 | 108.5424 |
| R7 | 0 | — | 49.5559 | 32.3077 | 0.4382 | 85.2900 | 38.4366 |

**Panel summary (Core C1 Donchian 40/20):**
- windows with exp>0: **1**/7 · net>0: **6**/7
- median expectancy €/trade: **-13.2850**
- median_trades: **1.0**
- panel net €: **208.1348**
- worst DD €: **74.7719**

### Soft promote (Core C1): **FAIL** (`soft_promote_v1`)

- median_trades=1.0 (ok=True, min>=1)
- exp>0: 1/7 (need ≥5; ok=False)
- panel_net €=208.1348 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs Core C0 EMA: **FAIL**

### Honesty deltas vs Core C0 EMA (C1 − C0)

| Metric | Core C0 EMA €140 | Core C1 Donchian40/20 €140 | Δ |
|--------|-----------------:|---------------------------:|--:|
| median exp € | -2.9545 | -13.2850 | -10.3304 |
| panel net € | 363.9983 | 208.1348 | -155.8635 |
| median_trades | 1.0 | 1.0 | 0.0 |
| n exp>0 / 7 | 2 | 1 | -1 |
| soft promote | FAIL (info) | **FAIL** | — |
| honesty | — | **FAIL** | promote_as_better=False |
| C2 allowed | — | **False** | only if C1 not eliminated |

---

## E. Soft PASS ≠ arm · C2 gate

soft_promote **FAIL**. Paper only. **Soft PASS ≠ Core-arm**. Mid/Scalp HALTED. Live ≤€20. `not_a_forecast: true`. `place_orders: false`.

**C1 eliminated.** Do **not** run C2. Archive. No Donchian N grind. No EMA/ADX rescue on this rung.

---

## What this is not

- Not a Donchian N / TF / cost grind.
- Not C2 (EMA50/200), C3 (ADX), or C4 (ATR trail) — prefixes only.
- Not Core #70 Donchian 20/10 (different lookbacks; that rung FAIL).
- Not a change to R1–R7 window dates.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Core-arming. Soft PASS ≠ arm. Live ≤€20 HALTED.
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
