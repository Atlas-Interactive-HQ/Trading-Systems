# 42 — Mid DOGE Donchian 20/10 long/flat (NO EMA; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **plain Donchian breakout** long/flat on **DOGE-USDT 1D** (20/10). **≠ Core EMA12/30**. **≠ phase1/39 BTC Donchian+EMA**. Reuses Donchian / mid_btc_donchian plumbing **without** EMA. Scalp halted. Mid €40 sleeve.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

Both sets reported. Same locked rules. **No strategy param rescue** on FAIL.

## Rule cards (LOCKED)

### No EMA

- **No** EMA12/30 regime filter on entry.
- **No** EMA regime flatten on exit.
- **No** Core-style RETURN / `core_style_return` gate (#41). Holdout-exp Mid like #36.

### Mid — Donchian breakout long (spot DOGE-USDT 1D, €40)

- Entry: close > prior 20-day high (Donchian breakout up). Long only.
- Exit (NO ATR; NO EMA): close < prior 10-day low OR time stop 15 trading days.
- Structural stop for 1.5% risk sizing / engine protective floor = prior 10-day low at entry (not an ATR knob; soft Donchian exit trails via updated prior low).
- Size: 1.5% risk of Mid €40; one position; costs PaperSettings 5+5 bps
- Fill: signal close → next open
- DD cap (PASS): max DD ≤ €16.0 (40% of sleeve start)
- Low-freq: median full-window trades ≤ 15 (FLAG if not)

### Core (informational only)

- Do **not** re-optimize. Report BH / EMA12/30 long sleeve €140 on DOGE-USDT as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only — holdout-exp like #36 `score_mid`)

- Dual-window: PRIMARY_SET_A then ALT_SET_B
- Expectancy after costs > 0 on ≥2 of 3 FULL windows
- On each such window: holdout n_trades≥1 AND holdout expectancy **not worse than** full
- Full-window max DD ≤ 40% of €40 (=€16.0)
- Median trades/window (full) ≤ 15 (if > still score but FLAG)

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (full+ windows=['A1', 'A2', 'A3'], holdout_fail=['A1', 'A2', 'A3'], dd_fail=[], median_trades=3.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 |

**Mid (DOGE Donchian 20/10; NO EMA; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 3 | 0.2387 | 0.7034 | 0.5192 | 0.0127 |
| holdout | 1 | -0.0150 | -0.0188 | 0.5100 | 0.0037 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 |

**Mid (DOGE Donchian 20/10; NO EMA; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 2 | 1.4517 | 2.9000 | 1.4592 | 0.0035 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 |

**Mid (DOGE Donchian 20/10; NO EMA; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 3 | 1.1255 | 3.3657 | 0.7565 | 0.0109 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (full+ windows=['B1', 'B3'], holdout_fail=['B1', 'B3'], dd_fail=[], median_trades=1.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 |

**Mid (DOGE Donchian 20/10; NO EMA; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 1 | 0.4561 | 1.0556 | 1.3814 | 0.0058 |
| holdout | 0 | NaN | 0.5971 | 0.7650 | 0.0014 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 |

**Mid (DOGE Donchian 20/10; NO EMA; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 1 | -0.0121 | -0.0150 | 0.2035 | 0.0029 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 |

**Mid (DOGE Donchian 20/10; NO EMA; NO ATR; time=15d DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 3 | 0.7339 | 2.1936 | 0.6500 | 0.0080 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

## Archive / next-family note

- **FAIL on both sets.** Do **not** grind Donchian N, stops, time stop, risk, or costs.
- Archive this trial. Next-family proposal only (example directions to consider later, not run here): alternate asset sleeve, or a different Mid entry family — not a param rescue of 20/10 Donchian on DOGE.

## What not to rescue

- Do **not** change Donchian lookbacks (20/10), time stop, risk %, costs, or bar size to chase PASS.
- Do **not** add EMA regime, ATR stop, or blend Core/pullback rules.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- Do **not** change `config/default.yaml`.
- On FAIL: archive; propose a **next family** only — no grind.

`source: mid_doge_donchian` · `place_orders: false` · `not_a_forecast: true`
