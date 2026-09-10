# 64 — rise_panel_v1 Mid: DOGE **4H Donchian 20/10** long/flat (€40)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Mid-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** Mid 4H EMA baseline [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) / [`56-rise-panel-mid-persist2.md`](./56-rise-panel-mid-persist2.md). **Canonical Donchian** (Scalp #61 / Mid #44 / `DonchianLongFlatV1`) on **4H** Mid. Do not re-grind EMA (Track A persist2 softer).

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

**ONE family only — NOT grinding Donchian N / TF / costs. No EMA filter. Do not re-grind EMA.**

**Family:** `donchian20_10_long_flat_4h`  
**mid_improve_id:** `rise_panel_v1_mid_doge_donchian20_10_4h_eur40`  
**compare_to:** `rise_panel_v1_mid_doge_ema12_30_4h_eur40`

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- Donchian: entry lookback **20**, exit lookback **10**.
- **Long:** closed-bar close > prior 20-bar high (exclusive lookback). Long only.
- **Flat/exit:** closed-bar close < prior 10-bar low. Never short.
- **No** EMA filter / regime gate. **No** ATR / time-stop knobs this trial (walk_long_flat / DonchianLongFlatV1 — same as Scalp #61).
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Mid sleeve €40 when long.
- Costs: PaperSettings 5+5 bps.
- **No** Donchian-N / TF / cost grind on FAIL. **No** EMA rescue. Track A persist2 was soft PASS but worse — do not re-grind EMA.

### Why this family

Mid baseline already PASS soft_promote on plain EMA12/30 4H (panel≈€83.6104). This trial ports the **canonical Donchian 20/10** paper rule (Scalp #61 / Mid #44 spirit, no EMA) onto Mid €40 / locked rise panel / **4H**.

---

## C. Harness

- Script: `scripts/run_rise_panel_mid_donchian_4h_eval.py`
- Module: `atlas.paper.rise_panel_mid_donchian_4h_eval`
- Strategy: `atlas.strategy.mid_doge_donchian_4h` (thin Mid wrapper around `DonchianLongFlatV1`)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; Core+Mid book €180 on PASS only (no Scalp)
- Unit tests: `tests/unit/test_rise_panel_mid_donchian_4h.py`

---

## D. Results — Mid Donchian 20/10 4H €40 on same 7

**mid_improve_id:** `rise_panel_v1_mid_doge_donchian20_10_4h_eur40`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 5 | 3.6565 | 18.2826 | 12.5519 | 0.4674 | 30.7232 | 19.7678 |
| R2 | 6 | 2.3114 | 13.0023 | 12.9710 | 0.4373 | 18.5427 | 35.0187 |
| R3 | 6 | 4.7970 | 28.7820 | 15.0527 | 0.2593 | 24.3395 | 19.8179 |
| R4 | 7 | -0.2490 | -0.5617 | 10.9903 | 0.5092 | 12.2152 | 9.1820 |
| R5 | 7 | -0.5873 | 7.3817 | 14.8135 | 0.4304 | 16.1254 | 13.7988 |
| R6 | 8 | 0.0294 | 0.2354 | 33.8666 | 0.3351 | 14.0932 | 36.1697 |
| R7 | 7 | 2.2860 | 16.0020 | 6.0450 | 0.4870 | 25.4916 | 12.4650 |

**Panel summary (Mid Donchian 20/10 4H):**
- windows with exp>0: **5**/7 · net>0: **6**/7
- median expectancy €/trade: **2.2860**
- median_trades: **7.0**
- panel net €: **83.1242**
- worst DD €: **33.8666**

### Soft promote (Mid Donchian): **PASS** (`soft_promote_v1`)

- median_trades=7.0 (ok=True, min>=1)
- exp>0: 5/7 (need ≥5; ok=True)
- panel_net €=83.1242 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs Mid 4H EMA baseline (Donchian − baseline)

> **Primary compare:** panel_net Δ **negative** vs Mid EMA baseline (≈€83.6104). **Worse on panel net — do not promote-as-better.** Soft PASS ≠ better.

| Metric | Mid EMA 4H €40 | Mid Donchian 4H €40 | Δ |
|--------|---------------:|--------------------:|--:|
| median exp € | 2.0928 | 2.2860 | 0.1932 |
| panel net € | 83.6104 | 83.1242 | -0.4862 |
| median_trades | 7.0 | 7.0 | 0.0 |
| n exp>0 / 7 | 6 | 5 | -1 |
| soft promote | PASS | **PASS** | — |

---

## E. Cascade / Core+Mid book (PASS → Core+Mid only, no Scalp)

Bot cascade/arming path = **Core + Mid only**. Scalp = Kaje manual — **no Scalp sleeve**. Book start **€180** (Core €140 + Mid €40). Independent sleeve panel nets (same honesty as #55 pre-cascade sleeve sums).

- **book_id:** `rise_panel_v1_core_mid_book_180_mid_donchian20_10_4h`
- **book_start_eur:** **180**
- **core_id:** `rise_panel_v1_core_doge_ema12_30_1d_eur140` (1D EMA12/30)
- **mid_id:** `rise_panel_v1_mid_doge_donchian20_10_4h_eur40` (4H Donchian 20/10)
- **scalp:** none (`no_scalp=true`)
- per-sleeve panel net: Core **363.9983** · Mid **83.1242** · Core+Mid **447.1225** €

### Honesty Δ vs #55 Core+Mid portion

| Sleeve | #55 Core+Mid portion | #64 Core+Mid (this Mid) | Δ |
|--------|---------------------:|------------------------:|--:|
| Core | 363.9983 | 363.9983 | 0.0000 |
| Mid | 83.6104 | 83.1242 | -0.4862 |
| Core+Mid | 447.6087 | 447.1225 | -0.4862 |

Reports: `data/reports/rise_panel_v1_core_mid_book_mid_donchian_64.json`

---

## What this is not

- Not a Donchian-N / TF / cost grind.
- Not an EMA filter / period grind (Track A persist2 already softer).
- Not a change to R1–R7 window dates (phase1/54 lock).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.
- Not a Scalp sleeve (bot path Core+Mid only).
- Not a claim that past rise windows forecast the next bull.
- **Not better than Mid EMA baseline on panel_net** — do not promote-as-better.

`not_a_forecast: true`. `place_orders: false`.
