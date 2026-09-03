#!/usr/bin/env python3
"""Phase D-lite paper eval. Expectancy after costs. not_a_forecast.

No orders. Do not headline PnL. Do not retune BreakoutV1.
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
from atlas.paper.eval import render_eval_markdown, run_paper_eval  # noqa: E402
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Costed paper eval (70/30 + stress). Research only. Never places orders."
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument(
        "--samples",
        default="similar,2020-09,2023-09",
        help="Comma list: similar,2020-09,2023-09,q4 (q4 = Oct/Nov/Dec 2020/2023/2024)",
    )
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--write-md",
        default=str(_ROOT / "phase1" / "13-paper-eval.md"),
        help="Markdown tables path (committed). Empty to skip.",
    )
    p.add_argument(
        "--md-heading",
        default=None,
        help="Markdown H1 (default: 13 — Paper eval). Use 14 heading for Q4 months.",
    )
    p.add_argument(
        "--md-intro",
        default=None,
        help="Optional extra intro paragraph for the markdown tables.",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)
    samples = [s.strip() for s in str(args.samples).split(",") if s.strip()]

    try:
        bundle = run_paper_eval(
            cfg, samples=samples, data_dir=data_dir, pause_s=args.pause_s
        )
    except ReplayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2

    public = {
        "ok": bundle.get("ok"),
        "place_orders": False,
        "not_a_forecast": True,
        "source": bundle.get("source"),
        "errors": bundle.get("errors"),
        "disclaimer": bundle.get("disclaimer"),
        "samples": [],
    }
    for s in bundle.get("samples") or []:
        if not s.get("ok"):
            public["samples"].append(
                {"sample_id": s.get("sample_id"), "ok": False, "error": s.get("error")}
            )
            continue
        public["samples"].append(
            {
                "sample_id": s.get("sample_id"),
                "md_label": s.get("md_label"),
                "split": s.get("split"),
                "full": {
                    k: (s.get("full") or {}).get(k)
                    for k in (
                        "n_trades",
                        "n_would_place",
                        "n_kill_days",
                        "expectancy_after_costs_eur",
                        "max_dd_eur",
                        "fee_drag_eur",
                        "turnover_vs_book",
                        "win_rate",
                    )
                },
                "holdout": {
                    k: (s.get("holdout") or {}).get(k)
                    for k in (
                        "n_trades",
                        "n_would_place",
                        "n_kill_days",
                        "expectancy_after_costs_eur",
                        "max_dd_eur",
                        "fee_drag_eur",
                    )
                },
                "not_a_forecast": True,
            }
        )
    print(json.dumps(public, indent=2, default=str))

    if args.write_md:
        md_path = Path(args.write_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        heading = args.md_heading or "13 — Paper eval (Phase D-lite)"
        md_path.write_text(
            render_eval_markdown(
                bundle, heading=heading, extra_intro=args.md_intro
            ),
            encoding="utf-8",
        )
        print(f"wrote {md_path}", file=sys.stderr)
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
