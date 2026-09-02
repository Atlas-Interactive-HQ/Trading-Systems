"""Spot demo OMS: risk gating, refuse live trade, refuse zero equity."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from atlas.okx.client import LiveTradingBlocked, OkxEeaClient, PaperTradeDisabled
from atlas.okx.credentials import OkxCredentials
from atlas.okx.instruments import resolve_spot_universe
from atlas.oms.spot_demo import (
    DEMO_FUNDS_HINT,
    DemoFundsMissing,
    OmsRiskBlocked,
    SpotDemoOms,
    daily_kill_decision,
    parse_eq,
    risk_equity,
    size_spot_buy,
    universe_base_positions,
)
from atlas.paper.risk import PaperConfigError


def _creds() -> OkxCredentials:
    return OkxCredentials(
        api_key="SUPERSECRETKEYVALUE",
        api_secret="SUPERSECRETSECRETVALUE",
        passphrase="SUPERSECRETPASSPHRASE",
        source_path="/tmp/fake-okx.json",
    )


def _balance_payload(total_eq: str, details: list | None = None) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "totalEq": total_eq,
                "details": details
                or [
                    {
                        "ccy": "USDT",
                        "eq": total_eq,
                        "cashBal": total_eq,
                        "availBal": total_eq,
                        "frozenBal": "0",
                    }
                ],
            }
        ],
    }


def _config_payload() -> dict:
    return {"code": "0", "msg": "", "data": [{"acctLv": "1", "posMode": "net_mode"}]}


def _spot_rows() -> list[dict]:
    return [
        {
            "instId": "DOGE-USDT",
            "instType": "SPOT",
            "baseCcy": "DOGE",
            "quoteCcy": "USDT",
            "state": "live",
            "minSz": "10",
            "lotSz": "0.000001",
            "tickSz": "0.00001",
        },
        {
            "instId": "DOGE-USD",
            "instType": "SPOT",
            "baseCcy": "DOGE",
            "quoteCcy": "USD",
            "state": "live",
            "minSz": "10",
            "lotSz": "0.000001",
            "tickSz": "0.00001",
        },
        {
            "instId": "PEPE-USDT",
            "instType": "SPOT",
            "baseCcy": "PEPE",
            "quoteCcy": "USDT",
            "state": "live",
            "minSz": "100000",
            "lotSz": "1",
            "tickSz": "0.000000001",
        },
        {
            "instId": "BTC-USDT",
            "instType": "SPOT",
            "baseCcy": "BTC",
            "quoteCcy": "USDT",
            "state": "live",
            "minSz": "0.00001",
            "lotSz": "0.00000001",
            "tickSz": "0.1",
        },
        {
            "instId": "SOL-USDT",
            "instType": "SPOT",
            "baseCcy": "SOL",
            "quoteCcy": "USDT",
            "state": "live",
            "minSz": "0.01",
            "lotSz": "0.000001",
            "tickSz": "0.01",
        },
        {
            "instId": "BTC-USDT-SWAP",
            "instType": "SWAP",
            "state": "live",
        },
    ]


def _client(
    mode: str,
    allow_trade: bool = False,
    calls: list | None = None,
    *,
    total_eq: str = "200",
    details: list | None = None,
    pending: list | None = None,
) -> OkxEeaClient:
    bucket = calls if calls is not None else []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        bucket.append(
            {
                "method": request.method,
                "path": path,
                "url": str(request.url),
                "has_sim": request.headers.get("x-simulated-trading"),
                "body": request.content.decode("utf-8") if request.content else "",
            }
        )
        if path.endswith("/account/balance"):
            return httpx.Response(200, json=_balance_payload(total_eq, details))
        if path.endswith("/account/config"):
            return httpx.Response(200, json=_config_payload())
        if path.endswith("/public/instruments"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": _spot_rows()})
        if path.endswith("/market/ticker"):
            inst = request.url.params.get("instId", "DOGE-USDT")
            last = "0.15" if inst.startswith("DOGE") else "100000"
            if inst.startswith("PEPE"):
                last = "0.00001"
            if inst.startswith("SOL"):
                last = "150"
            return httpx.Response(
                200, json={"code": "0", "msg": "", "data": [{"instId": inst, "last": last}]}
            )
        if path.endswith("/trade/orders-pending"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": pending or []})
        if path.endswith("/trade/order") or path.endswith("/trade/cancel-order"):
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [{"ordId": "1", "clOrdId": "", "sCode": "0", "sMsg": "", "state": "live"}],
                },
            )
        return httpx.Response(404, json={"code": "404", "msg": path, "data": []})

    return OkxEeaClient(
        mode=mode,  # type: ignore[arg-type]
        allow_trade=allow_trade,
        credentials=_creds(),
        transport=httpx.MockTransport(handler),
    )


# --- risk helpers ---


def test_parse_eq_zero_and_junk():
    assert parse_eq("0") == 0.0
    assert parse_eq("") == 0.0
    assert parse_eq(None) == 0.0
    assert parse_eq("not-a-number") == 0.0
    assert parse_eq("200.5") == pytest.approx(200.5)


def test_risk_equity_caps_at_paper_scale():
    assert risk_equity(10_000.0) == 200.0
    assert risk_equity(50.0) == 50.0
    assert risk_equity(0.0) == 0.0


def test_size_spot_buy_within_one_to_two_percent():
    plan = size_spot_buy(
        total_eq=200.0,
        last_px=0.15,
        min_sz=10.0,
        lot_sz=0.000001,
        available_quote=200.0,
        tiny_notional=2.0,
        inst_id="DOGE-USDT",
    )
    assert plan.allowed
    assert plan.risk_budget == pytest.approx(3.0)  # 1.5% of 200
    assert plan.notional <= 2.0 + 1e-6 or plan.notional == pytest.approx(plan.min_notional)
    assert float(plan.sz) * 0.15 == pytest.approx(plan.notional)


def test_size_spot_buy_rejects_risk_frac_outside_band():
    with pytest.raises(PaperConfigError):
        SpotDemoOms(
            _client("demo"),
            per_trade_risk_frac=0.05,
            data_dir="/tmp/oms-x",
        )
    plan = size_spot_buy(
        total_eq=200.0,
        last_px=0.15,
        min_sz=10.0,
        lot_sz=1.0,
        available_quote=200.0,
        per_trade_risk_frac=0.015,
        tiny_notional=2.0,
    )
    assert plan.allowed


def test_size_spot_buy_zero_equity():
    plan = size_spot_buy(
        total_eq=0.0,
        last_px=0.15,
        min_sz=10.0,
        lot_sz=1.0,
        available_quote=0.0,
    )
    assert not plan.allowed
    assert plan.reason == "demo_funds_missing"
    assert "claim demo funds" in plan.extra["hint"].lower()


def test_size_rejects_min_sz_above_risk_budget():
    # 1.5% of 200 = 3; minSz notional 10*1 = 10 > 3
    plan = size_spot_buy(
        total_eq=200.0,
        last_px=1.0,
        min_sz=10.0,
        lot_sz=1.0,
        available_quote=200.0,
        tiny_notional=2.0,
    )
    assert not plan.allowed
    assert plan.reason == "min_sz_exceeds_risk"


def test_daily_kill_five_percent_of_paper_scale():
    # €200 book, 5% = €10 absolute even if demo wallet is 10_000
    d = daily_kill_decision(
        day_start_total_eq=10_000.0,
        current_total_eq=9_990.0,
        paper_scale=200.0,
        daily_kill_frac=0.05,
    )
    assert d["killed"]
    assert d["threshold"] == pytest.approx(10.0)
    d2 = daily_kill_decision(
        day_start_total_eq=10_000.0,
        current_total_eq=9_990.01,
        paper_scale=200.0,
        daily_kill_frac=0.05,
    )
    assert not d2["killed"]


def test_daily_kill_zero_day_start():
    d = daily_kill_decision(day_start_total_eq=0.0, current_total_eq=0.0)
    assert d["killed"]
    assert d["reason"] == "non_positive_day_start"


def test_universe_one_position_detects_base_inventory():
    held = universe_base_positions(
        [{"ccy": "DOGE", "eq": "12", "cashBal": "12", "availBal": "12"}]
    )
    assert held and held[0]["ccy"] == "DOGE"
    assert universe_base_positions([{"ccy": "USDT", "eq": "200"}]) == []


def test_resolve_spot_universe_prefers_usdt():
    got = resolve_spot_universe(_spot_rows())
    ids = {r["base"]: r["instId"] for r in got["resolved"]}
    assert ids["DOGE"] == "DOGE-USDT"
    assert ids["PEPE"] == "PEPE-USDT"
    assert ids["BTC"] == "BTC-USDT"
    assert ids["SOL"] == "SOL-USDT"
    assert got["missing"] == []


# --- OMS wiring ---


def test_oms_refuses_live_client(tmp_path: Path):
    live = _client("live")
    with pytest.raises(LiveTradingBlocked, match="demo-only"):
        SpotDemoOms(live, data_dir=tmp_path)


def test_oms_refresh_zero_equity_fail_closed(tmp_path: Path):
    c = _client("demo", total_eq="0")
    oms = SpotDemoOms(c, data_dir=tmp_path)
    with pytest.raises(DemoFundsMissing, match="[Cc]laim demo funds"):
        oms.refresh_account()


def test_oms_refresh_zero_equity_snapshot_allowed(tmp_path: Path):
    c = _client("demo", total_eq="0")
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account(fail_closed_zero=False)
    assert snap.total_eq == 0.0
    assert not snap.funds_ok
    assert snap.acct_lv_name == "simple"


def test_oms_gate_kill_blocks_entry(tmp_path: Path):
    c = _client("demo", total_eq="190")
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    oms._state["paper_day_start"] = 200.0
    oms._state["paper_pnl"] = -10.0
    oms._state["killed"] = False
    oms._state["kill_reason"] = None
    kill = oms.check_kill(snap)
    assert kill["killed"] is True
    assert kill["threshold"] == pytest.approx(10.0)
    gate = oms.gate_new_entry(snap)
    assert not gate["allowed"]
    assert gate["reason"] == "daily_kill"


def test_oms_faucet_inventory_does_not_block(tmp_path: Path):
    c = _client(
        "demo",
        total_eq="200",
        details=[
            {"ccy": "USDT", "eq": "180", "cashBal": "180", "availBal": "180", "frozenBal": "0"},
            {"ccy": "PEPE", "eq": "500000", "cashBal": "500000", "availBal": "500000", "frozenBal": "0"},
        ],
    )
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    oms._state["day_start_total_eq"] = 200.0
    oms._state["killed"] = False
    gate = oms.gate_new_entry(snap)
    assert gate["allowed"]
    assert gate["reason"] == "ok"
    assert any(h["ccy"] == "PEPE" for h in gate.get("held") or [])


def test_oms_one_position_open_inst_and_pending(tmp_path: Path):
    # Sticky open_inst with empty pending is the cancel bug: must clear and allow.
    c = _client("demo", total_eq="200")
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    oms._state["day_start_total_eq"] = 200.0
    oms._state["killed"] = False
    oms._state["open_inst"] = "DOGE-USDT"
    gate = oms.gate_new_entry(snap)
    assert oms._state["open_inst"] is None
    assert gate["allowed"]
    assert gate["reason"] == "ok"

    c2 = _client(
        "demo",
        total_eq="200",
        pending=[{"instId": "DOGE-USDT", "ordId": "9", "state": "live", "side": "buy", "sz": "10"}],
    )
    oms2 = SpotDemoOms(c2, data_dir=tmp_path)
    snap2 = oms2.refresh_account()
    oms2._state["day_start_total_eq"] = 200.0
    oms2._state["killed"] = False
    gate2 = oms2.gate_new_entry(snap2, inst_ids={"DOGE-USDT"})
    assert not gate2["allowed"]
    assert gate2["reason"] == "one_position_pending"


def test_oms_place_dry_run_does_not_post(tmp_path: Path):
    calls: list = []
    c = _client("demo", allow_trade=True, calls=calls, total_eq="200")
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    inst = oms.resolve_symbol("DOGE-USDT")
    last = oms.last_price("DOGE-USDT")
    plan = oms.size_order(snap, inst, last_px=last, tiny=True, px=last * 0.5)
    assert plan.allowed
    out = oms.place(plan, dry_run=True)
    assert out["placed"] is False
    assert out["reason"] == "dry_run"
    posts = [x for x in calls if x["method"] == "POST"]
    assert posts == []


def test_oms_place_requires_allow_trade(tmp_path: Path):
    c = _client("demo", allow_trade=False, total_eq="200")
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    inst = oms.resolve_symbol("DOGE-USDT")
    plan = oms.size_order(snap, inst, last_px=0.15, tiny=True, px=0.08)
    assert plan.allowed
    with pytest.raises(PaperTradeDisabled):
        oms.place(plan, dry_run=False)


def test_live_place_spot_never_sends_http():
    calls: list = []
    c = _client("live", calls=calls)
    with pytest.raises(LiveTradingBlocked):
        c.place_spot_limit("DOGE-USDT", "buy", "10", "0.05")
    with pytest.raises(LiveTradingBlocked):
        c.place_spot_market("DOGE-USDT", "buy", "10")
    with pytest.raises(LiveTradingBlocked):
        c.cancel_order(instId="DOGE-USDT", ordId="1")
    assert calls == []


def test_demo_place_spot_limit_sends_simulated_and_cash():
    calls: list = []
    c = _client("demo", allow_trade=True, calls=calls)
    payload = c.place_spot_limit("DOGE-USDT", "buy", "10", "0.05")
    assert payload["code"] == "0"
    assert calls[0]["has_sim"] == "1"
    assert calls[0]["method"] == "POST"
    assert '"tdMode":"cash"' in calls[0]["body"]
    assert '"ordType":"limit"' in calls[0]["body"]


def test_demo_place_spot_refuses_swap_inst():
    c = _client("demo", allow_trade=True)
    with pytest.raises(ValueError, match="BASE-QUOTE"):
        c.place_spot_market("BTC-USDT-SWAP", "buy", "1")


def test_oms_real_place_demo_posts_once(tmp_path: Path):
    calls: list = []
    c = _client("demo", allow_trade=True, calls=calls, total_eq="200")
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    inst = oms.resolve_symbol("DOGE-USDT")
    plan = oms.size_order(snap, inst, last_px=0.15, tiny=True, px=0.08)
    out = oms.place(plan, dry_run=False)
    assert out["placed"] is True
    posts = [x for x in calls if x["method"] == "POST"]
    assert len(posts) == 1
    assert posts[0]["has_sim"] == "1"
    assert "/api/v5/trade/order" in posts[0]["path"]


def test_journal_has_no_secrets(tmp_path: Path):
    c = _client("demo", total_eq="200")
    oms = SpotDemoOms(c, data_dir=tmp_path, run_id="sec-test")
    oms.refresh_account()
    dumped = ""
    for path in (tmp_path / "oms").rglob("*.jsonl"):
        dumped += path.read_text(encoding="utf-8")
    dumped += (tmp_path / "oms" / "state.json").read_text(encoding="utf-8")
    assert "SUPERSECRET" not in dumped
    assert "api_secret" not in dumped.lower() or "***" in dumped
