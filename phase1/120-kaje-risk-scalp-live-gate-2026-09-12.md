# 120 — Kaje + Risk Scalp LIVE conditional gate (2026-09-12)

**Stance:** Live-gate / Risk ACK lock. `not_a_forecast: true`. **Never places orders from this note.**
**Config:** `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`.
**Scalp:** **Soft PASS ≠ Scalp-arm.** `place_orders: false`.
**Ledger:** `TL-120` in `research/trial_ledger.jsonl` — **`pre_registered: true`**. No score. No invented PnL / expectancy.
**Numbering:** This is **phase1/120** (next free after [`119`](./119-public-md-scalp-rsi14-mr-1h.md)). **phase1/121** is **reserved** for the 2020 majors **backtest / research** family-pick — **not** written or scored in this PR.

---

## Why this lock

Kaje + Risk ACK **2026-09-12** (Europe/Amsterdam): freeze the **conditional** path to a **first Scalp LIVE POST** so later work cannot treat Soft PASS, public-MD scores ([`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md)), DEMO_BLOCK, or a PEPE name as permission to POST.

**Risk ACK (authoritative wording for this note):**

1. **2020 BTC / ETH / DOGE = BACKTEST / research only** — lives on reserved **phase1/121**. Used to **pick the Scalp family**. **Not** a hard prerequisite that blocks every future Scalp POST forever. **First** Scalp live still uses the **121 winner as the locked family** (Kaje intent).
2. **Live instrument = any Ops `LIVE_CLEAR` coin.** **PEPE preferred if it works**; else next alts (PUMP / TRUMP / WIF / …).
3. Still need **Kaje `session-ja` + sleeve list** before any Scalp POST.
4. **Soft PASS ≠ arm** · Scalp **≤10%** book · **≤10× isolated** · **DEMO_BLOCK ≠ invent live**.

**Ops stamp (same date):** **PEPE `LIVE_CLEAR_BOTH` already verified.** That is **not** an arm.

**Soft PASS ≠ Scalp-arm. not_a_forecast.**

---

## Hard invariants

| Id | Lock |
|----|------|
| I1 | `not_a_forecast: true` · `place_orders: false` |
| I2 | **Soft PASS ≠ Scalp-arm.** V2 PASS / DEV board / [`115`](./115-public-md-scalp-method.md) method / [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) scores **≠** Scalp-arm. |
| I3 | `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`. |
| I4 | Do **not** invent PnL, expectancy, panel €, Core MTM, or an order `instId`. |
| I5 | **DEMO_BLOCK** on the **demo** key **≠ invent live**. Demo empty / place `51001` does **not** invent a live route. |
| I6 | Martingale / grid / average-down **forbidden**. |
| I7 | Daily kill **5% of book** still applies (pack lock; [`00`](./00-decisions-and-deltas.md) L2). |
| I8 | Sweeps / transfers / withdraws **never auto** — Kaje explicit yes ([`107`](./107-eur200-capital-readiness-2026-09-12.md)). |
| I9 | This note **does not POST**. Journal POSTs **only if** a later explicit arm clears the first-live gate below. |

`place_orders: false`. Soft PASS ≠ Scalp-arm.

---

## Still true (do not rewrite)

| Sleeve | State |
|--------|--------|
| **Core BTC** | Spot **hold already filled** ~€144 @ 77304.3 · `ordId` **`3915002084440100864`** ([`116`](./116-kaje-capital-intent-2026-09-12.md)). Core exception **executed**. Not parked. |
| **Mid DOGE** | **#71 conditional / currently flat.** Soft PASS / DEV #71 **≠ Mid-arm**. |
| **Scalp** | **Unarmed.** Soft PASS ≠ Scalp-arm until this gate **and** a later explicit arm. |

~€144 / ~€72 are the live 60/30 stamps from [`116`](./116-kaje-capital-intent-2026-09-12.md). They are **not** a new panel score.

---

## Stamps (do not collapse)

These stamps are **different**. None implies the next.

| Stamp | What it is | What it is **not** |
|-------|------------|---------------------|
| **Catalogue CLEAR** | Name / row on public `instruments` ([`114`](./114-scalp-multi-coin-watch-2026-09-12.md)). | **≠** demo-tradable. **≠** `LIVE_CLEAR`. **≠** arm. |
| **DEMO_BLOCK** | Ops **demo key** cannot demo-trade that name ([`114`](./114-scalp-multi-coin-watch-2026-09-12.md) / [`115`](./115-public-md-scalp-method.md)). Full meme screen on demo OMS. | **≠** proof the live key is blocked. **≠ invent live.** **≠** arm. |
| **DEMO_CLEAR** | Reserved: this account **can** demo-trade after re-verify. | **≠** `LIVE_CLEAR`. **≠** arm. |
| **`LIVE_CLEAR`** | Ops verified the **live** key can place that product (not demo). | **≠** Soft PASS. **≠** session-ja. **≠** arm. |
| **`LIVE_CLEAR_BOTH`** | Ops verified **both** listed live legs for that name (spot **and** isolated X-Perp where listed). | **≠** arm. **≠** permission to skip session-ja / sleeve list. |
| **Soft PASS** | Research-panel gate on a locked card. | **≠** Scalp-arm. |
| **arm** | Kaje **`ga live`** (parent [`113`](./113-kaje-architecture-2026-09-12.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md)) **and** **`session-ja`** **and** **sleeve list**, after the first-live family / instrument conditions below. | The only Scalp POST path. |

**DEMO_BLOCK ≠ invent live.** **`LIVE_CLEAR` ≠ arm.**

Public MD `…310404` **≠** an order `instId` (DOGE already taught MD `…310404` ≠ demo order `…310516`). Do **not** invent a live order id.

---

## Ops — PEPE `LIVE_CLEAR_BOTH` (2026-09-12)

Ops verified **PEPE `LIVE_CLEAR_BOTH`** on the **live** key **2026-09-12**.

| Leg (catalogue / MD cite only — **not** an invented order id) | Stamp |
|---------------------------------------------------------------|--------|
| Spot **PEPE-USDC** | `LIVE_CLEAR` (part of BOTH) |
| X-Perp MD **PEPE-USD_UM_XPERP-310404** | `LIVE_CLEAR` (part of BOTH) |

This stamp **clears the Ops live-placeable check for PEPE**. It does **not**:

- arm Scalp
- lift DEMO_BLOCK on the **demo** key
- invent a live order `instId`
- skip `session-ja` / sleeve list / `ga live`
- transplant 2020 or [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) numbers onto PEPE
- flip `pepe_enabled`

No other name is stamped `LIVE_CLEAR` in this note. PUMP / TRUMP / WIF / … remain **candidates** only after a later Ops live re-verify.

---

## Reserved 121 — 2020 majors BACKTEST / research (family pick)

**phase1/121** is reserved for a **measured** 1H backtest (not written here; **no invented numbers**):

| Field | Lock |
|-------|------|
| **Role** | **BACKTEST / research only** — **choose the Scalp family** |
| **Families** | BreakoutV1 · EMA12/21 · RSI14 MR · Dual Thrust+RVOL |
| **Assets** | **BTC-USD · ETH-USD · DOGE-USD** |
| **Bar** | **1H** |
| **Window** | **Jul 2020 → Jan 2021** |
| **Bar to beat** | **Honesty bar** (same-window / same-cost reference — **not** a Soft PASS claim alone) |
| **Not this** | Not a live-arm. Not a PEPE score. **No number transplant** onto PEPE or any alt. |

### How 121 binds (Risk ACK)

| Case | Bind |
|------|------|
| **First Scalp live** | Uses the **121 winner as the locked Scalp family** (Kaje intent). First live does **not** pick a different family by Soft PASS or by meme-score headline. |
| **Later Scalp POSTs** | 2020 / 121 is **not** a hard prerequisite that blocks every future Scalp POST forever. A later explicit Kaje/Risk note may change family; this lock does not freeze 121 as a perpetual veto. |
| **This PR** | Does **not** score 121. Does **not** invent a winner. Does **not** invent honesty-bar €. |

121 **unscored ≠** invent a family. First Scalp live **waits** on a later measured 121 winner (or an explicit later Kaje note that names the locked family).

---

## Live instrument (any Ops `LIVE_CLEAR`; PEPE preferred)

Live Scalp instrument is **not** locked to PEPE.

| Rule | Lock |
|------|------|
| **Universe** | **Any** Ops **`LIVE_CLEAR`** coin that can take **≤10× isolated** where leverage is used. |
| **Preference** | **PEPE preferred if it works** — PEPE already **`LIVE_CLEAR_BOTH`**, **and** a later **instrument re-score** of the **121 family** on **PEPE-USDC public-MD** shows **measured edge** (honesty bar; **no 2020 number transplant**). |
| **Else** | Next alts: **PUMP / TRUMP / WIF / …** — only after Ops **`LIVE_CLEAR`** on that name **and** the same-family **instrument re-score** on that coin’s public-MD. |
| **Watch ≠ allocate** | [`114`](./114-scalp-multi-coin-watch-2026-09-12.md) multi-coin watch stays under **one** 10% bucket. Watch ≠ sleeve ≠ arm. |
| **One position** | Does **not** lift the pack one-directional-position rule. |

**“If it works”** = measured edge on **that** instrument, same locked family, **not** a transplanted 2020 or PUMP/TRUMP/WIF [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) table.

Do **not** invent a PEPE / PUMP / TRUMP / WIF re-score in this PR.

---

## First Scalp live — conditions (ALL before first POST)

**First** Scalp LIVE POST still requires **all** of the following. This note **does not** satisfy them except the already-stamped PEPE `LIVE_CLEAR_BOTH`.

| # | Condition | Status in this PR |
|---|-----------|-------------------|
| **F1** | **121 winner locked as the Scalp family** (2020 majors backtest / honesty bar). Soft PASS claim alone **insufficient**. | **Pending** — 121 reserved, **unscored**. No invented winner. |
| **F2** | **Instrument re-score:** same family, **measured** on the chosen **`LIVE_CLEAR`** coin’s public-MD. **No 2020 transplant.** PEPE preferred if that re-score works; else next `LIVE_CLEAR` alt. | **Pending** — no invented PEPE/alt table. |
| **F3** | **Kaje `session-ja` + sleeve list** before POST. Parent [`113`](./113-kaje-architecture-2026-09-12.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md) **`ga live`** is **not** dropped. | **Pending** — this note is **not** `session-ja`. |
| **F4** | Ops **live** (not demo) **placeable** on the chosen coin. **DEMO_BLOCK ≠ invent live.** | **PEPE `LIVE_CLEAR_BOTH` already verified.** Other names: **not** stamped here. |

F1 is the **first-live family lock** (Kaje intent). It is **not** a forever-blocker of every later Scalp POST.

---

## Caps if armed (later — not an arm)

If a later explicit arm clears the first-live gate:

| Cap | Lock |
|-----|------|
| **Scalp bucket** | **≤10%** of book — the **1** in [`113`](./113-kaje-architecture-2026-09-12.md) **6 : 3 : 1**. |
| **Euro stamp (2026-09-12 Core fill)** | **~€24** of **~€103 USDC residual** (Kaje/Risk stamp after the Core fill). **Not** invented MTM PnL. **Not** a new panel €. |
| **Leverage** | **≤10× isolated** ([`113`](./113-kaje-architecture-2026-09-12.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md) addendum). Ceiling ≠ venue verify on a non-PEPE name ≠ arm. If used leverage cannot be demonstrated: **NO TRADE**. |
| **Journal** | Journal Scalp POSTs (append-only). This note still **`place_orders: false`**. |
| **Martingale** | **Forbidden.** [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) 3×SL → 28m still applies **once a Scalp system exists** — not size-up. |
| **Kill** | Daily **5% of book** still applies. |
| **Soft PASS** | Still **≠** arm. |

Runtime yaml **untouched** (`leverage_default: 2.0`, `leverage_hard_cap: 5.0`). This PR does **not** raise runtime caps.

---

## Cross-refs (do not re-lock)

| Doc | How this gate uses it |
|-----|------------------------|
| [`113`](./113-kaje-architecture-2026-09-12.md) | Parent architecture 6:3:1; PEPE was the Scalp **target name**; ≤10× Scalp; `ga live` + session-ja + sleeve list. This note **opens** live instrument to any `LIVE_CLEAR` (PEPE preferred). Does **not** rewrite 6:3:1 / cascade / Monday 09:00. |
| [`114`](./114-scalp-multi-coin-watch-2026-09-12.md) | Multi-coin **watch** under one 10% bucket. DEMO_BLOCK meme screen on **demo** key. Catalogue CLEAR ≠ DEMO_BLOCK ≠ `LIVE_CLEAR` ≠ arm. |
| [`115`](./115-public-md-scalp-method.md) | Public-MD method. Method-only. DEMO_BLOCK full meme screen on demo OMS. Public MD ≠ DEMO_CLEAR ≠ `LIVE_CLEAR` ≠ arm. |
| [`116`](./116-kaje-capital-intent-2026-09-12.md) | Live-gate / capital parent: Core fill ~€144; Mid #71 ~€72 conditional / flat; Soft PASS ≠ Scalp-arm; scalper-first for **Scalp-arm only**. |
| [`117`](./117-public-md-scalp-first-score-ema1221-1h.md) / [`118`](./118-public-md-scalp-breakoutv1-1h.md) / [`119`](./119-public-md-scalp-rsi14-mr-1h.md) | Public-MD **scores** on PUMP / TRUMP / WIF. Soft PASS **N/A**. **≠** 121. **≠** PEPE re-score. **≠** arm. Do **not** transplant those tables. |
| [`107`](./107-eur200-capital-readiness-2026-09-12.md) | HALTED / tiny / leverage addendum / ~€240 figure. Unchanged except this overlay pointer. |
| [`108`](./108-dev-board-research-lock.md) | Research freeze (Mid #71 / S1 / Core CASH as *research*). Live Core fill is capital, not a CORE-R1 promote. |
| [`111`](./111-sl-fill-release-human-ping.md) / [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) | Ping + 3×SL → 28m apply **once** a Scalp system is armed. Not an arm. |
| [`105`](./105-portfolio-core-major.md) / [`106`](./106-research-governance-board.md) | STRATEGY GREEN ≠ PORTFOLIO GREEN. Soft PASS ≠ arm. |
| **121** (reserved) | 2020 majors family-pick backtest. Not scored here. |

---

## What this PR does / does not

**Does**

- Lock the 2026-09-12 Kaje + Risk **Scalp LIVE conditional gate** as **phase1/120**.
- Stamp Risk ACK: 2020 / **121** = backtest family-pick; first live uses 121 winner; 121 is **not** a forever POST veto.
- Stamp live instrument = any Ops **`LIVE_CLEAR`** coin; **PEPE preferred if it works**; else next alts.
- Stamp Ops **PEPE `LIVE_CLEAR_BOTH` already verified** (not an arm).
- Restate **session-ja + sleeve list** (and parent **`ga live`**) before POST.
- Restate caps: ≤10% Scalp (~€24 of ~€103 USDC residual stamp) · ≤10× iso · 5% kill · no martingale · journal POSTs if later armed.
- Pre-register ledger row `TL-120` (not a score).
- Index this note in [`README`](./README.md).
- Point [`113`](./113-kaje-architecture-2026-09-12.md) / [`114`](./114-scalp-multi-coin-watch-2026-09-12.md) / [`116`](./116-kaje-capital-intent-2026-09-12.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md) at this overlay.

**Does not**

- Change `config/default.yaml` or flip `pepe_enabled`.
- Place Scalp / Mid orders or write phase1/121 scores.
- Invent PnL, expectancy, a 121 winner, or a PEPE / alt re-score table.
- Invent a live order `instId` or treat DEMO_BLOCK as a live workaround.
- Describe Core as unfilled / parked.
- Arm Scalp from Soft PASS, from [`115`](./115-public-md-scalp-method.md), or from PEPE `LIVE_CLEAR_BOTH`.
- Split the 10% Scalp bucket per coin.
- Re-score R1–R7 / #71 / S1 / [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md).

---

## Honesty / invalidation

- Soft PASS / V2 PASS / DEV board / [`115`](./115-public-md-scalp-method.md) / [`117`](./117-public-md-scalp-first-score-ema1221-1h.md)–[`119`](./119-public-md-scalp-rsi14-mr-1h.md) / PEPE `LIVE_CLEAR_BOTH` **≠ Scalp-arm**.
- A later PR that POSTs first Scalp live **without** a locked 121 family (or an explicit later Kaje family name) **and** an instrument re-score **and** `session-ja` + sleeve list **and** `ga live` violates this gate / [`106`](./106-research-governance-board.md).
- A later PR that treats 121 as a **forever veto** of every future Scalp POST contradicts the Risk ACK (first-live family lock only).
- A later PR that transplants 2020 or PUMP/TRUMP/WIF numbers onto PEPE (or any alt) violates F2 / I4.
- A later PR that invents live from DEMO_BLOCK, or invents `LIVE_CLEAR` for an unstamped name, violates I5.
- A later PR that edits `config/default.yaml` or flips `pepe_enabled` for this lock contradicts I3.
- A later PR that invents MTM PnL on the Core fill or on the ~€24 / ~€103 residual stamp violates I4.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ Scalp-arm. `config/default.yaml` untouched.
