# 44 — Mid DOGE Donchian 20/10 long/flat on **1H** (NO EMA; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **plain Donchian breakout** long/flat on **DOGE-USDT 1H** (20/10). **TF-shift vs failed #42 1D** — **same N 20/10** (NOT a Donchian-N grind). **≠ Core EMA12/30**. **≠ phase1/39 BTC Donchian+EMA**. Reuses Donchian / Mid #42 harness **without** EMA on 1H MD. Scalp halted. Mid €40 sleeve.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

Both sets reported. Same locked rules. Set A AND set B each must PASS for confirmation. **No strategy param rescue** on FAIL. On FAIL: archive; **stop Mid auto-chain** (do not propose/start #45); no N/stops/costs/TF grind.

## Rule cards (LOCKED)

### No EMA / no grind

- **No** EMA12/30 regime filter on entry.
- **No** EMA regime flatten on exit.
- **No** Core-style RETURN / `core_style_return` gate (#41). Holdout-exp Mid like #36.
- **No** Donchian-N / stops / costs / TF grind on FAIL (this *is* the TF-shift trial).

### Mid — Donchian breakout long (spot DOGE-USDT **1H**, €40)

- Entry: close > prior 20-bar high (Donchian breakout up). Long only.
- Exit (NO ATR; NO EMA): close < prior 10-bar low OR time stop 15 × 1H bars.
- Structural stop for 1.5% risk sizing / engine protective floor = prior 10-bar low at entry (not an ATR knob; soft Donchian exit trails via updated prior low).
- Size: 1.5% risk of Mid €40; one position; costs PaperSettings 5+5 bps
- Fill: signal close → next open
- DD cap (PASS): max DD ≤ €16.0 (40% of sleeve start)
- Low-freq: median full-window trades ≤ 15 (FLAG if not)
- Windows: same A/B calendars as #42/#43 mapped to 1H bars; MD fallbacks labeled

### Core (informational only)

- Do **not** re-optimize. Report BH / EMA12/30 long sleeve €140 on DOGE-USDT **1D** as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only — holdout-exp like #36 `score_mid`)

- Dual-window: PRIMARY_SET_A then ALT_SET_B
- Expectancy after costs > 0 on ≥2 of 3 FULL windows
- On each such window: holdout n_trades≥1 AND holdout expectancy **not worse than** full
- Full-window max DD ≤ 40% of €40 (=€16.0)
- Median trades/window (full) ≤ 15 (if > still score but FLAG)
- Set A AND set B each must PASS under the same rules for confirmation

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (full+ windows=['A1', 'A2', 'A3'], holdout_fail=['A1', 'A2'], dd_fail=[], median_trades=45.0000) FLAG:not-low-freq
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 |

**Mid (DOGE Donchian 20/10 1H; NO EMA; NO ATR; time=15×1H DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 49 | 0.0099 | -0.7007 | 3.1692 | 1.1840 |
| holdout | 12 | -0.1743 | -2.3208 | 3.0386 | 0.2291 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 |

**Mid (DOGE Donchian 20/10 1H; NO EMA; NO ATR; time=15×1H DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 36 | 0.2034 | 6.8716 | 3.1894 | 0.4499 |
| holdout | 13 | 0.0478 | 0.3923 | 2.7485 | 0.2289 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 |

**Mid (DOGE Donchian 20/10 1H; NO EMA; NO ATR; time=15×1H DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 45 | 0.0313 | 0.7183 | 2.8883 | 0.6891 |
| holdout | 10 | 0.0864 | 0.7425 | 0.7012 | 0.1210 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=True (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (full+ windows=['B3'], holdout_fail=['B3'], dd_fail=[], median_trades=44.0000) FLAG:not-low-freq
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 |

**Mid (DOGE Donchian 20/10 1H; NO EMA; NO ATR; time=15×1H DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 42 | -0.0552 | -3.2257 | 6.3565 | 0.9066 |
| holdout | 10 | 0.2581 | 2.4106 | 1.6412 | 0.1707 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 |

**Mid (DOGE Donchian 20/10 1H; NO EMA; NO ATR; time=15×1H DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 44 | -0.0816 | -4.1263 | 7.2673 | 0.8069 |
| holdout | 12 | -0.0934 | -1.0546 | 2.2940 | 0.2295 |
Mid score: full_pass=False exp>0=False dd_ok=True holdout_ok=None (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 |

**Mid (DOGE Donchian 20/10 1H; NO EMA; NO ATR; time=15×1H DD_cap=€16.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 46 | 0.1387 | 5.3217 | 3.0713 | 0.6687 |
| holdout | 9 | -0.0386 | -0.8175 | 1.6143 | 0.1326 |
Mid score: full_pass=True exp>0=True dd_ok=True holdout_ok=False (holdout rule: not worse than full)

**Scalp:** OUT of this trial (halt).

## Archive / stop Mid auto-chain

- **FAIL on both sets.**
- Do **not** grind Donchian N, stops, time stop, risk, costs, or TF further.
- Archive this trial. **Stop Mid auto-chain** — do **not** propose or start #45.

## What not to rescue

- Do **not** change Donchian lookbacks (20/10), time stop, risk %, costs, or bar size to chase PASS.
- Do **not** add EMA regime, ATR stop, or blend Core/pullback rules.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- Do **not** change `config/default.yaml`.
- On FAIL: archive; **stop Mid auto-chain** (no #45); no grind.

`source: mid_doge_donchian_1h` · `place_orders: false` · `not_a_forecast: true`
