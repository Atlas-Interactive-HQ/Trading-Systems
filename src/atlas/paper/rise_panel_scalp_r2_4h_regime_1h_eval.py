"""rise_panel_v1 SCALP-R2 first score — Dual Thrust + RVOL + 4H EMA12/21 vs S1.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Uses locked rise_panel_accounting_v2. Walker: walk_long_short (NOT walk_long_flat).
R1–R7 = DEV/eliminate-only. Soft PASS ≠ Scalp-arm. Live ≤€20 HALTED.
No RVOL 1.25/1.5 grind. Lock: phase1/93. Doc: phase1/99.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

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
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.ls_eval import walk_long_short
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    PANEL_LABEL,
    SCALP_R2_HYPOTHESIS_ID,
    RiseWindow,
    SOFT_PROMOTE_GATE,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
)
from atlas.paper.rise_panel_accounting_v2_eval import CANDIDATES, run_candidate_on_panel
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import q
from atlas.strategy.scalp_doge_dual_thrust_rvol_4h_regime_1h import (
    BAR,
    DT_N,
    FAMILY,
    K1,
    K2,
    LADDER_ID,
    REGIME_BAR,
    REGIME_FAST,
    REGIME_SLOW,
    RVOL_MIN,
    RVOL_N,
    SLEEVE,
    ScalpDogeDualThrustRvol4hRegime1hV1,
)

SOURCE = "rise_panel_v1_scalp_r2_4h_regime_99"
LOCK_NOTE = "phase1/93-frozen-mid-scalp-candidates.md"
DOC_NOTE = "phase1/99-rise-panel-scalp-r2-dt-4h-regime-1h.md"

SCALP_R2_ID = SCALP_R2_HYPOTHESIS_ID
SCALP_S1_ID = "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
SCALP_S0_ID = "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20"
SCALP_R2_KEY = "scalp_r2_dt_4h_regime"
SCALP_S1_KEY = "scalp_s1_rvol"

# 4H EMA21 needs ≥21 closed 4H bars; pad10 matches Mid caches.
PAD_DAYS_1H = 3  # DT N20 + RVOL20; 4H regime uses its own pad
PAD_DAYS_4H = 10
MIN_1H_BARS = 12
MIN_4H_BARS = 21
WARMUP_NOTE = "1H Dual Thrust N20 + RVOL20; 4H EMA12/21 regime (pad10 both)"


def _s1_spec() -> dict[str, Any]:
    for spec in CANDIDATES:
        if spec["id"] == SCALP_S1_KEY:
            return spec
    raise RuntimeError("scalp_s1_rvol missing from accounting_v2 CANDIDATES")


def _as_cascade(w: RiseWindow) -> CascadeWindow:
    return CascadeWindow(id=w.id, start=w.start, end=w.end, set_id="rise", label=w.label)


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _median(values: list[float | int]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def completed_panel_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [int(r.get("completed_round_trips") or r.get("n_trades") or 0) for r in rows]
    exps: list[float] = []
    for r in rows:
        e = r.get("expectancy_completed_eur")
        if e is not None:
            exps.append(float(e))
    n_exp_pos = sum(1 for e in exps if e > 0)
    realized = [float(r.get("realized_net_eur") or 0.0) for r in rows]
    dds = [float(r["max_dd_eur"]) for r in rows if r.get("max_dd_eur") is not None]
    tims = [float(r["time_in_market"]) for r in rows if r.get("time_in_market") is not None]
    entries = [int(r.get("n_entries") or 0) for r in rows]
    long_e = []
    short_e = []
    for r in rows:
        if "n_long_entries" in r or "n_short_entries" in r:
            long_e.append(int(r.get("n_long_entries") or 0))
            short_e.append(int(r.get("n_short_entries") or 0))
        else:
            # long-only walker (S1): all entries are long
            long_e.append(int(r.get("n_entries") or 0))
            short_e.append(0)
    forced = sum(
        1 for r in rows if r.get("forced_window_close") or r.get("open_position_at_end")
    )
    return {
        "n_windows": len(rows),
        "completed_round_trips_per_window": completed,
        "median_completed_round_trips": _median(completed),
        "n_expectancy_completed_gt_0": n_exp_pos,
        "median_expectancy_completed_eur": None if not exps else q(_median(exps)),
        "panel_realized_net_eur": q(sum(realized)),
        "worst_dd_eur": None if not dds else q(max(dds)),
        "median_time_in_market": None if not tims else q(_median(tims)),
        "n_entries_per_window": entries,
        "median_n_entries": _median(entries),
        "sum_n_entries": int(sum(entries)),
        "sum_n_long_entries": int(sum(long_e)),
        "sum_n_short_entries": int(sum(short_e)),
        "n_forced_window_close": forced,
        "not_a_forecast": True,
        "place_orders": False,
        "not_a_new_gate": True,
    }


def _fail_row(window: RiseWindow, error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "fail_closed": True,
        "error": error,
        "window_id": window.id,
        "arm": SCALP_R2_KEY,
        "n_trades": 0,
        "completed_round_trips": 0,
        "n_terminal_trips": 0,
        "n_entries": 0,
        "n_long_entries": 0,
        "n_short_entries": 0,
        "expectancy_after_costs_eur": None,
        "expectancy_completed_eur": None,
        "expectancy_terminal_adjusted_eur": None,
        "net_return_eur": None,
        "terminal_liquidation_net_eur": None,
        "not_a_forecast": True,
        "place_orders": False,
        "walker": "walk_long_short",
    }


def _row_from_walk(
    walk: dict[str, Any],
    bh: dict[str, Any],
    *,
    window: RiseWindow,
) -> dict[str, Any]:
    row = {
        "ok": True,
        "window_id": window.id,
        "start": window.start,
        "end": window.end,
        "character": window.character,
        "asset": ASSET,
        "bar": BAR,
        "regime_bar": REGIME_BAR,
        "arm": SCALP_R2_KEY,
        "role": "scalp_r2_dev_eliminate_only",
        "equity_eur": SCALP_START_EUR,
        "n_trades": int(walk.get("n_trades") or 0),
        "n_entries": int(walk.get("n_entries") or 0),
        "n_long_entries": int(walk.get("n_long_entries") or 0),
        "n_short_entries": int(walk.get("n_short_entries") or 0),
        "n_forced_flat_before_flip": int(walk.get("n_forced_flat_before_flip") or 0),
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
        "walker": "walk_long_short",
        "not_a_forecast": True,
        "place_orders": False,
        "audit_does_not_promote": True,
    }
    for k in V2_WALK_KEYS:
        if k in walk:
            row[k] = walk[k]
    return row


def run_scalp_s1_v2(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str | None = None,
) -> dict[str, Any]:
    """Re-score locked S1 under accounting_v2 via walk_long_flat (S1 is long-only)."""
    kwargs: dict[str, Any] = {"data_dir": data_dir, "pause_s": pause_s}
    if rest_base is not None:
        kwargs["rest_base"] = rest_base
    out = run_candidate_on_panel(cfg, _s1_spec(), **kwargs)
    out["source"] = SOURCE
    out["completed_summary"] = completed_panel_summary(out.get("rows") or [])
    out["lock_cite"] = LOCK_NOTE
    out["compare_role"] = "scalp_s1_provisional_dev"
    out["dev_eliminate_only"] = True
    out["promote"] = False
    return out


def run_scalp_r2_v2(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Score SCALP-R2 on R1–R7 with walk_long_short + 4H overlay. Fail-closed."""
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for w in panel_windows():
        cw = _as_cascade(w)
        try:
            h1 = fetch_bars(
                cw,
                ASSET,
                BAR,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=PAD_DAYS_1H,
            )
            h4 = fetch_bars(
                cw,
                ASSET,
                REGIME_BAR,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=PAD_DAYS_4H,
            )
            trade_1h = [b for b in h1 if w.start_ms <= b.ts_open_ms < w.end_ms_exclusive]
            trade_4h = [b for b in h4 if b.ts_close_ms <= w.end_ms_exclusive]
            if len(trade_1h) < MIN_1H_BARS:
                row = _fail_row(w, f"insufficient {BAR} bars")
                rows.append(row)
                continue
            if len([b for b in h4 if b.closed]) < MIN_4H_BARS:
                row = _fail_row(w, f"insufficient {REGIME_BAR} warmup for EMA{REGIME_SLOW}")
                rows.append(row)
                continue
            settings = EmaBookSettings(
                equity_eur=float(SCALP_START_EUR),
                fee_rate=fee_rate,
                slippage_bps=slip,
                leverage=1.0,
            )
            strategy = ScalpDogeDualThrustRvol4hRegime1hV1()
            # Refuse walk_long_flat path explicitly.
            try:
                strategy.desired_state(h1[:5])
                raise ReplayError("desired_state must raise for SCALP-R2 (fail closed)")
            except RuntimeError:
                pass
            walk = walk_long_short(
                h1,
                regime_bars=h4,
                strategy=strategy,
                settings=settings,
                trade_start_ms=w.start_ms,
                trade_end_ms=w.end_ms_exclusive,
            )
            if int(walk.get("n_short_entries") or 0) == 0 and int(
                walk.get("n_long_entries") or 0
            ) == 0:
                # Zero trades is a valid measured outcome; do not invent fills.
                pass
            bh = buy_and_hold(trade_1h, settings=settings)
            row = _row_from_walk(walk, bh, window=w)
            row["n_4h_bars_available"] = len(trade_4h)
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc))
        rows.append(row)

    old_soft = soft_promote_score(rows)
    v2_gate = accounting_v2_score(rows)
    deltas = [old_vs_v2_delta_row(r) for r in rows]
    return {
        "ok": all(r.get("ok") for r in rows),
        "candidate_key": SCALP_R2_KEY,
        "candidate_id": SCALP_R2_ID,
        "role": "scalp_r2_dev_eliminate_only",
        "ladder_id": LADDER_ID,
        "family": FAMILY,
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": BAR,
        "regime_bar": REGIME_BAR,
        "strategy": FAMILY,
        "sleeve_eur": SCALP_START_EUR,
        "sleeve": SLEEVE,
        "dt_n": DT_N,
        "k1": K1,
        "k2": K2,
        "rvol_n": RVOL_N,
        "rvol_min": RVOL_MIN,
        "regime_ema": f"{REGIME_FAST}/{REGIME_SLOW}",
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "walker": "walk_long_short",
        "refuses_walk_long_flat": True,
        "warmup_note": WARMUP_NOTE,
        "pad_days_1h": PAD_DAYS_1H,
        "pad_days_4h": PAD_DAYS_4H,
        "accounting_version": ACCOUNTING_VERSION,
        "soft_promote_v1_unchanged": old_soft,
        "soft_promote_gate": SOFT_PROMOTE_GATE,
        "accounting_v2": v2_gate,
        "accounting_v2_gate": ACCOUNTING_V2_GATE,
        "accounting_v2_note": ACCOUNTING_V2_NOTE,
        "old_summary": panel_summary_table(rows),
        "v2_summary": v2_panel_summary(rows),
        "completed_summary": completed_panel_summary(rows),
        "deltas": deltas,
        "windows": justification_rows(),
        "rows": rows,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "audit_does_not_promote": True,
        "soft_pass_ne_arm": True,
        "soft_pass_ne_scalp_arm": True,
        "dev_eliminate_only": True,
        "promote": False,
        "no_rvol_grind": True,
        "live_assume_eur_cap": 20.0,
        "mid_scalp_halted": True,
        "lock_cite": LOCK_NOTE,
        "source": SOURCE,
        "ts_ms": utc_ms(),
    }


