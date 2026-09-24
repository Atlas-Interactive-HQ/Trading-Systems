# OPEN_EVIDENCE — Atlas Cycle v1

**As-of:** 2026-09-24. **LIVE HOLD.**

Forward paper is **PENDING_FORWARD_EVIDENCE**. Elapsed forward calendar days: **0**. This file does not record a 30-day window. The synthetic series is generated inside the process. It is not a forward journal and it is not a claim that 30 days have elapsed.

Nothing here promotes a gate to PASS.

## What is already on disk

| Item | State |
|------|--------|
| Unit controls (ledger, risk, LIVE refusal, BTC reserve, settlement examples) | Tested. See `GATE_STATUS.md` G0–G5, G12–G15. |
| DOGE entry ablation | Synthetic, 20 OOS cycles per mode, bootstrap intervals cross 0. G7 stays **INSUFFICIENT_EVIDENCE**. |
| Scalp A/B/C/D | Synthetic, 0 OOS scalps, 20 OOS DOGE cycles. G6 stays **INSUFFICIENT_EVIDENCE**. Freeze `SCALP_OFF`. |
| Public SWAP snapshot (SOL, ETH, PEPE) | Stored in `public_probe.py` for the paper size table. Registry `listing_verified` stays false. G8 stays **INSUFFICIENT_EVIDENCE**. |
| Fee and slippage | Labeled assumptions. Funding unknown. G9 stays **INSUFFICIENT_EVIDENCE**. |
| Live free USDC | 0.69 from the 2026-09-24 upload. G10 stays **FAIL**. |

## What a future upgrade needs

Each line is required before the named gate can move. A single line is not enough to arm live trading.

### Real OHLCV provenance (G16, and the input to G7)

- Closed candles from a named public or recorded source, with symbol, timeframe, and the fetch time stored next to the file.
- `fetch_okx_history_candles` may be used as that source. A hand-built regime is not a substitute.
- The report states the file hash, the first and last bar timestamps, and that the walk did not peek at holdout during selection.
- A ticker `last` price is not a candle history.

### DOGE edge (G7)

- At least **200 OOS DOGE cycles** on that real series (validation + untouched holdout).
- Costs on, including the labeled fee and slippage until G9 is measured, and funding once it is known.
- Bootstrap 95% interval of OOS cycle PnL stays above 0.
- Selection uses development and validation only. Holdout is scored after the entry freeze is written down.
- The current synthetic preference for `direct_breakout` does not by itself move `entry_frozen`. The floor and the interval have to clear on the real series first.
- Do not loosen the signal to manufacture the 200 cycles.

### Scalp, only if it is revisited (G6)

- Scalp stays off until this list is met. DOGE-only remains a valid outcome if it is not met.
- Same rules for the fixed set SOL, then ETH, then PEPE. No extra coins.
- At least **300 OOS scalps** and at least **100 OOS DOGE cycles** on the real series.
- Positive validation scalp net inside the allowed DOGE window (+1R, stop not widened, risk mode NORMAL), costs on.
- Freeze the coin before holdout. Tie-break stays: lowest median round-trip cost as a fraction of gross 1.5R, then p95, then SOL → ETH → PEPE.
- Legacy live PEPE stays outside the cycle. Paper PEPE stays a separate simulated instrument.

### Forward paper (G11)

- Status stays **PENDING_FORWARD_EVIDENCE** until a real forward journal exists.
- Minimum window: **30 calendar days** and **30 DOGE cycles** in that forward journal.
- The clock starts when a paper session is actually run forward. Today is 2026-09-24 and that session has not started, so the count of elapsed days is 0.
- Replaying the synthetic 16,000 bars does not advance the calendar count. Those bars are not unseen future days.
- Smoke, the DOGE backtest, and the Phase 3 script do not fill this gate.

### Verified instrument metadata (G8, with G9)

- Promote a probe only with minSz, lotSz, tickSz, ctVal, ctType, state, and the account fee tier recorded as data.
- `listing_verified` stays false until that decision is explicit. The 2026-09-24 public snapshot is not that decision.
- Funding is a measured series or an explicit remaining-unknown that still blocks promotion.

### Live capital (G10)

- Free collateral at or above T = 0.40×A for the chosen A, without raising leverage.
- Or an explicit decision to run a smaller sleeve. That decision is not in this package.
- G10 can move off FAIL and the edge gates can still be **INSUFFICIENT_EVIDENCE**. Capital does not prove an edge.

## What this package will not invent

- A PASS on G6, G7, G8, G9, or G16 from synthetic expectancy.
- A completed 30-day forward window.
- `listing_verified=true`.
- A live arm, a scalp arm, or a change to `config/default.yaml`.
