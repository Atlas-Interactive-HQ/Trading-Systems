# 03 — Exchange-Neutral Data Schemas

**Convention:** All timestamps are **UTC**. Prefer integer epoch **milliseconds** unless noted.  
**Common columns on almost every fact table:** `venue`, `symbol` (neutral id), `sequence` (venue seq if any, else local monotonic), `exchange_ts`, `receive_ts`, `schema_version`.  
**Types:** logical types below; physical Parquet mapping recommended in notes.

---

## 0. Shared enums & identifiers

| Field | Type | Notes |
|-------|------|-------|
| `venue` | string/enum | e.g. `kraken_deriv`, `okx` — stable codes |
| `symbol` | string | Neutral: e.g. `BTC-USD-PERP` — map from venue instrument id in normalize |
| `venue_instrument_id` | string | Raw exchange product id (keep for joins) |
| `sequence` | int64 | Exchange channel sequence if provided; else collector-assigned monotonic per stream |
| `exchange_ts` | int64 (ms) | Event time from exchange payload (or null if absent) |
| `receive_ts` | int64 (ms) | Local UTC time when bytes received |
| `ingest_run_id` | string | Collector run id |
| `schema_version` | string | e.g. `market.quote.v1` |

**Clock skew note:** `receive_ts - exchange_ts` is a first-class DQ signal (see `05`).

---

## 1. Market

### 1.1 `market.quote` (top of book / BBO)

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol, venue_instrument_id | string | |
| sequence | int64 | |
| exchange_ts, receive_ts | int64 ms | |
| bid_px | float64 | Best bid |
| bid_sz | float64 | Size in base (or contracts — document unit in metadata) |
| ask_px | float64 | Best ask |
| ask_sz | float64 | |
| spread | float64 | Derived: ask_px - bid_px (store or compute) |
| mid_px | float64 | Derived optional |
| is_crossed | bool | bid_px >= ask_px |
| raw_msg_ref | string | Pointer/hash into raw store |

### 1.2 `market.trade`

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol, venue_instrument_id | string | |
| sequence | int64 | |
| exchange_ts, receive_ts | int64 ms | |
| trade_id | string | Exchange trade id if any |
| px | float64 | |
| sz | float64 | |
| side | enum | `buy` / `sell` / `unknown` (aggressor if known) |
| is_estimated | bool | True if synthetic from candle (should be rare) |

### 1.3 `market.mark`

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol, venue_instrument_id | string | |
| sequence | int64 | |
| exchange_ts, receive_ts | int64 ms | |
| mark_px | float64 | Mark price for PnL / liq |
| source | string | e.g. `exchange_mark` |

### 1.4 `market.index`

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol_or_index_id | string | Index may differ from perp symbol |
| sequence | int64 | |
| exchange_ts, receive_ts | int64 ms | |
| index_px | float64 | |

### 1.5 `market.funding`

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol, venue_instrument_id | string | |
| sequence | int64 | |
| exchange_ts, receive_ts | int64 ms | |
| funding_rate | float64 | As published (document period: 1h/8h etc. — **UNVERIFIED** per venue) |
| funding_ts | int64 ms | Time funding applies / next funding time |
| mark_px_at_funding | float64 | nullable |
| predicted | bool | True if predicted vs settled |

### 1.6 `market.status`

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol, venue_instrument_id | string | |
| sequence | int64 | |
| exchange_ts, receive_ts | int64 ms | |
| status | enum | `trading`, `halted`, `auction`, `settle`, `delisted`, `unknown` |
| suspend_reason | string | nullable |
| min_qty, tick_size, contract_value | float64 | nullable contract meta snapshots |

### 1.7 `market.bar` (derived)

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol | string | |
| timeframe | enum | `15m`, `1h`, … |
| bar_open_ts, bar_close_ts | int64 ms | UTC; bar closed only when `closed=true` |
| open, high, low, close, volume | float64 | |
| trade_count | int64 | nullable |
| vwap | float64 | nullable |
| closed | bool | **Must be true** before strategy use |
| build_version | string | Code version for replay |

---

## 2. Execution

### 2.1 `execution.order`

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol | string | |
| client_order_id | string | Idempotent; atlas-generated |
| venue_order_id | string | nullable until ack |
| sequence | int64 | Local or venue |
| exchange_ts, receive_ts | int64 ms | |
| side | enum | `buy` / `sell` |
| ord_type | enum | `limit`, `market`, `stop`, `stop_limit`, … |
| tif | enum | `gtc`, `ioc`, `fok`, … |
| px | float64 | nullable for market |
| stop_px | float64 | nullable |
| qty | float64 | |
| reduce_only | bool | |
| isolated | bool | Prefer true when supported |
| leverage | float64 | Requested |
| state | enum | `created`, `sent`, `ack`, `partial`, `filled`, `canceled`, `rejected` |
| reject_reason | string | nullable |
| strategy_id, run_id, config_hash | string | Traceability |
| paper | bool | Always true until live gate |

### 2.2 `execution.ack` / `execution.cancel` / `execution.fill`

**Ack**

| Field | Type | Notes |
|-------|------|-------|
| client_order_id, venue_order_id | string | |
| exchange_ts, receive_ts, sequence | | |
| ack_state | enum | `accepted`, `rejected` |
| message | string | |

