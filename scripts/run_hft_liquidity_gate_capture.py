#!/usr/bin/env python3
"""Sketch runner for the 24h BTC+ETH+DOGE EEA X-Perp liquidity gate.

Does NOT invent capture numbers. A real 24h simultaneous capture is out of
scope for this PR. This script:

1. Prints the locked plan + metric schema.
2. Optionally resolves live X-Perp instIds from public instruments (network).
3. Refuses to emit a selected instrument without a real 24h capture.

NO strategy PnL. not_a_forecast. config/default.yaml untouched.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from atlas.scalp_hft.liquidity_gate import (  # noqa: E402
    CHANNELS,
    LIQUIDITY_GATE_BASES,
    LiquidityGatePlan,
    empty_metrics_row,
    resolve_liquidity_inst_ids,
    select_instrument,
)


def _resolve_live() -> dict:
    """Public instruments only. Fail-closed on HTTP / missing ETH."""
    import httpx

    from atlas.common.config import load_config
    from atlas.collectors.okx_eea_public import OkxEeaPublicCollector

    cfg = load_config(None)
    col = OkxEeaPublicCollector(cfg)
    with httpx.Client(headers={"User-Agent": "atlas-trading/0.1 public-md"}, timeout=30.0) as client:
        data = col._get(client, "/api/v5/public/instruments", {"instType": "FUTURES"})
    rows = data.get("data") or []
    return resolve_liquidity_inst_ids(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--resolve-instruments",
        action="store_true",
        help="hit public EEA instruments (read-only) to resolve BTC/ETH/DOGE X-Perp",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "accounting_v2" / "hft_liquidity_gate_plan.json",
    )
    args = ap.parse_args(argv)
    plan = LiquidityGatePlan().to_dict()
    bundle: dict = {
        "ok": True,
        "plan": plan,
        "bases": list(LIQUIDITY_GATE_BASES),
        "channels": list(CHANNELS),
        "resolved": None,
        "metrics": [empty_metrics_row(b).to_dict() for b in LIQUIDITY_GATE_BASES],
        "selection": select_instrument([]),
        "capture_ran": False,
        "do_not_invent_capture_numbers": True,
        "no_strategy_pnl": True,
        "not_a_forecast": True,
        "place_orders": False,
        "sketch": (
            "python scripts/run_okx_public.py --capture --ws-only "
            "--duration-sec 86400 --inst-id <resolved BTC> "
            "--inst-id <resolved ETH> --inst-id <resolved DOGE>  "
            "# simultaneous 24h; then compute METRIC_FIELDS per inst. "
            "Do not start HFT alpha until select_instrument returns a lock."
        ),
    }
    if args.resolve_instruments:
        try:
            bundle["resolved"] = _resolve_live()
        except Exception as exc:  # noqa: BLE001
            bundle["ok"] = False
            bundle["resolved"] = {
                "ok": False,
                "fail_closed": True,
                "error": f"{type(exc).__name__}: {exc}",
                "do_not_invent_eth_instid": True,
            }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(bundle, indent=2))
    return 0 if bundle.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
