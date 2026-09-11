# 90 — Evaluation integrity audit (P0)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ arm. **This audit does not promote.**
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — R1–R7 remain DEV/eliminate-only.
**Follow-on:** [`91`](./91-rise-panel-accounting-v2.md) (evaluator-v2 + measured OLD vs V2).

---

## Hypothesis (verified in code)

`src/atlas/paper/ema_eval.py::walk_long_flat` mixes two different books:

| Field | What it actually measures |
|-------|---------------------------|
| `net_return_eur` | Terminal mark-to-market: `cash + qty * last.close − start`. If still long at the window end, **no** terminal sell fee or sell slippage is applied. |
| `n_trades` | Count of **completed** realized round-trips only. |
| `expectancy_after_costs_eur` | `realized_net / n_trades`, or `None` when `n_trades == 0`. |

Confirmed by reading the walker (historical keys written **before** the additive v2 block):

1. Realized PnL and `n_trades` increment only on a filled `FLAT` exit (sell slip + fee at **next open**).
2. After the loop, an open long is marked at `last.close` with **no** synthetic sell.
3. `buy_and_hold` already liquidates at last close with sell slip + fee — that is the honest finite-window analog the walker was missing.

This is why Core C0 windows such as R1 / R4 / R7 can show a large `net_return_eur` with `n_trades = 0` and expectancy `None` (buy-and-hold-like open hold). Soft-promote then treats those windows as **no expectancy**, while panel net still counts the unmarked MTM.

**Not a strategy bug.** Signals are unchanged. This is evaluator accounting.

---

## What this sprint does (and does not)

**Does:**

- Keep original historical keys byte-stable so old artifacts remain reproducible.
- Add an explicit `rise_panel_accounting_v2` path (see [`91`](./91-rise-panel-accounting-v2.md)).
- Re-score **unchanged** strategies and report OLD vs V2 deltas.
- Freeze Mid #71 / Scalp S1; register SCALP-R2 and CORE-R1 **before** scoring them.
- Split HFT `carried_forward` from `health_stale` ([`92`](./92-hft-staleness-semantics.md)).

**Does not:**

- Promote anyone from this audit.
- Rewrite `soft_promote_v1` or historical phase1/54, 72, 83, 86, 87, 88, 89 tables.
- Change `config/default.yaml`.
- Optimize R1–R7, grind RVOL 1.25/1.5, run Mid M2–M4, or score CORE-R1 / SCALP-R2 on R1–R7.
- Invent metrics, capture numbers, or an ETH X-Perp instId.

---

## Honesty / invalidation

- Soft PASS ≠ arm. V2 PASS ≠ promote. A labeled gate is not a silent rewrite.
- Do **not** create green by changing `rise_panel_accounting_v2` after seeing results.
- Do **not** treat a one-interval MTM hold (`n_trades=0`, large `net_return`) as complete-trade expectancy.
- R1–R7 remain DEV/eliminate-only. GREEN CANDIDATE still requires: positive after costs, positive **complete-trade** expectancy, not one-interval dominated, survives risk/cost stress, reproduces on unseen data.
- If candle history cannot be fetched, the re-score is `insufficient_data` — stop; do not invent rows.

`not_a_forecast: true`. `place_orders: false`.
