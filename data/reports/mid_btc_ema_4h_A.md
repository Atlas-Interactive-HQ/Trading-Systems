# Mid #49 BTC EMA 4H — set A

**Overall: FAIL**

- Mid: FAIL (clean_pass=['A2'], full+=['A2', 'A3'], holdout_fail=['A3'], dd_fail=['A1'], n_trades=[8, 8, 5], TIM=['0.7500', '0.6537', '0.6630'], median_trades=8.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 78.6981 | 14.3228 | 0 | 0.0700 | 78.4794 | 14.3228 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 8 | 1.4377 | 11.5013 | 7.2176 | 0.3894 | 0.7500 | 5.0322 |
| holdout | 3 | 0.2748 | 0.8244 | 3.7672 | 0.1233 | 0.5714 | 3.3943 |
Mid score: gate=core_style_return full_pass=False net>0=True dd_ok=False holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=5.5354, bh_dd=5.03217413); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 144.1046 | 66.7316 | 0 | 0.0700 | 143.8206 | 66.7316 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 8 | 1.7688 | 16.9500 | 20.1210 | 0.4153 | 0.6537 | 20.2614 |
| holdout | 4 | 0.4925 | 4.1398 | 6.6339 | 0.1827 | 0.6481 | 8.5751 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=22.2875, bh_dd=20.26135539); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 49.9231 | 33.6322 | 1 | 0.1650 | 59.8081 | 40.5475 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 5 | 4.0122 | 20.0610 | 8.1707 | 0.2843 | 0.6630 | 13.1932 |
| holdout | 2 | -0.7006 | -1.4013 | 3.8777 | 0.0785 | 0.3951 | 7.9388 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=14.5125, bh_dd=13.19315021); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

`source: mid_btc_ema_4h` · `bar: 4H` · `place_orders: false` · `not_a_forecast: true`
