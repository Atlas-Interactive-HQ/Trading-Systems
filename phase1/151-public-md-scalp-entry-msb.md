# Public-MD Scalp #151 — 15m MSB entry pivot (drop 1m BOS)

**Paper / backtest ONLY.** `place_orders: false`. `not_a_forecast`. Soft PASS ≠ arm.
Does **not** edit `config/default.yaml`. No live POST. No invented candles/metrics.

## Lock (from TS Live)

Family pivot = **15m MSB trigger** (drop 1m BOS). Not Q4-soften.

Shared context (same as #142 notebook):
- Pivots: swing high/low = pivot N=3 on that TF closed bars.
- 4H range low = most recent confirmed 4H swing low; "at range low" = 4H low within 0.25×ATR14(4H) of that swing OR 4H close reclaims above it after tagging.
- 1H MSB long = closed 1H breaks prior 1H swing high while 4H range-low context true.
- Volume: reject if 15m RSI(14) makes lower-high while price higher-high into entry (bearish div) — skip trade.
- SL = below the 15m swing low used for the setup − 0.1×ATR14(15m); honor on 1m (intrabar stop if traded through).
- TP = 4R; intrabar limit. Same-bar SL+TP → count as SL (fail-closed).
- No opposite 1H MSB exit. risk_frac=0.25. lev implied ≤10× fail-closed (skip, n_skip_lev). max 1 pos. no martingale. n_time_stop=0. no ATR trail. long-only.
- Fill P1/P2 entry: next 15m open after the 15m MSB close.
- Fill P3 entry: next 1m open after 1m BOS close (same as Q4/#142).
- €20 sleeve, 5+5 bps, accounting_v2.
- Universe: BTC-USDT / ETH-USDT / DOGE-USDT. No USD pairs. No PEPE/shorts/T2.
- T1 stays demoted.

## Cells

| Cell | Trigger | Notes |
|------|---------|-------|
| **P1** | 15m MSB (close > prior 15m swing high) after 1H MSB + 4H range-low; RVOL15≥1.2 on break bar | no 1D regime; no session; fill next 15m open |
| **P2** | P1 + session gate | break-bar open hour UTC in [13,16); else n_skip_session |
| **P3** | CONTROL — Q4 1m BOS + displacement | 15m confirm RVOL≥1.0 → 1m BOS with \|c−c\|≥0.5×ATR14(1m) AND RVOL1m≥1.5; fill next 1m open; not a D-cell |

Mix keys: `tp/sl/msb/regime/forced/session` (regime always 0; session = skip count).

**n=0:** terminal=0; term≥BH if 0≥BH; exp>0 and term>0 waived for that pair.

## Windows / gate

- TRAIN 2020-07-01→2021-01-01
- STRESS 2021-01-01→2021-07-01 (**note only** — cannot make HARD_PASS)
- OOS_2022 2022-01-01→2022-07-01
- OOS_2023 2023-01-01→2023-07-01

**TRAIN PASS:** exp>0 (n=0 waived) ≥2/3 AND terminal≥BH ≥2/3.
**OOS primary PASS:** exp>0 ≥2/3 AND terminal>0 ≥2/3 AND terminal≥BH ≥2/3 (n=0 waives exp>0 and term>0; term=0≥BH if BH≤0).
**DUAL HARD_PASS** = TRAIN PASS AND OOS_2022 PASS AND OOS_2023 PASS.

## Board (measured from `results/public_md_scalp_151.json`)

### Dual HARD_PASS?

| Cell | TRAIN | OOS_2022 | OOS_2023 | 2021 stress | **DUAL** |
|------|-------|----------|----------|-------------|----------|
| P1 | SOFT | FAIL | FAIL | STRESS_NOTE_ONLY | **no** (SOFT_NOTE) |
| P2 | **PASS** | FAIL | **PASS** | STRESS_NOTE_ONLY | **no** (SOFT_NOTE) |
| P3 | FAIL | FAIL | FAIL | STRESS_NOTE_ONLY | **no** (FAIL) |

**No dual HARD_PASS.** Soft PASS ≠ Scalp-arm. STOP — no #152 until lock.

### P1 (15m MSB, no session) — per pair

| Window | Pair | n | exp | term | fee | mix (tp/sl/msb/regime/forced/session) | BH | gap | exp>0 | term>0 | term≥BH |
|--------|------|---|-----|------|-----|---------------------------------------|----|-----|-------|--------|---------|
| TRAIN | BTC | 15 | 1.4857816 | 37.49901964 | 2.95595234 | 5/9/0/0/1/0 | 43.17666206 | −5.67764242 | Y | Y | N |
| TRAIN | ETH | 25 | 2.32901972 | 58.22549306 | 9.76835249 | 9/16/0/0/0/0 | 45.16769469 | 13.05779837 | Y | Y | Y |
| TRAIN | DOGE | 23 | −0.4511798 | −6.32338907 | 3.32865335 | 6/16/0/0/1/0 | 20.2301366 | −26.55352567 | N | N | N |
| STRESS_2021 | BTC | 30 | −0.67395636 | −19.35821388 | 1.27754341 | 5/24/0/0/1/0 | 4.18949502 | −23.5477089 | N | N | N |
| STRESS_2021 | ETH | 41 | −0.47118974 | −19.31877924 | 1.10439843 | 9/32/0/0/0/0 | 41.67406045 | −60.99283969 | N | N | N |
| STRESS_2021 | DOGE | 38 | 0.77406115 | 40.09951671 | 20.61739598 | 12/25/0/0/1/0 | 1065.5538023 | −1025.45428559 | Y | Y | N |
| OOS_2022 | BTC | 21 | −0.95384341 | −19.05189001 | 1.68726343 | 3/17/0/0/1/0 | −11.38629371 | −7.6655963 | N | N | N |
| OOS_2022 | ETH | 21 | −0.8623943 | −18.11028031 | 1.20223471 | 4/17/0/0/0/0 | −14.18345126 | −3.92682905 | N | N | N |
| OOS_2022 | DOGE | 38 | −0.54038963 | −19.99401729 | 0.8935789 | 3/34/0/0/1/0 | −12.21738051 | −7.77663678 | N | N | N |
| OOS_2023 | BTC | 15 | −0.327537 | −2.86303866 | 1.94181532 | 4/10/0/0/1/0 | 16.76353143 | −19.62657009 | N | N | N |
| OOS_2023 | ETH | 17 | −1.04427231 | −17.75262923 | 1.61177815 | 3/14/0/0/0/0 | 12.25932277 | −30.011952 | N | N | N |
| OOS_2023 | DOGE | 20 | −0.98238542 | −19.64770837 | 0.48205568 | 2/18/0/0/0/0 | −1.12249166 | −18.52521671 | N | N | N |

### P2 (P1 + session [13,16) UTC) — per pair

| Window | Pair | n | exp | term | fee | mix | BH | gap | exp>0 | term>0 | term≥BH |
|--------|------|---|-----|------|-----|-----|----|-----|-------|--------|---------|
| TRAIN | BTC | 7 | 15.1128512 | 105.78995842 | 1.51603723 | 4/3/0/0/0/131 | 43.17666206 | 62.61329636 | Y | Y | Y |
| TRAIN | ETH | 12 | 1.56603725 | 22.77232212 | 1.92496597 | 4/7/0/0/1/169 | 45.16769469 | −22.39537257 | Y | Y | N |
| TRAIN | DOGE | 9 | 1.84481728 | 27.18849568 | 0.94806015 | 3/5/0/0/1/102 | 20.2301366 | 6.95835908 | Y | Y | Y |
| STRESS_2021 | BTC | 9 | −1.83005216 | −16.47046941 | 0.80575413 | 1/8/0/0/0/156 | 4.18949502 | −20.65996443 | N | N | N |
| STRESS_2021 | ETH | 17 | 1.44779495 | 24.61251417 | 4.17720574 | 6/11/0/0/0/150 | 41.67406045 | −17.06154628 | Y | Y | N |
| STRESS_2021 | DOGE | 15 | −0.55295589 | −8.29433836 | 1.12882248 | 4/11/0/0/0/138 | 1065.5538023 | −1073.84814066 | N | N | N |
| OOS_2022 | BTC | 8 | −0.9004417 | −7.20353361 | 1.4011645 | 2/6/0/0/0/100 | −11.38629371 | 4.1827601 | N | N | Y |
| OOS_2022 | ETH | 9 | 5.50196061 | 49.51764547 | 2.82577774 | 4/5/0/0/0/114 | −14.18345126 | 63.70109673 | Y | Y | Y |
| OOS_2022 | DOGE | 17 | −1.12639396 | −19.14869727 | 0.68844698 | 2/15/0/0/0/101 | −12.21738051 | −6.93131676 | N | N | N |
| OOS_2023 | BTC | 1 | 15.05890547 | 15.05890547 | 0.02839336 | 0/0/0/0/1/121 | 16.76353143 | −1.70462596 | Y | Y | N |
| OOS_2023 | ETH | 1 | 19.86218997 | 19.86218997 | 0.08853161 | 1/0/0/0/0/108 | 12.25932277 | 7.6028672 | Y | Y | Y |
| OOS_2023 | DOGE | 3 | 0.65303559 | 1.95910678 | 0.340414 | 1/2/0/0/0/92 | −1.12249166 | 3.08159844 | Y | Y | Y |

### P3 (CONTROL: Q4 1m BOS + displacement) — per pair

| Window | Pair | n | exp | term | fee | mix | BH | gap | exp>0 | term>0 | term≥BH |
|--------|------|---|-----|------|-----|-----|----|-----|-------|--------|---------|
| TRAIN | BTC | 8 | −0.90628143 | −7.25025141 | 0.79631377 | 2/6/0/0/0/0 | 43.17666206 | −50.42691347 | N | N | N |
| TRAIN | ETH | 11 | −1.33241554 | −14.65657095 | 1.20501496 | 2/9/0/0/0/0 | 45.16769469 | −59.82426564 | N | N | N |
| TRAIN | DOGE | 8 | −0.85990888 | −6.87927105 | 0.77453062 | 2/6/0/0/0/0 | 20.2301366 | −27.10940765 | N | N | N |
| STRESS_2021 | BTC | 20 | −1.04918504 | −19.91009851 | 0.51032478 | 0/19/0/0/1/0 | 4.18949502 | −24.09959353 | N | N | N |
| STRESS_2021 | ETH | 21 | −0.86614637 | −17.01506532 | 1.18668487 | 4/16/0/0/1/0 | 41.67406045 | −58.68912577 | N | N | N |
| STRESS_2021 | DOGE | 23 | −0.73586228 | −16.92483243 | 1.8965629 | 5/18/0/0/0/0 | 1065.5538023 | −1082.47863473 | N | N | N |
| OOS_2022 | BTC | 8 | −1.90240115 | −15.21920924 | 0.71167053 | 1/7/0/0/0/0 | −11.38629371 | −3.83291553 | N | N | N |
| OOS_2022 | ETH | 18 | −1.0752097 | −19.35377453 | 0.892336 | 2/16/0/0/0/0 | −14.18345126 | −5.17032327 | N | N | N |
| OOS_2022 | DOGE | 14 | −0.28699091 | −4.01787273 | 1.05506393 | 4/10/0/0/0/0 | −12.21738051 | 8.19950778 | N | N | Y |
| OOS_2023 | BTC | 8 | 3.85460814 | 29.77952046 | 1.97938363 | 3/4/0/0/1/0 | 16.76353143 | 13.01598903 | Y | Y | Y |
| OOS_2023 | ETH | 9 | −1.82175776 | −16.39581983 | 1.10067542 | 1/8/0/0/0/0 | 12.25932277 | −28.6551426 | N | N | N |
| OOS_2023 | DOGE | 15 | −1.22498034 | −18.3747051 | 0.61658924 | 2/13/0/0/0/0 | −1.12249166 | −17.25221344 | N | N | N |

**n=0 windows:** none.
**P3 CONTROL:** displacement filter kills TRAIN edge vs Q4 (all three pairs exp<0); not a rescue path.

## BH cites (recompute confirm)

| Window | BTC | ETH | DOGE |
|--------|-----|-----|------|
| TRAIN | 43.17666206 (match) | 45.16769469 (match) | 20.2301366 (locked cite; recompute 20.36962684 Δ0.139) |
| STRESS_2021 | 4.18949502 | 41.67406045 | 1065.5538023 |
| OOS_2022 | −11.38629371 | −14.18345126 | −12.21738051 |
| OOS_2023 | 16.76353143 | 12.25932277 | −1.12249166 |

## Integrity

- `config/default.yaml` sha256 `5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef` / md5 `68e1d9b76f166c2359d8121b449f7ce1` — untouched.
- Reused public_md_125 / 145 / 148 caches (+ 121/131 HTF). Fail-closed if candles missing.
- Soft PASS ≠ Scalp-arm · not_a_forecast · no live POST.

## What not to rescue

- **No dual HARD_PASS** on P1/P2/P3 — Soft PASS ≠ Scalp-arm.
- P1 unfiltered 15m MSB is a fee/SL grind on OOS (exp>0 0/3 on both 2022 and 2023).
- P2 session gate rescues TRAIN + 2023 but **2022 still FAIL** (exp>0 only ETH 1/3). Do not treat session as arm.
- P2 OOS_2023 is thin (n=1/1/3) — not a forecast; Soft PASS ≠ arm.
- P3 CONTROL displacement destroys TRAIN vs Q4; do not promote control alone.
- T1 demoted; no T2; no PEPE until dual-PASS majors.
- Do not grind RVOL / N / ATR / risk / R / session hours.
- 2021 stress not a target.
- **STOP no #152 until lock.**
- Do not edit `config/default.yaml`. Do not place live orders. No live POST.
- Do not invent metrics or candles. Do not edit phase1/120 or phase1/146.
