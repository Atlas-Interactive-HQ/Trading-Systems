#!/usr/bin/env python3
"""Dry paper smoke for Atlas Cycle v1.

PAPER / BACKTEST only. Exits non-zero if the requested mode is LIVE, before
any fill is built. Does not read API keys and does not place orders.

Synthetic candles only (see atlas.paper.atlas_cycle.synthetic). A completed
run is a wiring check, not evidence of edge and not a live arm.

    python scripts/run_atlas_cycle_v1_smoke.py
    python scripts/run_atlas_cycle_v1_smoke.py --execution-mode LIVE   # exit 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

from atlas.paper.atlas_cycle.broker import LiveExecutionRefused, parse_execution_mode
from atlas.paper.atlas_cycle.config import (
    classify_live_capital,
    load_atlas_cycle_config,
)
from atlas.paper.atlas_cycle.coordinator import CycleCoordinator
from atlas.paper.atlas_cycle.doge_trend import DogeTrendParams, DogeTrendStrategy
from atlas.paper.atlas_cycle.synthetic import synthetic_smoke_cycle
from atlas.paper.journal import PaperJournal


def _refuse_live(message: str) -> int:
    print(message, file=sys.stderr)
    print("LIVE HOLD — geen orders. PAPER_PASS ≠ live-arm.", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Atlas Cycle v1 paper smoke (no live orders)")
    parser.add_argument(
        "--config",
        default="config/strategies/atlas_cycle_v1.yaml",
        help="Cycle config. Refuses config/default.yaml.",
    )
    parser.add_argument(
        "--execution-mode",
        default=None,
        help="BACKTEST or PAPER. LIVE exits non-zero before any fill.",
    )
    parser.add_argument(
        "--out",
        default="results/atlas_cycle_v1/runs/smoke_summary.json",
        help="Summary JSON path. Not written if LIVE is refused.",
    )
    args = parser.parse_args(argv)

    requested = args.execution_mode
    if requested is None:
        requested = os.environ.get("ATLAS_CYCLE_EXECUTION_MODE")
    if requested and str(requested).strip().upper().startswith("LIVE"):
        return _refuse_live("LIVE HOLD: refusing Atlas Cycle v1 smoke before any fill.")

    try:
        cfg = load_atlas_cycle_config(args.config)
    except LiveExecutionRefused as exc:
        return _refuse_live(str(exc))

    if args.execution_mode:
        try:
            mode = parse_execution_mode(args.execution_mode)
        except LiveExecutionRefused as exc:
            return _refuse_live(str(exc))
        cfg = replace(cfg, execution_mode=mode)

    if cfg.execution_mode.value not in ("BACKTEST", "PAPER"):
        return _refuse_live(f"refusing execution mode {cfg.execution_mode!r}")

    bars_15 = synthetic_smoke_cycle()
    reserve_before = None
    coord = CycleCoordinator.from_config(cfg)
    # Wiring check only. The yaml warm-up stays 250; this short series is
    # paired with 60 closed 4H so one cycle can finish in-process.
    coord.doge = DogeTrendStrategy(
        DogeTrendParams(
            entry_mode=cfg.entry_frozen,
            warmup_4h=60,
            intent_ttl_ms=cfg.intent_ttl_ms,
        )
    )
    reserve_before = coord.ledger.btc_reserve_qty
    out_path = Path(args.out)
    journal = PaperJournal(out_path.parent, "atlas-cycle-v1-smoke")
    fills = []
    settlement = None
    for bar in bars_15:
        step = coord.push_doge_bar(bar)
        for fill in step.fills:
            fills.append(fill)
            journal.append(
                "fills",
                {
                    "symbol": fill.symbol,
                    "side": fill.side,
                    "qty": str(fill.qty),
                    "price": str(fill.price),
                    "fee": str(fill.fee),
                    "kind": fill.kind,
                    "execution_mode": fill.execution_mode,
                    "listing_verified": fill.listing_verified,
                    "assumptions": fill.assumptions,
                },
                ts_ms=fill.ts_ms,
            )
        if step.settlement is not None:
            settlement = step.settlement

    if coord.ledger.btc_reserve_qty != reserve_before:
        print("BTC reserve quantity changed — refusing to report success", file=sys.stderr)
        return 1
    if len(fills) < 2 or coord.cycle_state.value != "FLAT" or settlement is None:
        print(
            "synthetic smoke did not complete a flat DOGE cycle "
            f"(fills={len(fills)} state={coord.cycle_state.value})",
            file=sys.stderr,
        )
        return 1

    summary = {
        "schema": "atlas_cycle_v1_smoke",
        "execution_mode": cfg.execution_mode.value,
        "live_hold": True,
        "place_orders": False,
        "paper_pass_neq_live_arm": True,
        "soft_pass_neq_arm": True,
        "not_a_forecast": True,
        "seed": cfg.seed,
        "deposit_a": str(coord.ledger.deposit_a),
        "trading_nav": str(coord.ledger.trading_nav()),
        "btc_reserve_quote": str(coord.ledger.btc_reserve_quote),
        "btc_reserve_qty": str(coord.ledger.btc_reserve_qty),
        "btc_pending_quote": str(coord.ledger.btc_pending_quote),
        "loss_carryforward": str(coord.ledger.loss_carryforward),
        "total_quote": str(coord.ledger.total_quote()),
        "cycle_pnl": str(settlement.cycle_pnl),
        "n_fills": len(fills),
        "listing_verified": False,
        "scalp_enabled": cfg.scalp_enabled,
        "live_capital_verdict": classify_live_capital(cfg),
        "candles": "synthetic_regimes",
        "warmup_4h_yaml": cfg.warmup_4h,
        "warmup_4h_smoke_override": 60,
        "not_oos_evidence": True,
        "assumptions": fills[-1].assumptions if fills else "",
        "journal_dir": str(journal.dir_for(bars_15[-1].ts_close_ms)),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    journal.write_summary(summary, ts_ms=bars_15[-1].ts_close_ms)
    print(
        f"PAPER smoke ok mode={cfg.execution_mode.value} "
        f"fills={len(fills)} live_capital={summary['live_capital_verdict']} "
        f"btc_qty={summary['btc_reserve_qty']}"
    )
    print("LIVE HOLD — geen orders. Dit resultaat is geen live-arm.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LiveExecutionRefused as exc:
        raise SystemExit(_refuse_live(str(exc))) from exc
