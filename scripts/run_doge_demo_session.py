#!/usr/bin/env python3
"""DOGE demo session: public breakout signals, dry journal by default.

Places OKX EEA **demo** orders ONLY with --place-demo-orders (alias:
--live-demo-orders). Always mode=demo. Live is impossible from this script.
PEPE is not routed. Prefer far limits / tiny size when placing.
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

from atlas.common.config import load_config  # noqa: E402
from atlas.common.logging import setup_logging  # noqa: E402
from atlas.okx.client import EEA_REST_BASE, OkxEeaClient  # noqa: E402
from atlas.oms.doge_demo_loop import DogeDemoLoop, VenueRoutingError  # noqa: E402
from atlas.oms.spot_demo import (  # noqa: E402
    DEMO_FUNDS_HINT,
    DemoFundsMissing,
    OmsRiskBlocked,
    SpotDemoOms,
)
from atlas.okx.client import LiveTradingBlocked, PaperTradeDisabled  # noqa: E402
from atlas.strategy.breakout import BreakoutParams, BreakoutV1  # noqa: E402


def _print(payload: dict) -> None:
    print(json.dumps(payload, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="DOGE demo session. Signal journal by default; demo orders need an explicit flag."
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--venue", choices=("spot", "xperp", "both"), default="both")
    p.add_argument("--bars", type=int, default=96, help="Closed 15m bars to scan (most recent)")
    p.add_argument("--oneh-filter", default=None, choices=("stub", "off"))
    p.add_argument("--secrets-path", default=None)
    p.add_argument(
        "--place-demo-orders",
        action="store_true",
        help="Place tiny far-limit demo orders via allow_trade. Default off (signals only).",
    )
    p.add_argument(
        "--live-demo-orders",
        action="store_true",
        help="Alias of --place-demo-orders (demo matching engine, never live).",
    )
    args = p.parse_args(argv)

    place = bool(args.place_demo_orders or args.live_demo_orders)
    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    rest_base = (cfg.okx.rest_base if cfg.okx else EEA_REST_BASE).rstrip("/")
    oms = None
    client_cm = None
    try:
        if place:
            client_cm = OkxEeaClient(
                mode="demo",
                allow_trade=True,
                secrets_path=args.secrets_path,
                rest_base=rest_base,
            )
            client_cm.__enter__()
            demo = cfg.okx.doge_demo
            oms = SpotDemoOms(
                client_cm,
                data_dir=data_dir,
                run_id="doge-demo-place",
                paper_equity_eur=demo.paper_equity_eur,
                daily_kill_frac=demo.daily_kill_frac,
                per_trade_risk_frac=demo.per_trade_risk_frac,
                one_position=demo.one_position,
                tiny_notional_eur=demo.tiny_notional_eur,
            )
        loop = DogeDemoLoop(
            cfg,
            data_dir=data_dir,
            oms=oms,
            rest_base=rest_base,
            run_id="doge-demo-place" if place else "doge-demo-signals",
        )
        if args.oneh_filter:
            bp = loop.strategy.params
            loop.strategy = BreakoutV1(
                BreakoutParams(
                    lookback_15m=bp.lookback_15m,
                    atr_period=bp.atr_period,
                    atr_stop_mult=bp.atr_stop_mult,
                    min_atr_frac=bp.min_atr_frac,
                    oneh_filter=args.oneh_filter,
                    oneh_lookback=bp.oneh_lookback,
                    ranging=False,
                    confirm_closed_only=bp.confirm_closed_only,
                )
            )
        summary = loop.run(
            venue=args.venue,
            place_orders=place,
            bars=args.bars,
            plumbing_if_no_signal=place,
        )
        public = {
            "ok": summary.get("ok"),
            "dry_run": summary.get("dry_run"),
            "mode": "demo",
            "simulated_header": True if place else None,
            "place_orders": place,
            "venue": args.venue,
            "run_id": summary.get("run_id"),
            "n_signals": summary.get("n_signals"),
            "historical_signals_only": summary.get("historical_signals_only"),
            "signals": summary.get("signals"),
            "legs": [
                {
                    k: leg.get(k)
                    for k in (
                        "venue",
                        "instId",
                        "mdInstId",
                        "instType",
                        "tdMode",
                        "n_bars_15m",
                        "n_bars_1h",
                        "last_px",
                        "last_bar_ts_ms",
                        "fetch_error",
                        "n_signals",
                        "current",
                        "place",
                    )
                }
                for leg in summary.get("legs") or []
            ],
            "journal": str(data_dir / "oms"),
        }
        _print(public)
        if any(leg.get("fetch_error") and not leg.get("n_bars_15m") for leg in summary.get("legs") or []):
            return 2 if not any(leg.get("n_bars_15m") for leg in summary.get("legs") or []) else 0
        return 0
    except VenueRoutingError as exc:
        _print({"ok": False, "error": str(exc), "dry_run": not place, "mode": "demo"})
        return 2
    except DemoFundsMissing as exc:
        _print(
            {
                "ok": False,
                "error": str(exc),
                "hint": DEMO_FUNDS_HINT,
                "dry_run": not place,
                "mode": "demo",
            }
        )
        return 3
    except (OmsRiskBlocked, PaperTradeDisabled, LiveTradingBlocked) as exc:
        _print({"ok": False, "error": f"{type(exc).__name__}: {exc}", "dry_run": not place, "mode": "demo"})
        return 3
    except Exception as exc:  # noqa: BLE001
        _print({"ok": False, "error": f"{type(exc).__name__}: {exc}", "dry_run": not place, "mode": "demo"})
        return 1
    finally:
        if client_cm is not None:
            try:
                client_cm.__exit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass


if __name__ == "__main__":
    raise SystemExit(main())
