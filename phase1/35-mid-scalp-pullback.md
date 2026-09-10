# 35 — Mid + Scalp EMA pullback long (complements Core spot)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** one pullback-long family, two sleeves (Mid / Scalp). Not BreakoutV1.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

Set B run because set A failed — **no strategy param rescue**. Same locked rules.

## Rule cards

### Regime gate (both sleeves)

- NEW entries only when **prior closed daily EMA12 > EMA30** on DOGE-USDT.
- If regime flat/bear: flat, **no shorts**.
- Also exit open position if daily regime flips to flat at next decision bar.

### Mid — pullback long (spot 15m, €40)

- Entry: dipped below 15m EMA12 within last 3 bars AND close back above EMA12;
  AND close > 15m EMA30; AND daily regime long.
- Stop: entry_ref − 1.5 × ATR(14,15m)
- Take profit: +2.0R
- Time stop: 8 bars (2h)
- Size: 1.5% risk of Mid €40; one position; costs PaperSettings 5+5 bps
- DD cap (PASS): max DD ≤ €16.0 (40% of sleeve start)

### Scalp — same pullback, tighter (SWAP 15m if available, else labeled stand-in ≤2×)

- Same entry gate as Mid
- Stop: entry_ref − 1.0 × ATR(14)
- TP: +1.0R
- Time stop: 3 bars (~45m)
- Leverage sim ≤ 2.0× isolated
- Size: 1.5% risk of Scalp €20; one position; same costs
- DD cap (PASS): max DD ≤ €8.0 (40% of sleeve start)

### Core (informational only)

- Do **not** re-optimize. Report BH / EMA12/30 long sleeve €140 as context only.

### PASS gates

- Mid and Scalp scored **separately**; overall PASS only if **BOTH** pass.
- Expectancy after costs > 0 on ≥2 of 3 primary FULL windows.
- Those windows' holdouts: n_trades≥1 and expectancy not worse than that window's full.
- Max DD on each passing full window ≤ 40% sleeve start (Mid €16 / Scalp €8).
- Missing MD / NaN / 0 trades on scored holdout = FAIL that sleeve.

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (full+ windows=[], holdout_fail=[], dd_fail=[])
- Scalp: FAIL (full+ windows=[], holdout_fail=[], dd_fail=[])
- Core: informational only (not in overall gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: spot15m=8832 daily(pad)=131 scalp_mode=perp_swap

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 |

**Mid (pullback atr_stop=1.5 TP=2.0R time=8 DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 353 | -0.0221 | -18.6161 | 20.4933 | 10.7998 |
| holdout | 141 | -0.0384 | -10.3446 | 12.2415 | 4.9368 |
Mid score: full_pass=False exp>0=False dd_ok=False holdout_ok=None

**Scalp (perp_swap / DOGE-USDT-SWAP; atr_stop=1.0 TP=1.0R time=3 DD_cap=€8.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 462 | -0.0156 | -16.3142 | 16.4764 | 9.0977 |
| holdout | 183 | -0.0285 | -10.2760 | 10.5070 | 5.0587 |
Scalp score: full_pass=False exp>0=False dd_ok=False holdout_ok=None

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: spot15m=8640 daily(pad)=129 scalp_mode=perp_swap

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 |

**Mid (pullback atr_stop=1.5 TP=2.0R time=8 DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 463 | -0.0400 | -27.3619 | 32.4110 | 8.8976 |
| holdout | 142 | -0.0691 | -14.1448 | 15.0632 | 4.4704 |
Mid score: full_pass=False exp>0=False dd_ok=False holdout_ok=None

**Scalp (perp_swap / DOGE-USDT-SWAP; atr_stop=1.0 TP=1.0R time=3 DD_cap=€8.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 596 | -0.0186 | -17.9250 | 19.4614 | 6.8247 |
| holdout | 189 | -0.0419 | -12.4161 | 12.7127 | 4.4692 |
Scalp score: full_pass=False exp>0=False dd_ok=False holdout_ok=None

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: spot15m=8640 daily(pad)=129 scalp_mode=perp_swap

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 |

**Mid (pullback atr_stop=1.5 TP=2.0R time=8 DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 283 | -0.0087 | -11.6226 | 15.4031 | 9.1578 |
| holdout | 55 | -0.0809 | -6.3916 | 8.6619 | 1.9411 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None

**Scalp (perp_swap / DOGE-USDT-SWAP; atr_stop=1.0 TP=1.0R time=3 DD_cap=€8.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 375 | -0.0104 | -11.6380 | 11.6380 | 7.7355 |
| holdout | 71 | -0.0241 | -3.9454 | 4.4820 | 2.2355 |
Scalp score: full_pass=False exp>0=False dd_ok=False holdout_ok=None

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (full+ windows=['B3'], holdout_fail=['B3'], dd_fail=[])
- Scalp: FAIL (full+ windows=[], holdout_fail=[], dd_fail=[])
- Core: informational only (not in overall gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: spot15m=8832 daily(pad)=131 scalp_mode=perp_swap

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 |

**Mid (pullback atr_stop=1.5 TP=2.0R time=8 DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 274 | -0.0130 | -12.4866 | 13.5776 | 8.9253 |
| holdout | 139 | -0.0210 | -7.5555 | 8.4398 | 4.6381 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None

**Scalp (perp_swap / DOGE-USDT-SWAP; atr_stop=1.0 TP=1.0R time=3 DD_cap=€8.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 347 | -0.0231 | -14.7533 | 15.0085 | 6.7422 |
| holdout | 163 | -0.0342 | -9.6640 | 10.0627 | 4.0935 |
Scalp score: full_pass=False exp>0=False dd_ok=False holdout_ok=None

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: spot15m=8640 daily(pad)=129 scalp_mode=perp_swap

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 |

**Mid (pullback atr_stop=1.5 TP=2.0R time=8 DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 183 | -0.0300 | -11.8530 | 13.1844 | 6.3618 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None

**Scalp (perp_swap / DOGE-USDT-SWAP; atr_stop=1.0 TP=1.0R time=3 DD_cap=€8.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 246 | -0.0218 | -12.0384 | 12.5460 | 6.6743 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Scalp score: full_pass=False exp>0=False dd_ok=False holdout_ok=None

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: spot15m=8832 daily(pad)=131 scalp_mode=perp_swap

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 |

**Mid (pullback atr_stop=1.5 TP=2.0R time=8 DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 404 | 0.0154 | -6.6948 | 9.1101 | 12.9161 |
| holdout | 73 | 0.0086 | -2.1584 | 7.2075 | 2.7870 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False

**Scalp (perp_swap / DOGE-USDT-SWAP; atr_stop=1.0 TP=1.0R time=3 DD_cap=€8.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 534 | -0.0134 | -15.5316 | 15.5914 | 8.3805 |
| holdout | 95 | -0.0083 | -3.8064 | 4.9655 | 3.0212 |
Scalp score: full_pass=False exp>0=False dd_ok=False holdout_ok=None

## What not to rescue

- Do **not** change ATR mult, TP R, time stops, EMA periods, dip lookback, risk %, or leverage caps to chase PASS.
- Do **not** re-introduce BreakoutV1 L+S on Mid/Scalp after this family fails.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On red PnL: try alternate windows (set B) before changing rules — already done if A failed.

`source: mid_scalp_pullback` · `place_orders: false` · `not_a_forecast: true`
