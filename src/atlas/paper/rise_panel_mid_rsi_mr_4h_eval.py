"""rise_panel_v1 Mid #66 — DOGE 4H RSI(14) MR €40 vs NEW Mid Breakout #65 baseline.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Same entry/exit style as Scalp #59 (cross-up ≤30 / exit ≥70); no EMA.
soft_promote_v1 gate unchanged. Honesty vs Breakout #65 panel_net≈€95.45 —
promote-as-better only if panel_net higher; else PASS-but-worse / FAIL clearly.
On PASS+better: Core+Mid book €180 (no Scalp). Soft PASS ≠ Mid-arm.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    BASELINE_ID,
    MID_BAR_CANDIDATE,
    MID_BASELINE_ID,
    MID_BASELINE_CORE_MID_PANEL_NET_EUR,
    MID_BASELINE_PANEL_NET_EUR,
    MID_EMA_ARCHIVE_ID,
    PANEL_LABEL,
    RISE_PANEL_V1,
    RiseWindow,
    SOFT_PROMOTE_GATE,
    SOFT_PROMOTE_NOTE,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
)
from atlas.paper.rise_panel_eval import run_core_baseline
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import Bar, q
from atlas.strategy.mid_doge_breakout_4h import MidDogeBreakout4hV1
from atlas.strategy.mid_doge_rsi_mr_4h import (
    BAR,
    ENTRY_RSI,
    EXIT_RSI,
    FAMILY,
    RSI_PERIOD,
    MidDogeRsiMr4hV1,
)

SOURCE = "rise_panel_v1_mid_rsi_mr_66"
WARMUP_PAD_4H_DAYS = 10

# NEW formal Mid baseline = Breakout #65 (promoted). EMA = archive only.
MID_BREAKOUT_BASELINE_ID = MID_BASELINE_ID  # rise_panel_v1_mid_doge_breakoutv1_4h_eur40
MID_IMPROVE_ID = "rise_panel_v1_mid_doge_rsi14_mr_4h_eur40"
CORE_MID_BOOK_EUR = CORE_START_EUR + MID_START_EUR  # 180
CORE_MID_BOOK_ID = "rise_panel_v1_core_mid_book_180_mid_rsi14_mr_4h"

CORE_55_PANEL_NET = 363.9983
MID_65_PANEL_NET = MID_BASELINE_PANEL_NET_EUR  # ≈95.4483
CORE_MID_65_PANEL_NET = MID_BASELINE_CORE_MID_PANEL_NET_EUR  # ≈459.4466
MID_EMA_ARCHIVE_PANEL_NET = 83.6104

MID_BREAKOUT_SNAPSHOT_65 = {
    "median_trades": 6.0,
    "n_exp_gt_0": 5,
    "panel_net_eur": 95.4483,
    "median_expectancy_eur": 2.4647,
    "verdict": "PASS",
    "note": "phase1/65 Mid 4H BreakoutV1 soft PASS; NEW formal Mid baseline (Kaje promote)",
}

MID_EMA_ARCHIVE_SNAPSHOT = {
    "median_trades": 7.0,
    "n_exp_gt_0": 6,
    "panel_net_eur": 83.6104,
    "median_expectancy_eur": 2.0928,
    "verdict": "PASS",
    "note": "phase1/54 Mid 4H EMA — ARCHIVE reference only after #65 promote",
}


def _as_cascade(w: RiseWindow) -> CascadeWindow:
    return CascadeWindow(
        id=w.id,
        start=w.start,
        end=w.end,
        set_id="rise",
        label=w.label,
    )


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _row_from_walk(
    walk: dict[str, Any],
    bh: dict[str, Any],
    *,
    window: RiseWindow,
    bar: str,
    equity: float,
    arm: str,
) -> dict[str, Any]:
    return {
        "ok": True,
        "window_id": window.id,
        "start": window.start,
        "end": window.end,
        "character": window.character,
        "asset": ASSET,
        "bar": bar,
        "arm": arm,
        "equity_eur": equity,
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
        "not_a_forecast": True,
        "place_orders": False,
    }


def _fail_row(window: RiseWindow, error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "fail_closed": True,
        "error": error,
        "window_id": window.id,
        "n_trades": 0,
        "expectancy_after_costs_eur": None,
        "net_return_eur": None,
        "max_dd_eur": None,
        "time_in_market": None,
        "bh_net_return_eur": None,
        "bh_max_dd_eur": None,
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_strategy_on_window(
    *,
    bars: list[Bar],
    window: RiseWindow,
    strategy: Any,
    equity: float,
    fee_rate: float,
    slippage_bps: float,
    bar: str,
    arm: str,
) -> dict[str, Any]:
    settings = EmaBookSettings(
        equity_eur=float(equity),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    trade_bars = [b for b in bars if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade_bars) < 12:
        return _fail_row(window, f"insufficient {bar} bars")
    walk = walk_long_flat(
        bars,
        strategy=strategy,
        settings=settings,
        trade_start_ms=window.start_ms,
        trade_end_ms=window.end_ms_exclusive,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    return _row_from_walk(walk, bh, window=window, bar=bar, equity=equity, arm=arm)


def _run_panel(
    cfg: Any,
    *,
    data_dir: Path,
    strategy_factory: Callable[[], Any],
    arm: str,
    candidate_id: str,
    strategy_label: str,
    family: str,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
    apply_soft_promote: bool = True,
) -> dict[str, Any]:
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for w in panel_windows():
        cw = _as_cascade(w)
        try:
            bars = fetch_bars(
                cw,
                ASSET,
                MID_BAR_CANDIDATE,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=WARMUP_PAD_4H_DAYS,
            )
            row = run_strategy_on_window(
                bars=bars,
                window=w,
                strategy=strategy_factory(),
                equity=MID_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
                bar=MID_BAR_CANDIDATE,
                arm=arm,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc))
        rows.append(row)

    soft = soft_promote_score(rows) if apply_soft_promote else None
    summary = panel_summary_table(rows)
    out: dict[str, Any] = {
        "ok": all(r.get("ok") for r in rows),
        "candidate_id": candidate_id,
        "mid_baseline_id": MID_BREAKOUT_BASELINE_ID,
        "mid_ema_archive_id": MID_EMA_ARCHIVE_ID,
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": BAR,
        "family": family,
        "strategy": strategy_label,
        "sleeve_eur": MID_START_EUR,
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "windows": justification_rows(),
        "rows": rows,
        "summary": summary,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
        "compare_to_mid_baseline": MID_BREAKOUT_BASELINE_ID,
        "rsi_period": RSI_PERIOD,
        "entry_rsi": ENTRY_RSI,
        "exit_rsi": EXIT_RSI,
        "ema_filter": False,
    }
    if soft is not None:
        out["soft_promote_gate"] = SOFT_PROMOTE_GATE
        out["soft_promote_note"] = SOFT_PROMOTE_NOTE
        out["soft_promote"] = soft
    return out


def run_mid_breakout_baseline(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Re-score NEW Mid formal baseline BreakoutV1 4H on rise_panel_v1 (€40)."""

    def factory() -> MidDogeBreakout4hV1:
        return MidDogeBreakout4hV1()

    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=factory,
        arm="mid_breakoutv1_4h",
        candidate_id=MID_BREAKOUT_BASELINE_ID,
        strategy_label="breakoutv1_lb16_atr14_long_flat",
        family="breakout_v1_long_flat_4h",
        pause_s=pause_s,
        rest_base=rest_base,
        apply_soft_promote=True,
    )
    out["role"] = "mid_baseline"
    out["mid_baseline_id"] = MID_BREAKOUT_BASELINE_ID
    out["promote_note"] = "NEW formal Mid baseline after #65 soft PASS promote (Kaje lock)"
    return out


