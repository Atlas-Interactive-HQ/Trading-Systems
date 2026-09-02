#!/usr/bin/env python3
"""Replay locked DOGE breakout on public historical candles. Signal-only.

No demo/live orders. No API keys. Success = pipeline + journals + tests,
not PnL. Replay is not a live Phase A week.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from atlas.common.config import load_config  # noqa: E402
from atlas.common.logging import setup_logging  # noqa: E402
from atlas.paper.replay import ReplayError, run_replay  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Historical Phase A replay (signal-only). Public OKX EEA candles. "
            "Never places orders."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--venue", choices=("spot", "xperp", "both"), default="both")
    p.add_argument("--lookback-days", type=int, default=90)
    p.add_argument("--window-days", type=int, default=7)
    p.add_argument(
        "--pause-s",
        type=float,
        default=0.12,
        help="Delay between history-candles pages (OKX 20 req / 2s)",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    try:
        summary = run_replay(
            cfg,
            venue=args.venue,
            lookback_days=args.lookback_days,
            window_days=args.window_days,
            data_dir=data_dir,
            pause_s=args.pause_s,
        )
    except ReplayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2

    print(json.dumps(summary, indent=2, default=str))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
