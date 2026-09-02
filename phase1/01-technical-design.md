# 01 — Technical Design (Phase 1)

**Project:** Atlas Trading Systems  
**Scope:** Architecture, services, data flow, paper→live gates, UI observability hooks  
**No live trading code in Phase 1.**  
**Labels:** **VERIFIED** (locked decision or settled engineering fact) · **ENGINEERING RECOMMENDATION** · **HYPOTHESIS** · **UNVERIFIED** (needs primary source)

---

## 1. Design goals

1. Measure **expectancy after costs** on paper at €200 scale before any live credentials. **[VERIFIED — L13]**  
2. Collect exchange-neutral market data with **append-only raw** retention and **deterministic replay**. **[ENGINEERING RECOMMENDATION]**  
3. Enforce risk: daily kill 5%, per-trade 1–2%, leverage ≤2x default / 5x paper hard, one directional position. **[VERIFIED — L2–L4, L9]**  
4. Strategy v1: breakout L+S; ranging disabled; untradeable regime gates. **[VERIFIED — L5]**  
5. Non-HFT: 15m execution + 1h regime. **[VERIFIED — L8]**  
6. Future UI consumes events/metrics only — no UI build in Phase 1. **[VERIFIED — L12]**

---

## 2. Challenge: unsafe or statistically weak requirements

| Requirement / temptation | Challenge | Atlas stance |
|--------------------------|-----------|--------------|
| “Optimize until backtest looks great” | Multiple testing / curve-fit; false expectancy | Fixed holdout + paper forward; no parameter fishing without registry |
| Sub-second / HFT on €200 | Fees, latency, ops cost dominate | Explicit non-HFT; 15m bars |
| Multi-symbol from day one | Alt illiquidity, funding spikes, data bugs | BTC perp plumbing first |
| Cross-margin max leverage | Liquidation cascades on small equity | Isolated where supported; ≤2x default, 5x paper hard |
| Ranging + breakouts together | Regime confusion, correlated false positives | Ranging DISABLED in v1 |
| Live keys “just for testing” | Catastrophic drawdown / key leak | Gate: paper + reconciliation + kill switches |
| Assistant as discretionary trader | Unauditable, unbounded risk | Assistants = research/code only |
| Assuming fill at mid / next open without slippage model | Inflated PnL | Conservative fill model (see §8 and `06-false-profitability-assumptions.md`) |
| Ignoring funding on perps | Silent bleed on holds across funding | Funding in cost model from day one of research |
| Claiming geo/product access without docs | Legal/compliance failure | All venue facts **UNVERIFIED** until primary sources |

**Statistically weak:** claiming edge from < few hundred independent trades on 15m BTC alone; meme/AI perps with sparse liquidity — treat early results as **HYPOTHESIS**, not product claims.

---

## 3. High-level architecture

```
┌─────────────┐   public WS/REST    ┌──────────────────┐
│ Exchanges   │ ──────────────────► │ Collectors       │
│ (Kraken MD, │                     │ (per venue)      │
│  OKX MD)    │ ◄── heartbeat/time  └────────┬─────────┘
└─────────────┘                              │ append-only
                                             ▼
                                    ┌──────────────────┐
                                    │ Raw object store │
                                    │ + Parquet lake   │
                                    └────────┬─────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              ▼                              ▼                              ▼
     ┌────────────────┐            ┌────────────────┐            ┌────────────────┐
     │ Research /     │            │ Feature /      │            │ Data quality   │
     │ Backtest       │            │ Bar builder    │            │ monitors       │
     │ (offline)      │            │ (15m / 1h)     │            │                │
     └───────┬────────┘            └───────┬────────┘            └───────┬────────┘
             │                              │                              │
             └──────────────┬───────────────┘                              │
                            ▼                                              │
                   ┌────────────────┐                                      │
                   │ Strategy +     │◄─────────────────────────────────────┘
                   │ Regime gates   │   (stale/gap → untradeable)
                   └───────┬────────┘
                            ▼
                   ┌────────────────┐     later (still paper)
                   │ Risk engine    │──────────────────────────► Paper order manager
                   │ (size, kills)  │◄── fills / positions ───── (venue demo APIs)
                   └───────┬────────┘
                            ▼
                   ┌────────────────┐
                   │ Monitoring +   │──── events/metrics ───► Future UI hooks
                   │ Observability  │
                   └────────────────┘
```

