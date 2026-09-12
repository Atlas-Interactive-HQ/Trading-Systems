# 107 — €200 capital readiness (fail-closed) — 2026-09-12

**Stance:** `not_a_forecast: true`. **Docs only — places no orders.**  
**Trigger:** Kaje intent = deposit ~€200 USDC then go live with highest Mid/Scalp/long **when research ready**.  
**Governance:** PR #89 (P4a/P4b/SHADOW/trial ledger/edge-vs-luck/cash-valid). Soft PASS ≠ arm.  
**Parents:** [`32`](./32-day1-risk-runbook-2026-09-11.md) · [`38`](./38-eur200-three-stream-confirmation.md) · [`83`](./83-noon-live-sprint-gate-2026-09-11.md)

---

## FAIL-CLOSED (do not drift)

| Rule | Locked |
|------|--------|
| Soft PASS ≠ arm | Absolute (PR #89) |
| Mid #71 | Best Mid DEV paper — **NOT** SHADOW-validated, **NOT** stressed, **NOT** edge-vs-luck → **no live-arm** |
| Scalp S1 | Best Scalp DEV paper — same: **no live-arm** |
| Core | No validated edge (EMA thin; Donchian dead; CORE-R1 no promote) → Core sleeve may stay **cash** until validated |
| HFT | P4a screening only; P4b 7d not started; no instrument lock; no H1 PnL → **no HFT-arm** |
| R1–R7 Soft PASS | **Never** arms Mid/Scalp/Core |
| Tiny until raise | Live POSTs stay ≤€20 until Kaje says **`ga live €200`** **and** session-ja + sleeve picks |
| Martingale | Forbidden |
| Sweeps / transfer | Never auto — Kaje explicit yes |

**HALTED for live sleeves until:** research gates (SHADOW / edge-vs-luck / stress as doctrine requires) **plus** Kaje **session-ja** **plus** explicit which sleeves to arm.

---

## Capital model (policy — not yet armed)

| Bucket | Target | Notes |
|--------|--------|-------|
| Total | **~€200 USDC** | Deposit intent only — Ops/Kaje execute |
| Spot (sleeve A) | **~€150** (3) | DOGE-USDC spot preferred for Mid/long practice |
| Perp (sleeve B) | **~€50** (1) | Isolated ≤**2×** in this original lock; **superseded as ceiling** by Mid ≤**5×** / Scalp ≤**10×** (addendum 2026-09-12, docs only) — hard lev check else NO TRADE |
| Ratio | **3:1** spot:perp equity | Rebalance **propose only** — day-1 / first live: **no auto sweep** |
| Core sleeve | **cash OK** | Until a Core edge is validated under current doctrine |
| Tiny practice | ≤€20 | Remains hard code/cap until `ga live €200` |

Per-trade risk: 1–2% of **armed** sleeve equity. Day kill: **5%** of day-start book (per sleeve and/or global if Kaje sets both).

---

## 1) Nederlandse checklist (Kaje)

### A. Deposit (geld bewegen — alleen jij)

- [ ] Deposit ~€200 USDC naar OKX EEA trading (geen bot-transfer).
- [ ] Bevestig free USDC ≈ target na fees; noteer day-start book.
- [ ] **Nog geen** `ga live €200` tot research gates + sleeve-pick.

### B. Pre-arm research gates (vóór enige Mid/Scalp POST >tiny)

- [ ] Soft PASS ≠ arm herbevestigd.
- [ ] Mid #71: SHADOW / edge-vs-luck / stress **of** expliciet Kaje override dat DEV-paper genoeg is voor tiny/€200 (override moet letterlijk).
- [ ] Scalp S1: idem.
- [ ] Core: cash of gevalideerde edge — geen Donchian-rescue.
- [ ] HFT: P4b pre-reg + 7d + instrument lock vóór HFT-arm (nu: **niet**).
- [ ] P4a capture klaar + screening rapport — **geen pick uit P4a alleen**.

### C. Live-arm (expliciet)

- [ ] Phrase: welke sleeves (Mid / Scalp / Core / none) + notional per sleeve ≤ policy.
- [ ] Phrase: **`session-ja`** voor deze sessie.
- [ ] Phrase: **`ga live €200`** alleen als tiny-cap omhoog mag (anders blijf ≤€20).
- [ ] Auth/IP groen; inventory + resting TP reconcile.
- [ ] Kill 5% armed; geen martingale; sweeps off.

### D. Abort / red lines

- Soft PASS / DEV panel treated as live-arm without SHADOW+ja.
- Lev above sleeve ceiling without verify → NO TRADE (Kaje 2026-09-12: Mid ≤5× iso, Scalp ≤10× iso, Core hold 1×; HFT lane still ≤10 only if later armed — today HALTED).
- Sum notionals > armed policy or >€20 without `ga live €200`.
- Any POST while HALTED / missing session-ja.

---

## 2) English rule card (bots)

```
€200 CAPITAL READINESS  |  2026-09-12  |  Atlas TS Risk
========================================================
Deposit  : ~€200 USDC (human) — bots do not transfer
Split    : ~€150 spot : ~€50 perp (3:1 historical) · see 113 for 6:3:1
Lev      : Mid ≤5× iso · Scalp ≤10× iso · Core hold 1× (Kaje 2026-09-12)
Core     : BTC spot hold policy (113) — not a Core-arm
Mid #71  : DEV paper — Soft PASS ≠ arm — HALTED
Scalp    : PEPE target (113); S1 DOGE was provisional — HALTED
HFT      : P4a screen only — no instrument — HALTED
Tiny     : ≤€20 until Kaje "ga live €200"
Kill     : 5% day-start · no martingale · no auto sweep
Arm      : needs research gates + session-ja + sleeve list
Soft PASS ≠ arm · not_a_forecast
```

---

## 3) What may auto vs confirm

| Auto (after arm) | Needs Kaje yes |
|------------------|----------------|
| Read-only bal/ticker/orders | Deposit / transfer / withdraw |
| Journal | `ga live €200` / session-ja / sleeve arm |
| Trip 5% kill → block new entries | Any Mid/Scalp/Core/HFT first POST |
| Propose 3:1 rebalance | Execute sweep |

---

## 4) Blockers now

| # | Item | Status |
|---|------|--------|
| B1 | Soft PASS ≠ arm / PR #89 | **LOCKED** |
| B2 | Mid #71 not SHADOW/edge-vs-luck | **OPEN** — no Mid-arm |
| B3 | Scalp S1 not SHADOW/edge-vs-luck | **OPEN** — no Scalp-arm |
| B4 | Core no validated edge | **OPEN** — cash OK |
| B5 | P4a still running; P4b not started | **OPEN** — no HFT |
| B6 | session-ja + sleeve pick | **PENDING Kaje** |
| B7 | `ga live €200` | **PENDING** (tiny ≤€20 until then) |

**Go recommendation:** Deposit OK as capital prep. **No live sleeve arm** until B2–B7 cleared per doctrine. Highest Mid/Scalp remain **candidates**, not armed strategies.

`not_a_forecast`

## Addendum — €240 parked + 3m paper→validate (2026-09-12)

Kaje: **~€240 USDC parked** on venue. **No live-arm.** Soft PASS ≠ arm holds. `phase1/107` still governs.

| Item | Lock |
|------|------|
| Parked capital | ~€240 — capital prep only, not sleeve arm |
| Live POSTs | **HALTED** · tiny ≤€20 until `ga live €200` + session-ja + sleeve picks |
| Soft PASS ≠ arm | Absolute |
| Research window | **~3 months** paper → validate; **document all** |
| Mid #71 / Scalp S1 | Candidates only — not SHADOW/edge-vs-luck → no arm |
| Core | Cash OK until validated |
| HFT | P4a/P4b doctrine — no instrument lock yet |

`not_a_forecast`

## Addendum — leverage ceilings Mid ≤5× / Scalp ≤10× (Kaje clear 2026-09-12)

**Docs only.** Does **not** arm. Does **not** edit `config/default.yaml`. Soft PASS ≠ arm.

Kaje clear **2026-09-12**: sleeve leverage **ceilings** (isolated where used):

| Sleeve | Ceiling | Notes |
|--------|---------|-------|
| Core / long | **No leverage** | [`113`](./113-kaje-architecture-2026-09-12.md) BTC **spot hold** — 1× only |
| Mid | **≤5× isolated** | DOGE #71 family; ceiling ≠ venue verify ≠ Mid-arm |
| Scalp | **≤10× isolated** | PEPE target under [`113`](./113-kaje-architecture-2026-09-12.md); ceiling ≠ listing verify ≠ Scalp-arm |

The body above still records the **earlier** fail-closed line (perp ≤2× / lev >2× → NO TRADE without verify). This addendum **raises the documented Mid/Scalp ceilings** as a Kaje clear. Runtime yaml stays `leverage_default: 2.0` / `leverage_hard_cap: 5.0`. If the venue / account / instrument cannot demonstrate the used leverage: **NO TRADE**.

HALTED until **`ga live`** + **session-ja** + sleeve list. Tiny ≤€20 until then. No invented PnL.

Sleeve **capital** ratio is now **6:3:1** Core : Mid : Scalp per [`113`](./113-kaje-architecture-2026-09-12.md) (supersedes the 3:1 spot:perp **as current policy**; this file’s 3:1 table stays historical). Rebalance remains **propose only**. Sweeps still need Kaje explicit yes.

See [`113`](./113-kaje-architecture-2026-09-12.md). `not_a_forecast`

## Addendum — ~€240 book + live Core fill (phase1/116, 2026-09-12)

**Docs only.** Does **not** edit `config/default.yaml`. **Soft PASS ≠ Scalp-arm.** `place_orders: false`.

[`116`](./116-kaje-capital-intent-2026-09-12.md) stamps Kaje intent + **live state 2026-09-12**. Do **not** describe capital as fully parked or Core as “no immediate action.”

| Item | Lock |
|------|------|
| Budget figure | **~€240** — **supersedes €200** as the later-arm **figure**. This file’s €200 tables / `ga live €200` phrase stay **historical**. |
| **Core BTC** | Spot **ALREADY FILLED** **~€144** @ **77304.3** · `ordId` **`3915002084440100864`**. Core exception **executed**. |
| **Mid DOGE** | **~€72 CONDITIONAL** on Mid **#71**. **Currently flat.** Soft PASS ≠ Mid-arm. |
| **Scalp** | **Soft PASS ≠ Scalp-arm.** Method = [`115`](./115-public-md-scalp-method.md). Scalper-first applies to **Scalp-arm only**. |
| Split | **60% BTC · 30% DOGE Mid · 10% Scalp** ([`113`](./113-kaje-architecture-2026-09-12.md) 6:3:1). ~€144 / ~€72 are the live 60/30 stamps — **not** invented MTM PnL. |
| Leverage | Allowed when idea + Risk gates; ceilings Mid **≤5×** / Scalp **≤10×** / Core hold **no lev** unless a later raise |
| DEMO_BLOCK | **Full meme screen on demo OMS** ([`115`](./115-public-md-scalp-method.md)): PEPE / PUMP / TRUMP DEMO_BLOCK; WIF / SHIB / BONK pending Ops |

No invented PnL.

See [`116`](./116-kaje-capital-intent-2026-09-12.md). `not_a_forecast`
