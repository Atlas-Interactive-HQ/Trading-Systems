# 120 — PEPE LIVE conditional gate (Kaje + Risk, 2026-09-12)

**Stance:** **PEPE LIVE conditional GATE.** `not_a_forecast: true`. **Never places orders from this note.**
**Config:** `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`.
**Scalp:** **Soft PASS ≠ Scalp-arm.** `place_orders: false`.
**Ledger:** `TL-120` in `research/trial_ledger.jsonl` — **`pre_registered: true`**. No score. No invented PnL / expectancy.
**Numbering:** This is **phase1/120** (next free after [`119`](./119-public-md-scalp-rsi14-mr-1h.md)). **phase1/121** is **reserved** for the 2020 majors **backtest / research** family-pick — **not** written or scored in this PR.

---

## Why this lock

This note is the **PEPE LIVE conditional GATE**. Soft PASS, public-MD scores ([`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md)), DEMO_BLOCK, or a PEPE name **do not POST**.

**Still no PEPE Scalp POST until ALL of:**

1. **2020 measured edge** — reserved **phase1/121** (BTC / ETH / DOGE 1H backtest; honesty bar; **not** a Soft PASS claim alone).
2. **PEPE re-score** — same 121 family, **measured** on PEPE-USDC public-MD. **No 2020 number transplant.**
3. **Kaje `session-ja`** (parent [`113`](./113-kaje-architecture-2026-09-12.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md) **`ga live` + sleeve list** not dropped).

**Soft PASS ≠ Scalp-arm. DEMO_BLOCK still. not_a_forecast.**

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
| I9 | This note **does not POST**. **No PEPE POST** until **121 + PEPE re-score + session-ja**. |
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

## Honesty — Ops LIVE_CLEAR_BOTH (2026-09-12, live key)

Ops **2026-09-12** stamped **`LIVE_CLEAR_BOTH`** on the **live** key for:

| Leg | Stamp | Notes |
|-----|--------|-------|
| **PEPE-USDC** (spot) | `LIVE_CLEAR` (BOTH) | Live key. **Not** demo. |
| **PEPE-USD_UM_XPERP-310404** (X-Perp) | `LIVE_CLEAR` (BOTH) | Catalogue / MD id cited as verified placeable on **live**. **Not** an invented order id. Public MD `…310404` **≠** a demo order id (DOGE taught MD `…310404` ≠ demo `…310516`). |

| Honesty | Lock |
|---------|------|
| **Key** | **Live** key — **not** demo. |
| **`settleCcy`** | **USDC on acct — confirm before place.** Do **not** POST until settle currency on the account is confirmed USDC for that product / size. This PR does **not** invent that confirm as already done for a live order. |
| **DEMO_BLOCK** | **Still on** for the **demo** key ([`114`](./114-scalp-multi-coin-watch-2026-09-12.md) / [`115`](./115-public-md-scalp-method.md)). Full meme screen on demo OMS. **DEMO_BLOCK ≠ invent live** — and live-clear **≠** lift DEMO_BLOCK. |
| **≠ arm** | `LIVE_CLEAR_BOTH` **≠** Soft PASS **≠** session-ja **≠** PEPE re-score **≠** Scalp-arm. |

This stamp **does not**:

- arm Scalp or place a PEPE POST
- lift DEMO_BLOCK on the demo key
- invent a live order `instId`
- skip **121 + PEPE re-score + session-ja**
- skip **`settleCcy` USDC confirm before place**
- transplant 2020 or [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) numbers onto PEPE
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
| **arm** | **121 + PEPE re-score + `session-ja`** (and parent **`ga live` + sleeve list**), then an explicit PEPE Scalp POST. | The only PEPE POST path on this gate. |

**DEMO_BLOCK still. DEMO_BLOCK ≠ invent live. `LIVE_CLEAR_BOTH` ≠ arm.**

---

## Reserved 121 — 2020 majors BACKTEST (required before PEPE POST)

**phase1/121** is reserved for a **measured** 1H backtest (not written here; **no invented numbers**):

| Field | Lock |
|-------|------|
| **Role** | **BACKTEST / research** — **measured edge** to pick the Scalp family |
| **Families** | BreakoutV1 · EMA12/21 · RSI14 MR · Dual Thrust+RVOL |
| **Assets** | **BTC-USD · ETH-USD · DOGE-USD** |
| **Bar** | **1H** |
| **Window** | **Jul 2020 → Jan 2021** |
| **Bar to beat** | **Honesty bar** (same-window / same-cost reference — **not** a Soft PASS claim alone) |
| **Bind on this gate** | **No PEPE POST until 121 measured edge exists.** Soft PASS claim alone **insufficient**. |
| **Not this** | Not a live-arm. Not a PEPE score. **No number transplant** onto PEPE. |

121 is **backtest / research**, not a live score. On **this PEPE gate**, it is still a **hard no-POST** until measured. This PR does **not** score 121 or invent a winner / honesty-bar €.

---

## PEPE re-score (required before PEPE POST)

| Rule | Lock |
|------|------|
| **Family** | The **121 winner** (same family; do not invent it here). |
| **Instrument** | **PEPE-USDC** public-MD (this gate). Do **not** copy [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) PUMP/TRUMP/WIF tables. |
| **Edge** | **Measured** vs honesty bar. **No 2020 number transplant.** |
| **This PR** | **Does not** write a PEPE re-score. No invented PEPE €. |

[`114`](./114-scalp-multi-coin-watch-2026-09-12.md) multi-coin **watch** stays under **one** 10% bucket. Watch ≠ this PEPE gate ≠ arm.

---

## PEPE LIVE POST — ALL required (none skipped)

**No PEPE Scalp POST** until **all** of the following. This note satisfies **only** the Ops live-placeable honesty stamp (and **not** the `settleCcy` confirm-before-place).

| # | Condition | Status in this PR |
|---|-----------|-------------------|
| **G1** | **2020 measured edge (phase1/121)** — family pick vs honesty bar. | **Pending** — 121 reserved, **unscored**. |
| **G2** | **PEPE re-score** — same family on PEPE-USDC public-MD; measured; no transplant. | **Pending** — no invented table. |
| **G3** | **Kaje `session-ja`** + sleeve list. Parent **`ga live`** not dropped. | **Pending** — this note is **not** `session-ja`. |
| **G4** | Ops **live** placeable. **DEMO_BLOCK still.** | **PEPE `LIVE_CLEAR_BOTH`** on **PEPE-USDC** + **PEPE-USD_UM_XPERP-310404** (live key, 2026-09-12). |
| **G5** | **`settleCcy` USDC on acct — confirm before place.** | **Required at place time.** Not invented as already confirmed for an order. |

Soft PASS ≠ Scalp-arm. `LIVE_CLEAR_BOTH` ≠ skip G1–G3 / G5.

---

## Caps if armed (later — not an arm)

If a later explicit arm clears **G1–G5**:

| Cap | Lock |
|-----|------|
| **Scalp bucket** | **≤10%** of book — the **1** in [`113`](./113-kaje-architecture-2026-09-12.md) **6 : 3 : 1**. |
| **Euro stamp (2026-09-12 Core fill)** | **~€24** of **~€103 USDC residual** (Kaje/Risk stamp after the Core fill). **Not** invented MTM PnL. **Not** a new panel €. |
| **Leverage** | **≤10× isolated**. If used leverage cannot be demonstrated: **NO TRADE**. |
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
| **121** (reserved) | 2020 majors measured-edge backtest. **Required before PEPE POST.** Not scored here. |

---

## What this PR does / does not

**Does**

- Lock **phase1/120** as the **PEPE LIVE conditional GATE**.
- Stamp Ops honesty **2026-09-12**: **`LIVE_CLEAR_BOTH`** on the **live** key for **PEPE-USDC** + **PEPE-USD_UM_XPERP-310404**.
- Stamp **`settleCcy` USDC on acct — confirm before place.**
- Stamp **DEMO_BLOCK still.**
- Stamp **no POST** until **121 + PEPE re-score + session-ja**.
- Restate **Soft PASS ≠ Scalp-arm** · ≤10% Scalp · ≤10× iso · 5% kill.
- Pre-register `TL-120` (not a score). Index in [`README`](./README.md). Overlay pointers on 107 / 113 / 114 / 116.

**Does not**

- Change `config/default.yaml` or flip `pepe_enabled`.
- Place PEPE / Mid orders or write phase1/121 / PEPE re-score numbers.
- Invent PnL, a 121 winner, or a PEPE table.
- Invent a live order `instId` or lift DEMO_BLOCK.
- Treat `LIVE_CLEAR_BOTH` or Soft PASS as Scalp-arm.
- Skip `settleCcy` USDC confirm-before-place.

---

## Honesty / invalidation

- Soft PASS / `LIVE_CLEAR_BOTH` / [`115`](./115-public-md-scalp-method.md) / [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) **≠ Scalp-arm**.
- A later PR that POSTs PEPE **without** 121 + PEPE re-score + session-ja violates this gate.
- A later PR that POSTs without **`settleCcy` USDC confirm** on acct violates I10.
- A later PR that lifts DEMO_BLOCK or invents live from demo `51001` violates I5.
- A later PR that transplants 2020 or PUMP/TRUMP/WIF numbers onto PEPE violates G2 / I4.
- A later PR that edits `config/default.yaml` or flips `pepe_enabled` contradicts I3.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ Scalp-arm. DEMO_BLOCK still. `config/default.yaml` untouched.
