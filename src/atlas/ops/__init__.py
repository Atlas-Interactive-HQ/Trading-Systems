"""Ops stubs. Paper / alert-prep only. not_a_forecast. Never places orders."""

from atlas.ops.sl_ping import (
    PING_STREAMS,
    PING_TRIGGERS,
    classify_stream_sl_event,
    lock_card as sl_ping_lock_card,
    may_arm_from_ping,
    prep_ops_alert,
)

__all__ = [
    "PING_STREAMS",
    "PING_TRIGGERS",
    "classify_stream_sl_event",
    "may_arm_from_ping",
    "prep_ops_alert",
    "sl_ping_lock_card",
]