def run_mid_rsi_mr_4h(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Mid RSI(14) MR 4H long/flat on SAME locked 7 — candidate #66."""

    def factory() -> MidDogeRsiMr4hV1:
        return MidDogeRsiMr4hV1()

    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=factory,
        arm="mid_rsi14_mr_4h",
        candidate_id=MID_IMPROVE_ID,
        strategy_label=f"rsi{RSI_PERIOD}_mr_cross_up_le{ENTRY_RSI:g}_exit_ge{EXIT_RSI:g}",
        family=FAMILY,
        pause_s=pause_s,
        rest_base=rest_base,
        apply_soft_promote=True,
    )
    out["role"] = "mid_improve"
    out["mid_improve_id"] = MID_IMPROVE_ID
    out["family"] = FAMILY
    out["reuse_note"] = (
        "Wilder RSI helper from mid_doge_rsi_mr; Mid #66 locks Scalp #59 style "
        "cross-up≤30 / exit≥70 on 4H (≠ Mid #43 1D level-entry<30 exit>50)."
    )
    return out


def deltas_vs_mid_baseline(baseline: dict[str, Any], improve: dict[str, Any]) -> dict[str, Any]:
    """Panel metric deltas: RSI MR Mid − Mid Breakout #65 baseline (NOT vs Core)."""
    b = baseline.get("summary") or {}
    i = improve.get("summary") or {}

    def _d(key: str) -> float | None:
        bv, iv = b.get(key), i.get(key)
        if bv is None or iv is None:
            return None
        return q(float(iv) - float(bv))

    d_net = _d("panel_net_eur")
    promote_as_better = d_net is not None and float(d_net) > 0
    return {
        "compare_to": MID_BREAKOUT_BASELINE_ID,
        "improve_id": MID_IMPROVE_ID,
        "median_expectancy_eur": {
            "baseline": b.get("median_expectancy_eur"),
            "improve": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur"),
        },
        "panel_net_eur": {
            "baseline": b.get("panel_net_eur"),
            "improve": i.get("panel_net_eur"),
            "delta": d_net,
        },
        "median_trades": {
            "baseline": b.get("median_trades"),
            "improve": i.get("median_trades"),
            "delta": _d("median_trades"),
        },
        "n_exp_gt_0": {
            "baseline": b.get("n_exp_gt_0"),
            "improve": i.get("n_exp_gt_0"),
            "delta": (
                None
                if b.get("n_exp_gt_0") is None or i.get("n_exp_gt_0") is None
                else int(i["n_exp_gt_0"]) - int(b["n_exp_gt_0"])
            ),
        },
        "promote_as_better": promote_as_better,
        "honesty_rule": (
            "promote-as-better only if panel_net higher than Breakout #65; "
            "else PASS-but-worse / FAIL clearly"
        ),
        "not_a_forecast": True,
        "place_orders": False,
    }


