# 114 — Scalp multi-coin watch policy (2026-09-12)

**Stance:** Universe / capital policy overlay on [`113`](./113-kaje-architecture-2026-09-12.md). `not_a_forecast: true`. **Never places orders.**
**Config:** `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. **This note does not arm.**
**No auto-POST** until Kaje **`ga live`** **and** **session-ja** **and** sleeve list ([`107`](./107-eur200-capital-readiness-2026-09-12.md), [`113`](./113-kaje-architecture-2026-09-12.md)).
**Ledger:** `TL-114` in `research/trial_ledger.jsonl` — **`pre_registered: true`**. No score. No invented expectancy. No invented order `instId`.

---

## Why this lock

Kaje overlay **2026-09-12** (Europe/Amsterdam), after [`113`](./113-kaje-architecture-2026-09-12.md) locked PEPE as the Scalp **architecture target**:

**Scalp may watch multiple coins at once.** They share **one** Scalp capital bucket — the **1** in **6 : 3 : 1** (Scalp = **10%** of total). This is **not** three Scalp sleeves and **not** a 10% allocation per coin.

Ops on the **demo key** (same date) stamped the meme watch names **DEMO_BLOCK**. Catalogue presence does **not** reopen demo routing. **Research ranks later** only if a later re-verify changes a stamp. This note does **not** invent expectancy, a ranked scoreboard, or order `instId`s.

**Soft PASS ≠ arm. HALTED. not_a_forecast.**

---

## Fail-closed catalogue

These stamps are **different**. None implies the next.

| Stamp | What it is | What it is **not** |
|-------|------------|---------------------|
| **Catalogue CLEAR** | Name / row seen on the OKX EEA **public** `instruments` catalogue (or a cited Learn launch list). MD / catalogue `instId` only. | **≠** demo-tradable. **≠** this-account order `instId`. **≠ Soft PASS.** **≠ arm.** **≠** score. |
| **DEMO_BLOCK** | Ops stamp **2026-09-12**: this **demo key** cannot demo-trade that name (product / compliance / tradable-list gate). | **≠** permission to invent a workaround `instId`. **≠ Soft PASS.** **≠ arm.** Catalogue CLEAR does **not** lift DEMO_BLOCK. |
| **DEMO_CLEAR** | Reserved stamp: this account **can** demo-trade that product after a **re-verify**. **None** of the Ops-stamped names below hold this stamp. | **≠ Soft PASS.** **≠ arm.** **≠** live. Do **not** headline a name as this stamp. |
| **Soft PASS** | A research-panel gate on a **locked card** (DEV / eliminate). | **≠ arm.** **≠** demo-tradable. **≠** permission to POST. |
| **arm** | Kaje **`ga live`** **and** **session-ja** **and** sleeve list. | The only POST path. Soft PASS / catalogue / DEMO_BLOCK **do not** arm. |

`place_orders: false`.

**Catalogue CLEAR ≠ DEMO_BLOCK ≠ Soft PASS ≠ arm.**

DOGE already taught the `instId` split: public MD `DOGE-USD_UM_XPERP-310404` **≠** demo order `…310516` ([`07`](./07-venue-preflight-notes.md), [`09`](./09-handoff-grok-cli.md), [`113`](./113-kaje-architecture-2026-09-12.md)). The same split applies to every name below.

---

## Scalp universe policy

| Rule | Lock |
|------|------|
| Capital bucket | **One** Scalp sleeve = **1 / 10** of the [`113`](./113-kaje-architecture-2026-09-12.md) **6 : 3 : 1** book (**10%** of total). |
| Euro split | **Do not invent** a parked-~€240 table. Parked ~€240 remains HOLD ([`107`](./107-eur200-capital-readiness-2026-09-12.md) / [`109`](./109-three-month-program-2026-09-12.md)). |
| Multi-coin | Scalp may **watch** several names at once under that **one** bucket. |
| Watch ≠ allocate | A name on the watchlist is **not** a sub-sleeve, **not** a reserved € slice, **not** a score, **not** an arm. |
| Positions | Does **not** lift the pack **one directional position** rule ([`phase1/README.md`](./README.md) locked highlights). Watch ≠ simultaneous live legs. |
| Architecture target | **PEPE** remains the [`113`](./113-kaje-architecture-2026-09-12.md) Scalp **name**. Ops stamp is **DEMO_BLOCK** — not a demo route. |
| Watch pool | PEPE-like names stay on the multi-coin watchlist for research. **Research ranks later.** DEMO_BLOCK names are **not** ranked and **not** routed. |
| Compounding | Still **advised** as sleeve intent ([`113`](./113-kaje-architecture-2026-09-12.md)). Winnings cascade **upward** Scalp → Mid → BTC. Not martingale. |
| Leverage ceiling | Scalp **≤10× isolated** remains a Kaje clear ([`107`](./107-eur200-capital-readiness-2026-09-12.md) addendum / [`113`](./113-kaje-architecture-2026-09-12.md)). Ceiling ≠ demo-tradable ≠ arm. Runtime yaml **untouched**. |
| System | **No PEPE Scalp system exists yet.** Do **not** attach S1 Dual Thrust / RVOL numbers to PEPE or to any alt. |

---

## Honesty stamp — DEMO_BLOCK (Ops 2026-09-12, demo key)

Ops checked the **demo key** on **2026-09-12**. These names are **DEMO_BLOCK**:

**PEPE · PUMP · TRUMP · WIF · SHIB · BONK · BOME · FLOKI**

| Name | Catalogue (public GET 2026-09-12; MD / catalogue only) | Ops demo key | Rank / score |
|------|--------------------------------------------------------|--------------|--------------|
| **PEPE** | SPOT + SWAP + xperp MD `PEPE-USD_UM_XPERP-310404` | **DEMO_BLOCK** | None |
| **PUMP** | SPOT + SWAP + xperp MD `PUMP-USD_UM_XPERP-310404` | **DEMO_BLOCK** | None |
| **TRUMP** | SPOT + SWAP + xperp MD `TRUMP-USD_UM_XPERP-310704` | **DEMO_BLOCK** | None |
| **WIF** | SPOT + SWAP + xperp MD `WIF-USD_UM_XPERP-310815` | **DEMO_BLOCK** | None |
| **SHIB** | SPOT + SWAP + xperp MD `SHIB-USD_UM_XPERP-310801` | **DEMO_BLOCK** | None |
| **BONK** | SPOT + SWAP + xperp MD `BONK-USD_UM_XPERP-310725` | **DEMO_BLOCK** | None |
| **BOME** | SPOT + SWAP (`BOME-USDT` / `BOME-USDT-SWAP`). **No** xperp row in this public GET. | **DEMO_BLOCK** | None |
| **FLOKI** | SPOT + SWAP (`FLOKI-USDT` / `FLOKI-USDT-SWAP`). **No** xperp row in this public GET. | **DEMO_BLOCK** | None |

Public catalogue probe: `https://eea.okx.com/api/v5/public/instruments` (docs-only, no orders). Catalogue rows **≠** order `instId`s. Do not copy them into OMS.

