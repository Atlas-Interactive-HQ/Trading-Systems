# 109 — Three-month research program (Europe/Amsterdam) — 2026-09-12

**Stance:** Research calendar + quiet-ops lock. `not_a_forecast: true`. **Never places orders.**
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. **This PR does not arm Mid / Scalp / Core / HFT.**
**DEV board:** [`108`](./108-dev-board-research-lock.md) is already locked — Mid **#71** primary, Scalp **S1** provisional, Core **CASH**. This note does **not** rewrite that board.
**Capital:** [`107`](./107-eur200-capital-readiness-2026-09-12.md) addendum + [`108`](./108-dev-board-research-lock.md) — parked **~€240 USDC** (HOLD from live tests). Capital prep only; not sleeve arm.
**Governance:** PR **#89** ([`100`](./100-p4a-screening-p4b-7d.md)–[`106`](./106-research-governance-board.md)). Philosophy: PR **#89** / [`105`](./105-portfolio-core-major.md).
**Timezone:** **Europe/Amsterdam**. Lock date **2026-09-12**. Horizon **2026-09-12 → 2026-12-11** (three calendar months).

---

## Hard invariants (override later “just pick / just arm” briefs)

| Id | Lock |
|----|------|
| I1 | `not_a_forecast: true` on every artifact |
| I2 | **Soft PASS ≠ arm** — no live from Soft PASS / V2 PASS / DEV board |
| I3 | Live POSTs **HALTED**. Tiny ≤€20 until Kaje **`ga live €200`** **and** **session-ja** **and** sleeve list |
| I4 | Do **not** arm Mid / Scalp / Core / HFT from this program |
| I5 | `config/default.yaml` **untouched** |
| I6 | **No R1–R7 family grind** (no M2–M4, no S2/S3 RVOL, no C3 Donchian, no CORE-R1 promote) |
| I7 | P4a = **screening report only** — **no instrument pick** ([`100`](./100-p4a-screening-p4b-7d.md), [`108`](./108-dev-board-research-lock.md)) |
| I8 | Do **not** invent SHADOW start/end dates ([`101`](./101-shadow-contiguous-methodology.md)) |
| I9 | Do **not** invent capture rates, PnL, or deflated Sharpe |
| I10 | STRATEGY GREEN ≠ PORTFOLIO GREEN; **CASH is valid** ([`105`](./105-portfolio-core-major.md)) |

---

## Capital (parked — HOLD)

Kaje lock 2026-09-12: **~€240 USDC parked** from live tests. **HOLD. No orders.**

| Item | Lock |
|------|------|
| Parked | ~€240 USDC on venue — capital prep, **not** sleeve arm |
| Deposit | **Read-path only** (balances / ticker / open orders GET). Bots do **not** transfer / withdraw / deposit |
| Resting TP | **Leave** on the book ([`28`](./28-live20-resting-exits.md)). Do not cancel. Do not place new TP / protect-limit from this note |
| Sleeve split | [`107`](./107-eur200-capital-readiness-2026-09-12.md) ~€150 spot : ~€50 perp remains **policy-not-armed**. Do **not** invent a new €240 allocation |
| Core | **CASH** on the [`108`](./108-dev-board-research-lock.md) board (allocation 0) |
| Tiny | ≤€20 until **`ga live €200`** + session-ja + which sleeves |
| Sweeps | Propose only. Never auto |

Do not treat parked ~€240 as permission to POST. Soft PASS ≠ arm.

---

## Philosophy (PR #89 / #105)

| Statement | Meaning on this program |
|-----------|-------------------------|
| Strategy green | Locked card survived **contiguous SHADOW** + edge-vs-luck + stress. Still `not_a_forecast`. Still Soft PASS ≠ arm. |
| Portfolio green | The **book** has a validated reason to take risk in that sleeve. |
| No validated edge | Allocation **0**. The sleeve is **CASH**. **CASH is OK.** |

[`108`](./108-dev-board-research-lock.md) already applied this: Mid #71 and S1 are **DEV candidates**, not armed; Core is **CASH** even though C0 / CORE-R1 show large rise-panel terminal nets. Do not fill Core €140 because a sleeve number exists in [`38`](./38-eur200-three-stream-confirmation.md).

---

## DEV board this program implements (paper / system — not live-arm)

Cite [`108`](./108-dev-board-research-lock.md) / `atlas.paper.rise_panel.DEV_BOARD`. Do **not** contradict:

| Sleeve | Role | Implement (paper/system) | Live |
|--------|------|--------------------------|------|
| Mid | **primary** | `#71` `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40` | **HALTED** — no Mid-arm |
| Scalp | **provisional DEV** | **S1** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20` | **HALTED** — no Scalp-arm |
| Core | **CASH** | Observer / cash book only. C0 = reference. CORE-R1 **not promoted**. Donchian **stopped** | **HALTED** — no Core-arm |
| HFT | wait | P4a screen → P4b 7d → health → H1 signal → **markout** → only then economic paper PnL | **HALTED** — no HFT-arm; **no instrument pick** |

M1 remains robustness comparator only. SCALP-R2 remains eliminated. Scoreboard: [`110`](./110-paper-scoreboard-synthesis-2026-09-12.md).

---

## Cadence (locked order — do not reorder to chase a green cell)

```
P4a screening report (no pick)
  → P4b 7 full calendar days
    → SHADOW contiguous AFTER contamination audit
      → edge-vs-luck / stress  Mid #71 + S1
        → HFT only after P4b lock + markout
