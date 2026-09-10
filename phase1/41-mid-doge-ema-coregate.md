# 41 — Mid DOGE EMA12/30 Core-style RETURN gate (Mid sleeve; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **EMA12/30 long/flat** on **DOGE-USDT 1D** — SAME Core rule (`EmaTrendV1` / `walk_long_flat` / three-tier Core arm) at Mid €40. **Gate:** Core-style RETURN (honest reuse of what measured plus). **This gate intentionally differs from Mid #36–#40 holdout-expectancy gate** (fragile low-n). Scalp halted.

## Verdict set A: **PASS**
## Verdict set B: **FAIL**

> **Dual-window disclaimer:** #41 is **NOT dual-window robust**. Set A PASSed under `core_style_return`; alternate set B **FAIL**ed (only B1 clean). Do **not** treat set A alone as OOS-confirmed across both window packs. This remains Core-style EMA long/flat on a Mid €40 sleeve — not HF Mid, not a live promote, not auto €200.

**Caveats kept:** gate label `core_style_return` (differs from #36–#40 holdout-exp); holdout `n_trades=0` requires TIM≥0.8 + marked net>0; **A2 Mid max DD ≈ €292 equals BH DD** on a €40 sleeve (relative DD gate only — not a live Mid risk profile).

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


## Results — alternate set B (no param rescue)

**Overall: FAIL**

Measured from `data/reports/mid_doge_ema_coregate_B.json`. Same locked `core_style_return` gate as set A — **no strategy param rescue**.

- Mid: FAIL (clean_pass=['B1'] only; full+=['B1', 'B3']; holdout_fail=['B3']; B2 full net<0; n_trades=[0, 2, 1]; TIM=['0.5714', '0.3933', '0.8901']; median_trades=1.0; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 28.8451 | 15.2657 | 0.0200 | 0.5714 | 15.4978 |
| holdout | 0 | NaN | 12.9730 | 11.7462 | 0.0200 | 1.0000 | 11.7462 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=17.0476, bh_dd=15.49783575); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40)) — **clean**

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on DOGE-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 2 | -1.2353 | -2.4707 | 8.0839 | 0.0783 | 0.3933 | 17.3017 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 6.3017 |
Mid score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=19.0319, bh_dd=17.30169164)) — **FAIL full net<0**

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on DOGE-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 77.9782 | 77.9782 | 56.4265 | 0.0790 | 0.8901 | 56.4265 |
| holdout | 1 | -7.8548 | -7.8548 | 15.3744 | 0.0361 | 0.6429 | 15.3744 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=62.0691, bh_dd=56.42648007); holdout net_return<0) — **FAIL holdout red**

**Scalp:** OUT of this trial (halt).

## What not to rescue

- Do **not** change EMA periods, sleeve size, bar size, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On red PnL: try alternate windows (set B) before changing rules.
- Set B already measured: **FAIL** — do **not** drop set B or rewrite the gate to claim dual-window PASS.
- Do **not** promote #41 to HF Mid live or auto €200; A2 DD≈BH on €40 is a relative-gate artifact.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#40 holdout-expectancy scoring for this trial.

`source: mid_doge_ema_coregate` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true`
