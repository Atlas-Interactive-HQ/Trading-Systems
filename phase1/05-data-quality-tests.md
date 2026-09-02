# 05 — Data Quality Test Plan

**Purpose:** Concrete, automatable checks before research or paper trading trusts a feed.  
**Fail mode:** Regime → **untradeable** / collector **degraded**; do not silently trade on bad data.  
**Thresholds marked HYPOTHESIS** are starting points — calibrate on BTC first.

---

## 1. Test layers

| Layer | When | Gate |
|-------|------|------|
| L0 Streaming | Live collector | Alert + degrade within seconds–minutes |
| L1 Batch hourly/daily | After Parquet land | CI/nightly report; block research partitions |
| L2 Research preload | Before backtest/replay | Hard fail if critical checks red |
| L3 Paper runtime | During paper OMS | Same as L0 + reconcile |

---

## 2. Catalog of tests

### 2.1 Sequence & completeness

| ID | Test | Method | Severity | Notes |
|----|------|--------|----------|-------|
| SEQ-01 | Sequence gaps | Diff consecutive `sequence` where venue provides seq | CRITICAL | Write gap ledger |
| SEQ-02 | Sequence rewind | sequence decreases | CRITICAL | Possible reconnect desync / bug |
| SEQ-03 | Duplicate messages | Hash(payload) or (trade_id) duplicates within window | HIGH | Dedupe policy explicit |
| SEQ-04 | Quiet gap vs expected activity | No trades/quotes for T_stale | HIGH | BTC T_stale **HYPOTHESIS** e.g. 60–120s; alts higher |
| SEQ-05 | Bar coverage | Every 15m/1h slot exists or explicitly marked holiday/halt | HIGH | Crypto 24/7 — missing bar usually bad |
| SEQ-06 | Raw vs normalized count drift | \|raw_msgs - normalized_rows\| beyond parse-fail budget | HIGH | |

### 2.2 Clocks & skew

| ID | Test | Method | Severity | Notes |
|----|------|--------|----------|-------|
| CLK-01 | `receive_ts` not before deploy epoch / not in future > slack | Bounds check | CRITICAL | Clock jump |
| CLK-02 | `exchange_ts` null rate | % null | MEDIUM | Document if channel lacks ts |
| CLK-03 | Skew `receive_ts - exchange_ts` | p50/p99 distribution | HIGH | Alert if p99 > **HYPOTHESIS** 2–5s (non-HFT) |
| CLK-04 | Negative skew large | exchange_ts >> receive_ts | HIGH | Exchange clock or parse unit error (s vs ms) |
| CLK-05 | Server time REST vs local | Periodic poll | MEDIUM | NTP health |
| CLK-06 | Bar boundary alignment | bar_open_ts % timeframe == 0 (UTC) | HIGH | |

### 2.3 Book / quote integrity

| ID | Test | Method | Severity | Notes |
|----|------|--------|----------|-------|
| BK-01 | Crossed book | bid_px >= ask_px | HIGH | Flag `is_crossed`; untradeable while crossed persists |
| BK-02 | Locked book | bid == ask | MEDIUM | May be valid briefly; track duration |
| BK-03 | Absurd spread | spread/mid > X bps | HIGH | BTC X **HYPOTHESIS** e.g. 50–100 bps; alts tighter gate for eligibility |
| BK-04 | Non-positive sizes | bid_sz/ask_sz ≤ 0 | HIGH | |
| BK-05 | Tick size violations | px not on tick grid | MEDIUM | Needs instrument meta (**UNVERIFIED** until meta collected) |
| BK-06 | Spike vs prior mid | \|Δmid\|/mid > Y in one update | MEDIUM | Could be real wick — don’t auto-delete; flag |

### 2.4 Trades

| ID | Test | Method | Severity | Notes |
|----|------|--------|----------|-------|
| TR-01 | Non-positive px/sz | | CRITICAL | |
| TR-02 | Trade outside recent BBO band | px << bid or >> ask by Z | MEDIUM | Print vs book desync |
| TR-03 | Duplicate trade_id | | HIGH | |
| TR-04 | Out-of-order exchange_ts | within stream | MEDIUM | Buffer/reorder policy |
| TR-05 | Volume explosion | 15m volume > K × median | MEDIUM | Meme risk; gate symbol |

### 2.5 Mark / index / funding / status

| ID | Test | Method | Severity | Notes |
|----|------|--------|----------|-------|
| FU-01 | Missing funding near expected time | No funding update in window | HIGH | Period **UNVERIFIED** per venue |
| FU-02 | Absurd funding rate | \|rate\| > F | HIGH | F **HYPOTHESIS**; block new entries |
| FU-03 | Mark vs mid divergence | \|mark-mid\|/mid > D | HIGH | Contagion / bad mark |
| FU-04 | Index missing | | MEDIUM | |
| ST-01 | Status not trading | | CRITICAL for entries | Force flat/untradeable |
| ST-02 | Status flapping | >N toggles/hour | HIGH | |

### 2.6 Derived bars & joins

| ID | Test | Method | Severity | Notes |
|----|------|--------|----------|-------|
| BR-01 | OHLC consistency | low ≤ open,close ≤ high; low ≤ high | CRITICAL | |
| BR-02 | Lookahead leak | Feature uses bar with `closed=false` or future ts | CRITICAL | Unit test in replay |
| BR-03 | Funding join lookahead | Funding with `funding_ts` after bar_close used in that bar | CRITICAL | |
| BR-04 | Determinism | Same raw → same bar hash | CRITICAL | |

### 2.7 Multi-symbol / scaling

| ID | Test | Method | Severity | Notes |
|----|------|--------|----------|-------|
| MS-01 | BTC stream priority | Under load, BTC lag ≤ alt lag | HIGH | |
| MS-02 | Eligibility gate inputs present | spread, ADV, funding, status for each alt | HIGH | Else cannot trade alt |
| MS-03 | Partition leak | Symbol A data in symbol B paths | CRITICAL | |

### 2.8 Security / hygiene (data path)

| ID | Test | Method | Severity | Notes |
|----|------|--------|----------|-------|
| SEC-01 | No secret material in raw payloads logged to git | Grep CI | CRITICAL | |
| SEC-02 | Paper flag consistency | execution rows `paper=true` pre-gate | CRITICAL | |

---

## 3. Suggested initial thresholds (HYPOTHESIS — calibrate)

| Symbol class | Max spread (bps) | Stale quote (s) | Max \|funding\| (per period) | Notes |
|--------------|------------------|-----------------|------------------------------|-------|
| BTC liquid perp | 50 | 120 | venue-dependent | Start here |
| Meme/AI/tech perp | 30–80 (stricter ADV) | 180 | lower absolute notional | Often worse books |

Document calibrated values in `configs/` with date.

---

## 4. Automation sketch

```text
atlas quality run --venue okx --symbol BTC-USD-PERP --date 2026-08-31
→ JSON + Markdown report
→ exit code ≠ 0 if any CRITICAL or HIGH count > budget
```

Emit `system.event` for each CRITICAL for future UI.

---

## 5. Pass criteria for paper strategy enablement

- Last **7 UTC days** BTC: no open CRITICAL; HIGH waivers written.  
- SEQ/CLK/BR lookahead tests green on replay sample.  
- Funding coverage ≥ agreed % of expected prints.  
- Crossed-book persistent episodes investigated.

Alts: each symbol must pass its own gate set before first paper order on that symbol.
