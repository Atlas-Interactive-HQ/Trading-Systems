import importlib.util
from pathlib import Path

import httpx
import pytest

from atlas.okx.client import (
    TINY_LIVE_NOTIONAL_CAP,
    LiveTradingBlocked,
    OkxEeaClient,
    PaperTradeDisabled,
    estimate_spot_limit_notional,
)
from atlas.okx.credentials import OkxCredentials
from atlas.okx.instruments import resolve_xperp_universe

ROOT = Path(__file__).resolve().parents[2]


def _creds() -> OkxCredentials:
    return OkxCredentials(
        api_key="SUPERSECRETKEYVALUE",
        api_secret="SUPERSECRETSECRETVALUE",
        passphrase="SUPERSECRETPASSPHRASE",
        source_path="/tmp/fake-okx.json",
    )


def _client(
    mode: str,
    allow_trade: bool = False,
    calls: list | None = None,
    *,
    tiny_live: bool = False,
) -> OkxEeaClient:
    bucket = calls if calls is not None else []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        bucket.append(
            {
                "method": request.method,
                "url": str(request.url),
                "path": path,
                "has_sim": request.headers.get("x-simulated-trading"),
                "has_key": "OK-ACCESS-KEY" in request.headers,
                "body": request.content.decode("utf-8") if request.content else "",
            }
        )
        if path.endswith("/market/ticker"):
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [{"instId": "DOGE-USDT", "last": "0.12"}],
                },
            )
        if path.endswith("/account/balance"):
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [
                        {
                            "totalEq": "33.7",
                            "details": [
                                {
                                    "ccy": "DOGE",
                                    "eq": "281",
                                    "availBal": "281",
                                    "cashBal": "281",
                                    "frozenBal": "0",
                                }
                            ],
                        }
                    ],
                },
            )
        if path.endswith("/asset/balances"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": []})
        if path.endswith("/trade/orders-pending"):
            return httpx.Response(200, json={"code": "0", "msg": "", "data": []})
        if path.endswith("/trade/order") or path.endswith("/trade/cancel-order"):
            return httpx.Response(
                200,
                json={
                    "code": "0",
                    "msg": "",
                    "data": [{"ordId": "99", "sCode": "0", "sMsg": ""}],
                },
            )
        return httpx.Response(
            200,
            json={"code": "0", "msg": "", "data": [{"totalEq": "0"}]},
        )

    return OkxEeaClient(
        mode=mode,  # type: ignore[arg-type]
        allow_trade=allow_trade,
        tiny_live=tiny_live,
        credentials=_creds(),
        transport=httpx.MockTransport(handler),
    )


def test_live_allow_trade_rejected_at_init():
    with pytest.raises(LiveTradingBlocked, match="allow_trade is forbidden"):
        _client("live", allow_trade=True)


def test_live_place_order_never_sends_http():
    calls: list = []
    c = _client("live", allow_trade=False, calls=calls)
    with pytest.raises(LiveTradingBlocked):
        c.place_order(instId="BTC-USD_UM_XPERP-310404", side="buy", sz="1")
    assert calls == []


def test_live_cancel_and_amend_never_send_http():
    calls: list = []
    c = _client("live", calls=calls)
    with pytest.raises(LiveTradingBlocked):
        c.cancel_order(instId="BTC-USD_UM_XPERP-310404", ordId="1")
    with pytest.raises(LiveTradingBlocked):
        c.amend_order(instId="BTC-USD_UM_XPERP-310404", ordId="1", newSz="1")
    assert calls == []


def test_live_balance_read_ok_without_simulated_header():
    calls: list = []
    c = _client("live", calls=calls)
    payload = c.get_balance()
    assert payload["code"] == "0"
    assert len(calls) == 1
    assert calls[0]["method"] == "GET"
    assert "/api/v5/account/balance" in calls[0]["url"]
    assert calls[0]["has_sim"] is None
    assert calls[0]["has_key"] is True


def test_demo_trade_requires_allow_trade_flag():
    calls: list = []
    c = _client("demo", allow_trade=False, calls=calls)
    with pytest.raises(PaperTradeDisabled):
        c.place_order(instId="BTC-USD_UM_XPERP-310404", side="buy", sz="1")
    assert calls == []


def test_demo_trade_sends_simulated_header_when_allowed():
    calls: list = []
    c = _client("demo", allow_trade=True, calls=calls)
    payload = c.place_order(instId="BTC-USD_UM_XPERP-310404", tdMode="cross", side="buy", sz="1")
    assert payload["code"] == "0"
    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert calls[0]["has_sim"] == "1"


def test_demo_balance_always_sends_simulated_header():
    calls: list = []
    c = _client("demo", allow_trade=False, calls=calls)
    c.get_balance()
    assert calls[0]["has_sim"] == "1"


def test_credentials_repr_does_not_leak():
    c = _creds()
    dumped = repr(c) + str(c)
    assert "SUPERSECRET" not in dumped
    assert "***" in dumped


def test_tiny_live_without_allow_trade_blocked():
    with pytest.raises(LiveTradingBlocked, match="tiny_live requires allow_trade"):
        _client("live", allow_trade=False, tiny_live=True)


def test_tiny_live_notional_over_cap_no_http():
    calls: list = []
    c = _client("live", allow_trade=True, tiny_live=True, calls=calls)
    with pytest.raises(LiveTradingBlocked, match="notional"):
        c.place_spot_limit("DOGE-USDT", "sell", "10", "3")  # 30 > 20
    assert calls == []
    assert TINY_LIVE_NOTIONAL_CAP == 20.0
    assert estimate_spot_limit_notional("10", "3") == pytest.approx(30.0)


def test_tiny_live_missing_sz_px_no_http():
    calls: list = []
    c = _client("live", allow_trade=True, tiny_live=True, calls=calls)
    with pytest.raises(LiveTradingBlocked, match="instId, sz, and px"):
        c.place_order(instId="DOGE-USDT", side="sell", tdMode="cash", ordType="limit")
    with pytest.raises(LiveTradingBlocked, match="instId, sz, and px"):
        c.place_order(
            instId="DOGE-USDT", side="sell", sz="10", tdMode="cash", ordType="limit"
        )
    with pytest.raises(LiveTradingBlocked, match="market"):
        c.place_spot_market("DOGE-USDT", "sell", "10")
    assert calls == []


def test_tiny_live_limit_under_cap_posts_then_cancel_without_sim_header():
    calls: list = []
    c = _client("live", allow_trade=True, tiny_live=True, calls=calls)
    placed = c.place_spot_limit("DOGE-USDT", "sell", "10", "0.24")
    assert placed["code"] == "0"
    c.cancel_order(instId="DOGE-USDT", ordId="99")
    posts = [x for x in calls if x["method"] == "POST"]
    assert len(posts) == 2
    assert all(x["has_sim"] is None for x in posts)
    assert "/api/v5/trade/order" in posts[0]["url"]
    assert "/api/v5/trade/cancel-order" in posts[1]["url"]


def test_live_get_balance_still_ok_without_tiny_live():
    calls: list = []
    c = _client("live", calls=calls)
    c.get_balance()
    c.get_asset_balances()
    assert all(x["method"] == "GET" for x in calls)
    assert all(x["has_sim"] is None for x in calls)


def _load_smoke():
    path = ROOT / "scripts" / "okx_tiny_live_smoke.py"
    spec = importlib.util.spec_from_file_location("okx_tiny_live_smoke", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_smoke_dry_run_does_not_post():
    calls: list = []
    c = _client("live", allow_trade=False, tiny_live=False, calls=calls)
    smoke = _load_smoke()
    code = smoke.main([], client=c)
    assert code == 0
    assert all(x["method"] == "GET" for x in calls)
    posts = [x for x in calls if x["method"] == "POST"]
    assert posts == []
    paths = {x["path"] for x in calls}
    assert any(p.endswith("/account/balance") for p in paths)
    assert any(p.endswith("/asset/balances") for p in paths)
    assert any(p.endswith("/market/ticker") for p in paths)
    assert any(p.endswith("/trade/orders-pending") for p in paths)


def test_smoke_one_flag_still_dry_run_no_post():
    calls: list = []
    c = _client("live", allow_trade=False, calls=calls)
    smoke = _load_smoke()
    code = smoke.main(["--place-far-limit"], client=c)
    assert code == 0
    assert [x for x in calls if x["method"] == "POST"] == []


def test_smoke_mutate_places_far_limit_and_cancels(capsys: pytest.CaptureFixture[str]):
    calls: list = []
    c = _client("live", allow_trade=True, tiny_live=True, calls=calls)
    smoke = _load_smoke()
    code = smoke.main(["--place-far-limit", "--cancel"], client=c)
    assert code == 0
    out = capsys.readouterr().out
    assert "SUPERSECRET" not in out
    assert "api_key" not in out.lower() or "***" in out
    posts = [x for x in calls if x["method"] == "POST"]
    assert len(posts) == 2
    assert '"side":"sell"' in posts[0]["body"]
    assert '"ordType":"limit"' in posts[0]["body"]
    assert '"sz":"10"' in posts[0]["body"]
    # px = 2 × last 0.12 = 0.24
    assert "0.24" in posts[0]["body"]
    assert "/cancel-order" in posts[1]["url"]


def test_resolve_xperp_universe_picks_primary_and_backup():
    rows = [
        {
            "instId": "BTC-USD_UM_XPERP-310404",
            "uly": "BTC-USD",
            "ruleType": "xperp",
            "state": "live",
            "settleCcy": "USD",
            "instType": "FUTURES",
            "minSz": "1",
            "ctVal": "0.0001",
            "ctValCcy": "BTC",
            "lotSz": "1",
            "lever": "50",
            "instFamily": "BTC-USD_UM_XPERP",
        },
        {
            "instId": "ETH-USD_UM_XPERP-310404",
            "uly": "ETH-USD",
            "ruleType": "xperp",
            "state": "live",
            "settleCcy": "USD",
        },
        {
            "instId": "DOGE-USD_UM_XPERP-310404",
            "uly": "DOGE-USD",
            "ruleType": "xperp",
            "state": "live",
            "settleCcy": "USD",
            "instFamily": "DOGE-USD_UM_XPERP",
        },
        {
            "instId": "PEPE-USD_UM_XPERP-310404",
            "uly": "PEPE-USD",
            "ruleType": "xperp",
            "state": "live",
            "settleCcy": "USD",
        },
        {
            "instId": "SOL-USD_UM_XPERP-310404",
            "uly": "SOL-USD",
            "ruleType": "xperp",
            "state": "live",
            "settleCcy": "USD",
        },
        {
            "instId": "BTC-USDT-SWAP",
            "uly": "BTC-USDT",
            "ruleType": "normal",
            "state": "live",
        },
    ]
    got = resolve_xperp_universe(rows)
    ids = {r["base"]: r["instId"] for r in got["resolved"]}
    assert ids["BTC"] == "BTC-USD_UM_XPERP-310404"
    assert ids["DOGE"] == "DOGE-USD_UM_XPERP-310404"
    assert ids["PEPE"] == "PEPE-USD_UM_XPERP-310404"
    assert ids["SOL"] == "SOL-USD_UM_XPERP-310404"
    assert got["missing"] == []
