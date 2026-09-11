# 89 — rise_panel_v1 Core **C2**: DOGE **1D Donchian 40/20 + EMA50/200** regime (€140)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**; Mid/Scalp **HALTED**; Soft PASS ≠ Core-arm. Plan: [`84-atlas-trading-vnext.md`](./84-atlas-trading-vnext.md).
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change).
**Compare:** Core C0 EMA12/30 [`54`](./54-rise-panel-v1.md). Prior C1 Donchian40/20 soft **FAIL** [`88`](./88-rise-panel-core-c1-donchian40-20-1d.md). **No** Donchian N / EMA / ADX / ATR grind. Branch: `research/vnext-core-c2-donchian40-20-ema50-200`. Base: main after PR #83 (C1 merged).

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1`: median_trades≥1 AND ≥5/7 exp>0 AND panel_net>0.
Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

**Honesty:** Soft PASS ≠ Core-arm. Promote-as-better only if panel_net > Core EMA C0. C2 is the pre-registered rung after C1 FAIL — **NOT rescue**. If C2 FAIL → stop Core Donchian family (**no C3**).

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

## B. LOCKED Core C2 family (BEFORE scoring)

**ONE family only — Donchian 40/20 + EMA50/200 regime as locked in #84 §3 CORE. No ADX/ATR (C3–C4). No N/TF/EMA grind.**

**Family:** `donchian40_20_ema50_200_regime_1d`  
**core_c2_id:** `rise_panel_v1_core_doge_donchian40_20_ema50_200_1d_eur140`  
**compare_to:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`  
**prior_c1_id:** `rise_panel_v1_core_doge_donchian40_20_1d_eur140` (soft FAIL — #88)
**Locked:** Donchian entry **40** / exit **20** + EMA**50**/**200** regime (yaml untouched). Decision bar **1D**. Long/flat only.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1D**.
- Donchian entry lookback **40** / exit lookback **20**.
- **Regime:** closed-bar **EMA50 > EMA200** required for long; **force flat** when EMA50 ≤ EMA200.
- **Long:** regime bull AND closed-bar close > prior 40-bar high. Long only.
- **Flat/exit:** regime fail OR closed-bar close < prior 20-bar low. Never short.
- **No** ADX / ATR (C3=ADX; C4=ATR trail). No close>EMA200 extra gate (that is C4 sketch).
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Core sleeve €140 when long.
- Costs: PaperSettings 5+5 bps.
- **No** Donchian N / EMA / TF / cost grind on FAIL. **Not** a rescue of C1.

### Why this family

Pre-registered Core ladder **C2** from [`84`](./84-atlas-trading-vnext.md): C1 Donchian **40/20** + **EMA50/200** regime filter. C1 soft FAIL ([`88`](./88-rise-panel-core-c1-donchian40-20-1d.md)) eliminated under its own gate; this rung is still run as the **pre-registered** next hypothesis — **NOT rescue / NOT param fishing**. If C2 FAIL → **stop Core Donchian family (no C3)**.

---

## C. Harness

- Script: `scripts/run_rise_panel_core_c2_donchian_ema_1d_eval.py`
- Module: `atlas.paper.rise_panel_core_c2_donchian_ema_1d_eval`
- Strategy: `atlas.strategy.core_doge_donchian40_20_ema50_200_1d` (Donchian 40/20 + EMA50/200 regime)
- Unit tests: `tests/unit/test_rise_panel_core_c2_donchian_ema_1d.py`

---

## D. Results — Core C2 Donchian 40/20 + EMA50/200 1D €140 on same 7

**core_c2_id:** `rise_panel_v1_core_doge_donchian40_20_ema50_200_1d_eur140`

### C2 per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 0 | — | 41.7391 | 40.2987 | 0.4396 | 104.3781 | 54.2424 |
| R2 | 1 | -25.4819 | -25.4819 | 38.1311 | 0.2500 | 69.3232 | 113.9447 |
| R3 | 0 | — | 0.0000 | 0.0000 | 0.0000 | 88.7868 | 52.9270 |
| R4 | 0 | — | 0.0000 | 0.0000 | 0.0000 | 41.4976 | 14.9763 |
| R5 | 1 | -10.9926 | 40.2338 | 29.3723 | 0.3556 | 85.9404 | 40.0347 |
| R6 | 1 | 29.9495 | 29.9495 | 74.7719 | 0.4835 | 36.2360 | 108.5424 |
| R7 | 0 | — | -11.9507 | 21.9564 | 0.0674 | 85.2900 | 38.4366 |

**Panel summary (Core C2 Donchian 40/20 + EMA50/200):**
- windows with exp>0: **1**/7 · net>0: **3**/7
- median expectancy €/trade: **-10.9926**
- median_trades: **0.0**
- panel net €: **74.4898**
- worst DD €: **74.7719**

### Soft promote (Core C2): **FAIL** (`soft_promote_v1`)

- median_trades=0.0 (ok=False, min>=1)
- exp>0: 1/7 (need ≥5; ok=False)
- panel_net €=74.4898 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs Core C0 EMA: **FAIL**

### Honesty deltas vs Core C0 EMA (C2 − C0)

| Metric | Core C0 EMA €140 | Core C2 Donchian40/20+EMA50/200 €140 | Δ |
|--------|-----------------:|-------------------------------------:|--:|
| median exp € | -2.9545 | -10.9926 | -8.0380 |
| panel net € | 363.9983 | 74.4898 | -289.5085 |
| median_trades | 1.0 | 0.0 | -1.0 |
| n exp>0 / 7 | 2 | 1 | -1 |
| soft promote | FAIL (info) | **FAIL** | — |
| honesty | — | **FAIL** | promote_as_better=False |
| C3 allowed | — | **False** | only if C2 soft PASS; else stop family |

---

## E. Soft PASS ≠ arm · C3 / family stop gate

soft_promote **FAIL**. Paper only. **Soft PASS ≠ Core-arm**. Mid/Scalp HALTED. Live ≤€20. `not_a_forecast: true`. `place_orders: false`.

**C2 eliminated.** Do **not** run C3. **Stop Core Donchian family.** Archive. No Donchian N / EMA / ADX grind. Not a rescue of C1.

---

## What this is not

- Not a Donchian N / EMA / TF / cost grind.
- Not a rescue / re-tune of C1 FAIL (#88).
- Not C3 (ADX) or C4 (ATR trail) — prefixes only.
- Not Core #70 Donchian 20/10 (different lookbacks; that rung FAIL).
- Not a change to R1–R7 window dates.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Core-arming. Soft PASS ≠ arm. Live ≤€20 HALTED.
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
