"""rise_panel_v1 Mid #72 — RISK-UP: same BreakoutV1+EMA12/21 4H rules as #71, Mid €60.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Same rules as #71 (BreakoutV1 4H + EMA12/21 long-regime); Mid sleeve **€60** (1.5× €40).
Gate soft_promote_v1. Honesty vs #71 @ €40: expect ~1.5× panel if linear —
report Δ panel, expectancy_after_costs, DD — not just bigger €.
On PASS: Core €140 + Mid €60 (book €200). Soft PASS ≠ Mid-arm. Live ≤€20.
Doc: phase1/73-mid-sleeve-riskup.md
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
    MID_BASELINE_CORE_MID_PANEL_NET_EUR,
    MID_BASELINE_ID,
    MID_BASELINE_PANEL_NET_EUR,
    MID_BREAKOUT_ARCHIVE_ID,
    MID_BREAKOUT_ARCHIVE_PANEL_NET_EUR,
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
from atlas.strategy.mid_doge_breakout_ema1221_4h import (
    ATR_PERIOD,
    BAR,
    EMA_FAST,
    EMA_SLOW,
    FAMILY,
    LOOKBACK,
    MIN_ATR_FRAC,
    MidDogeBreakoutEma1221V1,
)

FAST = EMA_FAST
SLOW = EMA_SLOW

SOURCE = "rise_panel_v1_mid_sleeve_riskup_72"
WARMUP_PAD_4H_DAYS = 10

# #71 is NEW formal Mid baseline (promote). #65 Breakout = archive only.
MID_71_BASELINE_ID = MID_BASELINE_ID  # rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40
MID_RISKUP_ID = "rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur60"
MID_SLEEVE_EUR40 = MID_START_EUR  # 40.0 — #71 sleeve
MID_SLEEVE_EUR60 = 60.0  # 1.5× €40 risk-up
SIZE_MULT = MID_SLEEVE_EUR60 / MID_SLEEVE_EUR40  # 1.5
CORE_MID_BOOK_EUR = CORE_START_EUR + MID_SLEEVE_EUR60  # 200
CORE_MID_BOOK_ID = "rise_panel_v1_core_mid_book_200_mid_breakout_ema1221_eur60"

CORE_55_PANEL_NET = 363.9983
MID_71_PANEL_NET = MID_BASELINE_PANEL_NET_EUR  # ≈97.2663
CORE_MID_71_PANEL_NET = MID_BASELINE_CORE_MID_PANEL_NET_EUR  # ≈461.2647
MID_65_ARCHIVE_PANEL_NET = MID_BREAKOUT_ARCHIVE_PANEL_NET_EUR  # ≈95.4483

MID_71_SNAPSHOT = {
    "median_trades": 7.0,
    "n_exp_gt_0": 5,
    "panel_net_eur": 97.2663,
    "median_expectancy_eur": 2.1531,
    "worst_dd_eur": 21.8963,
    "verdict": "PASS",
    "note": "phase1/72 Mid #71 BreakoutV1+EMA12/21 4H €40 — NEW formal Mid baseline (Kaje promote)",
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
    sleeve_eur: float,
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
                equity=float(sleeve_eur),
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
        "mid_baseline_id": MID_71_BASELINE_ID,
        "mid_breakout_archive_id": MID_BREAKOUT_ARCHIVE_ID,
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": BAR,
        "family": family,
        "strategy": strategy_label,
        "sleeve_eur": float(sleeve_eur),
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
        "compare_to_mid_baseline": MID_71_BASELINE_ID,
        "ema_fast": FAST,
        "ema_slow": SLOW,
        "daily_bull": False,
        "rsi_filter": False,
        "size_up": True,
        "size_mult_vs_mid40": SIZE_MULT,
    }
    if soft is not None:
        out["soft_promote_gate"] = SOFT_PROMOTE_GATE
        out["soft_promote_note"] = SOFT_PROMOTE_NOTE
        out["soft_promote"] = soft
    return out


def run_mid_71_baseline_eur40(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Re-score NEW Mid formal baseline #71 Breakout+EMA1221 4H on rise_panel_v1 (€40)."""

    def factory() -> MidDogeBreakoutEma1221V1:
        return MidDogeBreakoutEma1221V1()

    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=factory,
        arm="mid_breakout_ema1221_4h_eur40",
        candidate_id=MID_71_BASELINE_ID,
        strategy_label=(
            f"breakoutv1_lb{LOOKBACK}_atr{ATR_PERIOD}_ema{EMA_FAST}_{EMA_SLOW}_long_regime"
        ),
        family=FAMILY,
        sleeve_eur=MID_SLEEVE_EUR40,
        pause_s=pause_s,
        rest_base=rest_base,
        apply_soft_promote=True,
    )
    out["role"] = "mid_baseline"
    out["mid_baseline_id"] = MID_71_BASELINE_ID
    out["promote_note"] = (
        "NEW formal Mid baseline after #71 soft PASS promote (Kaje lock). "
        "#65 Breakout = archive only."
    )
    return out


