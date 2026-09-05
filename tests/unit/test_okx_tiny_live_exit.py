"""live20 resting exits: dry-run / incomplete flags / cap fail closed; place does not auto-cancel."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from atlas.okx.client import TINY_LIVE_NOTIONAL_CAP, LiveTradingBlocked, OkxEeaClient
from atlas.okx.credentials import OkxCredentials
from atlas.okx.live20 import LOCKED_INST, SOURCE_EXIT, run_resting_exits


def _creds() -> OkxCredentials:
    return OkxCredentials(
        api_key="SUPERSECRETKEYVALUE",
        api_secret="SUPERSECRETSECRETVALUE",
        passphrase="SUPERSECRETPASSPHRASE",
        source_path="/tmp/fake-okx.json",
    )


def _balance(doge: str = "281", usdc: str = "0") -> dict:
    details = [
        {"ccy": "DOGE", "eq": doge, "availBal": doge, "cashBal": doge, "frozenBal": "0"},
    ]
    if float(usdc or 0) > 0:
        details.append(
            {"ccy": "USDC", "eq": usdc, "availBal": usdc, "cashBal": usdc, "frozenBal": "0"}
        )
    return {"code": "0", "msg": "", "data": [{"totalEq": "33.7", "details": details}]}


def _client(
    *,
    calls: list,
    tiny_live: bool = False,
    allow_trade: bool = False,
    bid: str = "0.119",
    ask: str = "0.121",
    last: str = "0.12",
    pending: list[dict] | None = None,
) -> OkxEeaClient:
    pending_rows = list(pending or [])

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
                    "data": [{"instId": inst, "last": last, "bidPx": bid, "askPx": ask}],
                },
            )
        if path.endswith("/account/balance"):
            return httpx.Response(200, json=_balance())
        if path.endswith("/asset/balances"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": []})
        if path.endswith("/trade/orders-pending"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": pending_rows})
        if method == "POST" and path.endswith("/trade/order"):
            payload = json.loads(body) if body else {}
            assert payload.get("ordType") == "limit"
            assert payload.get("side") == "sell"
            assert payload.get("instId") == "DOGE-USDC"
            oid = "TP1" if float(payload.get("px") or 0) > float(last) else "PROT1"
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [{"ordId": oid, "sCode": "0", "sMsg": "", "state": "live"}],
                },
            )
        if method == "POST" and path.endswith("/trade/cancel-order"):
            payload = json.loads(body) if body else {}
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [{"ordId": payload.get("ordId"), "sCode": "0"}],
                },
            )
        return httpx.Response(404, json={"code": "404", "msg": path, "data": []})

    return OkxEeaClient(
        mode="live",
        allow_trade=allow_trade,
        tiny_live=tiny_live,
        credentials=_creds(),
        transport=httpx.MockTransport(handler),
    )


def _posts(calls: list) -> list:
    return [x for x in calls if x["method"] == "POST"]


def test_dry_run_no_post(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls)
    out = run_resting_exits(c, data_dir=tmp_path)
    assert out["dry_run"] is True
    assert out["ok"] is True
    assert out["source"] == SOURCE_EXIT
    assert _posts(calls) == []
    assert any(x["path"].endswith("/account/balance") for x in calls)
    assert any(x["path"].endswith("/trade/orders-pending") for x in calls)
    assert any("DOGE-USDC" in x["url"] for x in calls if x["path"].endswith("/market/ticker"))


def test_place_tp_without_flags_no_post(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True)
    out = run_resting_exits(c, place_tp=True, data_dir=tmp_path)
    assert out["ok"] is False
    assert _posts(calls) == []
    out2 = run_resting_exits(c, place_tp=True, sz="50", data_dir=tmp_path)
    assert out2["ok"] is False
    assert _posts(calls) == []


def test_notional_over_20_no_post(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True, bid="1.0", ask="1.01", last="1.0")
    out = run_resting_exits(
        c,
        place_tp=True,
        px=1.05,
        sz="50",
        max_notional=20.0,
        data_dir=tmp_path,
    )
    assert out["ok"] is False
    assert "notional" in str(out.get("error") or "").lower() or "exceeds" in str(out.get("error") or "")
    assert _posts(calls) == []
    assert TINY_LIVE_NOTIONAL_CAP == 20.0


def test_place_tp_leaves_resting_no_cancel(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True)
    out = run_resting_exits(
        c,
        place_tp=True,
        tp_pct=5.0,
        sz="50",
        max_notional=10.0,
        data_dir=tmp_path,
    )
    assert out["ok"] is True
    assert out["left_resting"] is True
    posts = _posts(calls)
    place = [x for x in posts if x["path"].endswith("/trade/order")]
    cancel = [x for x in posts if x["path"].endswith("/trade/cancel-order")]
    assert len(place) == 1
    assert cancel == []
    body = json.loads(place[0]["body"])
    assert body["side"] == "sell"
    assert body["ordType"] == "limit"
    assert body["instId"] == "DOGE-USDC"
    assert body["sz"] == "50"
    assert float(body["px"]) > 0.12
    assert all(x["has_sim"] is None for x in posts)
    events = next((tmp_path / "live20").rglob("events.jsonl"))
    text = events.read_text(encoding="utf-8")
    assert "SUPERSECRET" not in text
    assert SOURCE_EXIT in text
    assert "leave_resting" in text


def test_protect_without_px_no_post(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True)
    out = run_resting_exits(c, place_protect=True, sz="50", data_dir=tmp_path)
    assert out["ok"] is False
    assert _posts(calls) == []


def test_protect_px_not_below_mid_no_post(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True)
    out = run_resting_exits(
        c, place_protect=True, px=0.13, sz="50", data_dir=tmp_path
    )
    assert out["ok"] is False
    assert "below mid" in str(out.get("error") or "")
    assert _posts(calls) == []


def test_tp_px_not_above_mid_no_post(tmp_path: Path):
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True)
    out = run_resting_exits(c, place_tp=True, px=0.10, sz="50", data_dir=tmp_path)
    assert out["ok"] is False
    assert "above mid" in str(out.get("error") or "")
    assert _posts(calls) == []


def test_cancel_ord(tmp_path: Path):
    calls: list = []
    pending = [
        {
            "ordId": "RESTING1",
            "instId": "DOGE-USDC",
            "side": "sell",
            "px": "0.15",
            "sz": "50",
            "state": "live",
            "ordType": "limit",
        }
    ]
    c = _client(calls=calls, tiny_live=True, allow_trade=True, pending=pending)
    out = run_resting_exits(c, cancel_ord="RESTING1", data_dir=tmp_path)
    assert out["ok"] is True
    cancel = [x for x in _posts(calls) if x["path"].endswith("/trade/cancel-order")]
    place = [x for x in _posts(calls) if x["path"].endswith("/trade/order")]
    assert len(cancel) == 1
    assert place == []
    assert json.loads(cancel[0]["body"])["ordId"] == "RESTING1"
    assert json.loads(cancel[0]["body"])["instId"] == "DOGE-USDC"


def test_cancel_all_pending_doge_usdc_only(tmp_path: Path):
    calls: list = []
    pending = [
        {
            "ordId": "A",
            "instId": "DOGE-USDC",
            "side": "sell",
            "px": "0.15",
            "sz": "50",
            "state": "live",
            "ordType": "limit",
        },
        {
            "ordId": "B",
            "instId": "DOGE-USDT",
            "side": "sell",
            "px": "0.15",
            "sz": "50",
            "state": "live",
            "ordType": "limit",
        },
        {
            "ordId": "C",
            "instId": "DOGE-USDC",
            "side": "sell",
            "px": "0.16",
            "sz": "10",
            "state": "live",
            "ordType": "limit",
        },
    ]
    c = _client(calls=calls, tiny_live=True, allow_trade=True, pending=pending)
    out = run_resting_exits(c, cancel_all=True, data_dir=tmp_path)
    assert out["ok"] is True
    cancel = [x for x in _posts(calls) if x["path"].endswith("/trade/cancel-order")]
    ids = [json.loads(x["body"])["ordId"] for x in cancel]
    assert ids == ["A", "C"]
    assert "B" not in ids


def test_market_refused_on_tiny_live_client():
    calls: list = []
    c = _client(calls=calls, tiny_live=True, allow_trade=True)
    with pytest.raises(LiveTradingBlocked, match="market"):
        c.place_spot_market("DOGE-USDC", "sell", "50")
    assert _posts(calls) == []


def test_cli_dry_run_and_tp_without_flags(tmp_path: Path):
    import importlib.util

    path = Path(__file__).resolve().parents[2] / "scripts" / "okx_tiny_live_exit.py"
    spec = importlib.util.spec_from_file_location("okx_tiny_live_exit", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    calls: list = []
    c = _client(calls=calls)
    code = mod.main(["--data-dir", str(tmp_path)], client=c)
    assert code == 0
    assert _posts(calls) == []
    c2_calls: list = []
    c2 = _client(calls=c2_calls, tiny_live=True, allow_trade=True)
    code2 = mod.main(["--place-tp", "--sz", "50", "--data-dir", str(tmp_path)], client=c2)
    assert code2 != 0
    assert _posts(c2_calls) == []
