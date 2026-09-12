"""Kaje architecture lock 2026-09-12 (phase1/113).

Capital / sleeve policy only. Not a score. Not an arm.
Soft PASS ≠ arm. place_orders false. default.yaml untouched.
Do not invent PEPE instId, PnL, or expectancy.
"""

from __future__ import annotations

from typing import Any

LOCK_ID = "kaje_arch_2026_09_12"
LOCK_DATE = "2026-09-12"
TIMEZONE = "Europe/Amsterdam"

RATIO_CORE_MID_SCALP: tuple[int, int, int] = (6, 3, 1)
CASCADE_DIRECTION = ("scalp", "mid", "btc")
WEEKLY_REVIEW_WEEKDAY = "Monday"
WEEKLY_REVIEW_LOCAL_TIME = "09:00"
WEEKLY_REVIEW_AUTO_SWEEP = False

CORE_ASSET = "BTC"
CORE_STYLE = "spot_hold_3m"
CORE_LEVERAGE = 1.0
CORE_ADD_PERIODICALLY = True
CORE_AUTO_BUY = False

MID_ASSET = "DOGE"
MID_RESEARCH_FAMILY = "phase1/71"
MID_LEVERAGE_CEILING_ISOLATED = 5.0

SCALP_ASSET = "PEPE"
SCALP_PREVIOUSLY_DEFERRED = True
SCALP_COMPOUNDING_ADVISED = True
SCALP_LEVERAGE_CEILING_ISOLATED = 10.0
SCALP_INST_ID = None  # fail-closed — do not invent
SCALP_LISTING_VERIFIED = False
SCALP_SYSTEM_EXISTS = False

# phase1/112 still applies to Scalp once a PEPE system exists.
SCALP_3SL_28M_APPLIES_WHEN_SYSTEM_EXISTS = True
SL_PING_111_UNCHANGED = True

SOFT_PASS_NEQ_ARM = True
PLACE_ORDERS = False
DEFAULT_YAML_UNTOUCHED = True
LIVE_ARM = False
INVENT_PNL = False
INVENT_INST_ID = False


def kaje_arch_card() -> dict[str, Any]:
    """Frozen architecture card. Never places orders. Never invents instId."""
    return {
        "id": LOCK_ID,
        "lock_date": LOCK_DATE,
        "timezone": TIMEZONE,
        "status": "architecture_lock_not_live",
        "live_arm": LIVE_ARM,
        "soft_pass_neq_arm": SOFT_PASS_NEQ_ARM,
        "halted": True,
        "place_orders": PLACE_ORDERS,
        "not_a_forecast": True,
        "default_yaml_untouched": DEFAULT_YAML_UNTOUCHED,
        "invented_pnl": INVENT_PNL,
        "invented_inst_id": INVENT_INST_ID,
        "ratio_core_mid_scalp": list(RATIO_CORE_MID_SCALP),
        "cascade": {
            "direction": list(CASCADE_DIRECTION),
            "one_way": True,
            "downward_refill": False,
        },
        "weekly_review": {
            "weekday": WEEKLY_REVIEW_WEEKDAY,
            "local_time": WEEKLY_REVIEW_LOCAL_TIME,
            "timezone": TIMEZONE,
            "auto_sweep": WEEKLY_REVIEW_AUTO_SWEEP,
            "needs_kaje_yes_for_sweeps": True,
        },
        "core": {
            "asset": CORE_ASSET,
            "style": CORE_STYLE,
            "leverage": CORE_LEVERAGE,
            "add_periodically": CORE_ADD_PERIODICALLY,
            "auto_buy": CORE_AUTO_BUY,
            "research_promote": False,
        },
        "mid": {
            "asset": MID_ASSET,
            "research_family": MID_RESEARCH_FAMILY,
            "leverage_ceiling_isolated": MID_LEVERAGE_CEILING_ISOLATED,
            "arm": False,
        },
        "scalp": {
            "asset": SCALP_ASSET,
            "previously_deferred": SCALP_PREVIOUSLY_DEFERRED,
            "compounding_advised": SCALP_COMPOUNDING_ADVISED,
            "leverage_ceiling_isolated": SCALP_LEVERAGE_CEILING_ISOLATED,
            "inst_id": SCALP_INST_ID,
            "listing_verified": SCALP_LISTING_VERIFIED,
            "system_exists": SCALP_SYSTEM_EXISTS,
            "fail_closed_until_listing": True,
            "phase1_112_applies_when_system_exists": SCALP_3SL_28M_APPLIES_WHEN_SYSTEM_EXISTS,
            "arm": False,
        },
        "cross_ref": {
            "phase1/107": "capital + leverage addendum",
            "phase1/108": "DEV board overlay note",
            "phase1/111": "SL ping unchanged",
            "phase1/112": "3xSL 28m once PEPE system exists",
        },
        "sl_ping_111_unchanged": SL_PING_111_UNCHANGED,
        "arm_requires": ("ga live", "session-ja", "sleeve list"),
        "citation": ("phase1/113", "phase1/107", "phase1/108", "phase1/111", "phase1/112"),
    }


def refuse_invented_pepe_inst_id(inst_id: str | None) -> dict[str, Any]:
    """Fail-closed: no PEPE score/arm from an invented or unverified instId."""
    if SCALP_LISTING_VERIFIED and SCALP_INST_ID and inst_id == SCALP_INST_ID:
        return {
            "accepted": True,
            "fail_closed": False,
            "inst_id": SCALP_INST_ID,
            "score_allowed": False,
            "arm_allowed": False,
            "note": "listing flag is reserved; today listing_verified is False",
        }
    return {
        "accepted": False,
        "fail_closed": True,
        "inst_id": None,
        "invented_inst_id": True,
        "score_allowed": False,
        "arm_allowed": False,
        "place_orders": False,
        "reason": "PEPE instId not re-verified on OKX EEA; do not invent",
    }