def deltas_vs_ema_archive(improve: dict[str, Any]) -> dict[str, Any]:
    """Optional honesty: RSI MR Mid − archived EMA Mid snapshot."""
    i = improve.get("summary") or {}
    snap = MID_EMA_ARCHIVE_SNAPSHOT

    def _d(key: str, snap_key: str) -> float | None:
        iv = i.get(key)
        if iv is None:
            return None
        return q(float(iv) - float(snap[snap_key]))

    return {
        "compare_to": MID_EMA_ARCHIVE_ID,
        "improve_id": MID_IMPROVE_ID,
        "note": "optional honesty vs archived EMA Mid (not current Mid baseline)",
        "median_expectancy_eur": {
            "ema_archive": snap["median_expectancy_eur"],
            "improve": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur", "median_expectancy_eur"),
        },
        "panel_net_eur": {
            "ema_archive": snap["panel_net_eur"],
            "improve": i.get("panel_net_eur"),
            "delta": _d("panel_net_eur", "panel_net_eur"),
        },
        "median_trades": {
            "ema_archive": snap["median_trades"],
            "improve": i.get("median_trades"),
            "delta": _d("median_trades", "median_trades"),
        },
        "n_exp_gt_0": {
            "ema_archive": snap["n_exp_gt_0"],
            "improve": i.get("n_exp_gt_0"),
            "delta": (
                None
                if i.get("n_exp_gt_0") is None
                else int(i["n_exp_gt_0"]) - int(snap["n_exp_gt_0"])
            ),
        },
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_core_mid_book(
    cfg: Any,
    *,
    data_dir: Path,
    mid_bundle: dict[str, Any],
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
    force: bool = False,
) -> dict[str, Any]:
    """Core €140 1D EMA + this Mid €40 RSI MR — book €180, NO Scalp sleeve.

    Cascade book only when soft PASS AND panel_net better than Breakout (or force).
    Honest Δ vs Breakout Core+Mid €459.45.
    """
    core = run_core_baseline(cfg, data_dir=data_dir, pause_s=pause_s, rest_base=rest_base)
    cs = core.get("summary") or {}
    ms = mid_bundle.get("summary") or {}
    core_net = float(cs.get("panel_net_eur") or 0.0)
    mid_net = float(ms.get("panel_net_eur") or 0.0)
    combined = q(core_net + mid_net)
    return {
        "ok": bool(core.get("ok")) and bool(mid_bundle.get("ok")),
        "book_id": CORE_MID_BOOK_ID,
        "book_start_eur": CORE_MID_BOOK_EUR,
        "core_id": BASELINE_ID,
        "mid_id": MID_IMPROVE_ID,
        "scalp": None,
        "no_scalp": True,
        "force_informational": force,
        "note": (
            "Core+Mid only (bot cascade/arming path). Scalp = Kaje manual — "
            "no Scalp sleeve invented. Independent sleeve panel nets summed."
        ),
        "core": {
            "panel_net_eur": cs.get("panel_net_eur"),
            "median_trades": cs.get("median_trades"),
            "n_exp_gt_0": cs.get("n_exp_gt_0"),
            "summary": cs,
            "rows": core.get("rows"),
        },
        "mid": {
            "panel_net_eur": ms.get("panel_net_eur"),
            "median_trades": ms.get("median_trades"),
            "n_exp_gt_0": ms.get("n_exp_gt_0"),
            "soft_promote": mid_bundle.get("soft_promote"),
            "summary": ms,
        },
        "panel_sleeve_nets_eur": {
            "core": q(core_net),
            "mid": q(mid_net),
            "combined_core_mid": combined,
        },
        "vs_65_core_mid_breakout": {
            "core_65": CORE_55_PANEL_NET,
            "mid_65": MID_65_PANEL_NET,
            "combined_65": CORE_MID_65_PANEL_NET,
            "core_delta": q(core_net - CORE_55_PANEL_NET),
            "mid_delta": q(mid_net - MID_65_PANEL_NET),
            "combined_delta": q(combined - CORE_MID_65_PANEL_NET),
        },
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
    }


def write_report_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_record(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_results_markdown(
    baseline: dict[str, Any],
    improve: dict[str, Any],
    *,
    deltas: dict[str, Any] | None = None,
    deltas_ema: dict[str, Any] | None = None,
    core_mid_book: dict[str, Any] | None = None,
) -> str:
    """Full phase1/66 doc with lock + scored results (+ Core+Mid book if promote)."""
    if deltas is None:
        deltas = deltas_vs_mid_baseline(baseline, improve)
    if deltas_ema is None:
        deltas_ema = deltas_vs_ema_archive(improve)
    soft = improve.get("soft_promote") or {}
    soft_pass = str(soft.get("verdict", "")).upper() == "PASS"
    bs = baseline.get("summary") or {}
    ms = improve.get("summary") or {}
    soft_b = baseline.get("soft_promote") or bs.get("soft_promote") or {}
    d_net = (deltas.get("panel_net_eur") or {}).get("delta")
    panel_better = d_net is not None and float(d_net) > 0
    panel_worse = d_net is not None and float(d_net) < 0
    promote_as_better = soft_pass and panel_better
    if soft_pass and panel_worse:
        honesty_label = "PASS-but-worse"
    elif soft_pass and panel_better:
        honesty_label = "PASS-and-better (promote-as-better eligible)"
    elif soft_pass:
        honesty_label = "PASS (panel_net ≈ baseline)"
    else:
        honesty_label = "FAIL"

    lines: list[str] = []
    lines.append(
        "# 66 — rise_panel_v1 Mid: DOGE **4H RSI(14) MR** long/flat (€40)"
    )
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; "
        "Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Mid-arm."
    )
    lines.append(
        "**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked "
        "R1–R7 dates (DO NOT change)."
    )
    lines.append(
        "**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 "
        "([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))"
    )
    lines.append(
        "**Compare:** NEW Mid formal baseline Breakout [`65-rise-panel-mid-breakoutv1-4h.md`]"
        "(./65-rise-panel-mid-breakoutv1-4h.md) / promote [`65b-mid-breakout-promote.md`]"
        "(./65b-mid-breakout-promote.md). EMA Mid = archive only. "
        "**Same entry/exit style as Scalp #59** (cross-up ≤30 / exit ≥70); **no** EMA."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Soft promote gate (LOCKED — same as #54)")
    lines.append("")
    lines.append(
        "`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of "
        "`core_style_return` A∧B):"
    )
    lines.append("")
    lines.append(
        "1. `median_trades` across the 7 windows **≫ 0** "
        "(coded: `median_trades >= 1`)"
    )
    lines.append("2. **≥5 / 7** windows with `expectancy_after_costs > 0`")
    lines.append("3. **panel net > 0** (sum of after-costs net € across 7)")
    lines.append("")
    lines.append(
        "Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`."
    )
    lines.append("")
    lines.append(
        "**Honesty vs Breakout #65:** promote-as-better **only if** `panel_net` higher "
        f"than ≈€{MID_65_PANEL_NET:.2f}; else **PASS-but-worse** / **FAIL** clearly."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED Mid baseline (NEW formal — Breakout #65)")
    lines.append("")
    lines.append(f"**mid_baseline_id:** `{MID_BREAKOUT_BASELINE_ID}`  ")
    lines.append(
        "(soft_promote **PASS**, promoted #65 — see [`65b-mid-breakout-promote.md`]"
        "(./65b-mid-breakout-promote.md))"
    )
    lines.append("")
    lines.append(
        "- Rule: BreakoutV1 lookback 16 + ATR quiet; channel exit. Never short."
    )
    lines.append("- Bar: DOGE-USDT **4H**. Sleeve: Mid **€40**.")
    lines.append(
        "- Compare target for this trial: **Mid vs Mid-Breakout-baseline** (NOT vs Core €140)."
    )
    lines.append(
        f"- Snapshot (#65): panel_net≈**€{_fmt(MID_BREAKOUT_SNAPSHOT_65['panel_net_eur'])}** · "
        f"median_trades=**{_fmt(MID_BREAKOUT_SNAPSHOT_65['median_trades'], 1)}** · "
        f"exp>0 **{MID_BREAKOUT_SNAPSHOT_65['n_exp_gt_0']}**/7."
    )
    lines.append(
        f"- EMA Mid archive (`{MID_EMA_ARCHIVE_ID}`): panel_net≈**€{_fmt(MID_EMA_ARCHIVE_PANEL_NET)}** "
        "— **not** current Mid baseline."
    )
    lines.append("")
    lines.append("### Mid Breakout baseline per window (re-scored)")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in baseline.get("rows") or []:
        wid = r.get("window_id", "?")
        lines.append(
            f"| {wid} | {r.get('n_trades', 0)} | {_fmt(r.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(r.get('net_return_eur'))} | {_fmt(r.get('max_dd_eur'))} | "
            f"{_fmt(r.get('time_in_market'))} | {_fmt(r.get('bh_net_return_eur'))} | "
            f"{_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (Mid Breakout baseline):**")
    lines.append(
        f"- windows with exp>0: **{bs.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{bs.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(bs.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(bs.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(bs.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(bs.get('worst_dd_eur'))}**")
    lines.append(
        f"- soft_promote: **{soft_b.get('verdict', '—')}** (`{SOFT_PROMOTE_GATE}`)"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. LOCKED Mid family (BEFORE scoring)")
    lines.append("")
    lines.append(
        "**ONE family only — NOT grinding RSI period / thresholds / TF / costs. No EMA filter. "
        "Do not re-grind Breakout / EMA / Donchian.**"
    )
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**mid_improve_id:** `{MID_IMPROVE_ID}`  ")
    lines.append(
        f"**compare_to:** `{MID_BREAKOUT_BASELINE_ID}` (primary); optional archive `{MID_EMA_ARCHIVE_ID}`"
    )
    lines.append(
        f"**Canonical RSI MR (Scalp #59 style):** Wilder RSI(**{RSI_PERIOD}**); "
        f"long on cross-up from ≤{ENTRY_RSI:g}; flat when RSI≥{EXIT_RSI:g}. "
        "Decision bar **4H**. **No** EMA filter."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append(
        "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**."
    )
    lines.append(f"- RSI: Wilder **RSI({RSI_PERIOD})**.")
    lines.append(
        f"- **Long:** closed-bar RSI crosses up from ≤{ENTRY_RSI:g} "
        f"(prev ≤{ENTRY_RSI:g} and curr >{ENTRY_RSI:g}). Long only."
    )
    lines.append(
        f"- **Flat/exit:** closed-bar RSI ≥{EXIT_RSI:g}. Never short."
    )
    lines.append(
        "- **No** EMA filter / regime gate (distinct from Breakout #65, EMA archive, Donchian #64)."
    )
    lines.append("- Insufficient history → flat.")
    lines.append(
        "- Fill: signal close → next open. Size: full Mid sleeve €40 when long."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(
        "- **No** RSI period / threshold / TF / cost grind on FAIL. **No** EMA / Breakout rescue."
    )
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        "NEW Mid formal baseline is BreakoutV1 4H (#65, panel≈€95.45). "
        "This trial ports **Scalp #59 RSI(14) MR** entry/exit onto Mid €40 / locked rise panel / "
        "**4H** — testing mean-reversion without inventing EMA / Breakout knobs."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_mid_rsi_mr_4h_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_mid_rsi_mr_4h_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.mid_doge_rsi_mr_4h` "
        "(reuses `rsi_wilder` from `mid_doge_rsi_mr`; Scalp #59 cross-up/exit style)"
    )
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; "
        "Core+Mid book €180 on PASS+better only (no Scalp)"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_mid_rsi_mr_4h.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Mid RSI(14) MR 4H €40 on same 7")
    lines.append("")
    lines.append(f"**mid_improve_id:** `{MID_IMPROVE_ID}`")
    lines.append("")
    lines.append("### Improve per window")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in improve.get("rows") or []:
        wid = r.get("window_id", "?")
        lines.append(
            f"| {wid} | {r.get('n_trades', 0)} | {_fmt(r.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(r.get('net_return_eur'))} | {_fmt(r.get('max_dd_eur'))} | "
            f"{_fmt(r.get('time_in_market'))} | {_fmt(r.get('bh_net_return_eur'))} | "
            f"{_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (Mid RSI MR 4H):**")
    lines.append(
        f"- windows with exp>0: **{ms.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{ms.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(ms.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(ms.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(ms.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(ms.get('worst_dd_eur'))}**")
    lines.append("")
    lines.append(
        f"### Soft promote (Mid RSI MR): **{soft.get('verdict', '—')}** (`{SOFT_PROMOTE_GATE}`)"
    )
    lines.append("")
    lines.append(
        f"- median_trades={_fmt(soft.get('median_trades'), 1)} "
        f"(ok={soft.get('median_trades_ok')}, min>={soft.get('median_trades_min')})"
    )
    lines.append(
        f"- exp>0: {soft.get('n_expectancy_gt_0')}/7 "
        f"(need ≥{soft.get('n_expectancy_gt_0_required')}; ok={soft.get('expectancy_gt_0_ok')})"
    )
    lines.append(
        f"- panel_net €={_fmt(soft.get('panel_net_eur'))} (ok={soft.get('panel_net_ok')})"
    )
    lines.append(f"- note: {SOFT_PROMOTE_NOTE}")
    lines.append("")
    lines.append(f"### Honesty label vs Breakout #65: **{honesty_label}**")
    lines.append("")
    lines.append("### Honesty deltas vs Mid Breakout #65 baseline (RSI MR − Breakout)")
    lines.append("")
    lines.append(
        "| Metric | Mid Breakout 4H €40 (#65) | Mid RSI MR 4H €40 | Δ |"
    )
    lines.append("|--------|--------------------------:|------------------:|--:|")
    lines.append(
        f"| median exp € | {_fmt((deltas.get('median_expectancy_eur') or {}).get('baseline'))} | "
        f"{_fmt((deltas.get('median_expectancy_eur') or {}).get('improve'))} | "
        f"{_fmt((deltas.get('median_expectancy_eur') or {}).get('delta'))} |"
    )
    lines.append(
        f"| panel net € | {_fmt((deltas.get('panel_net_eur') or {}).get('baseline'))} | "
        f"{_fmt((deltas.get('panel_net_eur') or {}).get('improve'))} | "
        f"{_fmt((deltas.get('panel_net_eur') or {}).get('delta'))} |"
    )
    lines.append(
        f"| median_trades | {_fmt((deltas.get('median_trades') or {}).get('baseline'), 1)} | "
        f"{_fmt((deltas.get('median_trades') or {}).get('improve'), 1)} | "
        f"{_fmt((deltas.get('median_trades') or {}).get('delta'), 1)} |"
    )
    lines.append(
        f"| n exp>0 / 7 | {(deltas.get('n_exp_gt_0') or {}).get('baseline')} | "
        f"{(deltas.get('n_exp_gt_0') or {}).get('improve')} | "
        f"{(deltas.get('n_exp_gt_0') or {}).get('delta')} |"
    )
    lines.append(
        f"| soft promote | {soft_b.get('verdict', '—')} | **{soft.get('verdict', '—')}** | — |"
    )
    lines.append("")
    lines.append("### Honesty deltas vs EMA Mid archive (optional; RSI MR − EMA)")
    lines.append("")
    lines.append(
        "| Metric | Mid EMA 4H €40 (archive) | Mid RSI MR 4H €40 | Δ |"
    )
    lines.append("|--------|-------------------------:|------------------:|--:|")
    lines.append(
        f"| median exp € | {_fmt((deltas_ema.get('median_expectancy_eur') or {}).get('ema_archive'))} | "
        f"{_fmt((deltas_ema.get('median_expectancy_eur') or {}).get('improve'))} | "
        f"{_fmt((deltas_ema.get('median_expectancy_eur') or {}).get('delta'))} |"
    )
    lines.append(
        f"| panel net € | {_fmt((deltas_ema.get('panel_net_eur') or {}).get('ema_archive'))} | "
        f"{_fmt((deltas_ema.get('panel_net_eur') or {}).get('improve'))} | "
        f"{_fmt((deltas_ema.get('panel_net_eur') or {}).get('delta'))} |"
    )
    lines.append(
        f"| median_trades | {_fmt((deltas_ema.get('median_trades') or {}).get('ema_archive'), 1)} | "
        f"{_fmt((deltas_ema.get('median_trades') or {}).get('improve'), 1)} | "
        f"{_fmt((deltas_ema.get('median_trades') or {}).get('delta'), 1)} |"
    )
    lines.append(
        f"| n exp>0 / 7 | {(deltas_ema.get('n_exp_gt_0') or {}).get('ema_archive')} | "
        f"{(deltas_ema.get('n_exp_gt_0') or {}).get('improve')} | "
        f"{(deltas_ema.get('n_exp_gt_0') or {}).get('delta')} |"
    )
    lines.append("| soft promote | PASS (archive) | "
                 f"**{soft.get('verdict', '—')}** | — |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## E. Cascade / Core+Mid book")
    lines.append("")
    if promote_as_better and core_mid_book is not None:
        nets = core_mid_book.get("panel_sleeve_nets_eur") or {}
        vs = core_mid_book.get("vs_65_core_mid_breakout") or {}
        lines.append(
            "Bot cascade/arming path = **Core + Mid only**. Scalp = Kaje manual — "
            "**no Scalp sleeve**. Book start **€180** (Core €140 + Mid €40). "
            "PASS **and** panel_net better than Breakout → cascade recorded."
        )
        lines.append("")
        lines.append(f"- **book_id:** `{CORE_MID_BOOK_ID}`")
        lines.append(f"- **book_start_eur:** **{int(CORE_MID_BOOK_EUR)}**")
        lines.append(f"- **core_id:** `{BASELINE_ID}` (1D EMA12/30)")
        lines.append(f"- **mid_id:** `{MID_IMPROVE_ID}` (4H RSI14 MR)")
        lines.append("- **scalp:** none (`no_scalp=true`)")
        lines.append(
            f"- per-sleeve panel net: Core **{_fmt(nets.get('core'))}** · "
            f"Mid **{_fmt(nets.get('mid'))}** · Core+Mid **{_fmt(nets.get('combined_core_mid'))}** €"
        )
        lines.append("")
        lines.append("### Honesty Δ vs Breakout Core+Mid (#65)")
        lines.append("")
        lines.append("| Sleeve | #65 Core+Mid (Breakout Mid) | #66 Core+Mid (this Mid) | Δ |")
        lines.append("|--------|----------------------------:|------------------------:|--:|")
        lines.append(
            f"| Core | {_fmt(vs.get('core_65'))} | {_fmt(nets.get('core'))} | "
            f"{_fmt(vs.get('core_delta'))} |"
        )
        lines.append(
            f"| Mid | {_fmt(vs.get('mid_65'))} | {_fmt(nets.get('mid'))} | "
            f"{_fmt(vs.get('mid_delta'))} |"
        )
        lines.append(
            f"| Core+Mid | {_fmt(vs.get('combined_65'))} | {_fmt(nets.get('combined_core_mid'))} | "
            f"{_fmt(vs.get('combined_delta'))} |"
        )
        lines.append("")
        lines.append("Reports: `data/reports/rise_panel_v1_core_mid_book_mid_rsi_mr_66.json`")
    elif soft_pass and not panel_better:
        lines.append(
            f"**No promote claim.** Soft {honesty_label} vs Breakout — cascade skipped "
            "(optional informational only; not run as promote path)."
        )
        if core_mid_book is not None:
            nets = core_mid_book.get("panel_sleeve_nets_eur") or {}
            vs = core_mid_book.get("vs_65_core_mid_breakout") or {}
            lines.append("")
            lines.append(
                f"Informational Core+Mid (force): combined **{_fmt(nets.get('combined_core_mid'))}** € "
                f"(Δ vs Breakout Core+Mid {_fmt(vs.get('combined_delta'))})."
            )
            lines.append("Reports: `data/reports/rise_panel_v1_core_mid_book_mid_rsi_mr_66.json`")
    else:
        lines.append(
            "**FAIL** soft_promote — no promote claim; cascade skipped."
        )
        if core_mid_book is not None:
            nets = core_mid_book.get("panel_sleeve_nets_eur") or {}
            lines.append(
                f"Informational Core+Mid only: combined **{_fmt(nets.get('combined_core_mid'))}** €."
            )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not an RSI period / threshold / TF / cost grind.")
    lines.append("- Not an EMA filter / period grind (EMA Mid is archive only).")
    lines.append("- Not BreakoutV1 (#65) or Donchian 20/10 (#64).")
    lines.append("- Not Mid #43 1D level-entry RSI (this is Scalp #59 cross-up / exit≥70 on 4H).")
    lines.append("- Not a change to R1–R7 window dates (phase1/54 lock).")
    lines.append("- Not a rewrite of `core_style_return` A∧B on phase1/38.")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.")
    lines.append("- Not a Scalp sleeve (bot path Core+Mid only).")
    lines.append("- Not a claim that past rise windows forecast the next bull.")
    lines.append("")
    lines.append("`not_a_forecast: true`. `place_orders: false`.")
    lines.append("")
    # silence unused
    _ = (RISE_PANEL_V1, promote_as_better)
    return "\n".join(lines)
