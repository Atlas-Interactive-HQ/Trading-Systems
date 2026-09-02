# Self-learning paper path (Atlas)

**Stance:** Measured adaptation on paper logs. No profit guarantee. Demo before live. Live only with explicit yes.

## Goal
Build a feedback loop that improves *rules/parameters* from recorded outcomes — not an unconstrained online learner trading real capital.

## Universe (locked 2026-09-02)
- DOGE-USD spot
- DOGE-USD_UM_XPERP-310516 (demo orders); public MD may use …310404
- PEPE deferred until demo lists it

## Risk (locked)
- Book equity for sizing: €200 (ignore faucet MTM)
- Daily kill 5% on paper PnL
- ~1–2% risk per trade; one position; X-Perp isolated ≤2x
- No martingale / grid / averaging

## Phases

### A — Observer
Signal-only sessions (spot + xperp). Journal features, regime, signal, hypothetical fill (fee/slip).
**Exit:** stable pipeline + enough journaled bars/signals for evaluation.

### B — Shadow demo
Same signals; OMS sizes and would-place decisions logged; no auto place (or human confirm only).
**Exit:** shadow path respects kill / one-position; reconciles with account reads.

### C — Gated micro-demo
Auto-place only under gates: fresh data, spread, risk budget, kill clear, signal + 1h filter, low daily trade cap. Parameters frozen.
**Exit:** live demo fills ≈ shadow within tolerance; no permission/compliance surprises.

### D — Offline learn
Trial ledger of parameter sets. Chronological walk-forward + holdout. Primary score: expectancy after costs; also max DD, turnover, fee drag; Deflated Sharpe when sample allows. Stress: 2× fees, delay, missed fills.
**Exit:** candidate beats frozen baseline on holdout *and* stress; not just in-sample.

### E — Adaptive paper
Slow updates (e.g. weekly) to a small parameter set with freeze + rollback. No continuous online RL on the book.

## Promotion checklist (auto-demo)
- [ ] Demo key v2 auth stable
- [ ] Orders use demo account instruments (X-Perp 310516)
- [ ] Kill-switch + one-position verified
- [ ] Journal complete (signals, decisions, orders, fills)
- [ ] Explicit "auto-demo aan" from Kaje
- Live remains a separate explicit gate

## Non-goals
- Guaranteed profit
- HFT / sub-second
- Treating assistant output as discretionary live trading
