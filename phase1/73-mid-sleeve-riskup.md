# 73 — Mid #72 sleeve RISK-UP: DOGE **4H BreakoutV1 + EMA12/21** (€60)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Mid-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves (book):** Core €140 / Mid **€60** risk-up / Scalp €20 reserved (bot path still Core+Mid only — Scalp = Kaje manual).
**Compare:** Mid #71 baseline [`72-mid-long-strengthen.md`](./72-mid-long-strengthen.md) / promote [`72b-mid-breakout-ema1221-promote.md`](./72b-mid-breakout-ema1221-promote.md). Gate soft_promote_v1 vs #71 @ €40. **Same rules** as #71; Mid sleeve **€60** (1.5×). Breakout #65 = **archive only**.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

**Honesty vs #71 €40:** expect ~**1.5×** panel / expectancy / DD if linear; report Δ and ratios — **not** just bigger €.

---

## A. LOCKED Mid baseline (#71 — compare target)

**mid_baseline_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40`  
(soft_promote **PASS**, promoted #71 — see [`72b-mid-breakout-ema1221-promote.md`](./72b-mid-breakout-ema1221-promote.md))

- Rule: BreakoutV1 lookback 16 + ATR quiet + EMA12>EMA21 long-regime. Never short.
- Bar: DOGE-USDT **4H**. Sleeve: Mid **€40** (baseline).
- Compare target for this trial: **Mid €60 vs Mid #71 €40** (NOT vs Core €140).
- Snapshot (#71): panel_net≈**€97.2663** · median_trades=**7.0** · exp>0 **5**/7 · worst DD≈**€21.8963**.
- Breakout #65 archive (`rise_panel_v1_mid_doge_breakoutv1_4h_eur40`): panel_net≈**€95.4483** — **not** current Mid baseline.

### Mid #71 €40 baseline per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 4 | 5.9898 | 23.9590 | 15.7249 | 0.4583 | 30.7232 | 19.7678 |
| R2 | 7 | 0.9778 | 6.0916 | 18.3218 | 0.4659 | 18.5427 | 35.0187 |
| R3 | 6 | 4.5693 | 27.4157 | 14.7537 | 0.2944 | 24.3395 | 19.8179 |
| R4 | 8 | -0.0323 | 1.9067 | 7.9935 | 0.4304 | 12.2152 | 9.1820 |
| R5 | 7 | -0.8389 | 6.6592 | 16.5075 | 0.3919 | 16.1254 | 13.7988 |
| R6 | 7 | 2.3090 | 16.1628 | 21.8963 | 0.4710 | 14.0932 | 36.1697 |
| R7 | 7 | 2.1531 | 15.0714 | 7.1590 | 0.4556 | 25.4916 | 12.4650 |

**Panel summary (Mid #71 €40 baseline):**
- windows with exp>0: **5**/7 · net>0: **7**/7
- median expectancy €/trade: **2.1531**
- median_trades: **7.0**
- panel net €: **97.2663**
- worst DD €: **21.8963**
- soft_promote: **PASS** (`soft_promote_v1`)

---

## B. LOCKED Mid family (BEFORE scoring)

**ONE family only — NOT grinding lookback / EMA / ATR / TF / costs. No RSI. Only sleeve size change €40→€60. Same BreakoutV1 + EMA12/21 long-regime as #71.**

**Family:** `breakout_v1_ema1221_long_regime_4h`  
**mid_riskup_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur60`  
**compare_to:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40` (primary); archive `rise_panel_v1_mid_doge_breakoutv1_4h_eur40`
**Canonical:** BreakoutV1 lookback **16** + ATR quiet, gated by EMA(**12**/**21**). Decision bar **4H**. **No** RSI. Mid **€60** = 1.5× #71 €40.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- BreakoutV1: lookback **16**, ATR SMA **14**, min_atr_frac **0.001** (same as #71/#65).
- EMA long-regime: fast **12** / slow **21** (NOT 12/30).
- **Long entry:** BreakoutV1 break-up + ATR quiet **AND** EMA12 > EMA21. Long only.
- **Flat/exit:** BreakoutV1 channel exit **OR** EMA12 ≤ EMA21 (force flat / no new long). Never short.
- **No** RSI. **Size-up only:** Mid sleeve **€60** (was €40). Rules identical to #71.
- `oneh_filter: off` (decision TF is already 4H).
- Insufficient history → flat. Quiet ATR → no new long.
- Fill: signal close → next open. Size: full Mid sleeve **€60** when long.
- Costs: PaperSettings 5+5 bps.
- **No** lookback / EMA / ATR / TF / cost grind on FAIL. **No** RSI rescue.

### Why this family

Mid #71 BreakoutV1+EMA12/21 4H is the formal Mid baseline (panel≈€97.27). This trial **risks up the Mid sleeve** to €60 (1.5×) with **identical rules** — honesty requires linearity check, not celebrating bigger € alone.

---

## C. Harness

- Script: `scripts/run_rise_panel_mid_sleeve_riskup_72_eval.py`
- Module: `atlas.paper.rise_panel_mid_sleeve_riskup_72_eval`
- Strategy: `atlas.strategy.mid_doge_breakout_ema1221_4h` (same as Mid #71; sleeve €60 in harness only)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; Core+Mid book €200 on PASS (no Scalp)
- Unit tests: `tests/unit/test_rise_panel_mid_sleeve_riskup_72.py`
- Doc path: `phase1/73-mid-sleeve-riskup.md`

---

## D. Results — Mid BreakoutV1 + EMA12/21 4H €60 on same 7

**mid_riskup_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur60`