def deltas_vs_scalp_s1(baseline: dict[str, Any], improve: dict[str, Any]) -> dict[str, Any]:
    """Measured Δ vs S1 under accounting_v2. Not a second gate. promote always False."""
    b_old = baseline.get("old_summary") or {}
    i_old = improve.get("old_summary") or {}
    b_v2 = baseline.get("v2_summary") or {}
    i_v2 = improve.get("v2_summary") or {}
    b_c = baseline.get("completed_summary") or completed_panel_summary(baseline.get("rows") or [])
    i_c = improve.get("completed_summary") or completed_panel_summary(improve.get("rows") or [])
    v2g = improve.get("accounting_v2") or {}
    v2_pass = str(v2g.get("verdict", "")).upper() == "PASS"

    def _pair(ref: Any, imp: Any) -> dict[str, Any]:
        delta = None
        if ref is not None and imp is not None:
            delta = q(float(imp) - float(ref))
        return {"ref": ref, "improve": imp, "delta": delta}

    panel_term = _pair(
        b_v2.get("panel_terminal_liquidation_net_eur"),
        i_v2.get("panel_terminal_liquidation_net_eur"),
    )
    panel_old = _pair(b_old.get("panel_net_eur"), i_old.get("panel_net_eur"))
    completed_exp = _pair(
        b_c.get("median_expectancy_completed_eur"),
        i_c.get("median_expectancy_completed_eur"),
    )
    worst_dd = _pair(b_c.get("worst_dd_eur"), i_c.get("worst_dd_eur"))
    median_completed = _pair(
        b_c.get("median_completed_round_trips"),
        i_c.get("median_completed_round_trips"),
    )
    median_tim = _pair(b_c.get("median_time_in_market"), i_c.get("median_time_in_market"))
    n_exp_completed = {
        "ref": b_c.get("n_expectancy_completed_gt_0"),
        "improve": i_c.get("n_expectancy_completed_gt_0"),
        "delta": (
            None
            if b_c.get("n_expectancy_completed_gt_0") is None
            or i_c.get("n_expectancy_completed_gt_0") is None
            else int(i_c["n_expectancy_completed_gt_0"]) - int(b_c["n_expectancy_completed_gt_0"])
        ),
    }
    short_entries = int(i_c.get("sum_n_short_entries") or 0)
    participation_eliminated = int(i_c.get("sum_n_entries") or 0) == 0
    panel_term_better = panel_term["delta"] is not None and float(panel_term["delta"]) > 0
    complete_exp_improved = (
        completed_exp["delta"] is not None and float(completed_exp["delta"]) > 0
    )

    if not v2_pass:
        honesty = "FAIL"
    elif complete_exp_improved and panel_term_better and not participation_eliminated:
        honesty = "PASS-and-better"
    elif panel_term_better and not participation_eliminated:
        honesty = "PASS-and-better-panel-net"
    elif v2_pass and (panel_term["delta"] is not None and float(panel_term["delta"]) <= 0):
        honesty = "PASS-but-worse"
    else:
        honesty = "PASS"

    return {
        "compare_to": SCALP_S1_ID,
        "compare_to_s0": SCALP_S0_ID,
        "improve_id": SCALP_R2_ID,
        "lock_cite": LOCK_NOTE,
        "accounting_version": ACCOUNTING_VERSION,
        "gate": ACCOUNTING_V2_GATE,
        "v2_verdict_r2": v2g.get("verdict"),
        "old_verdict_r2": (improve.get("soft_promote_v1_unchanged") or {}).get("verdict"),
        "panel_terminal_liquidation_net_eur": panel_term,
        "panel_old_net_return_eur": panel_old,
        "median_expectancy_completed_eur": completed_exp,
        "n_expectancy_completed_gt_0": n_exp_completed,
        "median_completed_round_trips": median_completed,
        "worst_dd_eur": worst_dd,
        "median_time_in_market": median_tim,
        "sum_n_short_entries_r2": short_entries,
        "sum_n_long_entries_r2": int(i_c.get("sum_n_long_entries") or 0),
        "n_exp_terminal_adj_gt_0": {
            "ref": b_v2.get("n_exp_terminal_adj_gt_0"),
            "improve": i_v2.get("n_exp_terminal_adj_gt_0"),
            "delta": (
                None
                if b_v2.get("n_exp_terminal_adj_gt_0") is None
                or i_v2.get("n_exp_terminal_adj_gt_0") is None
                else int(i_v2["n_exp_terminal_adj_gt_0"]) - int(b_v2["n_exp_terminal_adj_gt_0"])
            ),
        },
        "complete_exp_improved": complete_exp_improved,
        "panel_term_better": panel_term_better,
        "participation_eliminated": participation_eliminated,
        "honesty_label": honesty,
        "honesty_is_not_a_gate": True,
        "honesty_vs": "S1 / #83 accounting_v2 path",
        "promote": False,
        "promote_as_better": False,
        "eliminate": not v2_pass,
        "dev_eliminate_only": True,
        "soft_pass_ne_arm": True,
        "soft_pass_ne_scalp_arm": True,
        "no_rvol_grind": True,
        "walker": "walk_long_short",
        "note": (
            "Headline PASS/FAIL is rise_panel_accounting_v2 (locked before this score). "
            "Honesty label is a research comparison vs S1 — not a second gate and not a promote. "
            "Soft PASS ≠ Scalp-arm. R1–R7 DEV/eliminate-only. Shorts counted via walk_long_short."
        ),
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_both(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str | None = None,
) -> dict[str, Any]:
    rest = rest_base or OKX_REST
    s1 = run_scalp_s1_v2(cfg, data_dir=data_dir, pause_s=pause_s, rest_base=rest)
    r2 = run_scalp_r2_v2(cfg, data_dir=data_dir, pause_s=pause_s, rest_base=rest)
    deltas = deltas_vs_scalp_s1(s1, r2)
    return {
        "ok": bool(s1.get("ok") and r2.get("ok")),
        "scalp_s1": s1,
        "scalp_r2": r2,
        "deltas": deltas,
        "accounting_version": ACCOUNTING_VERSION,
        "promote": False,
        "dev_eliminate_only": True,
        "soft_pass_ne_arm": True,
        "soft_pass_ne_scalp_arm": True,
        "no_rvol_grind": True,
        "walker_r2": "walk_long_short",
        "refuses_walk_long_flat": True,
        "live_assume_eur_cap": 20.0,
        "mid_scalp_halted": True,
        "config_default_yaml_untouched": True,
        "not_a_forecast": True,
        "place_orders": False,
        "source": SOURCE,
        "lock_cite": LOCK_NOTE,
        "doc": DOC_NOTE,
        "ts_ms": utc_ms(),
    }


def write_report_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redact_record(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def _window_table(bundle: dict[str, Any]) -> list[str]:
    lines = [
        "| Id | n_trades old | completed | term trips | open? | "
        "old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € | "
        "long ent | short ent | max DD € | TIM |",
        "|----|-------------:|----------:|-----------:|:-----:|"
        "----------:|-----------:|--------:|----------:|----------------:|---------------:|"
        "---------:|----------:|---------:|----:|",
    ]
    rows_by_id = {r.get("window_id"): r for r in (bundle.get("rows") or [])}
    for d in bundle.get("deltas") or []:
        r = rows_by_id.get(d.get("window_id")) or {}
        lines.append(
            f"| {d.get('window_id')} | {d.get('n_trades_old')} | "
            f"{d.get('completed_round_trips')} | {d.get('n_terminal_trips')} | "
            f"{'yes' if d.get('open_position_at_end') else 'no'} | "
            f"{_fmt(d.get('net_return_eur_old'))} | {_fmt(d.get('terminal_liquidation_net_eur'))} | "
            f"{_fmt(d.get('delta_net_v2_minus_old_eur'))} | "
            f"{_fmt(d.get('expectancy_after_costs_eur_old'))} | "
            f"{_fmt(d.get('expectancy_completed_eur'))} | "
            f"{_fmt(d.get('expectancy_terminal_adjusted_eur'))} | "
            f"{int(r['n_long_entries']) if 'n_long_entries' in r else int(r.get('n_entries') or 0)} | "
            f"{int(r.get('n_short_entries') or 0) if ('n_short_entries' in r or 'n_long_entries' in r) else 0} | "
            f"{_fmt(r.get('max_dd_eur'))} | {_fmt(r.get('time_in_market'))} |"
        )
    return lines


def _panel_block(bundle: dict[str, Any], title: str) -> list[str]:
    old_s = bundle.get("old_summary") or {}
    v2_s = bundle.get("v2_summary") or {}
    old_soft = bundle.get("soft_promote_v1_unchanged") or {}
    v2g = bundle.get("accounting_v2") or {}
    comp = bundle.get("completed_summary") or {}
    return [
        f"**Panel summary ({title}):**",
        "",
        "| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |",
        "|-------|-------------------------------:|--------------------------:|",
        f"| panel net € | {_fmt(old_s.get('panel_net_eur'))} | "
        f"{_fmt(v2_s.get('panel_terminal_liquidation_net_eur'))} |",
        f"| median exp € | {_fmt(old_s.get('median_expectancy_eur'))} | "
        f"{_fmt(v2_s.get('median_expectancy_terminal_adjusted_eur'))} |",
        f"| median trips | {_fmt(old_s.get('median_trades'), 1)} | "
        f"{_fmt(v2_s.get('median_terminal_trips'), 1)} |",
        f"| exp>0 / 7 | {old_s.get('n_exp_gt_0')} | {v2_s.get('n_exp_terminal_adj_gt_0')} |",
        f"| gate verdict | {old_soft.get('verdict')} (`soft_promote_v1`) | "
        f"{v2g.get('verdict')} (`{ACCOUNTING_V2_GATE}`) |",
        "",
        "**Complete-trade (realized only — not a gate):**",
        f"- completed trips / window: `{comp.get('completed_round_trips_per_window')}` · "
        f"median **{_fmt(comp.get('median_completed_round_trips'), 1)}**",
        f"- windows with completed exp>0: **{comp.get('n_expectancy_completed_gt_0')}**/7",
        f"- median expectancy_completed €: **{_fmt(comp.get('median_expectancy_completed_eur'))}**",
        f"- panel realized net €: **{_fmt(comp.get('panel_realized_net_eur'))}**",
        f"- worst DD €: **{_fmt(comp.get('worst_dd_eur'))}**",
        f"- median TIM: **{_fmt(comp.get('median_time_in_market'))}** · "
        f"sum n_entries: **{comp.get('sum_n_entries')}** "
        f"(long **{comp.get('sum_n_long_entries', '—')}** / "
        f"short **{comp.get('sum_n_short_entries', '—')}**)",
        f"- forced window closes: **{v2_s.get('n_forced_window_close')}**/7",
        "",
    ]


def render_results_markdown(
    baseline: dict[str, Any],
    improve: dict[str, Any],
    *,
    deltas: dict[str, Any] | None = None,
) -> str:
    if deltas is None:
        deltas = deltas_vs_scalp_s1(baseline, improve)
    v2g = improve.get("accounting_v2") or {}
    verdict = v2g.get("verdict", "—")
    honesty = deltas.get("honesty_label", "—")
    lines: list[str] = [
        "# 99 — SCALP-R2 FIRST SCORE: Dual Thrust + RVOL + **4H EMA12/21 regime** 1H €20",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.",
        "**Config:** `config/default.yaml` **untouched**.",
        "**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ Scalp-arm. **This score does not promote.**",
        f"**Accounting:** `{ACCOUNTING_VERSION}` (evaluator-v2 / terminal liquidation + "
        "completed expectancy). Gate locked in [`91`](./91-rise-panel-accounting-v2.md) "
        "**before** this score — do not rewrite it after seeing results.",
        f"**Lock (already on main):** [`93`](./93-frozen-mid-scalp-candidates.md) — "
        f"`{SCALP_R2_ID}`.",
        f"**Panel:** [`54`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change).",
        f"**Compare:** Scalp S1 `{SCALP_S1_ID}` (and S0 `#83` `{SCALP_S0_ID}` via S1 path).",
        "**Walker:** `walk_long_short` — **not** `walk_long_flat` (would silently drop shorts).",
        "**No** RVOL 1.25/1.5 grind. Not a threshold rescue of S1.",
        "**R1–R7:** DEV/eliminate-only — **no promote**. Soft PASS ≠ arm.",
        "**Branch:** `research/vnext-scalp-r2-dt-4h-regime`. Base: `main` after PR #86. "
        "phase1/98 reserved for H0 health; this doc is **99**.",
        "",
        "---",
        "",
        "## Gate (LOCKED — same as #91; do not change after seeing results)",
        "",
        f"`{ACCOUNTING_V2_GATE}`: median_terminal_trips≥1 AND ≥5/7 "
        "expectancy_terminal_adjusted>0 AND panel_terminal_liquidation_net>0.",
        "OLD `soft_promote_v1` is reported for honesty, **not** rewritten.",
        "",
        f"Gate note: {ACCOUNTING_V2_NOTE}",
        "",
        "**Honesty:** Soft PASS ≠ Scalp-arm. V2 PASS ≠ promote. "
        "Prefer `expectancy_completed_eur` + `completed_round_trips`. "
        "Short entries must be non-zero somewhere if the regime fires shorts — "
        "otherwise the walker is not exercising the short path.",
        "",
        "---",
        "",
        "## A. LOCKED Scalp S1 baseline — re-scored under accounting_v2",
        "",
        f"**scalp_s1_id:** `{SCALP_S1_ID}`",
        "",
        "- Rule: 1H Dual Thrust N20 k=0.5 + RVOL20>1, **long/flat only** (S1).",
        "- Walker: `walk_long_flat` (correct for long-only S1).",
        "- Bar: DOGE-USDT **1H**. Sleeve: Scalp **€20**.",
        "- Role: provisional DEV / honesty comparator ([`87`](./87-rise-panel-scalp-s1-rvol-1h.md), "
        "[`91`](./91-rise-panel-accounting-v2.md)).",
        "",
        "### S1 per window (OLD vs V2)",
        "",
    ]
    lines.extend(_window_table(baseline))
    lines.append("")
    lines.extend(_panel_block(baseline, "Scalp S1 RVOL"))
    lines.extend(
        [
            "`audit_does_not_promote: true`.",
            "",
            "`not_a_forecast: true`.",
            "",
            "---",
            "",
            "## B. LOCKED SCALP-R2 family (scored AFTER [`93`](./93-frozen-mid-scalp-candidates.md))",
            "",
            f"**Family:** `{FAMILY}`  ",
            f"**scalp_r2_id:** `{SCALP_R2_ID}`  ",
            "**Code:** `atlas.strategy.scalp_doge_dual_thrust_rvol_4h_regime_1h."
            "ScalpDogeDualThrustRvol4hRegime1hV1`  ",
            f"**compare_to:** `{SCALP_S1_ID}`  ",
            f"**Ladder:** `{LADDER_ID}` · sleeve `{SLEEVE}` · decision `{BAR}` · regime `{REGIME_BAR}`.",
            "",
            "### Rule card (LOCKED — do not rewrite)",
            "",
            "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.",
            f"- Dual Thrust: N=**{DT_N}**, k1=k2=**{K1}** + RVOL{RVOL_N}>**{RVOL_MIN}** (unchanged from S1).",
            f"- Regime: **{REGIME_BAR} EMA{REGIME_FAST}/{REGIME_SLOW}**.",
            f"- LONG: EMA{REGIME_FAST}>EMA{REGIME_SLOW} AND upper DT break AND RVOL>{RVOL_MIN}.",
            f"- SHORT: EMA{REGIME_FAST}<EMA{REGIME_SLOW} AND lower DT break AND RVOL>{RVOL_MIN}.",
            "- Exit: opposite DT boundary OR HTF regime reversal.",
            "- Max one position. No pyramid / avg / martingale.",
            "- Fill: signal close → next open. Size: Scalp €20. Costs: 5+5 bps.",
            "- **Walker:** `atlas.paper.ls_eval.walk_long_short` (signed qty; shorts filled).",
            "",
            "---",
            "",
            "## C. Harness",
            "",
            "- Script: `scripts/run_rise_panel_scalp_r2_4h_regime_1h_eval.py`",
            "- Module: `atlas.paper.rise_panel_scalp_r2_4h_regime_1h_eval`",
            "- Walker: `atlas.paper.ls_eval.walk_long_short`",
            f"- Accounting: `{ACCOUNTING_V2_GATE}` / [`91`](./91-rise-panel-accounting-v2.md)",
            "- Artifacts: `results/accounting_v2/rise_panel_accounting_v2_scalp_r2_*.json`",
            "- Unit tests: `tests/unit/test_walk_long_short.py`, "
            "`tests/unit/test_rise_panel_scalp_r2_4h_regime_1h.py`",
            "",
            "---",
            "",
            "## D. Results — SCALP-R2 on same 7 (accounting_v2)",
            "",
            f"**scalp_r2_id:** `{SCALP_R2_ID}`",
            "",
            "### R2 per window (OLD vs V2)",
            "",
        ]
    )
    lines.extend(_window_table(improve))
    lines.append("")
    lines.extend(_panel_block(improve, "SCALP-R2 4H regime"))
    lines.extend(
        [
            f"### accounting_v2 verdict (SCALP-R2): **{verdict}** (`{ACCOUNTING_V2_GATE}`)",
            "",
            f"- median_terminal_trips={_fmt(v2g.get('median_terminal_trips'), 1)} "
            f"(ok={v2g.get('median_terminal_trips_ok')})",
            f"- exp_terminal_adj>0: {v2g.get('n_expectancy_terminal_adjusted_gt_0')}/7 "
            f"(need ≥{v2g.get('n_expectancy_gt_0_required')}; "
            f"ok={v2g.get('expectancy_terminal_adjusted_gt_0_ok')})",
            f"- panel_terminal_liquidation_net €={_fmt(v2g.get('panel_terminal_liquidation_net_eur'))} "
            f"(ok={v2g.get('panel_net_ok')})",
            "",
            f"### Honesty label vs Scalp S1: **{honesty}**",
            "",
            "### Honesty deltas vs Scalp S1 (R2 − S1)",
            "",
            "| Metric | Scalp S1 €20 | SCALP-R2 €20 | Δ |",
            "|--------|-------------:|-------------:|--:|",
            f"| v2 panel term € | {_fmt((deltas.get('panel_terminal_liquidation_net_eur') or {}).get('ref'))} | "
            f"{_fmt((deltas.get('panel_terminal_liquidation_net_eur') or {}).get('improve'))} | "
            f"{_fmt((deltas.get('panel_terminal_liquidation_net_eur') or {}).get('delta'))} |",
            f"| old panel net € | {_fmt((deltas.get('panel_old_net_return_eur') or {}).get('ref'))} | "
            f"{_fmt((deltas.get('panel_old_net_return_eur') or {}).get('improve'))} | "
            f"{_fmt((deltas.get('panel_old_net_return_eur') or {}).get('delta'))} |",
            f"| median exp completed € | {_fmt((deltas.get('median_expectancy_completed_eur') or {}).get('ref'))} | "
            f"{_fmt((deltas.get('median_expectancy_completed_eur') or {}).get('improve'))} | "
            f"{_fmt((deltas.get('median_expectancy_completed_eur') or {}).get('delta'))} |",
            f"| n completed exp>0 / 7 | {(deltas.get('n_expectancy_completed_gt_0') or {}).get('ref')} | "
            f"{(deltas.get('n_expectancy_completed_gt_0') or {}).get('improve')} | "
            f"{(deltas.get('n_expectancy_completed_gt_0') or {}).get('delta')} |",
            f"| median completed trips | {_fmt((deltas.get('median_completed_round_trips') or {}).get('ref'), 1)} | "
            f"{_fmt((deltas.get('median_completed_round_trips') or {}).get('improve'), 1)} | "
            f"{_fmt((deltas.get('median_completed_round_trips') or {}).get('delta'), 1)} |",
            f"| worst DD € | {_fmt((deltas.get('worst_dd_eur') or {}).get('ref'))} | "
            f"{_fmt((deltas.get('worst_dd_eur') or {}).get('improve'))} | "
            f"{_fmt((deltas.get('worst_dd_eur') or {}).get('delta'))} |",
            f"| median TIM | {_fmt((deltas.get('median_time_in_market') or {}).get('ref'))} | "
            f"{_fmt((deltas.get('median_time_in_market') or {}).get('improve'))} | "
            f"{_fmt((deltas.get('median_time_in_market') or {}).get('delta'))} |",
            f"| sum short entries (R2) | — | **{deltas.get('sum_n_short_entries_r2')}** | — |",
            f"| sum long entries (R2) | — | **{deltas.get('sum_n_long_entries_r2')}** | — |",
            f"| soft promote (OLD) | {(baseline.get('soft_promote_v1_unchanged') or {}).get('verdict')} | "
            f"{(improve.get('soft_promote_v1_unchanged') or {}).get('verdict')} | — |",
            f"| v2 gate | {(baseline.get('accounting_v2') or {}).get('verdict')} | "
            f"**{verdict}** | — |",
            f"| honesty | — | **{honesty}** | promote=False |",
            "",
            "---",
            "",
            "## E. Soft PASS ≠ arm · no promote",
            "",
            f"accounting_v2 **{verdict}**. Paper only. **Soft PASS ≠ Scalp-arm**. "
            "Mid/Scalp **HALTED**. Live ≤€20. `not_a_forecast: true`. `place_orders: false`.",
            "",
            f"- **promote:** `False`",
            f"- **dev_eliminate_only:** `True`",
            f"- **eliminate:** `{deltas.get('eliminate')}`",
            f"- **no_rvol_grind:** `True`",
            f"- **walker:** `walk_long_short`",
            "",
        ]
    )
    if deltas.get("eliminate"):
        lines.extend(
            [
                "**SCALP-R2 eliminated under accounting_v2.** Archive. Do **not** grind RVOL "
                "1.25/1.5 or k on R1–R7.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "**V2 PASS is still DEV/eliminate-only.** It is **not** a GREEN CANDIDATE, "
                "**not** Scalp-arm, **not** a promote. Soft PASS ≠ arm.",
                "",
            ]
        )
    lines.extend(
        [
            "---",
            "",
            "## F. Integrity / non-goals",
            "",
            "- Not a rewrite of `rise_panel_accounting_v2` or [`91`](./91-rise-panel-accounting-v2.md).",
            "- Not scored with `walk_long_flat`.",
            "- Not a RVOL threshold rescue of S1.",
            "- Not Mid M2–M4. Not CORE tip grind. Not phase1/98 (H0 health).",
            "- `config/default.yaml` untouched.",
            "",
            "`not_a_forecast: true`. `place_orders: false`.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"
