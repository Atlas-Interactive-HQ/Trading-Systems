"""Loss attribution + one bull-gate counterfactual. Research only.

Reuses PaperEngine fills (fee+slip). No second ledger. No orders.
not_a_forecast: true. Do not retune lookback/stops. Do not headline PnL.

Bull gate (single, no grid): 1h SMA(20) rising vs prior SMA(20).
Allow = long AND bull. Fail-closed (missing 1h) = block.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from atlas.collectors.base import new_run_id
from atlas.oms.spot_demo import redact_record
from atlas.paper.engine import PaperEngine, PaperSettings, PaperSummary, strategy_from_app_config
from atlas.paper.eval import (
    SPLIT_FRAC,
    NullJournal,
    load_named_bars,
    load_similar_bars,
)
from atlas.paper.md import bars_1h_at_or_before
from atlas.paper.named_windows import NAMED_WINDOWS, expand_window_ids
from atlas.paper.replay import ReplayError
from atlas.paper.shadow import shadow_settings
from atlas.paper.types import Bar, Fill, Position, Side, q

ATTR_SOURCE = "loss-attribution"
BULL_GATE_ID = "bull_1h_sma20_rising"
BULL_GATE_N = 20
BULL_GATE_LABEL = (
    "1h SMA(20) of closes strictly greater than SMA(20) on the prior 1h bar "
    "(rising MA). Fail-closed if fewer than 21 closed 1h bars."
)

# Map engine exit reasons → driver buckets.
_REASON_BUCKET = {
    "stop": "stop_out",
    "time_stop": "time_stop",
    "daily_kill": "kill_flatten",
}


def bull_regime_1h(
    bars_1h: Sequence[Bar] | None, *, n: int = BULL_GATE_N
) -> tuple[bool | None, str]:
    """True if 1h SMA(n) is rising. None = fail-closed (do not invent a regime)."""
    if n < 2:
        return None, "fail_closed_bad_n"
    if not bars_1h or len(bars_1h) < n + 1:
        return None, "fail_closed_missing_1h"
    window = list(bars_1h[-(n + 1) :])
    if any(not b.closed for b in window):
        return None, "fail_closed_open_1h"
    closes = [float(b.close) for b in bars_1h]
    now = sum(closes[-n:]) / float(n)
    prev = sum(closes[-n - 1 : -1]) / float(n)
    if now > prev:
        return True, "1h_sma20_rising"
    return False, "1h_sma20_not_rising"


def gate_allows(side: str, bull: bool | None) -> tuple[bool, str]:
    """Bull-capable participation: long only when 1h SMA20 is rising."""
    if bull is None:
        return False, "fail_closed"
    if side == "long" and bull:
        return True, "allow_long_in_bull"
    if side == "long":
        return False, "block_long_not_bull"
    if bull:
        return False, "block_short_in_bull"
    return False, "block_short_not_bull"


def _bucket(reason: str) -> str:
    return _REASON_BUCKET.get(reason, "other_exit")


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / n)


@dataclass
class ClosedTrade:
    symbol: str
    side: str
    entry_ts_ms: int
    exit_ts_ms: int
    entry_bar_i: int
    exit_bar_i: int
    entry_px: float
    exit_px: float
    qty: float
    entry_fee: float
    exit_fee: float
    fee_eur: float
    price_pnl_eur: float
    net_pnl_eur: float
    exit_reason: str
    driver: str
    bars_held: int
    first_bar_mark_pnl_eur: float | None
    adverse_first_bar: bool
    mae_eur: float | None
    mfe_eur: float | None
    bull: bool | None
    bull_reason: str
    gate_allow: bool
    gate_tag: str
    in_holdout: bool = False
    not_a_forecast: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _OpenSnap:
    symbol: str
    side: Side
    qty: float
    entry_px: float
    entry_fee: float
    entry_ts_ms: int
    entry_bar_i: int
    entry_bar: Bar
    bull: bool | None
    bull_reason: str


class AttributionEngine(PaperEngine):
    """Same sequencing as PaperEngine; records closed trades + bull-gate flags."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.trades: list[ClosedTrade] = []
        self._open: _OpenSnap | None = None
        self._bars_by_symbol: dict[str, list[Bar]] = {}
        self._bars_1h: dict[str, list[Bar]] = {}

    def run(
        self,
        bars_by_symbol: Mapping[str, Sequence[Bar]],
        bars_1h_by_symbol: Mapping[str, Sequence[Bar]] | None = None,
        universe: Sequence[str] | None = None,
    ) -> PaperSummary:
        self.trades = []
        self._open = None
        self._bars_by_symbol = {s: list(v) for s, v in bars_by_symbol.items()}
        self._bars_1h = {s: list(v) for s, v in (bars_1h_by_symbol or {}).items()}
        return super().run(bars_by_symbol, bars_1h_by_symbol, universe)

    def _execute_pending(self, ledger: Any, bar: Bar, *, bar_i: int) -> None:
        order = self._pending
        n_before = self._entries
        super()._execute_pending(ledger, bar, bar_i=bar_i)
        if order is None or order.kind != "entry":
            return
        if self._entries <= n_before or ledger.position is None:
            return
        pos: Position = ledger.position
        h1 = bars_1h_at_or_before(list(self._bars_1h.get(pos.symbol) or []), bar.ts_open_ms)
        bull, why = bull_regime_1h(h1)
        self._open = _OpenSnap(
            symbol=pos.symbol,
            side=pos.side,
            qty=pos.qty,
            entry_px=pos.entry,
            entry_fee=pos.entry_fee,
            entry_ts_ms=pos.opened_ts_ms,
            entry_bar_i=bar_i,
            entry_bar=bar,
            bull=bull,
            bull_reason=why,
        )

    def _exit(
        self,
        ledger: Any,
        bar: Bar,
        *,
        ref_price: float,
        ts_ms: int,
        reason: str,
        bar_i: int,
    ) -> None:
        pos = ledger.position
        snap = self._open
        super()._exit(ledger, bar, ref_price=ref_price, ts_ms=ts_ms, reason=reason, bar_i=bar_i)
        if pos is None or snap is None:
            self._open = None
            return
        exit_fill: Fill | None = self._fills[-1] if self._fills else None
        if exit_fill is None or exit_fill.kind != "exit":
            self._open = None
            return
        fee = q(float(snap.entry_fee) + float(exit_fill.fee))
        price = float(exit_fill.pnl)
        net = q(price - fee)
        first = _first_bar_mark_pnl(snap, pos.side)
        mae, mfe = _mae_mfe(
            pos.side,
            snap.entry_px,
            snap.qty,
            self._bars_by_symbol.get(snap.symbol) or [],
            snap.entry_bar.ts_open_ms,
            bar.ts_open_ms,
        )
        allow, tag = gate_allows(pos.side.value, snap.bull)
        self.trades.append(
            ClosedTrade(
                symbol=snap.symbol,
                side=pos.side.value,
                entry_ts_ms=snap.entry_ts_ms,
                exit_ts_ms=exit_fill.ts_ms,
                entry_bar_i=snap.entry_bar_i,
                exit_bar_i=bar_i,
                entry_px=snap.entry_px,
                exit_px=exit_fill.price,
                qty=snap.qty,
                entry_fee=q(snap.entry_fee),
                exit_fee=q(exit_fill.fee),
                fee_eur=fee,
                price_pnl_eur=q(price),
                net_pnl_eur=net,
                exit_reason=reason,
                driver=_bucket(reason),
                bars_held=max(0, bar_i - snap.entry_bar_i),
                first_bar_mark_pnl_eur=first,
                adverse_first_bar=bool(first is not None and first < 0),
                mae_eur=mae,
                mfe_eur=mfe,
                bull=snap.bull,
                bull_reason=snap.bull_reason,
                gate_allow=allow,
                gate_tag=tag,
            )
        )
        self._open = None


