#!/usr/bin/env python3
"""EMA long/flat paper observer. Public BTC-USDT 1D. Never places orders.

Default: journal current long|flat state. Optional --paper-shadow updates a 1×
hypothetical next-open ledger under data/ema/. Distinct from Phase A DOGE
(data/oms/) and Phase B shadow (data/shadow/). not_a_forecast. Not live.
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
from atlas.paper.ema_observer import EMA_OBSERVER_SYMBOL, run_ema_paper_session  # noqa: E402
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "EMA paper observer (BTC-USDT 1D). Signal/state journal by default. "
            "Never places exchange orders. Does not replace Phase A DOGE."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--asset", default=EMA_OBSERVER_SYMBOL, help="Research MD instId (BTC-USDT)")
    p.add_argument("--lookback-days", type=int, default=90, help="Closed 1D bars to fetch (incl. EMA30 warmup)")
    p.add_argument("--fast", type=int, default=12, help="Fast EMA period (default 12)")
    p.add_argument("--slow", type=int, default=30, help="Slow EMA period (default 30; weekday routine)")
    p.add_argument(
        "--journal-subdir",
        default="ema",
        help="Under data-dir (default ema). Use ema21 for 12/21 without touching the 12/30 path.",
    )
    p.add_argument(
        "--paper-shadow",
        action="store_true",
        help="Update 1× hypothetical next-open ledger under data/ema/. No exchange orders.",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    try:
        public = run_ema_paper_session(
            cfg,
            data_dir=data_dir,
            symbol=args.asset,
            paper_shadow=bool(args.paper_shadow),
            lookback_days=args.lookback_days,
            fast=args.fast,
            slow=args.slow,
            journal_subdir=args.journal_subdir,
        )
    except ReplayError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "place_orders": False,
                    "not_a_forecast": True,
                    "source": "ema-paper-observer",
                },
                indent=2,
            )
        )
        return 2

    print(json.dumps(public, indent=2, default=str))
    return 0 if public.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
