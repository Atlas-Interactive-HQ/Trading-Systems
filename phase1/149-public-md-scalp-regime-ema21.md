# Public-MD Scalp #149 — B4/B5 (+B4b) notebook + EMA21 bull regime

**Paper / backtest ONLY.** `place_orders: false`. `not_a_forecast`. Soft PASS ≠ arm.
Does **not** edit `config/default.yaml`. No live POST. No invented candles/metrics.

## Lock (from #148)

- #148 Q4/Q5 TRAIN PASS but 2022 bear-wipe term~−19.5 ≪ BH −11/−14/−12 — long-only without regime filter.
- Soft PASS ≠ arm · NO POST. T1 stays demoted.
- GH PR #148 board = **#131** SHA `177aef3`.

## Cells

| Cell | Stack | Regime |
|------|-------|--------|
| **B4** | Q4 notebook TP4R risk0.25 no MSB | Enter iff 1D close > EMA21; exit next 1H open if 1D close < EMA21 |
| **B5** | Q5 notebook TP5R | Same 1D EMA21 |
| **B4b** | Same as B4 | 4H close > EMA21 (included — 4H already cached) |

Shared entry: 4H range-low → 1H MSB → 15m confirm RVOL≥1 → 1m BOS next-open; SL=15m−0.1×ATR14; risk 0.25; lev≤10×; max 1; n_time_stop=0; no ATR trail; same-bar SL+TP→SL; mix keys: `tp/sl/msb/regime/forced`.

**n=0:** terminal=0; term≥BH if 0≥BH; exp>0 and term>0 waived for that pair (report n=0 explicitly).

## Windows / gate

- TRAIN 2020-07-01→2021-01-01
- STRESS 2021-01-01→2021-07-01 (**note only** — cannot make HARD_PASS)
- OOS_2022 2022-01-01→2022-07-01
- OOS_2023 2023-01-01→2023-07-01

**Window PASS** = n=0 handling OR (n>0: exp>0 ≥2/3 AND term≥BH ≥2/3; OOS also term>0 ≥2/3).
**DUAL HARD_PASS** = PASS on TRAIN **AND** OOS_2022 **AND** OOS_2023.

Majors BTC/ETH/DOGE. €20 / 5+5bps / accounting_v2. No PEPE / shorts / T2.

## Board (measured)

### Dual HARD_PASS?

| Cell | TRAIN | OOS_2022 | OOS_2023 | 2021 stress | **DUAL** |
|------|-------|----------|----------|-------------|----------|
| B4 | FAIL | **PASS** | FAIL | STRESS_NOTE_ONLY | **no** (SOFT_NOTE) |
| B5 | FAIL | **PASS** | FAIL | STRESS_NOTE_ONLY | **no** (SOFT_NOTE) |
| B4b | SOFT | FAIL | **PASS** | STRESS_NOTE_ONLY | **no** (SOFT_NOTE) |

**No dual HARD_PASS.** Soft PASS ≠ Scalp-arm. STOP after board — no #150 until lock.

### B4 (1D EMA21) — per pair

