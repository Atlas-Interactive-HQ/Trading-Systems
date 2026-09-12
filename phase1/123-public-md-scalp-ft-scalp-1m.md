# 123 — Public-MD Scalp: freqtrade Scalp.py 1m Jul2020–Jan2021 (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/123** — native **1m** GPL-cited Scalp.py reimpl. **Do not edit** phase1/120 / 121 / 122 (122 = scout PR #105).

Code: `atlas.strategy.ft_scalp_1m` · `atlas.paper.public_md_scalp_ft_scalp_1m` · script `scripts/run_public_md_scalp_ft_scalp_1m.py`  
Report JSON: `data/reports/public_md_scalp_ft_scalp_1m_123.json` (also `results/public_md_scalp_ft_scalp_1m_123.json`)  
Candle cache: `results/public_md_123_cache/` (gitignored; regenerate via `scripts/_fetch_public_md_123_1m.py`)

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **123** (not 120/121/122) |
| **Source** | freqtrade-strategies `berlinguyinca/Scalp.py` (**GPL-3.0** — **cite + reimplement**; do **not** copy the upstream file into `src`) |
| **Source URL** | https://raw.githubusercontent.com/freqtrade/freqtrade-strategies/master/user_data/strategies/berlinguyinca/Scalp.py |
| **TF** | **1m NATIVE** (EEA history-candles HAS Jul2020–Jan2021 on all three USDT pairs; probed 2026-09-12). **Do NOT adapt to 1H.** |
| **Side** | Long/flat only. `confirm_closed_only`. Fill next-open. |
| **Indicators** | EMA5(high), EMA5(low), STOCHF(5,3,SMA) fastk/fastd, ADX(14) |
| **Entry** | open < EMA5(low) AND ADX>30 AND fastk<30 AND fastd<30 AND fastk crosses above fastd |
| **Exit (indicator)** | open ≥ EMA5(high) OR fastk crosses above 70 OR fastd crosses above 70 |
| **Locked exits** | ROI **+1%** from entry **and** SL **−4%** (source recommends ROI-led sells). Atlas **5+5 bps** still on top. |
| **Insts** | **BTC-USDT / ETH-USDT / DOGE-USDT** only |
| **USD** | **N/A** — do not invent USD bars |
| **Memes** | No PEPE / PUMP / TRUMP / WIF |
| **Sleeve** | Scalp **€20** paper; **one position**; **no** martingale |
| **Honesty — parallel trades** | Source text says “≥60 parallel trades” — **we do NOT do that**; single €20 sleeve |
| **Claimed window in source** | **UNVERIFIED** (no timerange). We **MEASURE** Jul2020→Jan2021 |
| **Clear edge** | completed exp > 0 **AND** terminal beats BH on **FULL** |
| **Soft PASS** | **N/A / not-an-arm** |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |
| **Not this** | No 121 family grind. No S1 transplant. No Mid #71. No 1H adaptation. |

### Candidate ids

| Spot | candidate_id |
|------|----------------|
| BTC-USDT | `public_md_v1_ft_berlinguyinca_scalp_1m_long_flat_btc_usdt_eur20` |
| ETH-USDT | `public_md_v1_ft_berlinguyinca_scalp_1m_long_flat_eth_usdt_eur20` |
| DOGE-USDT | `public_md_v1_ft_berlinguyinca_scalp_1m_long_flat_doge_usdt_eur20` |

### Windows (UTC, exclusive end)

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup fetch from **2020-06-01**. Series n (measured, closed 1m): BTC/ETH/DOGE-USDT = **308160** incl. warmup; FULL trade bars = **264960** each.

---

## Honesty

