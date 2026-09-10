# 52 — Scalp BTC EMA12/30 on **1H** + daily EMA bull — confirmation_windows_v2 (Scalp sleeve; Mid/Core OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Scalp **EMA12/30 long/flat** on **BTC-USDT 1H** + **daily EMA12>EMA30** filter ON for **new longs** (bull focus — entry gate); sleeve €20. SAME rule as Scalp #50. **Gate:** Core-style RETURN (intentional). **`differs_from_holdout_exp_gate: true`** — reason: Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 / #48 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate. **`confirmation_windows_v2: true`**. Mid/Core halted. BTC research-only.

> **Gate locked BEFORE score:** `core_style_return` dual-window — set A **and** set B each need ≥2/3 clean windows (FULL net>0 after costs + DD≤BH×1.1 else abs €10 + holdout net>0 or n=0&TIM≥0.8&marked net>0). Expectancy always documented. `differs_from_holdout_exp_gate: true`. `confirmation_windows_v2: true`.

## Verdict set A: **PASS**
## Verdict set B: **FAIL**

**Dual-window robust:** NO (requires A PASS **and** B PASS under locked `core_style_return`).
On FAIL: **no** EMA period / TF / asset / costs grind; do **not** silently revert windows; archive; report only. Do not propose Scalp param / asset / TF rescue from this trial.

## Windows LOCKED before scoring (`confirmation_windows_v2`)

### Set A — SAME as #50 / PRIMARY_SET_A

| id | start | end |
|----|-------|-----|
| A1 | 2023-10-01 | 2023-12-31 |
| A2 | 2021-01-01 | 2021-03-31 |
| A3 | 2024-02-01 | 2024-04-30 |

### Set B — bull-only alternate (NEW; not old #50 B2/B3)

**Reason:** Prior #50 B included non-bull / holdout-fragile windows while A PASSed on bull focus.

| id | start | end | note |
|----|-------|-----|------|
| B1 | 2020-10-01 | 2020-12-31 | 2020-10-01 → 2020-12-31 UTC (late-2020 bull run-up) |
| B2 | 2023-07-01 | 2023-09-30 | 2023-07-01 → 2023-09-30 UTC (Q3-2023 bull / pre-ETF) |
| B3 | 2024-05-01 | 2024-07-31 | 2024-05-01 → 2024-07-31 UTC (post-halving early-summer 2024) |

Excluded old B2 `2023-01-01→2023-03-31` and old B3 `2024-10-01→2024-12-31`. No overlap with PRIMARY_SET_A.

## Rule cards (LOCKED before scoring)

### DD (documented BEFORE scoring)

- DD (PASS): max DD ≤ BH max DD × 1.1 when BH DD available; else absolute DD ≤ €10.0 (50% of Scalp €20 sleeve).

### Scalp — EMA12/30 long/flat + daily bull (spot BTC-USDT **1H**, €20)

