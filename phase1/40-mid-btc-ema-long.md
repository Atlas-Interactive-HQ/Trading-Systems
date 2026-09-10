# 40 — Mid BTC EMA12/30 long-only (Core family; Mid sleeve; Scalp OUT)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Family:** Mid **EMA12/30 long/flat** on **BTC-USDT 1D** — same family as successful Core research (`ema_eval` / `EmaTrendV1` / phase1/19), Mid sleeve €40. **NOT** pullback (#38 FAIL). **NOT** Donchian (#39 FAIL). Scalp halted.

## Verdict set A: **FAIL**
## Verdict set B: **FAIL**

Set B run because set A failed — **no strategy param rescue**. Same locked rules.

## Rule cards

### Mid — EMA12/30 long/flat (spot BTC-USDT 1D, €40)

- Long iff closed-bar **EMA12 > EMA30**; else **flat**. Never short.
- Fill: signal close → next open (EMA family).
- Size: **full sleeve** when long (cash when flat) — `walk_long_flat` / `EmaTrendV1` with equity €40 (ema_eval €200 scaled to Mid). Prefer over 1.5% risk.
- Costs: PaperSettings 5+5 bps.
- DD cap (PASS): max DD ≤ €16.0 (40% of sleeve start)
- Low-freq: median full-window trades ≤ 15 (**PASS gate**)

### Core (informational only)

- Do **not** re-optimize. Report BH / EMA12/30 long sleeve €140 on BTC-USDT as context only.
- Do **not** gate Mid PASS on Core.

### Scalp

- **OUT** of this trial (halt).

### PASS gates (Mid only — dual gate for zero-trade windows)

1. **If n_trades ≥ 1:** expectancy after costs > 0 on ≥2 of 3 FULL windows; on each such window holdout n≥1 AND holdout expectancy **> 0**; full max DD ≤ €16; median full n ≤ 15.
2. **If n_trades = 0** (always long / high TIM): Core-style return gate **only for that window** — full net return > 0 AND max DD ≤ €16; holdout net return > 0 AND holdout max DD ≤ holdout BH max DD (BH-compatible). Prefer completed-trade expectancy when trades exist.

## Results — primary set A

**Overall: FAIL**

- Mid: FAIL (full+ windows=['A1', 'A3'], holdout_fail=['A3'], dd_fail=['A2'], zero_trade=['A1', 'A2'], median_trades=0.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### A1 — 2023-10-01 → 2023-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 78.6981 | 14.3228 | 0 | 0.0700 | 78.4794 | 14.3228 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40; DD_cap=€16.0; NOT pullback/Donchian)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 22.4851 | 4.0922 | 0.0200 | 1.0000 | 4.0922 |
| holdout | 0 | NaN | 2.6667 | 2.7943 | 0.0200 | 1.0000 | 2.7943 |
Mid score: gate=zero_trade_core_style_return full_pass=True exp>0=False net>0=True dd_ok=True holdout_ok=True (holdout rule: zero_trade: holdout net_return>0 AND max_dd ≤ holdout BH max_dd (BH-compatible))

**Scalp:** OUT of this trial (halt).

### A2 — 2021-01-01 → 2021-03-31 UTC (spike stress)

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 144.1046 | 66.7316 | 0 | 0.0700 | 143.8206 | 66.7316 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40; DD_cap=€16.0; NOT pullback/Donchian)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 41.1726 | 19.0661 | 0.0200 | 1.0000 | 19.0661 |
| holdout | 0 | NaN | 7.9387 | 7.0521 | 0.0200 | 1.0000 | 7.0521 |
Mid score: gate=zero_trade_core_style_return full_pass=False exp>0=False net>0=True dd_ok=False holdout_ok=None (holdout rule: zero_trade: holdout net_return>0 AND max_dd ≤ holdout BH max_dd (BH-compatible))

**Scalp:** OUT of this trial (halt).

