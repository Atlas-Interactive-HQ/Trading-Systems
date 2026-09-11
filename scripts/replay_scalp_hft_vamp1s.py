#!/usr/bin/env python3
"""Replay Layer B OKX books5 JSONL → 1s VAMP-5 feature samples (PAPER_ONLY).

Default output: results/scalp_hft_v1/layer_b_samples/vamp1s_<inst>_<date>.{csv,parquet}
(Optional --derived also writes data/derived/okx_eea/{date}/ per phase1/78 §6.)
No trading, no PnL, no live OMS. Does not touch config/default.yaml.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from atlas.scalp_hft.vamp import (  # noqa: E402
    PAPER_ONLY,
    SAMPLE_COLUMNS,
    Books5IngestStats,
    replay_books5_jsonl_to_1s,
    summarize_samples,
    write_samples,
)

DEFAULT_INST = "DOGE-USD_UM_XPERP-310404"
DEMO_ORDER_INST = "DOGE-USD_UM_XPERP-310516"
RESULTS_OUT = ROOT / "results" / "scalp_hft_v1" / "layer_b_samples"
DERIVED_ROOT = ROOT / "data" / "derived" / "okx_eea"


def _discover_books5(raw_root: Path, date: str | None) -> list[Path]:
    base = raw_root / "okx_eea"
    if date:
        p = base / date / "ws_books5.jsonl"
        return [p] if p.is_file() else []
    paths: list[Path] = []
    if not base.is_dir():
        return paths
    for day in sorted(base.iterdir()):
        cand = day / "ws_books5.jsonl"
        if cand.is_file():
            paths.append(cand)
    return paths


def _default_out_dir(date_tag: str | None) -> Path:
    _ = date_tag
    return RESULTS_OUT


def main(argv: list[str] | None = None) -> int:
    assert PAPER_ONLY is True
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--input",
        "-i",
        action="append",
        dest="inputs",
        help="books5 jsonl path (repeatable). Default: discover under data/raw/okx_eea/",
    )
    ap.add_argument(
        "--raw-root",
        type=Path,
        default=ROOT / "data" / "raw",
        help="raw data root (default: data/raw)",
    )
    ap.add_argument(
        "--date",
        default=None,
        help="UTC date folder YYYY-MM-DD under okx_eea (optional filter)",
    )
    ap.add_argument(
        "--inst-id",
        default=DEFAULT_INST,
        help=f"filter / label instrument (default {DEFAULT_INST})",
    )
    ap.add_argument(
        "--allow-proxy-swap",
        action="store_true",
        help="allow classic SWAP / non-primary instId (labels PROXY; not Layer B primary)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="output directory (default: results/scalp_hft_v1/layer_b_samples)",
    )
    ap.add_argument(
        "--also-derived",
        action="store_true",
        help="also write under data/derived/okx_eea/{date}/ (phase1/78 path)",
    )
    ap.add_argument(
        "--stem",
        default=None,
        help="output filename stem (default vamp1s_<inst>_<date>)",
    )
    ap.add_argument(
        "--no-fill-gaps",
        action="store_true",
        help="do not emit carried-forward seconds without a book update",
    )
    ap.add_argument(
        "--max-seconds",
        type=int,
        default=None,
        help="optional cap on emitted 1s samples (smoke/short replay)",
    )
    ap.add_argument(
        "--formats",
        default="csv,parquet",
        help="comma list: csv,parquet (parquet skipped if pyarrow missing)",
    )
    args = ap.parse_args(argv)

    if args.inst_id == DEMO_ORDER_INST and not args.allow_proxy_swap:
        print(
            json.dumps(
                {
                    "ok": False,
                    "paper_only": True,
                    "error": "demo_order_inst_refused",
                    "inst_id": args.inst_id,
                    "hint": "Layer B MD uses DOGE-USD_UM_XPERP-310404; pass --allow-proxy-swap only for explicit proxy",
                },
                indent=2,
            )
        )
        return 2
    if (
        args.inst_id != DEFAULT_INST
        and "SWAP" in args.inst_id.upper()
        and not args.allow_proxy_swap
    ):
        print(
            json.dumps(
                {
                    "ok": False,
                    "paper_only": True,
                    "error": "classic_swap_refused",
                    "inst_id": args.inst_id,
                    "hint": "pass --allow-proxy-swap for classic SWAP (SYNTHETIC / PROXY)",
                },
                indent=2,
            )
        )
        return 2

    inputs = [Path(p) for p in (args.inputs or [])]
    if not inputs:
        inputs = _discover_books5(args.raw_root, args.date)
    missing = [p for p in inputs if not p.is_file()]
    if missing or not inputs:
        msg = {
            "ok": False,
            "paper_only": True,
            "error": "no_books5_jsonl",
            "hint": (
                "Capture first: python scripts/run_okx_public.py --capture "
                "--ws-only --duration-sec 30"
            ),
            "looked_for": [str(p) for p in inputs] or [str(args.raw_root / "okx_eea")],
            "missing": [str(p) for p in missing],
        }
        print(json.dumps(msg, indent=2))
        return 2

    ingest = Books5IngestStats()
    samples = replay_books5_jsonl_to_1s(
        inputs,
        ingest_stats=ingest,
        fill_missing_seconds=not args.no_fill_gaps,
    )
    if args.inst_id:
        samples = [s for s in samples if (not s.inst_id) or s.inst_id == args.inst_id]
    if args.max_seconds is not None:
        samples = samples[: max(0, args.max_seconds)]

    date_tag = args.date
    if date_tag is None and inputs:
        parent = inputs[0].parent.name
        date_tag = parent if len(parent) == 10 and parent[4] == "-" else "smoke"
    out_dir = args.out_dir or _default_out_dir(date_tag)
    stem = args.stem or f"vamp1s_{args.inst_id}_{date_tag or 'replay'}"
    formats = [f.strip() for f in args.formats.split(",") if f.strip()]

    written = write_samples(samples, out_dir, stem=stem, formats=formats)
    written_all = {"primary": {k: str(v) for k, v in written.items()}}
    if args.also_derived:
        derived_dir = DERIVED_ROOT / (date_tag or "unknown")
        derived_stem = f"vamp1s_{args.inst_id}"
        written_d = write_samples(samples, derived_dir, stem=derived_stem, formats=formats)
        written_all["derived"] = {k: str(v) for k, v in written_d.items()}
    gap = summarize_samples(samples)

    summary = {
        "ok": True,
        "paper_only": True,
        "not_a_forecast": True,
        "schema": list(SAMPLE_COLUMNS),
        "note": "metrics-only 1s VAMP features; NO trading PnL / expectancy",
        "vamp_formula": (
            "VAMP5=(Σ Pbid_i*Qask_i + Σ Pask_i*Qbid_i)/(ΣQbid+ΣQask); "
            "edge_bps=1e4*(VAMP5-mid)/mid; mid=(bb+ba)/2"
        ),
        "inst_id": args.inst_id,
        "inputs": [str(p) for p in inputs],
        "ingest": ingest.to_dict(),
        "gaps": gap.to_dict(),
        "n_samples_1s": gap.n_samples_1s,
        "n_vamp_valid": gap.n_vamp_valid,
        "n_vamp_z_valid": gap.n_vamp_z_valid,
        "written": written_all,
        "out_dir": str(out_dir),
        "lock_freeze": False,
        "scored_paper": False,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
