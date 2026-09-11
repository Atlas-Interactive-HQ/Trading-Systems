"""Scalp-HFT research modules — PAPER_ONLY feature pipelines (no live OMS)."""

from atlas.scalp_hft.health import (
    TradingHealthStats,
    sample_trading_unhealthy,
    summarize_trading_health,
)
from atlas.scalp_hft.vamp import (
    EMA,
    HEALTH_STALE_MS,
    BookTop5,
    Books5IngestStats,
    ReplayGapStats,
    RollingZScore,
    SAMPLE_COLUMNS,
    Vamp1sSample,
    calculate_vamp,
    mid_from_book,
    parse_books5_levels,
    replay_books5_jsonl_to_1s,
    summarize_samples,
    vamp_edge_bps,
)

__all__ = [
    "EMA",
    "HEALTH_STALE_MS",
    "BookTop5",
    "Books5IngestStats",
    "ReplayGapStats",
    "RollingZScore",
    "SAMPLE_COLUMNS",
    "TradingHealthStats",
    "Vamp1sSample",
    "calculate_vamp",
    "mid_from_book",
    "parse_books5_levels",
    "replay_books5_jsonl_to_1s",
    "sample_trading_unhealthy",
    "summarize_samples",
    "summarize_trading_health",
    "vamp_edge_bps",
]
