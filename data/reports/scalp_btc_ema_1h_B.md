# Scalp #50 BTC EMA 1H + daily bull — set B

**Overall: FAIL**

- Scalp: FAIL (clean_pass=['B1'], full+=['B1', 'B2', 'B3'], holdout_fail=['B2', 'B3'], dd_fail=[], n_trades=[28, 28, 27], TIM=['0.6209', '0.4870', '0.5824'], expectancy=['0.5012', '0.1313', '0.2982'], median_trades=28.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 / #48 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate
- Daily bull filter: ON for new longs (entry gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 28 | 0.5012 | 16.5311 | 2.9144 | 0.6867 | 0.6209 | 5.3192 |
| holdout | 7 | 0.7569 | 7.1540 | 2.1663 | 0.1568 | 0.7068 | 1.9144 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=5.8511, bh_dd=5.31920988); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.5012)

**Mid / Core:** OUT of this trial.

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 28 | 0.1313 | 3.6304 | 3.9158 | 0.6937 | 0.4870 | 6.5761 |
| holdout | 8 | -0.0218 | -0.2120 | 2.8253 | 0.1703 | 0.4506 | 2.6522 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=7.2338, bh_dd=6.57614209); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.1313)

**Mid / Core:** OUT of this trial.

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 27 | 0.2982 | 8.0513 | 3.0478 | 0.7061 | 0.5824 | 5.1663 |
| holdout | 10 | -0.0859 | -0.8587 | 2.0797 | 0.1948 | 0.4673 | 3.4130 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=5.6829, bh_dd=5.1663125); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.2982)

**Mid / Core:** OUT of this trial.

`source: scalp_btc_ema_1h` · `bar: 1H` · `place_orders: false` · `not_a_forecast: true`
