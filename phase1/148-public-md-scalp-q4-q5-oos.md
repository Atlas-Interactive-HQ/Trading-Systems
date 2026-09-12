# 148 — Public-MD Scalp: Q4/Q5 dual OOS 2022+2023 (paper only)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched** (sha256 `5ea3910c…633fef` / md5 `68e1d9b76f166c2359d8121b449f7ce1`).
**Live:** Soft PASS ≠ arm. Soft PASS ≠ Scalp-arm. **NO POST.**
**Method:** Pre-registered notebook long stack · cells **Q4=TP4R** (=#147 R4) · **Q5=TP5R** (=#147 R5). **Do not edit** phase1/120 or phase1/146 (P4a).
**Lineage:** #147 dual-gate R2–R5 (GH-PR #130 / `e63532d`) — no dual HARD_PASS; R4/R5 TRAIN PASS but 2021 OOS fails term≥BH. T1 stays demoted.

Code: `atlas.paper.public_md_scalp_148` · walker reuse `public_md_scalp_144.walk_notebook_stretch_cell` · strategy `atlas.strategy.scalp_142_notebook` · script `scripts/run_public_md_scalp_148.py`  
Report JSON: `results/public_md_scalp_148.json`  
Caches: TRAIN `results/public_md_125_cache` + `data/paper/candles/public_md_{121,131}` · STRESS2021 `results/public_md_145_cache/w2` · OOS2022/2023 `results/public_md_148_cache/{oos_2022,oos_2023}`

---

## Lock

| Item | Spec |
|------|------|
| **Family** | Notebook long stack: 4H range-low → 1H MSB → 15m confirm **RVOL≥1.0** → 1m BOS next-open; SL=15m invalidation − 0.1×ATR14(15m); **no** 1H MSB exit; risk **0.25**; lev≤**10×**; max 1; n_time_stop=0; no ATR trail; same-bar SL+TP→SL |
| **Cells** | **Q4**=TP4R (=#147 R4 / #144 T1) · **Q5**=TP5R (=#147 R5) — only TP multiple differs |
| **No T2** | Occupancy cell **not** on this board |
| **No PEPE/sleeve** | Deferred until a cell **dual-PASSes** majors |
| **Costs** | €20 · 5+5 bps · accounting_v2 |
| **Universe** | BTC-USDT / ETH-USDT / DOGE-USDT only |
| **TRAIN** | `2020-07-01T00:00:00Z` → `2021-01-01T00:00:00Z` exclusive — PASS: exp>0 **AND** term≥BH ≥2/3 |
| **STRESS 2021** | `2021-01-01T00:00:00Z` → `2021-07-01T00:00:00Z` — **note only**, not a kill gate; cannot make HARD_PASS |
| **OOS_2022** | `2022-01-01T00:00:00Z` → `2022-07-01T00:00:00Z` — recompute BH; fail-closed if candles missing |
| **OOS_2023** | `2023-01-01T00:00:00Z` → `2023-07-01T00:00:00Z` — recompute BH; fail-closed if candles missing |
| **Primary OOS PASS** | exp>0 ≥2/3 **AND** terminal>0 ≥2/3 **AND** term≥BH ≥2/3 |
| **DUAL HARD_PASS** | TRAIN PASS **AND** OOS_2022 PASS **AND** OOS_2023 PASS (both primary OOS required) |
| **T1** | **Demoted** — train HARD_PASS ≠ OOS hold (#145) |

Candidate: `public_md_v1_148_{q4|q5}_{train|stress_2021|oos_2022|oos_2023}_{btc|eth|doge}_usdt_eur20`

---

## Assumptions

1. Shared entry = #142/#144 T1 / #147 R4–R5 notebook long; cells differ **only** by TP R-multiple (4R / 5R).
2. Pivot N=3; RVOL(20)≥1.0; RSI div skip; lev≤10× skip; NO opposite 1H MSB (`n_msb=0`); forced end accounting_v2.
3. TRAIN BH cites locked 43.17666206 / 45.16769469 / 20.2301366.
4. STRESS 2021 BH cites (note table): 4.18949502 / 41.67406045 / 1065.5538023 — DOGE BH is near-structural ceiling, **not a target**.
5. OOS_2022 / OOS_2023 BH **recomputed** per window on same 1m trade bars.
6. Q4/Q5 TRAIN + STRESS2021 must reproduce #147 R4/R5 — **all matched** (`repro_147_all_match: true`).
7. Soft PASS ≠ Scalp-arm · `not_a_forecast`. config/default.yaml untouched. No live POST.

---

## Registry / notes

- **HARD_PASS:** `[]` — **no dual-PASS cell**
- **SOFT_NOTE:** `['Q4', 'Q5']`
- **FAIL:** `[]`
- **T1_demoted:** train HARD_PASS does not hold OOS — not an arm-candidate.
- **T2_occupancy:** not included.
- **PEPE/sleeve:** deferred until dual-PASS.
- **Fail-closed facts:** none (all OOS_2022 / OOS_2023 candle caches present).
- **STOP after board — no #149 until lock.** Soft PASS ≠ Scalp-arm · `not_a_forecast`.

---

## Scoreboard

Source: `results/public_md_scalp_148.json` · costs 5+5 bps · sleeve €20 · accounting_v2 · generated `2026-09-12T19:39:33Z` (2026-09-12T21:39:33 Europe/Amsterdam).

Mix: `tp/sl/msb_exit/forced` · skips `skip_lev/skip_div/skip_rvol`. `n_msb_exit=0` on all MEASURED cells.

### Dual-gate summary

| Cell | TP | TRAIN | OOS_2022 | OOS_2023 | STRESS 2021 | DUAL HARD_PASS | Registry |
|------|---:|-------|----------|----------|-------------|:--------------:|----------|
| Q4 | 4R | **PASS** (exp 2/3 · term≥BH 2/3) | FAIL (exp 0/3 · term>0 0/3 · ≥BH 0/3) | FAIL (exp 1/3 · term>0 1/3 · ≥BH 1/3) | note only (exp 2/3 · ≥BH 0/3) | **no** | SOFT_NOTE |
| Q5 | 5R | **PASS** (exp 3/3 · term≥BH 3/3) | FAIL (exp 0/3 · term>0 0/3 · ≥BH 0/3) | SOFT (exp 2/3 · term>0 2/3 · ≥BH 0/3) | note only (exp 1/3 · ≥BH 0/3) | **no** | SOFT_NOTE |

### Q4 — SOFT_NOTE (TRAIN PASS = #147 R4 · primary OOS fail) · **repro OK**

| Window | Inst | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | term>0 |
|--------|------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|:------:|
| TRAIN | BTC-USDT | 15 | +6.36477658 | +125.15042363 | 4.23883011 | 43.17666206 | 6/8/0/1 | **yes** | yes |
| TRAIN | ETH-USDT | 23 | +5.32453944 | +122.46440707 | 19.53456749 | 45.16769469 | 9/14/0/0 | **yes** | yes |
| TRAIN | DOGE-USDT | 21 | −0.04298176 | +6.14613878 | 1.72566099 | 20.23013660 | 6/14/0/1 | no | yes |
| STRESS_2021 | BTC-USDT | 31 | −0.66233980 | −19.82177740 | 0.48880581 | 4.18949502 | 4/26/0/1 | no | no |
| STRESS_2021 | ETH-USDT | 37 | +0.04831938 | +4.23952795 | 8.30140495 | 41.67406045 | 11/25/0/1 | no | yes |
| STRESS_2021 | DOGE-USDT | 32 | +1.97618050 | +63.23777589 | 20.50289221 | 1065.55380230 | 11/21/0/0 | no | yes |
| OOS_2022 | BTC-USDT | 20 | −1.02845129 | −19.53006967 | 0.78042408 | −11.38629371 | 2/17/0/1 | no | no |
| OOS_2022 | ETH-USDT | 26 | −0.79162676 | −19.78673615 | 0.80534127 | −14.18345126 | 3/22/0/1 | no | no |
| OOS_2022 | DOGE-USDT | 28 | −0.70574112 | −19.76075134 | 0.89633352 | −12.21738051 | 4/24/0/0 | no | no |
| OOS_2023 | BTC-USDT | 11 | +3.09033211 | +33.93404058 | 2.68873094 | 16.76353143 | 4/6/0/1 | **yes** | yes |
| OOS_2023 | ETH-USDT | 14 | −0.32725083 | −4.58151162 | 1.71331503 | 12.25932277 | 4/10/0/0 | no | no |
| OOS_2023 | DOGE-USDT | 22 | −0.84595069 | −18.61091522 | 1.20565824 | −1.12249166 | 4/18/0/0 | no | no |

### Q5 — SOFT_NOTE (TRAIN PASS = #147 R5 · OOS_2022 fail · OOS_2023 soft) · **repro OK**

| Window | Inst | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | term>0 |
|--------|------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|:------:|
| TRAIN | BTC-USDT | 14 | +6.08201508 | +111.79279254 | 3.61120502 | 43.17666206 | 5/8/0/1 | **yes** | yes |
| TRAIN | ETH-USDT | 18 | +2.69833532 | +48.57003576 | 5.24792753 | 45.16769469 | 6/12/0/0 | **yes** | yes |
| TRAIN | DOGE-USDT | 18 | +0.66485257 | +22.75986136 | 1.91373791 | 20.23013660 | 5/12/0/1 | **yes** | yes |
| STRESS_2021 | BTC-USDT | 34 | −0.60520689 | −19.96132771 | 0.50764937 | 4.18949502 | 3/30/0/1 | no | no |
| STRESS_2021 | ETH-USDT | 39 | −0.48355336 | −16.56485211 | 2.23132853 | 41.67406045 | 8/30/0/1 | no | no |
| STRESS_2021 | DOGE-USDT | 33 | +1.62165156 | +53.51450138 | 45.58930658 | 1065.55380230 | 10/23/0/0 | no | yes |
| OOS_2022 | BTC-USDT | 20 | −1.04251868 | −19.80346107 | 0.71826059 | −11.38629371 | 1/18/0/1 | no | no |
| OOS_2022 | ETH-USDT | 24 | −0.84585697 | −19.44446601 | 1.03977993 | −14.18345126 | 3/20/0/1 | no | no |
| OOS_2022 | DOGE-USDT | 24 | −0.86684569 | −19.91303816 | 0.66260844 | −12.21738051 | 1/22/0/1 | no | no |
| OOS_2023 | BTC-USDT | 12 | +0.00413944 | +1.23901830 | 2.01869756 | 16.76353143 | 3/8/0/1 | no | yes |
| OOS_2023 | ETH-USDT | 10 | +0.71391484 | +7.13914840 | 1.56078324 | 12.25932277 | 3/7/0/0 | no | yes |
| OOS_2023 | DOGE-USDT | 19 | −0.95872986 | −18.21586743 | 1.41825370 | −1.12249166 | 3/16/0/0 | no | no |

---

## STRESS 2021 note (not a kill gate)

| Cell | Inst | term € | BH € | term≥BH |
|------|------|-------:|-----:|:-------:|
| Q4 | BTC | −19.82177740 | 4.18949502 | no |
| Q4 | ETH | +4.23952795 | 41.67406045 | no |
| Q4 | DOGE | +63.23777589 | 1065.55380230 | no |
| Q5 | BTC | −19.96132771 | 4.18949502 | no |
| Q5 | ETH | −16.56485211 | 41.67406045 | no |
| Q5 | DOGE | +53.51450138 | 1065.55380230 | no |

DOGE BH ~+€1065 is a near-structural ceiling on this window — **stress, not a target to beat**. Stress alone **cannot** make HARD_PASS.

---

## Reproducibility vs #147 R4/R5

| Check | Expected | Got | OK |
|-------|----------|-----|:--:|
| Q4 TRAIN BTC | n15 / +6.36477658 / +125.15042363 | same | yes |
| Q4 TRAIN ETH | n23 / +5.32453944 / +122.46440707 | same | yes |
| Q4 TRAIN DOGE | n21 / −0.04298176 / +6.14613878 | same | yes |
| Q4 2021 BTC | n31 / −0.6623398 / −19.8217774 | same | yes |
| Q4 2021 ETH | n37 / +0.04831938 / +4.23952795 | same | yes |
| Q4 2021 DOGE | n32 / +1.9761805 / +63.23777589 | same | yes |
| Q5 TRAIN BTC | n14 / +6.08201508 / +111.79279254 | same | yes |
| Q5 TRAIN ETH | n18 / +2.69833532 / +48.57003576 | same | yes |
| Q5 TRAIN DOGE | n18 / +0.66485257 / +22.75986136 | same | yes |
| Q5 2021 BTC | n34 / −0.60520689 / −19.96132771 | same | yes |
| Q5 2021 ETH | n39 / −0.48355336 / −16.56485211 | same | yes |
| Q5 2021 DOGE | n33 / +1.62165156 / +53.51450138 | same | yes |

`repro_147_all_match: true`

---

## Candle facts (fail-closed)

| Window | Inst | 1m first ISO | 1m last ISO | trade_n 1m |
|--------|------|--------------|-------------|-----------:|
| OOS_2022 | BTC/ETH/DOGE | 2021-11-01T00:00:00Z (cache+warmup) | 2022-06-30T23:59:00Z | 260640 |
| OOS_2023 | BTC/ETH/DOGE | 2022-11-01T00:00:00Z (cache+warmup) | 2023-06-30T23:59:00Z | 260640 |

Host: `https://eea.okx.com` history-candles. No invented bars.

---

## What not to rescue

- **T1 demoted** — train HARD_PASS does not hold OOS (#145 honesty).
- **No T2 occupancy** on this board.
- **No PEPE/sleeve** until a cell dual-PASSes majors.
- Do **not** grind N / ATR / RVOL / RSI / risk / R-multiple.
- **2021 DOGE BH** is stress not a target to beat.
- Do **not** start **#149** until board lock.
- Soft PASS ≠ Scalp-arm · `not_a_forecast`.
- Do **not** edit `config/default.yaml`. Do **not** place live orders. **No live POST.**
- Do **not** invent metrics or candles. Do **not** edit phase1/120 or phase1/146.
