# 23 — Gated OKX EEA tiny-live (manual far-limit + cancel)

**Stance:** `not_a_forecast: true`. **Not Phase C.** **Not a weekday auto-trade routine.** Manual far-limit + cancel only, on a box that already has live keys. Default remains **fail-closed**.

Universe for this smoke: **live SPOT DOGE-USDC**. On this EEA live key, **USDT cannot be added to the Crypto allowlist**; `DOGE-USDT` returned **50123**. The successful far-limit+cancel was **DOGE-USDC** (did not fill; not Phase C). Override with `--inst-id` only if another quote is allowlisted. BTC EMA observer (`phase1/21`) and Phase A DOGE 15m demo loop are **unchanged**. `config/default.yaml` breakout params are **unchanged**.

## What “tiny-live” is

A second, explicit opt-in on `OkxEeaClient` so Atlas can later run **one** SELL of ~10 DOGE at **2× last** (must not fill) and immediately **cancel**. Never market. Never asset transfer.

| Gate | Default | Tiny-live |
|---|---|---|
| `mode=live` + `allow_trade=True` | `LiveTradingBlocked` **at init** | still blocked unless `tiny_live=True` too |
| `tiny_live=True` without `allow_trade` | blocked at init | — |
| Live GET (balance, config, positions, pending, funding `GET /api/v5/asset/balances`) | allowed | allowed |
| Live trade POST | blocked before HTTP | only if **all** of: `mode=live` **and** `allow_trade=True` **and** `tiny_live=True` **and** notional cap |
| Estimated notional | n/a | `float(sz)*float(px)` ≤ **20** (EUR≈USDT). Missing `instId`/`sz`/`px` → fail closed, no HTTP |
| Market / transfer / set-leverage / batch | blocked | still blocked |

## How Atlas will run it (manual)

On the box with **live** keys (never commit those files; never print them):

```bash
# Read-only snapshot (trading balance, funding balances, DOGE-USDC ticker, pending)
python scripts/okx_tiny_live_smoke.py

# Mutating ONLY if BOTH flags are set: SELL sz=10 DOGE, px=2× last, then cancel same ordId
python scripts/okx_tiny_live_smoke.py --place-far-limit --cancel
# Optional override if a different quote is allowlisted:
# python scripts/okx_tiny_live_smoke.py --inst-id DOGE-USDT --place-far-limit --cancel
```

Refuse if available DOGE < `sz` or notional > 20. Account shape: **~281 DOGE** on trading, funding empty, no positions — SELL ~10 DOGE far-limit then cancel on **DOGE-USDC**.

Do **not** install a cron / Grok Bot routine from this document.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading strategy.
- Not a replacement for Phase A BreakoutV1 / DOGE demo.
- Not a change to the daily EMA paper observer.
- Not permission to send market orders or move funds off the trading account.

`not_a_forecast: true`. Default still `LiveTradingBlocked` unless `tiny_live` + cap.