| Window | Pair | n | exp | term | fee | mix (tp/sl/msb/regime/forced) | BH | term≥BH | term>0 |
|--------|------|---|-----|------|-----|-------------------------------|----|---------|--------|
| TRAIN | BTC | 13 | 19.82550561 | 323.10555017 | 8.0938858 | 6/5/0/1/1 | 43.17666206 | Y | Y |
| TRAIN | ETH | 22 | -0.20749525 | -4.5648955 | 4.97234221 | 6/15/0/1/0 | 45.16769469 | N | N |
| TRAIN | DOGE | 20 | -0.55172242 | -6.99920454 | 1.50244437 | 5/14/0/0/1 | 20.2301366 | N | N |
| STRESS_2021 | BTC | 21 | -0.92268325 | -19.3763482 | 0.55837968 | 2/17/0/2/0 | 4.18949502 | N | N |
| STRESS_2021 | ETH | 24 | 1.21231005 | 29.09544111 | 8.284051 | 8/15/0/1/0 | 41.67406045 | N | Y |
| STRESS_2021 | DOGE | 32 | 0.58439996 | 18.70079861 | 4.63590698 | 10/21/0/1/0 | 1065.5538023 | N | Y |
| OOS_2022 | BTC | 2 | 9.59233046 | 19.18466092 | 0.24342265 | 1/0/0/1/0 | -11.38629371 | Y | Y |
| OOS_2022 | ETH | 4 | 0.80451509 | 3.21806036 | 0.50256316 | 1/2/0/1/0 | -14.18345126 | Y | Y |
| OOS_2022 | DOGE | 9 | -1.15792762 | -10.42134856 | 1.44784649 | 2/7/0/0/0 | -12.21738051 | Y | N |
| OOS_2023 | BTC | 7 | 1.29068003 | 21.43913541 | 1.29846421 | 2/3/0/1/1 | 16.76353143 | Y | Y |
| OOS_2023 | ETH | 9 | -1.75056147 | -15.75505323 | 0.5758887 | 1/7/0/1/0 | 12.25932277 | N | N |
| OOS_2023 | DOGE | 6 | -2.40552711 | -14.43316265 | 0.3822566 | 0/4/0/2/0 | -1.12249166 | N | N |

### B5 (1D EMA21) — per pair

| Window | Pair | n | exp | term | fee | mix | BH | term≥BH | term>0 |
|--------|------|---|-----|------|-----|-----|----|---------|--------|
| TRAIN | BTC | 12 | 9.77618331 | 149.67031363 | 4.80693141 | 4/5/0/2/1 | 43.17666206 | Y | Y |
| TRAIN | ETH | 18 | -0.48509987 | -8.73179758 | 1.96940016 | 4/13/0/1/0 | 45.16769469 | N | N |
| TRAIN | DOGE | 18 | -0.56924542 | -5.89880125 | 1.69538809 | 4/13/0/0/1 | 20.2301366 | N | N |
| STRESS_2021 | BTC | 19 | -1.02777367 | -19.52769982 | 0.52111958 | 1/16/0/2/0 | 4.18949502 | N | N |
| STRESS_2021 | ETH | 28 | -0.56355131 | -15.77943666 | 1.94152595 | 6/21/0/1/0 | 41.67406045 | N | N |
| STRESS_2021 | DOGE | 30 | 1.84694211 | 55.40826341 | 6.9980899 | 9/20/0/1/0 | 1065.5538023 | N | Y |
| OOS_2022 | BTC | 2 | 4.36312218 | 8.72624436 | 0.23819083 | 0/0/0/2/0 | -11.38629371 | Y | Y |
| OOS_2022 | ETH | 4 | 1.53249879 | 6.12999515 | 0.53026936 | 1/2/0/1/0 | -14.18345126 | Y | Y |
| OOS_2022 | DOGE | 7 | -2.50962968 | -17.56740777 | 0.38145729 | 0/7/0/0/0 | -12.21738051 | N | N |
| OOS_2023 | BTC | 7 | 2.52455022 | 32.49674404 | 1.50554104 | 2/3/0/1/1 | 16.76353143 | Y | Y |
| OOS_2023 | ETH | 9 | -1.691277 | -15.22149304 | 0.58856694 | 1/7/0/1/0 | 12.25932277 | N | N |
| OOS_2023 | DOGE | 6 | -2.40552711 | -14.43316265 | 0.3822566 | 0/4/0/2/0 | -1.12249166 | N | N |

### B4b (4H EMA21) — per pair

