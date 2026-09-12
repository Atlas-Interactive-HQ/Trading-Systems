"""Human ping on SL fill / SL release (phase1/111).

Core / Mid / Scalp only, and only once that stream is armed.
Prep Ops alert path. Does not send. Does not arm. Does not place orders.

Scalp 3×SL → 28m delay is phase1/112 — do not re-lock it here.

Soft PASS ≠ arm. not_a_forecast.
"""

from __future__ import annotations

from typing import Any, Literal

PING_LOCK_ID = "phase1_111_sl_release_ping_v1"
PING_STREAMS: tuple[str, ...] = ("core", "mid", "scalp")
PING_TRIGGERS: tuple[str, ...] = ("stop_loss_fill", "stop_release")
# stop_release = cancel / close of a resting SL (not a TP cancel).
# Cooldown after 3 Scalp SL fills lives in phase1/112 — not this module.
SCALP_COOLDOWN_CROSSREF = "phase1/112"

StreamName = Literal["core", "mid", "scalp"]
PingTrigger = Literal["stop_loss_fill", "stop_release"]


def _norm(value: str) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def classify_stream_sl_event(
    *,
    stream: str,
    event: str,
    armed: bool,
) -> dict[str, Any]:
    """Classify a candidate ping. Never sends. Never arms."""
    stream_n = _norm(stream)
    event_n = _norm(event)
    known_stream = stream_n in PING_STREAMS
    known_event = event_n in PING_TRIGGERS
    if event_n in {"sl_fill", "stoploss_fill", "stop_fill"}:
        event_n = "stop_loss_fill"
        known_event = True
    if event_n in {"sl_release", "stop_cancel", "sl_cancel", "resting_sl_cancel"}:
        event_n = "stop_release"
        known_event = True

    should_ping = bool(armed) and known_stream and known_event
    return {
        "lock_id": PING_LOCK_ID,
        "stream": stream_n,
        "event": event_n,
        "known_stream": known_stream,
        "known_event": known_event,
        "armed": bool(armed),
        "should_ping": should_ping,
        "reason": _classify_reason(
            known_stream=known_stream,
            known_event=known_event,
            armed=bool(armed),
        ),
        "audience": "kaje_joint_review",
        "place_orders": False,
        "not_a_forecast": True,
        "soft_pass_neq_arm": True,
        "live_arm": False,
        "scalp_cooldown_lock": SCALP_COOLDOWN_CROSSREF,
    }


def _classify_reason(*, known_stream: bool, known_event: bool, armed: bool) -> str:
    if not known_stream:
        return "stream_out_of_scope"
    if not known_event:
        return "event_not_sl_fill_or_release"
    if not armed:
        return "stream_not_armed_prep_only"
    return "ping_kaje_joint_review"


def prep_ops_alert(
    *,
    stream: str,
    event: str,
    armed: bool = False,
    ga_live_eur200: bool = False,
    session_ja: bool = False,
    note: str = "",
) -> dict[str, Any]:
    """Build the would-ping payload. send is always false (prep path)."""
    classified = classify_stream_sl_event(stream=stream, event=event, armed=armed)
    return {
        **classified,
        "channel": "ops_kaje_joint_review",
        "send": False,
        "prep_only": True,
        "place_orders": False,
        "may_arm": may_arm_from_ping(
            ga_live_eur200=ga_live_eur200, session_ja=session_ja
        ),
        "ga_live_eur200": bool(ga_live_eur200),
        "session_ja": bool(session_ja),
        "note": note,
        "resting_tp_default": "leave",
    }


def may_arm_from_ping(*, ga_live_eur200: bool, session_ja: bool) -> bool:
    """A ping never arms. Phrase gates are recorded only."""
    del ga_live_eur200, session_ja
    return False


def lock_card() -> dict[str, Any]:
    return {
        "id": PING_LOCK_ID,
        "phase1": "111",
        "streams": list(PING_STREAMS),
        "triggers": list(PING_TRIGGERS),
        "send": False,
        "place_orders": False,
        "live_arm": False,
        "soft_pass_neq_arm": True,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "no_arm_until": ("ga live €200", "session-ja", "sleeve_list"),
        "parked_capital_eur_cited": 240,
        "parked_capital_source": "phase1/107 addendum + phase1/109",
        "capital_is_not_sleeve_arm": True,
        "does_not_re_lock_scalp_3sl_28m": True,
        "scalp_cooldown_lock": SCALP_COOLDOWN_CROSSREF,
    }
