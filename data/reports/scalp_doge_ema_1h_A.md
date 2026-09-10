# Scalp #48 DOGE EMA 1H + daily bull — set A

**Overall: FAIL**

- Scalp: FAIL (clean_pass=['A2'], full+=['A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[31, 33, 22], TIM=['0.4275', '0.4907', '0.3875'], expectancy=['-0.0264', '2.5542', '0.6690'], median_trades=31.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate
- Daily bull filter: ON for new longs (entry gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 31 | -0.0264 | -0.8184 | 6.1590 | 0.6366 | 0.4275 | 5.5954 |
| holdout | 14 | -0.1147 | -1.6057 | 5.9062 | 0.2876 | 0.4881 | 4.0524 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=False holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=6.1550, bh_dd=5.59543443); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=-0.0264)

**Mid / Core:** OUT of this trial.

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 33 | 2.5542 | 84.2875 | 180.2250 | 2.8954 | 0.4907 | 242.2376 |
| holdout | 10 | 0.0340 | 0.3404 | 4.8508 | 0.2143 | 0.5216 | 5.1566 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=266.4614, bh_dd=242.2376187); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=2.5542)

**Mid / Core:** OUT of this trial.

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 22 | 0.6690 | 14.7172 | 13.2060 | 0.6683 | 0.3875 | 24.4567 |
| holdout | 6 | -0.2848 | -1.7086 | 4.2617 | 0.1199 | 0.2068 | 8.7653 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=26.9023, bh_dd=24.45667683); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.6690)

**Mid / Core:** OUT of this trial.

`source: scalp_doge_ema_1h` · `bar: 1H` · `place_orders: false` · `not_a_forecast: true`
