#!/usr/bin/env python3
"""Phase B shadow on a similar-regime window. Signal-only would-place. No orders.

Uses the last data/replay summary if present; otherwise runs historical match
first. Success = gated decisions, not PnL. Shadow ≠ Phase C auto-demo.
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
from atlas.paper.replay import ReplayError  # noqa: E402
from atlas.paper.shadow import run_shadow  # noqa: E402


def _public_summary(summary: dict) -> dict:
    """Headline counts only. Research equity sits under research.not_a_forecast."""
    keys = (
        "ok",
        "place_orders",
        "mode",
        "source",
        "run_id",
        "venue",
        "paper_equity_eur",
        "n_signals",
        "n_would_place",
        "n_blocked",
        "n_blocked_by_reason",
        "n_open",
        "n_flatten",
        "n_kills",
        "windows",
        "errors",
        "disclaimer",
        "log_dir",
        "research",
    )
    out = {k: summary.get(k) for k in keys if k in summary}
    out["place_orders"] = False
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Phase B shadow replay. Would-place vs blocked. Never places orders."
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--venue", choices=("spot", "xperp", "both"), default="both")
    p.add_argument("--lookback-days", type=int, default=90)
    p.add_argument("--window-days", type=int, default=7)
    p.add_argument("--pause-s", type=float, default=0.12)
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    try:
        summary = run_shadow(
            cfg,
            venue=args.venue,
            data_dir=data_dir,
            lookback_days=args.lookback_days,
            window_days=args.window_days,
            pause_s=args.pause_s,
        )
    except ReplayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2

    print(json.dumps(_public_summary(summary), indent=2, default=str))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
