#!/usr/bin/env python3
"""EMA 12/30 asymmetric persist-2 entry (BTC-USDT 1D). Research only. No orders."""

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
from atlas.paper.ema_persist2_eval import (  # noqa: E402
    PERSIST2_ASSET,
    render_ema_persist2_markdown,
    run_ema_persist2_eval,
)
from atlas.paper.replay import ReplayError  # noqa: E402
from atlas.strategy.ema_persist2 import ENTRY_PERSIST  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "EMA 12/30 asymmetric persist-2 entry (BTC-USDT 1D). Research only. "
            "Never places orders. Does not replace Phase A or the EMA observer."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--asset", default=PERSIST2_ASSET)
    p.add_argument(
        "--windows",
        default="2020-09,2023-09,2022-bear,2023-chop",
        help="Named windows",
    )
    p.add_argument("--fast", type=int, default=12)
    p.add_argument("--slow", type=int, default=30)
    p.add_argument("--entry-persist", type=int, default=ENTRY_PERSIST)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--write-md",
        default=None,
        help="Markdown path. Default phase1/31-ema-persist2-entry.md. Empty to skip.",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    try:
        bundle = run_ema_persist2_eval(
            cfg,
            asset=args.asset,
            windows=args.windows,
            data_dir=data_dir,
            pause_s=args.pause_s,
            fast=args.fast,
            slow=args.slow,
            entry_persist=args.entry_persist,
        )
    except ReplayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2

    gate = bundle.get("pass_gate") or {}
    public = {
        "ok": bundle.get("ok"),
        "place_orders": False,
        "not_a_forecast": True,
        "asset": bundle.get("asset"),
        "strategy": bundle.get("strategy"),
        "pass_gate": {
            "verdict": gate.get("verdict"),
            "passed": gate.get("passed"),
            "checks": [
                {"id": c.get("id"), "ok": c.get("ok")} for c in (gate.get("checks") or [])
            ],
        },
        "errors": bundle.get("errors"),
        "disclaimer": bundle.get("disclaimer"),
    }
    print(json.dumps(public, indent=2, default=str))
    write_md = args.write_md
    if write_md is None:
        write_md = str(_ROOT / "phase1" / "31-ema-persist2-entry.md")
    if write_md:
        md_path = Path(write_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_ema_persist2_markdown(bundle), encoding="utf-8")
        print(f"wrote {md_path}", file=sys.stderr)
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
