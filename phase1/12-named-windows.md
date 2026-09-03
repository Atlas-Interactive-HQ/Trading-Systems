# 12 — Named backtest windows (2020-09, 2023-09, Q4 months)

**Stance:** Paper/research. No live or demo orders. No PnL headline.  
**Date:** 2026-09-03

Named windows are **calendar spans**, not similar-regime matches. They do not replace a live Phase A week and are not a forecast.

`2020-09` / `2023-09` stay the original **multi-month** research spans (Sep → following Mar). They are **not** calendar September.

Q4 ids `YYYY-10` / `YYYY-11` / `YYYY-12` are **true calendar months** (Oct 1–31, Nov 1–30, Dec 1–31 UTC). They exist so Phase D can define the system against the same season as the coming months. See [`14-q4-months.md`](./14-q4-months.md). They do not rewrite the 2020-09 / 2023-09 holdout pass rule.

## Windows (UTC, inclusive)

| Id | Span |
|----|------|
| `2020-09` | 2020-09-01 → 2021-03-31 |
| `2023-09` | 2023-09-01 → 2024-03-31 |
| `2020-10` | 2020-10-01 → 2020-10-31 |
| `2020-11` | 2020-11-01 → 2020-11-30 |
| `2020-12` | 2020-12-01 → 2020-12-31 |
| `2023-10` | 2023-10-01 → 2023-10-31 |
| `2023-11` | 2023-11-01 → 2023-11-30 |
| `2023-12` | 2023-12-01 → 2023-12-31 |
| `2024-10` | 2024-10-01 → 2024-10-31 |
| `2024-11` | 2024-11-01 → 2024-11-30 |
| `2024-12` | 2024-12-01 → 2024-12-31 |
| `2022-bear` | 2022-01-01 → 2022-12-31 |
| `2022-h1` | 2022-01-01 → 2022-06-30 |
| `2023-chop` | 2023-01-01 → 2023-08-31 |
| `2026-funding` | 2026-06-04 → 2026-09-02 |

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
python scripts/replay_phase_a_history.py --windows 2020-10,2020-11,2020-12,2023-10,2023-11,2023-12,2024-10,2024-11,2024-12 --venue spot
python scripts/run_shadow_replay.py --windows q4 --venue spot
python scripts/run_paper_eval.py --samples 2020-10,2020-11,2020-12,2023-10,2023-11,2023-12,2024-10,2024-11,2024-12 --write-md phase1/14-q4-months.md
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