**Private/order paths are design-only until paper gates pass.** Public collectors ship first.

---

## 4. Services (responsibilities)

### 4.1 Collectors (public market data)
- **Role:** Subscribe / poll public feeds; write **raw messages** + normalized rows.  
- **Venues (targets):** Kraken Derivatives public MD; OKX public MD for X-Perpetuals. Product availability **UNVERIFIED**.  
- **Constraints:** No secrets for public MD where possible; rate-limit backoff; sequence / gap detection.  
- **Label:** **ENGINEERING RECOMMENDATION** for process split (one collector process per venue).

### 4.2 Storage
- **Raw:** Append-only files (e.g. JSONL / msgpack / compressed NDJSON) keyed by `venue / channel / date / hour`. Never mutate.  
- **Derived:** Parquet partitions for quotes, trades, mark, index, funding, status, bars.  
- **Clock:** All stored timestamps UTC. Keep `exchange_ts`, `receive_ts`, and monotonic `sequence` where available.  
- **Label:** **ENGINEERING RECOMMENDATION** — Parquet + Hive-style partitions `venue=…/symbol=…/date=…`.

### 4.3 Research / backtest
- Offline only; reads Parquet + raw for audit.  
- Deterministic replay: same inputs + config hash → same decisions and simulated fills.  
- Cost model: fees, funding, slippage, partial fills, leverage/liquidation constraints.  
- Strategy registry: versioned configs; no silent re-optimization.  
- **Label:** **ENGINEERING RECOMMENDATION**.

### 4.4 Paper order manager (later in Phase 1+/2 — design now)
- Talks only to **demo/paper** APIs (**UNVERIFIED** product existence).  
- Idempotent client order IDs; full ack/cancel/fill journal.  
- Reconciliation vs venue positions/balances on interval + on reconnect.  
- **No live credentials** until gates pass. **[VERIFIED — L11]**

### 4.5 Risk engine
- Inputs: equity, open position (at most one direction), proposed order, market state, regime flag.  
- Enforces:  
  - `notional = min(risk_budget / stop_distance_fraction, leverage_cap * equity, liquidity_cap)` **[VERIFIED — L14]**  
  - Daily loss kill 5% **[VERIFIED — L2]**  
  - Per-trade risk 1–2% **[VERIFIED — L3]**  
  - Leverage default ≤2x, paper hard 5x isolated where supported **[VERIFIED — L4]**  
  - Reject if regime = untradeable or ranging mode requested in v1  
  - Reject pyramiding / averaging / martingale / grid intents  
- Fail-closed: missing data, stale clock, or risk service down → **no new risk**.

### 4.6 Strategy + regime
- **Execution TF:** 15m breakout L+S.  
- **Regime TF:** 1h — classify tradeable breakout vs untradeable (and later ranging — disabled).  
- Exact indicator set: **HYPOTHESIS** (to be fixed in research notebook with holdout). Design requires *gates exist*, not a specific RSI/ATR recipe yet.

### 4.7 Monitoring / observability
- Health: collector lag, gap counts, WS reconnects, disk, process heartbeats.  
- Trading (paper): orders, rejects, fills, PnL, kill-switch trips, regime state.  
- Emit structured events + Prometheus-style metrics (or equivalent) for future UI.  

---

## 5. Data flow (UTC, append-only, replay)

1. **Ingest:** WS/REST → raw append (`receive_ts` set at socket read).  
2. **Normalize:** Parse → exchange-neutral schema (see `03-data-schemas.md`) → Parquet. Retain `sequence` if present.  
3. **Bars:** Build 15m / 1h OHLCV (+ mark/funding join) from trades or candles **only with closed-bar rules** (no partial-bar lookahead).  
4. **Features / decisions:** Strategy reads closed bars only; writes decision records.  
5. **Risk:** Sizes / vetoes; writes risk decision records.  
6. **Paper exec (later):** Orders → acks/fills → account snapshots.  
7. **Replay:** Raw or normalized stream + config → bit-identical decision log (**ENGINEERING RECOMMENDATION**: hash config + code version into run metadata).

**Mutation policy:** Corrections land as **new** files / partitions with `correction_of` metadata — never rewrite historical raw.

