# 111 — SL fill / SL release human ping (Core / Mid / Scalp) — 2026-09-12

**Stance:** Ops alert-prep lock. `not_a_forecast: true`. **Never places orders.**
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. **This note does not arm.**
**Capital:** parked **~€240** HOLD ([`107`](./107-eur200-capital-readiness-2026-09-12.md) addendum / [`109`](./109-three-month-program-2026-09-12.md)). Capital prep only; not sleeve arm.
**DEV board:** [`108`](./108-dev-board-research-lock.md) — Mid **#71** primary, Scalp **S1** provisional, Core **CASH**. Do **not** contradict that board.

**Scalp cooldown (already locked — do not re-lock here):** [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) — Scalp S1 **3× consecutive SL → 28m delayed market entry**. This note is **only** the human-ping path.

**Ledger:** `TL-111` in `research/trial_ledger.jsonl` — **`pre_registered: true`**. No score. No invented metrics / PnL.

Code stub (prep only, no live): `atlas.ops.sl_ping`.

---

## Hard invariants

| Id | Lock |
|----|------|
| I1 | `not_a_forecast: true` · `place_orders: false` |
| I2 | **Soft PASS ≠ arm.** A ping is **not** a live-arm. |
| I3 | No live POSTs until Kaje **`ga live €200`** **and** **session-ja** **and** sleeve list ([`107`](./107-eur200-capital-readiness-2026-09-12.md), [`109`](./109-three-month-program-2026-09-12.md)) |
| I4 | `config/default.yaml` **untouched** |
| I5 | Do **not** re-lock or rewrite [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) |
| I6 | Do **not** invent backtest results, expectancy, or panel € |

`place_orders: false`. HALTED.

---

## Human ping on SL / release

**When any of Core / Mid / Scalp streams (once armed)** experiences either:

1. **stop-loss FILL**, or
2. **stop RELEASE** (cancel / close of a resting SL)

→ **ping Kaje for joint review.**

Prep the Ops alert path only. The stub records the event and the would-ping payload. It does **not** send a live order, cancel a TP, or arm a sleeve.

| Item | Lock |
|------|------|
| Streams | **Core**, **Mid**, **Scalp** only (not HFT) |
| Armed? | Ping **fires only once that stream is armed**. Today: **none armed**. Path is **prep**. |
| Events | `stop_loss_fill` · `stop_release` |
| Audience | Kaje — joint review (quiet-ops exception; see [`109`](./109-three-month-program-2026-09-12.md)) |
| Send | **Prep only** (`send=false`). No auto Slack/API POST from this lock. |
| Arm | **Forbidden** from a ping. Still needs **`ga live €200`** + **session-ja** + sleeve list. |
| Resting TP | Default **leave** ([`28`](./28-live20-resting-exits.md), [`109`](./109-three-month-program-2026-09-12.md)). A **stop release** ping is review, not permission to cancel TP. |

Soft PASS / V2 PASS / DEV board ≠ armed. A paper-engine stop in a journal is **not** this ping until a stream is live-armed.

A Scalp SL **fill** may also increment the consecutive-SL counter under [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md). That cooldown is a **separate** lock. This ping does **not** delay or size the next Scalp entry.

---

## Stub (no live)

| Module | Role |
|--------|------|
| `atlas.ops.sl_ping` | Classify Core/Mid/Scalp SL fill / SL release; `prep_ops_alert` (`send=false`, `place_orders=false`) |

Unit tests only. No venue POST. No `allow_trade`. No invented journal PnL.

---

## Ledger / multiplicity

Append-only row `TL-111` (`pre_registered: true`, `post_hoc: false`). Parent `TL-109`. Family `ops`. `pass_fail: N/A_ops_ping_lock_not_a_score`.

Starter `global_trial_count` becomes **12**. That starter N is still **not** a complete census of phase1/16–99 ([`102`](./102-trial-ledger.md)). Do not invent Deflated Sharpe / PBO.

---

## Honesty / invalidation

- If a later PR arms Mid/Scalp/Core from Soft PASS or from this stub, it violates [`106`](./106-research-governance-board.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md) / [`109`](./109-three-month-program-2026-09-12.md).
- If a later PR treats a ping as permission to cancel a resting TP, it contradicts [`28`](./28-live20-resting-exits.md) / [`109`](./109-three-month-program-2026-09-12.md).
- If a later PR re-locks Scalp 3×SL → 28m here, it contradicts [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md).
- If a later PR edits `config/default.yaml` for this lock, it contradicts I4.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.
