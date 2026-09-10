# 39 — Mid BTC Donchian + EMA regime long (new family; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **Donchian breakout** long on **BTC-USDT 1D** + EMA12/30 regime. **Different family** from Mid daily pullback (#38 FAIL). No ATR stop this trial. Scalp halted.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

Set B run because set A failed — **no strategy param rescue**. Same locked rules.

## Rule cards

### Regime gate

- NEW entries only when **signal-day closed daily EMA12 > EMA30** on BTC-USDT.
- If regime flat/bear: no new entries, **no shorts**.
- Flatten open Mid if EMA12 ≤ EMA30 on a later close (fill next open).

### Mid — Donchian breakout long (spot BTC-USDT 1D, €40)

- Entry: close > prior 20-day high (Donchian breakout up). Long only.
- Exit (NO ATR stop): close < prior 10-day low OR EMA12 ≤ EMA30 OR time stop 15 trading days.
- Structural stop for 1.5% risk sizing / engine protective floor = prior 10-day low at entry (not an ATR knob; soft Donchian exit trails via updated prior low).
- Size: 1.5% risk of Mid €40; one position; costs PaperSettings 5+5 bps
- Fill: signal close → next open
- DD cap (PASS): max DD ≤ €16.0 (40% of sleeve start)
- Low-freq: median full-window trades ≤ 15 (**PASS gate**)

### Core (informational only)

- Do **not** re-optimize. Report BH / EMA12/30 long sleeve €140 on BTC-USDT as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only)

- Expectancy after costs > 0 on ≥2 of 3 FULL windows
- On each such window: holdout n_trades≥1 AND holdout expectancy **> 0**
- Full-window max DD ≤ 40% of €40 (=€16.0)
- Median trades/window (full) ≤ 15 (**hard PASS gate**)

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (full+ windows=['A1', 'A2', 'A3'], holdout_fail=['A2', 'A3'], dd_fail=[], median_trades=3.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 78.6981 | 14.3228 | 0 | 0.0700 | 78.4794 | 14.3228 |

**Mid (BTC Donchian 20/10 + EMA regime; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 4 | 0.2010 | 0.7768 | 0.4953 | 0.0273 |
| holdout | 1 | 0.3585 | 0.3529 | 0.3659 | 0.0056 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=True (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 144.1046 | 66.7316 | 0 | 0.0700 | 143.8206 | 66.7316 |

**Mid (BTC Donchian 20/10 + EMA regime; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 3 | 0.1828 | 0.5413 | 0.6198 | 0.0072 |
| holdout | 1 | -0.3925 | -0.3950 | 0.3950 | 0.0025 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 49.9231 | 33.6322 | 1 | 0.1650 | 59.8081 | 40.5475 |

**Mid (BTC Donchian 20/10 + EMA regime; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 3 | 0.5412 | 1.6040 | 0.8270 | 0.0197 |
| holdout | 1 | -0.6050 | -0.6106 | 0.6106 | 0.0055 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (full+ windows=['B1', 'B2', 'B3'], holdout_fail=['B1', 'B2', 'B3'], dd_fail=[], median_trades=3.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 214.6651 | 35.0701 | 0 | 0.0700 | 235.2460 | 37.1423 |

**Mid (BTC Donchian 20/10 + EMA regime; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 3 | 0.7073 | 3.7550 | 0.6236 | 0.0175 |
| holdout | 0 | NaN | 1.5659 | 0.1503 | 0.0020 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 73.3980 | 22.8127 | 1 | 0.2534 | 100.3948 | 42.7671 |

**Mid (BTC Donchian 20/10 + EMA regime; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 2 | 1.4587 | 3.0040 | 0.7998 | 0.0181 |
| holdout | 0 | NaN | 0.0967 | 0.1320 | 0.0011 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 65.5164 | 32.2473 | 1 | 0.1728 | 72.8674 | 32.0409 |

**Mid (BTC Donchian 20/10 + EMA regime; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 4 | 0.1816 | 0.7059 | 1.1762 | 0.0205 |
| holdout | 2 | -0.5572 | -1.1234 | 1.1234 | 0.0090 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: expectancy>0)

**Scalp:** OUT of this trial (halt).

## What not to rescue

- Do **not** add ATR stop, change Donchian lookbacks, EMA periods, time stop, risk %, or bar size to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On red PnL: try alternate windows (set B) before changing rules.
- Do **not** change `config/default.yaml`.
- This is a **new family** vs pullback — do not blend pullback reclaim rules back in.

`source: mid_btc_donchian_ema` · `place_orders: false` · `not_a_forecast: true`
