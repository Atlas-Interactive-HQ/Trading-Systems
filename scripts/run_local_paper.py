#!/usr/bin/env python3
"""CLI: Phase-1.5 local paper engine. Public candles or local JSONL. No live orders."""

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

from atlas.common.config import load_config  # noqa: E402
from atlas.common.logging import setup_logging  # noqa: E402
from atlas.paper.engine import PaperEngine, PaperSettings, strategy_from_app_config  # noqa: E402
from atlas.paper.md import (  # noqa: E402
    PaperDataError,
    USER_AGENT,
    load_symbol_bars,
    resample_1h,
)
from atlas.strategy.breakout import BreakoutParams, BreakoutV1  # noqa: E402


def _universe(cfg, symbols_arg: str | None) -> list[str]:
    if symbols_arg:
        return [s.strip() for s in symbols_arg.split(",") if s.strip()]
    return list(cfg.paper.primary_symbols) + list(cfg.paper.backup_symbols)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Local paper trading on public 15m candles (no exchange orders)"
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--bars", type=int, default=96, help="Closed 15m bars to process (most recent)")
    p.add_argument("--duration-hours", type=float, default=None, help="Overrides --bars (hours * 4)")
    p.add_argument("--symbols", default=None, help="Comma list, default paper universe")
    p.add_argument(
        "--source",
        default=None,
        help="auto | okx_eea | kraken | jsonl (default: config paper.candle_source)",
    )
    p.add_argument("--jsonl", default=None, help="Single JSONL file (applies to first symbol)")
    p.add_argument("--offline", action="store_true", help="JSONL only; fail if missing")
    p.add_argument("--oneh-filter", default=None, choices=["stub", "off"])
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    if args.data_dir:
        cfg.data_dir = args.data_dir
    setup_logging(cfg.log_level)

    n_bars = args.bars
    if args.duration_hours is not None:
        n_bars = int(args.duration_hours * 4)
    if n_bars <= 0:
        print("fail closed: --bars / duration must be positive", file=sys.stderr)
        return 2

    source = (args.source or cfg.paper.candle_source or "auto").lower()
    if args.offline:
        source = "jsonl"
    symbols = _universe(cfg, args.symbols)
    if not symbols:
        print("fail closed: empty universe", file=sys.stderr)
        return 2

    data_dir = Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir

    warmup = max(cfg.strategy.breakout.lookback_15m, cfg.strategy.breakout.atr_period) + 2
    fetch_n = min(300, n_bars + warmup + 48)
    bar = cfg.paper.bar
    regime_bar = cfg.paper.regime_bar

    client: httpx.Client | None = None
    if source != "jsonl":
        client = httpx.Client(headers={"User-Agent": USER_AGENT})

    bars_15: dict[str, list] = {}
    bars_1h: dict[str, list] = {}
    errors: list[str] = []
    try:
        for i, symbol in enumerate(symbols):
            jsonl_path = Path(args.jsonl) if args.jsonl and i == 0 else None
            try:
                rows = load_symbol_bars(
                    symbol=symbol,
                    bar=bar,
                    source=source,
                    data_dir=data_dir,
                    client=client,
                    rest_base=cfg.venues.get("okx_eea").rest_base
                    if cfg.venues.get("okx_eea")
                    else "https://eea.okx.com",
                    limit=fetch_n,
                    jsonl_path=jsonl_path,
                )
            except PaperDataError as exc:
                errors.append(f"{symbol}: {exc}")
                continue
            if len(rows) < n_bars:
                # Use whatever we have if it covers warmup+some; else fail this symbol.
                if len(rows) <= warmup:
                    errors.append(f"{symbol}: only {len(rows)} bars (need > {warmup})")
                    continue
            else:
                rows = rows[-n_bars:]
            bars_15[symbol] = rows
            try:
                h1 = load_symbol_bars(
                    symbol=symbol,
                    bar=regime_bar,
                    source=source,
                    data_dir=data_dir,
                    client=client,
                    rest_base=cfg.venues.get("okx_eea").rest_base
                    if cfg.venues.get("okx_eea")
                    else "https://eea.okx.com",
                    limit=min(300, max(50, n_bars // 4 + cfg.strategy.breakout.oneh_lookback + 5)),
                )
            except PaperDataError:
                h1 = resample_1h(rows)
            if not h1:
                h1 = resample_1h(rows)
            bars_1h[symbol] = h1
    finally:
        if client is not None:
            client.close()

    if not bars_15:
        print("fail closed: no usable candles. " + " | ".join(errors), file=sys.stderr)
        return 2

    # Drop symbols that failed; keep universe order.
    universe = [s for s in symbols if s in bars_15]
    # Clock from first remaining symbol — others optional per bar.
    settings = PaperSettings.from_app_config(cfg)
    strat = strategy_from_app_config(cfg)
    if args.oneh_filter:
        bp = strat.params
        strat = BreakoutV1(
            BreakoutParams(
                lookback_15m=bp.lookback_15m,
                atr_period=bp.atr_period,
                atr_stop_mult=bp.atr_stop_mult,
                min_atr_frac=bp.min_atr_frac,
                oneh_filter=args.oneh_filter,
                oneh_lookback=bp.oneh_lookback,
                ranging=bp.ranging,
                confirm_closed_only=bp.confirm_closed_only,
            )
        )

    engine = PaperEngine(
        settings,
        strat,
        data_dir=str(data_dir),
    )
    summary = engine.run(bars_15, bars_1h, universe=universe)
    payload = summary.as_dict()
    payload["source"] = source
    payload["errors"] = errors
    payload["n_symbols_loaded"] = len(universe)
    print(json.dumps(payload, indent=2, default=str))
    print(
        f"\nPnL {payload['pnl']} EUR ({payload['pnl_pct']}%) | "
        f"trades={payload['n_trades']} entries={payload['n_entries']} "
        f"stops={payload['n_stops']} kills={payload['n_kills']} "
        f"rejects={payload['n_rejects']} | logs {payload['log_dir']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
