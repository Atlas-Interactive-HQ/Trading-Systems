"""phase1/111 — SL fill / SL release ping stub. No live. Does not re-lock phase1/112."""

from __future__ import annotations

from pathlib import Path

from atlas.ops.sl_ping import (
    PING_STREAMS,
    PING_TRIGGERS,
    SCALP_COOLDOWN_CROSSREF,
    classify_stream_sl_event,
    lock_card,
    may_arm_from_ping,
    prep_ops_alert,
)
from atlas.paper.rise_panel import (
    SCALP_S1_3SL_28M_COOLDOWN_ID,
    SCALP_S1_CONSECUTIVE_SL_TRIGGER,
    SCALP_S1_POST_3SL_ENTRY_DELAY_MIN,
)

ROOT = Path(__file__).resolve().parents[2]


def test_ping_lock_card_prep_only_and_crossrefs_112():
    card = lock_card()
    assert card["id"] == "phase1_111_sl_release_ping_v1"
    assert card["streams"] == ["core", "mid", "scalp"]
    assert card["triggers"] == ["stop_loss_fill", "stop_release"]
    assert card["send"] is False
    assert card["place_orders"] is False
    assert card["live_arm"] is False
    assert card["soft_pass_neq_arm"] is True
    assert card["default_yaml_untouched"] is True
    assert card["parked_capital_eur_cited"] == 240
    assert card["capital_is_not_sleeve_arm"] is True
    assert card["does_not_re_lock_scalp_3sl_28m"] is True
    assert card["scalp_cooldown_lock"] == "phase1/112"
    assert SCALP_COOLDOWN_CROSSREF == "phase1/112"
    # 112 remains the cooldown lock (already on main). Do not shadow it.
    assert SCALP_S1_3SL_28M_COOLDOWN_ID == "scalp_s1_3sl_28m_cooldown"
    assert SCALP_S1_CONSECUTIVE_SL_TRIGGER == 3
    assert SCALP_S1_POST_3SL_ENTRY_DELAY_MIN == 28


def test_classify_ping_only_when_armed_core_mid_scalp():
    assert PING_STREAMS == ("core", "mid", "scalp")
    assert PING_TRIGGERS == ("stop_loss_fill", "stop_release")

    paper = classify_stream_sl_event(
        stream="scalp", event="stop_loss_fill", armed=False
    )
    assert paper["should_ping"] is False
    assert paper["reason"] == "stream_not_armed_prep_only"
    assert paper["place_orders"] is False

    for stream in PING_STREAMS:
        fill = classify_stream_sl_event(
            stream=stream, event="stop_loss_fill", armed=True
        )
        assert fill["should_ping"] is True
        assert fill["audience"] == "kaje_joint_review"
        rel = classify_stream_sl_event(
            stream=stream, event="stop_release", armed=True
        )
        assert rel["should_ping"] is True

    hft = classify_stream_sl_event(stream="hft", event="stop_loss_fill", armed=True)
    assert hft["should_ping"] is False
    assert hft["known_stream"] is False
    assert hft["reason"] == "stream_out_of_scope"

    other = classify_stream_sl_event(stream="scalp", event="take_profit", armed=True)
    assert other["should_ping"] is False
    assert other["reason"] == "event_not_sl_fill_or_release"


def test_prep_ops_alert_never_sends_or_arms():
    alert = prep_ops_alert(
        stream="mid",
        event="sl_cancel",
        armed=True,
        ga_live_eur200=True,
        session_ja=True,
    )
    assert alert["event"] == "stop_release"
    assert alert["send"] is False
    assert alert["prep_only"] is True
    assert alert["place_orders"] is False
    assert alert["may_arm"] is False
    assert alert["resting_tp_default"] == "leave"
    assert alert["ga_live_eur200"] is True
    assert alert["session_ja"] is True
    assert may_arm_from_ping(ga_live_eur200=True, session_ja=True) is False

    alias = classify_stream_sl_event(stream="core", event="SL fill", armed=True)
    assert alias["event"] == "stop_loss_fill"
    assert alias["should_ping"] is True


def test_default_yaml_not_touched_by_this_lock():
    text = (ROOT / "config" / "default.yaml").read_text(encoding="utf-8")
    assert "leverage_default: 2.0" in text
    assert "allow_trade: false" in text
