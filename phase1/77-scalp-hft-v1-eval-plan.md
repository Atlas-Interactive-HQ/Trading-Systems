# 77 — Scalp-HFT v1 evaluation plan (R1–R7)

**Status:** paper-only · schema / plan lock · **no metrics numbers invented**  
**Strategy lock:** [`75-scalp-hft-v1-design.md`](./75-scalp-hft-v1-design.md) · [`76-scalp-hft-v1-rule-card.md`](./76-scalp-hft-v1-rule-card.md)  
**Panel authority:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) (dates frozen)  
**Artifacts:** `research/scalp_hft_v1.lock.json` · `research/scalp_hft_v1_sketch.py` · `results/scalp_hft_v1/R{1..7}/`  
**Config:** `config/default.yaml` **untouched** · Soft PASS **N/A** for this HFT lane until Layer B

---

## 1. Pre-run freeze checklist

Before any scored run:

1. Read exact R1–R7 definitions from `54-rise-panel-v1.md`
2. Compute/store rise_panel_v1 **manifest hash** into lock file
3. Freeze strategy parameters (EMA 12/21, VAMP-5, z=±1.0 seed, exits)
4. Freeze code commit SHA
5. Freeze fee assumptions + effective date
6. Freeze execution-model version (latency / queue assumptions)
7. Run R1–R7 **once** as locked evaluation

**Forbidden:** moving window boundaries; dropping bad minutes; swapping assets ex-post; threshold tuning per R-window; choosing long-only after shorts look bad.

### Warmup

- Only information **before** current timestamp may be used.
- If pre-window data exists: **60s causal warmup**.
- Else: first 60s of the R-window = warmup, **no trade**.
- Never use post-window data.

### Panel caveat

`rise_panel_v1` is a set of **selected rise** windows — not an unbiased market sample. R1–R7 can show behaviour in these up regimes; they **cannot** prove general profitability. Always-long already has a built-in advantage on rise panels.

**Required benchmarks (report separately LONG vs SHORT):**

- EMA12/21 only
- VAMP only
- always-long during window
- full EMA + VAMP candidate

---

## 2. Layer A vs Layer B (gate)

| Layer | When | Claim allowed |
|-------|------|---------------|
| **A** historical signal/regime | R windows (mostly pre–Apr 2026) + any non-OKX-EEA-XPerp proxy MD | `SYNTHETIC / PROXY EXECUTION` — signal behaviour only |
| **B** OKX forward paper | Post–Apr 2026 OKX X-Perp L2 + trades + mark + funding + latency + instrument params | execution **economics** statements |

Without causal VAMP-reconstructible depth: **`NO HFT BACKTEST CLAIM`** (fail-closed).

---

## 3. DATA INVENTORY (repo search, 2026-09-11)

Searched under `data/`, `phase1/`, `src/atlas/`, schemas, collectors. Summary:

### Exists

| Asset | What | Sufficiency for VAMP/HFT eval |
|-------|------|-------------------------------|
| `data/raw/okx_eea/2026-09-01/ws_books5.jsonl` | Collector smoke: OKX `books5` (top 5) envelopes for `BTC-USDT-SWAP` (~36 lines) | **Parser / schema smoke only** — not continuous history, not R1–R7 |
| Same day: `ws_bbo-tbt.jsonl`, `ws_trades.jsonl`, `mark_price.jsonl`, `funding_rate.jsonl`, instruments/tickers | Public MD sample | Smoke / unit tests |
| `data/paper/candles/`, `data/eval_cache/` | OHLCV / panel candle caches (DOGE/BTC multi-TF, rise windows) | Useful for **EMA-only / candle** Layer A proxies — **cannot** rebuild VAMP |
| `phase1/03-data-schemas.md` | `market.quote` (BBO), trades, mark, funding, bars | **No** dedicated multi-level `market.book` / L2 depth fact table yet |
| Schemas in code | `src/atlas/schemas/raw.py` raw envelopes | Raw `books5` possible; normalized L2 depth store not established for history |

### Missing (fail-closed blockers for VAMP HFT claim)

