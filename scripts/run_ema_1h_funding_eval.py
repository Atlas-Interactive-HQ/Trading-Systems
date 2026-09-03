#!/usr/bin/env python3
"""1H EMA long/flat eval with public perpetual funding. Research only. No orders."""

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
from atlas.paper.ema_1h_eval import (  # noqa: E402
    EMA_1H_SYMBOL,
    render_ema_1h_markdown,
    run_ema_1h_eval,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "EMA long/flat 1H eval (BTC-USDT-SWAP) + public funding. "
            "Research only. Never places orders. Daily observer unchanged."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--asset", default=EMA_1H_SYMBOL, help="Perp/swap instId (default BTC-USDT-SWAP)")
    p.add_argument(
        "--windows",
        default="2020-09,2023-09,2022-bear,2023-chop",
        help="Named windows (q4 optional if you accept more 1H pagination)",
    )
    p.add_argument("--samples", default=None, help="Alias for --windows")
    p.add_argument("--fast", type=int, default=12)
    p.add_argument("--slow", type=int, default=30)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--write-md",
        default=None,
        help="Markdown path. Default phase1/22-ema-1h-funding.md. Empty to skip.",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    try:
        bundle = run_ema_1h_eval(
            cfg,
            asset=args.asset,
            windows=args.samples or args.windows,
            data_dir=data_dir,
            pause_s=args.pause_s,
            fast=args.fast,
            slow=args.slow,
        )
    except ReplayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2

    public = {
        "ok": bundle.get("ok"),
        "place_orders": False,
        "not_a_forecast": True,
        "asset": bundle.get("asset"),
        "bar": bundle.get("bar"),
        "strategy": bundle.get("strategy"),
        "funding": {
            k: (bundle.get("funding") or {}).get(k)
            for k in (
                "source",
                "path",
                "n_prints",
                "oldest_funding_ms",
                "newest_funding_ms",
                "venue_lookback_note",
            )
        },
        "bull_holdout": bundle.get("bull_holdout"),
        "oos_stress": bundle.get("oos_stress"),
        "errors": bundle.get("errors"),
        "disclaimer": bundle.get("disclaimer"),
        "samples": [
            {
                "sample_id": s.get("sample_id"),
                "ok": s.get("ok"),
                "error": s.get("error"),
                "full": {
                    k: ((s.get("full") or {}) or {}).get(k)
                    for k in (
                        "n_trades",
                        "net_return_eur",
                        "net_return_fee_only_eur",
                        "net_return_with_observed_funding_eur",
                        "funding_drag_eur",
                        "funding_incomplete",
                        "decision_costs",
                        "max_dd_eur",
                        "time_in_market",
                    )
                }
                if s.get("ok")
                else None,
                "holdout": {
                    k: ((s.get("holdout") or {}) or {}).get(k)
                    for k in (
                        "n_trades",
                        "net_return_eur",
                        "net_return_fee_only_eur",
                        "net_return_with_observed_funding_eur",
                        "funding_incomplete",
                        "max_dd_eur",
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
    if write_md is None:
        write_md = str(_ROOT / "phase1" / "22-ema-1h-funding.md")
    if write_md:
        md_path = Path(write_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_ema_1h_markdown(bundle), encoding="utf-8")
        print(f"wrote {md_path}", file=sys.stderr)
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
