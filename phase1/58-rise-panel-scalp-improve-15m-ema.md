# 58 — rise_panel_v1 Scalp improvement: DOGE **15m EMA12/30** long/flat (€20)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. Soft PASS ≠ Scalp-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md); Scalp 4H [`57-rise-panel-scalp-improve-4h-ema.md`](./57-rise-panel-scalp-improve-4h-ema.md). Mid 4H stays Mid baseline.

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
(soft_promote **PASS** — same EMA12/30 long/flat family on **4H**)

- #57 snapshot (reported): exp>0 **6**/7 · median_trades=**7** · panel_net≈**€41.81** · median exp≈**€1.05**.

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

## B. LOCKED improvement family (BEFORE scoring)

**ONE family only — NOT grinding EMA 12/30 periods.**

**Family:** `ema12_30_long_flat_15m`  
**scalp_improve_id:** `rise_panel_v1_scalp_doge_ema12_30_15m_eur20`  
**compare_to:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20` and `rise_panel_v1_scalp_doge_ema12_30_4h_eur20`
**Same family as Mid baseline / Scalp #57:** EMA12/30 long/flat, Scalp **€20**, decision bar **15m** (not Mid €40; not 4H).

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **15m**.
- EMA periods: **fast=12, slow=30** (same as Mid baseline / #57 — no period grind).
- **Long/flat:** closed-bar EMA12 > EMA30 → long; else flat. Never short.
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Scalp sleeve €20 when long.
- Costs: PaperSettings 5+5 bps.
- **No** Donchian / ATR / RSI rescue knobs this trial. **No** EMA period / TF / cost grind on FAIL.

### Why this family

Provisional Scalp 1H+daily-bull failed soft_promote (exp>0 4/7). Scalp #57 4H plain EMA12/30 soft_promote PASS on the same locked rise panel. Porting the same EMA12/30 long/flat family to Scalp €20 on **15m** tests whether a faster bar lifts turnover while keeping ≥5/7 exp>0 — without inventing a new rule card.

---

## C. Harness

- Script: `scripts/run_rise_panel_scalp_improve_15m_eval.py`
- Module: `atlas.paper.rise_panel_scalp_improve_15m_eval`
- Strategy: `atlas.strategy.scalp_doge_ema_15m` (thin Scalp wrapper around `EmaTrendV1`)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, cascade compound (#55 rules) on PASS; patterns from #57 `rise_panel_scalp_improve_eval`
- Unit tests: `tests/unit/test_rise_panel_scalp_improve_15m.py`

---

## D. Results — Scalp improve (15m EMA12/30 €20) on same 7

**scalp_improve_id:** `rise_panel_v1_scalp_doge_ema12_30_15m_eur20`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 184 | -0.0465 | -8.5018 | 9.4278 | 0.5546 | 15.3616 | 12.9006 |
| R2 | 164 | -0.0588 | -9.2830 | 16.3447 | 0.4951 | 9.2713 | 17.7829 |
| R3 | 170 | -0.0317 | -5.3822 | 12.9469 | 0.5188 | 12.1697 | 13.9935 |
| R4 | 146 | -0.0524 | -7.3435 | 7.9301 | 0.5294 | 6.1076 | 4.9136 |
| R5 | 161 | -0.0048 | -0.7688 | 10.3797 | 0.5165 | 8.0627 | 7.4692 |
| R6 | 143 | -0.0131 | -1.9244 | 13.1610 | 0.4954 | 7.0466 | 18.1087 |
| R7 | 146 | 0.0046 | 0.7214 | 5.6636 | 0.5517 | 12.7458 | 7.4342 |

**Panel summary (Scalp improve 15m):**
- windows with exp>0: **1**/7 · net>0: **1**/7
- median expectancy €/trade: **-0.0317**
- median_trades: **161.0**
- panel net €: **-32.4822**
- worst DD €: **16.3447**

### Soft promote (Scalp improve): **FAIL** (`soft_promote_v1`)

- median_trades=161.0 (ok=True, min>=1)
- exp>0: 1/7 (need ≥5; ok=False)
- panel_net €=-32.4822 (ok=False)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs provisional Scalp #55 (15m − provisional)

| Metric | Provisional 1H €20 | Scalp 15m €20 | Δ |
|--------|-------------------:|--------------:|--:|
| median exp € | 0.2048 | -0.0317 | -0.2365 |
| panel net € | 44.7022 | -32.4822 | -77.1844 |
| median_trades | 18.0 | 161.0 | 143.0 |
| n exp>0 / 7 | 4 | 1 | -3 |
| soft promote | FAIL | **FAIL** | — |

### Honesty deltas vs Scalp #57 4H (15m − 4H)

| Metric | Scalp 4H €20 (#57) | Scalp 15m €20 | Δ |
|--------|-------------------:|--------------:|--:|
| median exp € | 1.0464 | -0.0317 | -1.0781 |
| panel net € | 41.8052 | -32.4822 | -74.2874 |
| median_trades | 7.0 | 161.0 | 154.0 |
| n exp>0 / 7 | 6 | 1 | -5 |
| soft promote | PASS | **FAIL** | — |

---

## E. Archive / next family (soft_promote FAIL → no grind)

No EMA period / TF / cost grind. Archive this candidate. Propose **one** next Scalp family:

**Next Scalp family (ONE, no EMA/TF/cost grind):** `ema12_30_persist2_entry_15m` on DOGE-USDT 15m Scalp €20 — asymmetric persist-2 entry (same structure as Mid #56) on the 15m EMA12/30 family. Intended to cut whipsaw entries if 15m plain fails soft_promote on exp>0 count, without retuning periods or switching TF.

---

## What this is not

- Not an EMA 12/30 period grind.
- Not a change to R1–R7 window dates.
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Scalp-arming. Soft PASS ≠ Scalp-arm. Live ≤€20.
- Not a claim that past rise windows forecast the next bull.
- Mid 4H stays Mid baseline.

`not_a_forecast: true`. `place_orders: false`.