| Need | Status |
|------|--------|
| Continuous OKX L2 / books (top≥5 with sizes) covering **R1–R7** (2020-10 → 2024-11) | **MISSING** |
| Historical OKX EEA **X-Perp** L2 for those windows | **Impossible as genuine venue history** — product live Apr 2026; use Layer A label only if proxy MD ever appears |
| Continuous ~100ms books + trades + mark + funding for **Layer B** forward paper (post-2026-04) | **MISSING** beyond single-day smoke |
| Queue-/latency-faithful fill model wired to stored L2 | **MISSING** (sketch stubs only) |
| Hugging Face / other-venue L2 in-repo | **Not present** (and even if fetched: **≠** OKX X-Perp; parser tests only) |

### Gate decision (until inventory changes)

1. **Do not** fill `results/scalp_hft_v1/R*/` with fabricated PnL / metric tables.
2. Any candle-only run must be labeled **not** an HFT/VAMP backtest (`NO HFT BACKTEST CLAIM` if VAMP is asserted).
3. Next engineering gate: ingest/store OKX books (top≥5) + trades + mark for Layer B; optionally proxy L2 for Layer A signal studies with explicit `SYNTHETIC / PROXY EXECUTION`.

---

## 4. Metrics schema (empty — fill only after real runs)

Per R1–R7 and pooled. Values stay **null / TODO** until evaluation writes them.

### Signal

- signal_count
- long_count / short_count
- future_mid_return_at_1s / 3s / 5s / 10s / 30s
- direction_hit_rate
- vamp_conditional_return

### Execution

- orders_submitted
- maker_fill_pct
- partial_fills
- cancel_pct
- cancel_fill_races
- average_queue_wait
- latency_distribution
- slippage

### Trading

- completed_trades
- gross_pnl / fees / funding / slippage / net_pnl
- win_rate / average_win / average_loss
- expectancy / profit_factor
- MAE / MFE / max_drawdown
- average_holding_time / time_in_market

### Risk

- hard_sl_count / hard_tp_count
- time_stop_count / edge_decay_exit_count
- kill_switch_count
- worst_net_margin_roi

Also report: maker–maker, maker–taker stress, taker–taker stress.

**No** Sharpe with misleading annualisation on a handful of selected windows without an explicit warning.

---

## 5. Ablation matrix (diagnostic — not winner-picking)

Candidate remains **EMA + VAMP5**. Ablations diagnose; they do **not** let R1–R7 pick a winner among dozens of variants. A3–A5 replacing the candidate requires a **new registered hypothesis** on unseen material.

| ID | Model | Question |
|----|-------|----------|
| A0 | EMA12/21 only | Does VAMP add incremental value? |
| A1 | VAMP5 only | Does EMA trend filtering add value? |
| A2 | EMA + VAMP5 | **Candidate** |
| A3 | EMA + static OBI | Is VAMP better than simple imbalance? |
| A4 | EMA + VAMP1 | Depth sensitivity |
| A5 | EMA + VAMP10 | Depth sensitivity |
| E0 | zero-added latency | Upper-bound diagnostic |
| E1 | +50 ms | Latency sensitivity |
| E2 | +100 ms | Latency sensitivity |
| E3 | +250 ms | Severe retail latency |
| F0 | maker/maker | Fee/fill case |
| F1 | maker/taker | Conservative normal case |
| F2 | taker/taker | Fee stress |

---

## 6. Acceptance classes

| Class | Meaning |
|-------|---------|
| `INVALID` | Data or execution model not trustworthy enough |
| `FAIL` | No net edge |
| `FRAGILE` | Base-case looks positive but dies under fees / latency / queue / regime stress |
| `PAPER CANDIDATE` | Incremental EMA+VAMP value; survives fees/slippage; realistic fills; not one-window; latency stress OK; **and** later reproduces direction on genuine OKX X-Perp forward paper |

`PAPER CANDIDATE ≠ LIVE APPROVAL`. Soft PASS from candle Mid/Scalp boards does **not** apply here.

---

## 7. Results tree

```
results/scalp_hft_v1/
  .gitkeep
  R1/ … R7/   # empty until real eval writes artifacts
```

Do not invent metrics files with numbers.
