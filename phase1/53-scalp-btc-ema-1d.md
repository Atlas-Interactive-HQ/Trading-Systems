# 53 — Scalp BTC EMA12/30 on **1D** Core-style RETURN gate (Scalp sleeve; Mid/Core OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Scalp **EMA12/30 long/flat** on **BTC-USDT 1D** — SAME Core rule as Mid #51 (`EmaTrendV1` / `walk_long_flat`) scaled to Scalp €20. **Gate:** Core-style RETURN (intentional). **`differs_from_holdout_exp_gate: true`** — reason: thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51). Mid/Core OUT. **Live:** BTC = **research-only** for live.

> **Gate + calendars locked BEFORE scoring.** Same A/B calendars as Mid #51. Expect same n≈0 / TIM≈BH caveat class as #51 — documented honestly; still valid under locked gate.

## Verdict set A: **PASS**
## Verdict set B: **PASS**

**Dual-window confirmation (A AND B):** PASS (Set A AND set B each must PASS under the same locked `core_style_return` gate).

## Rule cards (LOCKED before scoring)

### DD (documented BEFORE scoring)

- DD (PASS): max DD ≤ BH max DD × 1.1 when BH DD available; else absolute DD ≤ €10.0 (50% of Scalp €20 sleeve).

### Scalp — EMA12/30 long/flat (spot BTC-USDT **1D**, €20)

- Long iff closed-bar **EMA12 > EMA30**; else **flat**. Never short.
- Fill: signal close → next open (EMA family).
- Size: **full sleeve** when long (cash when flat) — `walk_long_flat` / `EmaTrendV1` with equity €20.
- Costs: PaperSettings 5+5 bps.
- Bar: **1D** (same daily Core-rule as Mid #51; scalp sleeve).
- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate). Expect same n≈0 / TIM≈BH caveat class as Mid #51 — document honestly; still valid under locked gate.
- Windows: **same A/B calendars as Mid #51** (Mid #51 (PRIMARY_SET_A / ALT_SET_B / A3_FALLBACK / B3_FALLBACK)); MD fallbacks labeled.

### Mid / Core

- **OUT** of this trial.

### Calendars (LOCKED — identical to Mid #51)

**Primary set A**

| id | start | end | label |
|---|---|---|---|
| A1 | 2023-10-01 | 2023-12-31 | 2023-10-01 → 2023-12-31 UTC |
| A2 | 2021-01-01 | 2021-03-31 | 2021-01-01 → 2021-03-31 UTC (spike stress) |
| A3 | 2024-02-01 | 2024-04-30 | 2024-02-01 → 2024-04-30 UTC |
| A3 fallback | 2023-09-01 | 2023-11-30 | 2023-09-01 → 2023-11-30 UTC (A3 fallback) |

**Alternate set B**

| id | start | end | label |
|---|---|---|---|
| B1 | 2020-10-01 | 2020-12-31 | 2020-10-01 → 2020-12-31 UTC |
| B2 | 2023-01-01 | 2023-03-31 | 2023-01-01 → 2023-03-31 UTC |
| B3 | 2024-10-01 | 2024-12-31 | 2024-10-01 → 2024-12-31 UTC |
| B3 fallback | 2022-07-01 | 2022-09-30 | 2022-07-01 → 2022-09-30 UTC (B3 fallback) |

### PASS gates (Scalp only — Core-style RETURN; NOT holdout-exp)

1. A window is **clean** only if: FULL after-costs net return > 0 **and** DD ≤ BH×1.1 (else ≤€10.0) **and** holdout net > 0 (or holdout n=0 & TIM≥0.8 & marked net>0).
2. Need **≥2 of 3** clean windows (Core-style count). Extra full+/holdout-red windows do not veto.
3. Document n_trades / TIM / **expectancy** in tables; low n OK (not a FAIL gate).
4. Set A **AND** set B each must PASS for dual-window confirmation.

> **Note:** `differs_from_holdout_exp_gate: true` — thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51). Mirrors Mid #51 / mid_doge_ema_coregate (#41) / mid_btc_ema_4h (#49) scoring spirit scaled to Scalp €20. Prior holdout-exp trials: ['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44'].

## Results — primary set A

**Overall: PASS**

- Scalp: PASS (clean_pass=['A1', 'A2'], full+=['A1', 'A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[0, 0, 1], TIM=['1.0000', '1.0000', '0.7640'], median_trades=0.0000; low_n_ok=True)
- Mid: OUT of trial
- Core: OUT of trial
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51))

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

## Results — alternate set B (no param rescue)

**Overall: PASS**

- Scalp: PASS (clean_pass=['B1', 'B2'], full+=['B1', 'B2', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[0, 1, 1], TIM=['0.9011', '0.8315', '0.9890'], median_trades=1.0000; low_n_ok=True)
- Mid: OUT of trial
- Core: OUT of trial
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51))

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

## Caveats (honest — same class as Mid #51)

- 1D EMA12/30 on BTC often shows **n_trades ≈ 0** with **TIM ≈ BH** (always-long through the window). That is structural on this bar/rule, not a scoring bug. Low n is **OK** under `core_style_return`; expectancy may be NaN when n=0. Documented; still valid under locked gate.
- Do not re-interpret n=0 as a FAIL or invent holdout-expectancy rescue.

## What not to rescue

- Do **not** change EMA periods, sleeve size, bar size, asset, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On FAIL: archive; report only — **no** EMA period / TF / asset / costs grind.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.
- BTC remains research-only for live.

`source: scalp_btc_ema_1d` · `bar: 1D` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true` · `calendars: same as Mid #51`
