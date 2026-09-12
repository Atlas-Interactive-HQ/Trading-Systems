# 127 — Public-MD Scalp: #126 + BOS follow-through + RSI 20–30 / ≥67 Jul2020–Jan2021 (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/127** — locked deltas on [`126-public-md-scalp-structure-bos-long-only.md`](./126-public-md-scalp-structure-bos-long-only.md). **Do not edit** phase1/120–126.
**Parent:** #126 FAIL (0/3). Locked deltas = BOS follow-through + RSI entry band [20,30] + RSI exit ≥67.

Code: `atlas.strategy.scalp_structure_bos_127` · `atlas.paper.public_md_scalp_structure_bos_127` (`walk_structure_bos_127` + reuse `public_md_125_cache`) · script `scripts/run_public_md_scalp_structure_bos_127.py`  
Report JSON: `results/public_md_scalp_structure_bos_127.json` (also `data/reports/…` local)  
Candle cache: **reuse** `results/public_md_125_cache/` (1m/3m/15m) — do not invent bars.

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **127** (not 120–126) |
| **Base** | **#126 long-only**: trade ONLY when 15m structure is **bull (HH+HL)**. **NO shorts**. Flat when bear or unclear/mixed. |
| **Delta 1 — stricter BOS** | Entry only after (a) closed 1m close > active 15m swing high **AND** (b) the **NEXT** closed 1m close ≥ that BOS bar's close (follow-through). **No first-touch / wick-only.** Fill = open of the bar **after** follow-through. |
| **Delta 2 — RSI entry band** | 3m RSI(14) Wilder: long only if RSI ∈ **[20, 30]** inclusive on the 3m bar in force at the signal (**replaces** RSI>50). |
| **Delta 3 — RSI exit** | Close long when 3m RSI **≥ 67** (first closed 3m that prints ≥67). Honesty: if RSI gaps/spikes through 67–75, **still exit on first ≥67** — do not wait for 75. |
| **Keep** | SL = last 15m swing low · TP **1.5R** OR RSI-exit OR opposite BOS, whichever first · **45×1m** time stop failsafe · one entry per BOS/FT event · no re-entry until **NEW** 15m swing |
| **Reuse** | Structure helpers from `scalp_structure_bos_125` · `load_or_fetch_triple` / `public_md_125_cache`. Do **not** edit 120–126. |
| **Doctrine** | Loose/independent Scalp sleeve. Paper only. |
| **TF stack** | **15m** structure · **3m** RSI(14) Wilder · **1m** BOS+FT entry |
| **Pivot N** | **3** |
| **Side** | **Long only**. One position. No martingale. No leverage. |
| **Costs** | PaperSettings **5+5 bps** both ways |
| **Sleeve** | Scalp **€20** · accounting_v2 |
| **Insts** | **BTC-USDT / ETH-USDT / DOGE-USDT** only |
| **USD / Memes** | N/A — no invented bars |
| **3m data** | Native EEA via #125 cache (probed) |
| **PASS** | completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs on **FULL**. Else FAIL / no promote. |
| **Soft PASS** | **N/A / not-an-arm** |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |

### Candidate ids

| Spot | candidate_id |
|------|----------------|
| BTC-USDT | `public_md_v1_structure_bos_15m_rsi3m_1m_long_only_ft_rsi_bands_btc_usdt_eur20` |
| ETH-USDT | `public_md_v1_structure_bos_15m_rsi3m_1m_long_only_ft_rsi_bands_eth_usdt_eur20` |
| DOGE-USDT | `public_md_v1_structure_bos_15m_rsi3m_1m_long_only_ft_rsi_bands_doge_usdt_eur20` |

### Windows (UTC, exclusive end) — same as #126

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup from **2020-06-01**. Series n (cache_125): 1m **308160** / FULL trade **264960**; 15m **20544**; 3m **102720** native.

---

## Honesty

