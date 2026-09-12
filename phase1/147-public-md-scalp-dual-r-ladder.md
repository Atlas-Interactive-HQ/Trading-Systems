# 147 — Public-MD Scalp: dual-gate TP R ladder R2–R5 (TRAIN + OOS)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched** (sha256 `5ea3910c…633fef` / md5 `68e1d9b76f166c2359d8121b449f7ce1`).
**Live:** Soft PASS ≠ arm. Soft PASS ≠ Scalp-arm. **NO POST.**
**Method:** Pre-registered notebook long stack · cells differ **only** by TP R ∈ {2,3,4,5}. **Do not edit** phase1/120 or phase1/146 (P4a).
**Lineage:** #144 T1 HARD_PASS on 2020 FULL (PR #127 / `af01da2`) · #145 OOS honesty — train does **not** hold OOS → **T1 demoted**. Number skip: phase1/146 = P4a (GH-PR #128).

Code: `atlas.paper.public_md_scalp_147` · walker reuse `public_md_scalp_144.walk_notebook_stretch_cell` · strategy `atlas.strategy.scalp_142_notebook` · script `scripts/run_public_md_scalp_147.py`  
Report JSON: `results/public_md_scalp_147.json`  
Caches: TRAIN `results/public_md_125_cache` + `data/paper/candles/public_md_{121,131}` · OOS `results/public_md_145_cache/w2` (+ 2020 warmup merge)

---

## Lock

