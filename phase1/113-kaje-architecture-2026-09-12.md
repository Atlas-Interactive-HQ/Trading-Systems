# 113 — Kaje architecture lock (2026-09-12)

**Stance:** Capital / sleeve architecture lock. `not_a_forecast: true`. **Never places orders.**
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. **This note does not arm.**
**No auto-POST** until Kaje **`ga live`** **and** **session-ja** **and** sleeve list ([`107`](./107-eur200-capital-readiness-2026-09-12.md), [`109`](./109-three-month-program-2026-09-12.md)).
**Ledger:** `TL-113` in `research/trial_ledger.jsonl` — **`pre_registered: true`**. No score. No invented metrics / PnL / expectancy.

Code card (lock only, no live): `atlas.research.kaje_arch`.

---

## Why this lock

Kaje locked the **own-capital sleeve architecture** on **2026-09-12** (Europe/Amsterdam). This note freezes that board so later work cannot quietly keep Core as research-CASH, keep Scalp as provisional DOGE S1, reuse the old **7:2:1** ([`34`](./34-three-tier-cascade.md)) or **3:1** spot:perp ([`107`](./107-eur200-capital-readiness-2026-09-12.md)) splits, or treat Soft PASS as permission to POST.

This is **policy**, not a scored system and not a live-arm.

**Soft PASS ≠ arm. HALTED. not_a_forecast.**

---

## Hard invariants

| Id | Lock |
|----|------|
| I1 | `not_a_forecast: true` · `place_orders: false` |
| I2 | **Soft PASS ≠ arm.** A locked board is **not** a live-arm. |
| I3 | No live POSTs until Kaje **`ga live`** **and** **session-ja** **and** sleeve list |
| I4 | `config/default.yaml` **untouched** (runtime still default ≤2× / paper hard 5×) |
| I5 | Do **not** invent backtest results, expectancy, panel €, or PEPE `instId` |
| I6 | Sweeps / transfers / withdraws **never auto** — Kaje explicit yes ([`107`](./107-eur200-capital-readiness-2026-09-12.md)) |
| I7 | Martingale / grid / average-down **forbidden** |
| I8 | PEPE Scalp: **fail-closed** until OKX EEA listing is re-verified; no score / no arm if missing |

`place_orders: false`. HALTED.

---

## Locked board (2026-09-12)

| Sleeve | Asset | Role | Leverage | Notes |
|--------|-------|------|----------|-------|
| **Core / long** | **BTC** | 3-month **spot hold**; add periodically | **None** on this hold sleeve | Capital policy, **not** a promoted Core strategy. Does **not** promote CORE-R1 / Donchian. |
| **Mid** | **DOGE** | Primary research Mid **#71** family | **≤5× isolated** (Kaje clear 2026-09-12) | Still DEV paper — not SHADOW / not edge-vs-luck → **no Mid-arm** |
| **Scalp** | **PEPE** | Compounding **advised** (intent) | **≤10× isolated** (Kaje clear 2026-09-12; see [`107`](./107-eur200-capital-readiness-2026-09-12.md) addendum) | **New Scalp target.** PEPE was previously **deferred**. No PEPE system exists yet. |

### Core — BTC spot hold

- **3-month** spot hold sleeve (aligns with the [`109`](./109-three-month-program-2026-09-12.md) horizon as calendar, not as a PnL claim).
- **Add periodically** (human / weekly review). **Not** an auto-buy bot. **Not** a scored EMA/Donchian Core edge.
- **No leverage** on this hold sleeve. Isolated / cross / X-Perp leverage is **out of scope** for Core hold.
- Updates the [`108`](./108-dev-board-research-lock.md) **Core CASH** *policy* → **BTC hold**. CASH remains a **valid** unvalidated-strategy allocation under [`105`](./105-portfolio-core-major.md); this lock chooses BTC spot hold as the Core **capital** sleeve, not a GREEN Core system.

### Mid — DOGE #71 family

- Primary research Mid remains **#71** BreakoutV1 + EMA12/21 **4H** ([`72`](./72-mid-long-strengthen.md), [`93`](./93-frozen-mid-scalp-candidates.md), [`108`](./108-dev-board-research-lock.md)).
- Leverage ceiling **≤5× isolated** is a **Kaje clear** dated **2026-09-12**. Ceiling ≠ venue-verified ≤5× ≠ arm.
- Soft PASS / V2 PASS on #71 **≠ arm**.

### Scalp — PEPE (fail-closed listing)

PEPE was previously **deferred** (demo / compliance / not routed): [`08`](./08-self-learning-paper-path.md), [`09`](./09-handoff-grok-cli.md), Phase 1.7 DOGE loop, `pepe_enabled: false` in `config/default.yaml` (**do not flip that flag in this PR**).

