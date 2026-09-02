import os

import pytest

from atlas.common.config import AppConfig, assert_public_only_path, refuse_if_secrets_present


def test_refuse_if_api_key_set(monkeypatch):
    monkeypatch.setenv("OKX_API_KEY", "not-a-real-key")
    with pytest.raises(SystemExit) as ei:
        refuse_if_secrets_present(AppConfig())
    assert "OKX_API_KEY" in str(ei.value)


def test_assert_public_only_path():
    assert_public_only_path("/api/v5/public/tickers")
    with pytest.raises(PermissionError):
        assert_public_only_path("/api/v5/trade/order")
