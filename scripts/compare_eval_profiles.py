#!/usr/bin/env python3
"""Compare a candidate eval profile against the frozen baseline. Research only.

Reads the per-profile JSON that scripts/run_paper_eval.py already wrote under
data/reports/profiles/<profile>/ — nothing is re-simulated and nothing is fetched.
Applies the up-front pass rule (atlas.paper.compare) and writes the comparison JSON
(+ optional markdown doc). Never places orders. not_a_forecast.
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
from atlas.oms.spot_demo import redact_record  # noqa: E402
from atlas.paper.engine import strategy_from_app_config  # noqa: E402
from atlas.paper.compare import (  # noqa: E402
    compare_profiles,
    extract_heading,
    extract_run_note,
    render_candidate_markdown,
)
from atlas.paper.eval import load_profile_reports  # noqa: E402
from atlas.paper.profiles import BASELINE, ProfileError, get_profile, profile_names  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Baseline vs candidate profile comparison (pass rule in code). Research only."
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--baseline", default=BASELINE, choices=profile_names())
    p.add_argument("--candidate", required=True, choices=profile_names())
    p.add_argument(
        "--write-json",
        default=None,
        help="Comparison JSON path (gitignored). Default data/reports/compare_<cand>_vs_<base>.json",
    )
    p.add_argument("--write-md", default="", help="Full markdown doc path (committed). Empty to skip.")
    p.add_argument(
        "--md-heading",
        default=None,
        help="Markdown H1 for --write-md. Default: reuse the H1 of the existing file, else a generic one.",
    )
    p.add_argument(
        "--md-note",
        default=None,
        help="Run-note section (markdown). Default: carry over the note between the run-note markers "
        "of the existing file, so a plain re-run reproduces the committed doc.",
    )
    args = p.parse_args(argv)

    try:
        base = get_profile(args.baseline)
        cand = get_profile(args.candidate)
    except ProfileError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2
    if cand.name == base.name:
        print(json.dumps({"ok": False, "error": "candidate equals baseline", "place_orders": False}))
        return 2

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    reports_dir = data_dir / "reports"
    profiles = load_profile_reports(reports_dir)
    missing = [n for n in (base.name, cand.name) if n not in profiles]
    if missing:
        print(
            json.dumps(
                {
                    "ok": False,
                    "place_orders": False,
                    "error": f"no eval reports for profile(s) {missing}; run scripts/run_paper_eval.py --profile <name> first",
                    "reports_dir": str(reports_dir),
                },
                indent=2,
            )
        )
        return 2

    # Overlay stamped in the doc/JSON is the RESOLVED one (concrete values vs this config's baseline).
    base_strategy = strategy_from_app_config(cfg)
    cmp = compare_profiles(
        profiles[base.name],
        profiles[cand.name],
        base_name=base.name,
        cand_name=cand.name,
        base_overlay=base.resolved_overlay(base_strategy),
        cand_overlay=cand.resolved_overlay(base_strategy),
        cand_description=cand.description,
        cand_notes=cand.notes,
        cand_baseline_note=cand.baseline_note,
    )
    out_json = Path(args.write_json) if args.write_json else reports_dir / f"compare_{cand.name}_vs_{base.name}.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(redact_record(cmp), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )

    rule = cmp["pass_rule"]
    public = {
        "ok": True,
        "place_orders": False,
        "not_a_forecast": True,
        "baseline": base.name,
        "candidate": cand.name,
        "candidate_overlay": cand.resolved_overlay(base_strategy),
        "verdict": rule["verdict"],
        "per_window": rule["per_window"],
        "samples_compared": [r["sample_id"] for r in cmp["samples"] if r.get("ok")],
        "samples_not_comparable": [r["sample_id"] for r in cmp["samples"] if not r.get("ok")],
        "wrote_json": str(out_json),
        "disclaimer": cmp["disclaimer"],
    }
    print(json.dumps(public, indent=2, default=str))

    if args.write_md:
        md_path = Path(args.write_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        existing = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
        heading = args.md_heading or extract_heading(existing) or f"Candidate {cand.name} vs frozen baseline (Phase D trial)"
        run_note = args.md_note if args.md_note is not None else extract_run_note(existing)
        reproduce = [
            "source .venv/bin/activate",
            f"python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile {base.name} --write-md ''",
            f"python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile {cand.name}",
            f"python scripts/run_paper_eval.py --samples q4 --profile {base.name} --write-md ''   # secondary",
            f"python scripts/run_paper_eval.py --samples q4 --profile {cand.name}                 # secondary",
            f"python scripts/compare_eval_profiles.py --candidate {cand.name} --write-md {md_path.relative_to(_ROOT) if md_path.is_absolute() and str(md_path).startswith(str(_ROOT)) else md_path}",
        ]
        md_path.write_text(
            render_candidate_markdown(
                cmp, heading=heading, reproduce=reproduce, run_note=run_note
            ),
            encoding="utf-8",
        )
        print(f"wrote {md_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