def run_mid_riskup_eur60(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Mid #72 RISK-UP: same #71 rules, Mid sleeve €60 (1.5×)."""

    def factory() -> MidDogeBreakoutEma1221V1:
        return MidDogeBreakoutEma1221V1()

    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=factory,
        arm="mid_breakout_ema1221_4h_eur60",
        candidate_id=MID_RISKUP_ID,
        strategy_label=(
            f"breakoutv1_lb{LOOKBACK}_atr{ATR_PERIOD}_ema{EMA_FAST}_{EMA_SLOW}_long_regime_eur60"
        ),
        family=FAMILY,
        sleeve_eur=MID_SLEEVE_EUR60,
        pause_s=pause_s,
        rest_base=rest_base,
        apply_soft_promote=True,
    )
    out["role"] = "mid_riskup"
    out["mid_riskup_id"] = MID_RISKUP_ID
    out["family"] = FAMILY
    out["ema_fast"] = EMA_FAST
    out["ema_slow"] = EMA_SLOW
    out["lookback"] = LOOKBACK
    out["atr_period"] = ATR_PERIOD
    out["min_atr_frac"] = MIN_ATR_FRAC
    out["reuse_note"] = (
        "Same MidDogeBreakoutEma1221V1 rules as #71; Mid sleeve €60 = 1.5× €40. "
        "Not a rule change. Not RSI. Soft PASS ≠ Mid-arm."
    )
    return out


