#!/usr/bin/env python3
"""Manual ≤€20 DOGE-USDC resting limit exits. READ-ONLY by default.

Mutating only with --place-tp / --place-protect-limit / --cancel-ord /
--cancel-all-pending. Limit SELL only. Never market. Never exchange stop.
A new place is left RESTING (this script does not auto-cancel it).
Requires tiny_live+allow_trade on the client. Cap 20 unchanged.
not_a_forecast. Not Phase C. Not a weekday auto-TP routine.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from atlas.okx.client import (  # noqa: E402
    EEA_REST_BASE,
    TINY_LIVE_NOTIONAL_CAP,
    LiveTradingBlocked,
    OkxEeaClient,
)
from atlas.okx.live20 import (  # noqa: E402
    LOCKED_INST,
    PRACTICE_NOTIONAL_DEFAULT,
    run_resting_exits,
)
from atlas.oms.spot_demo import redact_record  # noqa: E402


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(redact_record(payload), indent=2, default=str))


def main(argv: list[str] | None = None, *, client: OkxEeaClient | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Tiny-live DOGE-USDC resting exits. Default READ-ONLY. "
            "Mutate only with --place-tp, --place-protect-limit, --cancel-ord, "
            "or --cancel-all-pending. Places are left resting (no auto-cancel)."
        )
    )
    p.add_argument("--secrets-path", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument(
        "--inst-id",
        default=LOCKED_INST,
        help="SPOT instId (default DOGE-USDC; override only if allowlisted)",
    )
    p.add_argument(
        "--sz",
        default=None,
        help="Base size to SELL (required with --place-tp / --place-protect-limit)",
    )
    p.add_argument(
        "--px",
        type=float,
        default=None,
        help="Absolute limit px. TP: must be above mid. Protect: must be below mid.",
    )
    p.add_argument(
        "--tp-pct",
        type=float,
        default=None,
        help="TP only: percent above mid (e.g. 5 = 5%%). Not a stop.",
    )
    p.add_argument(
        "--max-notional",
        type=float,
        default=PRACTICE_NOTIONAL_DEFAULT,
        help=f"Script pre-check (default {PRACTICE_NOTIONAL_DEFAULT:g}). Hard client cap is {TINY_LIVE_NOTIONAL_CAP:g}.",
    )
    p.add_argument(
        "--place-tp",
        action="store_true",
        help="Limit SELL above mid ( --px or --tp-pct ) + --sz. Leave RESTING.",
    )
    p.add_argument(
        "--place-protect-limit",
        action="store_true",
        help=(
            "Limit SELL at --px below mid + --sz. Leave RESTING. "
            "This is NOT an exchange stop or market order; if px is at/below bid it may fill immediately."
        ),
    )
    p.add_argument("--cancel-ord", default=None, help="Cancel one resting order by ordId (DOGE-USDC).")
    p.add_argument(
        "--cancel-all-pending",
        action="store_true",
        help="Cancel all pending SPOT orders for this instId (default DOGE-USDC).",
    )
    args = p.parse_args(argv)
    mutate = bool(
        args.place_tp or args.place_protect_limit or args.cancel_ord or args.cancel_all_pending
    )
    data_dir = Path(args.data_dir) if args.data_dir else _ROOT / "data"
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    own = False
    try:
        if client is None:
            own = True
            client = OkxEeaClient(
                mode="live",
                allow_trade=mutate,
                tiny_live=mutate,
                secrets_path=args.secrets_path,
                rest_base=EEA_REST_BASE,
            )
        result = run_resting_exits(
            client,
            place_tp=bool(args.place_tp),
            place_protect=bool(args.place_protect_limit),
            cancel_ord=args.cancel_ord,
            cancel_all=bool(args.cancel_all_pending),
            px=args.px,
            tp_pct=args.tp_pct,
            sz=args.sz,
            inst_id=args.inst_id,
            max_notional=float(args.max_notional),
            data_dir=data_dir,
        )
        _print(result)
        return 0 if result.get("ok") else 2
    except LiveTradingBlocked as exc:
        _print(
            {
                "ok": False,
                "dry_run": not mutate,
                "error": str(exc),
                "place_orders": False,
                "not_a_forecast": True,
            }
        )
        return 3
    except Exception as exc:  # noqa: BLE001
        _print(
            {
                "ok": False,
                "dry_run": not mutate,
                "error": f"{type(exc).__name__}: {exc}",
                "place_orders": False,
                "not_a_forecast": True,
            }
        )
        return 1
    finally:
        if own and client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