- **GPL-3.0:** Upstream Scalp.py is cited; Atlas code is an **original reimplementation** of the published rule card (not a verbatim copy of the freqtrade file into `src`).
- **Native 1m:** Not resampled / not adapted to 1H.
- **≥60 parallel trades:** Source recommends covering losses with many parallel sleeves — **not used**. Single €20 sleeve, one position.
- **Claimed window:** Source has no timerange → **UNVERIFIED**. Measured window only.
- **USD N/A / no PEPE / no invented bars.** Fail closed if a series cannot fill the window.
- Soft PASS N/A ≠ arm. Scores ≠ GREEN CANDIDATE ≠ arm. **Do not promote. Do not grind.**

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_ft_scalp_1m_123.json` · costs 5+5 bps · sleeve €20 · next-open · ROI+1% / SL−4% honored.

**any_clear_edge = `False`** · clear_edge_cells_full = `[]` · beats_bh_full = `[]`

| Inst | Window | n bars | n trades | completed exp €/trade | terminal € | BH net € | PASS vs BH | clear edge FULL |
|------|--------|-------:|---------:|----------------------:|-----------:|---------:|:----------:|:---------------:|
| BTC-USDT | FULL | 264960 | 2202 | -0.00887676 | -19.54662696 | 43.17666206 | False | False |
| BTC-USDT | SUB_A_DEFI_SUMMER | 132480 | 1316 | -0.01384656 | -18.22207515 | 3.544385 | False | False |
| BTC-USDT | SUB_B_BTC_RUN | 132480 | 886 | -0.01681706 | -14.89991634 | 33.55838705 | False | False |
| ETH-USDT | FULL | 264960 | 1870 | -0.0101267 | -18.93692516 | 45.16769469 | False | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 132480 | 989 | -0.01567657 | -15.50412902 | 11.84225941 | False | False |
| ETH-USDT | SUB_B_BTC_RUN | 132480 | 881 | -0.01733358 | -15.27088396 | 20.8350418 | False | False |
| DOGE-USDT | FULL | 264960 | 1362 | -0.012813 | -17.45131185 | 20.36962684 | False | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 132480 | 782 | -0.01758146 | -13.74870302 | 2.76085653 | False | False |
| DOGE-USDT | SUB_B_BTC_RUN | 132480 | 580 | -0.02042395 | -11.84588964 | 15.36161462 | False | False |

### Exit attribution (FULL)

| Inst | n ROI exits | n SL exits | n indicator exits | win rate | max DD € |
|------|------------:|-----------:|------------------:|---------:|---------:|
| BTC-USDT | 5 | 1 | 2196 | 0.06494096 | 19.55114125 |
| ETH-USDT | 7 | 1 | 1862 | 0.15561497 | 18.94275864 |
| DOGE-USDT | 31 | 7 | 1324 | 0.25697504 | 17.8688141 |

---

## Gate result

- **Clear edge on FULL:** **NONE** (completed exp **negative** on every FULL cell; terminal loses badly to buy-hold in the 2020 bull).
- High trade count + tiny win rate + fee drag (5+5 bps each way) wipe the sleeve on this path.
- Soft PASS N/A ≠ arm. **Do not promote. Do not grind TF/thresholds/costs. Do not rescue with 1H adaptation or multi-sleeve martingale.**

---

## What this PR does / does not

**Does**

- GPL-cite + reimplement Scalp.py rule card at **native 1m**.
- Score BTC/ETH/DOGE-USDT FULL + SUB A + SUB B with ROI+1% / SL−4% + Atlas 5+5 bps.
- Persist 1m cache under `results/public_md_123_cache/` (fail closed if incomplete).
- Write measured JSON + this phase1/123 note + unit tests.

**Does not**

- Edit phase1/120 / 121 / 122 or `config/default.yaml`.
- Copy the upstream freqtrade `Scalp.py` file into `src`.
- Adapt to 1H / run ≥60 parallel trades / invent bars / score PEPE or USD.
- Transplant S1 / Mid #71 / 121 families.
- Place orders / arm live / apply Soft PASS as arm.

### What not to rescue

- Do **not** flip to 1H to chase #121-style numbers.
- Do **not** enable multi-sleeve / “60 parallel” to paper over expectancy.
- Do **not** grind ADX/STOCH/EMA/ROI/SL after this FAIL.
- Do **not** treat Soft PASS / any positive cell as arm.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.
