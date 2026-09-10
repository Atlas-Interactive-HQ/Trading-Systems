# 43 — Mid DOGE RSI(14) mean-reversion long/flat (Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **RSI(14) mean-reversion** long/flat on **DOGE-USDT 1D**. **≠ Core EMA12/30**. **≠ #42 Donchian**. **≠ #41 core_style_return**. Scalp halted. Mid €40 sleeve.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

Both sets reported. Same locked rules. **No strategy param rescue** on FAIL.

## Rule cards (LOCKED)

### No grind / no Core-style gate

- **No** RSI period / threshold / costs grind on FAIL.
- **No** EMA12/30 regime filter on entry.
- **No** Core-style RETURN / `core_style_return` gate (#41). Holdout-exp Mid like #36.

### Mid — RSI(14) mean-reversion long (spot DOGE-USDT 1D, €40)

- Entry: closed-bar RSI(14) **< 30** → long (signal close → next open). Long only.
- Exit: closed-bar RSI(14) **> 50** → flat (next open via exit_hint). Never short.
- Structural stop for 1.5% risk sizing / engine protective floor = close − 10% at entry (not an RSI knob; soft exit remains RSI>50).
- **NO** time stop (RSI exit only; engine time_stop_bars set inert).
- **NO** ATR stop / **NO** take-profit.
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
- Set A AND set B each must PASS under the same rules

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (full+ windows=['A1'], holdout_fail=['A1'], dd_fail=[], median_trades=0.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 |

**Mid (DOGE RSI(14) MR entry<30 exit>50; NO EMA; NO ATR; NO time-stop; DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 1 | 0.3215 | 0.3153 | 0.1344 | 0.0062 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 |

**Mid (DOGE RSI(14) MR entry<30 exit>50; NO EMA; NO ATR; NO time-stop; DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 |

**Mid (DOGE RSI(14) MR entry<30 exit>50; NO EMA; NO ATR; NO time-stop; DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (full+ windows=['B1', 'B2'], holdout_fail=['B1'], dd_fail=[], median_trades=2.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 |

**Mid (DOGE RSI(14) MR entry<30 exit>50; NO EMA; NO ATR; NO time-stop; DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 2 | 0.2691 | 0.5259 | 0.2335 | 0.0123 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 |

**Mid (DOGE RSI(14) MR entry<30 exit>50; NO EMA; NO ATR; NO time-stop; DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 2 | 0.2975 | 0.5828 | 0.6138 | 0.0122 |
| holdout | 2 | 0.2975 | 0.5828 | 0.6138 | 0.0122 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=True (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 |

**Mid (DOGE RSI(14) MR entry<30 exit>50; NO EMA; NO ATR; NO time-stop; DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

## Archive / next-family note

- **FAIL on both sets.** Do **not** grind RSI period, entry/exit thresholds, risk, or costs.
- Archive this trial. Next-family proposal only (example directions to consider later, not run here): alternate asset sleeve, or a different Mid entry family — not a param rescue of RSI(14) <30/>50 on DOGE.

## What not to rescue

- Do **not** change RSI period (14), entry (<30), exit (>50), risk %, costs, or bar size to chase PASS.
- Do **not** add EMA regime, ATR stop, TP, or time-stop grind.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- Do **not** change `config/default.yaml`.
- On FAIL: archive; propose a **next family** only — no grind.

`source: mid_doge_rsi_mr` · `place_orders: false` · `not_a_forecast: true`
