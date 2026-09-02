from datetime import datetime, timezone

from atlas.okx.signing import iso8601_ms, prehash, sign_okx_v5


# Frozen vectors (dummy secret, not a venue key).
_TS = "2020-12-08T09:08:57.715Z"
_SECRET = "dummy-secret-for-unit-test-only"
_GET_SIG = "IphbF58AxD2d978zgPnve2xPTj+T5EIlq7eLb4O1de4="
_POST_BODY = (
    '{"instId":"BTC-USDT-SWAP","tdMode":"cross","side":"buy",'
    '"ordType":"limit","px":"1000","sz":"0.01"}'
)
_POST_SIG = "mcx20QnYX/IY63n23dZpoHhpJhCmCSc415zt2xKJZHs="


def test_iso8601_ms_format():
    dt = datetime(2020, 12, 8, 9, 8, 57, 715000, tzinfo=timezone.utc)
    assert iso8601_ms(dt) == _TS


def test_sign_get_with_query_known_vector():
    path = "/api/v5/account/balance?ccy=BTC"
    assert prehash(_TS, "GET", path, "") == _TS + "GET" + path
    assert sign_okx_v5(_TS, "get", path, "", _SECRET) == _GET_SIG


def test_sign_post_body_known_vector():
    path = "/api/v5/trade/order"
    sig = sign_okx_v5(_TS, "POST", path, _POST_BODY, _SECRET)
    assert sig == _POST_SIG
    # empty body must not match the POST-with-body signature
    assert sign_okx_v5(_TS, "POST", path, "", _SECRET) != _POST_SIG