```

This is board **B → C → D → E** of [`106`](./106-research-governance-board.md). Step **F** (CORE-MAJOR) stays later. Do **not** invent P4a rates. Do **not** invent SHADOW dates. Do **not** pick an HFT name from 24h.

| Step | Doc | This program may | This program must not |
|------|-----|------------------|------------------------|
| **B — P4a** | [`100`](./100-p4a-screening-p4b-7d.md) | After 24h capture **ends**: screening report (instIds resolved? channels wrote? `METRIC_FIELDS` emit? dead-name **warnings**) | Lock instrument; start H1 economic PnL; invent rates; treat Friday→Saturday as the name |
| **B — P4b** | [`100`](./100-p4a-screening-p4b-7d.md) | Start / run **7 full UTC calendar days** same three X-Perps + four channels; score pooled + weekday/weekend + session slices | Reuse incomplete P4a as “7d”; pick from P4a favourite; default DOGE |
| **C — SHADOW** | [`101`](./101-shadow-contiguous-methodology.md) | Contamination audit of latest used timestamp for Mid #71 / S1 / Core families; lock start/end **after** audit in a follow-up note | Invent dates here; hand-pick rise/chop/down; another R1–R7 tip |
| **D — robustness** | [`103`](./103-edge-vs-luck-stress.md) | Walk frozen **#71** and **S1** **once** on the locked SHADOW; then placebo / block-bootstrap + stress matrix | Score luck on R1–R7; grind S1 RVOL; treat EDGE CONFIRMED as arm |
| **E — HFT** | [`96`](./96-hft-h1-ensemble-lock.md) [`104`](./104-h1-markout-event-time.md) | Only after **P4b instrument lock** + P1 health + H1 signal: fill-conditioned markout; economic paper PnL last | Economic HFT PnL before markout; rewrite 1s H1; pick from P4a |

If P4a is still running: **wait for the capture to end**, then write the screening report. [`108`](./108-dev-board-research-lock.md) already forbids starting P4a metrics before 24h ends.

If the contamination audit finds **no** clean historical block: **forward paper IS the SHADOW** ([`101`](./101-shadow-contiguous-methodology.md)). Do not stitch leftovers.

---

## Three-month board (Europe/Amsterdam)

Horizon is **calendar**, not a claim that each step finishes inside its month. Slip is documented in phase1 + `research/trial_ledger.jsonl`. Dates below are **program months**, not SHADOW intervals.

| Month | Amsterdam dates | Intended work | Forbidden |
|-------|-----------------|---------------|-----------|
| **M1** | 2026-09-12 → 2026-10-11 | Quiet HOLD. Deposit **read-path**. Resting TP **leave**. P4a **screening report** when 24h ends (**no pick**). If pipeline accepted, **start P4b 7d**. Paper/system implement [`108`](./108-dev-board-research-lock.md) board (observers / journals — **not** live-arm). Scoreboard [`110`](./110-paper-scoreboard-synthesis-2026-09-12.md) is the honesty cite. | Live POST; arm any sleeve; invent P4a numbers; pick HFT name; R1–R7 grind |
| **M2** | 2026-10-12 → 2026-11-11 | Finish P4b or **fail-closed** (no instrument). Contamination audit ([`101`](./101-shadow-contiguous-methodology.md)). If a clean block exists, **lock SHADOW dates in a follow-up note before any walk**, then contiguous #71 + S1 once. | Invent SHADOW dates in this file; hand-picked S/F/D; luck/stress before SHADOW lock |
| **M3** | 2026-11-12 → 2026-12-11 | Edge-vs-luck + stress on **#71** and **S1** **after** SHADOW ([`103`](./103-edge-vs-luck-stress.md)). HFT **only** if P4b locked **and** markout gate ([`104`](./104-h1-markout-event-time.md)). Core stays **CASH** until portfolio green. | Soft PASS → live; CORE-R1 promote; CORE-MAJOR score; fill Core because it looks lonely |

**Still HALTED** at the end of M3 unless Kaje says **`ga live €200`** + **session-ja** + sleeve list **and** the research gates that [`106`](./106-research-governance-board.md) / [`107`](./107-eur200-capital-readiness-2026-09-12.md) require.

---

## Quiet ops

Ping Kaje **only** on blockers that need a human decision. Everything else is written into **phase1** + **`research/trial_ledger.jsonl`**.

| Ping Kaje | Do **not** ping (document instead) |
|-----------|--------------------------------------|
| `ga live €200` / session-ja / which sleeves to arm | Routine paper walks, journals, ledger appends |
| Deposit / transfer / withdraw / sweep execute | Read-path balance / ticker / pending GET |
| Cancel or move a **resting TP** (default = **leave**) | P4a screening report with `selected=None` |
| Ambiguous contamination audit that needs a SHADOW date **lock** | Audit progress while dates remain TODO |
| P4b fail-closed / instrument-lock confirmation (**still ≠ HFT-arm**) | Invented “looks liquid” chat |
| Auth / IP / venue block that stops **read-path** | Soft PASS / V2 PASS treated as news |

No R1–R7 family grind in Slack/chat as a substitute for a phase1 note.

---

## Explicit non-goals

- **No R1–R7 family grind.**
- **No live from Soft PASS.** DEV board ≠ arm.
- No Mid / Scalp / Core / HFT arm from this PR or from M1–M3 paper work.
- No invented SHADOW dates. No HFT instrument pick.
- No rewrite of [`108`](./108-dev-board-research-lock.md) numbers or roles.
- No `config/default.yaml` edit.
- Not a forecast of the next three months of PnL.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.
