# Public-MD Scalp #150 — D1/D2/D3 regime soften (Q4 base)

**Paper / backtest ONLY.** `place_orders: false`. `not_a_forecast`. Soft PASS ≠ arm.
Does **not** edit `config/default.yaml`. No live POST. No invented candles/metrics.

## Lock (from #149)

- #149: 1D regime fixes 2022 but kills TRAIN; 4H flips the other way. Soft PASS ≠ arm · NO POST. T1 demoted.
- Parent #149 board GH PR #132 merged squash `1479348`. Base = Q4 notebook TP4R risk0.25 no MSB exit.

## Cells

| Cell | Stack | Regime |
|------|-------|--------|
| **D1** | Q4 notebook TP4R risk0.25 | Enter iff stack AND 1D close > EMA21; **no regime exit** (SL/TP/forced only; n_regime=0) |
| **D2** | Same Q4 | Enter iff 1D > EMA21; sticky exit after **3 consecutive** 1D closes < EMA21 → next 1H open |
| **D3** | Same Q4 | Enter iff 1D > **EMA50**; exit 1D close < EMA50 → next 1H open |

Shared entry: 4H range-low → 1H MSB → 15m confirm RVOL≥1 → 1m BOS next-open; SL=15m−0.1×ATR14; TP=4R; risk 0.25; lev≤10×; max 1; n_time_stop=0; no ATR trail; same-bar SL+TP→SL; mix keys: `tp/sl/msb/regime/forced`.

**n=0:** terminal=0; term≥BH if 0≥BH; exp>0 and term>0 waived for that pair (report n=0 explicitly).

## Windows / gate

- TRAIN 2020-07-01→2021-01-01
- STRESS 2021-01-01→2021-07-01 (**note only** — cannot make HARD_PASS)
- OOS_2022 2022-01-01→2022-07-01
- OOS_2023 2023-01-01→2023-07-01

**Window PASS** (n>0): exp>0 ≥2/3 AND term>0 ≥2/3 AND term≥BH ≥2/3 (TRAIN: exp>0 AND term≥BH ≥2/3 enough).
**n=0:** term=0; exp waived; term≥BH if 0≥BH.
**DUAL HARD_PASS** = PASS on TRAIN **AND** OOS_2022 **AND** OOS_2023.
Else **SOFT** if any window exp>0 ≥2/3 or a single PASS.

Majors BTC/ETH/DOGE. €20 / 5+5bps / accounting_v2. No PEPE / shorts / T2.

## Board (measured)

### Dual HARD_PASS?

| Cell | TRAIN | OOS_2022 | OOS_2023 | 2021 stress | **DUAL** |
|------|-------|----------|----------|-------------|----------|
| D1 | SOFT | FAIL | FAIL | STRESS_NOTE_ONLY | **no** (SOFT_NOTE) |
| D2 | SOFT | FAIL | FAIL | STRESS_NOTE_ONLY | **no** (SOFT_NOTE) |
| D3 | SOFT | **PASS** | FAIL | STRESS_NOTE_ONLY | **no** (SOFT_NOTE) |

**No dual HARD_PASS.** Soft PASS ≠ Scalp-arm. STOP after board — no #151 until lock.

### D1 (1D>EMA21 entry only; n_regime=0) — per pair

| Window | Pair | n | exp | term | fee | mix (tp/sl/msb/regime/forced) | BH | term≥BH | term>0 |
|--------|------|---|-----|------|-----|-------------------------------|----|---------|--------|
| TRAIN | BTC | 13 | 15.11346364 | 247.88152976 | 6.52903168 | 6/6/0/0/1 | 43.17666206 | Y | Y |
| TRAIN | ETH | 22 | 0.3064809 | 6.74257988 | 5.7157185 | 7/15/0/0/0 | 45.16769469 | N | Y |
| TRAIN | DOGE | 20 | -0.55172242 | -6.99920454 | 1.50244437 | 5/14/0/0/1 | 20.2301366 | N | N |
| STRESS_2021 | BTC | 18 | -1.01483673 | -18.26706116 | 0.57206935 | 3/15/0/0/0 | 4.18949502 | N | N |
| STRESS_2021 | ETH | 24 | 0.85674128 | 20.56179068 | 7.27683795 | 8/16/0/0/0 | 41.67406045 | N | Y |
| STRESS_2021 | DOGE | 28 | 2.76017728 | 77.28496379 | 8.04661429 | 10/18/0/0/0 | 1065.5538023 | N | Y |
| OOS_2022 | BTC | 2 | 4.7949439 | 9.5898878 | 0.19981389 | 1/1/0/0/0 | -11.38629371 | Y | Y |
| OOS_2022 | ETH | 4 | -0.94714165 | -3.7885666 | 0.41167254 | 1/3/0/0/0 | -14.18345126 | Y | N |
| OOS_2022 | DOGE | 9 | -1.15792762 | -10.42134856 | 1.44784649 | 2/7/0/0/0 | -12.21738051 | Y | N |
| OOS_2023 | BTC | 7 | 0.61543318 | 15.38774589 | 1.20745894 | 2/4/0/0/1 | 16.76353143 | N | Y |
| OOS_2023 | ETH | 9 | -1.82475032 | -16.42275288 | 0.54349035 | 1/8/0/0/0 | 12.25932277 | N | N |
| OOS_2023 | DOGE | 6 | -2.77226153 | -16.6335692 | 0.29978018 | 0/6/0/0/0 | -1.12249166 | N | N |

### D2 (sticky3 1D&lt;EMA21) — per pair

