# 38 — Mid BTC daily EMA pullback long (low-freq; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid daily pullback long on **BTC-USDT 1D** alongside Core EMA regime. Same locked rule card as DOGE #36 (FAIL) — asset swap only; no param grind. Scalp halted.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

Set B run because set A failed — **no strategy param rescue**. Same locked rules.

## Rule cards

### Regime gate

- NEW entries only when **signal-day closed daily EMA12 > EMA30** on BTC-USDT.
- If regime flat/bear: no new entries, **no shorts**.
- Flatten open Mid if EMA12 ≤ EMA30 on a later close (fill next open).

### Mid — daily pullback long (spot BTC-USDT 1D, €40)

- Entry: low ≤ EMA12 within the bar OR prior bar close < EMA12;
  AND signal close > EMA12 AND close > EMA30 (reclaim). Long only.
- Stop: entry_ref − 1.5 × ATR(14, daily)
- Take profit: +2.0R
- Time stop: 10 trading days if neither hit
- Size: 1.5% risk of Mid €40; one position; costs PaperSettings 5+5 bps
- Fill: signal close → next open (EMA family)
- DD cap (PASS): max DD ≤ €16.0 (40% of sleeve start)
- Low-freq: median full-window trades ≤ 15 (**PASS gate**)

### Core (informational only)

- Do **not** re-optimize. Report BH / EMA12/30 long sleeve €140 on BTC-USDT as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only — stricter holdout than DOGE #36)

- Expectancy after costs > 0 on ≥2 of 3 FULL windows
- On each such window: holdout n_trades≥1 AND holdout expectancy **> 0** (not merely not-worse-than-full)
- Full-window max DD ≤ 40% of €40 (=€16.0)
- Median trades/window (full) ≤ 15 (**hard PASS gate**)

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (full+ windows=['A1', 'A2', 'A3'], holdout_fail=['A1', 'A3'], dd_fail=[], median_trades=6.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 78.6981 | 14.3228 | 0 | 0.0700 | 78.4794 | 14.3228 |

**Mid (BTC daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 6 | 0.3657 | 2.1110 | 0.7887 | 0.0830 |
| holdout | 2 | -0.0503 | -0.1241 | 0.7468 | 0.0236 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 144.1046 | 66.7316 | 0 | 0.0700 | 143.8206 | 66.7316 |

**Mid (BTC daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 8 | 0.1460 | 1.4439 | 1.4401 | 0.0422 |
| holdout | 2 | 0.0296 | 0.3555 | 0.6387 | 0.0132 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=True (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 49.9231 | 33.6322 | 1 | 0.1650 | 59.8081 | 40.5475 |

**Mid (BTC daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 5 | 0.3567 | 1.7289 | 1.4595 | 0.0543 |
| holdout | 1 | -0.6084 | -0.6173 | 1.0906 | 0.0089 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (full+ windows=['B1', 'B3'], holdout_fail=['B3'], dd_fail=[], median_trades=4.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 214.6651 | 35.0701 | 0 | 0.0700 | 235.2460 | 37.1423 |

**Mid (BTC daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 4 | 0.9178 | 3.6284 | 0.5451 | 0.0429 |
| holdout | 1 | 0.4932 | 0.4868 | 0.3565 | 0.0064 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=True (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 73.3980 | 22.8127 | 1 | 0.2534 | 100.3948 | 42.7671 |

**Mid (BTC daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 3 | -0.0191 | 0.3297 | 0.9415 | 0.0360 |
| holdout | 0 | NaN | 0.4201 | 0.0408 | 0.0039 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 65.5164 | 32.2473 | 1 | 0.1728 | 72.8674 | 32.0409 |

**Mid (BTC daily pullback atr_stop=1.5 TP=2.0R time=10d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 6 | 0.2004 | 1.1304 | 1.4969 | 0.0722 |
| holdout | 2 | -0.3472 | -0.7145 | 1.4825 | 0.0200 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

## What not to rescue

- Do **not** change ATR mult, TP R, time stop, EMA periods, risk %, or bar size to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On red PnL: try alternate windows (set B) before changing rules.
- Do **not** change `config/default.yaml`.
- Do **not** param-grind the DOGE FAIL rule — BTC asset swap only.

`source: mid_btc_daily_pullback` · `place_orders: false` · `not_a_forecast: true`
