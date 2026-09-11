"""HFT trading-health semantics (phase1/92).

Trading health uses ``health_stale`` + reconnect + timestamp continuity.
``carried_forward`` (legacy ``book_stale``) is feature continuity, not a
health kill by itself.

``seqId`` skips on books5 are **not** treated as missing packets: OKX
books5 snapshots are self-contained.

No HFT PnL is computed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Sequence

from atlas.scalp_hft.vamp import HEALTH_STALE_MS, Vamp1sSample


def _attr(sample: Any, key: str, default: Any = None) -> Any:
    if isinstance(sample, Mapping):
        return sample.get(key, default)
    return getattr(sample, key, default)


def _is_carried(sample: Any) -> bool:
    carried = _attr(sample, "carried_forward")
    if carried is not None:
        return bool(carried)
    return bool(_attr(sample, "book_stale"))


def sample_trading_unhealthy(
    sample: Mapping[str, Any] | Vamp1sSample,
    reconnect_seconds: Optional[set[int]] = None,
) -> bool:
    """True when this 1s sample must not originate a trade.

    Unhealthy if any of:
    - ``health_stale`` (book_age_ms > HEALTH_STALE_MS)
    - ``ts_rewind`` (exchange book timestamp went backwards)
    - reconnect in this second (sidecar or ``reconnect_in_second``)

    ``carried_forward`` / legacy ``book_stale`` alone is NOT unhealthy.
    """
    if _attr(sample, "health_stale"):
        return True
    if _attr(sample, "ts_rewind"):
        return True
    if _attr(sample, "reconnect_in_second"):
        return True
    if reconnect_seconds:
        ts_s = _attr(sample, "ts_s")
        if ts_s is not None and int(ts_s) in reconnect_seconds:
            return True
    return False


def health_reason(
    sample: Mapping[str, Any] | Vamp1sSample,
    reconnect_seconds: Optional[set[int]] = None,
) -> str | None:
    if _attr(sample, "health_stale"):
        return "health_stale"
    if _attr(sample, "ts_rewind"):
        return "ts_rewind"
    if _attr(sample, "reconnect_in_second"):
        return "reconnect_in_second"
    if reconnect_seconds:
        ts_s = _attr(sample, "ts_s")
        if ts_s is not None and int(ts_s) in reconnect_seconds:
            return "reconnect_in_second"
    return None


# Backward-compatible alias used by draft notes.
trading_unhealthy = sample_trading_unhealthy


@dataclass
class TradingHealthStats:
    """Health-only counters. Never attach PnL / expectancy / soft-PASS."""

    n_samples: int = 0
    n_carried_forward: int = 0
    n_health_stale: int = 0
    n_ts_rewind: int = 0
    n_reconnect: int = 0
    n_trading_unhealthy: int = 0
    health_stale_threshold_ms: int = HEALTH_STALE_MS
    reconnect_seconds: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_samples": self.n_samples,
            "n_carried_forward": self.n_carried_forward,
            "n_health_stale": self.n_health_stale,
            "n_ts_rewind": self.n_ts_rewind,
            "n_reconnect": self.n_reconnect,
            "n_trading_unhealthy": self.n_trading_unhealthy,
            "health_stale_threshold_ms": self.health_stale_threshold_ms,
            "reconnect_seconds": list(self.reconnect_seconds),
            "no_hft_pnl": True,
            "health_uses_carried_forward_alone": False,
            "seq_id_skips_are_not_missing_packets": True,
            "not_a_forecast": True,
            "place_orders": False,
        }


def summarize_trading_health(
    samples: Sequence[Mapping[str, Any] | Vamp1sSample],
    reconnect_seconds: Optional[Iterable[int]] = None,
) -> TradingHealthStats:
    recon = {int(s) for s in reconnect_seconds} if reconnect_seconds else set()
    out = TradingHealthStats(
        n_samples=len(samples),
        reconnect_seconds=sorted(recon),
        n_reconnect=len(recon),
    )
    for s in samples:
        if _is_carried(s):
            out.n_carried_forward += 1
        if _attr(s, "health_stale"):
            out.n_health_stale += 1
        if _attr(s, "ts_rewind"):
            out.n_ts_rewind += 1
        if sample_trading_unhealthy(s, reconnect_seconds=recon):
            out.n_trading_unhealthy += 1
    return out
