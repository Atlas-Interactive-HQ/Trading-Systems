# 66 — rise_panel_v1 Mid: DOGE **4H RSI(14) MR** long/flat (€40)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Mid-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** NEW Mid formal baseline Breakout [`65-rise-panel-mid-breakoutv1-4h.md`](./65-rise-panel-mid-breakoutv1-4h.md) / promote [`65b-mid-breakout-promote.md`](./65b-mid-breakout-promote.md). EMA Mid = archive only. **Same entry/exit style as Scalp #59** (cross-up ≤30 / exit ≥70); **no** EMA.

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
- EMA Mid archive (`rise_panel_v1_mid_doge_ema12_30_4h_eur40`): panel_net≈**€83.6104** — **not** current Mid baseline.

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

**ONE family only — NOT grinding RSI period / thresholds / TF / costs. No EMA filter. Do not re-grind Breakout / EMA / Donchian.**

**Family:** `rsi14_mr_long_flat_4h`  
**mid_improve_id:** `rise_panel_v1_mid_doge_rsi14_mr_4h_eur40`  
**compare_to:** `rise_panel_v1_mid_doge_breakoutv1_4h_eur40` (primary); optional archive `rise_panel_v1_mid_doge_ema12_30_4h_eur40`
**Canonical RSI MR (Scalp #59 style):** Wilder RSI(**14**); long on cross-up from ≤30; flat when RSI≥70. Decision bar **4H**. **No** EMA filter.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.
- RSI: Wilder **RSI(14)**.
- **Long:** closed-bar RSI crosses up from ≤30 (prev ≤30 and curr >30). Long only.
- **Flat/exit:** closed-bar RSI ≥70. Never short.
- **No** EMA filter / regime gate (distinct from Breakout #65, EMA archive, Donchian #64).
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Mid sleeve €40 when long.
- Costs: PaperSettings 5+5 bps.
- **No** RSI period / threshold / TF / cost grind on FAIL. **No** EMA / Breakout rescue.

### Why this family

NEW Mid formal baseline is BreakoutV1 4H (#65, panel≈€95.45). This trial ports **Scalp #59 RSI(14) MR** entry/exit onto Mid €40 / locked rise panel / **4H** — testing mean-reversion without inventing EMA / Breakout knobs.

---

## C. Harness

- Script: `scripts/run_rise_panel_mid_rsi_mr_4h_eval.py`
- Module: `atlas.paper.rise_panel_mid_rsi_mr_4h_eval`
- Strategy: `atlas.strategy.mid_doge_rsi_mr_4h` (reuses `rsi_wilder` from `mid_doge_rsi_mr`; Scalp #59 cross-up/exit style)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; Core+Mid book €180 on PASS+better only (no Scalp)
- Unit tests: `tests/unit/test_rise_panel_mid_rsi_mr_4h.py`

---

## D. Results — Mid RSI(14) MR 4H €40 on same 7

**mid_improve_id:** `rise_panel_v1_mid_doge_rsi14_mr_4h_eur40`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 3 | 3.1405 | 9.4216 | 2.1817 | 0.3804 | 30.7232 | 19.7678 |
| R2 | 3 | 3.6010 | 10.8030 | 13.7785 | 0.3835 | 18.5427 | 35.0187 |
| R3 | 2 | 0.1220 | 0.2440 | 8.2977 | 0.5481 | 24.3395 | 19.8179 |
| R4 | 1 | -0.4802 | -0.4802 | 3.7808 | 0.4432 | 12.2152 | 9.1820 |
| R5 | 1 | 1.6531 | 1.6531 | 4.0397 | 0.1795 | 16.1254 | 13.7988 |
| R6 | 2 | 6.7690 | 13.5380 | 18.1113 | 0.3569 | 14.0932 | 36.1697 |
| R7 | 2 | 4.0656 | 8.1312 | 5.1511 | 0.3241 | 25.4916 | 12.4650 |

**Panel summary (Mid RSI MR 4H):**
- windows with exp>0: **6**/7 · net>0: **6**/7
- median expectancy €/trade: **3.1405**
- median_trades: **2.0**
- panel net €: **43.3106**
- worst DD €: **18.1113**

### Soft promote (Mid RSI MR): **PASS** (`soft_promote_v1`)

- median_trades=2.0 (ok=True, min>=1)
- exp>0: 6/7 (need ≥5; ok=True)
- panel_net €=43.3106 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty label vs Breakout #65: **PASS-but-worse**

### Honesty deltas vs Mid Breakout #65 baseline (RSI MR − Breakout)

| Metric | Mid Breakout 4H €40 (#65) | Mid RSI MR 4H €40 | Δ |
|--------|--------------------------:|------------------:|--:|
| median exp € | 2.4647 | 3.1405 | 0.6758 |
| panel net € | 95.4483 | 43.3106 | -52.1377 |
| median_trades | 6.0 | 2.0 | -4.0 |
| n exp>0 / 7 | 5 | 6 | 1 |
| soft promote | PASS | **PASS** | — |

### Honesty deltas vs EMA Mid archive (optional; RSI MR − EMA)

| Metric | Mid EMA 4H €40 (archive) | Mid RSI MR 4H €40 | Δ |
|--------|-------------------------:|------------------:|--:|
| median exp € | 2.0928 | 3.1405 | 1.0477 |
| panel net € | 83.6104 | 43.3106 | -40.2998 |
| median_trades | 7.0 | 2.0 | -5.0 |
| n exp>0 / 7 | 6 | 6 | 0 |
| soft promote | PASS (archive) | **PASS** | — |

---

## E. Cascade / Core+Mid book

**No promote claim.** Soft PASS-but-worse vs Breakout — cascade skipped (optional informational only; not run as promote path).

---

## What this is not

- Not an RSI period / threshold / TF / cost grind.
- Not an EMA filter / period grind (EMA Mid is archive only).
- Not BreakoutV1 (#65) or Donchian 20/10 (#64).
- Not Mid #43 1D level-entry RSI (this is Scalp #59 cross-up / exit≥70 on 4H).
- Not a change to R1–R7 window dates (phase1/54 lock).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.
- Not a Scalp sleeve (bot path Core+Mid only).
- Not a claim that past rise windows forecast the next bull.

`not_a_forecast: true`. `place_orders: false`.