| Window | Pair | n | exp | term | fee | mix | BH | term≥BH | term>0 |
|--------|------|---|-----|------|-----|-----|----|---------|--------|
| TRAIN | BTC | 19 | 0.8457184 | 26.85885882 | 4.00644673 | 3/6/0/9/1 | 43.17666206 | N | Y |
| TRAIN | ETH | 27 | 4.04828087 | 109.30358353 | 16.1778382 | 6/10/0/11/0 | 45.16769469 | Y | Y |
| TRAIN | DOGE | 22 | 0.05319678 | 1.17032926 | 2.88864745 | 4/7/0/11/0 | 20.2301366 | N | Y |
| STRESS_2021 | BTC | 28 | -0.69080364 | -19.34250181 | 0.86451302 | 1/15/0/12/0 | 4.18949502 | N | N |
| STRESS_2021 | ETH | 41 | 0.57554169 | 43.82047727 | 14.81086404 | 9/20/0/11/1 | 41.67406045 | Y | Y |
| STRESS_2021 | DOGE | 41 | 0.14887866 | 6.10402495 | 6.34510561 | 10/18/0/13/0 | 1065.5538023 | N | Y |
| OOS_2022 | BTC | 15 | -1.15935657 | -17.39034849 | 1.07209594 | 0/8/0/7/0 | -11.38629371 | N | N |
| OOS_2022 | ETH | 21 | -0.83263201 | -17.48527225 | 1.42542624 | 2/10/0/9/0 | -14.18345126 | N | N |
| OOS_2022 | DOGE | 22 | -0.00915817 | -0.20147975 | 3.8387522 | 5/8/0/9/0 | -12.21738051 | Y | N |
| OOS_2023 | BTC | 10 | 3.60608425 | 36.0608425 | 2.76849769 | 3/2/0/5/0 | 16.76353143 | Y | Y |
| OOS_2023 | ETH | 12 | 2.31738199 | 27.80858389 | 2.95195324 | 1/3/0/8/0 | 12.25932277 | Y | Y |
| OOS_2023 | DOGE | 18 | -1.0821718 | -19.47909232 | 0.70546459 | 0/10/0/8/0 | -1.12249166 | N | N |

**n=0 windows:** none in this board (all cells had n>0).

## BH recompute confirm

| Window | Pair | recomputed | cited | match |
|--------|------|------------|-------|-------|
| TRAIN | BTC/ETH | match locked cites | | Y |
| TRAIN | DOGE | 20.36962684 | 20.2301366 | N (same #148 delta; locked cite used for gate) |
| STRESS_2021 | all | match | | Y |
| OOS_2022 | all | −11.38629371 / −14.18345126 / −12.21738051 | match #148 | Y |
| OOS_2023 | all | 16.76353143 / 12.25932277 / −1.12249166 | match | Y |

## Honesty notes

- 1D EMA21 regime **fixed the 2022 bear wipe** for B4/B5 (OOS_2022 PASS: BTC/ETH positive term vs negative BH). TRAIN no longer PASS (ETH/DOGE under BH).
- B4b (4H) is noisier on 2022 (FAIL) but PASSes OOS_2023; TRAIN only SOFT.
- Parent #148 Q4/Q5 without regime **not** force-matched (regime changes path).
- `config/default.yaml` untouched: sha256 `5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef` / md5 `68e1d9b76f166c2359d8121b449f7ce1`.

## What not to rescue

- T1 demoted; no T2; no PEPE until dual-PASS; no grind RVOL/N/ATR; 2021 stress not a target; **no #150 until lock**; Soft PASS ≠ Scalp-arm · not_a_forecast.

## Artifacts

- `results/public_md_scalp_149.json`
- `src/atlas/paper/public_md_scalp_149.py` (+ `public_md_scalp_148.py` loaders reused)
- `scripts/run_public_md_scalp_149.py`
- `tests/unit/test_public_md_scalp_149.py` (n=0 term=0; 2021 cannot HARD_PASS; dual needs all three)
- 1D cache: `data/paper/candles/public_md_149/` (local; under `data/` gitignore)
