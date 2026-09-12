# 131 — Public-MD Scalp: Dual Thrust N4 + RVOL 1H + 4H EMA21 (Jul2020–Jan2021 €20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/131** — coordinator-locked **new card** (not a #130 TF grind, not a #121 transplant). **Do not edit** phase1/120–130.
**Lineage:** Leave **#130 15m DT STOP**. Do **not** restore BOS lineage (125–129). Do **not** import `scalp_structure_bos_*`.

Code: `atlas.strategy.scalp_dt_rvol_1h_131` · `atlas.paper.public_md_scalp_dt_rvol_1h_131` · script `scripts/run_public_md_scalp_dt_rvol_1h_131.py`  
Report JSON: `results/public_md_scalp_dt_rvol_1h_131.json` (also `data/reports/…`)  
Candle cache: **reuse** `data/paper/candles/public_md_121/*_1H.jsonl`; **4H** from OKX EEA `history-candles` bar=4H → `data/paper/candles/public_md_131/*_4H.jsonl` (source `okx_eea_history`; resample-1H fallback available, not used this run). Do not invent bars.

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **131** (not 120–130) |
| **Regime** | **4H** close > EMA(21) → long-only eligible; else flat (**no shorts**) |
| **Setup TF** | **1H Dual Thrust** N=4, k1=k2=0.5; range = HH(N)−LL(N) over *prior* N bars exclusive of decision bar (`prior_hh_ll_range` / `ranges_at`) |
| **Entry** | closed 1H close > BuyLine **AND** RVOL(20) > 1.2; fill = next 1H open; one position |
| **RVOL** | volume / SMA(volume, 20) via `atlas.strategy.rvol.rvol_series` on 1H |
| **SL** | SellLine **at entry**; if not strictly below entry → entry − 1×ATR(14) Wilder **1H**; if still not below → **skip** entry (fail closed) |
| **TP / exits** | 1.5R **OR** closed 1H close < **current-bar** SellLine (whichever first); honor SL; time-stop **24** × 1H (~1 day) |
| **Costs** | sleeve €20 · PaperSettings **5+5 bps** · accounting_v2 · confirm_closed_only · no martingale · no leverage |
| **Universe** | BTC-USDT / ETH-USDT / DOGE-USDT. USD N/A. Memes N/A. |
| **PASS (FULL)** | completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs. Else FAIL / no promote. Soft PASS N/A. |
| **No grind** | Do **not** grind N / k / RVOL / EMA / TF / R / time-stop this run. |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |
| **STOP** | Do **not** take **132**. |

### Candidate id

`public_md_v1_dt_n4_k0505_rvol20_gt12_ema21_4h_regime_1h_{btc|eth|doge}_usdt_eur20`

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

Source: `results/public_md_scalp_dt_rvol_1h_131.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T14:56:32Z` (2026-09-12T16:56:32 PT / Europe/Amsterdam).

Exit mix = **TP / SL / sellline / time-stop**.

BH recomputed on 1H trade bars in the walker (do not hardcode). BTC/ETH match #130 15m BH cells; DOGE 1H BH differs slightly from #130’s 15m BH (20.2301366 vs 20.36962684).

### FULL

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/sell/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|----------------------:|-----------:|
| BTC-USDT | 78 | -0.00408787 | -0.31885419 | 43.17666206 | False | False | 18/16/42/2 | 1.46277296 |
| ETH-USDT | 105 | -0.02607385 | -2.73775434 | 45.16769469 | False | False | 22/22/55/6 | 2.14912279 |
| DOGE-USDT | 57 | 0.06612059 | 3.7688737 | 20.2301366 | False | False | 10/3/40/4 | 1.40625618 |

### SUB_A (DeFi summer → 2020-10-01Z)

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/sell/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|----------------------:|-----------:|
| BTC-USDT | 34 | -0.07089897 | -2.41056488 | 3.544385 | False | False | 5/6/22/1 | 0.64731223 |
| ETH-USDT | 55 | 0.00719207 | 0.39556392 | 11.84225941 | False | False | 12/4/35/4 | 1.13864509 |
| DOGE-USDT | 20 | 0.21426613 | 4.28532269 | 2.68221033 | True | False | 4/0/14/2 | 0.52382933 |

