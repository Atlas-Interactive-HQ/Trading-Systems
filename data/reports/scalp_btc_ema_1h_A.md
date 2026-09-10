# Scalp #50 BTC EMA 1H + daily bull — set A

**Overall: PASS**

- Scalp: PASS (clean_pass=['A1', 'A2'], full+=['A1', 'A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[36, 34, 28], TIM=['0.6137', '0.6144', '0.4782'], expectancy=['0.1681', '0.3816', '0.1014'], median_trades=34.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 / #48 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate
- Daily bull filter: ON for new longs (entry gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 36 | 0.1681 | 5.9463 | 2.7434 | 0.8608 | 0.6137 | 2.8391 |
| holdout | 11 | 0.0323 | 0.2736 | 2.1436 | 0.2453 | 0.5223 | 1.9150 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=3.1230, bh_dd=2.83911076); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.1681)

**Mid / Core:** OUT of this trial.

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 34 | 0.3816 | 13.0356 | 5.8178 | 1.0012 | 0.6144 | 10.3864 |
| holdout | 12 | 0.1079 | 1.3342 | 3.7571 | 0.2683 | 0.6543 | 4.4010 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.4251, bh_dd=10.386421); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.3816)

**Mid / Core:** OUT of this trial.

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 28 | 0.1014 | 2.8398 | 3.8546 | 0.6343 | 0.4782 | 6.6995 |
| holdout | 4 | -0.0738 | -0.2950 | 1.4066 | 0.0804 | 0.2562 | 3.9694 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=7.3694, bh_dd=6.69948821); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.1014)

**Mid / Core:** OUT of this trial.

`source: scalp_btc_ema_1h` · `bar: 1H` · `place_orders: false` · `not_a_forecast: true`
