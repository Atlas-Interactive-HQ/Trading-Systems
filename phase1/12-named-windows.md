# 12 — Named backtest windows (2020-09, 2023-09)

**Stance:** Paper/research. No live or demo orders. No PnL headline.  
**Date:** 2026-09-03

Named windows are **calendar spans**, not similar-regime matches. They do not replace a live Phase A week and are not a forecast.

## Windows (UTC, inclusive)

| Id | Span |
|----|------|
| `2020-09` | 2020-09-01 → 2021-03-31 |
| `2023-09` | 2023-09-01 → 2024-03-31 |

## Why DOGE-USDT (research MD)

Verified 2026-09-03 on public EEA (`https://eea.okx.com`, no keys):

- `DOGE-USD` (OMS spot instId) history-candles only go back to ~2025-01-14. **Empty** on both named windows. Do not use it here.
- `DOGE-USDT` **does** cover those dates (`after` pagination). Use it as **research MD** (`md_inst_id=DOGE-USDT`). Label every journal: not the OMS spot instId `DOGE-USD`. Not orderable on this path.

## Why xperp is skipped

`DOGE-USD_UM_XPERP-310404` returns empty on 2020/2023. **Fail closed:** skip the xperp leg, record `unavailable`. Do not invent perp bars.

Optional research-perp: `DOGE-USDT-SWAP` may be fetched as a **separate** leg, labeled not-X-Perp / not orderable. If empty, skip.

Pagination uses `after` = exclusive end-of-window and walks backward. Do not use `before` as a date jump.

## How to run

Similar-regime default is unchanged (omit `--windows`).

```bash
source .venv/bin/activate
pytest -q
python scripts/replay_phase_a_history.py --windows 2020-09,2023-09 --venue spot
python scripts/run_shadow_replay.py --windows 2020-09,2023-09 --venue spot
python scripts/run_dashboard.py --replay   # named-window events show in overzicht
python scripts/run_dashboard.py --shadow
```

Journals: `data/replay/` and `data/shadow/` with `source=named-window` plus `window_id`. Gitignored. Distinct from live `data/oms/`.

If a window is empty after pagination, the summary records skip/`span_incomplete` and continues. No fake bars.

## Mac run (2026-09-03)

Public EEA `history-candles` on **DOGE-USDT** returned complete spans (`span_incomplete=false`). X-Perp was not requested (`--venue spot`). `DOGE-USDT-SWAP` also covered both windows (research-perp, not orderable).

| Window | 15m bars | Spot signals L/S | Would-place | Blocked `one_position` | Blocked `kill` |
|--------|----------:|------------------:|------------:|-----------------------:|---------------:|
| 2020-09 | 20352 | 836 / 642 | 675 | 712 | 91 |
| 2023-09 | 20448 | 1067 / 638 | 734 | 906 | 65 |

Not a forecast. Shadow ≠ Phase C. Phase A stays signal-only.

## What it is not

- Not similar-regime matching (`--lookback-days` path).
- Not a live Phase A week.
- Not Phase C gated micro-demo. Shadow still never places.
- Not a profitability claim. Research expectancy lives under `research.not_a_forecast` only.