[`08`](./08-self-learning-paper-path.md) / [`09`](./09-handoff-grok-cli.md) already deferred PEPE (not on the demo tradable list / compliance). `pepe_enabled: false` (**do not flip**). [`113`](./113-kaje-architecture-2026-09-12.md) I8 stays fail-closed. The Ops stamp **extends** that honesty to the rest of the list.

Phase 1.7 stays DOGE-only. Catalogue CLEAR **does not** reopen demo routing.

---

## Watch pool vs Mid / Core

**PEPE-like** here means meme / high-vol names on the watchlist — **not** Mid’s DOGE, **not** Core BTC, **not** a new invented base.

| Name | Why not a Scalp demo route |
|------|----------------------------|
| **DOGE** | Mid sleeve under [`113`](./113-kaje-architecture-2026-09-12.md). S1 DOGE was **provisional** Scalp research ([`108`](./108-dev-board-research-lock.md)), not a PEPE replacement. |
| **BTC** | Core hold sleeve. |
| Kraken `PF_*` ids | Public MD on a **different** venue. Not an OKX EEA demo route. |

Also **seen** on the public GET, **not** on the Ops DEMO_BLOCK list, **not** ranked: **MEME**, **FARTCOIN**, **BABYDOGE**. Do **not** invent a demo stamp or expectancy for them.

Research later may rank a name **only** after a later Ops re-verify. Ranking method, expectancy, and order `instId` are **future work**. Do **not** invent them because the watch names are DEMO_BLOCK.

---

## Cross-refs (do not re-lock)

