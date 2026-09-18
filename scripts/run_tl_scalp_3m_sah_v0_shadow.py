#!/usr/bin/env python3
"""TL-SCALP-3M-SAH-v0 SHADOW walk — CTRL / SAH-A / SAH-B on post-R7 majors.

Paper only. Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft ≠ arm. Scalp PAUSED.
"""

from __future__ import annotations

import argparse
import hashlib
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
from atlas.paper.tl_scalp_3m_sah_v0_shadow import (  # noqa: E402
    TRIAL_ID,
    WINDOW_ID,
    measured_table_rows,
    render_board_markdown,
    run_shadow_score,
    window_lock_card,
    write_report_json,
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="TL-SCALP-3M-SAH-v0 SHADOW post-R7 walk")
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--results-dir", default=None)
    p.add_argument(
        "--out",
        default="results/tl_scalp_3m_sah_v0_shadow.json",
    )
    p.add_argument(
        "--write-md",
        default="phase1/154-tl-scalp-3m-sah-v0-shadow-board.md",
    )
    p.add_argument(
        "--write-registry",
        default="phase1/registry/154-tl-scalp-3m-sah-v0-shadow.json",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    results_dir = Path(args.results_dir) if args.results_dir else _ROOT / "results"
    if not results_dir.is_absolute():
        results_dir = _ROOT / results_dir
    setup_logging(cfg.log_level)

    # Lock card into stdout BEFORE scoring
    lock = window_lock_card()
    print(json.dumps({"phase": "window_lock_pre_score", "lock": lock}, indent=2))

    default_yaml = _ROOT / "config" / "default.yaml"
    sha = _sha256(default_yaml)

    try:
        bundle = run_shadow_score(cfg, data_dir=data_dir)
    except ReplayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2

    bundle["default_yaml_sha256"] = sha
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = _ROOT / out_path
    write_report_json(bundle, out_path)

    reg_path = Path(args.write_registry)
    if not reg_path.is_absolute():
        reg_path = _ROOT / reg_path
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    slim = {
        "trial_id": TRIAL_ID,
        "window_id": WINDOW_ID,
        "verdicts": bundle.get("verdicts"),
        "sah_ranking": bundle.get("sah_ranking"),
        "table": measured_table_rows(bundle),
        "md_confirm": bundle.get("md_confirm"),
        "window_lock": bundle.get("window_lock"),
        "default_yaml_sha256": sha,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_ne_arm": True,
        "dual_hard_pass": "N/A_single_predeclared_window",
    }
    write_report_json(slim, reg_path)

    md_path = Path(args.write_md)
    if not md_path.is_absolute():
        md_path = _ROOT / md_path
    md_path.write_text(
        render_board_markdown(bundle, default_yaml_sha256=sha), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "ok": bundle.get("ok"),
                "wrote": [str(out_path), str(reg_path), str(md_path)],
                "verdicts": bundle.get("verdicts"),
                "sah_ranking": bundle.get("sah_ranking"),
                "table": measured_table_rows(bundle),
                "default_yaml_sha256": sha,
                "place_orders": False,
                "not_a_forecast": True,
                "soft_ne_arm": True,
            },
            indent=2,
        )
    )
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
