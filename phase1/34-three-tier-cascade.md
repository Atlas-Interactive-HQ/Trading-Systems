# 34 — Three-Tier Cascading stack (FIRST locked backtest)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` breakout `atr_stop_mult: 1.5` **untouched** (live default).

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

Set B run because set A failed — **no strategy param rescue**. Same locked rules.

## Rule cards

### Capital (locked)

| Sleeve | Start € | Share | Role |
|---|---:|---:|---|
| Core | 140 | 70% | Long-bias hold ~3m |
| Mid | 40 | 20% | 15m BreakoutV1 L+S |
| Scalp | 20 | 10% | Perp proxy, highest turnover |
| **Total** | **200** | **7:2:1** | One-way Scalp→Mid→Core |

- **Cascade:** weekly transfer of realized profit upward; min €1; **no downward refill**.
- **Depletion:** Mid/Scalp halt when equity ≤ 0 until manual inject (modeled as halt).
- **Kill:** 5% of sleeve day_start → no new entries that UTC day for that sleeve.

### Core

- **Rule (documented):** `ema12_30_long_only` — EMA12/30 long-only on daily DOGE-USDT; flat in bear legs.
- Not buy-and-hold for the scored arm; BH kept as benchmark only.
- Book: €140, 1×, PaperSettings fee+slip.

### Mid

- BreakoutV1 L+S, lookback 16, ATR 14, **atr_stop_mult=1.5** (locked default),
  min_atr_frac 0.001, time_stop 16, oneh_filter stub, ranging OFF.
- MD: DOGE-USDT 15m research spot proxy. Size from Mid equity, 1.5% risk, one position.

### Scalp

- Prefer DOGE-USDT-SWAP 15m (perpetual proxy). Leverage default 2.0×,
  hard cap 3.0× isolated. Same BreakoutV1 params as Mid.
- If SWAP MD unavailable: FAIL-closed that sleeve **or** labeled stand-in
  `standin_15m_breakout_2x_lev_on_spot` (never silent). Prefer NOT 3x ETF tokens.

### PASS gates (all must hold)

1. **Mid:** expectancy after costs > 0 on ≥2/3 primary FULL windows; holdout n_trades≥1
   with expectancy not worse than full on windows where full passed.
2. **Scalp:** same bar; MD unavailable → FAIL-closed.
3. **Core:** after-costs return ≥ 0 OR (return > BH AND DD ≤ BH×1.10) on ≥2/3.
4. **Cascade:** document upward transfers > 0 across profitable Mid/Scalp windows (informational).
5. Missing data / NaN = FAIL for affected sleeve.

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (full+ windows=[], holdout_fail=[])
- Scalp: FAIL (full+ windows=[], holdout_fail=[])
- Core: PASS (pass windows=['A1', 'A2', 'A3'])
- Cascade (informational): upward € sum on profitable windows = 0.0000 (n_profitable=0)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: spot15m=8832 daily(pad)=131 scalp_mode=perp_swap

**Core (EMA12/30 long-only)**

| arm | net € | max DD € | n_trades | fee € | vs BH net € | vs BH DD € | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 | PASS |

**Mid (BreakoutV1 atr_stop_mult=1.5)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 315 | -0.0567 | -30.2046 | 30.8177 | 12.3545 |
| holdout | 101 | -0.0740 | -13.8915 | 20.4451 | 6.4167 |

**Scalp (perp_swap / DOGE-USDT-SWAP)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 305 | -0.0313 | -15.3440 | 15.7333 | 5.8434 |
| holdout | 97 | -0.0335 | -6.2738 | 9.6959 | 3.1551 |

Cascade transfers this window: n=19, sum_eur=45.2557; mid/scalp profitable=False
Depletion: scalp halted (n_halts=1)

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: spot15m=8640 daily(pad)=129 scalp_mode=perp_swap

**Core (EMA12/30 long-only)**

| arm | net € | max DD € | n_trades | fee € | vs BH net € | vs BH DD € | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 | PASS |

**Mid (BreakoutV1 atr_stop_mult=1.5)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 290 | -0.0585 | -25.6175 | 46.0636 | 8.6581 |
| holdout | 83 | -0.1776 | -18.5758 | 20.2375 | 3.8380 |

**Scalp (perp_swap / DOGE-USDT-SWAP)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 287 | -0.0161 | -9.9629 | 28.1869 | 5.3342 |
| holdout | 80 | -0.0892 | -9.0219 | 9.5078 | 1.8882 |

