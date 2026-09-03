"""CLI: atlas-dashboard — local read-only UI. No keys, no orders."""

from __future__ import annotations

import argparse
from pathlib import Path

from atlas.common.config import load_config
from atlas.dashboard.app import create_app


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Atlas Trading Systems dashboard v0 (read-only). Geen live orders."
    )
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None, help="Root with oms/ and paper/ journals")
    p.add_argument(
        "--fixtures",
        action="store_true",
        help="Serve bundled sample journals (no local sessions required)",
    )
    p.add_argument(
        "--replay",
        action="store_true",
        help="Read data/replay journals (historical-replay). Distinct from Phase A data/oms/.",
    )
    p.add_argument(
        "--shadow",
        action="store_true",
        help="Read data/shadow journals (would-place / blocked). No orders.",
    )
    p.add_argument(
        "--ema",
        action="store_true",
        help="Read data/ema journals (EMA paper observer). No orders. Not Phase A DOGE.",
    )
    p.add_argument(
        "--oms",
        action="store_true",
        help="Read data/oms journals (Phase A DOGE). Default when no other mode is set.",
    )
    args = p.parse_args(argv)
    chosen = [
        n
        for n, v in (
            ("fixtures", args.fixtures),
            ("replay", args.replay),
            ("shadow", args.shadow),
            ("ema", args.ema),
            ("oms", args.oms),
        )
        if v
    ]
    if len(chosen) > 1:
        raise SystemExit("kies één van --fixtures / --replay / --shadow / --ema / --oms")

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if args.replay and args.data_dir is None:
        data_dir = Path(cfg.data_dir) / "replay"
    if args.shadow and args.data_dir is None:
        data_dir = Path(cfg.data_dir) / "shadow"
    if args.ema and args.data_dir is None:
        data_dir = Path(cfg.data_dir) / "ema"
    if not data_dir.is_absolute() and not args.fixtures:
        data_dir = Path.cwd() / data_dir

    app = create_app(
        data_dir=None if args.fixtures else data_dir,
        config_path=args.config,
        use_fixtures=bool(args.fixtures),
        use_replay=bool(args.replay),
        use_shadow=bool(args.shadow),
        use_ema=bool(args.ema),
    )
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "uvicorn ontbreekt. Installeer met: pip install -e '.[dashboard]'"
        ) from exc

    if args.fixtures:
        src_label = "fixtures"
    elif args.shadow:
        src_label = "shadow " + str(data_dir)
    elif args.replay:
        src_label = "replay " + str(data_dir)
    elif args.ema:
        src_label = "ema " + str(data_dir)
    else:
        src_label = str(data_dir)
    print(
        f"Atlas dashboard v0  http://{args.host}:{args.port}  "
        f"({src_label})  "
        "— alleen lezen, geen orders",
        flush=True,
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
