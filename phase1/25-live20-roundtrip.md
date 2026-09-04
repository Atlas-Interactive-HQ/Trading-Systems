# 25 — Manual €20 DOGE-USDC practice round-trip (tiny-live)

**Stance:** `not_a_forecast: true`. **Not Phase C.** **Not a weekday auto-trade routine.** Manual practice only, on a box that already has live keys. Default remains **fail-closed**. `TINY_LIVE_NOTIONAL_CAP` stays **20**. Market orders stay blocked. Never asset transfer / withdraw.

Keep `scripts/okx_tiny_live_smoke.py` (far-limit + cancel). This sibling is for a **fill** sell then buy-back under the same gate.

## Practice lane vs EMA week vs €200 gate

| Lane | What it is | Orders | Book |
|---|---|---|---|
| EMA week / observer | BTC-USDT 1D long/flat journals | **None** | paper €200 research |
| €200 paper eval | Donchian / EMA / breakout named windows | **None** (sim) | €200 |
| Tiny-live smoke | Far-limit SELL + **cancel** (must not fill) | live POST iff tiny_live+cap | ~10 DOGE |
| **live20 round-trip** | Aggressive **limit** SELL to fill, then **limit** BUY back | same tiny_live gate; ≤ €20 | first practice prefer ≤ €10 (`--sz 50` on DOGE-USDC) |

## Allowlist

On this EEA live key, **USDT cannot be added to Crypto**. `DOGE-USDT` returned **50123**. Default inst is **DOGE-USDC**. Override `--inst-id` only if another quote is allowlisted.

Account shape: ~281 DOGE on trading, often **0 USDC until after a sell fill**. Funding empty. No positions.

## How to run (Atlas, on the keyed box — not CI)

```bash
# Read-only snapshot (trading+funding, ticker, pending, avail DOGE/USDC)
python scripts/okx_tiny_live_roundtrip.py

# First practice: sell ~50 DOGE at/near bid, then buy-back at/near ask if USDC appears
python scripts/okx_tiny_live_roundtrip.py --roundtrip --sz 50

# Legs separately
python scripts/okx_tiny_live_roundtrip.py --sell-fill --sz 50
python scripts/okx_tiny_live_roundtrip.py --buy-back
```

`--max-notional` defaults to **10** (first practice). Hard client cap remains **20**. Timeout cancels leftovers. Journals: `data/live20/YYYY-MM-DD/events.jsonl` (gitignored). Issues log (local): `data/reports/live-20-issues.md` — tracked template: [`live-20-issues.md`](./live-20-issues.md).

Do **not** install a cron / Grok Bot routine from this document.

## What this is not

- Not a Phase C recommendation.
- Not permission to raise the €20 cap or send market orders.
- Not a replacement for the EMA observer or Phase A DOGE 15m.
- Not a default in `config/default.yaml`.

`not_a_forecast: true`. Default still fail-closed unless explicit flags + tiny_live + cap.
