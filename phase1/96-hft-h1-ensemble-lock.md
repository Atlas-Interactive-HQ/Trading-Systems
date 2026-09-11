# 96 — H1 ensemble lock (P5, design only)

**Stance:** Research / design lock. `not_a_forecast: true`. **NO HFT PnL in this note.**
**Config:** `config/default.yaml` **untouched**.
**Live:** HALTED.
**Depends on:** P1 health semantics ([`92`](./92-hft-staleness-semantics.md)) + P4 liquidity instrument lock ([`95`](./95-hft-liquidity-gate-plan.md)) + multi-day Layer B. **Not ready to score.**

---

## Locked score (no weight optimize)

```
micro_score = (z_vamp + z_microprice + z_ofi) / 3
```

Any missing / INVALID z → `micro_score = None` → no trade. Do **not** search weights.

EMA12/21 on midpoint = **regime, not alpha** (same as H0 / [`76`](./76-scalp-hft-v1-rule-card.md)).

---

## Side rule (LOCKED)

Uses P1 trading health (not `carried_forward` alone) and the existing 2-of-3 confirmation.

```
LONG:  healthy
       AND EMA12 > EMA21
       AND micro_score >= +1.0
       AND 2-of-3 confirmation

SHORT: healthy
       AND EMA12 < EMA21
       AND micro_score <= -1.0
       AND 2-of-3 confirmation
```

One position. No pyramid / martingale / average-down. R1–R7 tuning forbidden.

Code: `atlas.scalp_hft.h1_ensemble` (`H1_LOCK_ID = hft_h1_equal_weight_ensemble_v1`).

---

## Signal-only study first

After health + liquidity + multi-day Layer B exist, compare **future midpoint returns** at **1s / 3s / 5s / 10s** for:

1. VAMP-only
2. microprice-only
3. OFI-only
4. equal-weight `micro_score`
5. EMA regime + equal-weight

This is a **signal** study. A positive mean mid-return is **not** a profitable strategy (fees, queue, latency, adverse selection are absent).

---

## Economic PnL — later, and labeled

Only after the signal study is **frozen** may a latency / queue / fee simulator attach economic PnL. Do **not** headline a green signal as a profitable strategy. Soft PASS N/A until that sim exists.

---

## Honesty / invalidation

- Do not score H1 in this PR.
- Do not optimize the three weights after seeing horizon returns.
- Do not skip the liquidity gate and default to DOGE.
- Fee hurdle from [`75`](./75-scalp-hft-v1-design.md) remains the primary economic invalidation.

`not_a_forecast: true`. `place_orders: false`.
