from atlas.common.time import parse_exchange_ts_ms, utc_date_str


def test_parse_ms_and_seconds():
    assert parse_exchange_ts_ms(1_700_000_000_000) == 1_700_000_000_000
    assert parse_exchange_ts_ms(1_700_000_000) == 1_700_000_000_000
    assert parse_exchange_ts_ms("1700000000000") == 1_700_000_000_000
    assert parse_exchange_ts_ms(None) is None


def test_utc_date_str():
    # 2024-05-01 roughly
    assert utc_date_str(1_714_550_400_000) == "2024-05-01"
