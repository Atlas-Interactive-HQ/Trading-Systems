"""P4a screening vs P4b 7d lock. No invented capture numbers as claims."""

from __future__ import annotations

from atlas.scalp_hft.liquidity_gate import (
    P4A_MAY_LOCK_INSTRUMENT,
    P4B_CAPTURE_DAYS,
    P4B_MIN_SPAN_S,
    SLICE_REPORT_KEYS,
    LiquidityGateMetrics,
    LiquidityGatePlan,
    empty_p4b_report,
    p4a_screen,
    select_instrument,
    select_instrument_p4b,
)


def _eligible(inst_id: str, base: str, books5: float, span_s: float) -> LiquidityGateMetrics:
    return LiquidityGateMetrics(
        inst_id=inst_id,
        base=base,
        span_s=span_s,
        trades_per_sec=2.0,
        books5_changes_per_sec=books5,
        spread_bps_median=2.0,
        top5_depth_notional_median=1000.0,
        reconnect_count=1,
        book_age_ms_median=200.0,
        insufficient_data=False,
    )


def test_p4a_never_locks_even_with_eligible_24h_fixtures():
    assert P4A_MAY_LOCK_INSTRUMENT is False
    rows = [
        _eligible("A", "BTC", 8.0, 86400),
        _eligible("B", "ETH", 12.0, 86400),
        _eligible("C", "DOGE", 4.0, 86400),
    ]
    ranked = select_instrument(rows)
    assert ranked["selected"]["inst_id"] == "B"
    screen = p4a_screen(rows)
    assert screen["selected"] is None
    assert screen["instrument_lock"] is False
    assert screen["may_lock_instrument"] is False
    assert screen["phase"] == "P4a"
    assert "P4b" in screen["reason"]


def test_p4b_empty_and_24h_span_fail_closed():
    empty = select_instrument_p4b([])
    assert empty["fail_closed"] is True
    assert empty["selected"] is None
    assert empty["instrument_lock"] is False
    assert "insufficient_data" in empty["reason"]

    day = [
        _eligible("A", "BTC", 8.0, 86400),
        _eligible("B", "ETH", 12.0, 86400),
        _eligible("C", "DOGE", 4.0, 86400),
    ]
    short = select_instrument_p4b(day)
    assert short["fail_closed"] is True
    assert short["selected"] is None
    assert "24h" in short["reason"] or "calendar" in short["reason"]


def test_p4b_missing_slices_fail_closed():
    week = [
        _eligible("A", "BTC", 8.0, P4B_MIN_SPAN_S),
        _eligible("B", "ETH", 12.0, P4B_MIN_SPAN_S),
        _eligible("C", "DOGE", 4.0, P4B_MIN_SPAN_S),
    ]
    out = select_instrument_p4b(week)
    assert out["fail_closed"] is True
    assert out["selected"] is None
    assert "slice" in out["reason"]


def test_p4b_report_schema_has_no_invented_numbers():
    report = empty_p4b_report("ETH")
    for key in SLICE_REPORT_KEYS:
        assert key in report
    assert report["insufficient_data"] is True
    assert report["pooled"]["insufficient_data"] is True
    assert report["pooled"]["trades_per_sec"] is None
    assert len(report["by_utc_hour"]) == 24
    assert report["do_not_invent_capture_numbers"] is True
    plan = LiquidityGatePlan().to_dict()
    assert plan["p4a_may_lock_instrument"] is False
    assert plan["p4b_capture_days"] == P4B_CAPTURE_DAYS == 7


def test_p4b_stability_fixture_can_lock_without_claiming_capture():
    """Rule-test fixtures only — not a live instrument pick."""
    week = [
        _eligible("A", "BTC", 8.0, P4B_MIN_SPAN_S),
        _eligible("B", "ETH", 12.0, P4B_MIN_SPAN_S),
        _eligible("C", "DOGE", 4.0, P4B_MIN_SPAN_S),
    ]
    hours = {
        "BTC": {h: 1.0 for h in range(24)},
        "ETH": {h: 1.5 for h in range(24)},
        "DOGE": {h: 0.5 for h in range(24)},
    }
    hours["ETH"][3] = 1.6  # slight peak; residual still ETH-first
    out = select_instrument_p4b(
        week,
        weekday=week,
        weekend=week,
        sessions={"asia": week, "eu": week, "us": week},
        books5_by_hour=hours,
    )
    assert out["fail_closed"] is False
    assert out["selected"]["inst_id"] == "B"
    assert out["stability"]["ok"] is True
    assert out["p4a_is_not_a_lock"] is True


def test_p4b_spectacular_night_rejects():
    week = [
        _eligible("A", "BTC", 8.0, P4B_MIN_SPAN_S),
        _eligible("B", "ETH", 12.0, P4B_MIN_SPAN_S),
        _eligible("C", "DOGE", 4.0, P4B_MIN_SPAN_S),
    ]
    hours = {
        "BTC": {h: 2.0 for h in range(24)},
        "ETH": {h: 0.1 for h in range(24)},
        "DOGE": {h: 0.1 for h in range(24)},
    }
    hours["ETH"][2] = 100.0  # one spectacular hour
    out = select_instrument_p4b(
        week,
        weekday=week,
        weekend=week,
        sessions={"asia": week, "eu": week, "us": week},
        books5_by_hour=hours,
    )
    assert out["fail_closed"] is True
    assert out["selected"] is None
    assert "spectacular-night" in out["reason"]
