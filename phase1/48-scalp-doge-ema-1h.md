# 48 — Scalp DOGE EMA12/30 on **1H** + daily EMA bull (Scalp sleeve; Mid/Core OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Scalp **EMA12/30 long/flat** on **DOGE-USDT 1H** + **daily EMA12>EMA30** filter ON for **new longs** (bull focus — entry gate); sleeve €20. SAME Core EMA rule spirit (`EmaTrendV1` / Mid #41 / Mid #45) scaled to Scalp €20 on 1H. **Gate:** Core-style RETURN (intentional). **`differs_from_holdout_exp_gate: true`** — reason: Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate. Mid/Core halted.

> **Gate locked BEFORE score:** `core_style_return` dual-window — set A **and** set B each need ≥2/3 clean windows (FULL net>0 after costs + DD≤BH×1.1 else abs €10 + holdout net>0 or n=0&TIM≥0.8&marked net>0). Expectancy always documented. `differs_from_holdout_exp_gate: true`.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

**Dual-window robust:** NO (requires A PASS **and** B PASS under locked `core_style_return`).
On FAIL: **no** EMA period / TF / costs grind; archive; report only. Do not propose Scalp param rescue from this trial.

## Rule cards (LOCKED before scoring)

### DD (documented BEFORE scoring)

- DD (PASS): max DD ≤ BH max DD × 1.1 when BH DD available; else absolute DD ≤ €10.0 (50% of Scalp €20 sleeve).

### Scalp — EMA12/30 long/flat + daily bull (spot DOGE-USDT **1H**, €20)

- Long iff closed-bar **1H EMA12 > EMA30**; else **flat**. Never short.
- **Daily EMA12>EMA30 filter ON for new longs** (bull focus): while flat, enter long only when prior closed **daily EMA12 > EMA30**; else no entry. Exit when 1H EMA flips flat (daily flip alone does not force exit — entry gate, mirrors #46 / PullbackLongV1).
- Fill: signal close → next open (EMA family).
- Size: **full sleeve** when long (cash when flat) — Scalp €20.
- Costs: PaperSettings 5+5 bps.
- Bar: **1H**.
- Expectancy: **always documented**; not the PASS gate.
- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate).
- Windows: same A/B calendars as recent Mid/Scalp trials mapped to 1H bars; MD fallbacks labeled.

### Mid / Core

- **OUT** of this trial.

### PASS gates (Scalp only — Core-style RETURN; NOT holdout-exp)

1. A window is **clean** only if: FULL after-costs net return > 0 **and** DD ≤ BH×1.1 (else ≤€10.0) **and** holdout net > 0 (or holdout n=0 & TIM≥0.8 & marked net>0).
2. Need **≥2 of 3** clean windows per set. Extra full+/holdout-red windows do not veto.
3. Dual-window: set **A PASS and set B PASS**.
4. Document n_trades / TIM / expectancy; low n OK (not a FAIL gate).

> **Note:** `differs_from_holdout_exp_gate: true` — Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate. Prior holdout-exp trials: ['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44'].

## Results — primary set A

**Overall: FAIL**

- Scalp: FAIL (clean_pass=['A2'], full+=['A2', 'A3'], holdout_fail=['A3'], dd_fail=[], n_trades=[31, 33, 22], TIM=['0.4275', '0.4907', '0.3875'], expectancy=['-0.0264', '2.5542', '0.6690'], median_trades=31.0000; low_n_ok=True)
- Mid: OUT of trial
- Core: OUT of trial
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 31 | -0.0264 | -0.8184 | 6.1590 | 0.6366 | 0.4275 | 5.5954 |
| holdout | 14 | -0.1147 | -1.6057 | 5.9062 | 0.2876 | 0.4881 | 4.0524 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=False holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=6.1550, bh_dd=5.59543443); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=-0.0264)

**Mid / Core:** OUT of this trial.

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 33 | 2.5542 | 84.2875 | 180.2250 | 2.8954 | 0.4907 | 242.2376 |
| holdout | 10 | 0.0340 | 0.3404 | 4.8508 | 0.2143 | 0.5216 | 5.1566 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=266.4614, bh_dd=242.2376187); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=2.5542)

**Mid / Core:** OUT of this trial.

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 22 | 0.6690 | 14.7172 | 13.2060 | 0.6683 | 0.3875 | 24.4567 |
| holdout | 6 | -0.2848 | -1.7086 | 4.2617 | 0.1199 | 0.2068 | 8.7653 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=26.9023, bh_dd=24.45667683); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.6690)

**Mid / Core:** OUT of this trial.

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Scalp: FAIL (clean_pass=['B1'], full+=['B1', 'B3'], holdout_fail=['B3'], dd_fail=[], n_trades=[18, 14, 30], TIM=['0.3528', '0.2130', '0.5254'], expectancy=['0.6561', '-0.2718', '1.0301'], median_trades=18.0000; low_n_ok=True)
- Mid: OUT of trial
- Core: OUT of trial
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40', '#42', '#43', '#44']; reason=Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 / #45 / Scalp #46 pattern) scaled to Scalp €20 instead of Mid #36–#44 holdout-exp gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 18 | 0.6561 | 13.0156 | 5.0107 | 0.4290 | 0.3528 | 10.6267 |
| holdout | 9 | 0.7503 | 7.7666 | 4.2140 | 0.2039 | 0.5997 | 8.1859 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=True (dd_rule: dd<=BH×1.1 (cap=11.6894, bh_dd=10.62669187); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=0.6561)

**Mid / Core:** OUT of this trial.

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: 1H(pad)=2232 trade=2160 holdout=648 | daily(pad for bull filter)=129

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 14 | -0.2718 | -3.8054 | 4.8180 | 0.2583 | 0.2130 | 10.1109 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 3.3577 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=11.1220, bh_dd=10.11088231); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=-0.2718)

**Mid / Core:** OUT of this trial.

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: 1H(pad)=2280 trade=2208 holdout=663 | daily(pad for bull filter)=131

**Scalp (DOGE EMA12/30 long/flat + daily EMA bull entry gate; €20 on **1H**; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 30 | 1.0301 | 30.9031 | 15.5032 | 1.1851 | 0.5254 | 36.5003 |
| holdout | 9 | -0.2533 | -2.2798 | 3.7368 | 0.1748 | 0.2887 | 10.2277 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=40.1503, bh_dd=36.50030387); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason); expectancy_full=1.0301)

**Mid / Core:** OUT of this trial.

## What not to rescue

- Do **not** change EMA periods, sleeve size, bar size, daily filter, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On FAIL: archive; report only — **no** EMA period / TF / costs grind.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.

`source: scalp_doge_ema_1h` · `bar: 1H` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true`
