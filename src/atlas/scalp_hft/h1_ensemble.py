"""H1 ensemble lock — design only until P1 health + P4 liquidity are ready.

micro_score = (z_vamp + z_microprice + z_ofi) / 3 — no weight optimize.
EMA12/21 = regime, not alpha.

LONG:  healthy + EMA12>EMA21 + micro_score>=+1.0 + 2-of-3 confirmation
SHORT: healthy + EMA12<EMA21 + micro_score<=-1.0 + 2-of-3 confirmation

First study is **signal-only** (future midpoint return 1s/3s/5s/10s).
Do not headline a green signal as a profitable strategy.
Economic PnL only after the signal study is frozen AND a latency/queue/fee
sim exists. No HFT PnL in this module.
"""

from __future__ import annotations

from typing import Any, Sequence

H1_LOCK_ID = "hft_h1_equal_weight_ensemble_v1"
MICRO_SCORE_THRESHOLD = 1.0
HORIZONS_S: tuple[int, ...] = (1, 3, 5, 10)
CONFIRM_WINDOW = 3
CONFIRM_NEED = 2
SIGNAL_FAMILIES: tuple[str, ...] = (
    "vamp_only",
    "microprice_only",
    "ofi_only",
    "equal_weight",
    "ema_plus_equal_weight",
)


def micro_score(
    z_vamp: float | None,
    z_microprice: float | None,
    z_ofi: float | None,
) -> float | None:
    """Equal-weight mean. None if any leg is missing/invalid. No weights."""
    zs = (z_vamp, z_microprice, z_ofi)
    if any(z is None for z in zs):
        return None
    return (float(z_vamp) + float(z_microprice) + float(z_ofi)) / 3.0  # type: ignore[arg-type]


def confirmed_2of3(flags: Sequence[bool]) -> bool:
    """Existing H0 confirmation: 2 of last 3 seconds."""
    tail = list(flags)[-CONFIRM_WINDOW:]
    if len(tail) < CONFIRM_WINDOW:
        return False
    return sum(1 for f in tail if f) >= CONFIRM_NEED


def h1_side(
    *,
    healthy: bool,
    ema12: float | None,
    ema21: float | None,
    score: float | None,
    confirm_long: Sequence[bool],
    confirm_short: Sequence[bool],
) -> str:
    """Return long / short / flat. Never trades when unhealthy or score missing."""
    if not healthy or score is None or ema12 is None or ema21 is None:
        return "flat"
    if ema12 > ema21 and score >= MICRO_SCORE_THRESHOLD and confirmed_2of3(confirm_long):
        return "long"
    if ema12 < ema21 and score <= -MICRO_SCORE_THRESHOLD and confirmed_2of3(confirm_short):
        return "short"
    return "flat"


def lock_card() -> dict[str, Any]:
    return {
        "lock_id": H1_LOCK_ID,
        "micro_score": "(z_vamp + z_microprice + z_ofi) / 3",
        "weight_optimize": False,
        "ema12_21_role": "regime_not_alpha",
        "threshold": MICRO_SCORE_THRESHOLD,
        "confirmation": f"{CONFIRM_NEED}_of_{CONFIRM_WINDOW}",
        "horizons_s": list(HORIZONS_S),
        "signal_families": list(SIGNAL_FAMILIES),
        "signal_only_first": True,
        "economic_pnl_before_signal_study_frozen": False,
        "no_hft_pnl_in_this_module": True,
        "not_a_forecast": True,
        "place_orders": False,
        "ready_when": "P1 health semantics + P4 liquidity instrument lock + multi-day Layer B",
    }
