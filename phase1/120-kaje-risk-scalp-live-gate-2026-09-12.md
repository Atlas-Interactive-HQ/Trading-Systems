# 120 — PEPE LIVE conditional gate (Kaje + Risk, 2026-09-12)

**Stance:** **PEPE LIVE conditional GATE.** `not_a_forecast: true`. **Never places orders from this note.**
**Config:** `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`.
**Scalp:** **Soft PASS ≠ Scalp-arm.** `place_orders: false`.
**Ledger:** `TL-120` in `research/trial_ledger.jsonl` — **`pre_registered: true`**. No score. No invented PnL / expectancy.
**Numbering:** This is **phase1/120** (next free after [`119`](./119-public-md-scalp-rsi14-mr-1h.md)). **phase1/121** is **reserved** for the 2020 majors **backtest / research** family-pick — **not** written or scored in this PR.

---

## Why this lock

This note is the **PEPE LIVE conditional GATE**. Soft PASS, public-MD scores ([`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md)), DEMO_BLOCK, or a PEPE name **do not POST**.

**Live Scalp POST gate (hard — Risk HOLD / ACK):**

1. Ops **`LIVE_CLEAR`** on the chosen LIVE-queue name.
2. Kaje **`session-ja`** + **sleeve list** / **`ga live`** (parent [`113`](./113-kaje-architecture-2026-09-12.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md)).
3. Caps **≤10%** book · **≤10× isolated**.

**phase1/121** (2020 BTC / ETH / DOGE) = **BACKTEST / research family-pick ONLY.** **Not** a hard no-POST / live-blocker. Do **not** resurrect 2020 as a live-blocker.

**Instrument re-score (PEPE ★ first)** = **honesty preferred** before first live. **Not** a hard live-blocker. **Not** a 2020 transplant.

**Ops LIVE queue (live key, all `LIVE_CLEAR_BOTH`):** **PEPE ★ → PUMP → TRUMP → WIF**. Queue ≠ arm. **DEMO_BLOCK unchanged.**

**Soft PASS ≠ Scalp-arm. not_a_forecast.**

---

## Hard invariants

| Id | Lock |
|----|------|
| I1 | `not_a_forecast: true` · `place_orders: false` |
| I2 | **Soft PASS ≠ Scalp-arm.** V2 PASS / DEV board / [`115`](./115-public-md-scalp-method.md) method / [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) scores **≠** Scalp-arm. |
| I3 | `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`. |
| I4 | Do **not** invent PnL, expectancy, panel €, Core MTM, or an order `instId`. |
| I5 | **DEMO_BLOCK still** on the **demo** key. DEMO_BLOCK **≠ invent live**. This note does **not** lift the meme screen on demo OMS. |
| I6 | Martingale / grid / average-down **forbidden**. |
| I7 | Daily kill **5% of book** still applies (pack lock; [`00`](./00-decisions-and-deltas.md) L2). |
| I8 | Sweeps / transfers / withdraws **never auto** — Kaje explicit yes ([`107`](./107-eur200-capital-readiness-2026-09-12.md)). |
| I9 | This note **does not POST**. **Live POST gate** = Ops **`LIVE_CLEAR`** + Kaje **`session-ja`** (+ sleeve / `ga live`) + **≤10% / ≤10×**. **121 is not a live-blocker.** |
| I10 | **`settleCcy` USDC on acct — confirm before place.** LIVE_CLEAR_BOTH **≠** skip that confirm. |

`place_orders: false`. Soft PASS ≠ Scalp-arm. DEMO_BLOCK still.

---

## Still true (do not rewrite)

| Sleeve | State |
|--------|--------|
| **Core BTC** | Spot **hold already filled** ~€144 @ 77304.3 · `ordId` **`3915002084440100864`** ([`116`](./116-kaje-capital-intent-2026-09-12.md)). Core exception **executed**. Not parked. |
| **Mid DOGE** | **#71 conditional / currently flat.** Soft PASS / DEV #71 **≠ Mid-arm**. |
| **Scalp** | **Unarmed.** This is the **PEPE LIVE conditional GATE**. Soft PASS ≠ Scalp-arm. |

~€144 / ~€72 are the live 60/30 stamps from [`116`](./116-kaje-capital-intent-2026-09-12.md). They are **not** a new panel score.

---

## Honesty — Ops LIVE queue + LIVE_CLEAR_BOTH (2026-09-12, live key)

Ops **2026-09-12** stamped **`LIVE_CLEAR_BOTH`** on the **live** key for the **LIVE queue** (order locked):

**PEPE ★ → PUMP → TRUMP → WIF**

| # | Name | Spot (cite) | X-Perp MD (cite) | Stamp | Notes |
|---|------|-------------|------------------|--------|-------|
| **1 ★** | **PEPE** | **PEPE-USDC** | **PEPE-USD_UM_XPERP-310404** | `LIVE_CLEAR_BOTH` | **Preferred / first.** This gate’s primary name. |
| **2** | **PUMP** | **PUMP-USDC** | **PUMP-USD_UM_XPERP-310404** | `LIVE_CLEAR_BOTH` | Next if PEPE re-score does not work. |
| **3** | **TRUMP** | **TRUMP-USDC** | **TRUMP-USD_UM_XPERP-310704** | `LIVE_CLEAR_BOTH` | **Exchange max 50×** — **policy ≤10× isolated**. Do **not** use 50×. |
| **4** | **WIF** | **WIF-USDC** | **WIF-USD_UM_XPERP-310815** | `LIVE_CLEAR_BOTH` | Last in this Ops queue. |

Catalogue / MD ids are **cites** of the verified live legs — **not** invented order ids. Public MD `…310404` **≠** a demo order id (DOGE taught MD `…310404` ≠ demo `…310516`).

| Honesty | Lock |
|---------|------|
| **Key** | **Live** key — **not** demo. |
| **Queue** | **PEPE ★ → PUMP → TRUMP → WIF.** ★ = try PEPE first. Queue ≠ arm. Queue ≠ split the 10% bucket. |
| **TRUMP lev** | Venue/exchange **max 50×** is **not** permission. **Policy ≤10× isolated** still wins. If ≤10× cannot be demonstrated: **NO TRADE**. |
| **`settleCcy`** | **USDC on acct — confirm before place** (whichever queue name is later armed). This PR does **not** invent that confirm as already done for a live order. |
| **DEMO_BLOCK** | **Unchanged — still on** for the **demo** key ([`114`](./114-scalp-multi-coin-watch-2026-09-12.md) / [`115`](./115-public-md-scalp-method.md)). Full meme screen on demo OMS. Live-clear **≠** lift DEMO_BLOCK. |
| **≠ arm** | Queue / `LIVE_CLEAR_BOTH` **≠** Soft PASS **≠** session-ja **≠** re-score **≠** Scalp-arm. |

This stamp **does not**:

- arm Scalp or place a POST
- lift DEMO_BLOCK on the demo key (**DEMO_BLOCK unchanged**)
- invent a live order `instId`
- skip the **live POST gate** (`LIVE_CLEAR` + `session-ja` + sleeve / `ga live` + ≤10% / ≤10×)
- resurrect **121 / 2020** as a hard no-POST / live-blocker
- skip **`settleCcy` USDC confirm before place**
- treat TRUMP **50×** as usable leverage
- transplant 2020 or [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) numbers onto any queue name
- flip `pepe_enabled`

---

## Stamps (do not collapse)

These stamps are **different**. None implies the next.

| Stamp | What it is | What it is **not** |
|-------|------------|---------------------|
| **Catalogue CLEAR** | Name / row on public `instruments` ([`114`](./114-scalp-multi-coin-watch-2026-09-12.md)). | **≠** demo-tradable. **≠** `LIVE_CLEAR`. **≠** arm. |
| **DEMO_BLOCK** | Ops **demo key** cannot demo-trade that name. **Still on.** | **≠ invent live.** **≠** arm. Live-clear does **not** lift it. |
| **DEMO_CLEAR** | Reserved: this account **can** demo-trade after re-verify. | **≠** `LIVE_CLEAR`. **≠** arm. |
| **`LIVE_CLEAR` / `LIVE_CLEAR_BOTH`** | Ops verified the **live** key can place that product (spot + X-Perp for BOTH). | **≠** Soft PASS. **≠** session-ja. **≠** arm. **≠** skip `settleCcy` confirm. |
| **Soft PASS** | Research-panel gate on a locked card. | **≠** Scalp-arm. |
| **arm** | Ops **`LIVE_CLEAR`** + Kaje **`session-ja`** + **sleeve list** / **`ga live`** + **≤10% / ≤10×**. | Queue / `LIVE_CLEAR_BOTH` / Soft PASS / **121** **≠** this. |

**DEMO_BLOCK still. DEMO_BLOCK ≠ invent live. `LIVE_CLEAR_BOTH` ≠ arm.**

---

## Reserved 121 — 2020 majors BACKTEST / research family-pick ONLY

**phase1/121** is reserved for a **measured** 1H backtest (not written here; **no invented numbers**).

**Risk HOLD / ACK:** 121 is **BACKTEST / research family-pick ONLY.** It is **NOT** a hard no-POST / live-blocker. Do **not** resurrect 2020 as a live-blocker.

| Field | Lock |
|-------|------|
| **Role** | **BACKTEST / research only** — pick a Scalp **family** (honesty bar; not Soft PASS alone) |
| **Families** | BreakoutV1 · EMA12/21 · RSI14 MR · Dual Thrust+RVOL |
| **Assets** | **BTC-USD · ETH-USD · DOGE-USD** |
| **Bar** | **1H** |
| **Window** | **Jul 2020 → Jan 2021** |
| **Live bind** | **None.** 121 **does not** block a Scalp POST. |
| **Not this** | Not a live-arm. Not a PEPE score. **No number transplant** onto PEPE or any alt. |

This PR does **not** score 121 or invent a winner / honesty-bar €.

---

## Instrument re-score (PEPE ★ first) — honesty preferred, not a live-blocker

| Rule | Lock |
|------|------|
| **Role** | **Honesty preferred** before first live. **Not** a hard no-POST. **Not** a 2020 live-blocker. |
| **First instrument** | **PEPE-USDC** public-MD (**★**). |
| **If PEPE does not work** | Same family (if 121 has a winner; else do not invent one), **measured** on the **next LIVE-queue** name (PUMP → TRUMP → WIF). |
| **Not this** | Do **not** copy [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) tables as a live re-score. **No 2020 number transplant.** |
| **This PR** | **Does not** write a re-score. No invented €. |

[`114`](./114-scalp-multi-coin-watch-2026-09-12.md) multi-coin **watch** stays under **one** 10% bucket. Watch ≠ LIVE queue ≠ arm.

---

## Live Scalp POST gate (hard)

**This note does not POST.** A later Scalp POST still needs the **hard** gate below. **121 / 2020 is not in this table.**

| # | Condition | Status in this PR |
|---|-----------|-------------------|
| **G1** | Ops **`LIVE_CLEAR`** on the chosen LIVE-queue name. **DEMO_BLOCK unchanged.** | **LIVE queue** **PEPE ★ → PUMP → TRUMP → WIF** all **`LIVE_CLEAR_BOTH`** (live key, 2026-09-12). |
| **G2** | Kaje **`session-ja`** + **sleeve list** / **`ga live`**. | **Pending** — this note is **not** `session-ja`. |
| **G3** | Caps **≤10%** book · **≤10× isolated** (TRUMP exchange max 50× ≠ policy). | Policy locked. Runtime yaml **untouched**. |
| **G4** | **`settleCcy` USDC on acct — confirm before place.** | **Required at place time.** Not invented as already confirmed for an order. |

| Honesty (not a hard live-blocker) | Status |
|-----------------------------------|--------|
| **121** 2020 family-pick backtest | **Research only.** **Not** G1. **Not** a no-POST. |
| **Instrument re-score** (PEPE ★ first) | **Honesty preferred** before first live. **Not** a hard live-blocker. Do **not** resurrect 2020 as one. |

Soft PASS ≠ Scalp-arm. `LIVE_CLEAR_BOTH` ≠ skip G2. **121 ≠ live-blocker.**

---

## Caps if armed (later — not an arm)

If a later explicit arm clears the **hard** live POST gate (**G1–G4**):

| Cap | Lock |
|-----|------|
| **Scalp bucket** | **≤10%** of book — the **1** in [`113`](./113-kaje-architecture-2026-09-12.md) **6 : 3 : 1**. |
| **Euro stamp (2026-09-12 Core fill)** | **~€24** of **~€103 USDC residual** (Kaje/Risk stamp after the Core fill). **Not** invented MTM PnL. **Not** a new panel €. |
| **Leverage** | **≤10× isolated** for every queue name. **TRUMP exchange max 50× ≠ policy.** If ≤10× cannot be demonstrated: **NO TRADE**. |
| **Journal** | Journal Scalp POSTs (append-only). This note still **`place_orders: false`**. |
| **Martingale** | **Forbidden.** [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) 3×SL → 28m applies **once a PEPE system exists**. |
| **Kill** | Daily **5% of book** still applies. |
| **Soft PASS** | Still **≠** arm. |
| **DEMO_BLOCK** | **Still on** for demo OMS. |

Runtime yaml **untouched**. This PR does **not** raise runtime caps.

---

## Cross-refs (do not re-lock)

| Doc | How this gate uses it |
|-----|------------------------|
| [`113`](./113-kaje-architecture-2026-09-12.md) | Parent architecture 6:3:1; PEPE Scalp **target name**; ≤10×; `ga live` + session-ja + sleeve list. This note is the **PEPE LIVE conditional GATE**. |
| [`114`](./114-scalp-multi-coin-watch-2026-09-12.md) | Multi-coin **watch** under one 10% bucket. **DEMO_BLOCK still** on demo key. |
| [`115`](./115-public-md-scalp-method.md) | Public-MD method. DEMO_BLOCK full meme screen on demo OMS. Public MD ≠ arm. |
| [`116`](./116-kaje-capital-intent-2026-09-12.md) | Capital parent: Core fill ~€144; Mid #71 ~€72 conditional / flat; Soft PASS ≠ Scalp-arm. |
| [`117`](./117-public-md-scalp-first-score-ema1221-1h.md) / [`118`](./118-public-md-scalp-breakoutv1-1h.md) / [`119`](./119-public-md-scalp-rsi14-mr-1h.md) | Public-MD **scores** on PUMP / TRUMP / WIF. **≠** 121. **≠** PEPE re-score. **≠** arm. |
| [`107`](./107-eur200-capital-readiness-2026-09-12.md) | HALTED / tiny / leverage addendum / ~€240 figure. |
| [`108`](./108-dev-board-research-lock.md) | Research freeze. Live Core fill is capital, not a CORE-R1 promote. |
| [`111`](./111-sl-fill-release-human-ping.md) / [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) | Ping + 3×SL → 28m once a PEPE system is armed. Not an arm. |
| [`105`](./105-portfolio-core-major.md) / [`106`](./106-research-governance-board.md) | STRATEGY GREEN ≠ PORTFOLIO GREEN. Soft PASS ≠ arm. |
| **121** (reserved) | 2020 majors **BACKTEST / research family-pick ONLY.** **Not** a hard no-POST / live-blocker. Not scored here. |

---

## What this PR does / does not

**Does**

- Lock **phase1/120** as the **PEPE LIVE conditional GATE**.
- Stamp Ops **LIVE queue** **2026-09-12**: **PEPE ★ → PUMP → TRUMP → WIF**, all **`LIVE_CLEAR_BOTH`** on the **live** key.
- Stamp **TRUMP** exchange max **50×** but **policy ≤10×**.
- Stamp **`settleCcy` USDC on acct — confirm before place.**
- Stamp **DEMO_BLOCK unchanged.**
- Stamp **live POST gate** = **`LIVE_CLEAR` + `session-ja` (+ sleeve / `ga live`) + ≤10% / ≤10×**.
- Stamp **121 = backtest / family-pick ONLY** — **not** a hard no-POST.
- Stamp instrument re-score (PEPE ★ first) = **honesty preferred**, not a live-blocker.
- Restate **Soft PASS ≠ Scalp-arm** · ≤10% Scalp · ≤10× iso · 5% kill.
- Pre-register `TL-120` (not a score). Index in [`README`](./README.md). Overlay pointers on 107 / 113 / 114 / 116.

**Does not**

- Change `config/default.yaml` or flip `pepe_enabled`.
- Place PEPE / Mid orders or write phase1/121 / PEPE re-score numbers.
- Invent PnL, a 121 winner, or a PEPE table.
- Invent a live order `instId` or lift DEMO_BLOCK.
- Treat `LIVE_CLEAR_BOTH`, the LIVE queue, or Soft PASS as Scalp-arm.
- Skip `settleCcy` USDC confirm-before-place.
- Use TRUMP exchange **50×** (policy remains **≤10×**).

---

## Honesty / invalidation

- Soft PASS / `LIVE_CLEAR_BOTH` / [`115`](./115-public-md-scalp-method.md) / [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) **≠ Scalp-arm**.
- A later PR that POSTs **without** `LIVE_CLEAR` + `session-ja` (+ sleeve / `ga live`) + ≤10% / ≤10× violates the **live POST gate**.
- A later PR that treats **121 / 2020** as a **hard no-POST / live-blocker** contradicts this Risk HOLD / ACK.
- A later PR that uses TRUMP at **50×** (exchange max) violates the **≤10×** policy cap.
- A later PR that POSTs without **`settleCcy` USDC confirm** on acct violates I10.
- A later PR that lifts DEMO_BLOCK or invents live from demo `51001` violates I5.
- A later PR that transplants 2020 numbers onto PEPE / PUMP / TRUMP / WIF violates I4.
- A later PR that edits `config/default.yaml` or flips `pepe_enabled` contradicts I3.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ Scalp-arm. DEMO_BLOCK still. `config/default.yaml` untouched.
