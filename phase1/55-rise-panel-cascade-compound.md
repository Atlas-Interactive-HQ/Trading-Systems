# 55 — rise_panel_v1 Track B cascade compound (Core/Mid/Scalp)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; paper only.
**Panel:** `rise_panel_v1` (R1–R7 dates **locked** in phase1/54 — unchanged).
**compound_id:** `rise_panel_v1_cascade_compound_721`
**Parent:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) · [`34-three-tier-cascade.md`](./34-three-tier-cascade.md) · [`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md)

> **`provisional_scalp: true`** — Scalp stand-in `scalp_doge_ema_1h_daily_bull` did **not** soft-promote on rise_panel_v1. Full compound equity / transfers / DD still reported honestly below.

---

## Systems v1 (parallel)

| Sleeve | Start € | Share | System |
|--------|--------:|------:|--------|
| Core | 140 | 70% | DOGE-USDT **1D** EMA12/30 long/flat |
| Mid | 40 | 20% | DOGE-USDT **4H** EMA12/30 long/flat (soft_promote PASS #54) |
| Scalp | 20 | 10% | DOGE-USDT **1H** EMA12/30 + daily EMA bull (`scalp_doge_ema_1h_daily_bull`) **PROVISIONAL** |
| **Total** | **200** | **7:2:1** | One-way Scalp→Mid→Core |

### Scalp choice

- **Chosen:** `rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20` — turnover Scalp with real trades (not n≈0 BH twin). Prefer 1H EMA + daily filter over 15m breakout for MD/pad reuse.
- **`provisional_scalp`:** `true`
- Soft-promote (`soft_promote_v1`): **FAIL** (median_trades=18.0, exp>0=4/7, panel_net=44.7022)
- Note: INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0.

---

## Cascade + compounding rules (LOCKED for this trial)

- **Direction:** `scalp→mid→core` — one-way; no downward refill.
- **Surplus trigger:** `window_end_surplus_share_721` — at each window end, rebalance surplus to target shares 7:2:1 when `sleeve_equity > target_share * total + min_transfer (€1)`.
- **Documented rule:** After each R-window's three independent compounded walks, snapshot sleeve end equities onto CascadeLedger, then surplus_share_rebalance: for Scalp then Mid, if sleeve_equity > target_share * total_book + min_transfer (€1), transfer surplus upward. Core never sends. No mid-window refill.
- **Compounding:** Within each sleeve walk, size tracks sleeve cash (full sleeve when long / cash when flat) — compound up on closed trades. No martingale / no size-up-on-loss.
- **Windows:** Each R1–R7 window starts fresh at Core €140 / Mid €40 / Scalp €20 (panel windows are scored independently; no cross-window capital carry).
- **Costs:** PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.
- **Fail-closed** on missing MD / insufficient bars.
- **No martingale.**

---

## A. LOCKED panel dates (unchanged from #54)

| Id | Start (UTC) | End (UTC, incl.) | Approx end-to-end % | Character |
|----|-------------|------------------|--------------------:|-----------|
| R1 | 2020-10-01 | 2020-12-31 | **+87.1%** | late-2020 year-end grind |
| R2 | 2021-07-20 | 2021-10-20 | **+45.5%** | mid-2021 post-crash recovery chop |
| R3 | 2022-08-10 | 2022-11-07 | **+39.8%** | late-2022 bounce (choppy) |
| R4 | 2023-09-01 | 2023-11-30 | **+30.8%** | Sep–Nov 2023 ETF-anticipation grind |
| R5 | 2023-12-01 | 2024-02-29 | **+49.7%** | winter 23/24 continuation rise |
| R6 | 2024-03-01 | 2024-05-31 | **+28.8%** | spring 2024 choppy bull |
| R7 | 2024-08-07 | 2024-11-04 | **+78.0%** | late-2024 grind |

---

## B. Per-window compound results (measured)

| Id | Start € | End pre € | End post € | Comb net pre € | Transfers n/€ | Core net € | Mid net € | Scalp net € | DDΣ proxy € | Scalp n |
|----|--------:|----------:|-----------:|---------------:|---------------:|----------:|---------:|-----------:|------------:|--------:|
| R1 | 200.0 | 328.1406 | 328.1406 | 128.1406 | 0/0.0000 | 100.9579 | 14.1670 | 13.0156 | 79.7031 | 18 |
| R2 | 200.0 | 200.8407 | 200.8407 | 0.8407 | 1/17.1000 | -16.6090 | 17.2682 | 0.1815 | 95.7617 | 12 |
| R3 | 200.0 | 312.2683 | 312.2683 | 112.2683 | 1/6.3758 | 82.0222 | 12.6435 | 17.6026 | 71.8822 | 10 |
| R4 | 200.0 | 240.9324 | 240.9324 | 40.9324 | 0/0.0000 | 35.3467 | 4.8046 | 0.7810 | 24.1022 | 16 |
| R5 | 200.0 | 290.9943 | 290.9943 | 90.9943 | 0/0.0000 | 83.1141 | 4.1914 | 3.6889 | 58.8587 | 21 |
| R6 | 200.0 | 237.1153 | 237.1153 | 37.1153 | 1/8.4630 | 16.7226 | 15.8860 | 4.5066 | 128.1546 | 22 |
| R7 | 200.0 | 282.0194 | 282.0194 | 82.0194 | 0/0.0000 | 62.4439 | 14.6496 | 4.9258 | 47.2073 | 18 |

> DDΣ proxy = sum of per-sleeve max DD (not joint marked path). Transfers are window-end surplus-share only.

### Per-sleeve detail (pre-cascade walk metrics)

| Id | Core n/net/DD | Mid n/net/DD | Scalp n/exp/net/DD |
|----|--------------:|-------------:|-------------------:|
| R1 | 0/100.9579/53.4298 | 5/14.1670/21.2626 | 18/0.6561/13.0156/5.0107 |
| R2 | 2/-16.6090/69.2569 | 5/17.2682/23.2540 | 12/-0.0154/0.1815/3.2508 |
| R3 | 1/82.0222/43.1498 | 15/12.6435/20.8896 | 10/1.7603/17.6026/7.8428 |
| R4 | 0/35.3467/14.4543 | 10/4.8046/6.5329 | 16/-0.0063/0.7810/3.1150 |
| R5 | 1/83.1141/32.5003 | 11/4.1914/19.3072 | 21/-0.1132/3.6889/7.0512 |
| R6 | 1/16.7226/87.9988 | 7/15.8860/29.8875 | 22/0.2048/4.5066/10.2683 |
| R7 | 0/62.4439/34.5043 | 7/14.6496/9.4064 | 18/0.2558/4.9258/3.2967 |

---

## C. Full-panel narrative

- **ok windows:** 7/7
- **panel start equity (sum of independent window starts):** **1400.0000** € (= n_ok × €200)
- **panel end equity pre-cascade (sum):** **1892.3109** €
- **panel end equity post-cascade (sum):** **1892.3109** € (same total — surplus moves between sleeves only)
- **combined net pre-cascade:** **492.3109** €
- **transfers:** n=3 · sum **31.9388** € (Scalp→Mid / Mid→Core)
- **per-sleeve net (pre-cascade, panel sum):** Core **363.9983** · Mid **83.6104** · Scalp **44.7022** €
- **worst window DDΣ proxy:** **128.1546** €
- Panel sums treat each R-window as an independent €200 start (7×€200 = €1400 notionally across the panel). Cascade transfers are intra-window only.

### Soft-promote snapshots (informational for Core; Mid prior PASS; Scalp gate)

- Core: median_trades=1.0 · exp>0=2/7 · panel_net=363.9983
- Mid: median_trades=7.0 · exp>0=6/7 · panel_net=83.6104 · soft=PASS
- Scalp: median_trades=18.0 · exp>0=4/7 · panel_net=44.7022 · soft=FAIL · **provisional_scalp=true**

### Combined expectancy narrative

Expectancy is per-sleeve after costs (€/closed trade). Core on 1D often has low n (open-hold through rise legs). Mid 4H and Scalp 1H supply turnover. Cascade does not create edge — it only moves surplus capital upward after walks. Panel combined net is the sum of independent window book nets (pre-cascade). Scalp soft-promote is **FAIL**; treat Scalp as **provisional** stand-in for Track B compound reporting.

`not_a_forecast: true`.

---

## D. Harness

- Script: `scripts/run_rise_panel_cascade_compound_eval.py`
- Module: `atlas.paper.rise_panel_cascade_eval` · cascade surplus: `atlas.paper.cascade.surplus_share_rebalance` / `apply_walk_ends_then_surplus`
- Unit tests: `tests/unit/test_rise_panel_cascade_compound.py`
- Reports: `data/reports/rise_panel_v1_cascade_compound.json`

---

## What this is not

- Not a live / Phase C recommendation. Not `ga live €200`.
- Not a change to R1–R7 window dates.
- Not a claim that cascade surplus creates alpha.
- Not a silent rewrite of `core_style_return` A∧B.
- **Scalp is provisional** — do not treat soft-promote FAIL as board CONFIRMED.

`not_a_forecast: true`. `place_orders: false`. `config/default.yaml` untouched.
