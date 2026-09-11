# 95 — HFT liquidity-gate plan (P4)

**Stance:** Research / capture plan. `not_a_forecast: true`. **NO strategy PnL.**
**Config:** `config/default.yaml` **untouched**.
**Live:** HALTED. Public MD only.

A 24h simultaneous capture **cannot run in this PR**. This note is plan + schema + runner sketch. **No invented capture numbers.**

---

## Goal

Before choosing an HFT instrument, capture the **same** public channels for **24h** on BTC + ETH + DOGE EEA X-Perp **simultaneously**. Compare liquidity / health only. Lock the instrument via a **pre-registered** rule **before** any alpha score.

---

## Channels (same as Layer B)

`books5` · `trades` · `mark-price` · `funding-rate`

---

## Instrument resolution

Do **not** invent an ETH instId.

| Base | Hint (phase1/07, 2026-09-01 — re-resolve live) |
|------|------------------------------------------------|
| BTC | `BTC-USD_UM_XPERP-310404` |
| DOGE | `DOGE-USD_UM_XPERP-310404` |
| ETH | **None** — resolve from `GET /api/v5/public/instruments?instType=FUTURES` (`ruleType=xperp`, `state=live`) |

Code: `atlas.scalp_hft.liquidity_gate.resolve_liquidity_inst_ids` (uses `pick_for_base`). Missing ETH → fail closed.

Sketch:

```bash
# 1) resolve (read-only public instruments)
python scripts/run_hft_liquidity_gate_capture.py --resolve-instruments

# 2) after ids are live, a *future* 24h job (not this PR):
python scripts/run_okx_public.py --capture --ws-only --duration-sec 86400 \
  --inst-id <resolved-BTC> --inst-id <resolved-ETH> --inst-id <resolved-DOGE>
```

`--inst-id` is already repeatable on `scripts/run_okx_public.py`. Do not start the 24h job from this PR.

---

## Metric schema (compare only these)

| Field | Definition |
|-------|------------|
| `trades_per_sec` | public trades events / span seconds |
| `books5_changes_per_sec` | books5 updates / span seconds |
| `spread_bps_median` / `spread_bps_p95` | `(ask-bid)/mid * 1e4` |
| `top5_depth_notional_median` / `p95` | sum of top-5 bid+ask notional |
| `reconnect_count` | `ws_error` `gap_reason=ws_reconnect` |
| `gap_count` | other `is_gap` sidecars (not books5 `seqId` skips) |
| `book_age_ms_median` / `p95` | decision ts − last books5 exchange ts (P1 semantics) |
| `n_health_stale` / `n_carried_forward` | P1 split |

`METRIC_FIELDS` is locked in `atlas.scalp_hft.liquidity_gate`. No expectancy, no fills, no soft-PASS.

---

## Pre-registered selection rule (before any capture)

Registered **now**, before numbers exist:

1. Resolve live BTC/ETH/DOGE X-Perp (fail closed if any missing).
2. Capture 24h simultaneously.
3. Eligible iff `trades/sec > 0` AND `books5 changes/sec > 0` AND median `book_age_ms ≤ 1000` AND reconnect count is not worse than **2×** the three-name median.
4. Among eligible: highest `books5_changes_per_sec`; tie-break lower median spread bps, then higher median top-5 depth notional.
5. If none eligible → **no HFT instrument** (fail closed). Do not default to DOGE because Layer B already exists there.

`select_instrument([])` returns `insufficient_data` — that is the state of this PR.

---

## Honesty

- Do not pick the instrument that would have made a paper strategy look green.
- Do not invent ETH or 24h rates.
- H1 ([`96`](./96-hft-h1-ensemble-lock.md)) waits on this lock **and** P1 health **and** multi-day Layer B.

`not_a_forecast: true`. `place_orders: false`.
