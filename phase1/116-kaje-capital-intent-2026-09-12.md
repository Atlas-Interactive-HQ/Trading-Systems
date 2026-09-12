# 116 — Kaje capital / intent lock (2026-09-12)

**Stance:** Capital / intent lock + **live-state stamp**. `not_a_forecast: true`. **Never places orders from this note.**
**Config:** `config/default.yaml` **untouched**.
**Scalp:** **Soft PASS ≠ Scalp-arm.** Public-MD method is [`115`](./115-public-md-scalp-method.md) (PR **#98**). `place_orders: false`.
**Ledger:** `TL-116` in `research/trial_ledger.jsonl` — **`pre_registered: true`**. No score. No invented PnL / expectancy.
**Numbering:** [`115`](./115-public-md-scalp-method.md) is the **public-MD Scalp method** (merged PR **#98**). This capital/intent lock is **#116**. [`114`](./114-scalp-multi-coin-watch-2026-09-12.md) is the **merged** Scalp multi-coin watch (PR **#97**).

---

## Why this lock

Kaje locked **own-capital intent** on **2026-09-12** (Europe/Amsterdam): book **~€240**, split **60% BTC · 30% DOGE Mid · 10% Scalp**, leverage **allowed only** when idea + Risk gates (ceilings in [`113`](./113-kaje-architecture-2026-09-12.md)).

**Live state the same day:** the **Core exception is already executed.** Do **not** describe capital as fully parked or Core as “no immediate action.” **Scalper-first** still gates **Scalp-arm only**.

**Soft PASS ≠ Scalp-arm. Mid remains conditional / flat. not_a_forecast.**

---

## Hard invariants

| Id | Lock |
|----|------|
| I1 | `not_a_forecast: true` · `place_orders: false` |
| I2 | **Soft PASS ≠ Scalp-arm.** [`115`](./115-public-md-scalp-method.md) method-only ≠ Scalp-arm. |
| I3 | **Core exception already executed** — do **not** rewrite Core as parked / unfilled |
| I4 | **Scalper-first** applies to **Scalp-arm only** (working Scalper → refine → only then `ga live` + session-ja for **Scalp POST**) |
| I5 | `config/default.yaml` **untouched** |
| I6 | Do **not** invent PnL, expectancy, panel €, MTM on the Core fill, or an order `instId` |
| I7 | Sweeps / transfers / withdraws **never auto** — Kaje explicit yes ([`107`](./107-eur200-capital-readiness-2026-09-12.md)) |
| I8 | Martingale / grid / average-down **forbidden** |
| I9 | **DEMO_BLOCK** = full meme screen on **demo OMS** ([`115`](./115-public-md-scalp-method.md)) |

`place_orders: false`. Soft PASS ≠ Scalp-arm.

---

## Live state — 2026-09-12

| Sleeve | State (this stamp) |
|--------|--------------------|
| **Core BTC** | Spot **ALREADY FILLED** **~€144** @ **77304.3** · `ordId` **`3915002084440100864`**. Core exception **executed**. Not “parked.” Not “no immediate action.” |
| **Mid DOGE** | **~€72 CONDITIONAL** on Mid **#71**. **Currently flat.** Soft PASS / DEV #71 **≠ Mid-arm**. |
| **Scalp** | **Soft PASS ≠ Scalp-arm.** Method = public-MD [`115`](./115-public-md-scalp-method.md). No Scalp POST from this note. |

~€144 / ~€72 are the **live 60/30** stamps Kaje recorded against the **~€240** book. They are **not** a new panel score and **not** invented MTM PnL. Do **not** invent a remaining-cash table or a mark on `77304.3`.

Budget figure **~€240 supersedes €200** as the later-arm **figure** ([`107`](./107-eur200-capital-readiness-2026-09-12.md) €200 tables stay historical).

---

## Target allocation (6 : 3 : 1)

| Sleeve | Share | Live vs intent |
|--------|------:|----------------|
| **BTC** Core / long hold | **60%** | **Filled** (~€144 spot). [`113`](./113-kaje-architecture-2026-09-12.md) hold policy — not a Core strategy promote. |
| **DOGE Mid** | **30%** | **Conditional** (~€72) on **#71**. Flat today. |
| **Scalp** | **10%** | **Unarmed.** Any coin only after a **working scalper** (public-MD [`115`](./115-public-md-scalp-method.md) and/or later DEMO path). Coin **TBD**. |

This restates [`113`](./113-kaje-architecture-2026-09-12.md) **6 : 3 : 1**.

---

## Leverage (allowed — not a Scalp-arm)

Leverage is **allowed** when the **idea** clears **and** **Risk gates** clear. Ceilings stay [`113`](./113-kaje-architecture-2026-09-12.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md) addendum **unless a later Kaje raise**:

| Sleeve | Ceiling | Notes |
|--------|---------|-------|
| Core BTC hold | **No leverage** | 1× spot hold (fill already on book) |
| Mid DOGE | **≤5× isolated** | Ceiling ≠ venue verify ≠ Mid-arm |
| Scalp | **≤10× isolated** | Ceiling ≠ DEMO_CLEAR ≠ Scalp-arm |

Runtime yaml **untouched**. If used leverage cannot be demonstrated: **NO TRADE**.

---

## Sequence — Scalp-arm only

**Scalper-first does not unwind the Core fill.**

1. **Working Scalper first** — public-MD [`115`](./115-public-md-scalp-method.md) and/or later DEMO / local-MD. **No Scalp POST.**
2. **Strategy refinement** — lock / refine the working Scalp card. Still **≠ Scalp-arm**.
3. **Only then** Kaje **`ga live`** **and** **session-ja** **and** sleeve list for a **Scalp POST**.

Soft PASS / V2 PASS / DEV board / [`113`](./113-kaje-architecture-2026-09-12.md) / [`115`](./115-public-md-scalp-method.md) **do not** skip step 1 or 2 for Scalp.

Mid stays **conditional on #71** and **flat** until a later explicit Mid-arm. Core is **already filled**.

---

## DEMO_BLOCK — full meme screen (demo OMS)

Cross-ref [`115`](./115-public-md-scalp-method.md) (Ops + Research screen **2026-09-12**):

| Stamp | Lock |
|-------|------|
| **DEMO_BLOCK** | **Full meme screen on demo OMS.** Demo `/account/instruments` empty + place `51001` for **PEPE / PUMP / TRUMP**. |
| Also DEMO_BLOCK (Ops) | **PEPE, PUMP, TRUMP** |
| DEMO pending Ops | **WIF / SHIB / BONK** |
| Public MD | Allowed as **method** ([`115`](./115-public-md-scalp-method.md)). Public MD **≠** DEMO_CLEAR **≠** Scalp-arm. |
| Scalp coin | **TBD.** Watch ≠ allocate ≠ arm ([`114`](./114-scalp-multi-coin-watch-2026-09-12.md), merged PR **#97**). |

Do **not** invent a Scalp `instId`, expectancy, or ranked coin pick.

---

## Cross-refs (do not re-lock)

| Doc | How this lock uses it |
|-----|------------------------|
| [`115`](./115-public-md-scalp-method.md) | **Public-MD Scalp method** (PR #98). Method-only. Soft PASS ≠ Scalp-arm. DEMO_BLOCK full meme screen on demo OMS. |
| [`114`](./114-scalp-multi-coin-watch-2026-09-12.md) | **Merged** Scalp multi-coin watch (PR **#97**). Watch ≠ allocate ≠ Scalp-arm. |
| [`107`](./107-eur200-capital-readiness-2026-09-12.md) | HALTED / tiny / Soft PASS ≠ Scalp-arm. **€200** historical. **~€240** later-arm budget figure. Leverage addendum Mid ≤5× / Scalp ≤10× / Core hold 1×. |
| [`113`](./113-kaje-architecture-2026-09-12.md) | Parent architecture 6:3:1. This note stamps **live Core fill** + Mid conditional + Scalp-arm sequence. Does **not** rewrite the architecture card. |
| [`108`](./108-dev-board-research-lock.md) | Research freeze unchanged (Mid #71 / S1 / Core CASH as *research*). Live Core fill is **capital**, not a CORE-R1 promote. |
| [`109`](./109-three-month-program-2026-09-12.md) | Quiet-ops program unchanged. Do not invent SHADOW dates. |
| [`111`](./111-sl-fill-release-human-ping.md) / [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) | Ping + 3×SL → 28m still apply **once** a stream / Scalp system is armed. Not a Scalp-arm. |
| [`105`](./105-portfolio-core-major.md) / [`106`](./106-research-governance-board.md) | STRATEGY GREEN ≠ PORTFOLIO GREEN. Soft PASS ≠ Scalp-arm. |
| [`120`](./120-kaje-risk-scalp-live-gate-2026-09-12.md) | Overlay (same date): **PEPE LIVE conditional GATE.** Does **not** re-lock this capital stamp. |

---

## What this PR does / does not

**Does**

- Lock the 2026-09-12 Kaje capital / intent + live Core fill as **phase1/116**.
- Point [`107`](./107-eur200-capital-readiness-2026-09-12.md) / [`113`](./113-kaje-architecture-2026-09-12.md) at this overlay (docs).
- Pre-register ledger row `TL-116` (not a score).
- Index this note in [`README`](./README.md).

**Does not**

- Change `config/default.yaml`.
- Place Scalp / Mid orders or invent SHADOW dates.
- Invent PnL, expectancy, or MTM on `ordId 3915002084440100864`.
- Describe Core as fully parked or “no immediate action.”
- Apply scalper-first to the already-filled Core sleeve.
- Arm Scalp from Soft PASS or from [`115`](./115-public-md-scalp-method.md).
- Flip `pepe_enabled` or invent a Scalp `instId`.
- Re-score R1–R7 / #71 / S1 / PEPE.

---

## Honesty / invalidation

- Soft PASS / V2 PASS / DEV board / [`115`](./115-public-md-scalp-method.md) **≠ Scalp-arm**.
- A later PR that describes Core as unfilled / fully parked contradicts I3 and the `ordId` stamp.
- A later PR that POSTs Scalp before a working Scalper + refinement + `ga live` + session-ja + sleeve list violates I4 / [`106`](./106-research-governance-board.md).
- A later PR that invents MTM PnL on the Core fill, or a Scalp `instId`, violates I6.
- A later PR that treats DEMO_BLOCK names as demo-OMS tradable contradicts I9 / [`115`](./115-public-md-scalp-method.md).
- A later PR that edits `config/default.yaml` for this lock contradicts I5.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ Scalp-arm. `config/default.yaml` untouched.

---

## Overlay — Scalp LIVE conditional gate ([`120`](./120-kaje-risk-scalp-live-gate-2026-09-12.md))

Kaje + Risk ACK **2026-09-12**. This capital / intent lock is **unchanged** (Core filled · Mid #71 conditional / flat · Soft PASS ≠ Scalp-arm).

[`120`](./120-kaje-risk-scalp-live-gate-2026-09-12.md) is the **PEPE LIVE conditional GATE**. Ops honesty: **`LIVE_CLEAR_BOTH`** live key **PEPE-USDC** + **PEPE-USD_UM_XPERP-310404**; **`settleCcy` USDC on acct — confirm before place.** **DEMO_BLOCK still.** **No POST** until **121 + PEPE re-score + session-ja**. Soft PASS ≠ Scalp-arm. `not_a_forecast`.
