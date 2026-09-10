# 51 — Mid BTC EMA12/30 on **1D** Core-style RETURN gate (Mid sleeve; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **EMA12/30 long/flat** on **BTC-USDT 1D** — SAME Core rule (`EmaTrendV1` / `walk_long_flat` / #41/#45/#49 spirit) at Mid €40. **Daily Core-rule on BTC** (≠ 4H Mid #49). **Gate:** Core-style RETURN (intentional). **`differs_from_holdout_exp_gate: true`** — reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows. Scalp halted. **Live:** BTC = **research-only** for live.

## Verdict set A: **PASS**
## Verdict set B: **PASS**

**Dual-window confirmation (A AND B):** PASS (Set A AND set B each must PASS under the same locked `core_style_return` gate).

## Rule cards (LOCKED before scoring)

### DD (documented BEFORE scoring)

- DD (PASS): max DD ≤ BH max DD × 1.1 when BH DD available; else absolute DD ≤ €20.0 (50% of Mid €40 sleeve).

### Mid — EMA12/30 long/flat (spot BTC-USDT **1D**, €40)

- Long iff closed-bar **EMA12 > EMA30**; else **flat**. Never short.
- Fill: signal close → next open (EMA family).
- Size: **full sleeve** when long (cash when flat) — `walk_long_flat` / `EmaTrendV1` with equity €40.
- Costs: PaperSettings 5+5 bps.
- Bar: **1D** (daily Core-rule on BTC Mid; ≠ 4H #49).
- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate).
- Windows: same A/B calendars as recent Mid trials mapped to BTC 1D bars; MD fallbacks labeled.

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

> **Note:** `differs_from_holdout_exp_gate: true` — thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows. Mirrors scoring spirit of mid_doge_ema_coregate (#41) / mid_doge_ema_4h (#45) / mid_btc_ema_4h (#49) adapted to this BTC **1D** trial. Prior holdout-exp trials: ['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44'].

## Results — primary set A

**Overall: PASS**

- Mid: PASS (clean_pass=['A1', 'A2'], full+=['A1', 'A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[0, 0, 1], TIM=['1.0000', '1.0000', '0.7640'], median_trades=0.0000; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 78.6981 | 14.3228 | 0 | 0.0700 | 78.4794 | 14.3228 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 22.4851 | 4.0922 | 0.0200 | 1.0000 | 4.0922 |
| holdout | 0 | NaN | 2.6667 | 2.7943 | 0.0200 | 1.0000 | 2.7943 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=4.5015, bh_dd=4.09223682); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 144.1046 | 66.7316 | 0 | 0.0700 | 143.8206 | 66.7316 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 41.1726 | 19.0661 | 0.0200 | 1.0000 | 19.0661 |
| holdout | 0 | NaN | 7.9387 | 7.0521 | 0.0200 | 1.0000 | 7.0521 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=20.9727, bh_dd=19.06610067); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 49.9231 | 33.6322 | 1 | 0.1650 | 59.8081 | 40.5475 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 14.2637 | 14.2637 | 9.6092 | 0.0471 | 0.7640 | 11.5850 |
| holdout | 1 | -2.5508 | -2.5508 | 6.1206 | 0.0387 | 0.4815 | 6.9697 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=12.7435, bh_dd=11.58497151); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: PASS**

- Mid: PASS (clean_pass=['B1', 'B2'], full+=['B1', 'B2', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[0, 1, 1], TIM=['0.9011', '0.8315', '0.9890'], median_trades=1.0000; low_n_ok=True)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 214.6651 | 35.0701 | 0 | 0.0700 | 235.2460 | 37.1423 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 61.3328 | 10.0200 | 0.0200 | 0.9011 | 10.6121 |
| holdout | 0 | NaN | 18.8637 | 2.9682 | 0.0200 | 1.0000 | 2.9682 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.6733, bh_dd=10.61207651); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 73.3980 | 22.8127 | 1 | 0.2534 | 100.3948 | 42.7671 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 12.4107 | 20.9708 | 6.5179 | 0.0724 | 0.8315 | 12.2192 |
| holdout | 1 | -0.0717 | 6.4497 | 2.7605 | 0.0599 | 0.7037 | 4.5714 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=13.4411, bh_dd=12.21920259); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT 1D €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 65.5164 | 32.2473 | 1 | 0.1728 | 72.8674 | 32.0409 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40 on **1D**; Core-style RETURN gate; DD≤BH×1.1 else ≤€20.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 18.7190 | 18.7190 | 9.2136 | 0.0494 | 0.9890 | 9.1546 |
| holdout | 1 | -1.5657 | -1.5657 | 6.0306 | 0.0392 | 0.9643 | 5.9920 |
Mid score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=10.0701, bh_dd=9.15459792); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows))

**Scalp:** OUT of this trial (halt).

## What not to rescue

- Do **not** change EMA periods, sleeve size, bar size, asset, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On FAIL: archive; report only — **no** EMA period / TF / asset / costs grind.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.
- BTC remains research-only for live.

`source: mid_btc_ema_1d` · `bar: 1D` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true`
