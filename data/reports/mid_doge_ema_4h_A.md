# Mid #45 DOGE EMA 4H — set A

**Overall: PASS**

- Mid: PASS (clean_pass=['A1', 'A2'], full+=['A1', 'A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[10, 7, 5], TIM=['0.5996', '0.5574', '0.6037'], median_trades=7.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 10 | 0.8612 | 8.6116 | 9.8068 | 0.4542 | 0.5996 | 10.5470 |
| holdout | 4 | 0.1601 | 0.6403 | 8.1987 | 0.1701 | 0.4881 | 7.6385 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.6017, bh_dd=10.54697536); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 7 | 41.8858 | 293.2009 | 304.2936 | 1.6286 | 0.5574 | 484.4752 |
| holdout | 2 | 1.9884 | 3.9767 | 6.3666 | 0.0868 | 0.6049 | 10.3131 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=532.9228, bh_dd=484.47523739); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 5 | 7.5713 | 37.8566 | 38.7854 | 0.3564 | 0.6037 | 48.9134 |
| holdout | 2 | -3.7156 | -7.4312 | 9.8714 | 0.0709 | 0.3457 | 17.3368 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=53.8047, bh_dd=48.91335366); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

`source: mid_doge_ema_4h` · `bar: 4H` · `place_orders: false` · `not_a_forecast: true`
