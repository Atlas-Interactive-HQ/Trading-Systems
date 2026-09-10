# 70 — rise_panel_v1 Core: DOGE **1D Donchian 20/10** long/flat (€140)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Core-arm.
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked R1–R7 dates (DO NOT change).
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))
**Book:** Core + Mid Breakout only; Scalp = Kaje manual. Mid formal baseline: Breakout #65 `rise_panel_v1_mid_doge_breakoutv1_4h_eur40` panel≈€95.45 (unchanged this trial).
**Compare:** Core 1D EMA baseline [`54-rise-panel-v1.md`](./54-rise-panel-v1.md). **Canonical Donchian 20/10** (Mid #64 / Scalp #61 / DonchianLongFlatV1) on **1D** Core — **no** EMA filter. Promote-as-better only if panel_net > Core EMA.

---

## Soft promote gate (LOCKED — same as #54)

`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of `core_style_return` A∧B):

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

**Honesty:** promote-as-better only if panel_net higher than Core EMA baseline. Core EMA often thin n / BH-like — soft PASS alone ≠ Core-arm.

---

## A. LOCKED Core EMA baseline (do not retune)

**core_baseline_id:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`  
(phase1/54 reference; soft_promote NOT applied for board rewrite — informational soft would FAIL; thin n / BH-like)

- Rule: closed-bar **EMA12 > EMA30** → long; else flat. Never short.
- Bar: DOGE-USDT **1D**. Sleeve: Core **€140**.
- Compare target for this trial: **Core Donchian vs Core-EMA-baseline**.
- Snapshot (#54/#55/#65 recheck): panel_net≈**€363.9983** · median_trades=**1.0** · exp>0 **2**/7 (VERIFY measured below — do not invent).

### Core EMA baseline per window (re-scored)

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 0 | — | 100.9579 | 53.4298 | 0.5714 | 104.3781 | 54.2424 |
| R2 | 2 | -7.4986 | -16.6090 | 69.2569 | 0.4022 | 69.3232 | 113.9447 |
| R3 | 1 | -10.5166 | 82.0222 | 43.1498 | 0.3146 | 88.7868 | 52.9270 |
| R4 | 0 | — | 35.3467 | 14.4543 | 0.4111 | 41.4976 | 14.9763 |
| R5 | 1 | 1.5895 | 83.1141 | 32.5003 | 0.5333 | 85.9404 | 40.0347 |
| R6 | 1 | 26.3396 | 16.7226 | 87.9988 | 0.6154 | 36.2360 | 108.5424 |
| R7 | 0 | — | 62.4439 | 34.5043 | 0.4944 | 85.2900 | 38.4366 |

**Panel summary (Core EMA baseline — measured):**
- windows with exp>0: **2**/7 · net>0: **6**/7
- median expectancy €/trade: **-2.9545**
- median_trades: **1.0**
- panel net €: **363.9983**
- worst DD €: **87.9988**
- soft_promote (informational only): **FAIL** (`soft_promote_v1`) — NOT a board rewrite

---

## B. LOCKED Core family (BEFORE scoring)

**ONE family only — NOT grinding Donchian N / TF / costs. No EMA filter. Do not re-grind Core EMA.**

**Family:** `donchian20_10_long_flat_1d`  
**core_improve_id:** `rise_panel_v1_core_doge_donchian20_10_1d_eur140`  
**compare_to:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`
**Canonical Donchian:** repo `DonchianLongFlatV1` entry **20** / exit **10** (yaml untouched). Decision bar **1D**. Long/flat only. **No** EMA filter. Same family as Mid #64 / Scalp #61 paper rule.

### Rule card (LOCKED)

- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1D**.
- Donchian entry lookback **20** / exit lookback **10**.
- **Long:** closed-bar close > prior 20-bar high. Long only.
- **Flat/exit:** closed-bar close < prior 10-bar low. Never short.
- **No** EMA filter / regime gate (distinct from Core EMA12/30 baseline).
- Insufficient history → flat.
- Fill: signal close → next open. Size: full Core sleeve €140 when long.
- Costs: PaperSettings 5+5 bps.
- **No** Donchian N / TF / cost grind on FAIL. **No** EMA rescue.

### Why this family

Core EMA baseline panel≈€363.9983 with thin median_trades=1.0 (BH-like). Core #69 BreakoutV1 soft FAIL / worse panel_net. This trial ports **canonical Donchian 20/10** (Mid #64 / Scalp #61 / DonchianLongFlatV1) onto Core €140 / locked rise panel / **1D** — without EMA so the family stays distinct from Core EMA and #69 Breakout.

---

## C. Harness

- Script: `scripts/run_rise_panel_core_donchian_1d_eval.py`
- Module: `atlas.paper.rise_panel_core_donchian_1d_eval`
- Strategy: `atlas.strategy.core_doge_donchian_1d` (thin Core wrapper around canonical `DonchianLongFlatV1` 20/10)
- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; Core(Donchian)+Mid(Breakout) book €180 on PASS+better only (no Scalp)
- Unit tests: `tests/unit/test_rise_panel_core_donchian_1d.py`

---

## D. Results — Core Donchian 20/10 1D €140 on same 7

**core_improve_id:** `rise_panel_v1_core_doge_donchian20_10_1d_eur140`

### Improve per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 1 | 6.2628 | 36.8781 | 46.3083 | 0.4066 | 104.3781 | 54.2424 |
| R2 | 1 | 18.7178 | 18.7178 | 38.2918 | 0.2065 | 69.3232 | 113.9447 |
| R3 | 1 | -31.1945 | 51.5353 | 49.9523 | 0.6404 | 88.7868 | 52.9270 |
| R4 | 0 | — | 39.5834 | 14.8036 | 0.4222 | 41.4976 | 14.9763 |
| R5 | 1 | -0.7020 | 79.5032 | 22.5747 | 0.3111 | 85.9404 | 40.0347 |
| R6 | 2 | -17.6497 | -35.2994 | 91.4795 | 0.3846 | 36.2360 | 108.5424 |
| R7 | 0 | — | 57.2456 | 33.6183 | 0.8090 | 85.2900 | 38.4366 |

**Panel summary (Core Donchian 20/10 1D):**
- windows with exp>0: **2**/7 · net>0: **6**/7
- median expectancy €/trade: **-0.7020**
- median_trades: **1.0**
- panel net €: **248.1640**
- worst DD €: **91.4795**

### Soft promote (Core Donchian 20/10): **FAIL** (`soft_promote_v1`)

- median_trades=1.0 (ok=True, min>=1)
- exp>0: 2/7 (need ≥5; ok=False)
- panel_net €=248.1640 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Honesty deltas vs Core 1D EMA baseline (Donchian − baseline)

> **Primary compare:** panel_net Δ **≤0** vs Core EMA baseline (≈€363.9983). **Not better on panel net — do not promote-as-better.** Soft PASS ≠ Core-arm.

| Metric | Core EMA 1D €140 | Core Donchian 20/10 1D €140 | Δ |
|--------|-----------------:|------------------------:|--:|
| median exp € | -2.9545 | -0.7020 | 2.2525 |
| panel net € | 363.9983 | 248.1640 | -115.8343 |
| median_trades | 1.0 | 1.0 | 0.0 |
| n exp>0 / 7 | 2 | 2 | 0 |
| soft promote | FAIL (info) | **FAIL** | — |
| promote-as-better | — | **NO** | — |

---

## E. On FAIL — archive (no grind, no auto-next)

soft_promote **FAIL** (or incomplete). Archive this family. Do **not** grind lookback / ATR / TF / costs. Do **not** auto-start next. Do **not** invent Scalp. Cascade skip. Ping-ready for coordinator.

---

## What this is not

- Not a Donchian N / TF / cost grind.
- Not an EMA filter / period grind.
- Not Core #69 BreakoutV1 (lookback 16 + ATR) — this is Donchian 20/10.
- Not a change to R1–R7 window dates (phase1/54 lock).
- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not Core-arming / Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.
- Not a Scalp sleeve (bot path Core+Mid only; Scalp = Kaje manual).
- Not a claim that past rise windows forecast the next bull.
- **Not better than Core EMA baseline on panel_net** — do not promote-as-better.

`not_a_forecast: true`. `place_orders: false`.
