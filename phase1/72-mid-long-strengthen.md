# 72 — Mid #71 long-strengthen: DOGE **4H BreakoutV1 + EMA12/21** (€40)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Mid-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** Mid Breakout baseline [`65-rise-panel-mid-breakoutv1-4h.md`](./65-rise-panel-mid-breakoutv1-4h.md). Gate soft_promote_v1 vs #65. BreakoutV1 **+ EMA12/21 long-regime filter**. **No** RSI. **No** size-up. Research Mid **#71**; doc file **72** (avoid clash with Codex HFT brief).

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

**Honesty vs Breakout #65:** promote-as-better **only if** `panel_net` higher than ≈€95.45; else **PASS-but-worse** / **FAIL** clearly.

---

## A. LOCKED Mid baseline (Breakout #65 — compare target)

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

**ONE family only — NOT grinding lookback / EMA / ATR / TF / costs. No RSI. No size-up. Do not re-grind plain Breakout / EMA12/21 / RSI MR / Donchian.**

**Family:** `breakout_v1_ema1221_long_regime_4h`  
**mid_improve_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40`  
**compare_to:** `rise_panel_v1_mid_doge_breakoutv1_4h_eur40` (primary); optional archive `rise_panel_v1_mid_doge_ema12_30_4h_eur40`
**Canonical:** BreakoutV1 lookback **16** + ATR quiet, gated by EMA(**12**/**21**). Decision bar **4H**. **No** RSI. Same Mid €40 as #65.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- BreakoutV1: lookback **16**, ATR SMA **14**, min_atr_frac **0.001** (same as #65).
- EMA long-regime: fast **12** / slow **21** (NOT 12/30).
- **Long entry:** BreakoutV1 break-up + ATR quiet **AND** EMA12 > EMA21. Long only.
- **Flat/exit:** BreakoutV1 channel exit **OR** EMA12 ≤ EMA21 (force flat / no new long). Never short.
- **No** RSI. **No** size-up (Mid €40 same as #65). Distinct from plain Breakout #65, plain EMA12/21 #67, RSI MR #66.
- `oneh_filter: off` (decision TF is already 4H).
- Insufficient history → flat. Quiet ATR → no new long.
- Fill: signal close → next open. Size: full Mid sleeve €40 when long.
- Costs: PaperSettings 5+5 bps.
- **No** lookback / EMA / ATR / TF / cost grind on FAIL. **No** RSI rescue.

### Why this family

Mid #65 BreakoutV1 4H is the formal Mid baseline (panel≈€95.45, already L/F). This trial **strengthens long bias quality** with an EMA12/21 long-regime filter — not a size-up, not RSI. Same €40 sleeve for clean Δ vs #65.

---

## C. Harness

- Script: `scripts/run_rise_panel_mid_breakout_ema1221_4h_eval.py`
- Module: `atlas.paper.rise_panel_mid_breakout_ema1221_4h_eval`
- Strategy: `atlas.strategy.mid_doge_breakout_ema1221_4h` (BreakoutV1 + EMA12/21 long-regime; Mid #71)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; Core+Mid book €180 on PASS+better only (no Scalp)
- Unit tests: `tests/unit/test_rise_panel_mid_breakout_ema1221_4h.py`
- Doc path: `phase1/72-mid-long-strengthen.md` (Mid lock #71; avoid clash with `71-codex-scalp-hft-design-brief.md`)

---

## D. Results — Mid BreakoutV1 + EMA12/21 4H €40 on same 7

**mid_improve_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 4 | 5.9898 | 23.9590 | 15.7249 | 0.4583 | 30.7232 | 19.7678 |
| R2 | 7 | 0.9778 | 6.0916 | 18.3218 | 0.4659 | 18.5427 | 35.0187 |
| R3 | 6 | 4.5693 | 27.4157 | 14.7537 | 0.2944 | 24.3395 | 19.8179 |
| R4 | 8 | -0.0323 | 1.9067 | 7.9935 | 0.4304 | 12.2152 | 9.1820 |
| R5 | 7 | -0.8389 | 6.6592 | 16.5075 | 0.3919 | 16.1254 | 13.7988 |
| R6 | 7 | 2.3090 | 16.1628 | 21.8963 | 0.4710 | 14.0932 | 36.1697 |
| R7 | 7 | 2.1531 | 15.0714 | 7.1590 | 0.4556 | 25.4916 | 12.4650 |

**Panel summary (Mid Breakout + EMA12/21 4H):**
- windows with exp>0: **5**/7 · net>0: **7**/7
- median expectancy €/trade: **2.1531**
- median_trades: **7.0**
- panel net €: **97.2663**
- worst DD €: **21.8963**

### Soft promote (Mid Breakout + EMA12/21): **PASS** (`soft_promote_v1`)

- median_trades=7.0 (ok=True, min>=1)
- exp>0: 5/7 (need ≥5; ok=True)
- panel_net €=97.2663 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs Breakout #65: **PASS-and-better (promote-as-better eligible)**

### Honesty deltas vs Mid Breakout #65 baseline (Breakout+EMA1221 − Breakout)

| Metric | Mid Breakout 4H €40 (#65) | Mid Breakout+EMA1221 4H €40 | Δ |
|--------|--------------------------:|--------------------:|--:|
| median exp € | 2.4647 | 2.1531 | -0.3117 |
| panel net € | 95.4483 | 97.2663 | 1.8180 |
| median_trades | 6.0 | 7.0 | 1.0 |
| n exp>0 / 7 | 5 | 5 | 0 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs EMA12/30 Mid archive (optional; Breakout+EMA1221 − EMA12/30)

| Metric | Mid EMA12/30 4H €40 (archive) | Mid Breakout+EMA1221 4H €40 | Δ |
|--------|------------------------------:|--------------------:|--:|
| median exp € | 2.0928 | 2.1531 | 0.0603 |
| panel net € | 83.6104 | 97.2663 | 13.6559 |
| median_trades | 7.0 | 7.0 | 0.0 |
| n exp>0 / 7 | 6 | 5 | -1 |
| soft promote | PASS (archive) | **PASS** | — |

---

## E. Cascade / Core+Mid book

Bot cascade/arming path = **Core + Mid only**. Scalp = Kaje manual — **no Scalp sleeve**. Book start **€180** (Core €140 + Mid €40). PASS **and** panel_net better than Breakout → cascade recorded.

- **book_id:** `rise_panel_v1_core_mid_book_180_mid_breakout_ema1221_4h`
- **book_start_eur:** **180**
- **core_id:** `rise_panel_v1_core_doge_ema12_30_1d_eur140` (1D EMA12/30)
- **mid_id:** `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40` (4H Breakout+EMA1221)
- **scalp:** none (`no_scalp=true`)
- per-sleeve panel net: Core **363.9983** · Mid **97.2663** · Core+Mid **461.2647** €

### Honesty Δ vs Breakout Core+Mid (#65)

| Sleeve | #65 Core+Mid (Breakout Mid) | #71 Core+Mid (this Mid) | Δ |
|--------|----------------------------:|------------------------:|--:|
| Core | 363.9983 | 363.9983 | 0.0000 |
| Mid | 95.4483 | 97.2663 | 1.8180 |
| Core+Mid | 459.4466 | 461.2647 | 1.8181 |

Reports: `data/reports/rise_panel_v1_core_mid_book_mid_breakout_ema1221_71.json`

---

## What this is not

- Not a lookback / EMA / ATR / TF / cost grind.
- Not RSI MR (#66) or RSI filter.
- Not plain BreakoutV1 alone (#65) — this adds EMA12/21 regime.
- Not plain Mid EMA12/21 (#67) — Breakout stays the signal.
- Not Donchian 20/10 (#64) or Mid EMA12/30 archive.
- Not a size-up / risk-up of the Mid €40 sleeve.
- Not Scalp HFT / Codex lane (do not implement HFT).
- Not a change to R1–R7 window dates (phase1/54 lock).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.
- Not a Scalp sleeve (bot path Core+Mid only).
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
