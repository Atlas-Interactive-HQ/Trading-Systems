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
    args = p.parse_args(argv)
    chosen = [n for n, v in (("fixtures", args.fixtures), ("replay", args.replay), ("shadow", args.shadow)) if v]
    if len(chosen) > 1:
        raise SystemExit("kies één van --fixtures / --replay / --shadow")

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if args.replay and args.data_dir is None:
        data_dir = Path(cfg.data_dir) / "replay"
    if args.shadow and args.data_dir is None:
        data_dir = Path(cfg.data_dir) / "shadow"
    if not data_dir.is_absolute() and not args.fixtures:
        data_dir = Path.cwd() / data_dir

    app = create_app(
        data_dir=None if args.fixtures else data_dir,
        config_path=args.config,
        use_fixtures=bool(args.fixtures),
        use_replay=bool(args.replay),
        use_shadow=bool(args.shadow),
    )
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "uvicorn ontbreekt. Installeer met: pip install -e '.[dashboard]'"
        ) from exc

    print(
        f"Atlas dashboard v0  http://{args.host}:{args.port}  "
        f"({'fixtures' if args.fixtures else 'shadow ' + str(data_dir) if args.shadow else 'replay ' + str(data_dir) if args.replay else data_dir})  "
        "— alleen lezen, geen orders",
        flush=True,
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
