# 128 — Public-MD Scalp: indicator-layer ladder R1–R8 on #126+FT Jul2020–Jan2021 (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/128** — pre-registered indicator-layer ladder on [`126-public-md-scalp-structure-bos-long-only.md`](./126-public-md-scalp-structure-bos-long-only.md) + FT-BOS from #127 lineage. **Do not edit** phase1/120–127.
**Parent:** #126 FAIL (0/3). Baselines FULL (from `results/public_md_scalp_structure_bos_126.json`): BTC 339/−0.02643514/−8.96151151 · ETH 337/−0.0213103/−7.18156963 · DOGE 222/−0.02695481/−5.98396709 (n / completed exp € / terminal €).

Code: `atlas.strategy.scalp_structure_bos_128` · `atlas.paper.public_md_scalp_structure_bos_128` (`walk_structure_bos_128` + reuse `public_md_125_cache`) · script `scripts/run_public_md_scalp_structure_bos_128.py`  
Report JSON: `results/public_md_scalp_structure_bos_128.json` (also `data/reports/…` local)  
Candle cache: **reuse** `results/public_md_125_cache/` (1m/3m/15m) — do not invent bars.

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **128** (not 120–127) |
| **Base** | **#126 long-only**: trade ONLY when 15m structure is **bull (HH+HL)**. **NO shorts**. Flat when bear or unclear/mixed. |
| **BOS** | 1m BOS + follow-through A from #127: (a) closed close > active 15m swing high **AND** (b) next closed close ≥ that BOS bar close. Fill = open after FT. **No first-touch.** |
| **Entry RSI** | **OFF** for R1–R7 (no #127 [20,30] band). R2 adds late-filter skip if 3m RSI14 ≥75 at FT. R8 pullback: arm only after 3m RSI14 dipped ≤45 then rose. |
| **Indicator layer** | **ALWAYS present** (NEVER delete). Exit = indicator OR TP 1.5R OR opposite BOS OR 45×1m time-stop, whichever first. |
| **Ladder** | Pre-registered **R1–R8 only**. **NEVER grind off-ladder.** STOP after R8 — do not take 129 from this coord. |
| **Keep** | SL = last 15m swing low · one entry per BOS/FT · no re-entry until NEW 15m swing · confirm_closed_only · €20 · 5+5 bps · accounting_v2 |
| **Reuse** | Structure helpers from `scalp_structure_bos_125` · `load_or_fetch_triple` / `public_md_125_cache`. Do **not** edit 120–127. |
| **PASS per rung** | completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs on **FULL**. Soft PASS N/A ≠ arm. |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |

### Pre-registered ladder

| Rung | Spec |
|------|------|
| **R1** | FT-BOS + 3m RSI14 exit≥67 (RSI OFF entry) |
| **R2** | R1 + late-filter skip if 3m RSI14≥75 at FT |
| **R3** | R1 but RSI TF=15m exit≥67 |
| **R4** | R1 but RSI period=7 exit≥67 |
| **R5** | R1 but RSI period=21 exit≥67 |
| **R6** | 3m Stoch(14,3,3) exit %K≥80 |
| **R7** | 3m CCI(20) exit≥100 |
| **R8** | pullback: FT after RSI14 dipped≤45 then rose; exit≥67 |

### Candidate id prefix

`public_md_v1_structure_bos_15m_ind_ladder_1m_long_only_ft_{rung}_{btc|eth|doge}_usdt_eur20`

### Windows (UTC, exclusive end) — same as #126

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup from **2020-06-01**. Series n (cache_125): 1m **308160** / FULL trade **264960**. FULL-only measured this run (SUB optional).

---

## Ladder STOP

- Measured **all** R1–R8 × BTC/ETH/DOGE FULL.
- **any_rung_pass = false**. **rungs_pass = []**.
- Beat #126 on **expectancy**: `[]` (**none**).
- Beat #126 on **terminal** (less negative / better): `['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8']` — indicator exits cut #126 time-stop bleed on some pairs, but expectancy stays negative and terminal still ≪ BH on every cell.
- **STOP.** Do not take 129. Do not grind off-ladder. Do not delete indicator. Do not restore #127 RSI[20,30] band.

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_structure_bos_128.json` · costs 5+5 bps · sleeve €20 · next-open after FT · SL / 1.5R / indicator-exit / opp-BOS / time-stop 45 · accounting_v2 · generated `2026-09-12T09:27:39Z` (2026-09-12T11:27:39 PT / Europe/Amsterdam).

### R1 — FT-BOS + 3m RSI14 exit≥67 (RSI OFF entry)

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/ind/time |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|-------------------------:|
| BTC-USDT | 213 | -0.03076879 | -6.55375315 | 43.17666206 | False | False | 0/3/0/184/26 |
| ETH-USDT | 233 | -0.03179195 | -7.40752499 | 45.16769469 | False | False | 0/3/1/200/29 |
| DOGE-USDT | 147 | -0.04411005 | -6.48417767 | 20.36962684 | False | False | 0/5/0/109/33 |

### R2 — R1 + late-filter skip if 3m RSI14≥75 at FT

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/ind/time |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|-------------------------:|
| BTC-USDT | 191 | -0.0300173 | -5.73330473 | 43.17666206 | False | False | 0/3/0/162/26 |
| ETH-USDT | 210 | -0.03247828 | -6.8204397 | 45.16769469 | False | False | 0/3/1/177/29 |
| DOGE-USDT | 124 | -0.04482585 | -5.55840577 | 20.36962684 | False | False | 0/5/0/86/33 |

### R3 — R1 but RSI TF=15m exit≥67

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/ind/time |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|-------------------------:|
| BTC-USDT | 196 | -0.0315541 | -6.18460396 | 43.17666206 | False | False | 0/7/1/92/96 |
| ETH-USDT | 222 | -0.03347014 | -7.43037013 | 45.16769469 | False | False | 2/7/3/112/98 |
| DOGE-USDT | 142 | -0.04159981 | -5.9071727 | 20.36962684 | False | False | 4/6/0/56/76 |

### R4 — R1 but RSI period=7 exit≥67

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/ind/time |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|-------------------------:|
| BTC-USDT | 216 | -0.03106341 | -6.70969626 | 43.17666206 | False | False | 0/1/0/211/4 |
| ETH-USDT | 236 | -0.03117508 | -7.35731977 | 45.16769469 | False | False | 0/3/0/224/9 |
| DOGE-USDT | 148 | -0.03948317 | -5.84350889 | 20.36962684 | False | False | 0/5/0/134/9 |

### R5 — R1 but RSI period=21 exit≥67

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/ind/time |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|-------------------------:|
| BTC-USDT | 206 | -0.03276565 | -6.74972397 | 43.17666206 | False | False | 0/6/1/126/73 |
| ETH-USDT | 227 | -0.03464966 | -7.86547337 | 45.16769469 | False | False | 1/7/2/137/80 |
| DOGE-USDT | 141 | -0.05372472 | -7.57518487 | 20.36962684 | False | False | 1/7/0/71/62 |

### R6 — 3m Stoch(14,3,3) exit %K≥80

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/ind/time |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|-------------------------:|
| BTC-USDT | 215 | -0.03055934 | -6.57025855 | 43.17666206 | False | False | 0/1/0/203/11 |
| ETH-USDT | 236 | -0.03106985 | -7.33248426 | 45.16769469 | False | False | 0/3/0/217/16 |
| DOGE-USDT | 147 | -0.04214366 | -6.19511844 | 20.36962684 | False | False | 0/5/0/129/13 |

### R7 — 3m CCI(20) exit≥100

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/ind/time |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|-------------------------:|
| BTC-USDT | 216 | -0.03252352 | -7.02508034 | 43.17666206 | False | False | 0/1/0/208/7 |
| ETH-USDT | 236 | -0.02963689 | -6.9943063 | 45.16769469 | False | False | 0/3/0/224/9 |
| DOGE-USDT | 148 | -0.03792727 | -5.61323523 | 20.36962684 | False | False | 0/3/0/141/4 |

### R8 — pullback: FT after RSI14 dipped≤45 then rose; exit≥67

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/ind/time |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|-------------------------:|
| BTC-USDT | 45 | -0.03704305 | -1.66693705 | 43.17666206 | False | False | 0/2/0/40/3 |
| ETH-USDT | 54 | -0.03520486 | -1.90106259 | 45.16769469 | False | False | 0/1/1/48/4 |
| DOGE-USDT | 35 | -0.04885608 | -1.70996272 | 20.36962684 | False | False | 0/0/0/29/6 |

## Exit mix / vs #126 (FULL)

| Rung | Inst | n128 | n126 | exp128 | exp126 | term128 | term126 | beat exp? | beat term? | exit128 TP/SL/opp/ind/ts | exit126 TP/SL/opp/ts |
|------|------|-----:|-----:|-------:|-------:|--------:|--------:|:---------:|:----------:|-------------------------:|---------------------:|
| R1 | BTC-USDT | 213 | 339 | -0.03076879 | -0.02643514 | -6.55375315 | -8.96151151 | False | True | 0/3/0/184/26 | 12/13/5/309 |
| R1 | ETH-USDT | 233 | 337 | -0.03179195 | -0.0213103 | -7.40752499 | -7.18156963 | False | False | 0/3/1/200/29 | 11/15/7/304 |
| R1 | DOGE-USDT | 147 | 222 | -0.04411005 | -0.02695481 | -6.48417767 | -5.98396709 | False | False | 0/5/0/109/33 | 6/14/1/201 |
| R2 | BTC-USDT | 191 | 339 | -0.0300173 | -0.02643514 | -5.73330473 | -8.96151151 | False | True | 0/3/0/162/26 | 12/13/5/309 |
| R2 | ETH-USDT | 210 | 337 | -0.03247828 | -0.0213103 | -6.8204397 | -7.18156963 | False | True | 0/3/1/177/29 | 11/15/7/304 |
| R2 | DOGE-USDT | 124 | 222 | -0.04482585 | -0.02695481 | -5.55840577 | -5.98396709 | False | True | 0/5/0/86/33 | 6/14/1/201 |
| R3 | BTC-USDT | 196 | 339 | -0.0315541 | -0.02643514 | -6.18460396 | -8.96151151 | False | True | 0/7/1/92/96 | 12/13/5/309 |
| R3 | ETH-USDT | 222 | 337 | -0.03347014 | -0.0213103 | -7.43037013 | -7.18156963 | False | False | 2/7/3/112/98 | 11/15/7/304 |
| R3 | DOGE-USDT | 142 | 222 | -0.04159981 | -0.02695481 | -5.9071727 | -5.98396709 | False | True | 4/6/0/56/76 | 6/14/1/201 |
| R4 | BTC-USDT | 216 | 339 | -0.03106341 | -0.02643514 | -6.70969626 | -8.96151151 | False | True | 0/1/0/211/4 | 12/13/5/309 |
| R4 | ETH-USDT | 236 | 337 | -0.03117508 | -0.0213103 | -7.35731977 | -7.18156963 | False | False | 0/3/0/224/9 | 11/15/7/304 |
| R4 | DOGE-USDT | 148 | 222 | -0.03948317 | -0.02695481 | -5.84350889 | -5.98396709 | False | True | 0/5/0/134/9 | 6/14/1/201 |
| R5 | BTC-USDT | 206 | 339 | -0.03276565 | -0.02643514 | -6.74972397 | -8.96151151 | False | True | 0/6/1/126/73 | 12/13/5/309 |
| R5 | ETH-USDT | 227 | 337 | -0.03464966 | -0.0213103 | -7.86547337 | -7.18156963 | False | False | 1/7/2/137/80 | 11/15/7/304 |
| R5 | DOGE-USDT | 141 | 222 | -0.05372472 | -0.02695481 | -7.57518487 | -5.98396709 | False | False | 1/7/0/71/62 | 6/14/1/201 |
| R6 | BTC-USDT | 215 | 339 | -0.03055934 | -0.02643514 | -6.57025855 | -8.96151151 | False | True | 0/1/0/203/11 | 12/13/5/309 |
| R6 | ETH-USDT | 236 | 337 | -0.03106985 | -0.0213103 | -7.33248426 | -7.18156963 | False | False | 0/3/0/217/16 | 11/15/7/304 |
| R6 | DOGE-USDT | 147 | 222 | -0.04214366 | -0.02695481 | -6.19511844 | -5.98396709 | False | False | 0/5/0/129/13 | 6/14/1/201 |
| R7 | BTC-USDT | 216 | 339 | -0.03252352 | -0.02643514 | -7.02508034 | -8.96151151 | False | True | 0/1/0/208/7 | 12/13/5/309 |
| R7 | ETH-USDT | 236 | 337 | -0.02963689 | -0.0213103 | -6.9943063 | -7.18156963 | False | True | 0/3/0/224/9 | 11/15/7/304 |
| R7 | DOGE-USDT | 148 | 222 | -0.03792727 | -0.02695481 | -5.61323523 | -5.98396709 | False | True | 0/3/0/141/4 | 6/14/1/201 |
| R8 | BTC-USDT | 45 | 339 | -0.03704305 | -0.02643514 | -1.66693705 | -8.96151151 | False | True | 0/2/0/40/3 | 12/13/5/309 |
| R8 | ETH-USDT | 54 | 337 | -0.03520486 | -0.0213103 | -1.90106259 | -7.18156963 | False | True | 0/1/1/48/4 | 11/15/7/304 |
| R8 | DOGE-USDT | 35 | 222 | -0.04885608 | -0.02695481 | -1.70996272 | -5.98396709 | False | True | 0/0/0/29/6 | 6/14/1/201 |

Notes: #126 had **no** indicator-exit (mostly time-stop). Ladder rungs fire indicator-exit heavily; terminals often less negative than #126 on some pairs, but **no** rung improves completed expectancy vs #126, and **no** rung reaches terminal ≥ BH.

---

## Gate result

- **PASS requires (per rung)** completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs on FULL.
- **Measured:** **0 / 8** rungs PASS. Every FULL cell has negative completed exp and terminal ≪ BH.
- **Verdict: FAIL / no promote** on entire ladder.
- Soft PASS N/A ≠ arm. **Do not promote.**

---

## What NOT to rescue

- Do **not** grind off-ladder (no R9+, no free param search).
- Do **not** delete / remove the indicator layer entirely.
- Do **not** restore #127 RSI entry band [20,30] (empty sample in this window).
- Do **not** drop follow-through or restore first-touch BOS.
- Do **not** grind pivot N, R-multiple, time-stop, or costs.
- Do **not** restore shorts / transplant #125–#127 scores into a promote narrative.
- Do **not** transplant S1 / #121 / #123 / #124 / Mid #71.
- Do **not** run ≥60 parallel trades or martingale / leverage.
- Do **not** invent USD / meme bars or drop costs.
- Do **not** treat Soft PASS / less-negative terminal vs #126 as an arm gate.
- Do **not** take coord 129 from this ladder STOP.

---

## What this PR does / does not

**Does**

- Add #128 strategy + walker + script measuring pre-registered R1–R8 on #126+FT base.
- Reuse #125 structure helpers + `public_md_125_cache`; indicator exit attribution (RSI/Stoch/CCI).
- Score BTC/ETH/DOGE-USDT FULL for all 8 rungs; write measured JSON + this phase1/128 note + unit tests (rung ids, no-indicator-forbidden, PASS gate, no off-ladder).

**Does not**

- Edit phase1/120–127 or `config/default.yaml`.
- Place orders / arm / promote.
- Grind off-ladder or delete the indicator layer.

