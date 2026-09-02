#!/usr/bin/env python3
"""CLI: run Kraken Futures PUBLIC collector (smoke / continuous)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running without install: add src to path
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from atlas.common.config import load_config, refuse_if_secrets_present  # noqa: E402
from atlas.common.logging import setup_logging  # noqa: E402
from atlas.collectors.kraken_futures_public import KrakenFuturesPublicCollector  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Kraken Futures PUBLIC MD collector (no API keys)")
    p.add_argument("--config", default=None, help="Path to config YAML")
    p.add_argument("--duration-sec", type=float, default=60.0, help="Run duration (default 60)")
    p.add_argument("--ws", action="store_true", help="Also run short public WS stub")
    p.add_argument("--data-dir", default=None, help="Override data directory")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    if args.data_dir:
        cfg.data_dir = args.data_dir
    setup_logging(cfg.log_level)
    refuse_if_secrets_present(cfg)

    collector = KrakenFuturesPublicCollector(cfg)
    summary = collector.run(duration_sec=args.duration_sec, enable_ws=args.ws)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
