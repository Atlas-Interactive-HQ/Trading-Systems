"""Unit tests for Layer B OKX capture instId allowlist (no network)."""
from __future__ import annotations

import pytest

from atlas.collectors.okx_eea_public import (
    LAYER_B_DOGE_XPERP_MD_INST,
    LAYER_B_WS_CHANNELS,
    OkxEeaPublicCollector,
)


def test_default_resolves_to_doge_xperp_md():
    assert OkxEeaPublicCollector.resolve_capture_inst_ids(None) == [
        LAYER_B_DOGE_XPERP_MD_INST
    ]
    assert OkxEeaPublicCollector.resolve_capture_inst_ids([]) == [
        LAYER_B_DOGE_XPERP_MD_INST
    ]


def test_proxy_swap_refused_without_flag():
    with pytest.raises(ValueError, match="classic SWAP"):
        OkxEeaPublicCollector.resolve_capture_inst_ids(["DOGE-USDT-SWAP"])


def test_proxy_swap_allowed_with_flag():
    out = OkxEeaPublicCollector.resolve_capture_inst_ids(
        ["DOGE-USDT-SWAP"], allow_proxy_swap=True
    )
    assert out == ["DOGE-USDT-SWAP"]


def test_usdc_swap_always_refused():
    with pytest.raises(ValueError, match="51001"):
        OkxEeaPublicCollector.resolve_capture_inst_ids(["DOGE-USDC-SWAP"])


def test_demo_order_inst_refused():
    with pytest.raises(ValueError, match="demo"):
        OkxEeaPublicCollector.resolve_capture_inst_ids(
            ["DOGE-USD_UM_XPERP-310516"]
        )


def test_layer_b_channels_include_books5_trades_mark_funding():
    assert set(LAYER_B_WS_CHANNELS) == {
        "books5",
        "trades",
        "mark-price",
        "funding-rate",
    }
