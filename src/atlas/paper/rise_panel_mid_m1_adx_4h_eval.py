"""rise_panel_v1 Mid M1 — #71 BreakoutV1+EMA12/21 4H €40 PLUS ADX(14)>20.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
soft_promote_v1 vs Mid #71 baseline. Soft PASS ≠ Mid-arm. Live ≤€20 HALTED.
Doc: phase1/86-rise-panel-mid-m1-adx-4h.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import MID_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    MID_BAR_CANDIDATE,
    MID_BASELINE_ID,
    MID_BASELINE_PANEL_NET_EUR,
    PANEL_LABEL,
    RiseWindow,
    SOFT_PROMOTE_GATE,
    SOFT_PROMOTE_NOTE,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
)
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import Bar, q
from atlas.strategy.mid_doge_breakout_ema1221_4h import (
    FAMILY as M0_FAMILY,
    MidDogeBreakoutEma1221V1,
)
from atlas.strategy.mid_doge_breakout_ema1221_adx_4h import (
    ADX_GATE,
    ADX_PERIOD_LOCKED,
    ATR_PERIOD,
    BAR,
    EMA_FAST,
    EMA_SLOW,
    FAMILY,
    LOOKBACK,
    MIN_ATR_FRAC,
    MidDogeBreakoutEma1221AdxV1,
)

SOURCE = "rise_panel_v1_mid_m1_adx_86"
WARMUP_PAD_4H_DAYS = 10

MID_M0_ID = MID_BASELINE_ID  # #71
MID_M1_ID = "rise_panel_v1_mid_doge_breakoutv1_ema1221_adx14_gt20_4h_eur40"

MID_71_SNAPSHOT = {
    "median_trades": 7.0,
    "n_exp_gt_0": 5,
    "panel_net_eur": MID_BASELINE_PANEL_NET_EUR,
    "median_expectancy_eur": 2.1531,
    "worst_dd_eur": 21.8963,
    "verdict": "PASS",
    "note": "phase1/72 Mid #71 — formal Mid baseline (M0)",
}


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
        "win_rate": walk.get("win_rate"),
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

    soft = soft_promote_score(rows)
    summary = panel_summary_table(rows)
    return {
        "ok": all(r.get("ok") for r in rows),
        "candidate_id": candidate_id,
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
        "soft_promote_gate": SOFT_PROMOTE_GATE,
        "soft_promote_note": SOFT_PROMOTE_NOTE,
        "soft_promote": soft,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
        "soft_pass_ne_arm": True,
        "live_assume_eur_cap": 20.0,
        "mid_scalp_halted": True,
    }


def run_mid_m0_baseline(
    cfg: Any, *, data_dir: Path, pause_s: float = 0.12, rest_base: str = OKX_REST
) -> dict[str, Any]:
    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=lambda: MidDogeBreakoutEma1221V1(),
        arm="mid_breakout_ema1221_4h_m0",
        candidate_id=MID_M0_ID,
        strategy_label=f"breakoutv1_lb{LOOKBACK}_ema{EMA_FAST}_{EMA_SLOW}_long_regime",
        family=M0_FAMILY,
        pause_s=pause_s,
        rest_base=rest_base,
    )
    out["role"] = "mid_m0_baseline"
    out["mid_baseline_id"] = MID_M0_ID
    return out


def run_mid_m1_adx(
    cfg: Any, *, data_dir: Path, pause_s: float = 0.12, rest_base: str = OKX_REST
) -> dict[str, Any]:
    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=lambda: MidDogeBreakoutEma1221AdxV1(),
        arm="mid_breakout_ema1221_adx14_gt20_4h_m1",
        candidate_id=MID_M1_ID,
        strategy_label=(
            f"breakoutv1_lb{LOOKBACK}_atr{ATR_PERIOD}_ema{EMA_FAST}_{EMA_SLOW}"
            f"_adx{ADX_PERIOD_LOCKED}_gt{int(ADX_GATE)}_long_regime"
        ),
        family=FAMILY,
        pause_s=pause_s,
        rest_base=rest_base,
    )
    out["role"] = "mid_m1"
    out["mid_improve_id"] = MID_M1_ID
    out["compare_to_mid_baseline"] = MID_M0_ID
    out["adx_period"] = ADX_PERIOD_LOCKED
    out["adx_gate"] = ADX_GATE
    out["min_atr_frac"] = MIN_ATR_FRAC
    return out


def deltas_vs_mid_m0(baseline: dict[str, Any], improve: dict[str, Any]) -> dict[str, Any]:
    b = baseline.get("summary") or {}
    i = improve.get("summary") or {}

    def _d(key: str) -> float | None:
        bv, iv = b.get(key), i.get(key)
        if bv is None or iv is None:
            return None
        return q(float(iv) - float(bv))

    panel_delta = _d("panel_net_eur")
    promote_as_better = bool(
        panel_delta is not None
        and panel_delta > 0
        and str((improve.get("soft_promote") or {}).get("verdict", "")).upper() == "PASS"
    )
    honesty = "FAIL"
    soft_pass = str((improve.get("soft_promote") or {}).get("verdict", "")).upper() == "PASS"
    if soft_pass and promote_as_better:
        honesty = "PASS-and-better"
    elif soft_pass:
        honesty = "PASS-but-worse" if (panel_delta is not None and panel_delta <= 0) else "PASS"
    return {
        "compare_to": MID_M0_ID,
        "improve_id": MID_M1_ID,
        "median_expectancy_eur": {
            "ref": b.get("median_expectancy_eur"),
            "improve": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur"),
        },
        "panel_net_eur": {
            "ref": b.get("panel_net_eur"),
            "improve": i.get("panel_net_eur"),
            "delta": panel_delta,
        },
        "median_trades": {
            "ref": b.get("median_trades"),
            "improve": i.get("median_trades"),
            "delta": _d("median_trades"),
        },
        "n_exp_gt_0": {
            "ref": b.get("n_exp_gt_0"),
            "improve": i.get("n_exp_gt_0"),
            "delta": (
                None
                if b.get("n_exp_gt_0") is None or i.get("n_exp_gt_0") is None
                else int(i["n_exp_gt_0"]) - int(b["n_exp_gt_0"])
            ),
        },
        "promote_as_better": promote_as_better,
        "honesty_label": honesty,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_ne_arm": True,
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
) -> str:
    if deltas is None:
        deltas = deltas_vs_mid_m0(baseline, improve)
    soft = improve.get("soft_promote") or {}
    bs = baseline.get("summary") or {}
    ms = improve.get("summary") or {}
    soft_b = baseline.get("soft_promote") or {}
    verdict = soft.get("verdict", "—")
    honesty = deltas.get("honesty_label", "—")
    lines: list[str] = []
    lines.append("# 86 — rise_panel_v1 Mid **M1**: #71 + **ADX(14)>20** 4H €40")
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20 **HALTED**; Mid/Scalp **HALTED**; Soft PASS ≠ Mid-arm. "
        "Plan: [`84-atlas-trading-vnext.md`](./84-atlas-trading-vnext.md)."
    )
    lines.append(
        "**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change)."
    )
    lines.append(
        "**Compare:** Mid M0=#71 [`72-mid-long-strengthen.md`](./72-mid-long-strengthen.md). "
        "**No** ADX/EMA/lookback grind. Branch: `research/atlas-trading-vnext-84`."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Soft promote gate (LOCKED — same as #54)")
    lines.append("")
    lines.append("`soft_promote_v1`: median_trades≥1 AND ≥5/7 exp>0 AND panel_net>0.")
    lines.append("Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED Mid M0 baseline (#71)")
    lines.append("")
    lines.append(f"**mid_m0_id:** `{MID_M0_ID}`")
    lines.append("")
    lines.append("### M0 per window (re-scored)")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in baseline.get("rows") or []:
        lines.append(
            f"| {r.get('window_id', '?')} | {r.get('n_trades', 0)} | "
            f"{_fmt(r.get('expectancy_after_costs_eur'))} | {_fmt(r.get('net_return_eur'))} | "
            f"{_fmt(r.get('max_dd_eur'))} | {_fmt(r.get('time_in_market'))} | "
            f"{_fmt(r.get('bh_net_return_eur'))} | {_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (Mid M0 #71 re-score):**")
    lines.append(
        f"- windows with exp>0: **{bs.get('n_exp_gt_0')}**/7 · net>0: **{bs.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(bs.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(bs.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(bs.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(bs.get('worst_dd_eur'))}**")
    lines.append(f"- soft_promote: **{soft_b.get('verdict', '—')}** (`{SOFT_PROMOTE_GATE}`)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. LOCKED Mid M1 family (BEFORE scoring)")
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**mid_m1_id:** `{MID_M1_ID}`  ")
    lines.append(f"**compare_to:** `{MID_M0_ID}`")
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append("- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**.")
    lines.append(
        f"- BreakoutV1 lookback **{LOOKBACK}** + ATR quiet + EMA**{EMA_FAST}**/**{EMA_SLOW}** "
        f"(same as #71)."
    )
    lines.append(
        f"- **ADX gate (locked once):** Wilder **ADX({ADX_PERIOD_LOCKED}) > {int(ADX_GATE)}**."
    )
    lines.append(
        "- **Long entry:** BreakoutV1 break-up + ATR quiet **AND** EMA12>EMA21 **AND** ADX>20."
    )
    lines.append(
        "- **Flat/exit:** channel exit **OR** EMA12≤EMA21 **OR** ADX≤20. Never short."
    )
    lines.append("- Fill: next-open. Size: Mid €40. Costs: 5+5 bps.")
    lines.append("- **No** ADX threshold / period / EMA / lookback / TF grind on FAIL.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_mid_m1_adx_4h_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_mid_m1_adx_4h_eval`")
    lines.append("- Strategy: `atlas.strategy.mid_doge_breakout_ema1221_adx_4h`")
    lines.append("- Unit tests: `tests/unit/test_rise_panel_mid_m1_adx_4h.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Mid M1 ADX on same 7")
    lines.append("")
    lines.append(f"**mid_m1_id:** `{MID_M1_ID}`")
    lines.append("")
    lines.append("### M1 per window")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in improve.get("rows") or []:
        lines.append(
            f"| {r.get('window_id', '?')} | {r.get('n_trades', 0)} | "
            f"{_fmt(r.get('expectancy_after_costs_eur'))} | {_fmt(r.get('net_return_eur'))} | "
            f"{_fmt(r.get('max_dd_eur'))} | {_fmt(r.get('time_in_market'))} | "
            f"{_fmt(r.get('bh_net_return_eur'))} | {_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (Mid M1):**")
    lines.append(
        f"- windows with exp>0: **{ms.get('n_exp_gt_0')}**/7 · net>0: **{ms.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(ms.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(ms.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(ms.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(ms.get('worst_dd_eur'))}**")
    lines.append("")
    lines.append(f"### Soft promote (Mid M1): **{verdict}** (`{SOFT_PROMOTE_GATE}`)")
    lines.append("")
    lines.append(
        f"- median_trades={_fmt(ms.get('median_trades'), 1)} "
        f"(ok={soft.get('median_trades_ok')}, min>=1)"
    )
    lines.append(
        f"- exp>0: {ms.get('n_exp_gt_0')}/7 (need ≥5; ok={soft.get('expectancy_gt_0_ok')})"
    )
    lines.append(f"- panel_net €={_fmt(ms.get('panel_net_eur'))} (ok={soft.get('panel_net_ok')})")
    lines.append(f"- note: {soft.get('gate_note') or SOFT_PROMOTE_NOTE}")
    lines.append("")
    lines.append(f"### Honesty label vs Mid #71 (M0): **{honesty}**")
    lines.append("")
    lines.append("### Honesty deltas vs Mid M0 #71 (M1 − M0)")
    lines.append("")
    lines.append("| Metric | Mid M0 #71 €40 | Mid M1 ADX €40 | Δ |")
    lines.append("|--------|---------------:|---------------:|--:|")
    for key, label in (
        ("median_expectancy_eur", "median exp €"),
        ("panel_net_eur", "panel net €"),
        ("median_trades", "median_trades"),
        ("n_exp_gt_0", "n exp>0 / 7"),
    ):
        block = deltas.get(key) or {}
        lines.append(
            f"| {label} | {_fmt(block.get('ref'))} | {_fmt(block.get('improve'))} | "
            f"{_fmt(block.get('delta'))} |"
        )
    lines.append(
        f"| soft promote | {soft_b.get('verdict', '—')} | **{verdict}** | — |"
    )
    lines.append(f"| honesty | — | **{honesty}** | promote_as_better={deltas.get('promote_as_better')} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## E. Soft PASS ≠ arm")
    lines.append("")
    lines.append(
        f"soft_promote **{verdict}**. Paper only. **Soft PASS ≠ Mid-arm**. "
        "Mid/Scalp HALTED. Live ≤€20. `not_a_forecast: true`. `place_orders: false`."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


__all__ = [
    "MID_M0_ID",
    "MID_M1_ID",
    "MID_71_SNAPSHOT",
    "deltas_vs_mid_m0",
    "render_results_markdown",
    "run_mid_m0_baseline",
    "run_mid_m1_adx",
    "write_report_json",
]
