# 67 — rise_panel_v1 Mid: DOGE **4H EMA12/21** long/flat (€40)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Mid-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** NEW Mid formal baseline Breakout [`65-rise-panel-mid-breakoutv1-4h.md`](./65-rise-panel-mid-breakoutv1-4h.md) / promote [`65b-mid-breakout-promote.md`](./65b-mid-breakout-promote.md). EMA Mid 12/30 = archive only. Plain **EMA12/21** long/flat (NOT 12/30). **No** RSI. **No** daily-bull.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

**Honesty vs Breakout #65:** promote-as-better **only if** `panel_net` higher than ≈€95.45; else **PASS-but-worse** / **FAIL** clearly.

---

## A. LOCKED Mid baseline (NEW formal — Breakout #65)

**mid_baseline_id:** `rise_panel_v1_mid_doge_breakoutv1_4h_eur40`  
(soft_promote **PASS**, promoted #65 — see [`65b-mid-breakout-promote.md`](./65b-mid-breakout-promote.md))

- Rule: BreakoutV1 lookback 16 + ATR quiet; channel exit. Never short.
- Bar: DOGE-USDT **4H**. Sleeve: Mid **€40**.
- Compare target for this trial: **Mid vs Mid-Breakout-baseline** (NOT vs Core €140).
- Snapshot (#65): panel_net≈**€95.4483** · median_trades=**6.0** · exp>0 **5**/7.
- EMA Mid archive (`rise_panel_v1_mid_doge_ema12_30_4h_eur40`): panel_net≈**€83.6104** — **not** current Mid baseline (12/30, not this 12/21 trial).

### Mid Breakout baseline per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 4 | 4.8340 | 19.3359 | 15.9467 | 0.6377 | 30.7232 | 19.7678 |
| R2 | 5 | 3.9917 | 18.9947 | 15.4934 | 0.5269 | 18.5427 | 35.0187 |
| R3 | 8 | 2.6520 | 21.2157 | 19.8661 | 0.4278 | 24.3395 | 19.8179 |
| R4 | 6 | -0.3130 | 0.8810 | 9.1358 | 0.7326 | 12.2152 | 9.1820 |
| R5 | 6 | -1.2424 | 3.5761 | 19.2500 | 0.5659 | 16.1254 | 13.7988 |
| R6 | 7 | 2.0274 | 14.1917 | 22.2321 | 0.6014 | 14.0932 | 36.1697 |
| R7 | 7 | 2.4647 | 17.2531 | 7.0301 | 0.5259 | 25.4916 | 12.4650 |

**Panel summary (Mid Breakout baseline):**
- windows with exp>0: **5**/7 · net>0: **7**/7
- median expectancy €/trade: **2.4647**
- median_trades: **6.0**
- panel net €: **95.4483**
- worst DD €: **22.2321**
- soft_promote: **PASS** (`soft_promote_v1`)

---

## B. LOCKED Mid family (BEFORE scoring)

**ONE family only — NOT grinding EMA periods / TF / costs. No RSI. No daily-bull. Do not re-grind Breakout / RSI MR / Donchian / EMA12/30.**

**Family:** `ema12_21_long_flat_4h`  
**mid_improve_id:** `rise_panel_v1_mid_doge_ema12_21_4h_eur40`  
**compare_to:** `rise_panel_v1_mid_doge_breakoutv1_4h_eur40` (primary); optional archive `rise_panel_v1_mid_doge_ema12_30_4h_eur40`
**Canonical EMA (plain Mid 4H style):** EMA(**12**/**21**) long/flat. Decision bar **4H**. **No** RSI. **No** daily-bull.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- EMA: fast **12** / slow **21** (NOT 12/30).
- **Long:** closed-bar EMA fast > EMA slow. Long only.
- **Flat/exit:** closed-bar EMA fast ≤ EMA slow. Never short.
- **No** RSI filter. **No** daily-bull regime gate (distinct from Breakout #65, RSI MR #66, Donchian #64, EMA12/30 archive).
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Mid sleeve €40 when long.
- Costs: PaperSettings 5+5 bps.
- **No** EMA period / TF / cost grind on FAIL. **No** RSI / Breakout rescue.

### Why this family

NEW Mid formal baseline is BreakoutV1 4H (#65, panel≈€95.45). This trial ports plain **EMA12/21** (like Scalp #63 periods, Mid 4H TF) onto Mid €40 / locked rise panel — testing faster EMA twin vs Breakout without inventing RSI / Breakout knobs. Distinct from archived EMA12/30 Mid.

---

## C. Harness

- Script: `scripts/run_rise_panel_mid_ema1221_4h_eval.py`
- Module: `atlas.paper.rise_panel_mid_ema1221_4h_eval`
- Strategy: `atlas.strategy.mid_doge_ema1221_4h` (EmaTrendV1 wrapper; periods 12/21 locked)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; Core+Mid book €180 on PASS+better only (no Scalp)
- Unit tests: `tests/unit/test_rise_panel_mid_ema1221_4h.py`

---

## D. Results — Mid EMA12/21 4H €40 on same 7

**mid_improve_id:** `rise_panel_v1_mid_doge_ema12_21_4h_eur40`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 8 | 2.2032 | 18.0906 | 18.2874 | 0.5634 | 30.7232 | 19.7678 |
| R2 | 11 | -0.3268 | -1.2827 | 29.4283 | 0.5591 | 18.5427 | 35.0187 |
| R3 | 13 | 1.3682 | 17.7864 | 17.3076 | 0.4556 | 24.3395 | 19.8179 |
| R4 | 10 | 0.4137 | 7.5519 | 5.5967 | 0.5238 | 12.2152 | 9.1820 |
| R5 | 12 | -0.6806 | 3.5221 | 19.1120 | 0.4927 | 16.1254 | 13.7988 |
| R6 | 9 | 1.1316 | 10.1845 | 25.9198 | 0.5761 | 14.0932 | 36.1697 |
| R7 | 9 | 1.6074 | 14.4669 | 8.4857 | 0.5741 | 25.4916 | 12.4650 |

**Panel summary (Mid EMA12/21 4H):**
- windows with exp>0: **5**/7 · net>0: **6**/7
- median expectancy €/trade: **1.1316**
- median_trades: **10.0**
- panel net €: **70.3198**
- worst DD €: **29.4283**

### Soft promote (Mid EMA12/21): **PASS** (`soft_promote_v1`)

- median_trades=10.0 (ok=True, min>=1)
- exp>0: 5/7 (need ≥5; ok=True)
- panel_net €=70.3198 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs Breakout #65: **PASS-but-worse**

### Honesty deltas vs Mid Breakout #65 baseline (EMA12/21 − Breakout)

| Metric | Mid Breakout 4H €40 (#65) | Mid EMA12/21 4H €40 | Δ |
|--------|--------------------------:|--------------------:|--:|
| median exp € | 2.4647 | 1.1316 | -1.3331 |
| panel net € | 95.4483 | 70.3198 | -25.1285 |
| median_trades | 6.0 | 10.0 | 4.0 |
| n exp>0 / 7 | 5 | 5 | 0 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs EMA12/30 Mid archive (optional; EMA12/21 − EMA12/30)

| Metric | Mid EMA12/30 4H €40 (archive) | Mid EMA12/21 4H €40 | Δ |
|--------|------------------------------:|--------------------:|--:|
| median exp € | 2.0928 | 1.1316 | -0.9612 |
| panel net € | 83.6104 | 70.3198 | -13.2906 |
| median_trades | 7.0 | 10.0 | 3.0 |
| n exp>0 / 7 | 6 | 5 | -1 |
| soft promote | PASS (archive) | **PASS** | — |

---

## E. Cascade / Core+Mid book

**No promote claim.** Soft PASS-but-worse vs Breakout — cascade skipped (optional informational only; not run as promote path).

---

## What this is not

- Not an EMA period / TF / cost grind (12/21 locked; not 12/30).
- Not RSI MR (#66) or RSI filter.
- Not BreakoutV1 (#65) or Donchian 20/10 (#64).
- Not Mid EMA12/30 archive (different periods).
- Not Scalp #63 1H EMA12/21 (this is Mid 4H).
- Not a change to R1–R7 window dates (phase1/54 lock).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.
- Not a Scalp sleeve (bot path Core+Mid only).
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
