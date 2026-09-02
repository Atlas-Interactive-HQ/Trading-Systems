# 10 — Historical Phase A replay

**Stance:** Paper/research. No live orders. No demo orders. No profitability claim.  
**Date:** 2026-09-02

Replay exists to **accelerate Phase A observation** without waiting a calendar week of live signal-only sessions. It is **not** a substitute for that week, and a similar-regime window is **not** a forecast.

## What it does

1. Pulls **public** OKX EEA closed candles (`GET /api/v5/market/history-candles`, paginated with `after`/`before` + `limit≤100`). Recent “now” still uses `GET /api/v5/market/candles`.
2. Fingerprints the last ~7 days: realized vol (std of 15m log returns), range%, net trend, and v1 breakout **signal count** (same `BreakoutV1` params as the live loop).
3. Searches ~90d lookback for 7-day windows that **do not overlap** “now”. Picks the closest (lowest relative Euclidean score). If the score is poor (`> 0.45`), the report says so and **still uses that best candidate** — it does not invent a prettier window.
4. Walks closed 15m bars in time order (`scan_signals` / `BreakoutV1`, long **and** short). Journals under `data/replay/` tagged `source=historical-replay`.

No API keys. No `x-simulated-trading`. Universe: **DOGE-USD** spot MD + **DOGE-USD_UM_XPERP-310404** public X-Perp MD. Order instId `…310516` is unused (no orders). PEPE deferred.

Risk labels (€200 book, 5% day kill, 1–2%/trade) are written on the journal for continuity with Phase A. This run is **signal-only**. Hypothetical fills are not required; the printed summary has **no PnL**.

## How to run

```bash
cd Trading-Systems
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python scripts/replay_phase_a_history.py --venue both --lookback-days 90 --window-days 7
```

Journals: `data/replay/{UTC-date}/` (`events.jsonl`, `decisions.jsonl`, `summary_<run_id>.json`). Gitignored via `data/`.

Dashboard (read-only, keep `--fixtures` for the UI demo):

```bash
python scripts/run_dashboard.py --replay          # data/replay
python scripts/run_dashboard.py --fixtures        # bundled samples
python scripts/run_dashboard.py                   # live Phase A data/oms
```

## Replay ≠ live Phase A week

| | Historical replay | Phase A observer |
|--|-------------------|------------------|
| Data | Public history-candles (whatever span the venue actually returns) | Sessions as they happen |
| Journals | `data/replay/` | `data/oms/` |
| Orders | Never | Signal-only until gates are green |
| Meaning | Pipeline + similar-regime **sample** | The actual week you are measuring |

If pagination or the venue truncates history, the summary records the **actual** `fetched_start_ms` / `fetched_end_ms` and `span_incomplete`. The window shrinks to half the available bars rather than inventing candles.

Similar-regime match is a distance on four features, not an edge. Success metric remains **expectancy after costs on paper** when you have enough real Phase A journal — never “this window would have made €X”.

## Example run (Mac, 2026-09-02)

Public EEA `history-candles` pagination returned the requested ~90d (`2026-06-04 19:15 UTC` → `2026-09-02 19:00 UTC`, `span_incomplete=false`). No orders. Counts only:

| Venue | Now window | Best candidate | Score | Quality | Signals in candidate (L/S) |
|-------|------------|----------------|-------|---------|----------------------------|
| spot DOGE-USD | 2026-08-26 → 2026-09-02 | 2026-06-11 → 2026-06-18 | 0.092 | ok | 59 (28/31) |
| xperp MD `…310404` | 2026-08-26 → 2026-09-02 | 2026-06-14 → 2026-06-21 | 0.188 | ok | 54 (22/32) |

`decisions.jsonl` is partitioned by **bar** UTC date (inside the candidate window). `events.jsonl` + `summary_*.json` use the **run** UTC date. Dashboard `--replay` reads all dated dirs under `data/replay/`.
