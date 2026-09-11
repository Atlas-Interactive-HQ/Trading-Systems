# 75 — Scalp-HFT v1 design lock (EMA12/21 + VAMP-5)

**Status:** research / paper-only · **accepted v1 lock**  
**Research snapshot:** 2026-09-11  
**Lane:** Scalp — fully separate from Core + Mid  
**Forecast status:** `not_a_forecast`  
**Live execution:** forbidden  
**Martingale / averaging down:** forbidden  
**Global config:** `config/default.yaml` **untouched**

**Supersedes intake:** [`71-codex-scalp-hft-design-brief.md`](./71-codex-scalp-hft-design-brief.md). Docs **75–77** + `research/scalp_hft_v1_*` are the accepted v1 lock.

**Numbering note:** Mid already used `phase1/72*`, `73-mid-sleeve-riskup.md`. Scalp-HFT design therefore lands at **75 / 76 / 77** (not Codex paste’s provisional 72–74 paths).

**Companions:** [`76-scalp-hft-v1-rule-card.md`](./76-scalp-hft-v1-rule-card.md) · [`77-scalp-hft-v1-eval-plan.md`](./77-scalp-hft-v1-eval-plan.md) · [`81-scalp-hft-tp60-lock.md`](./81-scalp-hft-tp60-lock.md) · `research/scalp_hft_v1_sketch.py` · `research/scalp_hft_v1.lock.json`

---

## 1. Executive decision

v1 strategy:

**EMA 12/21 trend alignment + VAMP-5 order-book displacement**

VAMP = Volume-Adjusted Mid Price. It uses price **and** liquidity on both sides of the book to estimate where very short-horizon “fair price” sits relative to the ordinary midpoint.

Why VAMP over RSI / MACD / stochastic / a third candle indicator:

1. EMA 12/21 already carries price-trend information; another candle indicator largely repackages the same signal.
2. An order-book signal fits a scalp that targets seconds, not hours. Order-flow imbalance literature finds book changes informative on short horizons; Stoikov-style micro-price work finds book-adjusted prices can be better short-horizon estimators than raw mid. See Sources (Cont et al.; related micro-price literature).
3. Crypto-specific work (*Mind the Gaps*) reported a VAMP-style feature outperforming trade-/quote-imbalance variants for short-horizon direction in their BTC LOB dataset. That is **not** proof our strategy is profitable — only a better rationale for experimentation than adding RSI at random. See Sources (SSRN).

Public hftbacktest docs discuss VAMP / OBI as microstructure alpha and support latency-/queue-aware backtesting (MIT). We adopt the **concept** only and implement independently. See Sources (hftbacktest).

---

## 2. OKX EEA reality (leverage + fees)

Since April 2026, OKX Europe offers MiFID-regulated X-Perps in the EEA. Published crypto X-Perp leverage is currently up to **10×**; actual max for a given order can be lower (instrument, size, risk tier, equity). v1 **must not** assume 10× is executable.

**Rule:**

```
L_used = highest demonstrably allowed leverage for
         instrument + position + account/tier,
         with absolute cap 10x.
```

If max allowed leverage cannot be demonstrated: **NO TRADE** — do not guess.

Isolated margin is mandatory.

### Fee hurdle (primary economics risk)

Published standard X-Perp fees for verified EEA users (OKX; verify at lock time):

| | Maker | Taker |
|--|------:|------:|
| Execution fee | 0.02% | 0.05% |

Approximate round-trip **before** slippage/funding:

| Path | Notional cost | Effect on 10× margin |
|------|--------------:|---------------------:|
| Maker → Maker | 4 bps | 0.4% |
| Maker → Taker | 7 bps | 0.7% |
| Taker → Taker | 10 bps | 1.0% |

For microstructure strategies this is not a detail — it may be the main invalidation. A few-bps statistical edge can still be economically worthless.

---

## 3. 20% SL / 60% TP lock (net margin ROI)

Defined on **net return on isolated margin**:

- Hard Stop: `net_margin_ROI <= -20%`
- Hard Take Profit: `net_margin_ROI >= +60%`

**Net** = mark-to-market PnL − entry fees − exit fees (or estimated exit fees) − slippage − funding.

At 10×, before costs, roughly: −20% margin ROI ≈ −2% underlying; +60% ≈ +6% underlying.

**Design decision:** +60% TP is the **outer hard win bound**, not the normal scalp exit. Prefer closing when microstructure edge dies (edge-decay exit). Hard TP remains an outer bound only.

Define: **1R = 20% of isolated margin per trade** → Hard SL = −1R, Hard TP = +3R (1:3 R:R).  
**Kaje lock 2026-09-11:** “TP 1/3 dus 20 tot 60” = SL −20% / TP +60% where 1R = 20% isolated margin. Prior outer bound was +100% / +5R (superseded by this lock; see [`81-scalp-hft-tp60-lock.md`](./81-scalp-hft-tp60-lock.md)).