| Item | Spec |
|------|------|
| **Family** | Notebook long stack: 4H range-low → 1H MSB → 15m confirm **RVOL≥1.0** → 1m BOS next-open; SL=15m invalidation − 0.1×ATR14(15m); **no** 1H MSB exit; risk **0.25**; lev≤**10×**; max 1; n_time_stop=0; no ATR trail; same-bar SL+TP→SL |
| **Cells** | **R2**=2R · **R3**=3R · **R4**=4R (=#144 T1) · **R5**=5R — only TP multiple differs |
| **No T2** | Occupancy cell **not** on this board (always have a TP) |
| **No PEPE/sleeve** | Deferred until a cell **dual-PASSes** majors |
| **Costs** | €20 · 5+5 bps · accounting_v2 |
| **Universe** | BTC-USDT / ETH-USDT / DOGE-USDT only |
| **TRAIN** | `2020-07-01T00:00:00Z` → `2021-01-01T00:00:00Z` exclusive |
| **OOS** | `2021-01-01T00:00:00Z` → `2021-07-01T00:00:00Z` exclusive |
| **Window PASS** | exp>0 **AND** term≥BH on ≥2/3 pairs |
| **DUAL HARD_PASS** | **BOTH** TRAIN and OOS window-PASS |
| **One-window** | = **SOFT_NOTE** max (cannot be HARD_PASS) |
| **FAIL** | neither window meets exp>0 ≥2/3 |
| **T1** | **Demoted** — train HARD_PASS ≠ OOS hold (#145) |

Candidate: `public_md_v1_147_{r2|r3|r4|r5}_{train|oos}_{btc|eth|doge}_usdt_eur20`

---

## Assumptions

1. Shared entry = #142/#144 T1 notebook long; cells differ **only** by TP R-multiple.
2. Pivot N=3; RVOL(20)≥1.0; RSI div skip; lev≤10× skip; NO opposite 1H MSB (`n_msb=0`); forced end accounting_v2.
3. TRAIN BH cites locked 43.17666206 / 45.16769469 / 20.2301366 — recomputed and confirmed (BTC/ETH match; DOGE recompute 20.36962684, Δ=+0.13949024 — **gate still uses locked cite**; term≪BH either way).
4. OOS BH recomputed: BTC 4.18949502 · ETH 41.67406045 · DOGE 1065.5538023 — **all match #145 cites**.
5. R4 TRAIN must reproduce #144 T1 FULL; R4 OOS must reproduce #145 W2 — **both matched** (`r4_repro_all_match: true`).
6. Soft PASS ≠ Scalp-arm · `not_a_forecast`. config/default.yaml untouched. No live POST.

---

## Registry / notes

- **HARD_PASS:** `[]` — **no dual-PASS cell**
- **SOFT_NOTE:** `['R3', 'R4', 'R5']`
- **FAIL:** `['R2']`
- **T1_demoted:** train HARD_PASS does not hold OOS — not an arm-candidate.
- **T2_occupancy:** not included.
- **PEPE/sleeve:** deferred until dual-PASS.
- **STOP after board — no #148 until lock.** Soft PASS ≠ Scalp-arm · `not_a_forecast`.

---

## Scoreboard

Source: `results/public_md_scalp_147.json` · costs 5+5 bps · sleeve €20 · accounting_v2 · generated `2026-09-12T18:33:02Z` (2026-09-12T20:33:02 PT / Europe/Amsterdam).

Mix: `tp/sl/msb_exit/forced` · skips `skip_lev/skip_div/skip_rvol`. `n_msb_exit=0` on all MEASURED cells.

### Dual-gate summary

| Cell | TP | TRAIN | OOS | DUAL HARD_PASS | Registry |
|------|---:|-------|-----|:--------------:|----------|
| R2 | 2R | FAIL (exp 1/3 · term≥BH 0/3) | FAIL (exp 0/3 · term≥BH 0/3) | **no** | FAIL |
| R3 | 3R | SOFT (exp 3/3 · term≥BH 1/3) | FAIL (exp 1/3 · term≥BH 0/3) | **no** | SOFT_NOTE |
| R4 | 4R | **PASS** (exp 2/3 · term≥BH 2/3) | SOFT (exp 2/3 · term≥BH 0/3) | **no** | SOFT_NOTE |
| R5 | 5R | **PASS** (exp 3/3 · term≥BH 3/3) | FAIL (exp 1/3 · term≥BH 0/3) | **no** | SOFT_NOTE |

### R2 — FAIL

| Window | Inst | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | skips lev/div/rvol |
|--------|------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|-------------------:|
| TRAIN | BTC-USDT | 19 | +1.48348314 | +42.13097123 | 4.91682523 | 43.17666206 | 9/9/0/1 | no | 113/40/289 |
| TRAIN | ETH-USDT | 34 | −0.07882779 | −0.02436004 | 4.81253136 | 45.16769469 | 14/19/0/1 | no | 62/32/273 |
| TRAIN | DOGE-USDT | 29 | −0.53696804 | −14.51444758 | 1.19580069 | 20.23013660 | 10/18/0/1 | no | 53/23/163 |
| OOS | BTC-USDT | 42 | −0.47530092 | −19.96263852 | 0.56874921 | 4.18949502 | 9/33/0/0 | no | 31/29/288 |
| OOS | ETH-USDT | 65 | −0.13374417 | −8.69337106 | 9.29321742 | 41.67406045 | 27/38/0/0 | no | 13/63/316 |
| OOS | DOGE-USDT | 62 | −0.25957880 | −16.09388546 | 7.31182478 | 1065.55380230 | 24/38/0/0 | no | 21/20/170 |

### R3 — SOFT_NOTE (TRAIN soft / OOS fail)

| Window | Inst | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | skips lev/div/rvol |
|--------|------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|-------------------:|
| TRAIN | BTC-USDT | 18 | +1.54770408 | +41.60984197 | 2.97494866 | 43.17666206 | 7/10/0/1 | no | 101/40/289 |
| TRAIN | ETH-USDT | 27 | +1.92982636 | +52.10531168 | 11.58664522 | 45.16769469 | 11/16/0/0 | **yes** | 44/32/273 |
| TRAIN | DOGE-USDT | 23 | +0.26358455 | +8.50432947 | 1.87332570 | 20.23013660 | 8/14/0/1 | no | 49/23/163 |
| OOS | BTC-USDT | 36 | −0.56874154 | −19.87086486 | 0.50967759 | 4.18949502 | 6/29/0/1 | no | 23/29/288 |
| OOS | ETH-USDT | 48 | +0.23867481 | +22.59859850 | 10.34982909 | 41.67406045 | 17/30/0/1 | no | 13/63/316 |
| OOS | DOGE-USDT | 55 | −0.02853407 | −1.56937395 | 23.65644175 | 1065.55380230 | 19/36/0/0 | no | 20/20/170 |

### R4 — SOFT_NOTE (TRAIN PASS = #144 T1 · OOS SOFT = #145 W2) · **repro OK**

| Window | Inst | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | skips lev/div/rvol |
|--------|------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|-------------------:|
| TRAIN | BTC-USDT | 15 | +6.36477658 | +125.15042363 | 4.23883011 | 43.17666206 | 6/8/0/1 | **yes** | 98/40/289 |
| TRAIN | ETH-USDT | 23 | +5.32453944 | +122.46440707 | 19.53456749 | 45.16769469 | 9/14/0/0 | **yes** | 30/32/273 |
| TRAIN | DOGE-USDT | 21 | −0.04298176 | +6.14613878 | 1.72566099 | 20.23013660 | 6/14/0/1 | no | 45/23/163 |
| OOS | BTC-USDT | 31 | −0.66233980 | −19.82177740 | 0.48880581 | 4.18949502 | 4/26/0/1 | no | 22/29/288 |
| OOS | ETH-USDT | 37 | +0.04831938 | +4.23952795 | 8.30140495 | 41.67406045 | 11/25/0/1 | no | 14/63/316 |
| OOS | DOGE-USDT | 32 | +1.97618050 | +63.23777589 | 20.50289221 | 1065.55380230 | 11/21/0/0 | no | 3/20/170 |

### R5 — SOFT_NOTE (TRAIN PASS 3/3 · OOS FAIL)

| Window | Inst | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | skips lev/div/rvol |
|--------|------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|-------------------:|
| TRAIN | BTC-USDT | 14 | +6.08201508 | +111.79279254 | 3.61120502 | 43.17666206 | 5/8/0/1 | **yes** | 71/40/289 |
| TRAIN | ETH-USDT | 18 | +2.69833532 | +48.57003576 | 5.24792753 | 45.16769469 | 6/12/0/0 | **yes** | 25/32/273 |
| TRAIN | DOGE-USDT | 18 | +0.66485257 | +22.75986136 | 1.91373791 | 20.23013660 | 5/12/0/1 | **yes** | 45/23/163 |
| OOS | BTC-USDT | 34 | −0.60520689 | −19.96132771 | 0.50764937 | 4.18949502 | 3/30/0/1 | no | 20/29/288 |
| OOS | ETH-USDT | 39 | −0.48355336 | −16.56485211 | 2.23132853 | 41.67406045 | 8/30/0/1 | no | 9/63/316 |
| OOS | DOGE-USDT | 33 | +1.62165156 | +53.51450138 | 45.58930658 | 1065.55380230 | 10/23/0/0 | no | 4/20/170 |

---

## BH confirmation

| Window | Inst | cited | recomputed | match |
|--------|------|------:|-----------:|:-----:|
| TRAIN | BTC-USDT | 43.17666206 | 43.17666206 | yes |
| TRAIN | ETH-USDT | 45.16769469 | 45.16769469 | yes |
| TRAIN | DOGE-USDT | 20.2301366 | 20.36962684 | **no** (Δ +0.13949024; gate uses locked cite) |
| OOS | BTC-USDT | 4.18949502 | 4.18949502 | yes |
| OOS | ETH-USDT | 41.67406045 | 41.67406045 | yes |
| OOS | DOGE-USDT | 1065.5538023 | 1065.5538023 | yes |

---

## R4 reproducibility

| Check | Expected | Got | OK |
|-------|----------|-----|:--:|
| TRAIN BTC #144 T1 | n15 / +6.36477658 / +125.15042363 | same | yes |
| TRAIN ETH #144 T1 | n23 / +5.32453944 / +122.46440707 | same | yes |
| TRAIN DOGE #144 T1 | n21 / −0.04298176 / +6.14613878 | same | yes |
| OOS BTC #145 W2 | n31 / −0.6623398 / −19.8217774 | same | yes |
| OOS ETH #145 W2 | n37 / +0.04831938 / +4.23952795 | same | yes |
| OOS DOGE #145 W2 | n32 / +1.9761805 / +63.23777589 | same | yes |

`r4_repro_all_match: true`

---

## What not to rescue

- **T1 demoted** — train HARD_PASS does not hold OOS (#145 honesty).
- **No T2 occupancy** on this ladder.
- **No PEPE/sleeve** until a cell dual-PASSes majors.
- Do **not** grind N / ATR / RVOL / RSI / risk beyond this R2–R5 board.
- Do **not** start **#148** until board lock.
- Soft PASS ≠ Scalp-arm · `not_a_forecast`.
- Do **not** edit `config/default.yaml`. Do **not** place live orders. **No live POST.**
- Do **not** invent metrics or candles. Do **not** edit phase1/120 or phase1/146.
