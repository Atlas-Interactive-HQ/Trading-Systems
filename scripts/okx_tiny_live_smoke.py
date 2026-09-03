#!/usr/bin/env python3
"""OKX EEA tiny-live smoke. READ-ONLY by default. Never prints secrets.

Mutating far-limit+cancel only if BOTH --place-far-limit AND --cancel.
Live POST still requires client tiny_live+allow_trade+€20 cap.
Never market. Never asset transfer. Not a routine. not_a_forecast.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from atlas.okx.client import (  # noqa: E402
    EEA_REST_BASE,
    TINY_LIVE_NOTIONAL_CAP,
    LiveTradingBlocked,
    OkxEeaClient,
    estimate_spot_limit_notional,
)
from atlas.oms.spot_demo import redact_record  # noqa: E402

LOCKED_INST = "DOGE-USDC"  # EEA Crypto allowlist on this live key is USDC, not USDT
DEFAULT_SZ = "10"
PX_MULT = 2.0


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(redact_record(payload), indent=2, default=str))


def _ticker_last(payload: MappingLike) -> float | None:
    data = payload.get("data") or []
    if isinstance(data, list) and data and isinstance(data[0], dict):
        raw = data[0].get("last")
        try:
            px = float(raw)
        except (TypeError, ValueError):
            return None
        return px if px > 0 else None
    return None


def _avail_ccy(payload: MappingLike, ccy: str) -> float:
    data = payload.get("data") or []
    if not (isinstance(data, list) and data and isinstance(data[0], dict)):
        return 0.0
    details = data[0].get("details") or []
    if not isinstance(details, list):
        return 0.0
    want = ccy.upper()
    for row in details:
        if not isinstance(row, dict):
            continue
        if str(row.get("ccy") or "").upper() != want:
            continue
        for key in ("availBal", "availEq", "cashBal", "eq"):
            try:
                val = float(row.get(key) or 0)
            except (TypeError, ValueError):
                continue
            if val > 0:
                return val
        return 0.0
    return 0.0


def _public_balance(payload: MappingLike) -> dict[str, Any]:
    data = payload.get("data") or []
    row = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
    details = []
    for d in row.get("details") or []:
        if not isinstance(d, dict):
            continue
        details.append(
            {
                "ccy": d.get("ccy"),
                "eq": d.get("eq"),
                "availBal": d.get("availBal"),
                "cashBal": d.get("cashBal"),
                "frozenBal": d.get("frozenBal"),
            }
        )
    return {
        "code": payload.get("code"),
        "msg": payload.get("msg"),
        "totalEq": row.get("totalEq"),
        "details": details,
    }


def _public_asset(payload: MappingLike) -> dict[str, Any]:
    data = payload.get("data") or []
    rows = []
    if isinstance(data, list):
        for d in data:
            if not isinstance(d, dict):
                continue
            rows.append(
                {
                    "ccy": d.get("ccy"),
                    "bal": d.get("bal"),
                    "availBal": d.get("availBal"),
                    "frozenBal": d.get("frozenBal"),
                }
            )
    return {"code": payload.get("code"), "msg": payload.get("msg"), "data": rows}


def _pending_public(payload: MappingLike) -> dict[str, Any]:
    data = payload.get("data") or []
    n = len(data) if isinstance(data, list) else 0
    return {"code": payload.get("code"), "msg": payload.get("msg"), "n": n}


MappingLike = dict[str, Any]


def run_session(
    client: OkxEeaClient,
    *,
    mutate: bool,
    inst_id: str = LOCKED_INST,
    sz: str = DEFAULT_SZ,
) -> dict[str, Any]:
    """Read-only snapshot; optional far-limit sell + cancel. Never market. Never transfer."""
    inst = str(inst_id).strip().upper()
    trading = client.get_balance()
    funding = client.get_asset_balances()
    ticker = client.get_ticker(inst)
    pending = client.get_orders_pending(inst_type="SPOT", inst_id=inst)
    last = _ticker_last(ticker)
    avail = _avail_ccy(trading, inst.split("-", 1)[0])
    result: dict[str, Any] = {
        "ok": True,
        "dry_run": not mutate,
        "mode": client.mode,
        "tiny_live": bool(getattr(client, "tiny_live", False)),
        "place_orders": False,
        "not_a_forecast": True,
        "instId": inst,
        "side": "sell",
        "sz": str(sz),
        "px_mult": PX_MULT,
        "last": last,
        "avail_base": avail,
        "notional_cap": TINY_LIVE_NOTIONAL_CAP,
        "trading_balance": _public_balance(trading),
        "funding_balances": _public_asset(funding),
        "pending": _pending_public(pending),
        "placed": False,
        "cancelled": False,
        "disclaimer": (
            "tiny-live smoke. not_a_forecast. not Phase C. not a routine. "
            "manual far-limit+cancel only. BTC EMA observer + Phase A DOGE 15m unchanged."
        ),
    }
    posts = 0
    if not mutate:
        result["note"] = (
            "read-only. mutating requires BOTH --place-far-limit AND --cancel."
        )
        return result

    if last is None:
        result["ok"] = False
        result["error"] = "no ticker last (fail closed, no order)"
        return result
    try:
        size = float(sz)
    except (TypeError, ValueError):
        result["ok"] = False
        result["error"] = "invalid sz (fail closed, no order)"
        return result
    if avail < size:
        result["ok"] = False
        result["error"] = f"avail {avail} < sz {size} (fail closed, no order)"
        return result
    px = last * PX_MULT
    result["px"] = px
    notional = estimate_spot_limit_notional(sz, px)
    result["notional"] = notional
    if notional is None or notional > TINY_LIVE_NOTIONAL_CAP:
        result["ok"] = False
        result["error"] = (
            f"notional {notional} exceeds cap {TINY_LIVE_NOTIONAL_CAP:g} "
            "(fail closed, no order)"
        )
        return result

    placed = client.place_spot_limit(inst, "sell", str(sz), str(px))
    posts += 1
    result["place_response"] = {
        k: placed.get(k) for k in ("code", "msg", "data") if k in placed
    }
    data = placed.get("data") or []
    ord_id = ""
    s_code = ""
    if isinstance(data, list) and data and isinstance(data[0], dict):
        ord_id = str(data[0].get("ordId") or "")
        s_code = str(data[0].get("sCode") or "")
        result["ordId"] = ord_id
        result["sCode"] = s_code
        result["sMsg"] = data[0].get("sMsg")
    placed_ok = str(placed.get("code")) == "0" and s_code in {"0", ""} and bool(ord_id)
    result["placed"] = placed_ok
    if not placed_ok:
        result["ok"] = False
        result["error"] = "place did not return ordId (no cancel)"
        result["n_posts"] = posts
        return result

    cancel = client.cancel_order(instId=inst, ordId=ord_id)
    posts += 1
    result["cancel_response"] = {
        k: cancel.get(k) for k in ("code", "msg", "data") if k in cancel
    }
    cdata = cancel.get("data") or []
    c_ok = str(cancel.get("code")) == "0"
    if isinstance(cdata, list) and cdata and isinstance(cdata[0], dict):
        result["cancel_sCode"] = cdata[0].get("sCode")
        c_ok = c_ok and str(cdata[0].get("sCode") or "") in {"0", ""}
    result["cancelled"] = bool(c_ok)
    result["n_posts"] = posts
    result["ok"] = bool(c_ok)
    return result


def main(argv: list[str] | None = None, *, client: OkxEeaClient | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Tiny-live OKX EEA smoke. Default READ-ONLY. "
            "Mutate only with BOTH --place-far-limit AND --cancel."
        )
    )
    p.add_argument("--secrets-path", default=None)
    p.add_argument(
        "--inst-id",
        default=LOCKED_INST,
        help="SPOT instId (default DOGE-USDC; override e.g. DOGE-USDT if the key allowlists it)",
    )
    p.add_argument("--sz", default=DEFAULT_SZ, help="Base size to sell (default 10 DOGE)")
    p.add_argument(
        "--place-far-limit",
        action="store_true",
        help="Opt-in to place a 2× last SELL limit. Requires --cancel too.",
    )
    p.add_argument(
        "--cancel",
        action="store_true",
        help="Opt-in to cancel the same ordId. Requires --place-far-limit too.",
    )
    args = p.parse_args(argv)
    mutate = bool(args.place_far_limit) and bool(args.cancel)
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
        result = run_session(
            client, mutate=mutate, inst_id=args.inst_id, sz=str(args.sz)
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
