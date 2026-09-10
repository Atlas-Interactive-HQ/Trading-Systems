# Scalp #53 BTC EMA 1D — set A

**Overall: PASS**

- Scalp: PASS (clean_pass=['A1', 'A2'], full+=['A1', 'A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[0, 0, 1], TIM=['1.0000', '1.0000', '0.7640'], median_trades=0.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51)
- calendars: Mid #51 (PRIMARY_SET_A / ALT_SET_B / A3_FALLBACK / B3_FALLBACK)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Scalp (BTC EMA12/30 long/flat full-sleeve €20 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 11.2426 | 2.0461 | 0.0100 | 1.0000 | 2.0461 |
| holdout | 0 | NaN | 1.3333 | 1.3971 | 0.0100 | 1.0000 | 1.3971 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=2.2507, bh_dd=2.04613231); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51)))

**Mid / Core:** OUT of this trial.

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Scalp (BTC EMA12/30 long/flat full-sleeve €20 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 20.5863 | 9.5331 | 0.0100 | 1.0000 | 9.5331 |
| holdout | 0 | NaN | 3.9694 | 3.5261 | 0.0100 | 1.0000 | 3.5261 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=10.4864, bh_dd=9.53305033); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51)))

**Mid / Core:** OUT of this trial.

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Scalp (BTC EMA12/30 long/flat full-sleeve €20 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 7.1319 | 7.1319 | 4.8046 | 0.0236 | 0.7640 | 5.7925 |
| holdout | 1 | -1.2754 | -1.2754 | 3.0603 | 0.0194 | 0.4815 | 3.4849 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=6.3717, bh_dd=5.79248575); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51)))

**Mid / Core:** OUT of this trial.

`source: scalp_btc_ema_1d` · `bar: 1D` · `place_orders: false` · `not_a_forecast: true`