| Rule | Lock |
|------|------|
| Target | **PEPE** is the new Scalp **target** (S1 DOGE was **provisional** on [`108`](./108-dev-board-research-lock.md)) |
| Compounding | **Advised** as sleeve intent (winnings stay in Scalp until upward cascade). Not a size-up / martingale rule. |
| Listing | **Verify OKX EEA listing** (public `instruments` catalogue of record, [`07`](./07-venue-preflight-notes.md)) **before any score or arm** |
| `instId` | **Do not invent.** If spot and/or isolated perp `instId` cannot be verified for this account/product gate → **FAIL-CLOSED**. No score. No arm. |
| Historical cite only | [`07`](./07-venue-preflight-notes.md) saw `PEPE-USD_UM_XPERP-310404` on a **2026-09-01** public FUTURES xperp probe. That is **not** an order `instId`, **not** a re-verify, and **not** permission to score. DOGE already taught MD `…310404` ≠ order `…310516`. |
| System | **No PEPE Scalp system exists yet.** Do not attach S1 Dual Thrust / RVOL numbers to PEPE. Do not invent expectancy. |

---

## Ratio, cascade, weekly

| Item | Lock |
|------|------|
| **Capital ratio** | **6 : 3 : 1** Core : Mid : Scalp |
| Supersedes (as current policy) | [`34`](./34-three-tier-cascade.md) **7:2:1** and [`107`](./107-eur200-capital-readiness-2026-09-12.md) **3:1** spot:perp — those notes stay **historical** |
| Euro split | **Propose only.** Do **not** invent a parked-€240 allocation table. Parked ~€240 remains HOLD ([`107`](./107-eur200-capital-readiness-2026-09-12.md) addendum / [`109`](./109-three-month-program-2026-09-12.md)) |
| **Cascade** | All **winnings** offload **upward only**: **Scalp → Mid → BTC**. One-way. No downward refill. |
| **Weekly review** | Repo had **no** locked holdings-review weekday. **Propose / lock:** **Monday 09:00 Europe/Amsterdam** — check holdings / positioning, review, **propose** rebalance toward **6:3:1** |
| Sweeps / transfers | Still need **Kaje explicit yes**. Weekly review ≠ auto-sweep ≠ auto-POST |

Monday 09:00 Europe/Amsterdam is a **review clock**, not a cron that places orders.

---

## Cross-refs (do not re-lock)

