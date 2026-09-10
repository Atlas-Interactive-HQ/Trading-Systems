# 49 — Mid BTC EMA12/30 on **4H** Core-style RETURN gate (Mid sleeve; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **EMA12/30 long/flat** on **BTC-USDT 4H** — SAME Core rule (`EmaTrendV1` / `walk_long_flat` / #41/#45 spirit) at Mid €40. **Bull TF Mid on BTC** (≠ DOGE #45; asset diversify). **Gate:** Core-style RETURN (intentional). **`differs_from_holdout_exp_gate: true`** — reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows. Scalp halted.

## Verdict set A: **FAIL**
## Verdict set B: **PASS**

**Dual-window confirmation (A AND B):** FAIL (Set A AND set B each must PASS under the same locked `core_style_return` gate).
On FAIL: **no** EMA period / TF / asset / costs grind; archive; report only. Do not propose Mid param rescue from this trial.

## Rule cards (LOCKED before scoring)

### DD (documented BEFORE scoring)

- DD (PASS): max DD ≤ BH max DD × 1.1 when BH DD available; else absolute DD ≤ €20.0 (50% of Mid €40 sleeve).

### Mid — EMA12/30 long/flat (spot BTC-USDT **4H**, €40)

- Long iff closed-bar **EMA12 > EMA30**; else **flat**. Never short.
- Fill: signal close → next open (EMA family).
- Size: **full sleeve** when long (cash when flat) — `walk_long_flat` / `EmaTrendV1` with equity €40.
- Costs: PaperSettings 5+5 bps.
- Bar: **4H** (bull TF Mid on BTC; ≠ DOGE 4H twin #45).
- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate).
- Windows: same A/B calendars as recent Mid trials mapped to BTC 4H bars; MD fallbacks labeled.

### Core (informational only)

- Same rule on BTC-USDT €140 **1D** reported as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only — Core-style RETURN; NOT holdout-exp)

1. A window is **clean** only if: FULL after-costs net return > 0 **and** DD ≤ BH×1.1 (else ≤€20.0) **and** holdout net > 0 (or holdout n=0 & TIM≥0.8 & marked net>0).
2. Need **≥2 of 3** clean windows (Core-style count). Extra full+/holdout-red windows do not veto.
3. Document n_trades / TIM / **expectancy** in tables; low n OK (not a FAIL gate).
4. Set A **AND** set B each must PASS for dual-window confirmation.

> **Note:** `differs_from_holdout_exp_gate: true` — thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows. Mirrors scoring spirit of mid_doge_ema_4h (#45) / mid_doge_ema_coregate (#41) adapted to this BTC 4H trial. Prior holdout-exp trials: ['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44'].

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (clean_pass=['A2'], full+=['A2', 'A3'], holdout_fail=['A3'], dd_fail=['A1'], n_trades=[8, 8, 5], TIM=['0.7500', '0.6537', '0.6630'], median_trades=8.0000; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 78.6981 | 14.3228 | 0 | 0.0700 | 78.4794 | 14.3228 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 8 | 1.4377 | 11.5013 | 7.2176 | 0.3894 | 0.7500 | 5.0322 |
| holdout | 3 | 0.2748 | 0.8244 | 3.7672 | 0.1233 | 0.5714 | 3.3943 |
Mid score: gate=core_style_return full_pass=False net>0=True dd_ok=False holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=5.5354, bh_dd=5.03217413); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 144.1046 | 66.7316 | 0 | 0.0700 | 143.8206 | 66.7316 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 8 | 1.7688 | 16.9500 | 20.1210 | 0.4153 | 0.6537 | 20.2614 |
| holdout | 4 | 0.4925 | 4.1398 | 6.6339 | 0.1827 | 0.6481 | 8.5751 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=22.2875, bh_dd=20.26135539); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 49.9231 | 33.6322 | 1 | 0.1650 | 59.8081 | 40.5475 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 5 | 4.0122 | 20.0610 | 8.1707 | 0.2843 | 0.6630 | 13.1932 |
| holdout | 2 | -0.7006 | -1.4013 | 3.8777 | 0.0785 | 0.3951 | 7.9388 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=14.5125, bh_dd=13.19315021); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: PASS**

- Mid: PASS (clean_pass=['B1', 'B2'], full+=['B1', 'B2', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[4, 5, 9], TIM=['0.8623', '0.6463', '0.6196'], median_trades=5.0000; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 214.6651 | 35.0701 | 0 | 0.0700 | 235.2460 | 37.1423 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 4 | 5.8795 | 57.6766 | 8.0709 | 0.2230 | 0.8623 | 10.5520 |
| holdout | 1 | -1.3429 | 19.4460 | 2.7751 | 0.0586 | 0.8393 | 3.6936 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.6072, bh_dd=10.55202802); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: 4H(pad)=600 trade=540 holdout=162 | daily(pad for Core info)=129

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 73.3980 | 22.8127 | 1 | 0.2534 | 100.3948 | 42.7671 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 5 | 5.5008 | 27.6975 | 6.7515 | 0.3235 | 0.6463 | 12.8255 |
| holdout | 2 | 3.6013 | 7.3380 | 4.7210 | 0.1161 | 0.6235 | 5.0057 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=14.1080, bh_dd=12.82547074); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: 4H(pad)=612 trade=552 holdout=166 | daily(pad for Core info)=131

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 65.5164 | 32.2473 | 1 | 0.1728 | 72.8674 | 32.0409 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **4H**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 9 | 1.2376 | 11.1383 | 5.1226 | 0.4223 | 0.6196 | 9.3082 |
| holdout | 3 | -0.4018 | -1.2053 | 3.6276 | 0.1194 | 0.4821 | 6.1495 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=10.2390, bh_dd=9.3081965); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

## What not to rescue

- Do **not** change EMA periods, sleeve size, bar size, asset, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On FAIL: archive; report only — **no** EMA period / TF / asset / costs grind.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.

`source: mid_btc_ema_4h` · `bar: 4H` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true`
