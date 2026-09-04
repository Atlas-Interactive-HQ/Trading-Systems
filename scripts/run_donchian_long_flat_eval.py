#!/usr/bin/env python3
"""Daily Donchian long/flat eval (BTC-USDT). Research only. Never places orders."""

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
from atlas.paper.donchian_eval import (  # noqa: E402
    DONCHIAN_ASSET,
    render_donchian_markdown,
    run_donchian_eval,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Donchian long/flat daily eval (BTC-USDT). Research only. Never places orders. "
            "Parallel to EMA 12/30. Does not replace Phase A."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--asset", default=DONCHIAN_ASSET)
    p.add_argument(
        "--windows",
        default="2020-09,2023-09,2022-bear,2023-chop",
        help="Named windows",
    )
    p.add_argument("--samples", default=None, help="Alias for --windows")
    p.add_argument("--entry-lookback", type=int, default=20)
    p.add_argument("--exit-lookback", type=int, default=10)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--write-md",
        default=None,
        help="Markdown path. Default phase1/24-donchian-btc.md. Empty to skip.",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    try:
        bundle = run_donchian_eval(
            cfg,
            asset=args.asset,
            windows=args.samples or args.windows,
            data_dir=data_dir,
            pause_s=args.pause_s,
            entry_lookback=args.entry_lookback,
            exit_lookback=args.exit_lookback,
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
                "full": {
                    k: ((s.get("full") or {}) or {}).get(k)
                    for k in (
                        "n_trades",
                        "net_return_eur",
                        "expectancy_after_costs_eur",
                        "max_dd_eur",
                        "time_in_market",
                        "fee_drag_eur",
                    )
                }
                if s.get("ok")
                else None,
                "holdout": {
                    k: ((s.get("holdout") or {}) or {}).get(k)
                    for k in (
                        "n_trades",
                        "net_return_eur",
                        "expectancy_after_costs_eur",
                        "max_dd_eur",
                        "time_in_market",
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
        write_md = str(_ROOT / "phase1" / "24-donchian-btc.md")
    if write_md:
        md_path = Path(write_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_donchian_markdown(bundle), encoding="utf-8")
        print(f"wrote {md_path}", file=sys.stderr)
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
