# 38 — €200 three-stream confirmation gate

**Stance:** `not_a_forecast: true`. Docs / Risk checklist only. No orders. No auto raise of `TINY_LIVE_NOTIONAL_CAP`.
**Parent:** [`32-day1-risk-runbook-2026-09-11.md`](./32-day1-risk-runbook-2026-09-11.md) · Core overlay [`37-core-only-day1-2026-09-11.md`](./37-core-only-day1-2026-09-11.md)
**Locked (Kaje ACK 2026-09-10):** no `ga live €200` until **Core + Mid + Scalp all three confirmed**; then Kaje says the raise phrase.

---

## Dutch short — checklist voor Kaje (€200 three-stream)

### Voor `ga live €200`
- [ ] **Core CONFIRMED:** EMA12/30 DOGE long/flat research-PASS op primary choppy-bull windows (three-tier / #41 Core-info). Sleeve-design OK.
- [ ] **Mid CONFIRMED:** eigen familie (**≠** EMA12/30-copy). Dual-window: set **A PASS én set B PASS**. Gate locked in trial-md **vóór** run (prefer holdout-exp Mid gate; andere gate alleen als Research die als intentional labelt). Sleeve **€40**. Geen Scalp in Mid-trials.
- [ ] **Scalp CONFIRMED:** eigen familie. Dual-window A+B PASS. Sleeve **€20**. Gate locked vóór run.
- [ ] **Cascade:** strikt één richting Scalp → Mid → Core. Bij rode PnL: eerst andere periodes, **niet** meteen rule-tweak.
- [ ] Tot die tijd live: **≤€20** + **session-ja**; Mid/Scalp live **HALTED**; geen auto €200.
- [ ] Horizon ~**3m** windows; `not_a_forecast`; geen verzonnen metrics; `default.yaml` onaangeroerd.
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

Core  : CONFIRMED (design) — EMA12/30 DOGE long/flat research-PASS
        on primary choppy-bull windows
Mid   : PENDING — own family ≠ EMA twin; dual-window A AND B PASS;
        gate locked in trial md BEFORE run (prefer holdout-exp Mid);
        sleeve €40; Scalp OUT of Mid trials
Scalp : PENDING — own family; dual-window A AND B PASS; sleeve €20;
        gate locked BEFORE run
Cascade: Scalp → Mid → Core one-way only
Red PnL: try other periods BEFORE rule changes
Live NOW: ≤€20 + session-ja; Mid/Scalp HALTED; no auto €200
Horizon: ~3m windows; never invent metrics; default.yaml untouched
Parent : phase1/32 + 37 + this 38
```

### Status board (update on PASS/FAIL only)

| Stream | Sleeve | Family rule | Dual-window | Status |
|--------|--------|-------------|-------------|--------|
| Core | policy share of €200 (design) | EMA12/30 long/flat | primary choppy-bull PASS | **CONFIRMED** (design) |
| Mid | €40 | ≠ EMA (next: Donchian #42 …) | A **and** B PASS | **PENDING** |
| Scalp | €20 | own family TBD | A **and** B PASS | **PENDING** |

Live trade gate until board is all CONFIRMED + Kaje phrase: **TINY ≤ €20**.