| Doc | How this overlay uses it |
|-----|--------------------------|
| [`113`](./113-kaje-architecture-2026-09-12.md) | Parent architecture. 6:3:1, PEPE target **name**, ≤10× Scalp ceiling, cascade, Monday 09:00 review. This note **adds** multi-coin **watch** under the **same** 10% bucket and the Ops **DEMO_BLOCK** stamp. Does **not** replace #113. |
| [`107`](./107-eur200-capital-readiness-2026-09-12.md) | HALTED / tiny ≤€20 / leverage addendum. Unchanged. |
| [`108`](./108-dev-board-research-lock.md) | S1 DOGE remains the research freeze candidate. PEPE remains the architecture target **name**. Multi-watch does **not** re-score S1. |
| [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) | 3× consecutive SL → 28m delayed market entry still applies to the **Scalp sleeve** once a system exists. Not martingale. Paper-first. DEMO_BLOCK names have **no** system. |
| [`111`](./111-sl-fill-release-human-ping.md) | SL fill / release ping still applies once that stream is armed. A watchlist **≠** a ping **≠** an arm. |
| [`07`](./07-venue-preflight-notes.md) / [`08`](./08-self-learning-paper-path.md) / [`09`](./09-handoff-grok-cli.md) | Catalogue vs demo-tradable split; PEPE deferred. |
| [`105`](./105-portfolio-core-major.md) / [`106`](./106-research-governance-board.md) | STRATEGY GREEN ≠ PORTFOLIO GREEN. Soft PASS ≠ arm. |
| [`115`](./115-public-md-scalp-method.md) | Public-MD Scalp **paper method** (already on main). Not a second watch lock. Public MD ≠ demo route ≠ arm. |
| [`120`](./120-kaje-risk-scalp-live-gate-2026-09-12.md) | Overlay: **PEPE LIVE GATE** + Ops LIVE queue PEPE ★→PUMP→TRUMP→WIF `LIVE_CLEAR_BOTH` ≠ arm. **DEMO_BLOCK unchanged.** Does **not** re-lock this watch policy. |

---

## What this PR does / does not

**Does**

- Lock multi-coin Scalp **watch** under one 10% bucket as **phase1/114**.
- Catalogue the fail-closed chain: **catalogue CLEAR ≠ DEMO_BLOCK ≠ Soft PASS ≠ arm**.
- Stamp **PEPE / PUMP / TRUMP / WIF / SHIB / BONK / BOME / FLOKI** = **DEMO_BLOCK** (Ops 2026-09-12, demo key).
- Keep PEPE as the [`113`](./113-kaje-architecture-2026-09-12.md) architecture target **name** (not a demo route).
- Pre-register ledger row `TL-114` (not a score).
- Point [`113`](./113-kaje-architecture-2026-09-12.md) / [`108`](./108-dev-board-research-lock.md) at this overlay.

**Does not**

- Change `config/default.yaml` or flip `pepe_enabled`.
- Place orders / arm live / invent SHADOW dates.
- Invent expectancy, panel €, or a ranked scoreboard.
- Treat public catalogue `instId`s as demo order ids.
- Split the 10% Scalp bucket per coin.
- Lift the one-position rule.
- Re-score S1 / R1–R7 / #71 / PEPE.
- Promote an alt over PEPE.

---

## Honesty / invalidation

- Soft PASS / V2 PASS / DEV board / [`113`](./113-kaje-architecture-2026-09-12.md) / this watch policy **≠ arm**.
- Catalogue CLEAR **≠** DEMO_BLOCK **≠** Soft PASS **≠** arm.
- A Learn-page name or a 2026-09-12 public row **≠** demo-tradable `instId` for this account **≠** score **≠** arm.
- If a later PR invents expectancy or an order `instId` that was not re-verified, it violates [`113`](./113-kaje-architecture-2026-09-12.md) I5 / I8.
- If a later PR edits `config/default.yaml` or flips `pepe_enabled` for this lock, it contradicts the config invariant.
- If a later PR treats the watch pool as simultaneous live legs or as N×10% capital, it contradicts this lock.
- If a later PR ranks DEMO_BLOCK names with invented scores, that ranking is **invalid**.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.

---

## Overlay — Scalp LIVE conditional gate ([`120`](./120-kaje-risk-scalp-live-gate-2026-09-12.md))

Kaje + Risk ACK **2026-09-12**. This watch lock is **unchanged** (one 10% bucket · DEMO_BLOCK on the **demo** key · catalogue CLEAR ≠ DEMO_BLOCK ≠ Soft PASS ≠ arm).

[`120`](./120-kaje-risk-scalp-live-gate-2026-09-12.md) is the **PEPE LIVE conditional GATE** plus Ops **LIVE queue** **PEPE ★ → PUMP → TRUMP → WIF** (all **`LIVE_CLEAR_BOTH`** on the **live** key). **TRUMP** exchange max **50×** / **policy ≤10×**. **DEMO_BLOCK unchanged** on the demo key. Soft PASS ≠ Scalp-arm. `not_a_forecast`.
