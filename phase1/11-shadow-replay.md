# 11 — Phase B shadow replay

**Stance:** Paper/research. No live orders. No demo orders. No auto-demo. No profitability claim.  
**Date:** 2026-09-02

Shadow sits **after** historical replay (Phase A accelerator) and **before** gated micro-demo (Phase C). It applies the locked paper book to the same breakout signals and journals **would-place vs blocked**. It does not place.

## What it does

1. Loads the last `data/replay/` summary (candidate window timestamps). If missing, runs `replay_phase_a_history.py` match first. Does not invent bars.
2. Walks closed 15m bars with `PaperEngine` sequencing (no lookahead): pending fill at next open → stop vs OHLC → time-stop → UTC-day kill → then signal.
3. Sizing is `atlas.paper.risk.size_order` / `gate_new_entry` on the **€200** book (not faucet equity). Daily kill 5%, per-trade 1–2%, one position, X-Perp isolated ≤2x.
4. Journals under `data/shadow/` tagged `source=shadow-replay`. Distinct from `data/oms/` and `data/replay/`.

Blocked reasons: `one_position` | `kill` | `size` | `no_signal` | …

Hypothetical fills (fee+slip already in paper settings) update a paper ledger for research only. Labelled `not_a_forecast: true`. **Do not headline PnL.**

## What it is not

| | Shadow (B) | Gated micro-demo (C) |
|--|------------|----------------------|
| Orders | Never | Auto-place only under gates + explicit yes |
| Book | €200 paper ledger | OKX EEA demo matching engine |
| Journals | `data/shadow/` | `data/oms/` |
| Meaning | How many replay signals survive risk | Live demo fills ≈ shadow |

Replay/shadow ≠ a live Phase A week. Similar-regime ≠ future performance. BreakoutV1 params are **not** retuned here.

## How to run

```bash
source .venv/bin/activate
pytest -q
# uses last data/replay window; otherwise runs historical match first
python scripts/run_shadow_replay.py --venue both
python scripts/run_dashboard.py --shadow
```

If replay journals are missing:

```bash
python scripts/replay_phase_a_history.py --venue both --lookback-days 90 --window-days 7
python scripts/run_shadow_replay.py --venue both
```

Printed JSON: `n_signals`, `n_would_place`, `n_blocked_by_reason`, window timestamps. Research equity/expectancy-after-costs only under `research` with `not_a_forecast: true`.

## Example run (Mac, 2026-09-02)

Used the stored June similar-regime windows (spot 11–18 jun, xperp MD 14–21 jun). One €200 paper book, one position across venues, no orders, no kill.

| | Count |
|--|------:|
| Signals | 98 |
| Would-place | 26 |
| Blocked `one_position` | 72 |
| Blocked `kill` / `size` | 0 |
| Open / flatten (hypothetical) | 26 / 25 |

`no_signal` counts empty bars (not a strategy failure). 98 ≠ replay’s 59+54 because shadow uses **one book** (overlapping venue signals compete) and a shorter 1h pad than the original match fetch. Not a forecast.
