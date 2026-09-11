# 106 — Research-governance board (execution order lock)

**Stance:** Governance lock. `not_a_forecast: true`. Never places orders.
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm.
**This PR:** step **A** only. Registers B–F. Does **not** reveal P4a metrics, select an HFT instrument, score strategies, or invent SHADOW dates.

---

## Hard invariants

These override any later brief that asks to “just pick DOGE”, “use the 24h winner”, “score M2 on R1–R7”, or “hyperopt the weights”:

| Id | Invariant |
|----|-----------|
| I1 | `not_a_forecast: true` on every artifact |
| I2 | **Soft PASS ≠ arm** |
| I3 | Live **≤€20 HALTED** |
| I4 | R1–R7 = DEV/eliminate-only and **paused** for new family tips |
| I5 | **No post-hoc winners** |
| I6 | **No hyperopt** |
| I7 | `config/default.yaml` **untouched** |
| I8 | Do **not** invent capture numbers |
| I9 | Do **not** select an HFT instrument from P4a |
| I10 | Do **not** score Mid #71 / S1 / H1 / CORE-MAJOR in this governance PR |

Code: `atlas.research.governance.HARD_INVARIANTS` / `board_card`.

---

## Execution order (locked)

```
A  governance doctrine          ← this pack (100–106 + stubs)
B  P4a screening / P4b 7d       ← 100; 24h is not a lock
C  SHADOW contiguous            ← 101; after contamination audit
D  robustness #71 / S1          ← 103; after SHADOW
E  HFT liq → signal → markout → PnL   ← 100 then 96 then 104
F  CORE-MAJOR only afterwards   ← 105
```

| Step | Doc | May do now | Must not do now |
|------|-----|------------|-----------------|
| **A** | this note + [`102`](./102-trial-ledger.md) | Lock doctrine, ledger schema | Score, pick names, invent dates |
| **B** | [`100`](./100-p4a-screening-p4b-7d.md) (amends [`95`](./95-hft-liquidity-gate-plan.md)) | Finish P4a as **screening**; start P4b 7d | Lock instrument from 24h; invent rates |
| **C** | [`101`](./101-shadow-contiguous-methodology.md) | Run contamination audit | Hand-pick rise/chop/down; invent SHADOW dates |
| **D** | [`103`](./103-edge-vs-luck-stress.md) | — | Placebo/stress before SHADOW; grind S1 |
| **E** | [`96`](./96-hft-h1-ensemble-lock.md) + [`104`](./104-h1-markout-event-time.md) | — | Economic HFT PnL before markout; rewrite 1s H1 |
| **F** | [`105`](./105-portfolio-core-major.md) | CASH is valid | Score CORE-MAJOR; R1–R7 coin-pick |

Do not reorder to chase a green cell. Do not run F because Core looks lonely. Do not run E economic PnL because a signal mean was positive.

---

## Pack index

| Doc | Title |
|-----|-------|
| [`100`](./100-p4a-screening-p4b-7d.md) | P4a screening / P4b 7d liquidity amendment |
| [`101`](./101-shadow-contiguous-methodology.md) | Contiguous SHADOW; reject hand-picked S/F/D selection |
| [`102`](./102-trial-ledger.md) | Trial ledger + multiplicity (DSR/PBO conceptual) |
| [`103`](./103-edge-vs-luck-stress.md) | Placebo / stress registered, not scored |
| [`104`](./104-h1-markout-event-time.md) | Markout + H1a event-time; no 1s H1 rewrite |
| [`105`](./105-portfolio-core-major.md) | STRATEGY ≠ PORTFOLIO; CORE-MAJOR later |
| [`106`](./106-research-governance-board.md) | This board |

Stubs: `src/atlas/research/*`, `src/atlas/scalp_hft/liquidity_gate.py` (P4a/P4b), `research/trial_ledger.jsonl`.

---

## Honesty / invalidation

If a later PR locks an HFT name from P4a, scores #71 on a hand-picked bear week, or arms from Soft PASS, it **violates this board** even if the code compiles.

`not_a_forecast: true`. `place_orders: false`.