- BOS follow-through alone still leaves hundreds of candidate arms; the **RSI ∈ [20,30]** band at the FT signal is the killer filter in this 2020 bull window.
- Diagnostic (BTC FULL, not a score): ~456 BOS arms · ~241 FT price-OK · **0** with RSI in [20,30] at FT (RSI at FT price-OK: min≈41, median≈67, all >30). Same empty sample on ETH/DOGE.
- Zero trades ⇒ completed exp is **null** (not >0) · terminal **0** ≪ BH. Soft PASS N/A ≠ arm. Scores ≠ GREEN CANDIDATE ≠ arm. **Do not promote. Do not grind.**

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_structure_bos_127.json` · costs 5+5 bps · sleeve €20 · next-open after FT · SL / 1.5R / RSI≥67 / opp-BOS / time-stop 45 · accounting_v2 · generated `2026-09-12T09:16:34Z` (11:16 PT / Europe/Amsterdam).

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

### FULL (PASS gate window)

| Inst | n bars | n trades | long / short | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL |
|------|-------:|---------:|-------------:|----------------------:|-----------:|---------:|:----------:|:--------------:|
| BTC-USDT | 264960 | **0** | 0 / **0** | null | 0.0 | 43.17666206 | False | False |
| ETH-USDT | 264960 | **0** | 0 / **0** | null | 0.0 | 45.16769469 | False | False |
| DOGE-USDT | 264960 | **0** | 0 / **0** | null | 0.0 | 20.36962684 | False | False |

### FULL exit attribution (#127)

| Inst | n TP | n SL | n opp-BOS | n rsi_exit | n time-stop | win rate | fee drag € | max DD € |
|------|-----:|-----:|----------:|-----------:|------------:|---------:|-----------:|---------:|
| BTC-USDT | 0 | 0 | 0 | 0 | 0 | null | 0 | 0 |
| ETH-USDT | 0 | 0 | 0 | 0 | 0 | null | 0 | 0 |
| DOGE-USDT | 0 | 0 | 0 | 0 | 0 | null | 0 | 0 |

### Explicit vs #126 compare (FULL)

| Inst | n trades 127 | n trades 126 | **drop** | long 127/126 | short 127/126 | exp 127 | exp 126 | terminal 127 | terminal 126 | exit mix 127 (TP/SL/opp/rsi/time) | exit mix 126 (TP/SL/opp/time) |
|------|-------------:|-------------:|---------:|-------------:|--------------:|--------:|--------:|-------------:|-------------:|----------------------------------:|------------------------------:|
| BTC-USDT | 0 | 339 | **339** | 0/339 | **0**/0 | null | -0.02643514 | 0.0 | -8.96151151 | 0/0/0/0/0 | 12/13/5/309 |
| ETH-USDT | 0 | 337 | **337** | 0/337 | **0**/0 | null | -0.0213103 | 0.0 | -7.18156963 | 0/0/0/0/0 | 11/15/7/304 |
| DOGE-USDT | 0 | 222 | **222** | 0/222 | **0**/0 | null | -0.02695481 | 0.0 | -5.98396709 | 0/0/0/0/0 | 6/14/1/201 |

Notes: #126 already long-only. #127 adds FT + RSI[20,30] entry + RSI≥67 exit. Sample collapses to **zero** completed trades on every FULL cell — not a coding miss; FT price-OK events exist, but none coincide with RSI ∈ [20,30] under 15m bull in this window.

### SUB A / SUB B (informational; not the gate)

| Inst | Window | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH |
|------|--------|---------:|----------------------:|-----------:|---------:|:----------:|
| BTC-USDT | SUB_A_DEFI_SUMMER | 0 | null | 0.0 | 3.544385 | False |
| BTC-USDT | SUB_B_BTC_RUN | 0 | null | 0.0 | 33.55838705 | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 0 | null | 0.0 | 11.84225941 | False |
| ETH-USDT | SUB_B_BTC_RUN | 0 | null | 0.0 | 20.8350418 | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 0 | null | 0.0 | 2.76085653 | False |
| DOGE-USDT | SUB_B_BTC_RUN | 0 | null | 0.0 | 15.36161462 | False |

### 3m / cache probe stamp

| Inst | 1m/15m/3m source | 3m native | n 3m |
|------|------------------|:---------:|-----:|
| BTC-USDT | cache_125 | True | 102720 |
| ETH-USDT | cache_125 | True | 102720 |
| DOGE-USDT | cache_125 | True | 102720 |

---

## Gate result (2/3 rule)

- **PASS requires** completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs on FULL.
- **Measured:** **0 / 3** pairs pass. Completed exp **null** on every FULL cell (0 trades); terminal 0 still far below buy-hold.
- **Verdict: FAIL / no promote.**
- Parent #126 also FAIL 0/3. Locked RSI band + FT removes the entire long sample in this bull window.
- Soft PASS N/A ≠ arm. **Do not promote.**

---

## What NOT to rescue

- Do **not** widen/shift the RSI entry band (e.g. back toward >50, or [30,40], or any grind).
- Do **not** drop follow-through or restore first-touch BOS.
- Do **not** change RSI exit to wait for 75, or grind exit threshold.
- Do **not** grind pivot N, RSI period, TFs, R-multiple, or time-stop bars.
- Do **not** restore shorts / transplant #125–#126 scores into a promote narrative.
- Do **not** transplant S1 / #121 / #123 / #124 / Mid #71.
- Do **not** run ≥60 parallel trades or martingale / leverage.
- Do **not** invent USD / meme bars or drop costs.
- Do **not** treat Soft PASS / scores / flat terminal=0 as an arm gate.

---

## What this PR does / does not

**Does**

- Add #127 strategy (FT BOS + RSI[20,30] entry + RSI≥67 exit) on #126 long-only base.
- Reuse #125 structure helpers + `public_md_125_cache`; new walker with `rsi_exit` attribution.
- Score BTC/ETH/DOGE-USDT FULL + SUB A + SUB B; write measured JSON + this phase1/127 note + unit tests (FT required, RSI band in, RSI≥67 out, no shorts, PASS gate).

**Does not**

- Edit phase1/120–126 or `config/default.yaml`.
- Place orders / arm / promote.
- Grind locked deltas to force a non-empty sample.
