import httpx
import respx

from atlas.common.config import AppConfig, VenueConfig
from atlas.collectors.kraken_futures_public import KrakenFuturesPublicCollector


@respx.mock
def test_kraken_tickers_mocked(tmp_path):
    cfg = AppConfig(
        data_dir=str(tmp_path),
        venues={
            "kraken_futures": VenueConfig(
                venue="kraken_deriv",
                rest_base="https://futures.kraken.com/derivatives/api/v3",
                ws_url="wss://futures.kraken.com/ws/v1",
                symbols=["PF_XBTUSD"],
                rest_poll_sec=0.1,
            )
        },
    )
    respx.get("https://futures.kraken.com/derivatives/api/v3/instruments").mock(
        return_value=httpx.Response(200, json={"result": "success", "instruments": []})
    )
    respx.get("https://futures.kraken.com/derivatives/api/v3/tickers").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": "success",
                "tickers": [{"symbol": "PF_XBTUSD", "last": "50000", "time": 1700000000000}],
            },
        )
    )
    c = KrakenFuturesPublicCollector(cfg)
    summary = c.run_rest_poll(duration_sec=0.05)
    assert summary["local_seq"] >= 2
    raw_root = tmp_path / "raw" / "kraken_deriv"
    assert raw_root.exists()
    files = list(raw_root.rglob("*.jsonl"))
    assert files
