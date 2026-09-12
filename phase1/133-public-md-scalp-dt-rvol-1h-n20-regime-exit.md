# 133 — Public-MD Scalp: #132 entry + 4H EMA21 regime-flip exits (Jul2020–Jan2021 €20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/133** — coordinator-locked **pre-registered strengthen of exits** (same entry as #132). **NOT** an N/k/RVOL grind. **Do not edit** phase1/120–132.
**Lineage:** Leave **#130 / #131 / #132** STOP. Do **not** restore BOS lineage (125–129). Do **not** import `scalp_structure_bos_*`. Do **not** take **134**. Do **not** promote #130–132.

Code: `atlas.strategy.scalp_dt_rvol_1h_133` · `atlas.paper.public_md_scalp_dt_rvol_1h_133` · script `scripts/run_public_md_scalp_dt_rvol_1h_133.py`  
Report JSON: `results/public_md_scalp_dt_rvol_1h_133.json` (also `data/reports/…`)  
Candle cache: **reuse** `data/paper/candles/public_md_121/*_1H.jsonl`; **4H** reuse `data/paper/candles/public_md_131/*_4H.jsonl` (OKX EEA from #131). Do not invent bars.

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **133** (not 120–132) |
| **ENTRY** | **same as #132** |
| **Regime (entry)** | **4H** close > EMA(21) → long-only eligible; else **no entry** (**no shorts**) |
| **Setup TF** | **1H Dual Thrust** N=**20**, k1=k2=0.5; range = HH(N)−LL(N) over *prior* N bars exclusive of decision bar (`prior_hh_ll_range` / `ranges_at`) |
| **Entry** | closed 1H close > BuyLine **AND** RVOL(20) > **1.0**; fill = next 1H open; one position |
| **RVOL** | volume / SMA(volume, 20) via `atlas.strategy.rvol.rvol_series` on 1H |
| **SL** | SellLine **at entry** (fixed, not trailing); if not strictly below entry → entry − 1×ATR(14) Wilder **1H**; if still not below → **skip** entry (fail closed). Honor SL (close / next-open convention same as #132 walker). |
| **NEW exits** | Exit long when **4H close < EMA21** (regime flip) — signal on that closed 4H, fill **next 1H open** after the 4H close (no lookahead). **NO** Dual Thrust sell-line profit exit. **NO** 1.5R TP. Time-stop failsafe only: **168** × 1H (~1 week). |
| **Costs** | sleeve €20 · PaperSettings **5+5 bps** · accounting_v2 · confirm_closed_only · no martingale · no leverage |
| **Universe** | BTC-USDT / ETH-USDT / DOGE-USDT. USD N/A. Memes N/A. |
| **PASS (FULL)** | completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs. Else FAIL / no promote. Soft PASS N/A. |
| **No grind** | Do **not** grind N / k / RVOL / EMA / TF this run. Enabling `r_multiple` or sellline-exit raises `ValueError`. |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |
| **STOP** | Do **not** take **134**. Do **not** promote #130/#131/#132. |

### Candidate id

`public_md_v1_dt_n20_k0505_rvol20_gt10_ema21_4h_regime_exit_1h_{btc|eth|doge}_usdt_eur20`

### Windows (UTC, exclusive end)

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup from **2020-06-01**. Series n (measured): 1H **5136** / FULL trade **4416**; 4H **1284** per pair.

No-lookahead: for a closed 1H bar, regime uses the last **closed** 4H bar with close_ts ≤ 1H close_ts.

---

## Gate

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`  
Soft PASS = **N/A ≠ Scalp-arm** · `not_a_forecast` · no promote.

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_dt_rvol_1h_133.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T15:06:28Z` (2026-09-12T17:06:28 PT / Europe/Amsterdam).

Exit mix = **SL / regime-flip / time-stop**. `n_tp` and `n_sellline` are **0** on every cell (1.5R and sell-line profit exit off).

BH recomputed on 1H trade bars in the walker (do not hardcode). BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366 (matches #132 walker BH).

### FULL

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits SL/regime/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|---------------------:|-----------:|
| BTC-USDT | 16 | 0.14934035 | 6.30234864 | 43.17666206 | False | False | 4/10/2 | 0.33956782 |
| ETH-USDT | 22 | 0.53081093 | 15.95125382 | 45.16769469 | False | False | 4/16/2 | 0.64894192 |
| DOGE-USDT | 20 | 0.28186995 | 5.63739903 | 20.2301366 | False | False | 6/14/0 | 0.4415033 |

### SUB_A (DeFi summer → 2020-10-01Z)

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits SL/regime/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|---------------------:|-----------:|
| BTC-USDT | 9 | -0.02632599 | -0.23693394 | 3.544385 | False | False | 3/5/1 | 0.18439795 |
| ETH-USDT | 11 | 0.85535213 | 9.40887346 | 11.84225941 | False | False | 1/8/2 | 0.31440566 |
| DOGE-USDT | 7 | 0.3028067 | 2.11964692 | 2.68221033 | False | False | 2/5/0 | 0.17618461 |

### SUB_B (BTC run 2020-10-01Z → 2021-01-01Z)

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits SL/regime/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|---------------------:|-----------:|
| BTC-USDT | 7 | 0.3796947 | 6.61769811 | 33.55838705 | False | False | 1/5/1 | 0.15703012 |
| ETH-USDT | 11 | 0.14027722 | 4.44925599 | 20.8350418 | False | False | 3/8/0 | 0.22750701 |
| DOGE-USDT | 13 | 0.24466603 | 3.18065842 | 15.36161462 | False | False | 4/9/0 | 0.2398942 |

---

## Honesty vs #132 FULL exit-mix

#132 FULL (same entry; exits = 1.5R / sell-line / SL / time-stop 48): BTC 22/−0.11740487/−2.58290714 mix TP/SL/sell/time **4/6/5/7** · ETH 29/0.25271795/7.32882069 mix **11/9/4/5** · DOGE 24/0.21480547/5.1553314 mix **7/6/4/7**. BH BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.

#133 FULL exit-mix (SL / regime-flip / time-stop 168; TP=0 sellline=0): BTC **4/10/2** · ETH **4/16/2** · DOGE **6/14/0**.

| Inst | n 133 / 132 | exp 133 / 132 | terminal 133 / 132 | Δ exp | Δ terminal | mix 133 SL/reg/time | mix 132 TP/SL/sell/time |
|------|------------:|--------------:|-------------------:|------:|-----------:|--------------------:|------------------------:|
| BTC-USDT | 16 / 22 | 0.14934035 / -0.11740487 | 6.30234864 / -2.58290714 | 0.26674522 | 8.88525578 | 4/10/2 | 4/6/5/7 |
| ETH-USDT | 22 / 29 | 0.53081093 / 0.25271795 | 15.95125382 / 7.32882069 | 0.27809298 | 8.62243313 | 4/16/2 | 11/9/4/5 |
| DOGE-USDT | 20 / 24 | 0.28186995 / 0.21480547 | 5.63739903 / 5.1553314 | 0.06706448 | 0.48206763 | 6/14/0 | 7/6/4/7 |

Regime-flip exits + no 1.5R/sell-line TP **raise** exp and terminal vs #132 on all three pairs (fewer, longer holds). **None** beat BH → gate FAIL. Do **not** rescue via N/k/RVOL grind. Do **not** take 134.

---

## What not to rescue

- Do **not** grind N / k / RVOL / EMA / TF.
- Do **not** re-enable 1.5R or sell-line profit exit.
- Do **not** promote #130, #131, or #132.
- Do **not** restore BOS (125–129).
- Do **not** take **134**.
- Soft PASS **N/A ≠ Scalp-arm**. `not_a_forecast`. `default.yaml` untouched. `place_orders: false`.

---

## STOP

**STOP after 133.** No 134. Single pre-registered score recorded.
