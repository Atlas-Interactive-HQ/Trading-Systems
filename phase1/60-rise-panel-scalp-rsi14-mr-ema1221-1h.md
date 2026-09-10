# 60 — rise_panel_v1 Scalp: DOGE **1H RSI(14) MR ∩ EMA12/21** long/flat (€20)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. Soft PASS ≠ Scalp-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md); Scalp 4H [`57-rise-panel-scalp-improve-4h-ema.md`](./57-rise-panel-scalp-improve-4h-ema.md); Scalp RSI MR [`59-rise-panel-scalp-rsi14-mr-1h.md`](./59-rise-panel-scalp-rsi14-mr-1h.md); Scalp 15m [`58-rise-panel-scalp-improve-15m-ema.md`](./58-rise-panel-scalp-improve-15m-ema.md). **Combined** RSI∩EMA12/21 (not sequential trials).

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

---

## A. LOCKED compare targets

**scalp_provisional_id (#55):** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`  
(soft_promote **FAIL** — provisional stand-in)

- Rule: 1H EMA12/30 long/flat + daily EMA bull entry gate. Never short.
- Bar: DOGE-USDT **1H**. Sleeve: Scalp **€20**.
- #55 snapshot (reported): exp>0 **4**/7 · median_trades=**18** · panel_net≈**€44.70**.

**scalp_4h_id (#57):** `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`  
(soft_promote **PASS** — EMA12/30 long/flat on **4H**)

- #57 snapshot (reported): exp>0 **6**/7 · median_trades=**7** · panel_net≈**€41.81** · median exp≈**€1.05**.

**scalp_rsi_mr_id (#59):** `rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20`  
(soft_promote **PASS** — RSI(14) MR long/flat on **1H**, no EMA)

- #59 snapshot (reported): exp>0 **5**/7 · median_trades=**7** · panel_net≈**€18.24** · cascade≈**€465.85**.

**scalp_15m_id (#58):** `rise_panel_v1_scalp_doge_ema12_30_15m_eur20`  
(soft_promote **FAIL** — EMA12/30 long/flat on **15m**)

- #58 snapshot (reported): exp>0 **1**/7 · median_trades=**161** · panel_net≈**−€32.48**.

### Provisional Scalp per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 18 | 0.6561 | 13.0156 | 5.0107 | 0.3528 | 15.3616 | 10.6267 |
| R2 | 12 | -0.0154 | 0.1815 | 3.2508 | 0.2074 | 9.2713 | 17.5480 |
| R3 | 10 | 1.7603 | 17.6026 | 7.8428 | 0.1806 | 12.1697 | 13.4725 |
| R4 | 16 | -0.0063 | 0.7810 | 3.1150 | 0.2527 | 6.1076 | 4.9136 |
| R5 | 21 | -0.1132 | 3.6889 | 7.0512 | 0.2976 | 8.0627 | 6.9305 |
| R6 | 22 | 0.2048 | 4.5066 | 10.2683 | 0.3284 | 7.0466 | 18.0849 |
| R7 | 18 | 0.2558 | 4.9258 | 3.2967 | 0.2977 | 12.7458 | 7.0240 |

**Panel summary (provisional Scalp re-score):**
- windows with exp>0: **4**/7 · net>0: **7**/7
- median expectancy €/trade: **0.2048**
- median_trades: **18.0**
- panel net €: **44.7022**
- worst DD €: **10.2683**
- soft_promote: **FAIL** (`soft_promote_v1`)

---

## B. LOCKED Scalp family (BEFORE scoring)

**ONE combined family only — NOT sequential #59 then EMA; NOT grinding RSI/EMA periods / thresholds / TF / costs.**

**Family:** `rsi14_mr_ema1221_long_flat_1h`  
**scalp_improve_id:** `rise_panel_v1_scalp_doge_rsi14_mr_ema1221_1h_eur20`  
**compare_to:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20`, `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`, `rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20`, `rise_panel_v1_scalp_doge_ema12_30_15m_eur20`
**Combined rule:** RSI(14) MR entry (#59 spirit) **AND** EMA12>21; exit RSI≥70 **OR** EMA12<21. EMA periods **12/21** (not 12/30).

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.
- RSI: Wilder **RSI(14)**.
- EMA: **EMA12 / EMA21** (locked — not 12/30).
- **Long:** closed-bar RSI crosses up from ≤30 (prev ≤30 and curr >30) **AND** EMA12 > EMA21. Long only.
- **Flat/exit:** closed-bar RSI ≥70 **OR** EMA12 < EMA21. Never short.
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Scalp sleeve €20 when long.
- Costs: PaperSettings 5+5 bps.
- **No** Donchian / ATR / daily-bull rescue knobs this trial. **No** RSI/EMA period / threshold / TF / cost grind on FAIL.

### Why this family

Provisional Scalp 1H+daily-bull (#55) soft FAIL (exp>0 4/7). Scalp #57 4H EMA soft PASS; Scalp #58 15m EMA soft FAIL; Scalp #59 RSI-only 1H soft PASS (panel≈€18.24). This trial tests **one combined** RSI∩EMA12/21 system on the same locked rise panel / Scalp €20 / 1H bar — whether an EMA12/21 trend filter tightens #59 MR without inventing knobs.

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_rsi_ema1221_1h_eval.py`
- Module: `atlas.paper.rise_panel_scalp_rsi_ema1221_1h_eval`
- Strategy: `atlas.strategy.scalp_doge_rsi_ema1221_1h` (reuses `rsi_wilder` + `ema_series`)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, cascade compound (#55 rules) on PASS only; patterns from #59/#57
- Unit tests: `tests/unit/test_rise_panel_scalp_rsi_ema1221_1h.py`

---

## D. Results — Scalp RSI∩EMA12/21 1H €20 on same 7

**scalp_improve_id:** `rise_panel_v1_scalp_doge_rsi14_mr_ema1221_1h_eur20`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 0 | — | 0.0000 | 0.0000 | 0.0000 | 15.3616 | 10.6267 |
| R2 | 0 | — | 0.0000 | 0.0000 | 0.0000 | 9.2713 | 17.5480 |
| R3 | 0 | — | 0.0000 | 0.0000 | 0.0000 | 12.1697 | 13.4725 |
| R4 | 0 | — | 0.0000 | 0.0000 | 0.0000 | 6.1076 | 4.9136 |
| R5 | 0 | — | 0.0000 | 0.0000 | 0.0000 | 8.0627 | 6.9305 |
| R6 | 0 | — | 0.0000 | 0.0000 | 0.0000 | 7.0466 | 18.0849 |
| R7 | 0 | — | 0.0000 | 0.0000 | 0.0000 | 12.7458 | 7.0240 |

**Panel summary (Scalp RSI∩EMA12/21 1H):**
- windows with exp>0: **0**/7 · net>0: **0**/7
- median expectancy €/trade: **—**
- median_trades: **0.0**
- panel net €: **0.0000**
- worst DD €: **0.0000**

### Soft promote (Scalp RSI∩EMA12/21): **FAIL** (`soft_promote_v1`)

- median_trades=0.0 (ok=False, min>=1)
- exp>0: 0/7 (need ≥5; ok=False)
- panel_net €=0.0000 (ok=False)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs provisional Scalp #55 (RSI∩EMA − provisional)

| Metric | Provisional 1H €20 | Scalp RSI∩EMA 1H €20 | Δ |
|--------|------------------:|--------------------:|--:|
| median exp € | 0.2048 | — | — |
| panel net € | 44.7022 | 0.0000 | -44.7022 |
| median_trades | 18.0 | 0.0 | -18.0 |
| n exp>0 / 7 | 4 | 0 | -4 |
| soft promote | FAIL | **FAIL** | — |

### Honesty deltas vs Scalp #57 4H (RSI∩EMA − 4H)

| Metric | Scalp 4H €20 (#57) | Scalp RSI∩EMA 1H €20 | Δ |
|--------|------------------:|--------------------:|--:|
| median exp € | 1.0464 | — | — |
| panel net € | 41.8052 | 0.0000 | -41.8052 |
| median_trades | 7.0 | 0.0 | -7.0 |
| n exp>0 / 7 | 6 | 0 | -6 |
| soft promote | PASS | **FAIL** | — |

### Honesty deltas vs Scalp #59 RSI-only (RSI∩EMA − RSI MR)

| Metric | Scalp RSI MR 1H (#59) | Scalp RSI∩EMA 1H €20 | Δ |
|--------|---------------------:|--------------------:|--:|
| median exp € | 0.5128 | — | — |
| panel net € | 18.2424 | 0.0000 | -18.2424 |
| median_trades | 7.0 | 0.0 | -7.0 |
| n exp>0 / 7 | 5 | 0 | -5 |
| soft promote | PASS | **FAIL** | — |

### Honesty deltas vs Scalp #58 15m (RSI∩EMA − 15m)

| Metric | Scalp 15m €20 (#58) | Scalp RSI∩EMA 1H €20 | Δ |
|--------|-------------------:|--------------------:|--:|
| median exp € | -0.0317 | — | — |
| panel net € | -32.4822 | 0.0000 | 32.4822 |
| median_trades | 161.0 | 0.0 | -161.0 |
| n exp>0 / 7 | 1 | 0 | -1 |
| soft promote | FAIL | **FAIL** | — |

---

## E. Archive (soft_promote FAIL → no grind / no next-family auto)

No RSI/EMA period / threshold / TF / cost grind. No automatic next-family start. Archive this candidate. Parent will ping coordinator for the next family.

### Structural note (honest, not a rescue)

On locked R1–R7 DOGE-USDT **1H**, RSI(14) cross-up from ≤30 **never** co-occurred with EMA12 > EMA21 (counts: R1–R7 cross+ema_bull = **0/0/0/0/0/0/0**). Oversold RSI cross-ups arrive while the short EMA is still below EMA21, so the **combined** AND-entry is empty → **0 trades / 7**. Soft FAIL is therefore structural for this locked rule card on this panel — not a coding miss. Do **not** grind periods / thresholds / TF to invent trades.

**Cascade:** not run (`provisional_scalp` N/A; soft FAIL). No Δ vs #55 €492.31 / #57 €489.41 / #59 €465.85.

Reports: `data/reports/rise_panel_v1_scalp_rsi14_mr_ema1221_1h_60.json` + deltas_vs{55,57,58,59}.

---

## What this is not

- Not an EMA 12/30 twin / period grind (locked **12/21**).
- Not sequential #59 then EMA — one combined system.
- Not a change to R1–R7 window dates.
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Scalp-arming. Soft PASS ≠ Scalp-arm. Live ≤€20.
- Not a claim that past rise windows forecast the next bull.
- Mid 4H stays Mid baseline.

`not_a_forecast: true`. `place_orders: false`.
