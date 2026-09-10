# 46 — Scalp DOGE BreakoutV1 long-only + daily EMA bull (Scalp sleeve; Mid/Core OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched** (atr_stop_mult=1.5 research overlay labeled).
**Family:** Scalp **BreakoutV1 long-only** on **DOGE-USDT 15m** + **daily EMA12>EMA30** bull entry gate; sleeve €20. **Gate:** Core-style RETURN (Mid #41 pattern scaled to Scalp). **This gate intentionally differs from Mid #36–#40 holdout-expectancy gate** (thin-holdout: Scalp 15m breakout holdouts are thin / fragile for holdout-expectancy (low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 pattern) scaled to Scalp €20 instead of Mid #36–#40 holdout-exp gate). Mid/Core halted for this trial.

> **Gate locked BEFORE score:** `core_style_return` dual-window — set A **and** set B each need ≥2/3 clean windows (FULL net>0 after costs + DD≤BH×1.1 else abs €10 + holdout net>0 or n=0&TIM≥0.8&marked net>0). Expectancy always documented. `differs_from_holdout_exp_gate: true`.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

**Dual-window robust:** NO (requires A PASS **and** B PASS under locked `core_style_return`).
On FAIL: **no param grind** — archive as measured.

## Rule cards

### Scalp — BreakoutV1 long + daily EMA bull (spot DOGE-USDT 15m, €20)

- Long-only BreakoutV1 (Donchian 16 / ATR SMA14 / oneh stub). Never short.
- **Bull filter:** new longs only when prior closed **daily EMA12 > EMA30**; else no entry.
- atr_stop_mult **1.5** research overlay (= live default; yaml untouched).
- Fill: signal close → **next open** (ShadowEngine / BreakoutV1 bar-consistent).
- Costs: PaperSettings **5+5 bps**.
- DD (PASS): max DD ≤ BH max DD × 1.1 when BH DD available; else absolute DD ≤ €10.0 (50% of sleeve).
- Expectancy: **always documented**; not the PASS gate.
- Low n_trades: **OK** (document n_trades / TIM; not a FAIL gate).

### Mid / Core

- **OUT** of this trial.

### PASS gates (Scalp only — Core-style RETURN; NOT holdout-exp)

1. A window is **clean** only if: FULL after-costs net return > 0 **and** DD ≤ BH×1.1 (else ≤€10.0) **and** holdout net > 0 (or holdout n=0 & TIM≥0.8 & marked net>0).
2. Need **≥2 of 3** clean windows per set. Extra full+/holdout-red windows do not veto.
3. Dual-window: set **A PASS and set B PASS**.
4. Document n_trades / TIM / expectancy; low n OK (not a FAIL gate).

> **Note:** This gate **intentionally differs** from Mid trials #36–#40 (holdout expectancy). Thin Scalp 15m holdouts make holdout-exp fragile; #46 reuses Core-style RETURN (Mid #41) scaled to Scalp €20.

## Results — primary set A

**Overall: FAIL**

- Scalp: FAIL (clean_pass=[], full+=['A2'], holdout_fail=['A2'], dd_fail=[], n_trades=[92, 115, 102], TIM=['0.1619', '0.1625', '0.1772'], expectancy=['-0.0211', '0.0374', '0.0118'], median_trades=102.0000; low_n_ok=True)
- Mid: OUT of trial
- Core: OUT of trial
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40'])

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: 15m(pad)=8832 trade=8832 holdout=2650

**Scalp (DOGE BreakoutV1 long-only + daily EMA12/30 bull; €20; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 92 | -0.0211 | -3.5705 | 4.6755 | 1.5540 | 0.1619 | 5.0513 |
| holdout | 63 | -0.0293 | -3.0863 | 5.9341 | 1.2374 | 0.2381 | 4.1489 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=5.5565, bh_dd=5.05134443); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40; thin-holdout reason); expectancy_full=-0.0211)

**Mid / Core:** OUT of this trial.

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: 15m(pad)=8640 trade=8640 holdout=2592

