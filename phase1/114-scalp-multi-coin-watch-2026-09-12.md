# 114 — Scalp multi-coin watch policy (2026-09-12)

**Stance:** Universe / capital policy overlay on [`113`](./113-kaje-architecture-2026-09-12.md). `not_a_forecast: true`. **Never places orders.**
**Config:** `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. **This note does not arm.**
**No auto-POST** until Kaje **`ga live`** **and** **session-ja** **and** sleeve list ([`107`](./107-eur200-capital-readiness-2026-09-12.md), [`113`](./113-kaje-architecture-2026-09-12.md)).
**Ledger:** `TL-114` in `research/trial_ledger.jsonl` — **`pre_registered: true`**. No score. No invented PEPE / alt expectancy. No invented order `instId`.

---

## Why this lock

Kaje overlay **2026-09-12** (Europe/Amsterdam), after [`113`](./113-kaje-architecture-2026-09-12.md) already locked PEPE as the Scalp **target**:

**Scalp may watch multiple coins at once.** They share **one** Scalp capital bucket — the **1** in **6 : 3 : 1** (Scalp = **10%** of total). This is **not** three Scalp sleeves and **not** a 10% allocation per coin.

PEPE remains **preferred** if and only if it is **DEMO_CLEAR**. PEPE is **not** DEMO_CLEAR today (demo / compliance deferral). PEPE-like **alternatives** are an **unranked watch pool**. **Research ranks them later.** This note does **not** invent expectancy, a ranked scoreboard, or order `instId`s.

**Soft PASS ≠ arm. HALTED. not_a_forecast.**

---

## Fail-closed catalogue

These four stamps are **different**. None implies the next.

| Stamp | What it is | What it is **not** |
|-------|------------|---------------------|
| **Catalogue CLEAR** | Name / row seen on the OKX EEA **public** `instruments` catalogue (or a cited Learn launch list). MD / catalogue `instId` only. | **≠ DEMO_CLEAR.** **≠** this-account order `instId`. **≠ Soft PASS.** **≠ arm.** **≠** score. |
| **DEMO_CLEAR** | This account can **demo-trade** that product (spot and/or isolated perp) after a **re-verify** on the demo tradable list / product gate. | **≠ Soft PASS.** **≠ arm.** **≠** live. **≠** a PEPE (or alt) system. Catalogue CLEAR does **not** grant DEMO_CLEAR. |
| **Soft PASS** | A research-panel gate on a **locked card** (DEV / eliminate). | **≠ arm.** **≠ DEMO_CLEAR.** **≠** permission to POST. |
| **arm** | Kaje **`ga live`** **and** **session-ja** **and** sleeve list. | The only POST path. Soft PASS / catalogue / DEMO_CLEAR **do not** arm. |

`place_orders: false`.

DOGE already taught the `instId` split: public MD `DOGE-USD_UM_XPERP-310404` **≠** demo order `…310516` ([`07`](./07-venue-preflight-notes.md), [`09`](./09-handoff-grok-cli.md), [`113`](./113-kaje-architecture-2026-09-12.md)). The same split applies to PEPE and every alt below.

---

## Scalp universe policy

| Rule | Lock |
|------|------|
| Capital bucket | **One** Scalp sleeve = **1 / 10** of the [`113`](./113-kaje-architecture-2026-09-12.md) **6 : 3 : 1** book (**10%** of total). |
| Euro split | **Do not invent** a parked-~€240 table. Parked ~€240 remains HOLD ([`107`](./107-eur200-capital-readiness-2026-09-12.md) / [`109`](./109-three-month-program-2026-09-12.md)). |
| Multi-coin | Scalp may **watch** several names at once under that **one** bucket. |
| Watch ≠ allocate | A name on the watchlist is **not** a sub-sleeve, **not** a reserved € slice, **not** a score, **not** an arm. |
| Positions | Does **not** lift the pack **one directional position** rule ([`phase1/README.md`](./README.md) locked highlights). Watch ≠ simultaneous live legs. |
| Preferred | **PEPE** if **DEMO_CLEAR**. |
| If PEPE blocked | Keep PEPE as preferred *target*. Add PEPE-like names to the watch pool. **Research ranks later.** |
| Compounding | Still **advised** as sleeve intent ([`113`](./113-kaje-architecture-2026-09-12.md)). Winnings cascade **upward** Scalp → Mid → BTC. Not martingale. |
| Leverage ceiling | Scalp **≤10× isolated** remains a Kaje clear ([`107`](./107-eur200-capital-readiness-2026-09-12.md) addendum / [`113`](./113-kaje-architecture-2026-09-12.md)). Ceiling ≠ DEMO_CLEAR ≠ arm. Runtime yaml **untouched**. |
| System | **No PEPE Scalp system exists yet.** Do **not** attach S1 Dual Thrust / RVOL numbers to PEPE or to any alt. |

---

## PEPE — preferred, not DEMO_CLEAR

| Check | Status (this note) |
|-------|---------------------|
| [`113`](./113-kaje-architecture-2026-09-12.md) target | **Yes** — preferred Scalp name |
| Catalogue CLEAR | **Yes (public, 2026-09-12)** — EEA `GET /api/v5/public/instruments` saw `PEPE-USDT` / `PEPE-USD` / `PEPE-EUR` (SPOT), `PEPE-USDT-SWAP` (SWAP), `PEPE-USD_UM_XPERP-310404` (FUTURES `ruleType=xperp`). Same xperp **MD** id cited on [`07`](./07-venue-preflight-notes.md) / [`113`](./113-kaje-architecture-2026-09-12.md) (2026-09-01). **Not** an order `instId`. |
| DEMO_CLEAR | **No.** [`08`](./08-self-learning-paper-path.md) / [`09`](./09-handoff-grok-cli.md): PEPE **deferred** (not on demo tradable list / compliance). `pepe_enabled: false` (**do not flip**). [`113`](./113-kaje-architecture-2026-09-12.md) I8: fail-closed until listing is **re-verified** for this account. |
| Soft PASS / score | **None.** Do not invent PEPE expectancy. |
| arm | **No.** |

Catalogue CLEAR on PEPE **does not** reopen demo routing. Phase 1.7 stays DOGE-only until a later PR re-verifies DEMO_CLEAR **and** Kaje arms.

---

## PEPE-like alternatives (unranked — Research ranks later)

**PEPE-like** here means: meme / high-vol names already visible on the OKX EEA **public** catalogue or the cited Learn launch list — **not** Mid’s DOGE, **not** Core BTC, **not** a new invented base.

This table is a **watch pool**, not a ranking and not a tradable universe. **DEMO_CLEAR is unknown** for every alt (this PR did **not** call a signed demo tradable list). **No expectancy. No Soft PASS. No arm.**

Public catalogue probe **2026-09-12** (`https://eea.okx.com/api/v5/public/instruments`, docs-only, no keys, no orders):

