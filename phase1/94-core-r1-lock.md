# 94 — CORE-R1 lock (P3)

**Stance:** Research. `not_a_forecast: true`. Never places orders.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ Core-arm.
**Donchian C3/C4:** **STOPPED** (`CORE_DONCHIAN_FAMILY_STOPPED = True`). C2 soft FAIL ([`89`](./89-rise-panel-core-c2-donchian40-20-ema50-200-1d.md)) ended that family.

**No score until this lock is committed.** Do not attach R1–R7 numbers in this PR.

---

## Why a new family (not C3)

C3/C4 were the next Donchian rungs (ADX / ATR). Those are stopped. CORE-R1 is a **risk-side** overlay on the existing Core C0 EMA12/30 — not a Donchian continuation and not a param sweep.

Primary question (locked before score):

> Does risk-side protection improve **complete-trade** expectancy / drawdown without eliminating Core participation?

---

## Rule card (LOCKED)

**core_r1_id:** `rise_panel_v1_core_r1_doge_ema12_30_atr14_trail3_1d_eur140`  
**Code:** `atlas.strategy.core_doge_ema_atr_trail_1d.CoreR1EmaAtrTrailV1`

- Asset / bar: **DOGE-USDT 1D** long/flat. Sleeve Core **€140**.
- Entry: closed **EMA12 > EMA30**. Signal close → next open.
- Normal exit: **EMA12 ≤ EMA30**.
- Protection: SMA-ATR(14) trailing stop, multiplier **3.0**, on causally known **closed** bars only. Trail = peak **close** since entry − 3.0 × ATR. Intra-bar stop fills are not claimed (same next-open fill model).
- After an ATR stop **while EMA is still bullish**: require a **fresh** EMA12-above-EMA30 transition before re-entry (`need_fresh_cross`).
- Max one position. No pyramid / avg / martingale.
- **No** Donchian. **No** ADX. **No** param sweep. **No** alt ATR multipliers on R1–R7.

The strategy class rejects EMA / ATR / TF / sleeve sweeps.

---

## When it may be scored

1. This lock note is on `main` (or the PR that introduces it is merged).
2. Evaluator-v2 is the comparison path (terminal liquidation + completed expectancy).
3. Prefer a contiguous unseen SHADOW lock **before** any R1–R7 DEV re-score.
4. R1–R7 remain DEV/eliminate-only even then.

---

## Honesty / invalidation

- Do not score CORE-R1 in the same PR that registers it (this document).
- Do not “rescue” C2 by quietly changing Donchian N or adding ADX.
- A smaller time-in-market is not automatically better; the question is complete-trade expectancy and drawdown **with** participation.
- Soft PASS ≠ Core-arm.

`not_a_forecast: true`. `place_orders: false`.
