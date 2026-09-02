#!/usr/bin/env python3
"""OKX EEA demo account snapshot. Never prints secrets. Never places orders."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from atlas.okx.client import EEA_REST_BASE, OkxEeaClient  # noqa: E402
from atlas.oms.spot_demo import DEMO_FUNDS_HINT, SpotDemoOms  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="OKX EEA demo account snapshot (read-only). "
        "Always sends x-simulated-trading:1. Does not trade."
    )
    p.add_argument("--secrets-path", default=None)
    p.add_argument("--data-dir", default=str(_ROOT / "data"))
    args = p.parse_args(argv)

    try:
        with OkxEeaClient(
            mode="demo",
            allow_trade=False,
            secrets_path=args.secrets_path,
            rest_base=EEA_REST_BASE,
        ) as client:
            oms = SpotDemoOms(client, data_dir=args.data_dir, run_id="oms-snapshot")
            try:
                snap = oms.refresh_account(fail_closed_zero=False)
            except Exception as exc:  # noqa: BLE001
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "mode": "demo",
                            "simulated_header": True,
                            "error": f"{type(exc).__name__}: {exc}",
                            "totalEq": None,
                            "demo_funds_ok": False,
                            "rest_base": EEA_REST_BASE,
                        }
                    )
                )
                return 1
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "ok": False,
                    "mode": "demo",
                    "simulated_header": True,
                    "error": f"{type(exc).__name__}: {exc}",
                    "totalEq": None,
                    "demo_funds_ok": False,
                    "rest_base": EEA_REST_BASE,
                }
            )
        )
        return 1

    funds_ok = snap.funds_ok
    out = {
        "ok": snap.code == "0",
        "mode": "demo",
        "simulated_header": True,
        "rest_base": EEA_REST_BASE,
        **snap.public_dict(),
        "order_smoke_can_proceed": funds_ok,
        "demo_funds_note": None if funds_ok else DEMO_FUNDS_HINT,
    }
    print(json.dumps(out, indent=2))
    if snap.code != "0":
        return 1
    if not funds_ok:
        # Auth worked; funds missing is a closed fail for trading, exit 2.
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
