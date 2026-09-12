# 126 — Public-MD Scalp: #125 long-only 15m-bull strengthen Jul2020–Jan2021 (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/126** — strengthen of [`125-public-md-scalp-structure-bos.md`](./125-public-md-scalp-structure-bos.md). **Do not edit** phase1/120–125.
**Parent:** #125 FAIL (0/3). Locked delta = **long_only** flag only.

Code: `atlas.strategy.scalp_structure_bos_126` (wraps `scalp_structure_bos_125`) · `atlas.paper.public_md_scalp_structure_bos_126` (reuses `walk_structure_bos` + `public_md_125_cache`) · script `scripts/run_public_md_scalp_structure_bos_126.py`  
Report JSON: `results/public_md_scalp_structure_bos_126.json` (also `data/reports/…` local)  
Candle cache: **reuse** `results/public_md_125_cache/` (1m/3m/15m) — do not invent bars.

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **126** (not 120–125) |
| **Delta vs #125** | **`long_only=True`** — trade ONLY when 15m structure is **bull (HH+HL)**. **NO shorts**. Flat when bear or unclear/mixed. Everything else IDENTICAL. |
| **Reuse** | `atlas.strategy.scalp_structure_bos_125` precompute + `walk_structure_bos` walker. Add flag; **do not copy-paste grind**. |
| **Doctrine** | Loose/independent Scalp sleeve. Paper only. |
| **TF stack** | **15m** structure · **3m** RSI(14) Wilder · **1m** BOS entry |
| **Pivot N** | **3** (same as #125) |
| **Bias** | Bull iff HH+HL → long eligible; Bear / mixed / insufficient = **FLAT** (no entry; shorts suppressed) |
| **RSI gate** | Long only if RSI>50 under bull (unchanged). Short path disabled. |
| **Entry** | Closed 1m BOS: bull close > active 15m last swing high. `confirm_closed_only`. Fill **next 1m open**. |
| **One entry / BOS** | One entry per BOS event; no re-entry until a **NEW** 15m swing confirms |
| **Side** | **Long only**. One position. No martingale. No leverage. |
| **SL** | Last 15m swing low (same as #125 long). Fixed at entry. |
| **TP** | **1.5R** OR opposite BOS, whichever first (same as #125) |
| **Time stop** | **45** closed 1m bars · `signal_at_close_of_nth_held_bar_fill_next_open` |
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
| BTC-USDT | `public_md_v1_structure_bos_15m_rsi3m_1m_long_only_btc_usdt_eur20` |
| ETH-USDT | `public_md_v1_structure_bos_15m_rsi3m_1m_long_only_eth_usdt_eur20` |
| DOGE-USDT | `public_md_v1_structure_bos_15m_rsi3m_1m_long_only_doge_usdt_eur20` |

### Windows (UTC, exclusive end) — same as #125

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup from **2020-06-01**. Series n (cache_125): 1m **308160** / FULL trade **264960**; 15m **20544**; 3m **102720** native.

---

## Honesty

- Long-only removes short exposure in a 2020 bull regime → fewer trades, less fee drag, **less-bad** terminal — still **negative expectancy** and still loses to buy-hold.
- Soft PASS N/A ≠ arm. Scores ≠ GREEN CANDIDATE ≠ arm. **Do not promote. Do not grind.**
- No transplant of #125 scores into a promote narrative.

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_structure_bos_126.json` · costs 5+5 bps · sleeve €20 · next-open · SL / 1.5R / opp-BOS / time-stop 45 · accounting_v2 · generated `2026-09-12T08:40:44Z` (10:40 PT / Europe/Amsterdam).

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

### FULL (PASS gate window)

| Inst | n bars | n trades | long / short | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL |
|------|-------:|---------:|-------------:|----------------------:|-----------:|---------:|:----------:|:--------------:|
| BTC-USDT | 264960 | 339 | 339 / **0** | -0.02643514 | -8.96151151 | 43.17666206 | False | False |
| ETH-USDT | 264960 | 337 | 337 / **0** | -0.0213103 | -7.18156963 | 45.16769469 | False | False |
| DOGE-USDT | 264960 | 222 | 222 / **0** | -0.02695481 | -5.98396709 | 20.36962684 | False | False |

### FULL exit attribution (#126)

| Inst | n TP | n SL | n opp-BOS | n time-stop | win rate | fee drag € | max DD € |
|------|-----:|-----:|----------:|------------:|---------:|-----------:|---------:|
| BTC-USDT | 12 | 13 | 5 | 309 | 0.26253687 | 5.24582919 | 10.22242932 |
| ETH-USDT | 11 | 15 | 7 | 304 | 0.35014837 | 5.49520016 | 7.47079019 |
| DOGE-USDT | 6 | 14 | 1 | 201 | 0.28828829 | 4.06396754 | 11.67676793 |

### Explicit vs #125 compare (FULL)

| Inst | n trades 126 | n trades 125 | **drop** | long 126/125 | short 126/125 | exp 126 | exp 125 | terminal 126 | terminal 125 | exit mix 126 (TP/SL/opp/time) | exit mix 125 |
|------|-------------:|-------------:|---------:|-------------:|--------------:|--------:|--------:|-------------:|-------------:|------------------------------:|-------------:|
| BTC-USDT | 339 | 582 | **243** | 339/339 | **0**/243 | -0.02643514 | -0.02604903 | -8.96151151 | -15.1605353 | 12/13/5/309 | 21/29/7/525 |
| ETH-USDT | 337 | 545 | **208** | 337/337 | **0**/209 | -0.0213103 | -0.02132098 | -7.18156963 | -11.645816 | 11/15/7/304 | 22/23/13/487 |
| DOGE-USDT | 222 | 399 | **177** | 222/222 | **0**/177 | -0.02695481 | -0.02444921 | -5.98396709 | -9.75523652 | 6/14/1/201 | 16/28/2/353 |

Notes: long entry counts match #125 exactly (shorts removed only). Trade drop ≈ short entries removed (ETH drop 208 vs 209 shorts: one short may have been unfinished / window-boundary). Terminal improves (less negative) but exp stays ≤0 and BH still wins by a wide margin.

### SUB A / SUB B (informational; not the gate)

| Inst | Window | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH |
|------|--------|---------:|----------------------:|-----------:|---------:|:----------:|
| BTC-USDT | SUB_A_DEFI_SUMMER | 141 | -0.02326748 | -3.28775737 | 3.544385 | False |
| BTC-USDT | SUB_B_BTC_RUN | 197 | -0.03467567 | -6.83110771 | 33.55838705 | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 174 | -0.02102852 | -3.65896323 | 11.84225941 | False |
| ETH-USDT | SUB_B_BTC_RUN | 163 | -0.02645007 | -4.311362 | 20.8350418 | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 110 | -0.01360849 | -1.49693441 | 2.76085653 | False |
| DOGE-USDT | SUB_B_BTC_RUN | 112 | -0.04330395 | -4.85004245 | 15.36161462 | False |

### 3m / cache probe stamp

| Inst | 1m/15m/3m source | 3m native | n 3m |
|------|------------------|:---------:|-----:|
| BTC-USDT | cache_125 | True | 102720 |
| ETH-USDT | cache_125 | True | 102720 |
| DOGE-USDT | cache_125 | True | 102720 |

---

## Gate result (2/3 rule)

- **PASS requires** completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs on FULL.
- **Measured:** **0 / 3** pairs pass. Completed exp **negative** on every FULL cell; terminal still far below buy-hold.
- **Verdict: FAIL / no promote.**
- Parent #125 also FAIL 0/3. Long-only is a cleaner but still dead edge under 5+5 bps + 45×1m time-stop dominance.
- Soft PASS N/A ≠ arm. **Do not promote.**

---

## What NOT to rescue

- Do **not** grind RSI period, pivot N, timeframes, R-multiple, or time-stop bars.
- Do **not** restore shorts to “save” sample size.
- Do **not** transplant #125 (or any prior) scores into a promote / arm narrative.
- Do **not** transplant S1 / #121 / #123 / #124 / Mid #71.
- Do **not** run ≥60 parallel trades or martingale / leverage.
- Do **not** invent USD / meme bars or drop costs.
- Do **not** treat Soft PASS / scores as an arm gate.

---

## What this PR does / does not

**Does**

- Add `long_only` flag wrapper over #125 strategy + reuse walker/cache.
- Score BTC/ETH/DOGE-USDT FULL + SUB A + SUB B with identical exits/costs.
- Write measured JSON + this phase1/126 note + unit tests (no shorts, same exits, PASS gate).

**Does not**

- Edit phase1/120–125 or `config/default.yaml`.
- Place orders / arm / promote.
- Copy-paste grind of the #125 strategy body.