def deltas_vs_mid_71(baseline: dict[str, Any], riskup: dict[str, Any]) -> dict[str, Any]:
    """Panel metric deltas: Mid €60 risk-up − Mid #71 €40 (NOT vs Core)."""
    b = baseline.get("summary") or {}
    i = riskup.get("summary") or {}

    def _d(key: str) -> float | None:
        bv, iv = b.get(key), i.get(key)
        if bv is None or iv is None:
            return None
        return q(float(iv) - float(bv))

    d_net = _d("panel_net_eur")
    b_net = b.get("panel_net_eur")
    i_net = i.get("panel_net_eur")
    b_exp = b.get("median_expectancy_eur")
    i_exp = i.get("median_expectancy_eur")
    b_dd = b.get("worst_dd_eur")
    i_dd = i.get("worst_dd_eur")

    linear_panel = q(float(b_net) * SIZE_MULT) if b_net is not None else None
    linear_exp = q(float(b_exp) * SIZE_MULT) if b_exp is not None else None
    linear_dd = q(float(b_dd) * SIZE_MULT) if b_dd is not None else None
    panel_ratio_vs_linear = (
        q(float(i_net) / float(linear_panel))
        if i_net is not None and linear_panel not in (None, 0, 0.0)
        else None
    )
    exp_ratio_vs_linear = (
        q(float(i_exp) / float(linear_exp))
        if i_exp is not None and linear_exp not in (None, 0, 0.0)
        else None
    )
    dd_ratio_vs_linear = (
        q(float(i_dd) / float(linear_dd))
        if i_dd is not None and linear_dd not in (None, 0, 0.0)
        else None
    )

    # Bigger € alone is expected from size — promote-as-better requires soft PASS
    # AND panel at/above linear expectation (not just > #71 €40 panel).
    promote_as_better = (
        d_net is not None
        and float(d_net) > 0
        and panel_ratio_vs_linear is not None
        and float(panel_ratio_vs_linear) >= 0.95  # within ~5% of linear
    )
    return {
        "compare_to": MID_71_BASELINE_ID,
        "riskup_id": MID_RISKUP_ID,
        "size_mult": SIZE_MULT,
        "median_expectancy_eur": {
            "baseline_eur40": b.get("median_expectancy_eur"),
            "riskup_eur60": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur"),
            "linear_1_5x": linear_exp,
            "ratio_vs_linear": exp_ratio_vs_linear,
        },
        "panel_net_eur": {
            "baseline_eur40": b.get("panel_net_eur"),
            "riskup_eur60": i.get("panel_net_eur"),
            "delta": d_net,
            "linear_1_5x": linear_panel,
            "ratio_vs_linear": panel_ratio_vs_linear,
        },
        "worst_dd_eur": {
            "baseline_eur40": b.get("worst_dd_eur"),
            "riskup_eur60": i.get("worst_dd_eur"),
            "delta": _d("worst_dd_eur"),
            "linear_1_5x": linear_dd,
            "ratio_vs_linear": dd_ratio_vs_linear,
        },
        "median_trades": {
            "baseline_eur40": b.get("median_trades"),
            "riskup_eur60": i.get("median_trades"),
            "delta": _d("median_trades"),
        },
        "n_exp_gt_0": {
            "baseline_eur40": b.get("n_exp_gt_0"),
            "riskup_eur60": i.get("n_exp_gt_0"),
            "delta": (
                None
                if b.get("n_exp_gt_0") is None or i.get("n_exp_gt_0") is None
                else int(i["n_exp_gt_0"]) - int(b["n_exp_gt_0"])
            ),
        },
        "promote_as_better": promote_as_better,
        "honesty_rule": (
            "expect ~1.5× panel / expectancy / DD if linear; report Δ and ratios — "
            "not just bigger €. Soft PASS ≠ Mid-arm."
        ),
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_core_mid_book_200(
    cfg: Any,
    *,
    data_dir: Path,
    mid_bundle: dict[str, Any],
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
    force: bool = False,
) -> dict[str, Any]:
    """Core €140 1D EMA + this Mid €60 Breakout+EMA1221 — book €200, NO Scalp sleeve.

    Cascade book when soft PASS (or force). Honest Δ vs prior Core+Mid Mid€40 ≈€461.26.
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
        "mid_id": MID_RISKUP_ID,
        "scalp": None,
        "no_scalp": True,
        "force_informational": force,
        "note": (
            "Core+Mid only (bot cascade/arming path). Scalp = Kaje manual — "
            "no Scalp sleeve invented. Independent sleeve panel nets summed. "
            "Book €200 = Core €140 + Mid €60 (risk-up)."
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
            "sleeve_eur": MID_SLEEVE_EUR60,
        },
        "panel_sleeve_nets_eur": {
            "core": q(core_net),
            "mid": q(mid_net),
            "combined_core_mid": combined,
        },
        "vs_71_core_mid_eur40": {
            "core_71": CORE_55_PANEL_NET,
            "mid_71": MID_71_PANEL_NET,
            "combined_71": CORE_MID_71_PANEL_NET,
            "core_delta": q(core_net - CORE_55_PANEL_NET),
            "mid_delta": q(mid_net - MID_71_PANEL_NET),
            "combined_delta": q(combined - CORE_MID_71_PANEL_NET),
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
    riskup: dict[str, Any],
    *,
    deltas: dict[str, Any] | None = None,
    core_mid_book: dict[str, Any] | None = None,
) -> str:
    """Full phase1/73 doc with lock + scored results (+ Core+Mid €200 book if PASS)."""
    if deltas is None:
        deltas = deltas_vs_mid_71(baseline, riskup)
    soft = riskup.get("soft_promote") or {}
    soft_pass = str(soft.get("verdict", "")).upper() == "PASS"
    bs = baseline.get("summary") or {}
    ms = riskup.get("summary") or {}
    soft_b = baseline.get("soft_promote") or bs.get("soft_promote") or {}
    d_net = (deltas.get("panel_net_eur") or {}).get("delta")
    ratio = (deltas.get("panel_net_eur") or {}).get("ratio_vs_linear")
    panel_better = bool(deltas.get("promote_as_better"))
    if soft_pass and panel_better:
        honesty_label = "PASS-and-near-linear (promote-as-better eligible)"
    elif soft_pass and d_net is not None and float(d_net) > 0:
        honesty_label = "PASS-but-sublinear (bigger € expected; quality/ratio honesty)"
    elif soft_pass:
        honesty_label = "PASS (panel_net not larger than #71 — unexpected for 1.5× size)"
    else:
        honesty_label = "FAIL"

    lines: list[str] = []
    lines.append(
        "# 73 — Mid #72 sleeve RISK-UP: DOGE **4H BreakoutV1 + EMA12/21** (€60)"
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
        "**Parent sleeves (book):** Core €140 / Mid **€60** risk-up / Scalp €20 reserved "
        "(bot path still Core+Mid only — Scalp = Kaje manual)."
    )
    lines.append(
        "**Compare:** Mid #71 baseline [`72-mid-long-strengthen.md`](./72-mid-long-strengthen.md) "
        "/ promote [`72b-mid-breakout-ema1221-promote.md`](./72b-mid-breakout-ema1221-promote.md). "
        "Gate soft_promote_v1 vs #71 @ €40. **Same rules** as #71; Mid sleeve **€60** (1.5×). "
        "Breakout #65 = **archive only**."
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
        "**Honesty vs #71 €40:** expect ~**1.5×** panel / expectancy / DD if linear; "
        "report Δ and ratios — **not** just bigger €."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED Mid baseline (#71 — compare target)")
    lines.append("")
    lines.append(f"**mid_baseline_id:** `{MID_71_BASELINE_ID}`  ")
    lines.append(
        "(soft_promote **PASS**, promoted #71 — see [`72b-mid-breakout-ema1221-promote.md`]"
        "(./72b-mid-breakout-ema1221-promote.md))"
    )
    lines.append("")
    lines.append(
        "- Rule: BreakoutV1 lookback 16 + ATR quiet + EMA12>EMA21 long-regime. Never short."
    )
    lines.append("- Bar: DOGE-USDT **4H**. Sleeve: Mid **€40** (baseline).")
    lines.append(
        "- Compare target for this trial: **Mid €60 vs Mid #71 €40** (NOT vs Core €140)."
    )
    lines.append(
        f"- Snapshot (#71): panel_net≈**€{_fmt(MID_71_SNAPSHOT['panel_net_eur'])}** · "
        f"median_trades=**{_fmt(MID_71_SNAPSHOT['median_trades'], 1)}** · "
        f"exp>0 **{MID_71_SNAPSHOT['n_exp_gt_0']}**/7 · "
        f"worst DD≈**€{_fmt(MID_71_SNAPSHOT['worst_dd_eur'])}**."
    )
    lines.append(
        f"- Breakout #65 archive (`{MID_BREAKOUT_ARCHIVE_ID}`): "
        f"panel_net≈**€{_fmt(MID_65_ARCHIVE_PANEL_NET)}** — **not** current Mid baseline."
    )
    lines.append("")
    lines.append("### Mid #71 €40 baseline per window (re-scored)")
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
    lines.append("**Panel summary (Mid #71 €40 baseline):**")
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
        "**ONE family only — NOT grinding lookback / EMA / ATR / TF / costs. No RSI. "
        "Only sleeve size change €40→€60. Same BreakoutV1 + EMA12/21 long-regime as #71.**"
    )
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**mid_riskup_id:** `{MID_RISKUP_ID}`  ")
    lines.append(f"**compare_to:** `{MID_71_BASELINE_ID}` (primary); archive `{MID_BREAKOUT_ARCHIVE_ID}`")
    lines.append(
        f"**Canonical:** BreakoutV1 lookback **{LOOKBACK}** + ATR quiet, gated by "
        f"EMA(**{FAST}**/**{SLOW}**). Decision bar **4H**. **No** RSI. Mid **€60** = 1.5× #71 €40."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append("- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.")
    lines.append(
        f"- BreakoutV1: lookback **{LOOKBACK}**, ATR SMA **{ATR_PERIOD}**, "
        f"min_atr_frac **{MIN_ATR_FRAC}** (same as #71/#65)."
    )
    lines.append(f"- EMA long-regime: fast **{FAST}** / slow **{SLOW}** (NOT 12/30).")
    lines.append(
        "- **Long entry:** BreakoutV1 break-up + ATR quiet **AND** EMA12 > EMA21. Long only."
    )
    lines.append(
        "- **Flat/exit:** BreakoutV1 channel exit **OR** EMA12 ≤ EMA21 "
        "(force flat / no new long). Never short."
    )
    lines.append(
        "- **No** RSI. **Size-up only:** Mid sleeve **€60** (was €40). Rules identical to #71."
    )
    lines.append("- `oneh_filter: off` (decision TF is already 4H).")
    lines.append("- Insufficient history → flat. Quiet ATR → no new long.")
    lines.append(
        "- Fill: signal close → next open. Size: full Mid sleeve **€60** when long."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(
        "- **No** lookback / EMA / ATR / TF / cost grind on FAIL. **No** RSI rescue."
    )
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        "Mid #71 BreakoutV1+EMA12/21 4H is the formal Mid baseline (panel≈€97.27). "
        "This trial **risks up the Mid sleeve** to €60 (1.5×) with **identical rules** — "
        "honesty requires linearity check, not celebrating bigger € alone."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_mid_sleeve_riskup_72_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_mid_sleeve_riskup_72_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.mid_doge_breakout_ema1221_4h` "
        "(same as Mid #71; sleeve €60 in harness only)"
    )
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; "
        "Core+Mid book €200 on PASS (no Scalp)"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_mid_sleeve_riskup_72.py`")
    lines.append("- Doc path: `phase1/73-mid-sleeve-riskup.md`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Mid BreakoutV1 + EMA12/21 4H €60 on same 7")
    lines.append("")
    lines.append(f"**mid_riskup_id:** `{MID_RISKUP_ID}`")
    lines.append("")
    lines.append("### Risk-up per window")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in riskup.get("rows") or []:
        wid = r.get("window_id", "?")
        lines.append(
            f"| {wid} | {r.get('n_trades', 0)} | {_fmt(r.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(r.get('net_return_eur'))} | {_fmt(r.get('max_dd_eur'))} | "
            f"{_fmt(r.get('time_in_market'))} | {_fmt(r.get('bh_net_return_eur'))} | "
            f"{_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (Mid Breakout + EMA12/21 4H €60):**")
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
        f"### Soft promote (Mid €60 risk-up): **{soft.get('verdict', '—')}** (`{SOFT_PROMOTE_GATE}`)"
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
    lines.append(f"### Honesty label vs #71 €40: **{honesty_label}**")
    lines.append("")
    lines.append("### Honesty deltas vs Mid #71 €40 (risk-up − baseline) + linearity")
    lines.append("")
    lines.append(
        "| Metric | Mid #71 €40 | Mid #72 €60 | Δ | linear 1.5× | ratio vs linear |"
    )
    lines.append("|--------|------------:|------------:|--:|------------:|----------------:|")
    pn = deltas.get("panel_net_eur") or {}
    ex = deltas.get("median_expectancy_eur") or {}
    dd = deltas.get("worst_dd_eur") or {}
    mt = deltas.get("median_trades") or {}
    ne = deltas.get("n_exp_gt_0") or {}
    lines.append(
        f"| panel net € | {_fmt(pn.get('baseline_eur40'))} | {_fmt(pn.get('riskup_eur60'))} | "
        f"{_fmt(pn.get('delta'))} | {_fmt(pn.get('linear_1_5x'))} | {_fmt(pn.get('ratio_vs_linear'))} |"
    )
    lines.append(
        f"| median exp €/trade | {_fmt(ex.get('baseline_eur40'))} | {_fmt(ex.get('riskup_eur60'))} | "
        f"{_fmt(ex.get('delta'))} | {_fmt(ex.get('linear_1_5x'))} | {_fmt(ex.get('ratio_vs_linear'))} |"
    )
    lines.append(
        f"| worst DD € | {_fmt(dd.get('baseline_eur40'))} | {_fmt(dd.get('riskup_eur60'))} | "
        f"{_fmt(dd.get('delta'))} | {_fmt(dd.get('linear_1_5x'))} | {_fmt(dd.get('ratio_vs_linear'))} |"
    )
    lines.append(
        f"| median_trades | {_fmt(mt.get('baseline_eur40'), 1)} | {_fmt(mt.get('riskup_eur60'), 1)} | "
        f"{_fmt(mt.get('delta'), 1)} | — | — |"
    )
    lines.append(
        f"| n exp>0 / 7 | {ne.get('baseline_eur40')} | {ne.get('riskup_eur60')} | "
        f"{ne.get('delta')} | — | — |"
    )
    lines.append(
        f"| soft promote | {soft_b.get('verdict', '—')} | **{soft.get('verdict', '—')}** | — | — | — |"
    )
    lines.append("")
    lines.append(
        f"Linearity note: size_mult={SIZE_MULT:.1f}×; panel ratio vs linear ≈ **{_fmt(ratio)}** "
        "(1.0 = exact linear)."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## E. Cascade / Core+Mid book")
    lines.append("")

    if soft_pass and core_mid_book is not None:
        nets = core_mid_book.get("panel_sleeve_nets_eur") or {}
        vs = core_mid_book.get("vs_71_core_mid_eur40") or {}
        lines.append(
            "Bot cascade/arming path = **Core + Mid only**. Scalp = Kaje manual — "
            "**no Scalp sleeve**. Book start **€200** (Core €140 + Mid €60). "
            "soft_promote **PASS** → cascade recorded."
        )
        lines.append("")
        lines.append(f"- **book_id:** `{CORE_MID_BOOK_ID}`")
        lines.append(f"- **book_start_eur:** **{int(CORE_MID_BOOK_EUR)}**")
        lines.append(f"- **core_id:** `{BASELINE_ID}` (1D EMA12/30)")
        lines.append(f"- **mid_id:** `{MID_RISKUP_ID}` (4H Breakout+EMA1221 €60)")
        lines.append("- **scalp:** none (`no_scalp=true`)")
        lines.append(
            f"- per-sleeve panel net: Core **{_fmt(nets.get('core'))}** · "
            f"Mid **{_fmt(nets.get('mid'))}** · Core+Mid **{_fmt(nets.get('combined_core_mid'))}** €"
        )
        lines.append("")
        lines.append("### Honesty Δ vs prior Core+Mid with Mid €40 (#71 book ≈€461.26)")
        lines.append("")
        lines.append("| Sleeve | #71 Core+Mid (Mid €40) | #72 Core+Mid (Mid €60) | Δ |")
        lines.append("|--------|-----------------------:|-----------------------:|--:|")
        lines.append(
            f"| Core | {_fmt(vs.get('core_71'))} | {_fmt(nets.get('core'))} | "
            f"{_fmt(vs.get('core_delta'))} |"
        )
        lines.append(
            f"| Mid | {_fmt(vs.get('mid_71'))} | {_fmt(nets.get('mid'))} | "
            f"{_fmt(vs.get('mid_delta'))} |"
        )
        lines.append(
            f"| Core+Mid | {_fmt(vs.get('combined_71'))} | {_fmt(nets.get('combined_core_mid'))} | "
            f"{_fmt(vs.get('combined_delta'))} |"
        )
        lines.append("")
        lines.append("Reports: `data/reports/rise_panel_v1_core_mid_book_mid_breakout_ema1221_72_eur60.json`")
    elif not soft_pass:
        lines.append(
            "**FAIL** soft_promote — no promote claim; cascade skipped."
        )
        if core_mid_book is not None:
            nets = core_mid_book.get("panel_sleeve_nets_eur") or {}
            lines.append(
                f"Informational Core+Mid only: combined **{_fmt(nets.get('combined_core_mid'))}** €."
            )
    else:
        lines.append(
            "soft PASS but Core+Mid book not run (skipped)."
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not a lookback / EMA / ATR / TF / cost grind.")
    lines.append("- Not a rule change vs #71 — **sleeve size only** (€40→€60).")
    lines.append("- Not RSI MR (#66) or plain Breakout #65 (archive) or plain EMA12/21 (#67).")
    lines.append("- Not a claim that bigger € alone proves better edge (linearity honesty required).")
    lines.append("- Not Scalp HFT / Codex lane.")
    lines.append("- Not a change to R1–R7 window dates (phase1/54 lock).")
    lines.append("- Not a rewrite of `core_style_return` A∧B on phase1/38.")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.")
    lines.append("- Not a Scalp sleeve (bot path Core+Mid only).")
    lines.append("- Not a claim that past rise windows forecast the next bull.")
    lines.append("- Not a change to `config/default.yaml`.")
    lines.append("")
    lines.append("`not_a_forecast: true`. `place_orders: false`.")
    lines.append("")
    _ = (RISE_PANEL_V1, honesty_label)
    return "\n".join(lines)
