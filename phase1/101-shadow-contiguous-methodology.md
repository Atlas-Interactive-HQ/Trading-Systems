# 101 — SHADOW methodology (contiguous chronological)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. R1–R7 DEV/eliminate-only **paused** for new tip scores.
**Amends:** [`84`](./84-atlas-trading-vnext.md) §4.2 (hand-picked S/F/D as **selection**). Distinct from Phase B shadow-replay [`11`](./11-shadow-replay.md).
**Board:** step **C** of [`106`](./106-research-governance-board.md).

**Do not invent SHADOW start/end dates in this PR.** Leave TODO until the contamination audit lands.

---

## What SHADOW is

SHADOW is **one contiguous unseen historical interval** that begins at the first timestamp that has **never** been used for the families under test, after a contamination audit.

| Property | Lock |
|----------|------|
| Shape | One interval. Chronological. Contiguous. |
| Selection | Audit-driven (latest used timestamp → next unused timestamp). |
| Labels | `bull` / `chop` / `bear` may be attached **after** the interval is locked, for analysis only. |
| Fail closed | If no clean historical block remains → **forward paper IS the SHADOW**. Do not invent windows. |

SHADOW is the next score surface for frozen Mid **#71** and provisional Scalp **S1** ([`93`](./93-frozen-mid-scalp-candidates.md)). It is not a new strategy.

---

## What SHADOW is not

| Rejected as the **data-selection** rule | Why |
|-----------------------------------------|-----|
| Hand-picked rise / chop / down windows (S1–S3 / F1–F3 / D1–D3 in [`84`](./84-atlas-trading-vnext.md) §4.2) | Regime-shopping the holdout. That is post-hoc window selection even if dates are “TODO”. |
| Another R1–R7 tip, a reshuffled rise panel, or dropping the ugly window | R1–R7 remain DEV/eliminate-only and are **paused** for new family tips. |
| Named-window shopping (`2022-bear` because we want a bear SHADOW, etc.) | Labels after selection, never to choose which data enters. |
| Phase B `run_shadow_replay.py` journals ([`11`](./11-shadow-replay.md)) | Different object: would-place vs blocked on already-seen replay windows. |

[`84`](./84-atlas-trading-vnext.md) §4.2 is **amended**: those S/F/D ids are not how SHADOW data is chosen. If someone later wants regime **labels** on the locked contiguous interval, that is analysis, not selection.

Code: `atlas.research.shadow_contiguous.refuse_hand_picked_windows`.

---

## Contamination audit (required before lock)

Audit the **latest timestamp ever used** for:

1. **Mid #71 family** — `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40` and its robustness comparator M1 ([`72`](./72-mid-long-strengthen.md), [`86`](./86-rise-panel-mid-m1-adx-4h.md)).
2. **Scalp #83 / S1 family** — Dual Thrust N20 k=0.5 and RVOL>1 ([`83`](./83-rise-panel-scalp-dual-thrust-1h.md), [`87`](./87-rise-panel-scalp-s1-rvol-1h.md)).
3. **Core families** — C0 EMA12/30, C1/C2 Donchian, CORE-R1 ATR trail, and earlier named-window EMA/Donchian walks that used the same Core research MD.

The first truly untouched timestamp **after** that latest used timestamp is the earliest legal SHADOW start. Warmup bars that look into the contaminated side are still contamination — start the scored interval after warmup that itself sits on unseen data, or treat the warmup as part of the audit.

Known sources that the audit **must** include (dates already locked in-repo; **not** a SHADOW interval):

| Source | Span (UTC, from code/docs) | Families |
|--------|----------------------------|----------|
| `rise_panel_v1` R1–R7 | 2020-10-01 → 2024-11-04 (seven locked windows) | Mid #71, S1, Core scores |
| Named `2020-09` / `2023-09` multi-month | 2020-09-01→2021-03-31 / 2023-09-01→2024-03-31 | Early Phase D / EMA Core |
| Named `2022-bear` / `2023-chop` | 2022-01-01→2022-12-31 / 2023-01-01→2023-08-31 | EMA OOS ([`20`](./20-ema-oos-stress.md)) |
| Named `2026-funding` | 2026-06-04→2026-09-02 | Include **if** any Mid/Scalp/Core walk used it |
| Forward journals / Layer B / liqgate | post-2026-09 local captures | Include if those families trained or scored on them |

The audit may find a later “last used” timestamp than R7. **Do not guess it here.**

Template: `atlas.research.shadow_contiguous.contamination_audit_template`.  
`SHADOW_START_UTC` / `SHADOW_END_UTC` are **`None`** (`TODO_LOCK_AFTER_AUDIT`).

---

## Fail closed

| Situation | Action |
|-----------|--------|
| Audit not done | No SHADOW score. No invented dates. |
| Clean historical block exists | Lock start/end in a follow-up phase1 note **before** any SHADOW walk. |
| No clean historical block remains | **Forward paper IS the SHADOW.** Observer only. `place_orders: false`. Do not stitch non-contiguous leftovers. |
| Temptation to pick a pretty bear week | Reject. That is hand-picked selection. |

`lock_shadow_interval(start, end)` in this PR refuses dates on purpose.

---

## Honesty / invalidation

- Next Mid score = this SHADOW, not M2–M4 on R1–R7 ([`93`](./93-frozen-mid-scalp-candidates.md)).
- Edge-vs-luck / stress ([`103`](./103-edge-vs-luck-stress.md)) run **after** SHADOW exists, not before.
- Soft PASS on R1–R7 ≠ SHADOW pass ≠ arm.
- `not_a_forecast: true`. `place_orders: false`.
