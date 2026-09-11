"""rise_panel_accounting_v2 re-score of UNCHANGED strategies.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. Does NOT overwrite historical artifacts.
Does NOT promote. Soft PASS ≠ arm. Live ≤€20 HALTED.

Re-scores locked families on R1–R7 with additive v2 accounting.
Strategy signals are the existing classes — no param change.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.accounting_v2 import (
    ACCOUNTING_V2_GATE,
    ACCOUNTING_V2_NOTE,
    ACCOUNTING_VERSION,
    V2_WALK_KEYS,
    accounting_v2_score,
    old_vs_v2_delta_row,
    v2_panel_summary,
)
from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR, SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    BASELINE_ID,
    CORE_BAR,
    MID_BAR_CANDIDATE,
    MID_BASELINE_ID,
    PANEL_LABEL,
    RiseWindow,
    SOFT_PROMOTE_GATE,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
)
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.strategy.core_doge_donchian40_20_1d import CoreDogeDonchian40201dV1
from atlas.strategy.core_doge_donchian40_20_ema50_200_1d import CoreDogeDonchian4020Ema502001dV1
from atlas.strategy.ema_trend import EmaTrendParams, EmaTrendV1
from atlas.strategy.mid_doge_breakout_ema1221_4h import MidDogeBreakoutEma1221V1
from atlas.strategy.mid_doge_breakout_ema1221_adx_4h import MidDogeBreakoutEma1221AdxV1
from atlas.strategy.scalp_doge_dual_thrust_1h import ScalpDogeDualThrust1hV1
from atlas.strategy.scalp_doge_dual_thrust_rvol_1h import ScalpDogeDualThrustRvol1hV1

SOURCE = "rise_panel_accounting_v2_audit"
# New artifact stem — do not clobber historical rise_panel_v1_*.json
ARTIFACT_STEM = "rise_panel_accounting_v2"

CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "id": "core_c0_ema12_30",
        "role": "core_c0_baseline",
        "candidate_id": BASELINE_ID,
        "bar": CORE_BAR,
        "pad_days": 40,
        "equity": CORE_START_EUR,
        "min_bars": 5,
        "factory": lambda: EmaTrendV1(EmaTrendParams(fast=12, slow=30)),
        "label": "ema12_30_long_flat",
        "audit_only": False,
    },
    {
        "id": "mid_71_breakout_ema1221",
        "role": "mid_primary_frozen",
        "candidate_id": MID_BASELINE_ID,
        "bar": MID_BAR_CANDIDATE,
        "pad_days": 10,
        "equity": MID_START_EUR,
        "min_bars": 12,
        "factory": lambda: MidDogeBreakoutEma1221V1(),
        "label": "breakout_v1_ema1221_long_regime_4h",
        "audit_only": False,
    },
    {
        "id": "mid_m1_adx",
        "role": "mid_robustness_comparator",
        "candidate_id": "rise_panel_v1_mid_doge_breakoutv1_ema1221_adx14_gt20_4h_eur40",
        "bar": MID_BAR_CANDIDATE,
        "pad_days": 10,
        "equity": MID_START_EUR,
        "min_bars": 12,
        "factory": lambda: MidDogeBreakoutEma1221AdxV1(),
        "label": "breakout_v1_ema1221_adx14_gt20_4h",
        "audit_only": False,
    },
    {
        "id": "scalp_83_dual_thrust",
        "role": "scalp_s0",
        "candidate_id": "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20",
        "bar": "1H",
        "pad_days": 3,
        "equity": SCALP_START_EUR,
        "min_bars": 12,
        "factory": lambda: ScalpDogeDualThrust1hV1(),
        "label": "dual_thrust_n20_k0505_long_flat",
        "audit_only": False,
    },
    {
        "id": "scalp_s1_rvol",
        "role": "scalp_provisional_dev",
        "candidate_id": "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20",
        "bar": "1H",
        "pad_days": 3,
        "equity": SCALP_START_EUR,
        "min_bars": 12,
        "factory": lambda: ScalpDogeDualThrustRvol1hV1(),
        "label": "dual_thrust_n20_k0505_rvol20_gt1_long_flat",
        "audit_only": False,
    },
    {
        "id": "core_c1_donchian40_20",
        "role": "core_c1_audit_reference",
        "candidate_id": "rise_panel_v1_core_doge_donchian40_20_1d_eur140",
        "bar": CORE_BAR,
        "pad_days": 80,
        "equity": CORE_START_EUR,
        "min_bars": 5,
        "factory": lambda: CoreDogeDonchian40201dV1(),
        "label": "donchian40_20_long_flat",
        "audit_only": True,
    },
    {
        "id": "core_c2_donchian_ema",
        "role": "core_c2_audit_reference",
        "candidate_id": "rise_panel_v1_core_doge_donchian40_20_ema50_200_1d_eur140",
        "bar": CORE_BAR,
        "pad_days": 250,
        "equity": CORE_START_EUR,
        "min_bars": 5,
        "factory": lambda: CoreDogeDonchian4020Ema502001dV1(),
        "label": "donchian40_20_ema50_200_regime_1d",
        "audit_only": True,
    },
)


def _as_cascade(w: RiseWindow) -> CascadeWindow:
    return CascadeWindow(id=w.id, start=w.start, end=w.end, set_id="rise", label=w.label)


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _row_from_walk(
    walk: dict[str, Any],
    bh: dict[str, Any],
    *,
    window: RiseWindow,
    spec: dict[str, Any],
) -> dict[str, Any]:
    row = {
        "ok": True,
        "window_id": window.id,
        "start": window.start,
        "end": window.end,
        "character": window.character,
        "asset": ASSET,
        "bar": spec["bar"],
        "arm": spec["id"],
        "role": spec["role"],
        "equity_eur": spec["equity"],
        "n_trades": int(walk.get("n_trades") or 0),
        "n_entries": int(walk.get("n_entries") or 0),
        "expectancy_after_costs_eur": walk.get("expectancy_after_costs_eur"),
        "net_return_eur": walk.get("net_return_eur"),
        "max_dd_eur": walk.get("max_dd_eur"),
        "fee_drag_eur": walk.get("fee_drag_eur"),
        "time_in_market": walk.get("time_in_market"),
        "bh_net_return_eur": bh.get("net_return_eur"),
        "bh_max_dd_eur": bh.get("max_dd_eur"),
        "start_equity_eur": walk.get("start_equity_eur"),
        "end_equity_eur": walk.get("end_equity_eur"),
        "accounting_version": ACCOUNTING_VERSION,
        "not_a_forecast": True,
        "place_orders": False,
        "audit_does_not_promote": True,
    }
    for k in V2_WALK_KEYS:
        if k in walk:
            row[k] = walk[k]
    return row


def _fail_row(window: RiseWindow, spec: dict[str, Any], error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "fail_closed": True,
        "error": error,
        "window_id": window.id,
        "arm": spec["id"],
        "n_trades": 0,
        "completed_round_trips": 0,
        "n_terminal_trips": 0,
        "expectancy_after_costs_eur": None,
        "expectancy_completed_eur": None,
        "expectancy_terminal_adjusted_eur": None,
        "net_return_eur": None,
        "terminal_liquidation_net_eur": None,
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_candidate_on_panel(
    cfg: Any,
    spec: dict[str, Any],
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
    factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    make = factory or spec["factory"]
    for w in panel_windows():
        cw = _as_cascade(w)
        try:
            bars = fetch_bars(
                cw,
                ASSET,
                spec["bar"],
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=int(spec["pad_days"]),
            )
            trade_bars = [b for b in bars if w.start_ms <= b.ts_open_ms < w.end_ms_exclusive]
            if len(trade_bars) < int(spec["min_bars"]):
                row = _fail_row(w, spec, f"insufficient {spec['bar']} bars")
                rows.append(row)
                continue
            settings = EmaBookSettings(
                equity_eur=float(spec["equity"]),
                fee_rate=fee_rate,
                slippage_bps=slip,
                leverage=1.0,
            )
            walk = walk_long_flat(
                bars,
                strategy=make(),
                settings=settings,
                trade_start_ms=w.start_ms,
                trade_end_ms=w.end_ms_exclusive,
            )
            bh = buy_and_hold(trade_bars, settings=settings)
            row = _row_from_walk(walk, bh, window=w, spec=spec)
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, spec, str(exc))
        rows.append(row)

    old_soft = soft_promote_score(rows)
    v2_gate = accounting_v2_score(rows)
    deltas = [old_vs_v2_delta_row(r) for r in rows]
    return {
        "ok": all(r.get("ok") for r in rows),
        "candidate_key": spec["id"],
        "candidate_id": spec["candidate_id"],
        "role": spec["role"],
        "audit_only": bool(spec.get("audit_only")),
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": spec["bar"],
        "strategy": spec["label"],
        "sleeve_eur": spec["equity"],
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "accounting_version": ACCOUNTING_VERSION,
        "soft_promote_v1_unchanged": old_soft,
        "soft_promote_gate": SOFT_PROMOTE_GATE,
        "accounting_v2": v2_gate,
        "accounting_v2_gate": ACCOUNTING_V2_GATE,
        "accounting_v2_note": ACCOUNTING_V2_NOTE,
        "old_summary": panel_summary_table(rows),
        "v2_summary": v2_panel_summary(rows),
        "deltas": deltas,
        "windows": justification_rows(),
        "rows": rows,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "audit_does_not_promote": True,
        "soft_pass_ne_arm": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
    }


def run_accounting_v2_audit(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
    keys: list[str] | None = None,
) -> dict[str, Any]:
    wanted = set(keys) if keys else {c["id"] for c in CANDIDATES}
    bundles: list[dict[str, Any]] = []
    for spec in CANDIDATES:
        if spec["id"] not in wanted:
            continue
        bundles.append(
            run_candidate_on_panel(
                cfg, spec, data_dir=data_dir, pause_s=pause_s, rest_base=rest_base
            )
        )
    return {
        "ok": all(b.get("ok") for b in bundles) if bundles else False,
        "accounting_version": ACCOUNTING_VERSION,
        "panel": PANEL_LABEL,
        "source": SOURCE,
        "candidates": bundles,
        "promote": False,
        "audit_does_not_promote": True,
        "place_orders": False,
        "not_a_forecast": True,
        "live_assume_eur_cap": 20.0,
        "live_halted": True,
        "config_default_yaml_untouched": True,
        "ts_ms": utc_ms(),
        "disclaimer": (
            "OLD vs V2 audit of unchanged strategies. "
            "Do not promote from this audit alone. Soft PASS ≠ arm."
        ),
    }


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_old_vs_v2_markdown(audit: dict[str, Any]) -> str:
    lines: list[str] = [
        "# 91 — rise_panel_accounting_v2 OLD vs V2 re-score",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.",
        "**Config:** `config/default.yaml` **untouched**.",
        "**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ arm. **This audit does not promote.**",
        f"**Accounting:** `{ACCOUNTING_VERSION}` (additive; historical keys preserved).",
        "**Audit:** [`90`](./90-evaluation-integrity-audit.md).",
        "",
        "Gate `rise_panel_accounting_v2` was locked **before** this re-score. "
        "It is **not** a rewrite of `soft_promote_v1`. Do not create green by changing the gate after seeing results.",
        "",
        "Numbers below are **measured** from `scripts/run_rise_panel_accounting_v2_eval.py` "
        "(OKX EEA public `history-candles`, PaperSettings 5+5 bps, next-open fills). "
        "OLD `net_return` / `n_trades` / expectancy reproduce the historical phase1 tables.",
        "",
        "---",
        "",
        "## How to read (do not promote)",
        "",
        "- A V2 **PASS** is **not** a GREEN CANDIDATE and **not** a promote.",
        "- Core C0 / C1 can flip FAIL→PASS because a forced window close turns an "
        "open hold (`n_trades=0`) into `n_terminal_trips=1` with terminal-MTM expectancy. "
        "That is **one-interval dominated**, not complete-trade edge.",
        "- Prefer `expectancy_completed_eur` + `completed_round_trips` when asking "
        "whether the strategy actually finished trades.",
        "- Δ net is almost entirely the missing terminal sell fee/slip (~few cents to ~€0.24).",
        "- Mid M1 remains the robustness comparator (more exp>0 windows historically, "
        "lower median exp / panel). Not a post-hoc swap for #71.",
        "",
        "| Candidate | OLD soft | V2 gate | OLD panel € | V2 term € | OLD exp>0 | V2 exp>0 | forced |",
        "|-----------|:--------:|:-------:|------------:|----------:|----------:|---------:|-------:|",
    ]
    for b in audit.get("candidates") or []:
        old_s = b.get("old_summary") or {}
        v2_s = b.get("v2_summary") or {}
        old_soft = b.get("soft_promote_v1_unchanged") or {}
        v2g = b.get("accounting_v2") or {}
        lines.append(
            f"| {b.get('candidate_key')} | {old_soft.get('verdict')} | {v2g.get('verdict')} | "
            f"{_fmt(old_s.get('panel_net_eur'))} | {_fmt(v2_s.get('panel_terminal_liquidation_net_eur'))} | "
            f"{old_s.get('n_exp_gt_0')} | {v2_s.get('n_exp_terminal_adj_gt_0')} | "
            f"{v2_s.get('n_forced_window_close')}/7 |"
        )
    lines.extend(
        [
        "",
        "---",
        "",
        ]
    )
    for b in audit.get("candidates") or []:
        lines.append(f"## {b.get('candidate_key')} — `{b.get('candidate_id')}`")
        lines.append("")
        lines.append(
            f"Role: **{b.get('role')}**"
            + (" · audit/reference only" if b.get("audit_only") else "")
        )
        lines.append(
            f"Bar {b.get('bar')} · sleeve €{b.get('sleeve_eur')} · strategy `{b.get('strategy')}`"
        )
        lines.append("")
        lines.append(
            "| Id | n_trades old | completed | term trips | open? | "
            "old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € |"
        )
        lines.append(
            "|----|-------------:|----------:|-----------:|:-----:|"
            "----------:|-----------:|--------:|----------:|----------------:|---------------:|"
        )
        for d in b.get("deltas") or []:
            lines.append(
                f"| {d.get('window_id')} | {d.get('n_trades_old')} | "
                f"{d.get('completed_round_trips')} | {d.get('n_terminal_trips')} | "
                f"{'yes' if d.get('open_position_at_end') else 'no'} | "
                f"{_fmt(d.get('net_return_eur_old'))} | {_fmt(d.get('terminal_liquidation_net_eur'))} | "
                f"{_fmt(d.get('delta_net_v2_minus_old_eur'))} | "
                f"{_fmt(d.get('expectancy_after_costs_eur_old'))} | "
                f"{_fmt(d.get('expectancy_completed_eur'))} | "
                f"{_fmt(d.get('expectancy_terminal_adjusted_eur'))} |"
            )
        old_s = b.get("old_summary") or {}
        v2_s = b.get("v2_summary") or {}
        old_soft = b.get("soft_promote_v1_unchanged") or {}
        v2g = b.get("accounting_v2") or {}
        lines.append("")
        lines.append("| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |")
        lines.append("|-------|-------------------------------:|--------------------------:|")
        lines.append(
            f"| panel net € | {_fmt(old_s.get('panel_net_eur'))} | "
            f"{_fmt(v2_s.get('panel_terminal_liquidation_net_eur'))} |"
        )
        lines.append(
            f"| median exp € | {_fmt(old_s.get('median_expectancy_eur'))} | "
            f"{_fmt(v2_s.get('median_expectancy_terminal_adjusted_eur'))} |"
        )
        lines.append(
            f"| median trips | {_fmt(old_s.get('median_trades'), 1)} | "
            f"{_fmt(v2_s.get('median_terminal_trips'), 1)} |"
        )
        lines.append(
            f"| exp>0 / 7 | {old_s.get('n_exp_gt_0')} | {v2_s.get('n_exp_terminal_adj_gt_0')} |"
        )
        lines.append(
            f"| gate verdict | {old_soft.get('verdict')} (`soft_promote_v1`) | "
            f"{v2g.get('verdict')} (`rise_panel_accounting_v2`) |"
        )
        lines.append("")
        lines.append(
            f"Forced window closes: **{v2_s.get('n_forced_window_close')}**/7. "
            "`audit_does_not_promote: true`."
        )
        lines.append("")
        lines.append("`not_a_forecast: true`.")
        lines.append("")
        lines.append("---")
        lines.append("")
    lines.extend(
        [
            "## Honesty / invalidation",
            "",
            "- Soft PASS ≠ arm. V2 PASS ≠ promote. This audit does **not** promote anyone.",
            "- R1–R7 remain DEV/eliminate-only. Next Mid score = unseen SHADOW only.",
            "- Do not change `rise_panel_accounting_v2` after seeing these numbers.",
            "- Historical `soft_promote_v1` artifacts are **not** rewritten.",
            "- CORE-R1 and SCALP-R2 are **not** in this table (lock only).",
            "- Core C0 V2 PASS (7/7 forced closes) and C1 V2 PASS (5/7 forced) are "
            "**not** complete-trade expectancy proofs. C2 remains FAIL on both gates.",
            "",
            "`not_a_forecast: true`. `place_orders: false`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redact_record(bundle), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys
    from pathlib import Path as _Path

    from atlas.common.config import load_config
    from atlas.common.logging import setup_logging
    from atlas.paper.md import OKX_REST

    _root = _Path(__file__).resolve().parents[3]
    p = argparse.ArgumentParser(
        description="Re-score UNCHANGED R1–R7 candidates under rise_panel_accounting_v2"
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--keys",
        default=None,
        help="comma-separated candidate keys (default: all seven)",
    )
    p.add_argument(
        "--write-md",
        default="phase1/91-rise-panel-accounting-v2.md",
    )
    p.add_argument(
        "--out-dir",
        default="results/accounting_v2",
        help="new artifacts only — does not overwrite historical rise_panel_v1_*.json",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = _Path(args.data_dir) if args.data_dir else _Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _root / data_dir
    setup_logging(cfg.log_level)
    keys = [k.strip() for k in args.keys.split(",") if k.strip()] if args.keys else None
    rest = (getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip("/")
    audit = run_accounting_v2_audit(
        cfg, data_dir=data_dir, pause_s=args.pause_s, rest_base=rest, keys=keys
    )
    out_dir = _Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = _root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    wrote = write_report_json(audit, out_dir / "rise_panel_accounting_v2_audit.json")
    for b in audit.get("candidates") or []:
        write_report_json(
            b, out_dir / f"rise_panel_accounting_v2_{b.get('candidate_key')}.json"
        )
    print(
        json.dumps(
            {
                "wrote": str(wrote),
                "ok": audit.get("ok"),
                "n_candidates": len(audit.get("candidates") or []),
                "audit_does_not_promote": True,
                "place_orders": False,
                "not_a_forecast": True,
            },
            indent=2,
        )
    )
    if args.write_md:
        md_path = _Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _root / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_old_vs_v2_markdown(audit), encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path)}, indent=2))
    return 0 if audit.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

