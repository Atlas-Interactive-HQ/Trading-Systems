"""H1 fill-conditioned markout + event-time ablation (phase1/104).

After H1 signal study, BEFORE economic PnL.
Do NOT rewrite the locked 1s H1 clock (phase1/96).
"""

from __future__ import annotations

from typing import Any

from atlas.scalp_hft.h1_ensemble import H1_LOCK_ID, HORIZONS_S

H1_MARKOUT_ID = "hft_h1_markout_fill_conditioned_v1"
H1A_EVENT_TIME_ID = "hft_h1a_event_time_ablation_v1"
# Fill-conditioned markout horizons (ms). Distinct from locked 1s H1 clock.
MARKOUT_HORIZONS_MS: tuple[int, ...] = (100, 250, 500, 1_000, 3_000, 5_000, 10_000)
MARKOUT_SIDES: tuple[str, ...] = ("maker_buy", "maker_sell")
# Gate order is hard: signal → markout → queue/latency → economic paper PnL.
ECONOMIC_PNL_GATE: tuple[str, ...] = (
    "signal_green",
    "markout_green",
    "queue_latency",
    "economic_paper_pnl",
)
EVENT_TIME_ABLATION: dict[str, tuple[int, ...]] = {
    "book_changes": (1, 5, 10, 20),
    "aggressive_trades": (1, 5, 10, 20),
}
H1_1S_CLOCK_LOCKED = True
H1_CLOCK_HORIZONS_S = HORIZONS_S


def markout_card() -> dict[str, Any]:
    return {
        "markout_id": H1_MARKOUT_ID,
        "h1_lock_id": H1_LOCK_ID,
        "rewrite_locked_1s_h1": False,
        "h1_1s_clock_locked": H1_1S_CLOCK_LOCKED,
        "h1_clock_horizons_s": list(H1_CLOCK_HORIZONS_S),
        "markout_horizons_ms": list(MARKOUT_HORIZONS_MS),
        "sides": list(MARKOUT_SIDES),
        "fill_conditioned": True,
        "economic_pnl_gate": list(ECONOMIC_PNL_GATE),
        "event_time": {
            "id": H1A_EVENT_TIME_ID,
            "role": "h1a_diagnostic_future_h2",
            "rewrite_locked_1s_h1": False,
            "n": dict(EVENT_TIME_ABLATION),
        },
        "scored": False,
        "no_hft_pnl_in_this_module": True,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_neq_arm": True,
    }


def economic_pnl_allowed(*, signal_green: bool, markout_green: bool, queue_latency_ok: bool) -> dict[str, Any]:
    """Refuse economic paper PnL until the registered gate sequence is green."""
    steps = {
        "signal_green": bool(signal_green),
        "markout_green": bool(markout_green),
        "queue_latency": bool(queue_latency_ok),
    }
    allowed = all(steps.values())
    return {
        "allowed": allowed,
        "steps": steps,
        "next": "economic_paper_pnl" if allowed else ECONOMIC_PNL_GATE[next(
            i for i, k in enumerate(("signal_green", "markout_green", "queue_latency"))
            if not steps[k]
        )],
        "no_hft_pnl_in_this_module": True,
        "not_a_forecast": True,
    }