### A3 — 2024-02-01 → 2024-04-30 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 49.9231 | 33.6322 | 1 | 0.1650 | 59.8081 | 40.5475 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40; DD_cap=€16.0; NOT pullback/Donchian)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 14.2637 | 14.2637 | 9.6092 | 0.0471 | 0.7640 | 11.5850 |
| holdout | 1 | -2.5508 | -2.5508 | 6.1206 | 0.0387 | 0.4815 | 6.9697 |
Mid score: gate=n_trades_expectancy full_pass=True exp>0=True net>0=True dd_ok=True holdout_ok=False (holdout rule: n_trades≥1 AND expectancy_after_costs > 0)

**Scalp:** OUT of this trial (halt).

## Results — alternate set B (no param rescue)

**Overall: FAIL**

- Mid: FAIL (full+ windows=['B1', 'B2', 'B3'], holdout_fail=['B2', 'B3'], dd_fail=[], zero_trade=['B1'], median_trades=1.0000)
- Scalp: OUT of trial
- Core: informational only (not in overall gate)

### B1 — 2020-10-01 → 2020-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 214.6651 | 35.0701 | 0 | 0.0700 | 235.2460 | 37.1423 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40; DD_cap=€16.0; NOT pullback/Donchian)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 0 | NaN | 61.3328 | 10.0200 | 0.0200 | 0.9011 | 10.6121 |
| holdout | 0 | NaN | 18.8637 | 2.9682 | 0.0200 | 1.0000 | 2.9682 |
Mid score: gate=zero_trade_core_style_return full_pass=True exp>0=False net>0=True dd_ok=True holdout_ok=True (holdout rule: zero_trade: holdout net_return>0 AND max_dd ≤ holdout BH max_dd (BH-compatible))

**Scalp:** OUT of this trial (halt).

### B2 — 2023-01-01 → 2023-03-31 UTC

MD bars: daily(pad)=129 trade=89 holdout=27

**Core (informational — EMA12/30 long / BH on BTC-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 73.3980 | 22.8127 | 1 | 0.2534 | 100.3948 | 42.7671 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40; DD_cap=€16.0; NOT pullback/Donchian)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 12.4107 | 20.9708 | 6.5179 | 0.0724 | 0.8315 | 12.2192 |
| holdout | 1 | -0.0717 | 6.4497 | 2.7605 | 0.0599 | 0.7037 | 4.5714 |
Mid score: gate=n_trades_expectancy full_pass=True exp>0=True net>0=True dd_ok=True holdout_ok=False (holdout rule: n_trades≥1 AND expectancy_after_costs > 0)

**Scalp:** OUT of this trial (halt).

### B3 — 2024-10-01 → 2024-12-31 UTC

MD bars: daily(pad)=131 trade=91 holdout=28

**Core (informational — EMA12/30 long / BH on BTC-USDT €140)**

| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |
|---|---:|---:|---:|---:|---:|---:|
| EMA | 65.5164 | 32.2473 | 1 | 0.1728 | 72.8674 | 32.0409 |

**Mid (BTC EMA12/30 long/flat full-sleeve €40; DD_cap=€16.0; NOT pullback/Donchian)**

| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 1 | 18.7190 | 18.7190 | 9.2136 | 0.0494 | 0.9890 | 9.1546 |
| holdout | 1 | -1.5657 | -1.5657 | 6.0306 | 0.0392 | 0.9643 | 5.9920 |
Mid score: gate=n_trades_expectancy full_pass=True exp>0=True net>0=True dd_ok=True holdout_ok=False (holdout rule: n_trades≥1 AND expectancy_after_costs > 0)

**Scalp:** OUT of this trial (halt).

## What not to rescue

- Do **not** change EMA periods, sleeve size, bar size, or costs to chase PASS.
- Do **not** invent bars, drop windows, or claim live readiness.
- Do **not** place live orders from this research.
- On red PnL: try alternate windows (set B) before changing rules.
- Do **not** change `config/default.yaml`.
- Do **not** blend pullback or Donchian rules into this EMA long/flat family.

`source: mid_btc_ema_long` · `place_orders: false` · `not_a_forecast: true`
