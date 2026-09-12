# 130 — Public-MD Scalp: Dual Thrust N4 + RVOL 15m + 1H EMA21 (Jul2020–Jan2021 €20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/130** — **NEW family** (not a BOS rung, not a #121 transplant). **Do not edit** phase1/120–129.
**Lineage STOP:** phase1/125–129 structure-BOS (15m MS + 1m BOS) is **dead** under 5+5 bps on this window. Do **not** extend with more BOS rungs. Do **not** import `scalp_structure_bos_*`.

Code: `atlas.strategy.scalp_dt_rvol_15m_130` · `atlas.paper.public_md_scalp_dt_rvol_15m_130` · script `scripts/run_public_md_scalp_dt_rvol_15m_130.py`  
Report JSON: `results/public_md_scalp_dt_rvol_15m_130.json` (also `data/reports/…`)  
Candle cache: **reuse** `results/public_md_125_cache/*_15m.jsonl` + `data/paper/candles/public_md_121/*_1H.jsonl` — do not invent bars.

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **130** (not 120–129) |
| **Regime** | 1H close > EMA(21) → long-only eligible; else flat (**no shorts**) |
| **Setup TF** | **15m Dual Thrust** N=4, k1=k2=0.5; range = HH(N)−LL(N) over *prior* N bars exclusive of decision bar (`prior_hh_ll_range` / `ranges_at`) |
| **Entry** | closed 15m close > BuyLine **AND** RVOL(20) > 1.2; fill = next 15m open; one position |
| **RVOL** | volume / SMA(volume, 20) via `atlas.strategy.rvol.rvol_series` |
| **SL** | SellLine **at entry**; if not strictly below entry → entry − 1×ATR(14) Wilder 15m; if still not below → **skip** entry (fail closed) |
| **TP / exits** | 1.5R **OR** closed close < **current-bar** SellLine (whichever first); honor SL; time-stop **16** × 15m (~4h) |
| **Costs** | sleeve €20 · PaperSettings **5+5 bps** · accounting_v2 · confirm_closed_only · no martingale · no leverage |
| **Universe** | BTC-USDT / ETH-USDT / DOGE-USDT. USD N/A. Memes N/A. |
| **PASS (FULL)** | completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs. Else FAIL / no promote. Soft PASS N/A. |
| **No grind** | Do **not** grind N / k / RVOL / EMA / R / time-stop this run. |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |
| **STOP** | Do **not** take 131. |

### Candidate id

`public_md_v1_dt_n4_k0505_rvol20_gt12_ema21_1h_regime_15m_{btc|eth|doge}_usdt_eur20`

### Windows (UTC, exclusive end)

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup from **2020-06-01**. Series n (measured): 15m **20544** / FULL trade **17664**; 1H **5136** per pair.

---

## Gate

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`  
Soft PASS = **N/A ≠ Scalp-arm** · `not_a_forecast` · no promote.

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_dt_rvol_15m_130.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T14:36:55Z` (2026-09-12T16:36:55 PT / Europe/Amsterdam).

Exit mix = **TP / SL / sellline / time-stop**.

### FULL

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/sell/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|----------------------:|-----------:|
| BTC-USDT | 296 | -0.0339961 | -10.06284485 | 43.17666206 | False | False | 46/60/135/55 | 4.81986114 |
| ETH-USDT | 321 | -0.02545166 | -8.16998247 | 45.16769469 | False | False | 49/50/160/62 | 5.12133678 |
| DOGE-USDT | 275 | -0.03558125 | -9.78484417 | 20.36962684 | False | False | 44/58/123/50 | 3.89034027 |

### SUB_A (DeFi summer → 2020-10-01Z)

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/sell/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|----------------------:|-----------:|
| BTC-USDT | 130 | -0.02399371 | -3.1191817 | 3.544385 | False | False | 20/26/54/30 | 2.46732949 |
| ETH-USDT | 161 | -0.0274718 | -4.4263823 | 11.84225941 | False | False | 24/24/81/32 | 2.85750738 |
| DOGE-USDT | 117 | -0.05135827 | -6.00891772 | 2.76085653 | False | False | 16/19/57/25 | 2.11292969 |

### SUB_B (BTC run 2020-10-01Z → 2021-01-01Z)

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/sell/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|----------------------:|-----------:|
| BTC-USDT | 166 | -0.04955837 | -8.2266894 | 33.55838705 | False | False | 26/34/81/25 | 2.78722412 |
| ETH-USDT | 159 | -0.03003968 | -4.77630875 | 20.8350418 | False | False | 25/26/78/30 | 2.90324848 |
| DOGE-USDT | 158 | -0.03416214 | -5.3976189 | 15.36161462 | False | False | 28/39/66/25 | 2.54077646 |

---

## Honesty vs #126 (structure-BOS long-only FULL)

#126 baselines (n / exp / terminal): BTC 339/−0.02643514/−8.96151151 · ETH 337/−0.0213103/−7.18156963 · DOGE 222/−0.02695481/−5.98396709.

| Inst | n 130 / 126 | exp 130 / 126 | terminal 130 / 126 | Δ exp | Δ terminal |
|------|------------:|--------------:|-------------------:|------:|-----------:|
| BTC-USDT | 296 / 339 | -0.0339961 / -0.02643514 | -10.06284485 / -8.96151151 | -0.00756096 | -1.10133334 |
| ETH-USDT | 321 / 337 | -0.02545166 / -0.0213103 | -8.16998247 / -7.18156963 | -0.00414136 | -0.98841284 |
| DOGE-USDT | 275 / 222 | -0.03558125 / -0.02695481 | -9.78484417 / -5.98396709 | -0.00862644 | -3.80087708 |

**Read:** #130 does **not** beat #126 on expectancy or terminal on any pair. Different family (DT+RVOL 15m + 1H EMA21) — not a BOS rescue.

## Honesty vs #121 Dual Thrust + RVOL 1H FULL

#121 `dual_thrust_rvol` (1H N=20 RVOL>1 — different TF/N/gate): BTC 18 / 0.68658253 / 19.14953712 · ETH 19 / 1.1968212 / 22.73960271 · DOGE 24 / 0.2233388 / 5.36013111 — all FAIL vs BH (exp>0 but term < BH).

| Inst | n 130 / 121 | exp 130 / 121 | terminal 130 / 121 | Δ exp | Δ terminal |
|------|------------:|--------------:|-------------------:|------:|-----------:|
| BTC-USDT | 296 / 18 | -0.0339961 / 0.68658253 | -10.06284485 / 19.14953712 | -0.72057863 | -29.21238197 |
| ETH-USDT | 321 / 19 | -0.02545166 / 1.1968212 | -8.16998247 / 22.73960271 | -1.22227286 | -30.90958518 |
| DOGE-USDT | 275 / 24 | -0.03558125 / 0.2233388 | -9.78484417 / 5.36013111 | -0.25892005 | -15.14497528 |

**Read:** #130 is **not** a transplant of #121. 15m N=4 RVOL>1.2 + 1H EMA21 ≠ 1H N=20 RVOL>1. Do not claim #121 as #130. On this window #130 expectancy is negative vs #121's positive-but-below-BH terminals.

---

## What not to rescue

- **No** N / k / RVOL / EMA / R / time-stop grind this run.
- **No** BOS restore / `scalp_structure_bos_*` import.
- **No** Soft PASS → arm.
- **No** #121 number transplant / TF reinterpretation.
- **STOP** — do **not** take **131**.

---

## Confirmation

- `config/default.yaml` untouched.
- phase1/120–129 untouched.
- `place_orders: false` · `not_a_forecast: true` · Soft PASS N/A ≠ arm.
