# 21 — EMA paper observer (forward journals)

**Stance:** Research / paper observer. `not_a_forecast: true`. **Observer only. No exchange orders.** OOS CLEAR on historical 2022-bear / 2023-chop **≠ live** and **≠ Phase C**. Does **not** replace Phase A DOGE breakout. Do not headline PnL.

Locked rule (same as `phase1/19` / `20`): **EMA(12) / EMA(30) daily**, long iff 12 > 30 else **flat**, never short. Signal at confirmed close, hypothetical fill at **next open**. Asset: **BTC-USDT** public OKX EEA 1D (no keys). Book: **€200**, **1×**, fee+slip from existing `PaperSettings`.

## How this differs from Phase A DOGE

| | Phase A DOGE | EMA paper observer |
|---|---|---|
| Script | `scripts/run_doge_demo_session.py` | `scripts/run_ema_paper_session.py` |
| Strategy | BreakoutV1 15m L+S | `ema_long_flat_v1` 1D long/flat |
| Asset | DOGE-USD spot + X-Perp | BTC-USDT 1D public MD |
| Journals | `data/oms/` | `data/ema/` (`source=ema-paper-observer`) |
| Orders | default signal-only; `--place-demo-orders` is a **demo** path | **never** — no trade client, no `--place-demo-orders` |
| Dashboard | default / `--oms` | `--ema` |
| Status | Phase A (untouched by this lane) | Forward observer for journals, not a live gate |

Phase A scripts, routines, and `config/default.yaml` breakout params are **not** changed here. `data/shadow/` remains Phase B would-place/blocked on the breakout family.

## How to run

```bash
cd Trading-Systems
source .venv/bin/activate
pip install -e ".[dev]"

# Signal/state only (default). Public 1D BTC-USDT. Appends data/ema/{UTC-date}/*.jsonl
python scripts/run_ema_paper_session.py

# Optional 1× paper shadow: hypothetical next-open fills, ledger at data/ema/state.json
python scripts/run_ema_paper_session.py --paper-shadow

# Read-only UI over EMA journals (keep --oms / --replay / --shadow / --fixtures)
python scripts/run_dashboard.py --ema
```

Stdout is a JSON snapshot: `desired` (`long`|`flat`), `ema_fast`, `ema_slow`, `last_close`, `as_of_bar_ts_*`, `place_orders: false`, `not_a_forecast: true`. No venue order is placed.

### Sample journal paths (gitignored)

```
data/ema/2026-09-03/decisions.jsonl   # ema_decision, ema_state
data/ema/2026-09-03/events.jsonl      # session start/end; optional ema_paper_fill
data/ema/state.json                   # only with --paper-shadow (1× ledger, no paper_pnl hero)
```

Every row is tagged `source=ema-paper-observer`. Distinct from `data/oms/` and `data/shadow/`. `data/` stays gitignored.

`--paper-shadow` is **not** Phase B shadow-replay and **not** Phase C. It starts *forward* from the first shadow run (no historical backfill). Pending from a closed bar fills at the **next** bar’s **open** (no same-bar lookahead). Re-running on the same last closed bar does not double-fill.

## Dashboard

`python scripts/run_dashboard.py --ema` reads `data/ema/` only. `/eval` also shows a read-only observer section (current desired + recent decisions) when those journals exist. **No PnL hero.** Existing `--oms` (default), `--replay`, `--shadow`, `--fixtures` are unchanged.

## Suggested cron (document only — do not install a Grok Bot routine from this PR)

OKX 1D bars confirm after the UTC daily close. Add a buffer so the last candle is closed, then run weekdays (or daily):

```cron
# ~00:15 UTC weekdays — observer only, never orders. Adjust path/user.
15 0 * * 1-5  cd /path/to/Trading-Systems && .venv/bin/python scripts/run_ema_paper_session.py
# Optional 1× hypothetical ledger:
# 15 0 * * 1-5  cd /path/to/Trading-Systems && .venv/bin/python scripts/run_ema_paper_session.py --paper-shadow
```

Kaje / Atlas: paste this into the host crontab (or an existing scheduler) if you want unattended forward journals. **Do not** create a Grok Bot routine unless explicitly asked.

## What this is not

- Not a Phase C recommendation.
- Not a live-trading recommendation.
- Not a replacement for Phase A BreakoutV1 / DOGE demo.
- Not a PASS vs the breakout baseline (different family).
- Historical OOS CLEAR (`phase1/20`) is **not** a live gate.
- `--paper-shadow` fills are hypothetical; they never hit OKX.

`not_a_forecast: true`. Observer only. No orders. Phase A DOGE untouched.