- Long iff closed-bar **1H EMA12 > EMA30**; else **flat**. Never short.
- **Daily EMA12>EMA30 filter ON for new longs** (bull focus): while flat, enter long only when prior closed **daily EMA12 > EMA30**; else no entry. Exit when 1H EMA flips flat (daily flip alone does not force exit — entry gate, mirrors #46 / #48 / PullbackLongV1).
- Fill: signal close → next open (EMA family).
- Size: **full sleeve** when long (cash when flat) — Scalp €20.
- Costs: PaperSettings 5+5 bps.
- Bar: **1H**.
- Expectancy: **always documented**; not the PASS gate.
- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate).
- Windows: set A = PRIMARY_SET_A (#50); set B = bull-only `confirmation_windows_v2` (#52); MD fallbacks labeled.

### Mid / Core

- **OUT** of this trial.

### PASS gates (Scalp only — Core-style RETURN; NOT holdout-exp)

1. A window is **clean** only if: FULL after-costs net return > 0 **and** DD ≤ BH×1.1 (else ≤€10.0) **and** holdout net > 0 (or holdout n=0 & TIM≥0.8 & marked net>0).
2. Need **≥2 of 3** clean windows per set. Extra full+/holdout-red windows do not veto.
3. Dual-window: set **A PASS and set B PASS**.
4. Document n_trades / TIM / expectancy; low n OK (not a FAIL gate).

> **Note:** `differs_from_holdout_exp_gate: true` — Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 / #48 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate. Prior holdout-exp trials: ['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']. `confirmation_windows_v2: true` — bull-only alternate B (see locked table).

## Results — primary set A

**Overall: PASS**

- Scalp: PASS (clean_pass=['A1', 'A2'], full+=['A1', 'A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[36, 34, 28], TIM=['0.6137', '0.6144', '0.4782'], expectancy=['0.1681', '0.3816', '0.1014'], median_trades=34.0000; low_n_ok=True)
- Mid: OUT of trial
- Core: OUT of trial
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 / #48 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 36 | 0.1681 | 5.9463 | 2.7434 | 0.8608 | 0.6137 | 2.8391 |
| holdout | 11 | 0.0323 | 0.2736 | 2.1436 | 0.2453 | 0.5223 | 1.9150 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=3.1230, bh_dd=2.83911076); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.1681)

**Mid / Core:** OUT of this trial.

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 34 | 0.3816 | 13.0356 | 5.8178 | 1.0012 | 0.6144 | 10.3864 |
| holdout | 12 | 0.1079 | 1.3342 | 3.7571 | 0.2683 | 0.6543 | 4.4010 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.4251, bh_dd=10.386421); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.3816)

**Mid / Core:** OUT of this trial.

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 28 | 0.1014 | 2.8398 | 3.8546 | 0.6343 | 0.4782 | 6.6995 |
| holdout | 4 | -0.0738 | -0.2950 | 1.4066 | 0.0804 | 0.2562 | 3.9694 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=7.3694, bh_dd=6.69948821); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.1014)

**Mid / Core:** OUT of this trial.

## Results — alternate set B bull-only v2 (no param rescue)

**Overall: FAIL**

- Scalp: FAIL (clean_pass=['B1'], full+=['B1'], holdout_fail=[], dd_fail=[], n_trades=[28, 14, 19], TIM=['0.6209', '0.1241', '0.2292'], expectancy=['0.5012', '-0.1818', '-0.1266'], median_trades=19.0000; low_n_ok=True)
- Mid: OUT of trial
- Core: OUT of trial
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 / #48 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate)

### B1 — 2020-10-01 → 2020-12-31 UTC (late-2020 bull run-up)

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 28 | 0.5012 | 16.5311 | 2.9144 | 0.6867 | 0.6209 | 5.3192 |
| holdout | 7 | 0.7569 | 7.1540 | 2.1663 | 0.1568 | 0.7068 | 1.9144 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=5.8511, bh_dd=5.31920988); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.5012)

**Mid / Core:** OUT of this trial.

### B2 — 2023-07-01 → 2023-09-30 UTC (Q3-2023 bull / pre-ETF)

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 14 | -0.1818 | -2.5844 | 2.8023 | 0.2700 | 0.1241 | 4.3265 |
| holdout | 0 | NaN | -0.0446 | 0.0766 | 0.0100 | 0.0119 | 1.0525 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=4.7592, bh_dd=4.32650151); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=-0.1818)

**Mid / Core:** OUT of this trial.

### B3 — 2024-05-01 → 2024-07-31 UTC (post-halving early-summer 2024)

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (BTC EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 19 | -0.1266 | -2.4052 | 3.6664 | 0.3606 | 0.2292 | 5.8554 |
| holdout | 4 | -0.0412 | -0.1650 | 0.9369 | 0.0802 | 0.2351 | 2.1514 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=6.4409, bh_dd=5.85538209); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=-0.1266)

**Mid / Core:** OUT of this trial.

## What not to rescue

- Do **not** change EMA periods, sleeve size, bar size, daily filter, asset, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On FAIL: archive; report only — **no** EMA period / TF / asset / costs grind; **do not silently revert windows**.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.

`source: scalp_btc_ema_1h_v2` · `bar: 1H` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true` · `confirmation_windows_v2: true`
