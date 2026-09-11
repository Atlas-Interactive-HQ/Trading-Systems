# 71 — Codex brief: standalone HFT Scalp lane (design)

**Status:** draft for Codex / cloud agent — **paper design only**  
**Label:** `scalp_hft_lane_v0` · **not_a_forecast** · no profit guarantee  
**Coordinator:** Atlas | Trading Systems · **Research:** Atlas | TS Research (own lane)  
**Date:** 2026-09-11

---

## 0. Mission (Kaje)

Design a **standalone high-frequency scalping system** for Atlas Trading Systems, **separate** from the Core+Mid bot book.

Architecture intent:

| Stream | Role | Research |
|--------|------|----------|
| Core | Existing bot book (EMA 1D ref) | **Paused** this phase |
| Mid | Existing bot book (Breakout #65 baseline) | **Paused** this phase |
| **Scalp** | **Standalone HFT lane** | **Own research + own design** |

Later (explicit Kaje yes only): go live with **both** lanes (Core+Mid book **and** Scalp HFT). Until then: **paper / sim only**. Live cap remains ≤€20 practice unless Kaje writes `ga live …`.

---

## 1. Hard constraints (fail-closed)

1. **Paper-first.** No live orders, no OMS POST, no `default.yaml` mutation unless labeled parallel overlay.
2. **not_a_forecast.** “Profitable” = measurable criteria after costs, never a guarantee. Markets can wipe leveraged sleeves.
3. **Risk shape (Kaje lock for this design):**
   - Stop loss: **20%** of position notional (define precisely: entry-based % vs equity %)
   - Take profit: **100%** of position notional (same definition as SL)
   - Leverage: **as high as venue allows** under isolated margin, with hard caps documented from OKX EEA product limits
4. **Kill-switch:** max loss/day, max position, stop-all. No martingale.
5. **Venue:** OKX EEA (DOGE-USDC spot and/or DOGE swap/perp as justified). Prefer instruments that actually support the leverage thesis; spot cannot do “max leverage” — if HFT scalp needs leverage, design must use **isolated perp/swap** with explicit liquidation distance math.
6. **Costs:** fees + funding + slippage must be in expectancy. HFT without costs is invalid.
7. **Do not** claim soft_promote / live-arm. Soft PASS ≠ arm.
8. Consult **Hugging Face** and/or **public GitHub repos** for ideas (features, microstructure heuristics, RL baselines) — cite sources; do not copy GPL code into Atlas without license note; prefer reimplementation of ideas.

---

## 2. Measurement panel (locked)

Use Atlas `rise_panel_v1` (7 DOGE-USDT similar rise / choppy-bull windows):

| ID | Start | End | Notes |
|----|-------|-----|-------|
| R1 | 2020-10-01 | 2020-12-31 | late-2020 grind |
| R2 | 2021-07-20 | 2021-10-20 | mid-2021 recovery chop |
| R3 | 2022-08-10 | 2022-11-07 | late-2022 bounce |
| R4 | 2023-09-01 | 2023-11-30 | ETF-anticipation |
| R5 | 2023-12-01 | 2024-02-29 | winter continuation |
| R6 | 2024-03-01 | 2024-05-31 | spring choppy bull |
| R7 | 2024-08-07 | 2024-11-04 | late-2024 grind |

Code refs in repo: `atlas.paper.rise_panel.RISE_PANEL_V1`, `scripts/run_rise_panel_eval.py`, `phase1/54-rise-panel-v1.md`.

**Suggested Scalp gate (label clearly, e.g. `scalp_hft_soft_promote_v0`):**

- median_trades ≥ N (propose N for HFT; likely ≫ Mid’s 1)
- ≥5/7 windows expectancy_after_costs > 0
- panel_net > 0
- report max DD, liquidation events, fee drag, median holding time

Honesty: compare against prior Scalp board (EMA 1H/4H, RSI, Donchian, Breakout on rise_panel) without claiming those as this HFT system.

---

## 3. Signal stack (Kaje)

**Required:**

1. **EMA 12 / 21** as regime or entry filter (state how: long-only when 12>21, flatten when cross, etc.).
2. **A second indicator for edge** — Codex must propose **one primary** (+ optional ablates), justified for HFT / short holding times. Candidates to evaluate (not all required):
   - RSI / stochastic micro-MR
   - MACD hist / momentum impulse
   - Bollinger %B / squeeze release
   - Order-flow proxies from OHLCV only (range, volume z-score) if no L2 data
   - Volatility filter (ATR%) so 20% SL is not constant noise

**Out of scope unless justified:** full L2 book replay (may not exist in current Atlas MD pipeline). If Codex needs L2, propose a **data acquisition plan** instead of inventing fills.

---

## 4. Trade / risk mechanics to specify

Codex must produce a concrete rule card:

- Timeframe(s): e.g. 1m / 5m / 15m (pick with evidence on rise_panel)
- Entry, exit, size, max concurrent positions
- **SL 20% / TP 100%** implementation: mark price? last? mid?
- Leverage choice + isolated margin + liquidation buffer vs 20% SL (SL must trigger **before** liq if possible)
- Session filters (funding hour, weekend, spread gate)
- Fail-closed: missing data, API error, kill hit

Capital model for paper: propose sleeve size (e.g. €20 practice vs €50–€200 later) — **do not** assume `ga live €200`.

---

## 5. Deliverables (Codex output)

1. **Design doc** (`phase1/7x-scalp-hft-design.md`): rules, risk, data, sources consulted (HF/repos with links).
2. **Pseudocode / Python sketch** fitting Atlas paper walk style (entry/exit hooks), **no** live OMS wiring.
3. **Eval plan** on `rise_panel_v1` + metrics table template.
4. **Ablation list:** EMA12/21 alone vs EMA+indicator A vs A alone.
5. **Honesty section:** what would **invalidate** the design (fee drag, SL hit rate, liq risk).
6. **Do not** change `config/default.yaml`. Do not push live keys.

---

## 6. Success criteria (design phase)

Design is “done” when:

- Rules are unambiguous enough to implement without reinterpretation
- Risk math (SL/TP/leverage/liq) is consistent
- Eval plan uses locked R1–R7 windows
- Sources cited; no fabricated backtest numbers

**Implementation / paper numbers** are a **follow-up** Research lock after Kaje accepts the design — Codex must **not invent** PnL tables.

---

## 7. Paste block for Codex

```text
You are designing (paper-only) a standalone HFT scalping system for Atlas-Interactive-HQ/Trading-Systems.

Context:
- Separate Scalp lane from Core+Mid bot book (Core/Mid research paused).
- Measure on locked rise_panel_v1 windows R1–R7 (see phase1/54-rise-panel-v1.md).
- Required signals: EMA 12/21 + one additional edge indicator (justify choice; consult Hugging Face / public repos for ideas; cite links; reimplement ideas, don’t dump licensed code).
- Risk lock: 20% stop loss, 100% take profit, maximize leverage under isolated OKX EEA limits with kill-switch; no martingale.
- Fail-closed; not_a_forecast; no invented backtest metrics; no default.yaml changes; no live orders.

Deliver: design doc + rule card + pseudocode/sketch + eval plan + ablations + honesty/invalidation + source citations.
```

