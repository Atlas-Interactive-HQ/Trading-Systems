# Mid #47 DOGE BreakoutV1 1D — set B

**Overall: FAIL**

- Mid: FAIL (clean_pass=[], full+=['B1', 'B3'], holdout_fail=['B1', 'B3'], dd_fail=[], n_trades=[1, 0, 2], TIM=['0.3516', '0.0000', '0.3736'], expectancy=['1.2751', 'NaN', '3.7200'], median_trades=1.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: 1D BreakoutV1 holdouts are thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN (Mid #41/#45 pattern) instead of Mid #36–#44 holdout-exp gate

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 |

**Mid (DOGE BreakoutV1 long-only + same-bar EMA12/30 bull; €40; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 1.2751 | 3.0153 | 2.7044 | 0.0130 | 0.3516 | 15.4978 |
| holdout | 0 | NaN | 1.6953 | 2.1719 | 0.0040 | 0.5357 | 11.7462 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=17.0476, bh_dd=15.49783575); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=1.2751)

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 |

**Mid (DOGE BreakoutV1 long-only + same-bar EMA12/30 bull; €40; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 17.3017 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 6.3017 |
Mid score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=19.0319, bh_dd=17.30169164); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=NaN)

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 |

**Mid (DOGE BreakoutV1 long-only + same-bar EMA12/30 bull; €40; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 2 | 3.7200 | 7.4245 | 1.5312 | 0.0155 | 0.3736 | 56.4265 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 15.3744 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=62.0691, bh_dd=56.42648007); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=3.7200)

**Scalp:** OUT of this trial (halt).

`source: mid_doge_breakout_1d` · `bar: 1D` · `place_orders: false` · `not_a_forecast: true`