---

## 4. Market data & speed

Technically a **low-latency microstructure scalper**, not colocated institutional HFT.

v1 baseline:

| Item | Choice |
|------|--------|
| Source | OKX books (400-level capable source) |
| Feed | ~100 ms incremental (not VIP 10 ms TBT-dependent) |
| VAMP depth | **top 5 levels** |
| Signal clock | **1 second closed** samples |

Use `seqId` / `prevSeqId` for continuity. Do not rely on deprecated checksum integrity.

Also record: trades, mark price, index price, funding timestamps/rates, instrument metadata.

**Mark price** is used for risk/PnL (aligned with OKX X-Perp liquidation logic).

---

## 5. Signal definition

### 5.1 Price stream (per closed second)

```
mid_t = (best_bid_t + best_ask_t) / 2
EMA_fast = EMA(mid, 12)
EMA_slow = EMA(mid, 21)
```

No intrabar / future updates for that second.

### 5.2 VAMP-5

Take the five best bid and ask levels: `(Pbid_i, Qbid_i)`, `(Pask_i, Qask_i)`.

```
VAMP5 = (
    Σ(Pbid_i × Qask_i) + Σ(Pask_i × Qbid_i)
) / (
    ΣQbid_i + ΣQask_i
)
```

Asset-independent edge:

```
vamp_edge_bps = 10_000 × (VAMP5 - mid) / mid
vamp_z = (vamp_edge_bps - rolling_mean_60s) / rolling_std_60s
```

If std is zero/invalid: `vamp_z = INVALID` → **NO TRADE**.

---

## 6. Entry rules (all must hold)

**LONG**

- `state == FLAT`
- `data_health == HEALTHY`
- `cooldown_complete == true`
- `EMA12 > EMA21`
- `VAMP5 > mid`
- `vamp_z >= +1.0`
- confirmed in **≥2 of last 3** closed 1s samples

**SHORT** — exact mirror (`EMA12 < EMA21`, `VAMP5 < mid`, `vamp_z <= -1.0`, 2-of-3).

`±1.0` is a **pre-registered seed**, not a claimed optimum. Do **not** search R1–R7 for e.g. 0.83 because it happened to print more profit.

---

## 7. Entry execution

- Normal entry: **post-only maker**
- LONG quote = current best bid; SHORT = current best ask
- TTL = **1 second**; if unfilled → cancel, **do not chase**
- After cancel: wait for **terminal** order state before allowing a new order (ack alone is not proof of cancel)
- Forbidden: market chase, pyramiding, scale-in, average-down, martingale
- Max **one** open position

---

## 8. Exit hierarchy (binding order)

1. **System kill** — integrity/risk fault → simulated immediate flatten → `HALTED`
2. **Hard SL** — `net_margin_ROI <= -20%` → immediate simulated taker exit
3. **Hard TP** — `net_margin_ROI >= +60%` → immediate close
4. **Edge-decay exit** — LONG: `EMA12 <= EMA21` OR `vamp_z <= 0` (SHORT mirrored); require 2-of-3; try post-only maker exit ≤1s, then taker flatten if still open
5. **Time stop** — `max_hold = 60 seconds` → close regardless of PnL

---

## 9. Position sizing

No fictional euro account in early backtests.

- `margin_unit = 1.0000` per trade
- `position_notional = margin_unit × verified_leverage`
- Report as return on isolated margin
- **No** compounding inside R1–R7; no size-up after win/loss
- Contract-size validation is separate (e.g. BTC X-Perp contract size may be 0.01 BTC) — paper notional ≠ live feasibility

---

## 10. Kill-switch (sticky; no auto-restart)

| Kill | Trigger (summary) |
|------|-------------------|
| `KILL_DATA` | seq discontinuity; invalid book; bid≥ask outside auction; neg/NaN qty; timestamp reversal; book too stale for entry; WS reconnect without snapshot |
| After gap | discard local book → rebuild snapshot → re-warmup indicators |
| `KILL_ORDER_STATE` | ambiguous fill/cancel; non-idempotent duplicate terminal; unknown open order |
| `KILL_LATENCY` | exchange data >1s behind decision → no entry; **3** consecutive → `HALT` |
| `KILL_CONFIG` | cannot verify instrument, contract size, tick, margin mode, max leverage, fee schedule |
| `KILL_LOSS` | cumulative window PnL ≤ −2R → flatten + halt for remainder of R-window (safety, not alpha) |
| `PAPER_ONLY` | any path attempting live `POST /trade/order`, private WS placement, or trading credential load → `PAPER_ONLY_VIOLATION` → `HALT` |

---

