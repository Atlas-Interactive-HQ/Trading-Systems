# 36 — Mid daily EMA pullback long (low-freq; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid daily pullback long alongside Core EMA regime. Scalp halted. Not BreakoutV1.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

Set B run because set A failed — **no strategy param rescue**. Same locked rules.

## Rule cards

### Regime gate

- NEW entries only when **signal-day closed daily EMA12 > EMA30** on DOGE-USDT.
- If regime flat/bear: no new entries, **no shorts**.
- Flatten open Mid if EMA12 ≤ EMA30 on a later close (fill next open).

### Mid — daily pullback long (spot 1D, €40)

- Entry: low ≤ EMA12 within the bar OR prior bar close < EMA12;
  AND signal close > EMA12 AND close > EMA30 (reclaim). Long only.
- Stop: entry_ref − 1.5 × ATR(14, daily)
- Take profit: +2.0R
- Time stop: 10 trading days if neither hit
- Size: 1.5% risk of Mid €40; one position; costs PaperSettings 5+5 bps
- Fill: signal close → next open (EMA family)
- DD cap (PASS): max DD ≤ €16.0 (40% of sleeve start)
- Low-freq sanity: median full-window trades ≤ 15 (FLAG if not)

### Core (informational only)

- Do **not** re-optimize. Report BH / EMA12/30 long sleeve €140 as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only)

- Expectancy after costs > 0 on ≥2 of 3 FULL windows
- On each such window: holdout n_trades≥1 AND holdout expectancy not worse than full
- Full-window max DD ≤ 40% of €40 (=€16.0)
- Median trades/window (full) ≤ 15 (if > still score but FLAG)

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (full+ windows=['A1', 'A2', 'A3'], holdout_fail=['A1', 'A2', 'A3'], dd_fail=[], median_trades=4.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 |

**Mid (daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 4 | 0.6704 | 2.4497 | 0.5572 | 0.0298 |
| holdout | 1 | -0.0969 | -0.2942 | 0.3811 | 0.0085 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 |

**Mid (daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 6 | 0.0137 | 0.0629 | 1.1568 | 0.0193 |
| holdout | 2 | -0.0925 | -0.1935 | 0.7611 | 0.0085 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 |

**Mid (daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 4 | 0.4006 | 1.5794 | 0.6954 | 0.0229 |
| holdout | 1 | -0.6039 | -0.6074 | 0.6588 | 0.0035 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (full+ windows=['B1', 'B3'], holdout_fail=['B1', 'B3'], dd_fail=[], median_trades=3.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 |

**Mid (daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 3 | 0.6915 | 2.4076 | 0.3915 | 0.0242 |
| holdout | 2 | 0.5530 | 1.4414 | 0.3078 | 0.0138 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 |

**Mid (daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 3 | -0.1834 | -0.5684 | 1.2936 | 0.0183 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 |

**Mid (daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 5 | 0.5750 | 2.8489 | 0.6619 | 0.0264 |
| holdout | 1 | -0.0983 | -0.1021 | 0.8186 | 0.0038 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False

**Scalp:** OUT of this trial (halt).

## What not to rescue

- Do **not** change ATR mult, TP R, time stop, EMA periods, risk %, or bar size to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On red PnL: try alternate windows (set B) before changing rules.
- Do **not** change `config/default.yaml`.

`source: mid_daily_pullback` · `place_orders: false` · `not_a_forecast: true`