| Window | Pair | n | exp | term | fee | mix | BH | term≥BH | term>0 |
|--------|------|---|-----|------|-----|-----|----|---------|--------|
| TRAIN | BTC | 13 | 15.11346364 | 247.88152976 | 6.52903168 | 6/6/0/0/1 | 43.17666206 | Y | Y |
| TRAIN | ETH | 22 | 0.3064809 | 6.74257988 | 5.7157185 | 7/15/0/0/0 | 45.16769469 | N | Y |
| TRAIN | DOGE | 20 | -0.55172242 | -6.99920454 | 1.50244437 | 5/14/0/0/1 | 20.2301366 | N | N |
| STRESS_2021 | BTC | 20 | -0.93465837 | -18.69316747 | 0.56557644 | 3/16/0/1/0 | 4.18949502 | N | N |
| STRESS_2021 | ETH | 24 | 0.85674128 | 20.56179068 | 7.27683795 | 8/16/0/0/0 | 41.67406045 | N | Y |
| STRESS_2021 | DOGE | 28 | 2.76017728 | 77.28496379 | 8.04661429 | 10/18/0/0/0 | 1065.5538023 | N | Y |
| OOS_2022 | BTC | 2 | 6.80244235 | 13.60488469 | 0.2180621 | 1/0/0/1/0 | -11.38629371 | Y | Y |
| OOS_2022 | ETH | 4 | -0.94714165 | -3.7885666 | 0.41167254 | 1/3/0/0/0 | -14.18345126 | Y | N |
| OOS_2022 | DOGE | 9 | -1.15792762 | -10.42134856 | 1.44784649 | 2/7/0/0/0 | -12.21738051 | Y | N |
| OOS_2023 | BTC | 7 | 0.61543318 | 15.38774589 | 1.20745894 | 2/4/0/0/1 | 16.76353143 | N | Y |
| OOS_2023 | ETH | 9 | -1.82475032 | -16.42275288 | 0.54349035 | 1/8/0/0/0 | 12.25932277 | N | N |
| OOS_2023 | DOGE | 6 | -2.77226153 | -16.6335692 | 0.29978018 | 0/6/0/0/0 | -1.12249166 | N | N |

### D3 (1D EMA50 enter/exit) — per pair

| Window | Pair | n | exp | term | fee | mix | BH | term≥BH | term>0 |
|--------|------|---|-----|------|-----|-----|----|---------|--------|
| TRAIN | BTC | 13 | 15.11346364 | 247.88152976 | 6.52903168 | 6/6/0/0/1 | 43.17666206 | Y | Y |
| TRAIN | ETH | 23 | 1.42755032 | 32.83365733 | 11.04630721 | 8/15/0/0/0 | 45.16769469 | N | Y |
| TRAIN | DOGE | 19 | -0.40176117 | -2.55823656 | 1.60584628 | 5/13/0/0/1 | 20.2301366 | N | N |
| STRESS_2021 | BTC | 21 | -0.91892322 | -19.29738755 | 0.48519713 | 3/18/0/0/0 | 4.18949502 | N | N |
| STRESS_2021 | ETH | 31 | -0.41776627 | -12.95075435 | 4.41200887 | 8/21/0/2/0 | 41.67406045 | N | N |
| STRESS_2021 | DOGE | 23 | 6.45283765 | 148.41526585 | 12.83546245 | 9/14/0/0/0 | 1065.5538023 | N | Y |
| OOS_2022 | BTC | 1 | 19.73906662 | 19.73906662 | 0.17061156 | 1/0/0/0/0 | -11.38629371 | Y | Y |
| OOS_2022 | ETH | 2 | 5.5791957 | 11.1583914 | 0.36750386 | 1/0/0/1/0 | -14.18345126 | Y | Y |
| OOS_2022 | DOGE | 8 | -0.87388099 | -6.99104789 | 2.22357255 | 2/6/0/0/0 | -12.21738051 | Y | N |
| OOS_2023 | BTC | 8 | -0.36212617 | 6.0862618 | 1.39440545 | 2/5/0/0/1 | 16.76353143 | N | Y |
| OOS_2023 | ETH | 8 | -1.6538964 | -13.23117117 | 0.61641244 | 1/6/0/1/0 | 12.25932277 | N | N |
| OOS_2023 | DOGE | 6 | -2.75946187 | -16.55677123 | 0.38275033 | 0/5/0/1/0 | -1.12249166 | N | N |

**n=0 windows:** none (all cells had n>0).
**D1 n_regime:** 0 on every window×pair (asserted).

## BH cites (recompute confirm)

| Window | BTC | ETH | DOGE |
|--------|-----|-----|------|
| TRAIN | 43.17666206 (match) | 45.16769469 (match) | 20.2301366 (locked cite; recompute 20.36962684 Δ0.139) |
| STRESS_2021 | 4.18949502 | 41.67406045 | 1065.5538023 |
| OOS_2022 | −11.38629371 | −14.18345126 | −12.21738051 |
| OOS_2023 | 16.76353143 | 12.25932277 | −1.12249166 |

## Integrity

- `config/default.yaml` sha256 `5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef` / md5 `68e1d9b76f166c2359d8121b449f7ce1` — untouched.
- Fail-closed if 1D missing; reused public_md_149/140 1D (warmup from 2020-01 for EMA50).
- Soft PASS ≠ Scalp-arm · not_a_forecast · no live POST.

## What not to rescue

- T1 demoted; Soft PASS ≠ Scalp-arm.
- No T2; no PEPE until dual-PASS.
- No grind; no #151 until lock.
- Do not edit `config/default.yaml`. Do not place live orders.
