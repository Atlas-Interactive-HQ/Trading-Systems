import httpx
import pytest

from atlas.okx.client import LiveTradingBlocked, OkxEeaClient, PaperTradeDisabled
from atlas.okx.credentials import OkxCredentials
from atlas.okx.instruments import resolve_xperp_universe


def _creds() -> OkxCredentials:
    return OkxCredentials(
        api_key="SUPERSECRETKEYVALUE",
        api_secret="SUPERSECRETSECRETVALUE",
        passphrase="SUPERSECRETPASSPHRASE",
        source_path="/tmp/fake-okx.json",
    )


def _client(mode: str, allow_trade: bool = False, calls: list | None = None) -> OkxEeaClient:
    bucket = calls if calls is not None else []

    def handler(request: httpx.Request) -> httpx.Response:
        bucket.append(
            {
                "method": request.method,
                "url": str(request.url),
                "has_sim": request.headers.get("x-simulated-trading"),
                "has_key": "OK-ACCESS-KEY" in request.headers,
            }
        )
        return httpx.Response(
            200,
            json={"code": "0", "msg": "", "data": [{"totalEq": "0"}]},
        )

    return OkxEeaClient(
        mode=mode,  # type: ignore[arg-type]
        allow_trade=allow_trade,
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
