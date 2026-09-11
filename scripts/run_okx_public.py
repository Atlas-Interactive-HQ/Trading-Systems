#!/usr/bin/env python3
"""CLI: run OKX EEA PUBLIC collector (smoke / continuous Layer B capture).

PAPER / public market-data only. No private order endpoints. No trading keys.
Does not mutate config/default.yaml — pass --inst-id / --channels on the CLI.
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

from atlas.common.config import load_config, refuse_if_secrets_present  # noqa: E402
from atlas.common.logging import setup_logging  # noqa: E402
from atlas.collectors.okx_eea_public import (  # noqa: E402
    LAYER_B_DOGE_XPERP_MD_INST,
    LAYER_B_WS_CHANNELS,
    OkxEeaPublicCollector,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="OKX EEA PUBLIC MD collector (no API keys). Layer B capture via --capture."
    )
    p.add_argument("--config", default=None, help="Path to config YAML")
    p.add_argument(
        "--duration-sec",
        type=float,
        default=60.0,
        help="Run duration seconds (default 60). For continuous ops use a large value.",
    )
    p.add_argument("--ws", action="store_true", help="Also run short public WS stub (legacy smoke)")
    p.add_argument(
        "--capture",
        action="store_true",
        help=(
            "Layer B continuous public WS capture "
            f"(default inst={LAYER_B_DOGE_XPERP_MD_INST}; "
            f"channels={','.join(LAYER_B_WS_CHANNELS)})"
        ),
    )
    p.add_argument(
        "--ws-only",
        action="store_true",
        help="With --capture: skip the legacy REST poll loop (recommended for long runs)",
    )
    p.add_argument(
        "--inst-id",
        action="append",
        default=None,
        help=(
            "Instrument id(s) to capture (repeatable). "
            f"Default for --capture: {LAYER_B_DOGE_XPERP_MD_INST}"
        ),
    )
    p.add_argument(
        "--channels",
        default=None,
        help=(
            "Comma-separated public WS channels "
            f"(default for --capture: {','.join(LAYER_B_WS_CHANNELS)})"
        ),
    )
    p.add_argument(
        "--allow-proxy-swap",
        action="store_true",
        help="Allow classic DOGE-*-SWAP ids (labeled non-X-Perp / PROXY — not Layer B primary)",
    )
    p.add_argument("--data-dir", default=None, help="Override data directory")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    if args.data_dir:
        cfg.data_dir = args.data_dir
    setup_logging(cfg.log_level)
    refuse_if_secrets_present(cfg)

    collector = OkxEeaPublicCollector(cfg)
    channels = None
    if args.channels:
        channels = [c.strip() for c in args.channels.split(",") if c.strip()]

    if args.capture or args.ws_only:
        summary = collector.run(
            duration_sec=args.duration_sec,
            ws_capture=True,
            ws_only=True,
            inst_ids=args.inst_id,
            channels=channels,
            allow_proxy_swap=args.allow_proxy_swap,
        )
    else:
        summary = collector.run(duration_sec=args.duration_sec, enable_ws=args.ws)

    print(json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