| Name | Why it is in the pool | Catalogue CLEAR (2026-09-12 public) | DEMO_CLEAR | Rank / score |
|------|------------------------|--------------------------------------|------------|--------------|
| **PEPE** | [`113`](./113-kaje-architecture-2026-09-12.md) preferred target | SPOT + SWAP + xperp MD `PEPE-USD_UM_XPERP-310404` | **No** (deferred) | Preferred **if** DEMO_CLEAR; **no** score |
| **PUMP** | Learn “at launch” next to PEPE ([`07`](./07-venue-preflight-notes.md)); 2026-09-01 xperp cite `PUMP-USD_UM_XPERP-310404` | SPOT + SWAP + xperp MD `PUMP-USD_UM_XPERP-310404` | **Unknown** | Research later |
| **BONK** | Meme family; Kraken `PF_BONKUSD` already in [`07`](./07-venue-preflight-notes.md) (different venue) | SPOT + SWAP + xperp MD `BONK-USD_UM_XPERP-310725` | **Unknown** | Research later |
| **WIF** | Meme family; Kraken `PF_WIFUSD` in [`07`](./07-venue-preflight-notes.md) (different venue) | SPOT + SWAP + xperp MD `WIF-USD_UM_XPERP-310815` | **Unknown** | Research later |
| **SHIB** | Meme family on the same 2026-09-12 public catalogue | SPOT + SWAP + xperp MD `SHIB-USD_UM_XPERP-310801` | **Unknown** | Research later |

Also **seen** on that public GET, **not** promoted into the ranked set (there is no ranked set yet):

- **FLOKI**, **MEME** — SPOT + SWAP; **no** xperp row in this probe.
- **FARTCOIN** — `FARTCOIN-USDT-SWAP` only (Kraken `PF_FARTCOINUSD` in [`07`](./07-venue-preflight-notes.md) is **not** an OKX demo id).
- **BABYDOGE** — SPOT only. Name-adjacent to **Mid DOGE** — extra caution; not a Scalp pick here.

**Out of pool**

