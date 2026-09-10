# 65 — rise_panel_v1 Mid: DOGE **4H BreakoutV1** long/flat (€40)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Mid-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** Mid 4H EMA baseline [`54-rise-panel-v1.md`](./54-rise-panel-v1.md); optional vs Mid Donchian [`64-rise-panel-mid-donchian20-10-4h.md`](./64-rise-panel-mid-donchian20-10-4h.md). **Canonical BreakoutV1** (Scalp #62 / lookback 16 + ATR quiet) on **4H** Mid — **no** EMA filter. Distinct from EMA and Donchian.

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
- Snapshot (#54/#55/#56): panel_net≈**€83.6104** · median_trades=**7.0** · exp>0 **6**/7.
- Optional #64 Donchian Mid: panel_net≈**€83.1242** (Δ −€0.4862 vs EMA — not promote-as-better).

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

## B. LOCKED Mid family (BEFORE scoring)

**ONE family only — NOT grinding lookback / ATR / TF / costs. No EMA filter. Do not re-grind EMA or Donchian.**

**Family:** `breakout_v1_long_flat_4h`  
**mid_improve_id:** `rise_panel_v1_mid_doge_breakoutv1_4h_eur40`  
**compare_to:** `rise_panel_v1_mid_doge_ema12_30_4h_eur40` (primary); optional `rise_panel_v1_mid_doge_donchian20_10_4h_eur40`
**Canonical BreakoutV1:** repo `BreakoutV1` / `BreakoutParams` lookback **16**, ATR SMA **14**, min_atr_frac **0.001**, atr_stop_mult **1.5** overlay (yaml untouched). Decision bar **4H**; `oneh_filter=off`. Long/flat channel exit (no Signal ATR-stop in walk_long_flat). **No** EMA filter.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- BreakoutV1 Donchian lookback **16** (entry high / exit low same N).
- **Long:** closed-bar close > prior 16-bar high AND ATR(14)/close ≥ 0.001. Long only.
- **Flat/exit:** closed-bar close < prior 16-bar low. Never short.
- **No** EMA filter / regime gate (distinct from Mid EMA baseline and Donchian #64).
- `oneh_filter: off` (decision TF is already 4H).
- Insufficient history → flat. Quiet ATR → no new long.
- Fill: signal close → next open. Size: full Mid sleeve €40 when long.
- Costs: PaperSettings 5+5 bps.
- **No** lookback / ATR / TF / cost grind on FAIL. **No** EMA / Donchian rescue.

### Why this family

Mid baseline already PASS soft_promote on plain EMA12/30 4H (panel≈€83.6104). Mid #64 Donchian soft PASS but worse (panel≈€83.1242). This trial ports **canonical BreakoutV1** (Scalp #62 lookback 16 + ATR quiet) onto Mid €40 / locked rise panel / **4H** — without EMA so the family stays distinct.

---

## C. Harness

- Script: `scripts/run_rise_panel_mid_breakout_4h_eval.py`
- Module: `atlas.paper.rise_panel_mid_breakout_4h_eval`
- Strategy: `atlas.strategy.mid_doge_breakout_4h` (thin Mid wrapper around canonical `BreakoutV1` channel + ATR quiet)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; Core+Mid book €180 on PASS only (no Scalp)
- Unit tests: `tests/unit/test_rise_panel_mid_breakout_4h.py`

---

## D. Results — Mid BreakoutV1 4H €40 on same 7

**mid_improve_id:** `rise_panel_v1_mid_doge_breakoutv1_4h_eur40`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 4 | 4.8340 | 19.3359 | 15.9467 | 0.6377 | 30.7232 | 19.7678 |
| R2 | 5 | 3.9917 | 18.9947 | 15.4934 | 0.5269 | 18.5427 | 35.0187 |
| R3 | 8 | 2.6520 | 21.2157 | 19.8661 | 0.4278 | 24.3395 | 19.8179 |
| R4 | 6 | -0.3130 | 0.8810 | 9.1358 | 0.7326 | 12.2152 | 9.1820 |
| R5 | 6 | -1.2424 | 3.5761 | 19.2500 | 0.5659 | 16.1254 | 13.7988 |
| R6 | 7 | 2.0274 | 14.1917 | 22.2321 | 0.6014 | 14.0932 | 36.1697 |
| R7 | 7 | 2.4647 | 17.2531 | 7.0301 | 0.5259 | 25.4916 | 12.4650 |

**Panel summary (Mid BreakoutV1 4H):**
- windows with exp>0: **5**/7 · net>0: **7**/7
- median expectancy €/trade: **2.4647**
- median_trades: **6.0**
- panel net €: **95.4483**
- worst DD €: **22.2321**

### Soft promote (Mid BreakoutV1): **PASS** (`soft_promote_v1`)

- median_trades=6.0 (ok=True, min>=1)
- exp>0: 5/7 (need ≥5; ok=True)
- panel_net €=95.4483 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs Mid 4H EMA baseline (Breakout − baseline)

| Metric | Mid EMA 4H €40 | Mid BreakoutV1 4H €40 | Δ |
|--------|---------------:|----------------------:|--:|
| median exp € | 2.0928 | 2.4647 | 0.3719 |
| panel net € | 83.6104 | 95.4483 | 11.8379 |
| median_trades | 7.0 | 6.0 | -1.0 |
| n exp>0 / 7 | 6 | 5 | -1 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs Mid #64 Donchian (Breakout − Donchian; optional)

| Metric | Mid Donchian 4H €40 (#64) | Mid BreakoutV1 4H €40 | Δ |
|--------|-------------------------:|----------------------:|--:|
| median exp € | 2.2860 | 2.4647 | 0.1787 |
| panel net € | 83.1242 | 95.4483 | 12.3241 |
| median_trades | 7.0 | 6.0 | -1.0 |
| n exp>0 / 7 | 5 | 5 | 0 |
| soft promote | PASS | **PASS** | — |

---

## E. Cascade / Core+Mid book (PASS → Core+Mid only, no Scalp)

Bot cascade/arming path = **Core + Mid only**. Scalp = Kaje manual — **no Scalp sleeve**. Book start **€180** (Core €140 + Mid €40). Independent sleeve panel nets (same honesty as #55 pre-cascade sleeve sums).

- **book_id:** `rise_panel_v1_core_mid_book_180_mid_breakoutv1_4h`
- **book_start_eur:** **180**
- **core_id:** `rise_panel_v1_core_doge_ema12_30_1d_eur140` (1D EMA12/30)
- **mid_id:** `rise_panel_v1_mid_doge_breakoutv1_4h_eur40` (4H BreakoutV1)
- **scalp:** none (`no_scalp=true`)
- per-sleeve panel net: Core **363.9983** · Mid **95.4483** · Core+Mid **459.4466** €

### Honesty Δ vs #55 Core+Mid portion

| Sleeve | #55 Core+Mid portion | #65 Core+Mid (this Mid) | Δ |
|--------|---------------------:|------------------------:|--:|
| Core | 363.9983 | 363.9983 | 0.0000 |
| Mid | 83.6104 | 95.4483 | 11.8379 |
| Core+Mid | 447.6087 | 459.4466 | 11.8379 |

### Honesty Δ vs #64 Core+Mid (Donchian Mid)

| Sleeve | #64 Core+Mid | #65 Core+Mid (this Mid) | Δ |
|--------|-------------:|------------------------:|--:|
| Core | 363.9983 | 363.9983 | 0.0000 |
| Mid | 83.1242 | 95.4483 | 12.3241 |
| Core+Mid | 447.1225 | 459.4466 | 12.3241 |

Reports: `data/reports/rise_panel_v1_core_mid_book_mid_breakout_65.json`

---

## What this is not

- Not a lookback / ATR / TF / cost grind.
- Not an EMA filter / period grind (Track A persist2 already softer).
- Not Donchian 20/10 (#64) — BreakoutV1 lookback 16 + ATR quiet.
- Not a change to R1–R7 window dates (phase1/54 lock).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.
- Not a Scalp sleeve (bot path Core+Mid only).
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
---

## Promote status (Kaje lock — see 65b)

**PROMOTED** to NEW Mid formal baseline: `rise_panel_v1_mid_doge_breakoutv1_4h_eur40` (panel_net≈€95.45). EMA Mid 4H = **archive reference only**. Details: [`65b-mid-breakout-promote.md`](./65b-mid-breakout-promote.md). Soft PASS / promote ≠ Mid-arm / live. Bot Core+Mid only; Scalp = Kaje manual.
