#!/usr/bin/env python3
"""Manual ≤€20 DOGE-USDC practice round-trip. READ-ONLY by default.

Mutating only with --sell-fill / --buy-back / --roundtrip.
Limit only (bid/ask). Never market. Never asset transfer.
Requires tiny_live+allow_trade on the client. Cap 20 unchanged.
not_a_forecast. Not Phase C. Not a weekday routine.
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
    DEFAULT_SZ,
    LOCKED_INST,
    PRACTICE_NOTIONAL_DEFAULT,
    run_roundtrip,
)
from atlas.oms.spot_demo import redact_record  # noqa: E402


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(redact_record(payload), indent=2, default=str))


def main(argv: list[str] | None = None, *, client: OkxEeaClient | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Tiny-live DOGE-USDC practice round-trip. Default READ-ONLY. "
            "Mutate only with --sell-fill, --buy-back, or --roundtrip."
        )
    )
    p.add_argument("--secrets-path", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument(
        "--inst-id",
        default=LOCKED_INST,
        help="SPOT instId (default DOGE-USDC; override only if allowlisted)",
    )
    p.add_argument("--sz", default=DEFAULT_SZ, help="Base size to SELL (default 50 DOGE)")
    p.add_argument(
        "--quote-sz",
        default=None,
        help="Quote size (USDC) to spend on buy-back. Default: available trading USDC.",
    )
    p.add_argument(
        "--max-notional",
        type=float,
        default=PRACTICE_NOTIONAL_DEFAULT,
        help=f"Script pre-check (default {PRACTICE_NOTIONAL_DEFAULT:g}). Hard client cap is {TINY_LIVE_NOTIONAL_CAP:g}.",
    )
    p.add_argument("--timeout-sec", type=float, default=20.0)
    p.add_argument("--poll-sec", type=float, default=0.4)
    p.add_argument(
        "--sell-fill",
        action="store_true",
        help="Aggressive limit SELL at/near bid. Poll; timeout cancels leftover.",
    )
    p.add_argument(
        "--buy-back",
        action="store_true",
        help="Aggressive limit BUY at/near ask using available USDC (or --quote-sz).",
    )
    p.add_argument(
        "--roundtrip",
        action="store_true",
        help="Sell-fill then buy-back in one process (buy only if sell filled).",
    )
    args = p.parse_args(argv)
    sell = bool(args.sell_fill or args.roundtrip)
    buy = bool(args.buy_back or args.roundtrip)
    mutate = sell or buy
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
        result = run_roundtrip(
            client,
            sell=sell,
            buy=buy,
            sz=str(args.sz),
            quote_sz=args.quote_sz,
            inst_id=args.inst_id,
            max_notional=float(args.max_notional),
            timeout_s=float(args.timeout_sec),
            poll_s=float(args.poll_sec),
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