| Name | Why not |
|------|---------|
| **DOGE** | Mid sleeve under [`113`](./113-kaje-architecture-2026-09-12.md). S1 DOGE was **provisional** Scalp research ([`108`](./108-dev-board-research-lock.md)), not a PEPE replacement. |
| **BTC** | Core hold sleeve. |
| Kraken `PF_*` ids | Public MD on a **different** venue. Not OKX EEA DEMO_CLEAR. |

Research later may rank any name that reaches **DEMO_CLEAR**. Ranking method, expectancy, and order `instId` are **future work**. Do **not** invent them in a follow-up that has not re-verified demo tradability.

xperp `…310404` / `…310725` / `…310801` / `…310815` rows above are **catalogue / MD ids**. They are **not** order `instId`s. Do not copy them into OMS.

---

## Cross-refs (do not re-lock)

| Doc | How this overlay uses it |
|-----|--------------------------|
| [`113`](./113-kaje-architecture-2026-09-12.md) | Parent architecture. 6:3:1, PEPE target, ≤10× Scalp ceiling, cascade, Monday 09:00 review. This note **adds** multi-coin **watch** under the **same** 10% bucket. Does **not** replace PEPE as preferred target. |
| [`107`](./107-eur200-capital-readiness-2026-09-12.md) | HALTED / tiny ≤€20 / leverage addendum. Unchanged. |
| [`108`](./108-dev-board-research-lock.md) | S1 DOGE remains the research freeze candidate. PEPE remains the architecture target. Multi-watch does **not** re-score S1. |
| [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) | 3× consecutive SL → 28m delayed market entry still applies to the **Scalp sleeve** once a system exists (PEPE **or** a later DEMO_CLEAR alt). Not martingale. Paper-first. |
| [`111`](./111-sl-fill-release-human-ping.md) | SL fill / release ping still applies once that stream is armed. A watchlist **≠** a ping **≠** an arm. |
| [`07`](./07-venue-preflight-notes.md) / [`08`](./08-self-learning-paper-path.md) / [`09`](./09-handoff-grok-cli.md) | Catalogue vs demo-tradable split; PEPE deferred. |
| [`105`](./105-portfolio-core-major.md) / [`106`](./106-research-governance-board.md) | STRATEGY GREEN ≠ PORTFOLIO GREEN. Soft PASS ≠ arm. |

---

## What this PR does / does not

**Does**

- Lock multi-coin Scalp **watch** under one 10% bucket as **phase1/114**.
- Catalogue the fail-closed chain: **catalogue CLEAR ≠ DEMO_CLEAR ≠ Soft PASS ≠ arm**.
- Keep PEPE preferred **if** DEMO_CLEAR; record that PEPE is **not** DEMO_CLEAR today.
- Name an **unranked** PEPE-like watch pool from existing Learn cites + a 2026-09-12 **public** catalogue GET.
- Pre-register ledger row `TL-114` (not a score).
- Point [`113`](./113-kaje-architecture-2026-09-12.md) / [`108`](./108-dev-board-research-lock.md) at this overlay.

**Does not**

- Change `config/default.yaml` or flip `pepe_enabled`.
- Place orders / arm live / invent SHADOW dates.
- Invent PEPE or alt expectancy, panel €, or a ranked scoreboard.
- Treat public catalogue `instId`s as demo order ids.
- Declare DEMO_CLEAR for PUMP / BONK / WIF / SHIB / others.
- Split the 10% Scalp bucket per coin.
- Lift the one-position rule.
- Re-score S1 / R1–R7 / #71 / PEPE.
- Promote an alt over PEPE.

---

## Honesty / invalidation

- Soft PASS / V2 PASS / DEV board / [`113`](./113-kaje-architecture-2026-09-12.md) / this watch policy **≠ arm**.
- Catalogue CLEAR **≠** DEMO_CLEAR **≠** Soft PASS **≠** arm.
- A Learn-page name or a 2026-09-12 public row **≠** verified demo-tradable `instId` for this account **≠** score **≠** arm.
- If a later PR invents PEPE / alt expectancy or an order `instId` that was not re-verified, it violates [`113`](./113-kaje-architecture-2026-09-12.md) I5 / I8.
- If a later PR edits `config/default.yaml` or flips `pepe_enabled` for this lock, it contradicts the config invariant.
- If a later PR treats the watch pool as simultaneous live legs or as N×10% capital, it contradicts this lock.
- If a later PR ranks alts with invented scores “because PEPE is blocked,” that ranking is **invalid**.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.
