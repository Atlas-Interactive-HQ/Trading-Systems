# 41 — Mid DOGE EMA12/30 Core-style RETURN gate (Mid sleeve; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **EMA12/30 long/flat** on **DOGE-USDT 1D** — SAME Core rule (`EmaTrendV1` / `walk_long_flat` / three-tier Core arm) at Mid €40. **Gate:** Core-style RETURN (honest reuse of what measured plus). **This gate intentionally differs from Mid #36–#40 holdout-expectancy gate** (fragile low-n). Scalp halted.

## Verdict set A: **PASS**

## Rule cards

### Mid — EMA12/30 long/flat (spot DOGE-USDT 1D, €40)

- Long iff closed-bar **EMA12 > EMA30**; else **flat**. Never short.
- Fill: signal close → next open (EMA family).
- Size: **full sleeve** when long (cash when flat) — `walk_long_flat` / `EmaTrendV1` with equity €40.
- Costs: PaperSettings 5+5 bps.
- DD (PASS): max DD ≤ BH max DD × 1.1 when BH DD available; else absolute DD ≤ €20.0 (50% of sleeve).
- Low n_trades: **OK** (document n_trades / TIM; not a FAIL gate).

### Core (informational only)

- Same rule on DOGE-USDT €140 reported as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only — Core-style RETURN; NOT holdout-exp)

1. A window is **clean** only if: FULL after-costs net return > 0 **and** DD ≤ BH×1.1 (else ≤€20.0) **and** holdout net > 0 (or holdout n=0 & TIM≥0.8 & marked net>0).
2. Need **≥2 of 3** clean windows (Core-style count). Extra full+/holdout-red windows do not veto.
3. Document n_trades / TIM; low n OK (not a FAIL gate).

> **Note:** This gate **intentionally differs** from Mid trials #36–#40 (holdout expectancy / DD€16). Those failed on fragile low-n holdout-exp despite often positive full windows. #41 reuses the Core RETURN measurement that already PASSed on choppy-bull DOGE windows.

## Results — primary set A

**Overall: PASS**

- Mid: PASS (clean_pass=['A1', 'A2'], full+=['A1', 'A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[0, 0, 1], TIM=['0.7473', '1.0000', '0.6854'], median_trades=0.0000; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40'])

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 14.8128 | 7.3777 | 0.0200 | 0.7473 | 7.7517 |
| holdout | 0 | NaN | 2.8612 | 5.7690 | 0.0200 | 1.0000 | 5.7690 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=8.5269, bh_dd=7.75172117); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40))

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 394.8496 | 292.3905 | 0.0200 | 1.0000 | 292.3905 |
| holdout | 0 | NaN | 2.8149 | 8.3167 | 0.0200 | 1.0000 | 8.3167 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=321.6295, bh_dd=292.39046327); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40))

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 29.4166 | 29.4166 | 32.7102 | 0.0547 | 0.6854 | 41.9945 |
| holdout | 1 | -6.9988 | -6.9988 | 12.3279 | 0.0365 | 0.4815 | 15.3100 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=46.1939, bh_dd=41.9944692); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40))

**Scalp:** OUT of this trial (halt).

## What not to rescue

- Do **not** change EMA periods, sleeve size, bar size, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On red PnL: try alternate windows (set B) before changing rules.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#40 holdout-expectancy scoring for this trial.

`source: mid_doge_ema_coregate` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true`
