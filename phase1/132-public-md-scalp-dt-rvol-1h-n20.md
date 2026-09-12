# 132 — Public-MD Scalp: Dual Thrust N20 + RVOL>1.0 1H + 4H EMA21 (Jul2020–Jan2021 €20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/132** — coordinator-locked **pre-registered** card from #121 honesty (1H DT N20 RVOL>1 relatively better than #131 N4 RVOL>1.2). **NOT** a blind grind of #131. **Do not edit** phase1/120–131.
**Lineage:** Leave **#130 15m** and **#131 N4** STOP. Do **not** restore BOS lineage (125–129). Do **not** import `scalp_structure_bos_*`. Do **not** take **133**.

Code: `atlas.strategy.scalp_dt_rvol_1h_132` · `atlas.paper.public_md_scalp_dt_rvol_1h_132` · script `scripts/run_public_md_scalp_dt_rvol_1h_132.py`  
Report JSON: `results/public_md_scalp_dt_rvol_1h_132.json` (also `data/reports/…`)  
Candle cache: **reuse** `data/paper/candles/public_md_121/*_1H.jsonl`; **4H** reuse `data/paper/candles/public_md_131/*_4H.jsonl` (OKX EEA from #131). Do not invent bars.

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **132** (not 120–131) |
| **Regime** | **4H** close > EMA(21) → long-only eligible; else flat (**no shorts**) |
| **Setup TF** | **1H Dual Thrust** N=**20**, k1=k2=0.5; range = HH(N)−LL(N) over *prior* N bars exclusive of decision bar (`prior_hh_ll_range` / `ranges_at`) |
| **Entry** | closed 1H close > BuyLine **AND** RVOL(20) > **1.0**; fill = next 1H open; one position |
| **RVOL** | volume / SMA(volume, 20) via `atlas.strategy.rvol.rvol_series` on 1H |
| **SL** | SellLine **at entry**; if not strictly below entry → entry − 1×ATR(14) Wilder **1H**; if still not below → **skip** entry (fail closed) |
| **TP / exits** | 1.5R **OR** closed 1H close < **current-bar** SellLine (whichever first); honor SL; time-stop **48** × 1H |
| **Costs** | sleeve €20 · PaperSettings **5+5 bps** · accounting_v2 · confirm_closed_only · no martingale · no leverage |
| **Universe** | BTC-USDT / ETH-USDT / DOGE-USDT. USD N/A. Memes N/A. |
| **PASS (FULL)** | completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs. Else FAIL / no promote. Soft PASS N/A. |
| **No grind** | Do **not** grind N / k / RVOL / EMA / TF / R / time-stop this run (incl. N=4 / RVOL 1.2). |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |
| **STOP** | Do **not** take **133**. Do **not** promote #130/#131. |

### Candidate id

`public_md_v1_dt_n20_k0505_rvol20_gt10_ema21_4h_regime_1h_{btc|eth|doge}_usdt_eur20`

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

Source: `results/public_md_scalp_dt_rvol_1h_132.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T15:00:34Z` (2026-09-12T17:00:34 PT / Europe/Amsterdam).

Exit mix = **TP / SL / sellline / time-stop**.

BH recomputed on 1H trade bars in the walker (do not hardcode). BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.

### FULL

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/sell/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|----------------------:|-----------:|
| BTC-USDT | 22 | -0.11740487 | -2.58290714 | 43.17666206 | False | False | 4/6/5/7 | 0.41122004 |
| ETH-USDT | 29 | 0.25271795 | 7.32882069 | 45.16769469 | False | False | 11/9/4/5 | 0.71211858 |
| DOGE-USDT | 24 | 0.21480547 | 5.1553314 | 20.2301366 | False | False | 7/6/4/7 | 0.58920256 |

### SUB_A (DeFi summer → 2020-10-01Z)

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/sell/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|----------------------:|-----------:|
| BTC-USDT | 12 | -0.13253563 | -1.59042758 | 3.544385 | False | False | 1/3/4/4 | 0.23694522 |
| ETH-USDT | 14 | 0.38367927 | 5.37150982 | 11.84225941 | False | False | 5/3/3/3 | 0.34319895 |
| DOGE-USDT | 8 | 0.43587877 | 3.48703018 | 2.68221033 | True | False | 3/3/2/0 | 0.20183599 |

### SUB_B (BTC run 2020-10-01Z → 2021-01-01Z)

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/sell/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|----------------------:|-----------:|
| BTC-USDT | 10 | -0.10782382 | -1.07823823 | 33.55838705 | False | False | 3/3/1/3 | 0.18933047 |
| ETH-USDT | 15 | 0.10286139 | 1.54292078 | 20.8350418 | False | False | 6/6/1/2 | 0.29081408 |
| DOGE-USDT | 16 | 0.08878843 | 1.4206149 | 15.36161462 | False | False | 4/3/2/7 | 0.3298557 |

---

## Honesty vs #131 (1H DT N4 RVOL>1.2 + 4H EMA21 FULL)

#131 FULL: BTC 78/−0.00408787/−0.31885419 · ETH 105/−0.02607385/−2.73775434 · DOGE 57/0.06612059/3.7688737.

| Inst | n 132 / 131 | exp 132 / 131 | terminal 132 / 131 | Δ exp | Δ terminal |
|------|------------:|--------------:|-------------------:|------:|-----------:|
| BTC-USDT | 22 / 78 | -0.11740487 / -0.00408787 | -2.58290714 / -0.31885419 | -0.113317 | -2.26405295 |
| ETH-USDT | 29 / 105 | 0.25271795 / -0.02607385 | 7.32882069 / -2.73775434 | 0.2787918 | 10.06657503 |
| DOGE-USDT | 24 / 57 | 0.21480547 / 0.06612059 | 5.1553314 / 3.7688737 | 0.14868488 | 1.3864577 |

ETH/DOGE beat #131 on exp and terminal; BTC worse. **None** beat BH → gate FAIL. Do **not** rescue via N/k/RVOL/EMA grind.

---

## Honesty vs #121 dual_thrust_rvol FULL (1H N20 RVOL>1, NO 4H regime, NO SL/TP/time-stop)

#121 DT+RVOL FULL: BTC 18/0.68658253/19.14953712 · ETH 19/1.1968212/22.73960271 · DOGE 24/0.2233388/5.36013111 — FAIL vs BH.

| Inst | n 132 / 121 | exp 132 / 121 | terminal 132 / 121 | Δ exp | Δ terminal |
|------|------------:|--------------:|-------------------:|------:|-----------:|
| BTC-USDT | 22 / 18 | -0.11740487 / 0.68658253 | -2.58290714 / 19.14953712 | -0.8039874 | -21.73244426 |
| ETH-USDT | 29 / 19 | 0.25271795 / 1.1968212 | 7.32882069 / 22.73960271 | -0.94410325 | -15.41078202 |
| DOGE-USDT | 24 / 24 | 0.21480547 / 0.2233388 | 5.1553314 / 5.36013111 | -0.00853333 | -0.20479971 |

Adding 4H EMA21 regime + SL/TP/time-stop **cuts** terminal vs naked #121 DT+RVOL on all three pairs. Still FAIL vs BH.

---

## What not to rescue

- Do **not** grind N / k / RVOL / EMA / R / time-stop / TF further this run.
- Do **not** promote #130 or #131.
- Do **not** restore BOS (125–129).
- Do **not** take **133**.
- Soft PASS **N/A ≠ Scalp-arm**. `not_a_forecast`. `default.yaml` untouched. `place_orders: false`.

---

## STOP

**STOP after 132.** No 133. Single pre-registered score recorded.
