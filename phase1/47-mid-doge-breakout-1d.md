# 47 — Mid DOGE BreakoutV1 long-only 1D + same-bar EMA bull (Mid sleeve; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched** (atr_stop_mult=1.5 research overlay labeled).
**Family:** Mid **BreakoutV1 long-only** on **DOGE-USDT 1D** + **same-bar EMA12>EMA30** bull entry gate; sleeve €40. Reuse BreakoutV1 plumbing (Donchian 16 / ATR SMA14 / oneh off on 1D). **Gate:** Core-style RETURN (intentional). **`differs_from_holdout_exp_gate: true`** — reason: 1D BreakoutV1 holdouts are thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN (Mid #41/#45 pattern) instead of Mid #36–#44 holdout-exp gate. Scalp halted.

> **Gate locked BEFORE score:** `core_style_return` dual-window — set A **and** set B each need ≥2/3 clean windows (FULL net>0 after costs + DD≤BH×1.1 else abs €20 + holdout net>0 or n=0&TIM≥0.8&marked net>0). Expectancy always documented. `differs_from_holdout_exp_gate: true`.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

**Dual-window confirmation (A AND B):** FAIL (Set A AND set B each must PASS under the same locked `core_style_return` gate).
On FAIL: **no** lookback / atr / costs grind; archive; report only. Do not propose Mid param rescue from this trial.

## Rule cards (LOCKED before scoring)

### DD (documented BEFORE scoring)

- DD (PASS): max DD ≤ BH max DD × 1.1 when BH DD available; else absolute DD ≤ €20.0 (50% of Mid €40 sleeve).

### Mid — BreakoutV1 long + same-bar EMA bull (spot DOGE-USDT **1D**, €40)

- Long-only BreakoutV1 (Donchian lookback 16 / ATR SMA14 / atr_stop_mult **1.5** research overlay / `oneh_filter: off` on 1D). Never short.
- **Bull filter:** new longs only when closed-bar **EMA12 > EMA30** on the **same** daily decision bar; else no entry.
- Fill: signal close → **next open** (PaperEngine / BreakoutV1 bar-consistent).
- Size: 1.5% risk of Mid €40; one position; time stop 16 daily bars (lookback-aligned).
- Costs: PaperSettings **5+5 bps**.
- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate).
- Windows: same A/B calendars as recent Mid trials on 1D; MD fallbacks labeled.

### Core (informational only)

- EMA12/30 long / BH on DOGE-USDT €140 **1D** reported as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only — Core-style RETURN; NOT holdout-exp)

1. A window is **clean** only if: FULL after-costs net return > 0 **and** DD ≤ BH×1.1 (else ≤€20.0) **and** holdout net > 0 (or holdout n=0 & TIM≥0.8 & marked net>0).
2. Need **≥2 of 3** clean windows (Core-style count). Extra full+/holdout-red windows do not veto.
3. Document n_trades / TIM / **expectancy** in tables; low n OK (not a FAIL gate).
4. Set A **AND** set B each must PASS for dual-window confirmation.

> **Note:** `differs_from_holdout_exp_gate: true` — 1D BreakoutV1 holdouts are thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN (Mid #41/#45 pattern) instead of Mid #36–#44 holdout-exp gate. Prior holdout-exp trials: ['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44'].

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (clean_pass=['A1'], full+=['A1', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[3, 2, 3], TIM=['0.4066', '0.1236', '0.2697'], expectancy=['0.2824', '-0.6023', '2.4986'], median_trades=3.0000; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=1D BreakoutV1 holdouts are thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN (Mid #41/#45 pattern) instead of Mid #36–#44 holdout-exp gate)

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

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (clean_pass=[], full+=['B1', 'B3'], holdout_fail=['B1', 'B3'], dd_fail=[], n_trades=[1, 0, 2], TIM=['0.3516', '0.0000', '0.3736'], expectancy=['1.2751', 'NaN', '3.7200'], median_trades=1.0000; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=1D BreakoutV1 holdouts are thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN (Mid #41/#45 pattern) instead of Mid #36–#44 holdout-exp gate)

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

## What not to rescue

- Do **not** change lookback, atr_stop, sleeve, bar size, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On FAIL: archive; report only — **no** lookback / atr / costs grind.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.

`source: mid_doge_breakout_1d` · `bar: 1D` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true`
