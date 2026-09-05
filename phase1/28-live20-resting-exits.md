# 28 — Manual live20 resting limit exits (TP / protect-limit)

**Stance:** `not_a_forecast: true`. **Not Phase C.** **Not a weekday auto-TP routine.** Manual practice only, on a box that already has live keys. Default remains **fail-closed**. `TINY_LIVE_NOTIONAL_CAP` stays **20**. Market orders stay blocked. Never asset transfer / withdraw.

Sibling of [`25-live20-roundtrip.md`](./25-live20-roundtrip.md). Round-trip is an aggressive limit fill then buy-back (timeout **cancels** leftovers). This script places a **resting** limit SELL and **leaves it** (does not auto-cancel).

Context: a long DOGE position with **no resting order** cannot “hit” a target. This lane lets Atlas park a limit take-profit (and optionally a protective *limit*, not a stop) under the same tiny_live gate.

## TP vs protect-limit

| Flag | Side | Price rule | What it is | What it is **not** |
|---|---|---|---|---|
| `--place-tp` | limit **SELL** | `--px` **above mid**, or `--tp-pct` % above mid | Resting take-profit. Left on the book. | Not a market order. Not an algo/stop. |
| `--place-protect-limit` | limit **SELL** | `--px` **below mid** | GTC limit only. Left on the book. | **Not** an exchange stop. **Not** market. If `px` is at/below bid it may **fill immediately**. |

Both require `--sz N`. Notional `sz * px` must be ≤ `--max-notional` (script default 10) and ≤ client cap **20**. Incomplete flags → **no POST**.

`--place-tp` and `--place-protect-limit` together: `--tp-pct` for the TP and `--px` for the protect (one `--px` cannot be both above and below mid).

## Cancel

| Flag | Effect |
|---|---|
| `--cancel-ord <ordId>` | Cancel that order (`instId` default DOGE-USDC) |
| `--cancel-all-pending` | Cancel pending SPOT orders for **this inst only** (default DOGE-USDC) |

## How to run (Atlas, on the keyed box — not CI, not this agent)

```bash
# Read-only: balances, DOGE-USDC ticker, pending
python scripts/okx_tiny_live_exit.py

# Resting TP 5% above mid, 50 DOGE, leave on the book
python scripts/okx_tiny_live_exit.py --place-tp --tp-pct 5 --sz 50

# Resting TP at an absolute px (must be above mid)
python scripts/okx_tiny_live_exit.py --place-tp --px 0.15 --sz 50

# Protective LIMIT (NOT a stop) below mid — may fill immediately if px ≤ bid
python scripts/okx_tiny_live_exit.py --place-protect-limit --px 0.10 --sz 50

# Cancel
python scripts/okx_tiny_live_exit.py --cancel-ord 1234567890
python scripts/okx_tiny_live_exit.py --cancel-all-pending
```

Client POSTs only if `tiny_live=True` **and** `allow_trade=True` **and** `mode=live` **and** notional ≤ 20. The script sets those only when a mutate flag is present. Journals: `data/live20/YYYY-MM-DD/events.jsonl` tagged `source=live20-resting-exits` (gitignored).

Do **not** install a cron / Grok Bot / weekday auto-TP from this document. Round-trip practice remains [`25`](./25-live20-roundtrip.md). Chart remains `python scripts/run_dashboard.py --live20` (GET-only; does not place or cancel).

## What this is not

- Not a Phase C recommendation.
- Not a weekday auto-TP or auto-stop routine.
- Not permission to raise the €20 cap or send market orders.
- Not an OKX stop / algo / OCO / trailing order.
- Not a replacement for the EMA observer or Phase A DOGE 15m.

`not_a_forecast: true`. Default still fail-closed unless explicit flags + tiny_live + cap.
