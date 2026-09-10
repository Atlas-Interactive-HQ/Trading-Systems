# 56 — rise_panel_v1 Mid improvement: EMA12/30 **persist2 entry** on 4H (€40)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

---

## A. LOCKED Mid baseline (do not retune)

**mid_baseline_id:** `rise_panel_v1_mid_doge_ema12_30_4h_eur40`  
(soft_promote **PASS**, merged #53 / phase1/54)

- Rule: closed-bar **EMA12 > EMA30** → long; else flat. Never short.
- Bar: DOGE-USDT **4H**. Sleeve: Mid **€40**.
- Compare target for this trial: **Mid vs Mid-baseline** (NOT vs Core €140).

### Mid baseline per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 5 | 2.6469 | 14.1670 | 21.2626 | 0.5670 | 30.7232 | 19.7678 |
| R2 | 5 | 2.6589 | 17.2682 | 23.2540 | 0.5412 | 18.5427 | 35.0187 |
| R3 | 15 | 0.8429 | 12.6435 | 20.8896 | 0.4519 | 24.3395 | 19.8179 |
| R4 | 10 | 0.2490 | 4.8046 | 6.5329 | 0.5238 | 12.2152 | 9.1820 |
| R5 | 11 | -0.6979 | 4.1914 | 19.3072 | 0.4890 | 16.1254 | 13.7988 |
| R6 | 7 | 2.2694 | 15.8860 | 29.8875 | 0.5960 | 14.0932 | 36.1697 |
| R7 | 7 | 2.0928 | 14.6496 | 9.4064 | 0.5815 | 25.4916 | 12.4650 |

**Panel summary (Mid baseline):**
- windows with exp>0: **6**/7 · net>0: **7**/7
- median expectancy €/trade: **2.0928**
- median_trades: **7.0**
- panel net €: **83.6104**
- worst DD €: **29.8875**
- soft_promote: **PASS** (`soft_promote_v1`)

---

## B. LOCKED improvement family (BEFORE scoring)

**ONE family only — NOT grinding EMA 12/30 periods.**

**Family:** `ema12_30_persist2_entry_4h`  
**mid_improve_id:** `rise_panel_v1_mid_doge_ema12_30_persist2_4h_eur40`  
**compare_to:** `rise_panel_v1_mid_doge_ema12_30_4h_eur40`

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- EMA periods: **fast=12, slow=30** (same as Mid baseline — no period grind).
- **Entry (FLAT→LONG):** EMA12 > EMA30 on *this* closed 4H bar **AND** on the prior closed 4H bar (`entry_persist=2`). Reuses `EmaPersist2EntryV1` / `atlas.strategy.ema_persist2`.
- **Exit (LONG→FLAT):** first closed bar with EMA12 ≤ EMA30 (**immediate** exit; no persist on exit).
- Never short. Insufficient history → flat.
- Fill: signal close → next open. Size: full Mid sleeve €40 when long.
- Costs: PaperSettings 5+5 bps.
- **No** persist=3/4/5 sweeps. **No** Donchian / ATR / RSI rescue knobs this trial. **No** EMA period / TF / cost grind on FAIL.

### Why this family

Mid baseline already PASS soft_promote on plain EMA12/30 4H. Persist-2 entry is a **structure** change (asymmetric confirmation) intended to cut whipsaw entries in choppy-bull rise windows without retuning the 12/30 periods.

---

## C. Harness

- Script: `scripts/run_rise_panel_mid_improve_eval.py`
- Module: `atlas.paper.rise_panel_mid_improve_eval`
- Strategy: `atlas.strategy.mid_doge_ema_persist2_4h` (thin Mid wrapper around `EmaPersist2EntryV1`)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows
- Unit tests: `tests/unit/test_rise_panel_mid_improve.py`

---

## D. Results — Mid improve (persist2) on same 7

**mid_improve_id:** `rise_panel_v1_mid_doge_ema12_30_persist2_4h_eur40`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 5 | 2.1561 | 12.9404 | 20.1068 | 0.5562 | 30.7232 | 19.7678 |
| R2 | 4 | 3.8978 | 19.5139 | 21.7142 | 0.5305 | 18.5427 | 35.0187 |
| R3 | 13 | 1.2251 | 15.9267 | 19.8736 | 0.4259 | 24.3395 | 19.8179 |
| R4 | 10 | 0.1036 | 3.3863 | 7.1176 | 0.5055 | 12.2152 | 9.1820 |
| R5 | 10 | -0.6872 | 5.2555 | 18.5507 | 0.4689 | 16.1254 | 13.7988 |
| R6 | 7 | 1.3918 | 9.7425 | 31.8146 | 0.5851 | 14.0932 | 36.1697 |
| R7 | 7 | 1.6547 | 11.5826 | 8.8785 | 0.5685 | 25.4916 | 12.4650 |

**Panel summary (Mid improve):**
- windows with exp>0: **6**/7 · net>0: **7**/7
- median expectancy €/trade: **1.3918**
- median_trades: **7.0**
- panel net €: **78.3479**
- worst DD €: **31.8146**

### Soft promote (Mid improve): **PASS** (`soft_promote_v1`)

- median_trades=7.0 (ok=True, min>=1)
- exp>0: 6/7 (need ≥5; ok=True)
- panel_net €=78.3479 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Deltas vs Mid 4H baseline (improve − baseline)

| Metric | Mid baseline €40 | Mid persist2 €40 | Δ |
|--------|-----------------:|-----------------:|--:|
| median exp € | 2.0928 | 1.3918 | -0.7010 |
| panel net € | 83.6104 | 78.3479 | -5.2625 |
| median_trades | 7.0 | 7.0 | 0.0 |
| n exp>0 / 7 | 6 | 6 | 0 |
| soft promote | PASS | **PASS** | — |

---

## What this is not

- Not an EMA 12/30 period grind.
- Not a compare vs Core €140 (Mid vs Mid-baseline only).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
