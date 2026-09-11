# 80 — rise_panel_v1 Core #73: DOGE **1D BreakoutV1 + EMA12/21** (€140)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Core-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Book:** Core + Mid #71 only; Scalp = Kaje manual. Mid formal baseline: Breakout+EMA1221 #71 `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40` panel≈€97.2663 (**unchanged** this trial).
**Compare:** Core 1D EMA baseline [`54-rise-panel-v1.md`](./54-rise-panel-v1.md). **BreakoutV1 lookback 16 + ATR quiet AND EMA12>EMA21** long-regime on **1D** Core. **No** RSI. Research Core **#73**; doc file **80**. Promote-as-better only if panel_net > Core EMA.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

**Honesty:** promote-as-better only if panel_net higher than Core EMA baseline. Core EMA often thin n / BH-like — soft PASS alone ≠ Core-arm.

---

## A. LOCKED Core EMA baseline (do not retune)

**core_baseline_id:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`  
(phase1/54 reference; soft_promote NOT applied for board rewrite — informational soft would FAIL; thin n / BH-like)

- Rule: closed-bar **EMA12 > EMA30** → long; else flat. Never short.
- Bar: DOGE-USDT **1D**. Sleeve: Core **€140**.
- Compare target for this trial: **Core Breakout+EMA1221 vs Core-EMA-baseline**.
- Snapshot (#54/#55/#71 recheck): panel_net≈**€363.9983** · median_trades=**1.0** · exp>0 **2**/7 (VERIFY measured below — do not invent).

### Core EMA baseline per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 0 | — | 100.9579 | 53.4298 | 0.5714 | 104.3781 | 54.2424 |
| R2 | 2 | -7.4986 | -16.6090 | 69.2569 | 0.4022 | 69.3232 | 113.9447 |
| R3 | 1 | -10.5166 | 82.0222 | 43.1498 | 0.3146 | 88.7868 | 52.9270 |
| R4 | 0 | — | 35.3467 | 14.4543 | 0.4111 | 41.4976 | 14.9763 |
| R5 | 1 | 1.5895 | 83.1141 | 32.5003 | 0.5333 | 85.9404 | 40.0347 |
| R6 | 1 | 26.3396 | 16.7226 | 87.9988 | 0.6154 | 36.2360 | 108.5424 |
| R7 | 0 | — | 62.4439 | 34.5043 | 0.4944 | 85.2900 | 38.4366 |

**Panel summary (Core EMA baseline — measured):**
- windows with exp>0: **2**/7 · net>0: **6**/7
- median expectancy €/trade: **-2.9545**
- median_trades: **1.0**
- panel net €: **363.9983**
- worst DD €: **87.9988**
- soft_promote (informational only): **FAIL** (`soft_promote_v1`) — NOT a board rewrite

---

## B. LOCKED Core family (BEFORE scoring)

**ONE family only — NOT grinding lookback / EMA / ATR / TF / costs. No RSI. Do not re-grind Core EMA / plain Breakout #69 / Donchian #70.**

**Family:** `breakout_v1_ema1221_long_regime_1d`  
**core_improve_id:** `rise_panel_v1_core_doge_breakoutv1_ema1221_long_1d_eur140`  
**compare_to:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`
**Canonical:** BreakoutV1 lookback **16** + ATR quiet, gated by EMA(**12**/**21**). Decision bar **1D**. **No** RSI. Same Core €140 as #69/#70.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1D**.
- BreakoutV1: lookback **16**, ATR SMA **14**, min_atr_frac **0.001** (same as #69).
- EMA long-regime: fast **12** / slow **21** (NOT 12/30).
- **Long entry:** BreakoutV1 break-up + ATR quiet **AND** EMA12 > EMA21. Long only.
- **Flat/exit:** BreakoutV1 channel exit **OR** EMA12 ≤ EMA21 (force flat / no new long). Never short.
- **No** RSI. Distinct from plain Breakout #69, Donchian #70, Core EMA12/30.
- `oneh_filter: off` (decision TF is already 1D).
- Insufficient history → flat. Quiet ATR → no new long.
- Fill: signal close → next open. Size: full Core sleeve €140 when long.
- Costs: PaperSettings 5+5 bps.
- **No** lookback / EMA / ATR / TF / cost grind on FAIL. **No** RSI rescue.

### Why this family

Core EMA baseline panel≈€363.9983 with thin median_trades=1.0 (BH-like). Mid #71 Breakout+EMA1221 beat Mid Breakout #65 on panel_net. Core #69 plain Breakout failed soft_promote / was not better on panel_net. This trial ports **BreakoutV1 + EMA12/21 long-regime** (same as Mid #71) onto Core €140 / 1D.

---

## C. Harness

- Script: `scripts/run_rise_panel_core_breakout_ema1221_1d_eval.py`
- Module: `atlas.paper.rise_panel_core_breakout_ema1221_1d_eval`
- Strategy: `atlas.strategy.core_doge_breakout_ema1221_1d` (BreakoutV1 + EMA12/21 long-regime; Core #73)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; Core(this)+Mid(#71) book €180 on PASS+better only (no Scalp)
- Unit tests: `tests/unit/test_rise_panel_core_breakout_ema1221_1d.py`
- Doc path: `phase1/80-rise-panel-core-breakout-ema1221-1d.md` (research Core #73; avoid clash with Mid sleeve-riskup doc 73)

---

## D. Results — Core BreakoutV1 + EMA12/21 1D €140 on same 7

**core_improve_id:** `rise_panel_v1_core_doge_breakoutv1_ema1221_long_1d_eur140`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 1 | 10.4682 | 41.9638 | 46.3083 | 0.4505 | 104.3781 | 54.2424 |
| R2 | 1 | 7.7974 | 7.7974 | 49.2121 | 0.3370 | 69.3232 | 113.9447 |
| R3 | 1 | -21.1023 | 63.8710 | 39.6221 | 0.2472 | 88.7868 | 52.9270 |
| R4 | 0 | — | 39.5834 | 14.8036 | 0.4222 | 41.4976 | 14.9763 |
| R5 | 1 | -10.9926 | 63.2875 | 32.6073 | 0.4889 | 85.9404 | 40.0347 |
| R6 | 1 | 29.9495 | 29.9495 | 74.7719 | 0.4835 | 36.2360 | 108.5424 |
| R7 | 0 | — | 62.4439 | 34.5043 | 0.4944 | 85.2900 | 38.4366 |

**Panel summary (Core BreakoutV1 + EMA12/21 1D):**
- windows with exp>0: **3**/7 · net>0: **7**/7
- median expectancy €/trade: **7.7974**
- median_trades: **1.0**
- panel net €: **308.8966**
- worst DD €: **74.7719**

### Soft promote (Core Breakout + EMA12/21): **FAIL** (`soft_promote_v1`)

- median_trades=1.0 (ok=True, min>=1)
- exp>0: 3/7 (need ≥5; ok=False)
- panel_net €=308.8966 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs Core EMA: **FAIL**

### Honesty deltas vs Core 1D EMA baseline (Breakout+EMA1221 − baseline)

> **Primary compare:** panel_net Δ **≤0** vs Core EMA baseline (≈€363.9983). **Not better on panel net — do not promote-as-better.** Soft PASS ≠ Core-arm.

| Metric | Core EMA 1D €140 | Core Breakout+EMA1221 1D €140 | Δ |
|--------|-----------------:|------------------------------:|--:|
| median exp € | -2.9545 | 7.7974 | 10.7520 |
| panel net € | 363.9983 | 308.8966 | -55.1018 |
| median_trades | 1.0 | 1.0 | 0.0 |
| n exp>0 / 7 | 2 | 3 | 1 |
| soft promote | FAIL (info) | **FAIL** | — |
| promote-as-better | — | **NO** | — |

---

## E. On FAIL — archive (no grind, no auto-next)

soft_promote **FAIL** (or incomplete). Archive this family. Do **not** grind lookback / EMA / ATR / TF / costs. Do **not** retune #69 Breakout alone or #70 Donchian. Do **not** auto-start next. Do **not** invent Scalp. Cascade skip. Mid #71 unchanged. Ping-ready for coordinator.

---

## What this is not

- Not a lookback / EMA / ATR / TF / cost grind.
- Not RSI MR / RSI filter.
- Not a rescue / retune of Core #69 Breakout alone or Core #70 Donchian.
- Not plain BreakoutV1 alone (#69) — this adds EMA12/21 regime.
- Not Donchian 20/10 (#70).
- Not Mid #71 (4H) — this is Core 1D with the same regime pattern.
- Not a change to R1–R7 window dates (phase1/54 lock).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Core-arming / Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.
- Not a Scalp sleeve (bot path Core+Mid only; Scalp = Kaje manual).
- Not a change to Mid baseline #71.
- Not a claim that past rise windows forecast the next bull.
- **Not better than Core EMA baseline on panel_net** — do not promote-as-better.

`not_a_forecast: true`. `place_orders: false`.