Cascade transfers this window: n=17, sum_eur=126.5313; mid/scalp profitable=False
Depletion: mid halted (n_halts=1); scalp halted (n_halts=1)

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: spot15m=8640 daily(pad)=129 scalp_mode=perp_swap

**Core (EMA12/30 long-only)**

| arm | net € | max DD € | n_trades | fee € | vs BH net € | vs BH DD € | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 | PASS |

**Mid (BreakoutV1 atr_stop_mult=1.5)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 312 | -0.0320 | -20.9103 | 22.5932 | 10.9209 |
| holdout | 85 | 0.0011 | -4.3355 | 11.8651 | 4.4288 |

**Scalp (perp_swap / DOGE-USDT-SWAP)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 308 | -0.0180 | -10.8811 | 11.5770 | 5.3491 |
| holdout | 87 | 0.0074 | -1.6845 | 6.2271 | 2.3267 |

Cascade transfers this window: n=20, sum_eur=69.3503; mid/scalp profitable=False
Depletion: mid halted (n_halts=1); scalp halted (n_halts=1)

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (full+ windows=[], holdout_fail=[])
- Scalp: FAIL (full+ windows=[], holdout_fail=[])
- Core: PASS (pass windows=['B1', 'B3'])
- Cascade (informational): upward € sum on profitable windows = 0.0000 (n_profitable=0)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: spot15m=8832 daily(pad)=131 scalp_mode=perp_swap

**Core (EMA12/30 long-only)**

| arm | net € | max DD € | n_trades | fee € | vs BH net € | vs BH DD € | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 | PASS |

**Mid (BreakoutV1 atr_stop_mult=1.5)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 293 | -0.0727 | -30.8397 | 32.5510 | 9.5376 |
| holdout | 92 | -0.0477 | -9.1812 | 20.1868 | 4.7965 |

**Scalp (perp_swap / DOGE-USDT-SWAP)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 299 | -0.0310 | -14.6468 | 15.0192 | 5.3854 |
| holdout | 91 | -0.0072 | -3.3462 | 10.1754 | 2.6874 |

Cascade transfers this window: n=16, sum_eur=41.7550; mid/scalp profitable=False
Depletion: scalp halted (n_halts=1)

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: spot15m=8640 daily(pad)=129 scalp_mode=perp_swap

**Core (EMA12/30 long-only)**

| arm | net € | max DD € | n_trades | fee € | vs BH net € | vs BH DD € | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 | FAIL |

**Mid (BreakoutV1 atr_stop_mult=1.5)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 280 | -0.0642 | -28.9045 | 32.2166 | 10.9405 |
| holdout | 82 | -0.0537 | -9.5341 | 9.8907 | 5.1279 |

**Scalp (perp_swap / DOGE-USDT-SWAP)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 274 | -0.0330 | -14.4858 | 15.7444 | 5.4491 |
| holdout | 85 | -0.0313 | -5.3044 | 5.5706 | 2.6434 |

Cascade transfers this window: n=18, sum_eur=55.7609; mid/scalp profitable=False
Depletion: mid halted (n_halts=1); scalp halted (n_halts=1)

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: spot15m=8832 daily(pad)=131 scalp_mode=perp_swap

**Core (EMA12/30 long-only)**

| arm | net € | max DD € | n_trades | fee € | vs BH net € | vs BH DD € | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 | PASS |

**Mid (BreakoutV1 atr_stop_mult=1.5)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 315 | -0.0664 | -30.1159 | 33.1667 | 9.2061 |
| holdout | 86 | -0.1097 | -13.4252 | 14.7427 | 3.9894 |

**Scalp (perp_swap / DOGE-USDT-SWAP)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |
|---|---:|---:|---:|---:|---:|
| full | 313 | -0.0330 | -14.9205 | 16.4288 | 4.5793 |
| holdout | 87 | -0.0573 | -6.9812 | 7.6217 | 1.9952 |

Cascade transfers this window: n=14, sum_eur=53.2614; mid/scalp profitable=False
Depletion: mid halted (n_halts=1); scalp halted (n_halts=1)

## What not to rescue

- Do **not** change `atr_stop_mult`, lookback, EMA periods, risk %, or leverage caps to chase PASS.
- Do **not** enable downward refill or auto-inject to mask depletion.
- Do **not** silently swap atr_stop_mult=3.0 (candidate elsewhere) into Mid.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.

`source: three_tier_cascade` · `place_orders: false` · `not_a_forecast: true`
