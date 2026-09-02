#!/usr/bin/env python3
"""OKX EEA signed auth smoke: balance read. Never prints secrets. Never places orders."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import httpx  # noqa: E402

from atlas.okx.client import EEA_REST_BASE, USER_AGENT, OkxEeaClient  # noqa: E402


def _egress_ip() -> str:
    headers = {"User-Agent": USER_AGENT}
    for url in (
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://1.1.1.1/cdn-cgi/trace",
    ):
        try:
            r = httpx.get(url, headers=headers, timeout=10.0)
            r.raise_for_status()
            text = r.text.strip()
            if "ip=" in text:
                for line in text.splitlines():
                    if line.startswith("ip="):
                        return line.split("=", 1)[1].strip()
            # ipify / ifconfig.me return a bare address
            first = text.splitlines()[0].strip()
            if first and " " not in first and len(first) < 64:
                return first
        except Exception:  # noqa: BLE001
            continue
    return "unknown"


def _total_eq(payload: dict) -> str | None:
    data = payload.get("data") or []
    if isinstance(data, list) and data and isinstance(data[0], dict):
        val = data[0].get("totalEq")
        if val is not None:
            return str(val)
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="OKX EEA auth smoke (read-only). --mode live is READ-ONLY. "
        "demo always sends x-simulated-trading:1 and still does not trade here."
    )
    p.add_argument("--mode", choices=("demo", "live"), required=True)
    p.add_argument("--secrets-path", default=None, help="Override ATLAS_OKX_SECRETS_PATH")
    args = p.parse_args(argv)

    ip = _egress_ip()
    try:
        with OkxEeaClient(
            mode=args.mode,
            allow_trade=False,
            secrets_path=args.secrets_path,
            rest_base=EEA_REST_BASE,
        ) as client:
            payload = client.get_balance()
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "ok": False,
                    "mode": args.mode,
                    "code": None,
                    "msg": f"{type(exc).__name__}: {exc}",
                    "totalEq": None,
                    "egress_ip": ip,
                    "http_status": None,
                    "simulated_header": args.mode == "demo",
                }
            )
        )
        return 1

    code = str(payload.get("code", ""))
    msg = payload.get("msg", "")
    http_status = payload.get("_http_status")
    total_eq = _total_eq(payload)
    ok = code == "0"
    print(
        json.dumps(
            {
                "ok": ok,
                "mode": args.mode,
                "code": code,
                "msg": msg,
                "totalEq": total_eq,
                "egress_ip": ip,
                "http_status": http_status,
                "simulated_header": args.mode == "demo",
                "rest_base": EEA_REST_BASE,
            }
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
