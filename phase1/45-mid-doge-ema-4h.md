# 45 — Mid DOGE EMA12/30 on **4H** Core-style RETURN gate (Mid sleeve; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **EMA12/30 long/flat** on **DOGE-USDT 4H** — SAME Core rule (`EmaTrendV1` / `walk_long_flat` / #41 spirit) at Mid €40. **TF Mid ≠ 1D Core twin #41**. **Gate:** Core-style RETURN (intentional). **`differs_from_holdout_exp_gate: true`** — reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows. Scalp halted.

## Verdict set A: **PASS**
## Verdict set B: **FAIL**

**Dual-window confirmation (A AND B):** FAIL (Set A AND set B each must PASS under the same locked `core_style_return` gate).
On FAIL: **no** EMA period / TF / costs grind; archive; report only. Do not propose Mid param rescue from this trial.

## Rule cards (LOCKED before scoring)

### DD (documented BEFORE scoring)

- DD (PASS): max DD ≤ BH max DD × 1.1 when BH DD available; else absolute DD ≤ €20.0 (50% of Mid €40 sleeve).

### Mid — EMA12/30 long/flat (spot DOGE-USDT **4H**, €40)

- Long iff closed-bar **EMA12 > EMA30**; else **flat**. Never short.
- Fill: signal close → next open (EMA family).
- Size: **full sleeve** when long (cash when flat) — `walk_long_flat` / `EmaTrendV1` with equity €40.
- Costs: PaperSettings 5+5 bps.
- Bar: **4H** (TF Mid ≠ 1D Core twin #41).
- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate).
- Windows: same A/B calendars as recent Mid trials mapped to 4H bars; MD fallbacks labeled.

### Core (informational only)

- Same rule on DOGE-USDT €140 **1D** reported as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only — Core-style RETURN; NOT holdout-exp)

1. A window is **clean** only if: FULL after-costs net return > 0 **and** DD ≤ BH×1.1 (else ≤€20.0) **and** holdout net > 0 (or holdout n=0 & TIM≥0.8 & marked net>0).
2. Need **≥2 of 3** clean windows (Core-style count). Extra full+/holdout-red windows do not veto.
3. Document n_trades / TIM / **expectancy** in tables; low n OK (not a FAIL gate).
4. Set A **AND** set B each must PASS for dual-window confirmation.

> **Note:** `differs_from_holdout_exp_gate: true` — thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows. Mirrors scoring spirit of mid_doge_ema_coregate (#41) adapted to this 4H trial. Prior holdout-exp trials: ['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44'].

## Results — primary set A

**Overall: PASS**

- Mid: PASS (clean_pass=['A1', 'A2'], full+=['A1', 'A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[10, 7, 5], TIM=['0.5996', '0.5574', '0.6037'], median_trades=7.0000; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 51.8446 | 25.8220 | 0 | 0.0700 | 61.3688 | 27.1310 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 10 | 0.8612 | 8.6116 | 9.8068 | 0.4542 | 0.5996 | 10.5470 |
| holdout | 4 | 0.1601 | 0.6403 | 8.1987 | 0.1701 | 0.4881 | 7.6385 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.6017, bh_dd=10.54697536); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 1381.9736 | 1023.3666 | 0 | 0.0700 | 1380.4520 | 1023.3666 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 7 | 41.8858 | 293.2009 | 304.2936 | 1.6286 | 0.5574 | 484.4752 |
| holdout | 2 | 1.9884 | 3.9767 | 6.3666 | 0.0868 | 0.6049 | 10.3131 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=532.9228, bh_dd=484.47523739); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 102.9582 | 114.4858 | 1 | 0.1915 | 97.8395 | 146.9806 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 5 | 7.5713 | 37.8566 | 38.7854 | 0.3564 | 0.6037 | 48.9134 |
| holdout | 2 | -3.7156 | -7.4312 | 9.8714 | 0.0709 | 0.3457 | 17.3368 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=53.8047, bh_dd=48.91335366); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (clean_pass=['B1'], full+=['B1', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[5, 7, 7], TIM=['0.5670', '0.5648', '0.5688'], median_trades=7.0000; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 100.9579 | 53.4298 | 0 | 0.0700 | 104.3781 | 54.2424 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 5 | 2.6469 | 14.1670 | 21.2626 | 0.2472 | 0.5670 | 19.7678 |
| holdout | 1 | 6.1340 | 6.9423 | 18.4266 | 0.0661 | 0.6190 | 15.2273 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=21.7445, bh_dd=19.76776918); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | -8.6474 | 28.2935 | 2 | 0.2741 | 11.4788 | 60.5559 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 7 | -0.0765 | -0.0713 | 9.1005 | 0.3106 | 0.5648 | 19.1126 |
| holdout | 2 | -1.3968 | -2.3563 | 6.5430 | 0.0964 | 0.5062 | 6.2227 |
Mid score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=21.0238, bh_dd=19.1125539); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 272.9236 | 197.4927 | 1 | 0.2765 | 273.6432 | 197.4927 |

**Mid (DOGE EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 7 | 9.4165 | 65.9158 | 34.5170 | 0.4742 | 0.5688 | 71.0556 |
| holdout | 1 | -1.8142 | -1.8142 | 5.0513 | 0.0391 | 0.1786 | 19.8517 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=78.1612, bh_dd=71.05560399); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

## What not to rescue

- Do **not** change EMA periods, sleeve size, bar size, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On FAIL: archive; report only — **no** EMA period / TF / costs grind.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.

`source: mid_doge_ema_4h` · `bar: 4H` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true`
