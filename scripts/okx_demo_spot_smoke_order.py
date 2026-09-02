#!/usr/bin/env python3
"""OKX EEA SPOT demo smoke: DRY-RUN by default.

Places a real demo order ONLY with --i-confirm-demo-order AND --symbol.
Always mode=demo + x-simulated-trading:1. Live is impossible from this script.
Never prints secrets.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from atlas.okx.client import EEA_REST_BASE, OkxEeaClient  # noqa: E402
from atlas.oms.spot_demo import (  # noqa: E402
    DEMO_FUNDS_HINT,
    DemoFundsMissing,
    OmsRiskBlocked,
    SpotDemoOms,
    round_px,
    _dec,
)


def _print(payload: dict) -> None:
    print(json.dumps(payload, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="SPOT demo smoke. Dry-run unless --i-confirm-demo-order is set."
    )
    p.add_argument("--symbol", default=None, help="SPOT instId e.g. DOGE-USDT")
    p.add_argument("--side", choices=("buy", "sell"), default="buy")
    p.add_argument("--ord-type", choices=("limit", "market"), default="limit")
    p.add_argument(
        "--px-offset-frac",
        type=float,
        default=0.40,
        help="Limit buy px = last*(1-offset); sell = last*(1+offset). Default 0.40.",
    )
    p.add_argument("--timeout-sec", type=float, default=8.0)
    p.add_argument("--secrets-path", default=None)
    p.add_argument("--data-dir", default=str(_ROOT / "data"))
    p.add_argument(
        "--i-confirm-demo-order",
        action="store_true",
        help="Actually place a tiny demo order. Default is dry-run (size only).",
    )
    args = p.parse_args(argv)

    confirm = bool(args.i_confirm_demo_order)
    if confirm and not args.symbol:
        _print(
            {
                "ok": False,
                "dry_run": False,
                "error": "--symbol is required with --i-confirm-demo-order",
            }
        )
        return 2

    allow_trade = confirm
    try:
        with OkxEeaClient(
            mode="demo",
            allow_trade=allow_trade,
            secrets_path=args.secrets_path,
            rest_base=EEA_REST_BASE,
        ) as client:
            oms = SpotDemoOms(client, data_dir=args.data_dir, run_id="oms-spot-smoke")
            try:
                snap = oms.refresh_account(fail_closed_zero=True)
            except DemoFundsMissing as exc:
                _print(
                    {
                        "ok": False,
                        "dry_run": not confirm,
                        "mode": "demo",
                        "simulated_header": True,
                        "error": str(exc),
                        "totalEq": "0",
                        "demo_funds_ok": False,
                        "hint": DEMO_FUNDS_HINT,
                    }
                )
                return 2

            public = snap.public_dict()
            inst = oms.choose_inst(args.symbol)
            inst_id = str(inst.get("instId"))
            last = oms.last_price(inst_id)
            gate = oms.gate_new_entry(snap, inst_ids={inst_id})
            if not gate.get("allowed"):
                _print(
                    {
                        "ok": False,
                        "dry_run": not confirm,
                        "mode": "demo",
                        "totalEq": public.get("totalEq"),
                        "demo_funds_ok": True,
                        "gate": gate,
                        "instId": inst_id,
                        "last": last,
                    }
                )
                return 3

            px = None
            if args.ord_type == "limit":
                if args.side == "buy":
                    raw = last * (1.0 - float(args.px_offset_frac))
                else:
                    raw = last * (1.0 + float(args.px_offset_frac))
                if raw <= 0:
                    raw = last * 0.5
                tick = _dec(inst.get("tickSz") or "0.00000001")
                px = float(round_px(Decimal(str(raw)), tick, side=args.side))

            plan = oms.size_order(
                snap,
                inst,
                last_px=last,
                tiny=True,
                px=px,
                side=args.side,
                ord_type=args.ord_type,
            )
            result = {
                "ok": plan.allowed,
                "dry_run": not confirm,
                "mode": "demo",
                "simulated_header": True,
                "rest_base": EEA_REST_BASE,
                "totalEq": public.get("totalEq"),
                "demo_funds_ok": True,
                "account_mode": public.get("account_mode"),
                "inst": {
                    "instId": inst_id,
                    "minSz": inst.get("minSz"),
                    "lotSz": inst.get("lotSz"),
                    "tickSz": inst.get("tickSz"),
                    "state": inst.get("state"),
                },
                "last": last,
                "plan": plan.as_dict(),
                "gate": gate,
                "placed": False,
            }
            if not plan.allowed:
                result["error"] = plan.reason
                _print(result)
                return 3

            placed = oms.place(plan, dry_run=not confirm)
            result["place"] = {
                k: placed.get(k)
                for k in ("dry_run", "placed", "reason", "response", "http_status")
                if k in placed
            }
            result["placed"] = bool(placed.get("placed"))

            if confirm and args.ord_type == "limit" and placed.get("placed"):
                data = (placed.get("response") or {}).get("data") or []
                ord_id = ""
                if data and isinstance(data, list) and isinstance(data[0], dict):
                    ord_id = str(data[0].get("ordId") or "")
                    result["ordId"] = ord_id
                    result["sCode"] = data[0].get("sCode")
                    result["sMsg"] = data[0].get("sMsg")
                if ord_id:
                    deadline = time.time() + float(args.timeout_sec)
                    state = ""
                    while time.time() < deadline:
                        od = oms.get_order(inst_id, ord_id)
                        rows = od.get("data") or []
                        if rows and isinstance(rows[0], dict):
                            state = str(rows[0].get("state") or "")
                            result["order_state"] = state
                            if state in {"filled", "canceled", "mmp_canceled"}:
                                break
                            if state in {"live", "partially_filled"}:
                                time.sleep(0.5)
                                continue
                            break
                        time.sleep(0.5)
                    if state in {"live", "partially_filled", ""}:
                        cancel = oms.cancel(inst_id, ord_id)
                        result["cancel"] = cancel.get("response")
                        result["cancel_reason"] = "unfilled_timeout"
            _print(result)
            if confirm and not result["placed"]:
                return 4
            return 0 if result["ok"] else 3
    except (OmsRiskBlocked, DemoFundsMissing) as exc:
        _print({"ok": False, "error": str(exc), "mode": "demo", "dry_run": not confirm})
        return 3
    except Exception as exc:  # noqa: BLE001
        _print(
            {
                "ok": False,
                "mode": "demo",
                "dry_run": not confirm,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
