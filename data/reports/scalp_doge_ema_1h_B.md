# Scalp #48 DOGE EMA 1H + daily bull — set B

**Overall: FAIL**

- Scalp: FAIL (clean_pass=['B1'], full+=['B1', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[18, 14, 30], TIM=['0.3528', '0.2130', '0.5254'], expectancy=['0.6561', '-0.2718', '1.0301'], median_trades=18.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate
- Daily bull filter: ON for new longs (entry gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 18 | 0.6561 | 13.0156 | 5.0107 | 0.4290 | 0.3528 | 10.6267 |
| holdout | 9 | 0.7503 | 7.7666 | 4.2140 | 0.2039 | 0.5997 | 8.1859 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.6894, bh_dd=10.62669187); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.6561)

**Mid / Core:** OUT of this trial.

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 14 | -0.2718 | -3.8054 | 4.8180 | 0.2583 | 0.2130 | 10.1109 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 3.3577 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=11.1220, bh_dd=10.11088231); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=-0.2718)

**Mid / Core:** OUT of this trial.

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 30 | 1.0301 | 30.9031 | 15.5032 | 1.1851 | 0.5254 | 36.5003 |
| holdout | 9 | -0.2533 | -2.2798 | 3.7368 | 0.1748 | 0.2887 | 10.2277 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=40.1503, bh_dd=36.50030387); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=1.0301)

**Mid / Core:** OUT of this trial.

`source: scalp_doge_ema_1h` · `bar: 1H` · `place_orders: false` · `not_a_forecast: true`
