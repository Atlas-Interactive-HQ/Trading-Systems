#!/usr/bin/env python3
"""Daily EMA long/flat eval. Research only. Never places orders. not_a_forecast."""

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
from atlas.paper.ema_eval import (  # noqa: E402
    OOS_BEAR,
    OOS_CHOP,
    render_ema_markdown,
    render_oos_markdown,
    run_ema_eval,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="EMA long/flat daily eval (BTC-USDT primary). Research only. Never places orders."
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--asset", default="BTC-USDT", help="Research MD instId (BTC-USDT or DOGE-USDT)")
    p.add_argument("--windows", default="2020-09,2023-09", help="Named windows or q4")
    p.add_argument("--samples", default=None, help="Alias for --windows")
    p.add_argument("--fast", type=int, default=12)
    p.add_argument("--slow", type=int, default=30)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--write-md",
        default=None,
        help="Markdown path. Default 19 for bull windows, 20 if OOS stress windows are present. Empty to skip.",
    )
    p.add_argument("--no-neighbors", action="store_true")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    try:
        bundle = run_ema_eval(
            cfg,
            asset=args.asset,
            windows=args.samples or args.windows,
            data_dir=data_dir,
            pause_s=args.pause_s,
            fast=args.fast,
            slow=args.slow,
            neighbors=not args.no_neighbors,
        )
    except ReplayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2

    public = {
        "ok": bundle.get("ok"),
        "place_orders": False,
        "not_a_forecast": True,
        "asset": bundle.get("asset"),
        "strategy": bundle.get("strategy"),
        "interesting": bundle.get("interesting"),
        "oos_stress": bundle.get("oos_stress"),
        "errors": bundle.get("errors"),
        "disclaimer": bundle.get("disclaimer"),
        "samples": [
            {
                "sample_id": s.get("sample_id"),
                "ok": s.get("ok"),
                "error": s.get("error"),
                "holdout": {
                    k: ((s.get("holdout") or {}) or {}).get(k)
                    for k in (
                        "n_trades",
                        "net_return_eur",
                        "net_return_pct",
                        "max_dd_eur",
                        "expectancy_after_costs_eur",
                        "time_in_market",
                        "fee_drag_eur",
                    )
                }
                if s.get("ok")
                else None,
            }
            for s in (bundle.get("samples") or [])
        ],
    }
    print(json.dumps(public, indent=2, default=str))
    write_md = args.write_md
    ids = {s.get("sample_id") for s in (bundle.get("samples") or [])}
    oos_run = OOS_BEAR in ids or OOS_CHOP in ids
    if write_md is None:
        write_md = str(
            _ROOT / "phase1" / ("20-ema-oos-stress.md" if oos_run else "19-ema-long-flat.md")
        )
    if write_md:
        md_path = Path(write_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        render = render_oos_markdown if oos_run else render_ema_markdown
        md_path.write_text(render(bundle), encoding="utf-8")
        print(f"wrote {md_path}", file=sys.stderr)
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
