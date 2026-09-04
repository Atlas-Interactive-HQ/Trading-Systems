"""live20 round-trip: dry-run / cap / flags fail closed; roundtrip only after fill+USDC."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from atlas.okx.client import TINY_LIVE_NOTIONAL_CAP, LiveTradingBlocked, OkxEeaClient
from atlas.okx.credentials import OkxCredentials
from atlas.okx.live20 import LOCKED_INST, run_roundtrip


def _creds() -> OkxCredentials:
    return OkxCredentials(
        api_key="SUPERSECRETKEYVALUE",
        api_secret="SUPERSECRETSECRETVALUE",
        passphrase="SUPERSECRETPASSPHRASE",
        source_path="/tmp/fake-okx.json",
    )


def _balance(doge: str, usdc: str = "0") -> dict:
    details = [
        {"ccy": "DOGE", "eq": doge, "availBal": doge, "cashBal": doge, "frozenBal": "0"},
    ]
    if float(usdc or 0) > 0:
        details.append(
            {"ccy": "USDC", "eq": usdc, "availBal": usdc, "cashBal": usdc, "frozenBal": "0"}
        )
    return {
        "code": "0",
        "msg": "",
        "data": [{"totalEq": "33.7", "details": details}],
    }


def _client(
    *,
    calls: list,
    tiny_live: bool = False,
    allow_trade: bool = False,
    bid: str = "0.119",
    ask: str = "0.121",
    last: str = "0.12",
    fill_sell: bool = True,
    fill_buy: bool = True,
    usdc_after_sell: str = "5.95",
) -> OkxEeaClient:
    state = {"sold": False, "buy_posted": False}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        method = request.method
        body = request.content.decode("utf-8") if request.content else ""
        calls.append(
            {
                "method": method,
                "path": path,
                "url": str(request.url),
                "body": body,
                "has_sim": request.headers.get("x-simulated-trading"),
            }
        )
        if path.endswith("/market/ticker"):
            inst = request.url.params.get("instId") or LOCKED_INST
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [
                        {
                            "instId": inst,
                            "last": last,
                            "bidPx": bid,
                            "askPx": ask,
                        }
                    ],
                },
            )
        if path.endswith("/account/balance"):
            if state["sold"]:
                return httpx.Response(200, json=_balance("231", usdc_after_sell))
            return httpx.Response(200, json=_balance("281", "0"))
        if path.endswith("/asset/balances"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": []})
        if path.endswith("/trade/orders-pending"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": []})
        if method == "POST" and path.endswith("/trade/order"):
            payload = json.loads(body) if body else {}
            assert payload.get("ordType") == "limit"
            side = payload.get("side")
            if side == "sell":
                state["sold"] = fill_sell
                oid = "SELL1"
            else:
                state["buy_posted"] = True
                oid = "BUY1"
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [{"ordId": oid, "sCode": "0", "sMsg": "", "state": "live"}],
                },
            )
        if method == "GET" and path.endswith("/trade/order"):
            oid = request.url.params.get("ordId") or ""
            if oid == "SELL1":
                st = "filled" if fill_sell else "live"
                return httpx.Response(
                    200,
                    json={
                        "code": "0",
                        "msg": "",
                        "data": [
                            {
                                "ordId": oid,
                                "state": st,
                                "side": "sell",
                                "accFillSz": "50" if fill_sell else "0",
                                "avgPx": last,
                                "fee": "-0.001",
                                "feeCcy": "USDC",
                            }
                        ],
                    },
                )
            if oid == "BUY1":
                st = "filled" if fill_buy else "live"
                return httpx.Response(
                    200,
                    json={
                        "code": "0",
                        "msg": "",
                        "data": [
                            {
                                "ordId": oid,
                                "state": st,
                                "side": "buy",
                                "accFillSz": "49" if fill_buy else "0",
                                "avgPx": ask,
                                "fee": "-0.05",
                                "feeCcy": "DOGE",
                            }
                        ],
                    },
                )
            return httpx.Response(200, json={"code": "0", "msg": "", "data": [{"state": "live"}]})
        if method == "POST" and path.endswith("/trade/cancel-order"):
            return httpx.Response(
                200,
                json={"code": "0", "msg": "", "data": [{"ordId": "x", "sCode": "0"}]},
            )
        return httpx.Response(404, json={"code": "404", "msg": path, "data": []})

    return OkxEeaClient(
        mode="live",
        allow_trade=allow_trade,
        tiny_live=tiny_live,
        credentials=_creds(),
        transport=httpx.MockTransport(handler),
    )


def test_dry_run_no_post(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls)
    out = run_roundtrip(c, sell=False, buy=False, data_dir=tmp_path, timeout_s=0, poll_s=0)
    assert out["dry_run"] is True
    assert out["ok"] is True
    assert [x for x in calls if x["method"] == "POST"] == []
    assert any(x["path"].endswith("/account/balance") for x in calls)
    assert any(x["path"].endswith("/asset/balances") for x in calls)
    assert any("DOGE-USDC" in x["url"] for x in calls if x["path"].endswith("/market/ticker"))


def test_sz_without_flags_no_post(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls)
    out = run_roundtrip(c, sell=False, buy=False, sz="50", data_dir=tmp_path)
    assert out["dry_run"] is True
    assert [x for x in calls if x["method"] == "POST"] == []


def test_notional_over_20_no_post(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True, bid="1.0", ask="1.01", last="1.0")
    out = run_roundtrip(
        c,
        sell=True,
        buy=False,
        sz="50",
        max_notional=20.0,
        data_dir=tmp_path,
        timeout_s=0,
        poll_s=0,
    )
    assert out["ok"] is False
    assert "notional" in str(out.get("error") or "").lower() or "exceeds" in str(out.get("error") or "")
    assert [x for x in calls if x["method"] == "POST"] == []
    assert TINY_LIVE_NOTIONAL_CAP == 20.0


def test_market_refused_on_tiny_live_client():
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True)
    with pytest.raises(LiveTradingBlocked, match="market"):
        c.place_spot_market("DOGE-USDC", "sell", "50")
    assert [x for x in calls if x["method"] == "POST"] == []


def test_roundtrip_posts_sell_then_buy_after_fill_and_usdc(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True)
    out = run_roundtrip(
        c,
        sell=True,
        buy=True,
        sz="50",
        max_notional=10.0,
        data_dir=tmp_path,
        timeout_s=1,
        poll_s=0,
        sleep=lambda _s: None,
    )
    assert out["sold"] is True
    assert out["bought"] is True
    assert out["ok"] is True
    posts = [x for x in calls if x["method"] == "POST"]
    place = [x for x in posts if x["path"].endswith("/trade/order")]
    assert len(place) == 2
    sell_body = json.loads(place[0]["body"])
    buy_body = json.loads(place[1]["body"])
    assert sell_body["side"] == "sell"
    assert sell_body["ordType"] == "limit"
    assert sell_body["instId"] == "DOGE-USDC"
    assert sell_body["sz"] == "50"
    assert "market" not in sell_body["ordType"]
    assert buy_body["side"] == "buy"
    assert buy_body["ordType"] == "limit"
    assert buy_body["instId"] == "DOGE-USDC"
    assert all(x["has_sim"] is None for x in posts)
    events = next((tmp_path / "live20").rglob("events.jsonl"))
    text = events.read_text(encoding="utf-8")
    assert "SUPERSECRET" not in text
    assert "live20-roundtrip" in text


def test_roundtrip_skips_buy_if_sell_does_not_fill(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True, fill_sell=False)
    out = run_roundtrip(
        c,
        sell=True,
        buy=True,
        sz="50",
        data_dir=tmp_path,
        timeout_s=0,
        poll_s=0,
        sleep=lambda _s: None,
    )
    assert out["sold"] is False
    assert out["bought"] is False
    place = [x for x in calls if x["method"] == "POST" and x["path"].endswith("/trade/order")]
    assert len(place) == 1
    assert json.loads(place[0]["body"])["side"] == "sell"


def test_cli_dry_run_and_sz_only(tmp_path: Path):
    import importlib.util

    path = Path(__file__).resolve().parents[2] / "scripts" / "okx_tiny_live_roundtrip.py"
    spec = importlib.util.spec_from_file_location("okx_tiny_live_roundtrip", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    calls: list = []
    c = _client(calls=calls)
    code = mod.main(["--sz", "50", "--data-dir", str(tmp_path)], client=c)
    assert code == 0
    assert [x for x in calls if x["method"] == "POST"] == []