**Cancel**

| Field | Type | Notes |
|-------|------|-------|
| client_order_id, venue_order_id | string | |
| exchange_ts, receive_ts, sequence | | |
| cancel_source | enum | `user`, `system`, `kill`, `venue` |
| success | bool | |

**Fill**

| Field | Type | Notes |
|-------|------|-------|
| client_order_id, venue_order_id, trade_id | string | |
| exchange_ts, receive_ts, sequence | | |
| px, qty | float64 | |
| fee_amount | float64 | |
| fee_ccy | string | |
| liquidity | enum | `maker`, `taker`, `unknown` |
| is_snapshot_synth | bool | True if reconstructed — flag for DQ |

---

## 3. Account

### 3.1 `account.position`

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol | string | |
| exchange_ts, receive_ts, sequence | | |
| side | enum | `flat`, `long`, `short` |
| qty | float64 | Absolute size; 0 if flat |
| entry_px | float64 | nullable if flat |
| leverage | float64 | |
| isolated | bool | |
| unrealized_pnl | float64 | |
| liquidation_px | float64 | nullable |
| margin_used | float64 | |
| atlas_one_position_ok | bool | Derived: at most one directional across book |

### 3.2 `account.margin` / balances

| Field | Type | Notes |
|-------|------|-------|
| venue, ccy | string | e.g. EUR, USDT — **confirm paper ccy UNVERIFIED** |
| exchange_ts, receive_ts, sequence | | |
| equity | float64 | |
| available | float64 | |
| margin_balance | float64 | |
| paper_equity_scale | float64 | Expected ~200 for Phase 1 paper |

### 3.3 `account.pnl`

| Field | Type | Notes |
|-------|------|-------|
| venue, symbol | string | nullable for portfolio row |
| ts | int64 ms | Snapshot time (UTC) |
| realized_pnl | float64 | |
| unrealized_pnl | float64 | |
| fees | float64 | Cumulative period |
| funding | float64 | Cumulative period |
| pnl_after_costs | float64 | realized + unrealized - fees - funding (define period) |
| daily_pnl_pct | float64 | Vs day-start equity; drives 5% kill |

---

## 4. Strategy / risk decisions

### 4.1 `strategy.decision`

| Field | Type | Notes |
|-------|------|-------|
| run_id, config_hash, strategy_id | string | |
| venue, symbol | string | |
| bar_close_ts | int64 ms | Decision on **closed** bar only |
| exchange_ts, receive_ts, sequence | | Decision emit times |
| timeframe | enum | `15m` exec / context |
| regime | enum | `breakout_tradeable`, `untradeable`, `ranging_disabled` |
| signal | enum | `enter_long`, `enter_short`, `exit`, `flat`, `none` |
| stop_px | float64 | |
| stop_distance_fraction | float64 | \|entry-stop\|/entry |
| reason_codes | list[string] | Explainability for UI |
| look_ahead_safe | bool | Assert true in replay audits |

### 4.2 `risk.decision`

| Field | Type | Notes |
|-------|------|-------|
| run_id, strategy_decision_id | string | |
| exchange_ts, receive_ts, sequence | | |
| equity | float64 | |
| risk_budget | float64 | € from 1–2% rule |
| leverage_cap | float64 | min(default 2, hard 5, venue) |
| liquidity_cap | float64 | |
| notional_approved | float64 | Result of sizing formula |
| notional_raw_signal | float64 | Before caps |
| action | enum | `approve`, `reject`, `kill_daily`, `halt_stale` |
| reject_reasons | list[string] | e.g. `daily_kill`, `one_position`, `regime_untradeable`, `ranging_disabled` |

**Sizing (authoritative):**  
`notional = min(risk_budget / stop_distance_fraction, leverage_cap * equity, liquidity_cap)`

---

## 5. System health

### 5.1 `system.health`

| Field | Type | Notes |
|-------|------|-------|
| component | string | `collector.kraken`, `risk`, … |
| ts | int64 ms | receive/local UTC |
| status | enum | `ok`, `degraded`, `down` |
| md_lag_ms | int64 | nullable |
| last_sequence | int64 | |
| gap_count_1h | int64 | |
| ws_connected | bool | |
| detail | string | Free text / JSON |

### 5.2 `system.event` (UI hook stream)

| Field | Type | Notes |
|-------|------|-------|
| event_id | string | UUID |
| ts | int64 ms | UTC |
| event_type | string | See technical design §7 |
| severity | enum | `info`, `warn`, `error`, `critical` |
| payload_json | string | Structured; no secrets |
| run_id, venue, symbol | string | nullable linkage |

---

## 6. Raw preservation pointer

| Field | Type | Notes |
|-------|------|-------|
| raw_path | string | Object key / file path |
| byte_offset | int64 | optional |
| content_hash | string | sha256 of message |
| venue, channel | string | |
| receive_ts | int64 ms | |

Normalized rows should reference raw for dispute / replay.

---

## 7. Engineering recommendations

- Enforce schemas with Pydantic or Pandera at write boundary.  
- Partition Parquet by `venue/symbol/date` (UTC date).  
- Never overwrite; late data → new partition file + catalog entry.  
- Unit conventions (`sz` in base vs contracts) must be fixed per venue in metadata — **UNVERIFIED** until contract specs read.