## 11. State machine

```
BOOT → VERIFY_CONFIG → WARMUP → FLAT → ENTRY_WORKING → OPEN
     → EXIT_WORKING → COOLDOWN → FLAT
```

Any invariant violation → `KILL` → `HALTED`. No implicit transitions. Position exists **only** after a simulator fill event.

---

## 12. Fill simulation (fail-closed)

“Filled because price touched limit” is **not** acceptable.

v1 must simulate at least: feed latency, submit/cancel latency, quantity ahead in queue, trades through price, partial fills, cancel/fill races, taker book walking.

With L2 only, cancellations ahead/behind are unknown → **conservative queue**: cancellations do not grant free queue progress; trades through the level do.

If R-window data cannot support this reconstruction: **`EXECUTION_BACKTEST_INVALID`** — never assume instant fill.

---

## 13. Layer A / Layer B gate (prominent)

OKX EEA X-Perps went live **April 2026**. R1–R7 in `rise_panel_v1` are **2020–2024** — they **cannot** be genuine historical OKX EEA X-Perp execution backtests.

| Layer | Role | Label |
|-------|------|-------|
| **A — historical signal/regime test** | EMA / VAMP behaviour, entry timing, directional edge, regime sensitivity on available historical MD | `SYNTHETIC / PROXY EXECUTION` |
| **B — genuine OKX forward paper** | OKX X-Perp L2 + trades + mark + funding + spread + latency + instrument params; paper orders against that | only Layer B supports serious OKX EEA **execution economics** claims |

**Fail-closed for VAMP:** without causal reconstructible top-of-book depth (levels + sizes) on the evaluation clock, do **not** claim an HFT/VAMP backtest. See [`77`](./77-scalp-hft-v1-eval-plan.md) DATA INVENTORY.

Hugging Face / Coinbase / Kraken / Binance L2 may be used for parser/unit tests only — **≠** OKX X-Perp L2; never use to claim realistic OKX fill-PnL.

---

## 14. Honesty / invalidation (summary)

| Class | Outcome label |
|-------|---------------|
| No causal VAMP data | `NO HFT BACKTEST CLAIM` |
| Gross edge dies after realistic fees | `EDGE EXISTS STRATEGY NOT ECONOMIC` |
| Needs instant maker / fantasy queue | `REJECT` |
| Dies under plausible latency | `LATENCY-ARBITRAGE NOT ACCESSIBLE` |
| EMA+VAMP not better than EMA-only | `VAMP NOT JUSTIFIED` |
| One window / few outliers drive result | `FRAGILE / NO GENERALIZATION CLAIM` |
| Works only on rise panel | `RISE-REGIME SPECIALIST AT BEST` |
| 10× not allowed for contract/size/tier | use highest verified lower leverage |
| OKX product/API/fee change | `HALT REVALIDATE` |

Acceptance classes (no pre-promised PASS): `INVALID` | `FAIL` | `FRAGILE` | `PAPER CANDIDATE`.  
Even `PAPER CANDIDATE ≠ LIVE APPROVAL`. Soft PASS N/A for this HFT lane until Layer B forward paper exists.

---

## 15. Hypothesis under test

Not “EMA + another indicator makes money.”

**When EMA12/21 indicates a very short trend direction, does VAMP-5 displacement vs mid contain enough incremental book information to produce an exploitable short-horizon edge after fees, queueing, latency, and slippage?**

Largest concern: **economics**. With ~2 bps maker / ~5 bps taker, a correct few-bps forecast may simply be untradeable. Evaluate obsessively fee-/queue-/latency-aware — do not pretty-up a candle backtest. If costs kill the hypothesis, shoot the system.

---

## Sources

- OKX Europe — Regulated X-Perps in Europe: https://www.okx.com/en-eu/learn/okx-x-perps-mifid-regulated-crypto-futures-derivatives-europe
- OKX — X-Perps leverage explained: https://www.okx.com/en-eu/help/okx-x-perps-eea-leverage-explained
- OKX — X-Perps fees overview: https://www.okx.com/en-eu/help/okx-x-perps-eea-fees-overview
- OKX — X-Perps contract specifications: https://www.okx.com/en-eu/help/x-perps-contract-specifications
- OKX API v5: https://www.okx.com/docs-v5
- nkaz001/hftbacktest (MIT): https://github.com/nkaz001/hftbacktest
- hftbacktest — Market Making with Alpha: Order Book Imbalance: https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html
- SSRN — Mind the Gaps: Short-Term Crypto Price Prediction: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4351947
- arXiv — The Price Impact of Order Book Events (Cont et al.): https://arxiv.org/abs/1011.6402
- Hugging Face — example public Coinbase L2 replay (parser/research only): https://huggingface.co/datasets/deusmos/cbb26-timeseries-db
