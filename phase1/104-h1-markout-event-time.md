# 104 — H1 markout + event-time ablation (registered)

**Stance:** Research / design lock. `not_a_forecast: true`. **NO HFT PnL in this note.**
**Config:** `config/default.yaml` **untouched**.
**Live:** HALTED. Soft PASS N/A until the economic sim exists.
**Depends on:** P4b instrument lock ([`100`](./100-p4a-screening-p4b-7d.md)) + P1 health ([`92`](./92-hft-staleness-semantics.md)) + H1 signal study ([`96`](./96-hft-h1-ensemble-lock.md)).
**Board:** step **E** of [`106`](./106-research-governance-board.md) — after liquidity, after signal, **before** economic paper PnL.

Do **not** rewrite the locked **1s H1** clock ([`96`](./96-hft-h1-ensemble-lock.md) `HORIZONS_S = 1/3/5/10s`).

---

## Gate (hard)

```
signal green  →  markout green  →  queue / latency  →  economic paper PnL
```

A green H1 **signal** study (future midpoint return at 1s/3s/5s/10s) is **not** a profitable strategy. Fees, queue, latency, and adverse selection are absent. Economic paper PnL is forbidden until markout is green **and** a queue/latency sim exists.

Code: `atlas.research.h1_markout.economic_pnl_allowed`.

---

## H1-MARKOUT (fill-conditioned)

**When:** after the H1 signal study is frozen; before economic PnL.  
**Id:** `hft_h1_markout_fill_conditioned_v1`.  
**Conditioning:** **fills**, not every signal. Maker **buys** and maker **sells** separately.

Horizons (ms after fill):

`100, 250, 500, 1000, 3000, 5000, 10000`

Markout = signed change in mid (or microprice, labeled) from fill to horizon, in bps, **after** the maker fee assumption from [`75`](./75-scalp-hft-v1-design.md). Report buy and sell separately. Do not average away a one-sided disaster.

**Markout green (registered, not scored here):** both sides have mean markout that is not fee-eaten at the horizons the signal study claimed. Exact numeric hurdle is locked in the scoring PR **before** that run — not invented here.

If markout is red: **stop**. Do not “fix” it by rewriting H1 weights (weight optimize remains forbidden) or by skipping to economic PnL.

---

## Event-time ablation (H1a diagnostic / future H2)

Clock time (1s samples) can hide that the book moved 30 times in that second — or once. Register an **event-time** view:

| Clock | Event-time (registered) |
|-------|-------------------------|
| Locked H1 1s / 3s / 5s / 10s | **N book changes** after the signal: N ∈ {1, 5, 10, 20} |
| Same | **N aggressive trades** after the signal: N ∈ {1, 5, 10, 20} |

**Role:** H1a **diagnostic** now; candidate input to a future **H2** rung ([`84`](./84-atlas-trading-vnext.md) HFT ladder).  
**Forbidden:** using event-time to rewrite the locked 1s H1 ensemble, to search N, or to replace P4b / Layer B.

Id: `hft_h1a_event_time_ablation_v1`. Not scored in this PR.

---

## Honesty / invalidation

- Do not score markout or event-time in this PR.
- Do not skip markout because the signal study looked green.
- Do not invent fill-conditioned bps.
- Fee hurdle in [`75`](./75-scalp-hft-v1-design.md) remains the primary economic invalidation.
- `not_a_forecast: true`. `place_orders: false`.