---

## 6. Paper → live gate (hard)

Live order credentials are forbidden until **all** pass:

| Gate | Criterion |
|------|-----------|
| G1 | Public MD quality tests green for BTC perp window (see `05-data-quality-tests.md`) |
| G2 | Paper order path reconciles positions/balances vs venue for N consecutive days (**N TBD** — **ENGINEERING RECOMMENDATION**: ≥10 trading days) |
| G3 | Kill switches demonstrated (daily loss, per-trade reject, stale data, manual halt) |
| G4 | Expectancy after costs measured on paper; no marketing claims |
| G5 | Secrets hygiene: withdrawals disabled on keys; secrets not in git/logs/prompts; rotation drill |
| G6 | Legal/product eligibility for live product cited from primary sources (**UNVERIFIED** until then) |

---

## 7. UI observability hooks (design only)

Future professional UI will consume — **do not build UI now**:

**Events (examples):**
- `collector.gap_detected`, `collector.reconnect`, `bar.closed`  
- `regime.changed`, `strategy.signal`, `risk.reject`, `risk.kill_daily`  
- `order.submitted|ack|reject|cancel|fill`  
- `account.snapshot`, `pnl.mark_to_market`  
- `system.heartbeat`, `system.degraded`

**Metrics (examples):**
- `md_receive_lag_ms`, `sequence_gap_count`, `ws_connected`  
- `open_position_notional`, `equity_eur`, `daily_pnl_pct`  
- `orders_rejected_total{reason=…}`, `funding_paid_eur`  
- `expectancy_after_costs` (batch research metric, not live claim)

**Linkage:** Every bot/strategy decision carries `run_id`, `config_hash`, `symbol`, `venue` so UI can interlink activity timelines with number feeds.

---

## 8. Execution & cost model (paper / backtest)

**ENGINEERING RECOMMENDATION** defaults (tune with venue fee schedules — fee numbers **UNVERIFIED** until docs):

- Fill: conservative — e.g. touch adverse side of spread + slippage buffer; no magic mid fills on marketable orders.  
- Fees: maker/taker from schedule; assume taker until proven otherwise for breakout entries.  
- Funding: apply at venue funding timestamps to open notional.  
- Partial fills / rejects: model queue risk; one position rule simplifies inventory.  
- Liquidation: if isolated margin model available, simulate maintenance margin; else treat unknown as **fail research run**.  
- Liquidity cap: size cannot exceed a fraction of recent traded volume / book depth (**HYPOTHESIS**: e.g. ≤1% of trailing 15m volume — calibrate later).

Sizing remains risk-first per L14.

---

## 9. Universe scaling path

1. **Phase A:** One liquid BTC perpetual — full plumbing. **[VERIFIED — L6]**  
2. **Phase B:** Add meme/AI/tech perps only if they pass gates: min ADV, max spread, max |funding|, status=trading, data quality green. Thresholds = **HYPOTHESIS** until calibrated.  
3. Still **one directional position at a time** across the book (not one per symbol). **[VERIFIED — L9]**

---

## 10. Security & ops (Phase 1 relevant)

- No live secrets in repo; `.env` / secret manager only later; never log keys. **[VERIFIED — L11]**  
- Withdrawals disabled on any trading key.  
- UTC clocks; NTP on hosts.  
- Docker for reproducible research/collector images (**ENGINEERING RECOMMENDATION**).  
- Assistants may propose code/PRs; humans approve merges and any credential use. **[VERIFIED — L10]**

---

## 11. Technology baseline

| Item | Choice | Label |
|------|--------|-------|
| Language | Python 3.12 | ENGINEERING RECOMMENDATION |
| Packaging | Git + Docker | ENGINEERING RECOMMENDATION |
| Analytics store | Parquet | ENGINEERING RECOMMENDATION |
| Metrics | Prometheus exposition or OTel — pick in impl | ENGINEERING RECOMMENDATION |
| Message bus | Optional later (NATS/Kafka); start with files + DB | ENGINEERING RECOMMENDATION |

---

## 12. Out of scope (Phase 1)

Live trading, full UI, ranging strategies, IB/CME integration beyond noting optional later, guaranteed profit, HFT co-lo, copy-trading, social signals as primary edge (**HYPOTHESIS** rejected for v1).
