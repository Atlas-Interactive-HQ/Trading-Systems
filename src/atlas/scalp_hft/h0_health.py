"""H0 health-only replay after staleness-semantics patch. NO HFT PnL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from atlas.scalp_hft.health import summarize_trading_health
from atlas.scalp_hft.vamp import (
    Books5IngestStats,
    replay_books5_jsonl_to_1s,
    summarize_samples,
)


def discover_books5(raw_root: Path, date: str | None = None) -> list[Path]:
    base = raw_root / "okx_eea"
    if date:
        p = base / date / "ws_books5.jsonl"
        return [p] if p.is_file() else []
    if not base.is_dir():
        return []
    out: list[Path] = []
    for day in sorted(base.iterdir()):
        cand = day / "ws_books5.jsonl"
        if cand.is_file():
            out.append(cand)
    return out


def reconnect_seconds_from_ws_error(paths: Iterable[Path]) -> set[int]:
    """Seconds that contain a ws_reconnect / ws_error_event sidecar line."""
    secs: set[int] = set()
    for path in paths:
        err = path.parent / "ws_error.jsonl"
        if not err.is_file():
            continue
        with err.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    env = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(env, dict):
                    continue
                reason = str(env.get("gap_reason") or "")
                if reason not in {"ws_reconnect", "ws_error_event"}:
                    continue
                ts = env.get("exchange_ts") or env.get("receive_ts")
                try:
                    ts_i = int(ts)
                except (TypeError, ValueError):
                    continue
                secs.add(ts_i // 1000)
    return secs


def run_h0_health_only(
    *,
    raw_root: Path,
    date: str | None = None,
) -> dict[str, Any]:
    """Replay books5 → 1s and report health vs carry. Fail-closed if no capture."""
    paths = discover_books5(raw_root, date)
    if not paths:
        return {
            "ok": False,
            "fail_closed": True,
            "insufficient_data": True,
            "error": (
                "no ws_books5.jsonl under data/raw/okx_eea/ — cannot re-run H0. "
                "Do not invent health counts. Historical 79/85 numbers stay as-is."
            ),
            "no_hft_pnl": True,
            "not_a_forecast": True,
            "place_orders": False,
        }
    ingest = Books5IngestStats()
    samples = replay_books5_jsonl_to_1s(paths, ingest_stats=ingest)
    recon = reconnect_seconds_from_ws_error(paths)
    gap = summarize_samples(samples)
    health = summarize_trading_health(samples, reconnect_seconds=recon)
    return {
        "ok": True,
        "insufficient_data": False,
        "inputs": [str(p) for p in paths],
        "ingest": ingest.to_dict(),
        "gap": gap.to_dict(),
        "health": health.to_dict(),
        "n_samples_1s": gap.n_samples_1s,
        "n_carried_forward": health.n_carried_forward,
        "n_health_stale": health.n_health_stale,
        "n_trading_unhealthy": health.n_trading_unhealthy,
        "n_ts_rewind": health.n_ts_rewind,
        "n_reconnect": health.n_reconnect,
        "historical_79_85_not_rewritten": True,
        "no_hft_pnl": True,
        "not_a_forecast": True,
        "place_orders": False,
        "disclaimer": (
            "Health-only. book_stale/carried_forward is feature continuity. "
            "Trading health uses health_stale + reconnect + ts continuity. "
            "seqId skips are not missing packets. No HFT PnL."
        ),
    }