def _first_bar_mark_pnl(snap: _OpenSnap, side: Side) -> float | None:
    close = float(snap.entry_bar.close)
    if side is Side.LONG:
        return q(snap.qty * (close - snap.entry_px))
    return q(snap.qty * (snap.entry_px - close))


def _mae_mfe(
    side: Side,
    entry_px: float,
    qty: float,
    bars: Sequence[Bar],
    entry_open_ms: int,
    exit_open_ms: int,
) -> tuple[float | None, float | None]:
    held = [b for b in bars if entry_open_ms <= b.ts_open_ms <= exit_open_ms]
    if not held:
        return None, None
    if side is Side.LONG:
        mae = q(qty * (entry_px - min(b.low for b in held)))
        mfe = q(qty * (max(b.high for b in held) - entry_px))
    else:
        mae = q(qty * (max(b.high for b in held) - entry_px))
        mfe = q(qty * (entry_px - min(b.low for b in held)))
    return mae, mfe


def _group_stats(trades: Sequence[ClosedTrade], *, label: str) -> dict[str, Any]:
    n = len(trades)
    net = q(sum(t.net_pnl_eur for t in trades))
    price = q(sum(t.price_pnl_eur for t in trades))
    fees = q(sum(t.fee_eur for t in trades))
    wins = sum(1 for t in trades if t.net_pnl_eur > 0)
    return {
        "label": label,
        "n_trades": n,
        "n_long": sum(1 for t in trades if t.side == "long"),
        "n_short": sum(1 for t in trades if t.side == "short"),
        "price_pnl_eur": price,
        "fee_drag_eur": fees,
        "net_pnl_eur": net,
        "expectancy_after_costs_eur": _expectancy(net, n),
        "win_rate": q(wins / n) if n else None,
        "not_a_forecast": True,
    }