| Doc | How this lock uses it |
|-----|------------------------|
| [`107`](./107-eur200-capital-readiness-2026-09-12.md) | Capital readiness / HALTED / tiny ≤€20 until `ga live` + session-ja + sleeves. **Leverage addendum** (same date): Mid **≤5×** isolated, Scalp **≤10×** isolated — **docs only**. Ceiling ≠ arm. |
| [`108`](./108-dev-board-research-lock.md) | Research board addendum: Core **CASH → BTC hold policy**; Scalp **S1 DOGE was provisional — PEPE is the new Scalp target**. Measured #71 / S1 / C0 tables are **citations**, not re-scores. |
| [`111`](./111-sl-fill-release-human-ping.md) | SL fill / SL release → ping Kaje still applies to Core / Mid / Scalp **once that stream is armed**. A ping is **not** an arm. Prep only today. |
| [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) | **3× consecutive SL → 28m delayed market entry** still applies to the **Scalp** sleeve **once a PEPE system exists**. Do not invent PEPE params here. Not martingale. Paper-first. |
| [`105`](./105-portfolio-core-major.md) / [`106`](./106-research-governance-board.md) | STRATEGY GREEN ≠ PORTFOLIO GREEN. Soft PASS ≠ arm. BTC hold ≠ CORE-MAJOR-v1 score. |
| [`109`](./109-three-month-program-2026-09-12.md) | 3-month quiet-ops program unchanged. This lock does not invent SHADOW dates or pick HFT. |
| [`114`](./114-scalp-multi-coin-watch-2026-09-12.md) | Overlay (same date): Scalp may **watch multiple coins** under the **one** 10% bucket. Ops **DEMO_BLOCK** on demo key for PEPE/PUMP/TRUMP/WIF/SHIB/BONK/BOME/FLOKI. Catalogue CLEAR ≠ DEMO_BLOCK ≠ Soft PASS ≠ arm. Does **not** re-lock this architecture. |
| [`115`](./115-public-md-scalp-method.md) | Public-MD Scalp **method** (PR #98). Method-only. Soft PASS ≠ Scalp-arm. DEMO_BLOCK full meme screen on demo OMS. |
| [`116`](./116-kaje-capital-intent-2026-09-12.md) | Overlay (same date): live Core BTC fill ~€144 @ 77304.3 (`ordId 3915002084440100864`); Mid #71 ~€72 conditional / flat; Scalp Soft PASS ≠ arm; scalper-first for **Scalp-arm only**. Does **not** re-lock this architecture. |
| [`120`](./120-kaje-risk-scalp-live-gate-2026-09-12.md) | Overlay (same date): Scalp LIVE conditional gate (Risk ACK). 2020/121 backtest family-pick; any `LIVE_CLEAR` (PEPE preferred); PEPE `LIVE_CLEAR_BOTH` ≠ arm. Does **not** re-lock this architecture. |

---

## Leverage (policy clear — not runtime, not arm)

Kaje clear **2026-09-12** (documented on [`107`](./107-eur200-capital-readiness-2026-09-12.md) addendum + this note):

| Sleeve | Ceiling | Isolated | Meaning |
|--------|---------|:--------:|---------|
| Core BTC hold | **1× / no lev** | n/a (spot hold) | No leverage on the hold sleeve |
| Mid DOGE | **≤5×** | yes | Ceiling only |
| Scalp PEPE | **≤10×** | yes | Ceiling only; still must match venue / retail / account limits ([`07`](./07-venue-preflight-notes.md), [`75`](./75-scalp-hft-v1-design.md)) |

If max allowed leverage **cannot be demonstrated** for the instrument / size / tier / account: **NO TRADE**. Do not guess. Do not copy API `lever` as retail truth.

`config/default.yaml` stays at pack defaults (`leverage_default: 2.0`, `leverage_hard_cap: 5.0`). This PR does **not** raise runtime caps.

---

## What this PR does / does not

**Does**

- Lock the 2026-09-12 Kaje architecture as **phase1/113**.
- Point [`107`](./107-eur200-capital-readiness-2026-09-12.md) / [`108`](./108-dev-board-research-lock.md) at the overlay (docs).
- Pre-register ledger row `TL-113` (not a score).
- Freeze a read-only card in `atlas.research.kaje_arch`.

**Does not**

- Change `config/default.yaml`.
- Place orders / arm live / invent SHADOW dates.
- Invent PnL, expectancy, or a PEPE `instId`.
- Score or re-score R1–R7, #71, S1, or PEPE.
- Flip `pepe_enabled`.
- Execute weekly sweeps or BTC adds.
- Promote CORE-R1 or treat BTC hold as CORE-MAJOR-v1.

---

## Honesty / invalidation

- Soft PASS / V2 PASS / DEV board / this architecture **≠ arm**.
- A PEPE name on a Learn page or a 2026-09-01 public catalogue row **≠** verified tradable `instId` for this account **≠** score **≠** arm.
- If a later PR POSTs without `ga live` + session-ja + sleeve list, it violates [`106`](./106-research-governance-board.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md).
- If a later PR invents PEPE expectancy or an `instId` that was not re-verified, it violates I5 / I8.
- If a later PR edits `config/default.yaml` for this lock, it contradicts I4.
- If a later PR treats Monday 09:00 as auto-sweep / auto-POST, it contradicts I6.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.

---

## Overlay — multi-coin Scalp watch ([`114`](./114-scalp-multi-coin-watch-2026-09-12.md))

Kaje overlay **2026-09-12**: Scalp may **watch multiple coins** under the **one** Scalp **10%** bucket (the **1** in **6 : 3 : 1**). PEPE remains the architecture target **name**. Ops stamp on the demo key: **PEPE / PUMP / TRUMP / WIF / SHIB / BONK / BOME / FLOKI = DEMO_BLOCK**. Catalogue CLEAR ≠ DEMO_BLOCK ≠ Soft PASS ≠ arm. **No invented expectancy / order `instId`.** See [`114`](./114-scalp-multi-coin-watch-2026-09-12.md). This architecture lock is **unchanged**.

## Overlay — capital / intent ([`116`](./116-kaje-capital-intent-2026-09-12.md))

Kaje overlay **2026-09-12**: book **~€240** **supersedes €200** as the later-arm **budget figure**. **6 : 3 : 1** remains. **Live:** Core BTC spot **already filled** ~€144 @ 77304.3 (`ordId 3915002084440100864`) — Core exception **executed**; do **not** call Core parked. Mid DOGE ~€72 **conditional** on #71, **currently flat**. Scalp: **Soft PASS ≠ Scalp-arm**; method [`115`](./115-public-md-scalp-method.md). **Scalper-first applies to Scalp-arm only.** DEMO_BLOCK = full meme screen on demo OMS. See [`116`](./116-kaje-capital-intent-2026-09-12.md). This architecture lock is **unchanged**.

## Overlay — Scalp LIVE conditional gate ([`120`](./120-kaje-risk-scalp-live-gate-2026-09-12.md))

Kaje + Risk ACK **2026-09-12**: first Scalp LIVE POST is **conditional**. **2020 BTC/ETH/DOGE = BACKTEST / research only** (reserved **phase1/121**) — pick the Scalp family; **not** a forever POST veto; **first** live still uses the 121 winner as the locked family. Live instrument = **any Ops `LIVE_CLEAR` coin**; **PEPE preferred if it works**; else next alts. Ops: **PEPE `LIVE_CLEAR_BOTH` already verified** — **≠ arm**. Still need **`session-ja` + sleeve list** (parent **`ga live`** not dropped). Soft PASS ≠ arm · Scalp ≤10% · ≤10× iso · DEMO_BLOCK ≠ invent live. See [`120`](./120-kaje-risk-scalp-live-gate-2026-09-12.md). This architecture lock is **unchanged**.