### Risk-up per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 4 | 8.9846 | 35.9385 | 23.5874 | 0.4583 | 46.0848 | 29.6517 |
| R2 | 7 | 1.4667 | 9.1374 | 27.4827 | 0.4659 | 27.8140 | 52.5280 |
| R3 | 6 | 6.8539 | 41.1235 | 22.1305 | 0.2944 | 36.5092 | 29.7269 |
| R4 | 8 | -0.0484 | 2.8600 | 11.9903 | 0.4304 | 18.3228 | 13.7731 |
| R5 | 7 | -1.2583 | 9.9887 | 24.7613 | 0.3919 | 24.1880 | 20.6982 |
| R6 | 7 | 3.4635 | 24.2442 | 32.8444 | 0.4710 | 21.1398 | 54.2546 |
| R7 | 7 | 3.2296 | 22.6072 | 10.7385 | 0.4556 | 38.2374 | 18.6975 |

**Panel summary (Mid Breakout + EMA12/21 4H €60):**
- windows with exp>0: **5**/7 · net>0: **7**/7
- median expectancy €/trade: **3.2296**
- median_trades: **7.0**
- panel net €: **145.8995**
- worst DD €: **32.8444**

### Soft promote (Mid €60 risk-up): **PASS** (`soft_promote_v1`)

- median_trades=7.0 (ok=True, min>=1)
- exp>0: 5/7 (need ≥5; ok=True)
- panel_net €=145.8995 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs #71 €40: **PASS-and-near-linear (promote-as-better eligible)**

### Honesty deltas vs Mid #71 €40 (risk-up − baseline) + linearity

| Metric | Mid #71 €40 | Mid #72 €60 | Δ | linear 1.5× | ratio vs linear |
|--------|------------:|------------:|--:|------------:|----------------:|
| panel net € | 97.2663 | 145.8995 | 48.6332 | 145.8995 | 1.0000 |
| median exp €/trade | 2.1531 | 3.2296 | 1.0765 | 3.2296 | 1.0000 |
| worst DD € | 21.8963 | 32.8444 | 10.9481 | 32.8444 | 1.0000 |
| median_trades | 7.0 | 7.0 | 0.0 | — | — |
| n exp>0 / 7 | 5 | 5 | 0 | — | — |
| soft promote | PASS | **PASS** | — | — | — |

Linearity note: size_mult=1.5×; panel ratio vs linear ≈ **1.0000** (1.0 = exact linear).

---

## E. Cascade / Core+Mid book

Bot cascade/arming path = **Core + Mid only**. Scalp = Kaje manual — **no Scalp sleeve**. Book start **€200** (Core €140 + Mid €60). soft_promote **PASS** → cascade recorded.

- **book_id:** `rise_panel_v1_core_mid_book_200_mid_breakout_ema1221_eur60`
- **book_start_eur:** **200**
- **core_id:** `rise_panel_v1_core_doge_ema12_30_1d_eur140` (1D EMA12/30)
- **mid_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur60` (4H Breakout+EMA1221 €60)
- **scalp:** none (`no_scalp=true`)
- per-sleeve panel net: Core **363.9983** · Mid **145.8995** · Core+Mid **509.8978** €

### Honesty Δ vs prior Core+Mid with Mid €40 (#71 book ≈€461.26)

| Sleeve | #71 Core+Mid (Mid €40) | #72 Core+Mid (Mid €60) | Δ |
|--------|-----------------------:|-----------------------:|--:|
| Core | 363.9983 | 363.9983 | 0.0000 |
| Mid | 97.2663 | 145.8995 | 48.6332 |
| Core+Mid | 461.2647 | 509.8978 | 48.6331 |

Reports: `data/reports/rise_panel_v1_core_mid_book_mid_breakout_ema1221_72_eur60.json`

---

## What this is not

- Not a lookback / EMA / ATR / TF / cost grind.
- Not a rule change vs #71 — **sleeve size only** (€40→€60).
- Not RSI MR (#66) or plain Breakout #65 (archive) or plain EMA12/21 (#67).
- Not a claim that bigger € alone proves better edge (linearity honesty required).
- Not Scalp HFT / Codex lane.
- Not a change to R1–R7 window dates (phase1/54 lock).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.
- Not a Scalp sleeve (bot path Core+Mid only).
- Not a claim that past rise windows forecast the next bull.
- Not a change to `config/default.yaml`.

`not_a_forecast: true`. `place_orders: false`.
