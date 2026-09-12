# 125 — Public-MD Scalp: 15m structure + 3m RSI + 1m BOS Jul2020–Jan2021 (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/125** — loose/independent Scalp sleeve (structure BOS). **Do not edit** phase1/120–124.
**Supersedes:** Freqtrade shortlist STOP (scout #122 path). Paper only.

Code: `atlas.strategy.scalp_structure_bos_125` · `atlas.paper.public_md_scalp_structure_bos_125` · script `scripts/run_public_md_scalp_structure_bos_125.py`  
Report JSON: `results/public_md_scalp_structure_bos_125.json` (also `data/reports/…` local)  
Candle cache: `results/public_md_125_cache/` (gitignored; regenerate via `scripts/_fetch_public_md_125.py`)

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **125** (not 120–124) |
| **Doctrine** | Loose/independent Scalp sleeve. Paper only. |
| **TF stack** | **15m** structure · **3m** RSI(14) Wilder · **1m** BOS entry |
| **Pivot N** | **3** (swing high = high strictly > N each side; swing low = low strictly < N each side; confirm after right-side N closes) |
| **Bias** | Bull iff HH+HL; Bear iff LH+LL; mixed / insufficient = **FLAT** (no entry) |
| **RSI gate** | Long only if RSI>50 under bull; short only if RSI<50 under bear; contradict → flat |
| **Entry** | Closed 1m BOS: bull close > active 15m last swing high; bear close < active 15m last swing low. `confirm_closed_only`. Fill **next 1m open**. |
| **One entry / BOS** | One entry per BOS event; no re-entry until a **NEW** 15m swing confirms (updates active extreme) |
| **Side** | Long **and** short when bias+RSI align. **One position**. No martingale. No leverage. |
| **SL** | Beyond opposite 15m swing (long SL = last swing low; short SL = last swing high). Invalidation. Fixed at entry. |
| **TP** | **1.5R** (R = \|entry−SL\|) **OR** opposite BOS (closed 1m through opposite 15m extreme), whichever first |
| **Time stop** | **45** closed 1m bars max. Convention: signal at close of Nth held bar → **fill next open** (`signal_at_close_of_nth_held_bar_fill_next_open`) |
| **Costs** | PaperSettings **5+5 bps** both ways |
| **Sleeve** | Scalp **€20** · accounting_v2 (completed exp + terminal liquidation) |
| **Insts** | **BTC-USDT / ETH-USDT / DOGE-USDT** only |
| **USD** | **N/A** — do not invent USD bars |
| **Memes** | No PEPE / PUMP / TRUMP / WIF |
| **3m data** | Prefer native EEA history-candles; if missing, resample **CLOSED** 1m→3m (do not invent). Probe + stamp. |
| **PASS** | completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs on **FULL**. Else FAIL / no promote. |
| **Soft PASS** | **N/A / not-an-arm** |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |
| **GPL** | **unused** (no freqtrade file transplant) |
| **Not this** | No grind of RSI period / pivot N / TFs / R-multiple / time-stop. No 60-parallel. No S1 / #121 / #123 / #124 transplant. No Mid #71. |

### Candidate ids

| Spot | candidate_id |
|------|----------------|
| BTC-USDT | `public_md_v1_structure_bos_15m_rsi3m_1m_long_short_btc_usdt_eur20` |
| ETH-USDT | `public_md_v1_structure_bos_15m_rsi3m_1m_long_short_eth_usdt_eur20` |
| DOGE-USDT | `public_md_v1_structure_bos_15m_rsi3m_1m_long_short_doge_usdt_eur20` |

### Windows (UTC, exclusive end)

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup fetch from **2020-06-01**. Series n (measured): 1m **308160** incl. warmup / FULL trade **264960**; 15m **20544** / **17664**; 3m **102720** / **88320** (native EEA, probed 2026-09-12).

---

## Honesty

- **Fee/slippage on 1m:** 5+5 bps both ways on every entry/exit fill (next-open). High time-stop exit share → fee drag compounds.
- **Mixed structure = flat:** HH+LL / LH+HL / insufficient swings → no entry.
- **No 60-parallel:** single €20 sleeve, one position.
- **No S1 / #121 / #123 / #124 transplant.** No Mid #71.
- **GPL unused:** original Atlas rule card (not a freqtrade file copy).
- **USD N/A / no PEPE / no invented bars.** Fail closed if a series cannot fill the window.
- Soft PASS N/A ≠ arm. Scores ≠ GREEN CANDIDATE ≠ arm. **Do not promote. Do not grind.**

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_structure_bos_125.json` · costs 5+5 bps · sleeve €20 · next-open · SL / 1.5R / opp-BOS / time-stop 45 · accounting_v2.

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

### FULL (PASS gate window)

| Inst | n bars | n trades | long / short entries | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL |
|------|-------:|---------:|---------------------:|----------------------:|-----------:|---------:|:----------:|:--------------:|
| BTC-USDT | 264960 | 582 | 339 / 243 | -0.02604903 | -15.1605353 | 43.17666206 | False | False |
| ETH-USDT | 264960 | 545 | 337 / 209 | -0.02132098 | -11.645816 | 45.16769469 | False | False |
| DOGE-USDT | 264960 | 399 | 222 / 177 | -0.02444921 | -9.75523652 | 20.36962684 | False | False |

### FULL exit attribution

| Inst | n TP | n SL | n opp-BOS | n time-stop | win rate | fee drag € | max DD € |
|------|-----:|-----:|----------:|------------:|---------:|-----------:|---------:|
| BTC-USDT | 21 | 29 | 7 | 525 | 0.2371134 | 6.48103028 | 15.27102601 |
| ETH-USDT | 22 | 23 | 13 | 487 | 0.34311927 | 7.24305301 | 11.82403258 |
| DOGE-USDT | 16 | 28 | 2 | 353 | 0.29323308 | 6.59184493 | 17.01395969 |

### SUB A / SUB B (informational; not the gate)

| Inst | Window | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH |
|------|--------|---------:|----------------------:|-----------:|---------:|:----------:|
| BTC-USDT | SUB_A_DEFI_SUMMER | 283 | -0.03150779 | -8.92137242 | 3.544385 | False |
| BTC-USDT | SUB_B_BTC_RUN | 298 | -0.03788811 | -11.29065687 | 33.55838705 | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 284 | -0.02607138 | -7.40427181 | 11.84225941 | False |
| ETH-USDT | SUB_B_BTC_RUN | 261 | -0.02564672 | -6.73489313 | 20.8350418 | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 209 | -0.01933109 | -4.04019756 | 2.76085653 | False |
| DOGE-USDT | SUB_B_BTC_RUN | 190 | -0.03769364 | -7.16179164 | 15.36161462 | False |

### 3m probe stamp

| Inst | 3m source | native | n 3m (incl. warmup) |
|------|-----------|:------:|--------------------:|
| BTC-USDT | eea history-candles (cache_125) | True | 102720 |
| ETH-USDT | eea history-candles (cache_125) | True | 102720 |
| DOGE-USDT | eea history-candles (cache_125) | True | 102720 |

1m copied from #123 cache; 15m copied from #124 cache; 3m fetched native EEA (2026-09-12).

---

## Gate result (2/3 rule)

- **PASS requires** completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs on FULL.
- **Measured:** **0 / 3** pairs pass. Completed exp **negative** on every FULL cell; terminal loses badly to buy-hold in the 2020 bull.
- **Verdict: FAIL / no promote.**
- Dominant exit is **time-stop (45×1m)**; fee/slippage on 1m + adverse short exposure in a bull regime wipe the €20 sleeve.
- Soft PASS N/A ≠ arm. **Do not promote. Do not grind pivot N / RSI period / TFs / R-multiple / time-stop.**

---

## What NOT to rescue

- Do **not** grind RSI period, pivot N, timeframes, R-multiple, or time-stop bars.
- Do **not** transplant S1 / #121 families / #123 Scalp.py / #124 ScalpingCCI / Mid #71.
- Do **not** run ≥60 parallel trades or martingale / leverage.
- Do **not** adapt to 1H to “save” the score.
- Do **not** invent USD / meme bars or drop costs.
- Do **not** treat Soft PASS / scores as an arm gate.

---

## What this PR does / does not

**Does**

- Implement locked 15m structure + 3m RSI + 1m BOS long/short paper sleeve.
- Score BTC/ETH/DOGE-USDT FULL + SUB A + SUB B with SL / 1.5R / opp-BOS / time-stop 45 + Atlas 5+5 bps + accounting_v2.
- Persist 1m/15m/3m cache under `results/public_md_125_cache/` (fail closed if incomplete).
- Write measured JSON + this phase1/125 note + unit tests (pivot confirm, HH/HL vs LH/LL, RSI gate, one-entry-per-BOS, exits, PASS gate 2/3).

**Does not**

- Edit phase1/120–124 or `config/default.yaml`.
- Place orders / arm live / apply Soft PASS as arm.
- Grind locked knobs or rescue with transplants.
