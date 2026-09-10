# Scalp #52 BTC EMA 1H + daily bull (confirmation_windows_v2) — set B

**Overall: FAIL**

- Scalp: FAIL (clean_pass=['B1'], full+=['B1'], holdout_fail=[], dd_fail=[], n_trades=[28, 14, 19], TIM=['0.6209', '0.1241', '0.2292'], expectancy=['0.5012', '-0.1818', '-0.1266'], median_trades=19.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 / #48 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate
- Daily bull filter: ON for new longs (entry gate)

### B1 — 2020-10-01 → 2020-12-31 UTC (late-2020 bull run-up)

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 28 | 0.5012 | 16.5311 | 2.9144 | 0.6867 | 0.6209 | 5.3192 |
| holdout | 7 | 0.7569 | 7.1540 | 2.1663 | 0.1568 | 0.7068 | 1.9144 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=5.8511, bh_dd=5.31920988); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.5012)

**Mid / Core:** OUT of this trial.

### B2 — 2023-07-01 → 2023-09-30 UTC (Q3-2023 bull / pre-ETF)

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 14 | -0.1818 | -2.5844 | 2.8023 | 0.2700 | 0.1241 | 4.3265 |
| holdout | 0 | NaN | -0.0446 | 0.0766 | 0.0100 | 0.0119 | 1.0525 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=4.7592, bh_dd=4.32650151); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=-0.1818)

**Mid / Core:** OUT of this trial.

### B3 — 2024-05-01 → 2024-07-31 UTC (post-halving early-summer 2024)

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 19 | -0.1266 | -2.4052 | 3.6664 | 0.3606 | 0.2292 | 5.8554 |
| holdout | 4 | -0.0412 | -0.1650 | 0.9369 | 0.0802 | 0.2351 | 2.1514 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=6.4409, bh_dd=5.85538209); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=-0.1266)

**Mid / Core:** OUT of this trial.

`source: scalp_btc_ema_1h_v2` · `bar: 1H` · `place_orders: false` · `not_a_forecast: true`
