# 124 — Public-MD Scalp: guibvieira ScalpingCCI 15m Jul2020–Jan2021 (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/124** — native **15m** GPL-cited ScalpingCCI reimpl. **Do not edit** phase1/120 / 121 / 122 / 123 (123 = PR #106 Scalp.py 1m FAIL).

Code: `atlas.strategy.scalping_cci_15m` · `atlas.paper.public_md_scalp_scalpingcci_15m` · script `scripts/run_public_md_scalp_scalpingcci_15m.py`  
Report JSON: `results/public_md_scalp_scalpingcci_15m_124.json` (also `data/reports/…` local)  
Candle cache: `results/public_md_124_cache/` (gitignored; regenerate via `scripts/_fetch_public_md_124_15m.py`)

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **124** (not 120/121/122/123) |
| **Source** | guibvieira `ScalpingCCI.py` (**GPL-3.0** — **cite + reimplement**; do **not** copy the upstream file into `src`) |
| **Source URL** | https://raw.githubusercontent.com/guibvieira/freqtrade-crypto/master/user_data/strategies/ScalpingCCI.py |
| **TF** | **15m NATIVE** (`ticker_interval='15'`; EEA history-candles HAS Jul2020–Jan2021). **Do NOT adapt to 1H.** |
| **Side** | Long/flat only. `confirm_closed_only`. Fill next-open. |
| **Indicators** | EMA20(close), MACD(12,26,9), daily resample ×96: pivot=(H+L+C)/3, bc=(H+L)/2, **tc=(pivot−bc)/2** (FILE formula; comment's classic TC ignored), high_daily |
| **Entry (FILE)** | close > EMA20 AND MACD crosses above signal AND close > pivot/bc/tc AND pivot > pivot.shift(97) AND bc > bc.shift(97) AND **close > tc.shift(97)** (FILE — not close rising) |
| **Exit (indicator)** | open ≥ 0.98 × high_daily OR MACD crosses below signal |
| **Locked exits** | Source **ROI ladder** 0→2%, 10→5%, 20→4%, 60→30%, 120→20% **and** SL **−4%**. Atlas **5+5 bps** still on top. |
| **ROI honesty** | On 15m bars the first close after fill is already ≥15 minutes held → first ROI rung seen is **5%** (10-minute key), not 2%. Measured: almost all exits are indicator. |
| **Insts** | **BTC-USDT / ETH-USDT / DOGE-USDT** only |
| **USD** | **N/A** — do not invent USD bars |
| **Memes** | No PEPE / PUMP / TRUMP / WIF |
| **Sleeve** | Scalp **€20** paper; **one position**; **no** martingale |
| **Honesty — parallel trades** | Source text says “≥60 parallel trades” — **we do NOT do that**; single €20 sleeve |
| **Claimed window in source** | **UNVERIFIED** (no timerange). We **MEASURE** Jul2020→Jan2021 |
| **Clear edge** | completed exp > 0 **AND** terminal beats BH on **FULL** |
| **Soft PASS** | **N/A / not-an-arm** |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |
| **Not this** | No 121 family grind. No S1 transplant. No Mid #71. No 1H adaptation. No 123 param-rescue. |

### Candidate ids

| Spot | candidate_id |
|------|----------------|
| BTC-USDT | `public_md_v1_guibvieira_scalping_cci_15m_long_flat_btc_usdt_eur20` |
| ETH-USDT | `public_md_v1_guibvieira_scalping_cci_15m_long_flat_eth_usdt_eur20` |
| DOGE-USDT | `public_md_v1_guibvieira_scalping_cci_15m_long_flat_doge_usdt_eur20` |

### Windows (UTC, exclusive end)

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup fetch from **2020-06-01**. Series n (measured, closed 15m): BTC/ETH/DOGE-USDT = **20544** incl. warmup; FULL trade bars = **17664** each.

---

## Honesty

- **GPL-3.0:** Upstream ScalpingCCI.py is cited; Atlas code is an **original reimplementation** of the published rule card (not a verbatim copy of the freqtrade file into `src`).
- **FILE wins:** tc=(pivot−bc)/2; entry uses close > tc.shift(97) (dossier paraphrase “close rising” rejected).
- **Native 15m:** Not resampled / not adapted to 1H.
- **≥60 parallel trades:** Source recommends covering losses with many parallel sleeves — **not used**. Single €20 sleeve, one position.
- **Claimed window:** Source has no timerange → **UNVERIFIED**. Measured window only.
- **Causal daily levels:** running UTC-day OHLC through the current 15m bar (no future bars within the day).
- **USD N/A / no PEPE / no invented bars.** Fail closed if a series cannot fill the window.
- Soft PASS N/A ≠ arm. Scores ≠ GREEN CANDIDATE ≠ arm. **Do not promote. Do not grind.**

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_scalpingcci_15m_124.json` · costs 5+5 bps · sleeve €20 · next-open · ROI ladder + SL−4% honored.

**any_clear_edge = `False`** · clear_edge_cells_full = `[]` · beats_bh_full = `[]`

| Inst | Window | n bars | n trades | completed exp €/trade | terminal € | BH net € | PASS vs BH | clear edge FULL |
|------|--------|-------:|---------:|----------------------:|-----------:|---------:|:----------:|:---------------:|
| BTC-USDT | FULL | 17664 | 18 | -0.07565196 | -1.36173524 | 43.17666206 | False | False |
| BTC-USDT | SUB_A_DEFI_SUMMER | 8832 | 3 | 0.01919597 | 0.05758792 | 3.544385 | False | False |
| BTC-USDT | SUB_B_BTC_RUN | 8832 | 15 | -0.09434987 | -1.41524808 | 33.55838705 | False | False |
| ETH-USDT | FULL | 17664 | 25 | -0.0174802 | -0.43700501 | 45.16769469 | False | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 8832 | 13 | 0.02314937 | 0.30094186 | 11.84225941 | False | False |
| ETH-USDT | SUB_B_BTC_RUN | 8832 | 12 | -0.06058396 | -0.72700754 | 20.8350418 | False | False |
| DOGE-USDT | FULL | 17664 | 73 | -0.09096194 | -6.64022128 | 20.36962684 | False | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 8832 | 30 | -0.03914808 | -1.17444244 | 2.76085653 | False | False |
| DOGE-USDT | SUB_B_BTC_RUN | 8832 | 43 | -0.13504103 | -5.80676437 | 15.36161462 | False | False |

### Exit attribution (FULL)

| Inst | n ROI exits | n SL exits | n indicator exits | win rate | max DD € |
|------|------------:|-----------:|------------------:|---------:|---------:|
| BTC-USDT | 0 | 0 | 18 | 0.27777778 | 1.79338985 |
| ETH-USDT | 1 | 0 | 24 | 0.44 | 1.55310186 |
| DOGE-USDT | 1 | 1 | 71 | 0.21917808 | 8.14316421 |

---

## Gate result

- **Clear edge on FULL:** **NONE** (completed exp **negative** on every FULL cell; terminal loses badly to buy-hold in the 2020 bull).
- SUB_A shows tiny positive completed exp on BTC/ETH but **does not** beat BH — Soft PASS N/A ≠ arm; not a rescue signal.
- Sparse entries (pivot/MACD/EMA confluence) + fee drag + bull-market BH crush this path.
- Soft PASS N/A ≠ arm. **Do not promote. Do not grind TF/thresholds/ROI/SL. Do not rescue with 1H adaptation or multi-sleeve martingale. Do not param-rescue from #123.**

---

## What this PR does / does not

**Does**

- GPL-cite + reimplement ScalpingCCI.py rule card at **native 15m**.
- Score BTC/ETH/DOGE-USDT FULL + SUB A + SUB B with source ROI ladder + SL−4% + Atlas 5+5 bps.
- Persist 15m cache under `results/public_md_124_cache/` (fail closed if incomplete).
- Write measured JSON + this phase1/124 note + unit tests.

**Does not**

- Edit phase1/120 / 121 / 122 / 123 or `config/default.yaml`.
- Copy the upstream freqtrade `ScalpingCCI.py` file into `src`.
- Adapt to 1H / run ≥60 parallel trades / invent bars / score PEPE or USD.
- Transplant S1 / Mid #71 / 121 families / 123 param-rescue.
- Place orders / arm live / apply Soft PASS as arm.

### What not to rescue

- Do **not** flip to 1H to chase #121-style numbers.
- Do **not** enable multi-sleeve / “60 parallel” to paper over expectancy.
- Do **not** grind EMA/MACD/pivot/ROI/SL after this FAIL.
- Do **not** treat Soft PASS / any positive SUB cell as arm.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.
