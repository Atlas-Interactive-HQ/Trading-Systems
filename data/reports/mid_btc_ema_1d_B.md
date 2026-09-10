# Mid #51 BTC EMA 4H — set B

**Overall: PASS**

- Mid: PASS (clean_pass=['B1', 'B2'], full+=['B1', 'B2', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[0, 1, 1], TIM=['0.9011', '0.8315', '0.9890'], median_trades=1.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 214.6651 | 35.0701 | 0 | 0.0700 | 235.2460 | 37.1423 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 61.3328 | 10.0200 | 0.0200 | 0.9011 | 10.6121 |
| holdout | 0 | NaN | 18.8637 | 2.9682 | 0.0200 | 1.0000 | 2.9682 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.6733, bh_dd=10.61207651); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 73.3980 | 22.8127 | 1 | 0.2534 | 100.3948 | 42.7671 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 12.4107 | 20.9708 | 6.5179 | 0.0724 | 0.8315 | 12.2192 |
| holdout | 1 | -0.0717 | 6.4497 | 2.7605 | 0.0599 | 0.7037 | 4.5714 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=13.4411, bh_dd=12.21920259); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 65.5164 | 32.2473 | 1 | 0.1728 | 72.8674 | 32.0409 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 18.7190 | 18.7190 | 9.2136 | 0.0494 | 0.9890 | 9.1546 |
| holdout | 1 | -1.5657 | -1.5657 | 6.0306 | 0.0392 | 0.9643 | 5.9920 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=10.0701, bh_dd=9.15459792); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

`source: mid_btc_ema_1d` · `bar: 1D` · `place_orders: false` · `not_a_forecast: true`
