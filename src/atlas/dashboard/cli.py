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
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute() and not args.fixtures:
        data_dir = Path.cwd() / data_dir

    app = create_app(
        data_dir=None if args.fixtures else data_dir,
        config_path=args.config,
        use_fixtures=bool(args.fixtures),
    )
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "uvicorn ontbreekt. Installeer met: pip install -e '.[dashboard]'"
        ) from exc

    print(
        f"Atlas dashboard v0  http://{args.host}:{args.port}  "
        f"({'fixtures' if args.fixtures else data_dir})  — alleen lezen, geen orders",
        flush=True,
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