def _driver_rows(trades: Sequence[ClosedTrade]) -> list[dict[str, Any]]:
    order = ("stop_out", "time_stop", "kill_flatten", "other_exit", "fee_drag", "adverse_first_bar")
    by: dict[str, list[ClosedTrade]] = {k: [] for k in order}
    for t in trades:
        by[t.driver].append(t)
        if t.adverse_first_bar:
            by["adverse_first_bar"].append(t)
    rows: list[dict[str, Any]] = []
    for key in order:
        chunk = by[key]
        if key == "fee_drag":
            n = len(trades)
            contrib = q(-sum(t.fee_eur for t in trades))
            rows.append(
                {
                    "driver": key,
                    "n": n,
                    "price_pnl_eur": None,
                    "eur_contribution": contrib,
                    "note": "sum of entry+exit taker fees (sign flipped as PnL drag)",
                    "overlaps": True,
                }
            )
            continue
        if key == "adverse_first_bar":
            adv = [t.first_bar_mark_pnl_eur or 0.0 for t in chunk]
            contrib = q(sum(x for x in adv if x < 0))
            rows.append(
                {
                    "driver": key,
                    "n": len(chunk),
                    "price_pnl_eur": q(sum(adv)),
                    "eur_contribution": contrib,
                    "note": "first 15m bar after entry fill; diagnostic, overlaps exits",
                    "overlaps": True,
                }
            )
            continue
        price = q(sum(t.price_pnl_eur for t in chunk))
        net = q(sum(t.net_pnl_eur for t in chunk))
        rows.append(
            {
                "driver": key,
                "n": len(chunk),
                "price_pnl_eur": price,
                "eur_contribution": net,
                "note": "after-cost net of trades with this exit reason",
                "overlaps": False,
            }
        )
    return rows


def _top_loss_drivers(rows: Sequence[dict[str, Any]], *, k: int = 3) -> list[dict[str, Any]]:
    ranked = sorted(
        (r for r in rows if r.get("driver") != "adverse_first_bar"),
        key=lambda r: float(r.get("eur_contribution") or 0.0),
    )
    loss = [r for r in ranked if float(r.get("eur_contribution") or 0.0) < 0]
    return loss[:k]


def tag_holdout(trades: list[ClosedTrade], bars_by_symbol: Mapping[str, Sequence[Bar]]) -> int:
    """Tag trades whose entry is in the last 30% of the primary 15m clock. Returns cut_ts."""
    if not bars_by_symbol:
        return 0
    primary = max(bars_by_symbol.items(), key=lambda kv: len(kv[1]))[1]
    n = len(primary)
    cut = int(n * SPLIT_FRAC)
    cut_ts = primary[cut - 1].ts_close_ms if cut > 0 else 0
    for t in trades:
        t.in_holdout = t.entry_ts_ms > cut_ts
    return cut_ts


