#!/usr/bin/env python3
"""Read-only EMA 12/30 vs 12/21 week digest from local journals. No orders. No network."""

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
from atlas.paper.ema_digest import render_ema_week_digest, run_ema_week_digest  # noqa: E402
from atlas.oms.spot_demo import redact_record  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Compare locked 12/30 (data/ema/) vs parallel 12/21 (data/ema21/) journals. "
            "Read-only. Fail closed if a required dir is missing. No orders."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--ema-subdir", default="ema", help="Locked 12/30 journals (default ema)")
    p.add_argument("--ema21-subdir", default="ema21", help="Parallel 12/21 journals (default ema21)")
    p.add_argument("--json", action="store_true", help="Print JSON instead of the compact table")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir

    bundle = run_ema_week_digest(
        data_dir, ema_subdir=args.ema_subdir, ema21_subdir=args.ema21_subdir
    )
    if args.json:
        print(json.dumps(redact_record(bundle), indent=2, default=str))
    else:
        print(render_ema_week_digest(bundle), end="")
    return 0 if bundle.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
