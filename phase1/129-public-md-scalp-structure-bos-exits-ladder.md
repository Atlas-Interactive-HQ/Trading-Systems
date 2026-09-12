# 129 — Public-MD Scalp: time-stop/R/ATR-SL/retest ladder on #126+FT Jul2020–Jan2021 (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/129** — pre-registered **exit** ladder on [`126-public-md-scalp-structure-bos-long-only.md`](./126-public-md-scalp-structure-bos-long-only.md) + FT-BOS (no indicator gate/exit). **Do not edit** phase1/120–128.
**Parent:** #126 FAIL (0/3). Baselines FULL: BTC 339/−0.02643514/−8.96151151 · ETH 337/−0.0213103/−7.18156963 · DOGE 222/−0.02695481/−5.98396709 (n / completed exp € / terminal €).
**Not:** another indicator-settings rung (#128 worsened expectancy).

Code: `atlas.strategy.scalp_structure_bos_129` · `atlas.paper.public_md_scalp_structure_bos_129` (`walk_structure_bos_129` + reuse `public_md_125_cache`) · script `scripts/run_public_md_scalp_structure_bos_129.py`  
Report JSON: `results/public_md_scalp_structure_bos_129.json` (also `data/reports/…` local)  
Candle cache: **reuse** `results/public_md_125_cache/` (1m/3m/15m) — do not invent bars.

---

## Lock card (LOCKED — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **129** (not 120–128) |
| **Base** | **#126 long-only**: trade ONLY when 15m structure is **bull (HH+HL)**. **NO shorts**. Flat when bear or unclear/mixed. Pivot N=3. |
| **BOS** | 1m BOS + follow-through: (a) closed close > active 15m swing high **AND** (b) next closed close ≥ that BOS bar close. Fill = open after FT (E6: after retest). **No first-touch.** |
| **Entry gates** | **NO** RSI/Stoch/CCI entry gate. **NEVER** restore #127 [20,30] band. |
| **Indicator exit** | **NO** indicator early-exit (#128 worsened exp). Exits = SL / R-TP / opp-BOS / optional time-stop only. |
| **Structure** | **Do NOT remove** 15m structure layer. |
| **Ladder** | Pre-registered **E1–E6 only**. **NEVER grind off-ladder.** STOP after E6 — do not take 130. |
| **Keep** | one entry per BOS/FT (or FT+retest) · no re-entry until NEW 15m swing · confirm_closed_only · €20 · 5+5 bps · accounting_v2 |
| **Reuse** | Structure helpers from `scalp_structure_bos_125` · `load_or_fetch_triple` / `public_md_125_cache`. Do **not** edit 120–128. |
| **PASS per rung** | completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs on **FULL**. Soft PASS N/A ≠ arm. |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |

### Pre-registered ladder

| Rung | Spec |
|------|------|
| **E1** | time_stop=180 (was 45), R=1.5, SL=opposite 15m swing |
| **E2** | time_stop=480, R=1.5, SL=swing |
| **E3** | time_stop=180, R=1.0, SL=swing |
| **E4** | time_stop=None (only SL / 1.5R / opp-BOS), SL=swing |
| **E5** | time_stop=180, R=1.5, SL=entry−1.5×ATR(14,1m) Wilder; TP=1.5R from that SL |
| **E6** | after FT-BOS, wait for 1m retest of broken swing (low touches/crosses broken swing high within 15 bars) then enter next open; exits as E1 |

### Candidate id prefix

`public_md_v1_structure_bos_15m_exits_ladder_1m_long_only_ft_{e1..e6}_{btc|eth|doge}_usdt_eur20`

### Windows (UTC, exclusive end) — same as #126

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup from **2020-06-01**. Series n (cache_125): 1m **308160** / FULL trade **264960**. FULL-only measured this run (SUB optional).

---

## Ladder STOP

- Measured **all** E1–E6 × BTC/ETH/DOGE FULL.
- **any_rung_pass = false**. **rungs_pass = []**.
- Beat #126 on **expectancy**: `[]` (**none** — every cell still negative and ≤ #126 exp).
- Beat #126 on **terminal** (less negative / better): `['E1', 'E2', 'E3', 'E4', 'E5', 'E6']` — wider time-stops / fewer entries cut fee churn vs #126's 45-bar time-stop dominance, but expectancy stays negative and terminal still ≪ BH on every cell.
- **STOP.** Do not take 130. Do not grind off-ladder. Do not restore indicator exits. Do not restore #127 RSI[20,30] band. Do not remove structure.

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_structure_bos_129.json` · costs 5+5 bps · sleeve €20 · next-open after FT · accounting_v2 · generated `2026-09-12T13:58:51Z` (2026-09-12T15:58:51 PT / Europe/Amsterdam).

Exit mix columns = **TP / SL / opp-BOS / time-stop** (indicator exits always 0 on #129).

### E1 — ts=180 R=1.5 SL=swing (no indicator exit)

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|---------------------:|-----------:|
| BTC-USDT | 162 | -0.02865017 | -4.64132694 | 43.17666206 | None | False | 19/28/27/88 | 2.84101522 |
| ETH-USDT | 170 | -0.03187151 | -5.41815748 | 45.16769469 | None | False | 18/26/24/102 | 3.09971837 |
| DOGE-USDT | 118 | -0.04022896 | -4.7470167 | 20.36962684 | None | False | 10/24/16/68 | 2.31088995 |

### E2 — ts=480 R=1.5 SL=swing

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|---------------------:|-----------:|
| BTC-USDT | 148 | -0.03363537 | -4.97803463 | 43.17666206 | None | False | 26/28/75/19 | 2.59508473 |
| ETH-USDT | 157 | -0.04331942 | -6.8011491 | 45.16769469 | None | False | 28/32/83/14 | 2.83282923 |
| DOGE-USDT | 111 | -0.05170932 | -5.73973415 | 20.36962684 | None | False | 16/26/48/21 | 2.09518632 |

### E3 — ts=180 R=1.0 SL=swing

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|---------------------:|-----------:|
| BTC-USDT | 163 | -0.03003469 | -4.89565443 | 43.17666206 | None | False | 34/25/27/77 | 2.86338268 |
| ETH-USDT | 173 | -0.03493162 | -6.04316987 | 45.16769469 | None | False | 32/26/25/90 | 3.09449845 |
| DOGE-USDT | 119 | -0.04795115 | -5.70618669 | 20.36962684 | None | False | 20/23/14/62 | 2.18157633 |

### E4 — ts=None (SL/1.5R/opp-BOS only) SL=swing

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|---------------------:|-----------:|
| BTC-USDT | 144 | -0.03453149 | -4.972534 | 43.17666206 | None | False | 29/27/88/0 | 2.54022084 |
| ETH-USDT | 154 | -0.04817571 | -7.41905971 | 45.16769469 | None | False | 30/32/92/0 | 2.72638764 |
| DOGE-USDT | 106 | -0.04238571 | -4.49288528 | 20.36962684 | None | False | 21/24/61/0 | 2.01720975 |

### E5 — ts=180 R=1.5 SL=entry-1.5×ATR(14,1m) Wilder

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|---------------------:|-----------:|
| BTC-USDT | 212 | -0.03185082 | -6.7523732 | 43.17666206 | None | False | 52/160/0/0 | 3.45699323 |
| ETH-USDT | 233 | -0.02919657 | -6.80280112 | 45.16769469 | None | False | 73/160/0/0 | 3.8619751 |
| DOGE-USDT | 142 | -0.04298769 | -6.10425261 | 20.36962684 | None | False | 33/109/0/0 | 2.4837192 |

### E6 — FT then 1m retest broken swing ≤15 bars; exits as E1

**gate_verdict = `FAIL`** · n_pairs_pass_full = `0` / 3 · pairs_pass_full = `[]`

| Inst | n trades | completed exp €/trade | terminal € | BH net € | pass vs BH | pair PASS FULL | exits TP/SL/opp/time | fee_drag € |
|------|---------:|----------------------:|-----------:|---------:|:----------:|:--------------:|---------------------:|-----------:|
| BTC-USDT | 90 | -0.03411879 | -3.07069116 | 43.17666206 | None | False | 13/21/21/35 | 1.6535113 |
| ETH-USDT | 91 | -0.05129126 | -4.66750429 | 45.16769469 | None | False | 9/20/15/47 | 1.6321933 |
| DOGE-USDT | 71 | -0.04350125 | -3.08858842 | 20.36962684 | None | False | 4/16/10/41 | 1.26859196 |

### Explicit vs #126 (FULL) — which beat on exp / terminal

| Rung | Inst | n 129 | n 126 | exp 129 | exp 126 | beat exp? | terminal 129 | terminal 126 | beat term? | fee_drag 129 |
|------|------|------:|------:|--------:|--------:|:---------:|-------------:|-------------:|:----------:|-------------:|
| E1 | BTC-USDT | 162 | 339 | -0.02865017 | -0.02643514 | False | -4.64132694 | -8.96151151 | True | 2.84101522 |
| E1 | ETH-USDT | 170 | 337 | -0.03187151 | -0.0213103 | False | -5.41815748 | -7.18156963 | True | 3.09971837 |
| E1 | DOGE-USDT | 118 | 222 | -0.04022896 | -0.02695481 | False | -4.7470167 | -5.98396709 | True | 2.31088995 |
| E2 | BTC-USDT | 148 | 339 | -0.03363537 | -0.02643514 | False | -4.97803463 | -8.96151151 | True | 2.59508473 |
| E2 | ETH-USDT | 157 | 337 | -0.04331942 | -0.0213103 | False | -6.8011491 | -7.18156963 | True | 2.83282923 |
| E2 | DOGE-USDT | 111 | 222 | -0.05170932 | -0.02695481 | False | -5.73973415 | -5.98396709 | True | 2.09518632 |
| E3 | BTC-USDT | 163 | 339 | -0.03003469 | -0.02643514 | False | -4.89565443 | -8.96151151 | True | 2.86338268 |
| E3 | ETH-USDT | 173 | 337 | -0.03493162 | -0.0213103 | False | -6.04316987 | -7.18156963 | True | 3.09449845 |
| E3 | DOGE-USDT | 119 | 222 | -0.04795115 | -0.02695481 | False | -5.70618669 | -5.98396709 | True | 2.18157633 |
| E4 | BTC-USDT | 144 | 339 | -0.03453149 | -0.02643514 | False | -4.972534 | -8.96151151 | True | 2.54022084 |
| E4 | ETH-USDT | 154 | 337 | -0.04817571 | -0.0213103 | False | -7.41905971 | -7.18156963 | False | 2.72638764 |
| E4 | DOGE-USDT | 106 | 222 | -0.04238571 | -0.02695481 | False | -4.49288528 | -5.98396709 | True | 2.01720975 |
| E5 | BTC-USDT | 212 | 339 | -0.03185082 | -0.02643514 | False | -6.7523732 | -8.96151151 | True | 3.45699323 |
| E5 | ETH-USDT | 233 | 337 | -0.02919657 | -0.0213103 | False | -6.80280112 | -7.18156963 | True | 3.8619751 |
| E5 | DOGE-USDT | 142 | 222 | -0.04298769 | -0.02695481 | False | -6.10425261 | -5.98396709 | False | 2.4837192 |
| E6 | BTC-USDT | 90 | 339 | -0.03411879 | -0.02643514 | False | -3.07069116 | -8.96151151 | True | 1.6535113 |
| E6 | ETH-USDT | 91 | 337 | -0.05129126 | -0.0213103 | False | -4.66750429 | -7.18156963 | True | 1.6321933 |
| E6 | DOGE-USDT | 71 | 222 | -0.04350125 | -0.02695481 | False | -3.08858842 | -5.98396709 | True | 1.26859196 |

### Rungs that beat #126 (any pair)

| Metric | Rungs |
|--------|-------|
| expectancy | `[]` |
| terminal | `['E1', 'E2', 'E3', 'E4', 'E5', 'E6']` |

---

## Gate result (2/3 rule)

- **PASS requires** completed exp > 0 **AND** terminal ≥ BH on **≥2/3** pairs on FULL **per rung**.
- **Measured:** **0 / 6** rungs pass. Completed exp **negative** on every FULL cell; terminal still far below buy-hold.
- **Verdict: FAIL / no promote** on every rung. Soft PASS N/A ≠ arm.
- Parent #126 also FAIL 0/3. #128 indicator exits worsened exp; #129 exit-ladder improves some terminals via less time-stop churn but does **not** flip expectancy.

---

## What NOT to rescue

- Do **not** grind off-ladder time-stops / R / ATR mult / retest window.
- Do **not** restore #127 RSI[20,30] entry band or #128 indicator early-exits (worsened exp).
- Do **not** remove the 15m structure layer.
- Do **not** restore shorts to “save” sample size.
- Do **not** transplant #125/#126/#128 scores into a promote / arm narrative.
- Do **not** transplant S1 / #121 / #123 / #124 / Mid #71.
- Do **not** run ≥60 parallel trades or martingale / leverage.
- Do **not** invent USD / meme bars or drop costs.
- Do **not** treat Soft PASS / scores as an arm gate.
- Do **not** take phase1/130 from this coord.

---

## What this PR does / does not

**Does**

- Add E1–E6 exit ladder on #126 long-only + FT-BOS with **no** indicator entry/exit.
- Reuse `public_md_125_cache` + structure/BOS helpers; fail closed; no invented bars.
- Score BTC/ETH/DOGE-USDT FULL with SL / R-TP / opp-BOS / rung time-stop; report exit mix + fee_drag vs #126.
- Lock Soft PASS N/A ≠ arm; `place_orders: false`; `not_a_forecast: true`.

**Does not**

- Edit phase1/120–128 or `config/default.yaml`.
- Promote / arm / live gate.
- Restore #127 band or #128 indicator exits.
- Take 130.

---

## Honesty

- Wider / removed time-stops reduce #126's time-stop-dominated churn → often **less-bad terminal** and lower fee_drag, but completed expectancy stays **negative** and never beats BH.
- ATR SL (E5) and retest (E6) change trade count / exit mix without producing an edge under 5+5 bps.
- Soft PASS N/A ≠ arm. Scores ≠ GREEN CANDIDATE ≠ arm. **Do not promote. Do not grind.**