def attribute_bars(
    *,
    sample_id: str,
    bars_by_symbol: dict[str, list[Bar]],
    bars_1h_by_symbol: dict[str, list[Bar]],
    settings: PaperSettings,
    strategy: Any,
    md_label: str = "",
) -> dict[str, Any]:
    if not bars_by_symbol or not any(bars_by_symbol.values()):
        return {
            "ok": False,
            "sample_id": sample_id,
            "error": "empty bars",
            "place_orders": False,
            "not_a_forecast": True,
        }
    eng = AttributionEngine(
        settings,
        strategy,
        journal=NullJournal(),
        run_id=new_run_id(f"attr-{sample_id}"),
        data_dir="data",
    )
    paper = eng.run(bars_by_symbol, bars_1h_by_symbol, universe=list(bars_by_symbol.keys()))
    tag_holdout(eng.trades, bars_by_symbol)
    trades = eng.trades
    full = _group_stats(trades, label="full")
    hold = _group_stats([t for t in trades if t.in_holdout], label="holdout_30")
    ins = _group_stats([t for t in trades if not t.in_holdout], label="in_sample_70")
    allow = [t for t in trades if t.gate_allow]
    block = [t for t in trades if not t.gate_allow]
    allow_h = [t for t in allow if t.in_holdout]
    block_h = [t for t in block if t.in_holdout]
    drivers = _driver_rows(trades)
    cells = {
        "long_bull": _group_stats(
            [t for t in trades if t.side == "long" and t.bull is True], label="long_bull"
        ),
        "long_not_bull": _group_stats(
            [t for t in trades if t.side == "long" and t.bull is False], label="long_not_bull"
        ),
        "short_bull": _group_stats(
            [t for t in trades if t.side == "short" and t.bull is True], label="short_bull"
        ),
        "short_not_bull": _group_stats(
            [t for t in trades if t.side == "short" and t.bull is False], label="short_not_bull"
        ),
        "fail_closed": _group_stats(
            [t for t in trades if t.bull is None], label="fail_closed"
        ),
    }
    n_primary = len(next(iter(bars_by_symbol.values())))
    return {
        "ok": True,
        "place_orders": False,
        "source": ATTR_SOURCE,
        "sample_id": sample_id,
        "md_label": md_label,
        "not_a_forecast": True,
        "bull_gate": {
            "id": BULL_GATE_ID,
            "n": BULL_GATE_N,
            "label": BULL_GATE_LABEL,
            "allow_rule": "long AND 1h SMA20 rising; fail-closed blocks",
        },
        "split": {
            "frac_in_sample": SPLIT_FRAC,
            "n_bars_full": n_primary,
            "n_bars_in_sample": int(n_primary * SPLIT_FRAC),
            "n_bars_holdout": max(0, n_primary - int(n_primary * SPLIT_FRAC)),
            "rule": "first 70% of 15m bars by time; trades tagged by entry ts; cut never searched",
        },
        "engine": {
            "n_trades": paper.n_trades,
            "n_entries": paper.n_entries,
            "n_stops": paper.n_stops,
            "n_kills": paper.n_kills,
            "fees_paid_eur": paper.fees_paid,
            "realized_price_pnl_eur": paper.realized_pnl,
            "end_equity_eur": paper.end_equity,
        },
        "full": full,
        "in_sample": ins,
        "holdout": hold,
        "drivers": drivers,
        "top_loss_drivers": _top_loss_drivers(drivers),
        "bull_gate_counterfactual": {
            "allow": _group_stats(allow, label="gate_allow"),
            "block": _group_stats(block, label="gate_block"),
            "allow_holdout": _group_stats(allow_h, label="gate_allow_holdout"),
            "block_holdout": _group_stats(block_h, label="gate_block_holdout"),
            "cells": cells,
            "note": (
                "same journal path: gate does not re-sequence one-position/kill. "
                "allow vs block is a subset of baseline fills."
            ),
        },
        "disclaimer": (
            "research only. not_a_forecast. named-window / similar-regime / Q4 ≠ future. "
            "do not headline PnL. do not promote to Phase C or live. "
            "do not retune lookback/stops from this file."
        ),
    }


