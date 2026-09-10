# Mid #47 DOGE BreakoutV1 1D — set A

**Overall: FAIL**

- Mid: FAIL (clean_pass=['A1'], full+=['A1', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[3, 2, 3], TIM=['0.4066', '0.1236', '0.2697'], expectancy=['0.2824', '-0.6023', '2.4986'], median_trades=3.0000; low_n_ok=True)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True
- differs_reason: 1D BreakoutV1 holdouts are thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN (Mid #41/#45 pattern) instead of Mid #36–#44 holdout-exp gate

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 |

**Mid (DOGE BreakoutV1 long-only + same-bar EMA12/30 bull; €40; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | 0.2824 | 0.8194 | 1.2181 | 0.0278 | 0.4066 | 7.7517 |
| holdout | 1 | 0.1898 | 0.1808 | 1.1991 | 0.0089 | 0.6071 | 5.7690 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=8.5269, bh_dd=7.75172117); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.2824)

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 |

**Mid (DOGE BreakoutV1 long-only + same-bar EMA12/30 bull; €40; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 2 | -0.6023 | -1.2111 | 2.9674 | 0.0065 | 0.1236 | 292.3905 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 8.3167 |
Mid score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=321.6295, bh_dd=292.39046327); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=-0.6023)

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 |

**Mid (DOGE BreakoutV1 long-only + same-bar EMA12/30 bull; €40; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 3 | 2.4986 | 7.4669 | 1.6228 | 0.0289 | 0.2697 | 41.9945 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 15.3100 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=46.1939, bh_dd=41.9944692); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=2.4986)

**Scalp:** OUT of this trial (halt).

`source: mid_doge_breakout_1d` · `bar: 1D` · `place_orders: false` · `not_a_forecast: true`
