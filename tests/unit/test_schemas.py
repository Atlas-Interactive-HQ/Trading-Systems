from atlas.schemas.raw import RawEnvelope


def test_raw_envelope_parse_smoke():
    env = RawEnvelope(
        venue="kraken_deriv",
        channel="ticker",
        venue_instrument_id="PF_XBTUSD",
        exchange_ts=1_700_000_000_000,
        receive_ts=1_700_000_000_100,
        local_seq=1,
        ingest_run_id="test-run",
        payload={"symbol": "PF_XBTUSD", "last": 50000},
    )
    d = env.to_jsonl_dict()
    assert d["venue"] == "kraken_deriv"
    assert d["exchange_ts"] == 1_700_000_000_000
    assert d["schema_version"] == "raw.envelope.v1"
    again = RawEnvelope.model_validate(d)
    assert again.local_seq == 1