**Scalp (DOGE BreakoutV1 long-only + daily EMA12/30 bull; €20; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 115 | 0.0374 | 2.1679 | 14.8999 | 1.8716 | 0.1625 | 250.0371 |
| holdout | 49 | -0.0845 | -4.9698 | 5.4954 | 0.8279 | 0.1501 | 5.2045 |
Scalp score: gate=core_style_return full_pass=True net>0=True dd_ok=True holdout_ok=False (dd_rule: dd<=BH×1.1 (cap=275.0408, bh_dd=250.03710613); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40; thin-holdout reason); expectancy_full=0.0374)

**Mid / Core:** OUT of this trial.

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: 15m(pad)=8640 trade=8640 holdout=2592

**Scalp (DOGE BreakoutV1 long-only + daily EMA12/30 bull; €20; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 102 | 0.0118 | -0.5820 | 3.5523 | 1.7847 | 0.1772 | 20.0054 |
| holdout | 21 | 0.0196 | 0.0168 | 0.9533 | 0.3948 | 0.1046 | 8.9113 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=22.0059, bh_dd=20.00539415); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40; thin-holdout reason); expectancy_full=0.0118)

**Mid / Core:** OUT of this trial.

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Scalp: FAIL (clean_pass=[], full+=[], holdout_fail=[], dd_fail=[], n_trades=[51, 72, 139], TIM=['0.0704', '0.1047', '0.2433'], expectancy=['-0.0225', '-0.0628', '-0.0177'], median_trades=72.0000; low_n_ok=True)
- Mid: OUT of trial
- Core: OUT of trial
- Gate: `core_style_return` — differs_from_holdout_exp_gate=True (prior=['#36', '#37', '#38', '#39', '#40'])

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: 15m(pad)=8832 trade=8832 holdout=2650

**Scalp (DOGE BreakoutV1 long-only + daily EMA12/30 bull; €20; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 51 | -0.0225 | -2.0649 | 2.3772 | 0.9176 | 0.0704 | 9.2775 |
| holdout | 60 | -0.0424 | -3.5956 | 7.0121 | 1.0507 | 0.2411 | 9.9027 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=10.2053, bh_dd=9.27751131); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40; thin-holdout reason); expectancy_full=-0.0225)

**Mid / Core:** OUT of this trial.

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: 15m(pad)=8640 trade=8640 holdout=2592

**Scalp (DOGE BreakoutV1 long-only + daily EMA12/30 bull; €20; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 72 | -0.0628 | -5.7612 | 6.4903 | 1.2395 | 0.1047 | 7.3748 |
| holdout | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 3.5585 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=8.1123, bh_dd=7.37482921); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40; thin-holdout reason); expectancy_full=-0.0628)

**Mid / Core:** OUT of this trial.

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: 15m(pad)=8832 trade=8832 holdout=2650

**Scalp (DOGE BreakoutV1 long-only + daily EMA12/30 bull; €20; atr_stop=1.5 overlay; Core-style RETURN; DD≤BH×1.1 else ≤€10.0)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 139 | -0.0177 | -4.7902 | 5.7702 | 2.3352 | 0.2433 | 19.0005 |
| holdout | 32 | -0.0563 | -2.3646 | 3.7363 | 0.5635 | 0.1211 | 10.3315 |
Scalp score: gate=core_style_return full_pass=False net>0=False dd_ok=True holdout_ok=None (dd_rule: dd<=BH×1.1 (cap=20.9006, bh_dd=19.00051758); holdout: holdout net_return>0; if n_trades=0 require TIM≥0.8 and marked net>0 (NOT holdout-expectancy — differs from Mid #36–#40; thin-holdout reason); expectancy_full=-0.0177)

**Mid / Core:** OUT of this trial.

## What not to rescue

- Do **not** change lookback, atr_stop, sleeve, bar size, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On FAIL: **archive** — no param grind.
- Do **not** change `config/default.yaml`.
- Do **not** revert to #36–#40 holdout-expectancy scoring for this trial.

`source: scalp_doge_breakout_bull` · `place_orders: false` · `not_a_forecast: true` · `gate: core_style_return` · `differs_from_holdout_exp_gate: true`
