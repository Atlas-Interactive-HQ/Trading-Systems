"""DOGE demo OMS: clear-on-cancel, venue routing, xperp isolated ≤2x. No live."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from atlas.common.config import load_config
from atlas.okx.client import LiveTradingBlocked, OkxEeaClient, PaperTradeDisabled
from atlas.okx.credentials import OkxCredentials
from atlas.okx.instruments import assert_xperp_inst_id
from atlas.oms.doge_demo_loop import (
    LOCKED_SPOT_INST,
    LOCKED_XPERP_INST,
    PUBLIC_XPERP_MD_INST,
    DogeDemoLoop,
    VenueRoutingError,
    parse_venue_arg,
    pick_doge_xperp_inst,
    pick_doge_xperp_md_inst,
    scan_signals,
    venues_from_config,
)
from atlas.oms.spot_demo import SpotDemoOms, cap_xperp_leverage, size_xperp
from atlas.paper.types import Bar
from atlas.strategy.breakout import BreakoutParams, BreakoutV1


def _creds() -> OkxCredentials:
    return OkxCredentials(
        api_key="SUPERSECRETKEYVALUE",
        api_secret="SUPERSECRETSECRETVALUE",
        passphrase="SUPERSECRETPASSPHRASE",
        source_path="/tmp/fake-okx.json",
    )


def _balance_payload(total_eq: str = "200") -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "totalEq": total_eq,
                "details": [
                    {
                        "ccy": "USD",
                        "eq": total_eq,
                        "cashBal": total_eq,
                        "availBal": total_eq,
                        "frozenBal": "0",
                    }
                ],
            }
        ],
    }


def _spot_rows() -> list[dict]:
    return [
        {
            "instId": "DOGE-USD",
            "instType": "SPOT",
            "baseCcy": "DOGE",
            "quoteCcy": "USD",
            "state": "live",
            "minSz": "10",
            "lotSz": "1",
            "tickSz": "0.00001",
        }
    ]


def _xperp_rows() -> list[dict]:
    return [
        {
            "instId": "DOGE-USD_UM_XPERP-310516",
            "instType": "FUTURES",
            "uly": "DOGE-USD",
            "ruleType": "xperp",
            "state": "live",
            "settleCcy": "USD",
            "minSz": "1",
            "lotSz": "1",
            "tickSz": "0.00001",
            "ctVal": "10",
            "ctValCcy": "DOGE",
            "lever": "20",
        }
    ]


def _client(
    mode: str,
    allow_trade: bool = False,
    calls: list | None = None,
    *,
    pending: list | None = None,
    positions: list | None = None,
    cancel_s_code: str = "0",
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
            return httpx.Response(200, json=_balance_payload())
        if path.endswith("/account/config"):
            return httpx.Response(
                200, json={"code": "0", "msg": "", "data": [{"acctLv": "2", "posMode": "net_mode"}]}
            )
        if path.endswith("/account/positions"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": positions or []})
        if path.endswith("/public/instruments") or path.endswith("/account/instruments"):
            inst_type = request.url.params.get("instType", "SPOT")
            rows = _spot_rows() if inst_type == "SPOT" else _xperp_rows()
            return httpx.Response(200, json={"code": "0", "msg": "", "data": rows})
        if path.endswith("/market/ticker"):
            inst = request.url.params.get("instId", "DOGE-USD")
            return httpx.Response(
                200, json={"code": "0", "msg": "", "data": [{"instId": inst, "last": "0.15"}]}
            )
        if path.endswith("/trade/orders-pending"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": pending or []})
        if path.endswith("/account/set-leverage") or path.endswith("/trade/order"):
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [{"ordId": "42", "clOrdId": "", "sCode": "0", "sMsg": ""}],
                },
            )
        if path.endswith("/trade/cancel-order"):
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [{"ordId": "42", "sCode": cancel_s_code, "sMsg": ""}],
                },
            )
        return httpx.Response(404, json={"code": "404", "msg": path, "data": []})

    return OkxEeaClient(
        mode=mode,  # type: ignore[arg-type]
        allow_trade=allow_trade,
        credentials=_creds(),
        transport=httpx.MockTransport(handler),
    )


# --- venue routing ---


def test_parse_venue_arg():
    assert parse_venue_arg("spot") == ("spot",)
    assert parse_venue_arg("xperp") == ("xperp",)
    assert parse_venue_arg("both") == ("spot", "xperp")
    with pytest.raises(VenueRoutingError):
        parse_venue_arg("pepe")
    with pytest.raises(VenueRoutingError):
        parse_venue_arg("live")


def test_venues_from_config_locked_doge(tmp_path: Path):
    cfg = load_config()
    both = venues_from_config(cfg, "both")
    ids = {s.key: s.inst_id for s in both}
    assert ids["spot"] == LOCKED_SPOT_INST == "DOGE-USD"
    assert ids["xperp"] == LOCKED_XPERP_INST == "DOGE-USD_UM_XPERP-310516"
    assert all(s.inst_id.startswith("DOGE") for s in both)
    assert not any("PEPE" in s.inst_id for s in both)
    spot = venues_from_config(cfg, "spot")
    assert [s.key for s in spot] == ["spot"]
    assert spot[0].td_mode == "cash"
    xp = venues_from_config(cfg, "xperp")
    assert xp[0].td_mode == "isolated"
    assert xp[0].rule_type == "xperp"
    assert xp[0].leverage == pytest.approx(2.0)
    assert cfg.okx.doge_demo.pepe_enabled is False
    assert cfg.okx.doge_demo.ranging is False
    assert cfg.okx.doge_demo.paper_equity_eur == pytest.approx(200.0)


def test_pick_doge_xperp_order_never_falls_back_to_public_310404():
    rows = [
        {
            "instId": "DOGE-USD_UM_XPERP-310404",
            "uly": "DOGE-USD",
            "ruleType": "xperp",
            "state": "live",
        },
        {
            "instId": "PEPE-USD_UM_XPERP-310404",
            "uly": "PEPE-USD",
            "ruleType": "xperp",
            "state": "live",
        },
    ]
    inst, reason = pick_doge_xperp_inst(rows, "DOGE-USD_UM_XPERP-310516")
    assert inst == "DOGE-USD_UM_XPERP-310516"
    assert reason == "configured_missing"
    assert inst != PUBLIC_XPERP_MD_INST


def test_pick_doge_xperp_md_can_use_public_310404():
    rows = [
        {
            "instId": "DOGE-USD_UM_XPERP-310404",
            "uly": "DOGE-USD",
            "ruleType": "xperp",
            "state": "live",
        },
    ]
    inst, reason = pick_doge_xperp_md_inst(rows, "DOGE-USD_UM_XPERP-310516")
    assert inst == "DOGE-USD_UM_XPERP-310404"
    assert reason in {"public_fallback", "catalogue_live"}
    inst2, reason2 = pick_doge_xperp_md_inst(rows, "DOGE-USD_UM_XPERP-310404")
    assert inst2 == "DOGE-USD_UM_XPERP-310404"
    assert reason2 == "configured"


def test_pick_doge_xperp_order_uses_account_310516():
    rows = _xperp_rows() + [
        {
            "instId": "DOGE-USD_UM_XPERP-310404",
            "uly": "DOGE-USD",
            "ruleType": "xperp",
            "state": "live",
        }
    ]
    inst, reason = pick_doge_xperp_inst(rows, "DOGE-USD_UM_XPERP-310516")
    assert inst == "DOGE-USD_UM_XPERP-310516"
    assert reason == "configured"


def test_assert_xperp_inst_id_refuses_spot():
    with pytest.raises(ValueError, match="xperp"):
        assert_xperp_inst_id("DOGE-USD")
    assert assert_xperp_inst_id("doge-usd_um_xperp-310516") == "DOGE-USD_UM_XPERP-310516"


# --- state clear on cancel / pending empty ---


def test_cancel_clears_open_inst(tmp_path: Path):
    c = _client("demo", allow_trade=True)
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    inst = oms.resolve_symbol("DOGE-USD")
    plan = oms.size_order(snap, inst, last_px=0.15, tiny=True, px=0.08)
    out = oms.place(plan, dry_run=False)
    assert out["placed"] is True
    assert oms._state["open_inst"] == "DOGE-USD"
    cancel = oms.cancel("DOGE-USD", "42")
    assert cancel["open_inst_cleared"] is True
    assert oms._state["open_inst"] is None
    assert oms._state["open_ord_id"] is None
    gate = oms.gate_new_entry(snap, inst_ids={"DOGE-USD"})
    assert gate["allowed"] is True


def test_pending_empty_clears_sticky_open_inst(tmp_path: Path):
    c = _client("demo", pending=[])
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    oms._state["open_inst"] = "DOGE-USD"
    oms._state["open_ord_id"] = "stale-9"
    oms._state["killed"] = False
    oms._save_state()
    gate = oms.gate_new_entry(snap, inst_ids={"DOGE-USD"})
    assert oms._state["open_inst"] is None
    assert gate["allowed"] is True
    assert gate["reason"] == "ok"


def test_pending_still_blocks_one_position(tmp_path: Path):
    c = _client(
        "demo",
        pending=[{"instId": "DOGE-USD", "ordId": "9", "state": "live", "side": "buy", "sz": "10"}],
    )
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    oms._state["killed"] = False
    oms._state["open_inst"] = "DOGE-USD"
    gate = oms.gate_new_entry(snap, inst_ids={"DOGE-USD"})
    assert not gate["allowed"]
    assert gate["reason"] == "one_position_pending"
    assert oms._state["open_inst"] == "DOGE-USD"


def test_filled_flat_clears_when_no_futures_pos(tmp_path: Path):
    c = _client("demo", pending=[], positions=[])
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    oms._state["open_inst"] = "DOGE-USD_UM_XPERP-310516"
    oms._state["open_venue"] = "xperp"
    recon = oms.reconcile_open_inst({"DOGE-USD_UM_XPERP-310516"})
    assert recon["cleared"] is True
    assert oms._state["open_inst"] is None
    gate = oms.gate_new_entry(snap, inst_ids={"DOGE-USD_UM_XPERP-310516"})
    assert gate["allowed"]


def test_open_futures_pos_keeps_open_inst(tmp_path: Path):
    c = _client(
        "demo",
        pending=[],
        positions=[{"instId": "DOGE-USD_UM_XPERP-310516", "pos": "1", "posSide": "net"}],
    )
    oms = SpotDemoOms(c, data_dir=tmp_path)
    snap = oms.refresh_account()
    oms._state["open_inst"] = "DOGE-USD_UM_XPERP-310516"
    gate = oms.gate_new_entry(snap, inst_ids={"DOGE-USD_UM_XPERP-310516"})
    assert not gate["allowed"]
    assert gate["reason"] == "one_position"
    assert oms._state["open_inst"] == "DOGE-USD_UM_XPERP-310516"


def test_failed_cancel_does_not_clear(tmp_path: Path):
    c = _client("demo", allow_trade=True, cancel_s_code="1")
    oms = SpotDemoOms(c, data_dir=tmp_path)
    oms._state["open_inst"] = "DOGE-USD"
    oms._state["open_ord_id"] = "42"
    rec = oms.cancel("DOGE-USD", "42")
    assert rec["open_inst_cleared"] is False
    assert oms._state["open_inst"] == "DOGE-USD"


# --- xperp routing / leverage ---


def test_cap_xperp_leverage():
    assert cap_xperp_leverage(2.0) == 2.0
    assert cap_xperp_leverage(5.0) == 2.0
    assert cap_xperp_leverage(1.0) == 1.0


def test_size_xperp_tiny_one_contract():
    plan = size_xperp(
        last_px=0.15,
        ct_val=10.0,
        min_sz=1.0,
        lot_sz=1.0,
        tiny_notional=2.0,
        inst_id="DOGE-USD_UM_XPERP-310516",
        side="sell",
    )
    assert plan.allowed
    assert plan.side == "sell"
    assert float(plan.sz) >= 1.0
    assert plan.notional <= 400.0 + 1e-9  # 2x * 200
    assert plan.extra["leverage"] == pytest.approx(2.0)
    assert plan.extra["tdMode"] == "isolated"


def test_place_xperp_dry_run_no_http(tmp_path: Path):
    calls: list = []
    c = _client("demo", allow_trade=True, calls=calls)
    oms = SpotDemoOms(c, data_dir=tmp_path)
    meta = _xperp_rows()[0]
    plan = oms.size_xperp_order(meta, last_px=0.15, side="buy", tiny=True, px=0.08)
    assert plan.allowed
    out = oms.place_xperp(plan, dry_run=True)
    assert out["placed"] is False
    posts = [x for x in calls if x["method"] == "POST"]
    assert posts == []


def test_place_xperp_sets_isolated_leverage_then_order(tmp_path: Path):
    calls: list = []
    c = _client("demo", allow_trade=True, calls=calls)
    oms = SpotDemoOms(c, data_dir=tmp_path)
    meta = _xperp_rows()[0]
    plan = oms.size_xperp_order(meta, last_px=0.15, side="sell", tiny=True, px=0.20)
    out = oms.place_xperp(plan, dry_run=False, leverage=2.0, set_leverage=True)
    assert out["placed"] is True
    posts = [x for x in calls if x["method"] == "POST"]
    assert any("/account/set-leverage" in x["path"] for x in posts)
    assert any("/trade/order" in x["path"] for x in posts)
    lev = next(x for x in posts if x["path"].endswith("/account/set-leverage"))
    assert '"mgnMode":"isolated"' in lev["body"]
    assert '"lever":"2"' in lev["body"]
    order = next(x for x in posts if x["path"].endswith("/trade/order"))
    assert '"tdMode":"isolated"' in order["body"]
    assert '"ordType":"limit"' in order["body"]
    assert '"side":"sell"' in order["body"]
    assert "posSide" not in order["body"]
    assert oms._state["open_inst"] == "DOGE-USD_UM_XPERP-310516"
    assert oms._state["open_venue"] == "xperp"


def test_live_xperp_never_sends_http():
    calls: list = []
    c = _client("live", calls=calls)
    with pytest.raises(LiveTradingBlocked):
        c.place_xperp_limit("DOGE-USD_UM_XPERP-310516", "buy", "1", "0.08")
    with pytest.raises(LiveTradingBlocked):
        c.set_leverage("DOGE-USD_UM_XPERP-310516", 2)
    with pytest.raises(LiveTradingBlocked):
        SpotDemoOms(c, data_dir="/tmp/oms-live-x")
    assert calls == []


def test_demo_xperp_requires_allow_trade(tmp_path: Path):
    c = _client("demo", allow_trade=False)
    oms = SpotDemoOms(c, data_dir=tmp_path)
    meta = _xperp_rows()[0]
    plan = oms.size_xperp_order(meta, last_px=0.15, tiny=True, px=0.08)
    with pytest.raises(PaperTradeDisabled):
        oms.place_xperp(plan, dry_run=False)


def test_loop_signal_only_never_posts(tmp_path: Path):
    """place_orders=False must not construct/use a trading client."""
    cfg = load_config()
    loop = DogeDemoLoop(cfg, data_dir=tmp_path, oms=None)
    with pytest.raises(PaperTradeDisabled, match="SpotDemoOms"):
        loop.run(venue="spot", place_orders=True, bars=8)


def test_clear_stale_foreign_open_inst(tmp_path: Path):
    c = _client("demo", pending=[], positions=[])
    oms = SpotDemoOms(c, data_dir=tmp_path)
    oms._state["open_inst"] = "SOL-USD"
    oms._state["open_order_id"] = "stale"
    oms._save_state()
    recon = oms.clear_stale_open_state({"DOGE-USD", "DOGE-USD_UM_XPERP-310516"})
    assert oms._state["open_inst"] is None
    assert recon["reason"] in {"pending_empty", "already_flat"}


def test_resolve_xperp_keeps_demo_order_inst(tmp_path: Path):
    public_only = [
        {
            "instId": "DOGE-USD_UM_XPERP-310404",
            "uly": "DOGE-USD",
            "ruleType": "xperp",
            "state": "live",
            "instType": "FUTURES",
        }
    ]

    def public_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/public/instruments"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": public_only})
        return httpx.Response(404, json={"code": "404", "data": []})

    c = _client("demo", allow_trade=True)
    oms = SpotDemoOms(c, data_dir=tmp_path)
    cfg = load_config()
    loop = DogeDemoLoop(cfg, data_dir=tmp_path, oms=oms)
    specs = venues_from_config(cfg, "xperp")
    with httpx.Client(transport=httpx.MockTransport(public_handler)) as client:
        out = loop._resolve_xperp_specs(specs, client)
    assert out[0].inst_id == LOCKED_XPERP_INST == "DOGE-USD_UM_XPERP-310516"
    assert out[0].md_inst_id == PUBLIC_XPERP_MD_INST
    assert "310404" not in out[0].inst_id


def test_plumbing_xperp_uses_310516_then_cancels(tmp_path: Path):
    calls: list = []
    c = _client("demo", allow_trade=True, calls=calls)
    oms = SpotDemoOms(c, data_dir=tmp_path)
    cfg = load_config()
    loop = DogeDemoLoop(cfg, data_dir=tmp_path, oms=oms)
    specs = venues_from_config(cfg, "xperp")
    rec = loop._place_plumbing(specs[0], last_px=0.15, offset_frac=0.40)
    assert rec["placed"] is True
    assert rec["cancelled"] is True
    assert rec["ordId"] == "42"
    assert rec["instId"] == "DOGE-USD_UM_XPERP-310516"
    posts = [x for x in calls if x["method"] == "POST"]
    order = next(x for x in posts if x["path"].endswith("/trade/order"))
    assert "DOGE-USD_UM_XPERP-310516" in order["body"]
    assert "310404" not in order["body"]
    assert any(x["path"].endswith("/trade/cancel-order") for x in posts)


def test_scan_signals_long_and_short():
    s = BreakoutV1(BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="off", min_atr_frac=0.0))
    start = 1_700_000_000_000
    ms = 15 * 60 * 1000

    def b(i, o, h, l, c):
        ts = start + i * ms
        return Bar("DOGE-USD", ts, ts + ms, o, h, l, c, 1.0, True, "test")

    bars = [b(i, 0.10, 0.101, 0.099, 0.10) for i in range(10)]
    bars.append(b(10, 0.10, 0.12, 0.10, 0.12))  # long
    bars.append(b(11, 0.12, 0.12, 0.07, 0.07))  # short
    sigs = scan_signals(s, bars, [])
    sides = [x.side.value for x in sigs]
    assert "long" in sides
    assert "short" in sides
