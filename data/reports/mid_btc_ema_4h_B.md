# Mid #49 BTC EMA 4H — set B

**Overall: PASS**

- Mid: PASS (clean_pass=['B1', 'B2'], full+=['B1', 'B2', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[4, 5, 9], TIM=['0.8623', '0.6463', '0.6196'], median_trades=5.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 214.6651 | 35.0701 | 0 | 0.0700 | 235.2460 | 37.1423 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 4 | 5.8795 | 57.6766 | 8.0709 | 0.2230 | 0.8623 | 10.5520 |
| holdout | 1 | -1.3429 | 19.4460 | 2.7751 | 0.0586 | 0.8393 | 3.6936 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.6072, bh_dd=10.55202802); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 73.3980 | 22.8127 | 1 | 0.2534 | 100.3948 | 42.7671 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 5 | 5.5008 | 27.6975 | 6.7515 | 0.3235 | 0.6463 | 12.8255 |
| holdout | 2 | 3.6013 | 7.3380 | 4.7210 | 0.1161 | 0.6235 | 5.0057 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=14.1080, bh_dd=12.82547074); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 65.5164 | 32.2473 | 1 | 0.1728 | 72.8674 | 32.0409 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 9 | 1.2376 | 11.1383 | 5.1226 | 0.4223 | 0.6196 | 9.3082 |
| holdout | 3 | -0.4018 | -1.2053 | 3.6276 | 0.1194 | 0.4821 | 6.1495 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=10.2390, bh_dd=9.3081965); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

`source: mid_btc_ema_4h` · `bar: 4H` · `place_orders: false` · `not_a_forecast: true`
