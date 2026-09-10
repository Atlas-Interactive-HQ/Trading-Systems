# 54 — rise_panel_v1 (DOGE-USDT similar upward / choppy-bull panel)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming.
**Label:** `rise_panel_v1`
**Parent:** [`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md) · cascade sleeves Core €140 / Mid €40 / Scalp €20

---

## Soft promote gate (LOCKED — intentional, labeled)

**NOT** a silent rewrite of the Core-style A∧B three-stream board (`core_style_return` dual A∧B).
This panel gate is a **separate**, explicitly labeled research promote path for rise-character windows:

1. `median_trades` across the 7 windows **≫ 0** (coded: `median_trades >= 1`; excludes n≈0 BH-twin open-hold)
2. **≥5 / 7** windows with `expectancy_after_costs > 0`
3. **panel net > 0** (sum of after-costs net € across 7)

All three required for soft-promote PASS. Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.

---

## A. LOCKED panel — 7 DOGE-USDT windows (BEFORE any scoring)

**Asset / bar (primary live path):** `DOGE-USDT` research MD (not OMS `DOGE-USD`), decision bar for Core baseline = **1D**.
**Selection rule:** ~2–4 month spans with **similar upward / choppy-bull rise character** across years. Not random. Not cherry-picked after a trial. Mega-spike fragments (e.g. 2021-01 DOGE mania) excluded as dissimilar.

Approx % moves computed from OKX EEA public `history-candles` DOGE-USDT **1D** (open of start day → close of end day; intra peak% / close-to-close max DD%). Fetched 2026-09-10 UTC. Do not invent %.

| Id | Start (UTC) | End (UTC, incl.) | Approx end-to-end % | Peak from open % | Intra max DD % | Character |
|----|-------------|------------------|--------------------:|-----------------:|---------------:|-----------|
| R1 | 2020-10-01 | 2020-12-31 | **+87.1%** | +107.2% | 24.3% | late-2020 year-end grind |
| R2 | 2021-07-20 | 2021-10-20 | **+45.5%** | +109.5% | 40.9% | mid-2021 post-crash recovery chop |
| R3 | 2022-08-10 | 2022-11-07 | **+39.8%** | +123.4% | 31.9% | late-2022 bounce (choppy) |
| R4 | 2023-09-01 | 2023-11-30 | **+30.8%** | +38.0% | 9.6% | Sep–Nov 2023 ETF-anticipation grind |
| R5 | 2023-12-01 | 2024-02-29 | **+49.7%** | +62.7% | 23.5% | winter 23/24 continuation rise |
| R6 | 2024-03-01 | 2024-05-31 | **+28.8%** | +84.2% | 44.4% | spring 2024 choppy bull |
| R7 | 2024-08-07 | 2024-11-04 | **+78.0%** | +83.3% | 20.6% | late-2024 grind |

**Similarity band:** end-to-end roughly **+29% … +87%**; all upward; all show intra drawdowns (choppy-bull, not one-way vertical). Spans **2020–2024**; non-overlapping.

**Code lock:** `atlas.paper.rise_panel.RISE_PANEL_V1` / label `rise_panel_v1`.

---

## B. Harness

- Script: `scripts/run_rise_panel_eval.py`
- Module: `atlas.paper.rise_panel` (defs + soft-promote) · `atlas.paper.rise_panel_eval` (Core / Mid walks)
- Reuse: `walk_long_flat` / `EmaTrendV1` (EMA Core / Mid harnesses)
- Sleeve baseline Core: **€140**. Mid candidate: **€40**. Mid €40 scale for Core twin out of scope for baseline unless trivial.
- Unit tests: `tests/unit/test_rise_panel.py`

---

## C. Baseline — Core DOGE 1D EMA12/30 long/flat (€140)

**baseline_id:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`

Strategy: long iff closed-bar EMA12 > EMA30; else flat. Never short. Signal close → next open. PaperSettings 5+5 bps.

### Baseline per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 0 | — | 100.9579 | 53.4298 | 0.5714 | 104.3781 | 54.2424 |
| R2 | 2 | -7.4986 | -16.6090 | 69.2569 | 0.4022 | 69.3232 | 113.9447 |
| R3 | 1 | -10.5166 | 82.0222 | 43.1498 | 0.3146 | 88.7868 | 52.9270 |
| R4 | 0 | — | 35.3467 | 14.4543 | 0.4111 | 41.4976 | 14.9763 |
| R5 | 1 | 1.5895 | 83.1141 | 32.5003 | 0.5333 | 85.9404 | 40.0347 |
| R6 | 1 | 26.3396 | 16.7226 | 87.9988 | 0.6154 | 36.2360 | 108.5424 |
| R7 | 0 | — | 62.4439 | 34.5043 | 0.4944 | 85.2900 | 38.4366 |

**Panel summary (baseline):**
- windows with exp>0: **2**/7 · net>0: **6**/7
- median expectancy €/trade: **-2.9545**
- median_trades: **1.0**
- panel net €: **363.9983**
- worst DD €: **87.9988**

> Soft-promote is **not** applied to Core baseline for board rewrite; baseline is the reference for Mid compare. Informational soft-promote on baseline would be: **FAIL** (differs_from_core_style_ab=true).

`not_a_forecast: true`.

---

## D. Mid improvement candidate (same 7)

**mid_candidate_id:** `rise_panel_v1_mid_doge_ema12_30_4h_eur40`  · **compare_to:** `rise_panel_v1_core_doge_ema12_30_1d_eur140`

Mid DOGE-USDT **4H** EMA12/30 long/flat (€40) — TF Mid ≠ 1D Core twin; exits on EMA cross → real turnover (not n≈0 BH twin).

### Mid per window

| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |
|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|
| R1 | 5 | 2.6469 | 14.1670 | 21.2626 | 0.5670 | 30.7232 | 19.7678 |
| R2 | 5 | 2.6589 | 17.2682 | 23.2540 | 0.5412 | 18.5427 | 35.0187 |
| R3 | 15 | 0.8429 | 12.6435 | 20.8896 | 0.4519 | 24.3395 | 19.8179 |
| R4 | 10 | 0.2490 | 4.8046 | 6.5329 | 0.5238 | 12.2152 | 9.1820 |
| R5 | 11 | -0.6979 | 4.1914 | 19.3072 | 0.4890 | 16.1254 | 13.7988 |
| R6 | 7 | 2.2694 | 15.8860 | 29.8875 | 0.5960 | 14.0932 | 36.1697 |
| R7 | 7 | 2.0928 | 14.6496 | 9.4064 | 0.5815 | 25.4916 | 12.4650 |

**Panel summary (Mid):**
- windows with exp>0: **6**/7 · net>0: **7**/7
- median expectancy €/trade: **2.0928**
- median_trades: **7.0**
- panel net €: **83.6104**
- worst DD €: **29.8875**

### Soft promote (Mid): **PASS** (`soft_promote_v1`)

- median_trades=7.0 (ok=True, min>=1)
- exp>0: 6/7 (need ≥5; ok=True)
- panel_net €=83.6104 (ok=True)
- note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

### Mid vs baseline (panel metrics)

| Metric | Baseline Core €140 1D | Mid €40 4H |
|--------|----------------------:|-----------:|
| median_trades | 1.0 | 7.0 |
| n exp>0 / 7 | 2 | 6 |
| panel net € | 363.9983 | 83.6104 |
| median exp € | -2.9545 | 2.0928 |
| worst DD € | 87.9988 | 29.8875 |
| soft promote | informational FAIL | **PASS** |

`not_a_forecast: true`.

---

## What this is not

- Not a rewrite of `core_style_return` A∧B on phase1/38.
- Not a live / Phase C recommendation. Not `ga live €200`.
- Not a claim that past rise windows forecast the next bull.
- Named calendar windows ≠ similar-regime matching.

`not_a_forecast: true`. `place_orders: false`.