### SUB_B (BTC run 2020-10-01Z → 2021-01-01Z)

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/sell/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|----------------------:|-----------:|
| BTC-USDT | 44 | 0.05405403 | 2.37837731 | 33.55838705 | False | False | 13/10/20/1 | 0.92721802 |
| ETH-USDT | 50 | -0.06145098 | -3.07254893 | 20.8350418 | False | False | 10/18/20/2 | 0.9908799 |
| DOGE-USDT | 37 | -0.01149508 | -0.42531779 | 15.36161462 | False | False | 6/3/26/2 | 0.72671617 |

---

## Honesty vs #130 (15m DT+RVOL FULL)

#130 FULL (15m N4 RVOL>1.2 1H EMA21): BTC 296/−0.0339961/−10.06284485 · ETH 321/−0.02545166/−8.16998247 · DOGE 275/−0.03558125/−9.78484417.

| Inst | n 131 / 130 | exp 131 / 130 | terminal 131 / 130 | Δ exp | Δ terminal |
|------|------------:|--------------:|-------------------:|------:|-----------:|
| BTC-USDT | 78 / 296 | -0.00408787 / -0.0339961 | -0.31885419 / -10.06284485 | 0.02990823 | 9.74399066 |
| ETH-USDT | 105 / 321 | -0.02607385 / -0.02545166 | -2.73775434 / -8.16998247 | -0.00062219 | 5.43222813 |
| DOGE-USDT | 57 / 275 | 0.06612059 / -0.03558125 | 3.7688737 / -9.78484417 | 0.10170184 | 13.55371787 |

**Read:** Different locks (1H + 4H EMA21 + 24-bar time-stop ≠ 15m + 1H EMA21 + 16-bar). Terminals improve vs #130 on all three, but FULL gate still FAIL (0/3 pass vs BH). Not a rescue of #130 via TF grind — coordinator locked a new card.

## Honesty vs #121 Dual Thrust + RVOL 1H FULL

#121 `dual_thrust_rvol` (1H N=20 RVOL>1, no 4H regime, no SL/TP/time-stop): BTC 18 / 0.68658253 / 19.14953712 · ETH 19 / 1.1968212 / 22.73960271 · DOGE 24 / 0.2233388 / 5.36013111 — FAIL vs BH (exp>0, term < BH).

| Inst | n 131 / 121 | exp 131 / 121 | terminal 131 / 121 | Δ exp | Δ terminal |
|------|------------:|--------------:|-------------------:|------:|-----------:|
| BTC-USDT | 78 / 18 | -0.00408787 / 0.68658253 | -0.31885419 / 19.14953712 | -0.6906704 | -19.46839131 |
| ETH-USDT | 105 / 19 | -0.02607385 / 1.1968212 | -2.73775434 / 22.73960271 | -1.22289505 | -25.47735705 |
| DOGE-USDT | 57 / 24 | 0.06612059 / 0.2233388 | 3.7688737 / 5.36013111 | -0.15721821 | -1.59125741 |

**Read:** #131 is **not** a transplant of #121. N=4 RVOL>1.2 + 4H EMA21 + SL/TP/24-bar time-stop ≠ N=20 RVOL>1 naked. Do not claim #121 as #131. On this window #131 underperforms #121 terminals on all three pairs.

---

## What not to rescue

- **No** N / k / RVOL / EMA / TF / R / time-stop grind this run.
- **No** BOS restore / `scalp_structure_bos_*` import.
- **No** Soft PASS → arm.
- **No** #121 number transplant / #130 TF reinterpretation.
- **Leave #130 15m STOP** — do not restore 15m DT params.
- **STOP** — do **not** take **132**.

---

## Confirmation

- `config/default.yaml` untouched.
- phase1/120–130 untouched.
- `place_orders: false` · `not_a_forecast: true` · Soft PASS N/A ≠ arm.
- 4H data path this run: **OKX EEA history-candles** (not resample fallback).
