# Mid #45 DOGE EMA 4H — set B

**Overall: FAIL**

- Mid: FAIL (clean_pass=['B1'], full+=['B1', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[5, 7, 7], TIM=['0.5670', '0.5648', '0.5688'], median_trades=7.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 5 | 2.6469 | 14.1670 | 21.2626 | 0.2472 | 0.5670 | 19.7678 |
| holdout | 1 | 6.1340 | 6.9423 | 18.4266 | 0.0661 | 0.6190 | 15.2273 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=21.7445, bh_dd=19.76776918); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 7 | -0.0765 | -0.0713 | 9.1005 | 0.3106 | 0.5648 | 19.1126 |
| holdout | 2 | -1.3968 | -2.3563 | 6.5430 | 0.0964 | 0.5062 | 6.2227 |
Mid score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=21.0238, bh_dd=19.1125539); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 7 | 9.4165 | 65.9158 | 34.5170 | 0.4742 | 0.5688 | 71.0556 |
| holdout | 1 | -1.8142 | -1.8142 | 5.0513 | 0.0391 | 0.1786 | 19.8517 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=78.1612, bh_dd=71.05560399); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

`source: mid_doge_ema_4h` · `bar: 4H` · `place_orders: false` · `not_a_forecast: true`
