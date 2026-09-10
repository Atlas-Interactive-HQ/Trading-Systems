# 68 — rise_panel_v1 Mid: DOGE **4H MACD(12,26,9)** long/flat (€40)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Mid-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** NEW Mid formal baseline Breakout [`65-rise-panel-mid-breakoutv1-4h.md`](./65-rise-panel-mid-breakoutv1-4h.md) / promote [`65b-mid-breakout-promote.md`](./65b-mid-breakout-promote.md). EMA Mid 12/30 = archive only. Canonical **MACD(12,26,9)** cross long/flat. **No** RSI. **No** daily-bull. **No** EMA grind.

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
- EMA Mid archive (`rise_panel_v1_mid_doge_ema12_30_4h_eur40`): panel_net≈**€83.6104** — **not** current Mid baseline (archive EMA12/30; this trial is MACD).

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

**ONE family only — NOT grinding MACD periods / TF / costs. No RSI. No daily-bull. Do not re-grind Breakout / RSI MR / Donchian / EMA12/21 / EMA12/30.**

**Family:** `macd12269_long_flat_4h`  
**mid_improve_id:** `rise_panel_v1_mid_doge_macd12269_4h_eur40`  
**compare_to:** `rise_panel_v1_mid_doge_breakoutv1_4h_eur40` (primary); optional archive `rise_panel_v1_mid_doge_ema12_30_4h_eur40`
**Canonical MACD (paper rule):** MACD(**12**,**26**,**9**) cross long/flat. Decision bar **4H**. **No** RSI. **No** daily-bull.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- MACD: fast **12** / slow **26** / signal **9**.
- **Long:** closed-bar MACD line crosses *above* signal. Long only.
- **Flat/exit:** closed-bar MACD line crosses *below* signal. Never short.
- **No** RSI filter. **No** daily-bull regime gate (distinct from Breakout #65, EMA12/21 #67, RSI MR #66, Donchian #64, EMA12/30 archive).
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Mid sleeve €40 when long.
- Costs: PaperSettings 5+5 bps.
- **No** MACD period / TF / cost grind on FAIL. **No** RSI / Breakout / EMA rescue.

### Why this family

NEW Mid formal baseline is BreakoutV1 4H (#65, panel≈€95.45). No prior Mid/Scalp MACD module in-repo — this trial locks canonical **MACD(12,26,9)** cross long/flat onto Mid €40 / locked rise panel — testing MACD vs Breakout without inventing RSI / Breakout / EMA knobs.

---

## C. Harness

- Script: `scripts/run_rise_panel_mid_macd_4h_eval.py`
- Module: `atlas.paper.rise_panel_mid_macd_4h_eval`
- Strategy: `atlas.strategy.mid_doge_macd_4h` (MacdTrendV1 wrapper; MACD 12/26/9 locked)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; Core+Mid book €180 on PASS+better only (no Scalp)
- Unit tests: `tests/unit/test_rise_panel_mid_macd_4h.py`

---

## D. Results — Mid MACD(12,26,9) 4H €40 on same 7

**mid_improve_id:** `rise_panel_v1_mid_doge_macd12269_4h_eur40`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 18 | 0.4995 | 9.1945 | 9.7007 | 0.5380 | 30.7232 | 19.7678 |
| R2 | 23 | 0.2776 | 5.8545 | 11.4654 | 0.5412 | 18.5427 | 35.0187 |
| R3 | 21 | 1.2348 | 25.9315 | 11.7392 | 0.5593 | 24.3395 | 19.8179 |
| R4 | 23 | 0.0778 | 3.5155 | 5.0767 | 0.5201 | 12.2152 | 9.1820 |
| R5 | 30 | -0.3361 | -0.5047 | 14.8735 | 0.5128 | 16.1254 | 13.7988 |
| R6 | 26 | 0.1056 | 2.7455 | 24.7647 | 0.4638 | 14.0932 | 36.1697 |
| R7 | 19 | 1.3723 | 26.0113 | 8.6329 | 0.5407 | 25.4916 | 12.4650 |

**Panel summary (Mid MACD 4H):**
- windows with exp>0: **6**/7 · net>0: **6**/7
- median expectancy €/trade: **0.2776**
- median_trades: **23.0**
- panel net €: **72.7480**
- worst DD €: **24.7647**

### Soft promote (Mid MACD): **PASS** (`soft_promote_v1`)

- median_trades=23.0 (ok=True, min>=1)
- exp>0: 6/7 (need ≥5; ok=True)
- panel_net €=72.7480 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs Breakout #65: **PASS-but-worse**

### Honesty deltas vs Mid Breakout #65 baseline (MACD − Breakout)

| Metric | Mid Breakout 4H €40 (#65) | Mid MACD(12,26,9) 4H €40 | Δ |
|--------|--------------------------:|--------------------:|--:|
| median exp € | 2.4647 | 0.2776 | -2.1871 |
| panel net € | 95.4483 | 72.7480 | -22.7003 |
| median_trades | 6.0 | 23.0 | 17.0 |
| n exp>0 / 7 | 5 | 6 | 1 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs EMA12/30 Mid archive (optional; MACD − EMA12/30)

| Metric | Mid EMA12/30 4H €40 (archive) | Mid MACD(12,26,9) 4H €40 | Δ |
|--------|------------------------------:|--------------------:|--:|
| median exp € | 2.0928 | 0.2776 | -1.8152 |
| panel net € | 83.6104 | 72.7480 | -10.8624 |
| median_trades | 7.0 | 23.0 | 16.0 |
| n exp>0 / 7 | 6 | 6 | 0 |
| soft promote | PASS (archive) | **PASS** | — |

---

## E. Cascade / Core+Mid book

**No promote claim.** Soft PASS-but-worse vs Breakout — cascade skipped (optional informational only; not run as promote path).

---

## What this is not

- Not a MACD period / TF / cost grind (12/26/9 locked).
- Not EMA12/21 (#67) or EMA12/30 archive.
- Not RSI MR (#66) or RSI filter.
- Not BreakoutV1 (#65) or Donchian 20/10 (#64).
- Not Scalp (this is Mid 4H; Scalp = Kaje manual).
- Not a change to R1–R7 window dates (phase1/54 lock).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.
- Not a Scalp sleeve (bot path Core+Mid only).
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
