import json
from pathlib import Path

from atlas.storage.raw import JsonlRawWriter


def test_jsonl_writer_append(tmp_path: Path):
    w = JsonlRawWriter(tmp_path, "kraken_deriv")
    p1 = w.write_dict(
        channel="ticker",
        payload={"a": 1},
        local_seq=1,
        ingest_run_id="r1",
        receive_ts=1_720_000_000_000,
        exchange_ts=1_720_000_000_000,
        venue_instrument_id="PF_XBTUSD",
    )
    p2 = w.write_dict(
        channel="ticker",
        payload={"a": 2},
        local_seq=2,
        ingest_run_id="r1",
        receive_ts=1_720_000_000_000,
    )
    assert p1 == p2
    assert p1.exists()
    lines = p1.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert row["venue"] == "kraken_deriv"
    assert row["payload"]["a"] == 1
    assert "receive_ts" in row and "exchange_ts" in row