def run_loss_attribution(
    cfg: Any,
    *,
    samples: list[str],
    data_dir: str | Path = "data",
    pause_s: float = 0.12,
    client: Any | None = None,
    bars_by_sample: dict[str, tuple[dict[str, list[Bar]], dict[str, list[Bar]], dict[str, str], str]]
    | None = None,
) -> dict[str, Any]:
    settings = shadow_settings(cfg)
    strategy = strategy_from_app_config(cfg)
    root = Path(data_dir)
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    samples = expand_window_ids(list(samples))
    for sid in samples:
        key = sid.strip()
        try:
            if bars_by_sample and key in bars_by_sample:
                b15, b1h, _vmap, label = bars_by_sample[key]
            elif key in ("similar", "similar-regime"):
                b15, b1h, _vmap, label = load_similar_bars(
                    cfg, root, client=client, pause_s=pause_s
                )
            elif key in NAMED_WINDOWS:
                b15, b1h, _vmap, label = load_named_bars(
                    cfg, root, key, client=client, pause_s=pause_s
                )
            else:
                raise ReplayError(f"unknown sample {key!r}")
            row = attribute_bars(
                sample_id=key,
                bars_by_symbol=b15,
                bars_1h_by_symbol=b1h,
                settings=settings,
                strategy=strategy,
                md_label=label,
            )
        except ReplayError as exc:
            errors.append(f"{key}:{exc}")
            row = {
                "ok": False,
                "sample_id": key,
                "place_orders": False,
                "error": str(exc),
                "not_a_forecast": True,
            }
        results.append(row)
        out = reports_dir / f"attr_{key}.json"
        payload = dict(row)
        payload.pop("trades", None)
        out.write_text(
            json.dumps(redact_record(payload), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
    bundle = {
        "ok": any(r.get("ok") for r in results),
        "place_orders": False,
        "source": ATTR_SOURCE,
        "not_a_forecast": True,
        "bull_gate": {"id": BULL_GATE_ID, "n": BULL_GATE_N, "label": BULL_GATE_LABEL},
        "samples": results,
        "errors": errors,
        "disclaimer": (
            "research only. expectancy after costs is not a forecast and not a Phase C/live gate. "
            "hand bull-gate to candidate_v2 only if holdout numbers support it."
        ),
    }
    (reports_dir / "attr_bundle.json").write_text(
        json.dumps(redact_record(bundle), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return bundle


def _fmt_exp(v: Any) -> str:
    if v is None:
        return "—"
    return f"{float(v):.4f}"


def _fmt_eur(v: Any) -> str:
    if v is None:
        return "—"
    return f"{float(v):.4f}"


def render_attribution_markdown(bundle: dict[str, Any]) -> str:
    lines = [
        "# 15 — Loss attribution + bull-gate counterfactual",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live. Not a candidate_v1 implementation (Claude owns that lane).",
        "",
        "Primary score remains **expectancy after costs** = (price PnL − entry/exit fees) / n_trades. Existing eval reports price PnL / n as “expectancy after costs” and fee drag as a separate line; this file uses the net figure and keeps fee drag as its own driver.",
        "",
        f"**Bull gate (one, no grid):** `{BULL_GATE_ID}`. {BULL_GATE_LABEL} Allow = long AND rising 1h SMA20. Fail-closed blocks. Counterfactual is on the **same journal path** (no re-sequence of one-position / kill).",
        "",
        "Named-window / similar-regime / Q4 ≠ future performance. BreakoutV1 lookback/stops were not retuned.",
        "",
    ]
    # Compact cross-sample
    lines.append("## Cross-sample (full window)")
    lines.append("")
    lines.append(
        "| Sample | n | expectancy after costs | fee drag (€) | stop n / € | time-stop n / € | kill-flatten n / € | gate allow n / exp | gate block n / exp |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for sample in bundle.get("samples") or []:
        sid = sample.get("sample_id")
        if not sample.get("ok"):
            lines.append(f"| {sid} | — | skipped | — | — | — | — | — | — |")
            continue
        full = sample.get("full") or {}
        dmap = {r["driver"]: r for r in (sample.get("drivers") or [])}
        gate = sample.get("bull_gate_counterfactual") or {}
        allow = gate.get("allow") or {}
        block = gate.get("block") or {}

        def _drv(key: str) -> str:
            r = dmap.get(key) or {}
            return f"{r.get('n', 0)} / {_fmt_eur(r.get('eur_contribution'))}"

        lines.append(
            f"| {sid} | {full.get('n_trades')} | {_fmt_exp(full.get('expectancy_after_costs_eur'))} | "
            f"{_fmt_eur(full.get('fee_drag_eur'))} | {_drv('stop_out')} | {_drv('time_stop')} | "
            f"{_drv('kill_flatten')} | {allow.get('n_trades')} / {_fmt_exp(allow.get('expectancy_after_costs_eur'))} | "
            f"{block.get('n_trades')} / {_fmt_exp(block.get('expectancy_after_costs_eur'))} |"
        )
    lines.append("")
    lines.append("`not_a_forecast: true`.")
    lines.append("")

    for sample in bundle.get("samples") or []:
        sid = sample.get("sample_id")
        lines.append(f"## {sid}")
        lines.append("")
        if not sample.get("ok"):
            lines.append(f"Skipped: `{sample.get('error')}`. No fake fills.")
            lines.append("")
            continue
        lines.append(f"MD: {sample.get('md_label')}")
        split = sample.get("split") or {}
        lines.append(
            f"Bars: full {split.get('n_bars_full')} · IS {split.get('n_bars_in_sample')} · holdout {split.get('n_bars_holdout')}."
        )
        lines.append("")
        lines.append("### What hurts (drivers)")
        lines.append("")
        lines.append("| Driver | n | price PnL (€) | € contribution | overlaps |")
        lines.append("|---|---:|---:|---:|---|")
        for r in sample.get("drivers") or []:
            lines.append(
                f"| {r.get('driver')} | {r.get('n')} | {_fmt_eur(r.get('price_pnl_eur'))} | "
                f"{_fmt_eur(r.get('eur_contribution'))} | {'yes' if r.get('overlaps') else 'no'} |"
            )
        top = sample.get("top_loss_drivers") or []
        if top:
            names = ", ".join(
                f"{r.get('driver')} ({_fmt_eur(r.get('eur_contribution'))})" for r in top
            )
            lines.append("")
            lines.append(f"Top loss drivers (most negative €, fee_drag included, adverse-first-bar excluded from rank): {names}.")
        lines.append("")
        lines.append("### Slices")
        lines.append("")
        lines.append("| Slice | n | n_long | n_short | expectancy after costs | fee drag (€) | net PnL (€) |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for key, title in (("full", "full"), ("in_sample", "in-sample 70%"), ("holdout", "holdout 30%")):
            m = sample.get(key) or {}
            lines.append(
                f"| {title} | {m.get('n_trades')} | {m.get('n_long')} | {m.get('n_short')} | "
                f"{_fmt_exp(m.get('expectancy_after_costs_eur'))} | {_fmt_eur(m.get('fee_drag_eur'))} | "
                f"{_fmt_eur(m.get('net_pnl_eur'))} |"
            )
        lines.append("")
        lines.append("### Bull-gate counterfactual (same fills)")
        lines.append("")
        lines.append("| Bucket | n | n_long | n_short | expectancy after costs | fee drag (€) |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        gate = sample.get("bull_gate_counterfactual") or {}
        for key, title in (
            ("allow", "allow (long ∩ bull)"),
            ("block", "block"),
            ("allow_holdout", "allow holdout"),
            ("block_holdout", "block holdout"),
        ):
            m = gate.get(key) or {}
            lines.append(
                f"| {title} | {m.get('n_trades')} | {m.get('n_long')} | {m.get('n_short')} | "
                f"{_fmt_exp(m.get('expectancy_after_costs_eur'))} | {_fmt_eur(m.get('fee_drag_eur'))} |"
            )
        lines.append("")
        lines.append("Side × regime cells (diagnostic, not a second gate):")
        lines.append("")
        lines.append("| Cell | n | expectancy after costs |")
        lines.append("|---|---:|---:|")
        cells = gate.get("cells") or {}
        for key in ("long_bull", "long_not_bull", "short_bull", "short_not_bull", "fail_closed"):
            m = cells.get(key) or {}
            lines.append(
                f"| {key} | {m.get('n_trades')} | {_fmt_exp(m.get('expectancy_after_costs_eur'))} |"
            )
        lines.append("")
        lines.append("`not_a_forecast: true`.")
        lines.append("")

    lines.extend(
        [
            "## What NOT to do next",
            "",
            "- Do not treat allow-bucket expectancy as a live edge or a Phase C gate.",
            "- Do not retune Donchian lookback, ATR stop, or time-stop to chase these numbers.",
            "- Do not grid-search N on the 1h SMA in this lane.",
            "- Do not silently rewrite the 2020-09 / 2023-09 holdout pass rule.",
            "- Hand this bull gate to Atlas/Claude for **candidate_v2 only if** holdout allow expectancy is better than baseline holdout **and** n_trades is not a handful. Otherwise keep it as a documented hypothesis.",
            "- Claude’s `candidate_v1_filters` (daily_cap / min_atr_frac) is a separate implementation lane — do not merge this gate into that PR from here.",
            "",
            "## What this is not",
            "",
            "- Not a Phase C recommendation.",
            "- Not a live-trading recommendation.",
            "- Not a claim that the locked breakout has edge in bull markets.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"
