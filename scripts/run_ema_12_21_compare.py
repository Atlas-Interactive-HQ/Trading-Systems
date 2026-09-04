#!/usr/bin/env python3
"""Compare EMA 12/21 vs locked 12/30 on BTC-USDT 1D. Research only. No orders."""

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
from atlas.paper.ema_12_21 import render_ema_12_21_markdown, run_ema_12_21_compare  # noqa: E402
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "EMA 12/21 vs 12/30 daily compare (BTC-USDT). Research only. "
            "Does not change the 12/30 observer default."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--asset", default="BTC-USDT")
    p.add_argument(
        "--windows",
        default="2020-09,2023-09,2022-bear,2023-chop",
    )
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--write-md",
        default=None,
        help="Markdown path. Default phase1/26-ema-12-21.md. Empty to skip.",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    try:
        bundle = run_ema_12_21_compare(
            cfg,
            asset=args.asset,
            windows=args.windows,
            data_dir=data_dir,
            pause_s=args.pause_s,
        )
    except ReplayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2

    public = {
        "ok": bundle.get("ok"),
        "place_orders": False,
        "not_a_forecast": True,
        "asset": bundle.get("asset"),
        "base": bundle.get("base"),
        "alt": bundle.get("alt"),
        "interesting_12_30": bundle.get("interesting_12_30"),
        "interesting_12_21": bundle.get("interesting_12_21"),
        "oos_12_30": bundle.get("oos_12_30"),
        "oos_12_21": bundle.get("oos_12_21"),
        "windows": bundle.get("windows"),
        "errors": bundle.get("errors"),
        "disclaimer": bundle.get("disclaimer"),
    }
    print(json.dumps(public, indent=2, default=str))
    write_md = args.write_md
    if write_md is None:
        write_md = str(_ROOT / "phase1" / "26-ema-12-21.md")
    if write_md:
        md_path = Path(write_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_ema_12_21_markdown(bundle), encoding="utf-8")
        print(f"wrote {md_path}", file=sys.stderr)
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
