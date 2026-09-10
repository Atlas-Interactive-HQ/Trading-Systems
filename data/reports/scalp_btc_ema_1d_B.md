# Scalp #53 BTC EMA 1D — set B

**Overall: PASS**

- Scalp: PASS (clean_pass=['B1', 'B2'], full+=['B1', 'B2', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[0, 1, 1], TIM=['0.9011', '0.8315', '0.9890'], median_trades=1.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51)
- calendars: Mid #51 (PRIMARY_SET_A / ALT_SET_B / A3_FALLBACK / B3_FALLBACK)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Scalp (BTC EMA12/30 long/flat full-sleeve €20 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 30.6664 | 5.0100 | 0.0100 | 0.9011 | 5.3060 |
| holdout | 0 | NaN | 9.4318 | 1.4841 | 0.0100 | 1.0000 | 1.4841 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=5.8366, bh_dd=5.30603826); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51)))

**Mid / Core:** OUT of this trial.

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Scalp (BTC EMA12/30 long/flat full-sleeve €20 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 6.2054 | 10.4854 | 3.2590 | 0.0362 | 0.8315 | 6.1096 |
| holdout | 1 | -0.0358 | 3.2249 | 1.3803 | 0.0300 | 0.7037 | 2.2857 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=6.7205, bh_dd=6.10957598); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51)))

**Mid / Core:** OUT of this trial.

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Scalp (BTC EMA12/30 long/flat full-sleeve €20 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 9.3595 | 9.3595 | 4.6068 | 0.0247 | 0.9890 | 4.5773 |
| holdout | 1 | -0.7829 | -0.7829 | 3.0153 | 0.0196 | 0.9643 | 2.9960 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=5.0350, bh_dd=4.57729896); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51)))

**Mid / Core:** OUT of this trial.

`source: scalp_btc_ema_1d` · `bar: 1D` · `place_orders: false` · `not_a_forecast: true`
