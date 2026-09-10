# 38 — €200 three-stream confirmation gate

**Stance:** `not_a_forecast: true`. Docs / Risk checklist only. No orders. No auto raise of `TINY_LIVE_NOTIONAL_CAP`.
**Parent:** [`32-day1-risk-runbook-2026-09-11.md`](./32-day1-risk-runbook-2026-09-11.md) · Core overlay [`37-core-only-day1-2026-09-11.md`](./37-core-only-day1-2026-09-11.md)
**Locked (Kaje ACK 2026-09-10):** no `ga live €200` until **Core + Mid + Scalp all three confirmed**; then Kaje says the raise phrase.

### Gate change 2026-09-10 (intentional — Kaje authorized)

| Item | Was (#36–44) | Now |
|------|----------------|-----|
| Mid/Scalp confirm gate | holdout-exp dual A∧B | **`core_style_return` dual A∧B** (labeled intentional) |
| Mid family rule | ≠ EMA twin preferred | Atlas may pick systems for +expectancy; **bull focus** |
| Core | CONFIRMED | **unchanged CONFIRMED** |
| Live | ≤€20 | **unchanged ≤€20**; no `ga live €200` yet |

Archived Mid FAILS under old gate: #42 Donchian, #43 RSI(14) MR, #44 1H Donchian — no grind on those rules.
Archived Mid under `core_style_return` (not dual-robust): **#45** DOGE 4H EMA12/30 — set A PASS · set B FAIL; no grind.
Archived Scalp FAIL under `core_style_return`: **#46** DOGE 15m BreakoutV1 long + daily EMA bull — set A FAIL · set B FAIL; no param grind.
Archived Scalp under `core_style_return` + `confirmation_windows_v2`: **#52** BTC 1H EMA12/30 + daily bull — set A PASS · set B FAIL (bull-only B; no grind; no window revert).

---

## Dutch short — checklist voor Kaje (€200 three-stream)

### Voor `ga live €200`
- [ ] **Core CONFIRMED:** EMA12/30 DOGE long/flat research-PASS op primary choppy-bull windows. Sleeve-design OK.
- [x] **Mid CONFIRMED (research):** #51 BTC 1D EMA12/30 dual A∧B PASS onder `core_style_return` (PR #48). Sleeve **€40**. Caveat: clean windows vaak n=0 / TIM≈BH open-hold — niet HF Mid. **BTC = research-only** (geen live arming).
- [ ] **Scalp CONFIRMED:** dual-window A+B PASS onder **`core_style_return`**. Sleeve **€20**. Gate locked vóór run.
- [ ] **Cascade:** strikt één richting Scalp → Mid → Core. Bij rode PnL: eerst andere periodes, **niet** meteen rule-tweak op een FAIL.
- [ ] Tot die tijd live: **≤€20** + **session-ja**; Mid/Scalp live **HALTED**; geen auto €200.
- [ ] Horizon ~**3m** / bull-focus windows zoals in trial-md; `not_a_forecast`; geen verzonnen metrics; `default.yaml` onaangeroerd.
- [ ] Pas dan: jij schrijft letterlijk **`ga live €200`**.

### Live tot confirmation
- [ ] Core tiny only (≤€20) na session-ja
- [ ] Geen Mid/Scalp arming
- [ ] Geen POST zonder session-ja; IP whitelist actueel
- [ ] 5% day-start book kill; resting TP alleen met bewust ja wijzigen

---

## English rule card — bots

```
€200 THREE-STREAM CONFIRMATION  |  Atlas TS Risk  |  not_a_forecast
================================================================
RAISE "ga live €200" ONLY when ALL THREE confirmed + Kaje phrase

Core  : CONFIRMED (design) — EMA12/30 DOGE long/flat
Mid   : CONFIRMED (research) — #51 BTC 1D EMA12/30 dual A∧B PASS;
        sleeve €40; caveat n≈0/TIM≈BH on clean windows; BTC research-only
Scalp : FAIL archive #52 — same #50 rule + bull-only B v2 (A PASS / B FAIL);
        sleeve €20; no window revert / no EMA-TF grind; BTC research-only
Cascade: Scalp → Mid → Core one-way only
Red PnL: other periods BEFORE grinding a FAIL rule
Live NOW: ≤€20 + session-ja; Mid/Scalp HALTED; no auto €200
Horizon: bull focus; never invent metrics; default.yaml untouched
Parent : phase1/32 + 37 + this 38
```

### Status board (update on PASS/FAIL only)

| Stream | Sleeve | Family / trial | Gate | Status |
|--------|--------|----------------|------|--------|
| Core | policy share of €200 (design) | EMA12/30 long/flat | primary choppy-bull PASS | **CONFIRMED** (design) |
| Mid | €40 | #51 BTC 1D EMA12/30 PASS (PR #48) · caveat: clean windows often n=0 TIM≈1.0 ≈BH open-hold, not HF Mid · BTC research-only | `core_style_return` A∧B | **CONFIRMED** (research + caveat) |
| Scalp | €20 | #46/#48/#50/#52 FAIL — #52 A PASS / B FAIL on bull-only `confirmation_windows_v2` (archived; no grind; no window revert) | `core_style_return` A∧B | **FAIL** (archived) |

Live trade gate until board is all CONFIRMED + Kaje phrase: **TINY ≤ €20**.

**2026-09-10 Mid #51:** CONFIRMED with caveat (n≈0 / TIM≈BH).
**2026-09-10 Scalp #52:** FAIL (A PASS / B FAIL on bull-only confirmation_windows_v2; B2/B3 full net≤0). Archived; no EMA/TF/asset/costs grind; windows not reverted. Three-stream still blocked on **Scalp**. Live remains DOGE tiny ≤€20; no BTC arming; no `ga live €200` until Scalp CONFIRMED + Kaje phrase.
