"""rise_panel_v1 Scalp #63 — DOGE 1H EMA12/21 long/flat €20 vs #55/#57/#61/#62/#59.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Plain EMA12/21 long/flat (NOT 12/30; no RSI; no daily-bull). soft_promote_v1 unchanged.
On FAIL: archive; propose nothing automatic (hunt-queue note in md only).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    PANEL_LABEL,
    SOFT_PROMOTE_GATE,
    SOFT_PROMOTE_NOTE,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
    RiseWindow,
)
from atlas.paper.rise_panel_cascade_eval import (
    SCALP_CANDIDATE_ID as PROVISIONAL_SCALP_ID,
    SCALP_CANDIDATE_ID_4H,
    SCALP_CANDIDATE_ID_BREAKOUT,
    SCALP_CANDIDATE_ID_DONCHIAN,
    SCALP_CANDIDATE_ID_RSI_MR,
)
from atlas.paper.rise_panel_scalp_improve_eval import (
    run_scalp_4h_improve,
    run_scalp_provisional_1h,
    run_strategy_on_window,
)
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import q
from atlas.strategy.scalp_doge_ema1221_1h import (
    BAR,
    FAMILY,
    FAST,
    SLOW,
    ScalpDogeEma1221V1,
)

SOURCE = "rise_panel_v1_scalp_ema1221_63"
WARMUP_PAD_1H_DAYS = 3

SCALP_PROVISIONAL_ID = PROVISIONAL_SCALP_ID
SCALP_4H_ID = SCALP_CANDIDATE_ID_4H
SCALP_RSI_MR_ID = SCALP_CANDIDATE_ID_RSI_MR
SCALP_DONCHIAN_ID = SCALP_CANDIDATE_ID_DONCHIAN
SCALP_BREAKOUT_ID = SCALP_CANDIDATE_ID_BREAKOUT
SCALP_IMPROVE_ID = "rise_panel_v1_scalp_doge_ema12_21_1h_eur20"

PROVISIONAL_SNAPSHOT_55 = {
    "median_trades": 18.0,
    "n_exp_gt_0": 4,
    "panel_net_eur": 44.7022,
    "median_expectancy_eur": 0.2048,
    "verdict": "FAIL",
    "note": "phase1/55 provisional Scalp soft FAIL",
}
SCALP_4H_SNAPSHOT_57 = {
    "median_trades": 7.0,
    "n_exp_gt_0": 6,
    "panel_net_eur": 41.8052,
    "median_expectancy_eur": 1.0464,
    "verdict": "PASS",
    "note": "phase1/57 Scalp 4H soft PASS",
}
SCALP_RSI_MR_SNAPSHOT_59 = {
    "median_trades": 7.0,
    "n_exp_gt_0": 5,
    "panel_net_eur": 18.2424,
    "median_expectancy_eur": 0.5128,
    "verdict": "PASS",
    "note": "phase1/59 Scalp RSI14 MR 1H soft PASS",
}
SCALP_DONCHIAN_SNAPSHOT_61 = {
    "median_trades": 29.0,
    "n_exp_gt_0": 6,
    "panel_net_eur": 26.6195,
    "median_expectancy_eur": 0.0661,
    "verdict": "PASS",
    "note": "phase1/61 Scalp Donchian 20/10 1H soft PASS",
}
SCALP_BREAKOUT_SNAPSHOT_62 = {
    "median_trades": 26.0,
    "n_exp_gt_0": 5,
    "panel_net_eur": 25.2045,
    "median_expectancy_eur": 0.0652,
    "verdict": "PASS",
    "note": "phase1/62 Scalp BreakoutV1 1H soft PASS",
}
CASCADE_55_COMBINED = 492.3109
CASCADE_57_COMBINED = 489.4139
CASCADE_61_COMBINED = 474.2282
CASCADE_62_COMBINED = 472.8132
CASCADE_59_COMBINED = 465.8511


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


def _fail_row(window: RiseWindow, error: str, *, arm: str = "scalp") -> dict[str, Any]:
    return {
        "ok": False,
        "fail_closed": True,
        "error": error,
        "window_id": window.id,
        "arm": arm,
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


def run_scalp_ema1221_1h(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Scalp EMA12/21 1H long/flat €20 on SAME locked 7 — candidate #63."""
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    def factory() -> ScalpDogeEma1221V1:
        return ScalpDogeEma1221V1()

    for w in panel_windows():
        cw = _as_cascade(w)
        try:
            bars = fetch_bars(
                cw,
                ASSET,
                BAR,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=WARMUP_PAD_1H_DAYS,
            )
            row = run_strategy_on_window(
                bars=bars,
                window=w,
                strategy=factory(),
                equity=SCALP_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
                bar=BAR,
                arm="scalp_ema12_21_1h",
                family=FAMILY,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc), arm="scalp_ema12_21_1h")
        rows.append(row)

    soft = soft_promote_score(rows)
    summary = panel_summary_table(rows)
    return {
        "ok": all(r.get("ok") for r in rows),
        "candidate_id": SCALP_IMPROVE_ID,
        "scalp_improve_id": SCALP_IMPROVE_ID,
        "role": "scalp_improve",
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": BAR,
        "family": FAMILY,
        "strategy": f"ema{FAST}_{SLOW}_long_flat",
        "fast": FAST,
        "slow": SLOW,
        "daily_bull": False,
        "rsi": False,
        "sleeve_eur": SCALP_START_EUR,
        "reuse_note": (
            "Plain EmaTrendV1 EMA12/21 long/flat on 1H (Mid 4H style periods 12/21); "
            "no daily-bull; no RSI; Scalp €20 full-sleeve via walk_long_flat."
        ),
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
        "compare_to_provisional_scalp": SCALP_PROVISIONAL_ID,
        "compare_to_scalp_4h": SCALP_4H_ID,
        "compare_to_scalp_donchian": SCALP_DONCHIAN_ID,
        "compare_to_scalp_breakout": SCALP_BREAKOUT_ID,
        "compare_to_scalp_rsi_mr": SCALP_RSI_MR_ID,
    }


def deltas_vs_ref(
    ref: dict[str, Any],
    improve: dict[str, Any],
    *,
    ref_id: str,
    improve_id: str,
) -> dict[str, Any]:
    """Panel metric deltas: improve − ref."""
    b = ref.get("summary") or {}
    i = improve.get("summary") or {}

    def _d(key: str) -> float | None:
        bv, iv = b.get(key), i.get(key)
        if bv is None or iv is None:
            return None
        return q(float(iv) - float(bv))

    return {
        "compare_to": ref_id,
        "improve_id": improve_id,
        "median_expectancy_eur": {
            "ref": b.get("median_expectancy_eur"),
            "improve": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur"),
        },
        "panel_net_eur": {
            "ref": b.get("panel_net_eur"),
            "improve": i.get("panel_net_eur"),
            "delta": _d("panel_net_eur"),
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
        "not_a_forecast": True,
        "place_orders": False,
    }


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def write_report_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    redacted = redact_record(payload)
    path.write_text(json.dumps(redacted, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _delta_table(
    lines: list[str],
    *,
    title: str,
    header_a: str,
    header_b: str,
    deltas: dict[str, Any] | None,
    soft_ref: dict[str, Any],
    soft_imp: dict[str, Any],
    snapshot: dict[str, Any] | None = None,
    ms: dict[str, Any] | None = None,
) -> None:
    lines.append(title)
    lines.append("")
    if deltas is not None:
        lines.append(f"| Metric | {header_a} | {header_b} | Δ |")
        lines.append("|--------|" + "-" * max(18, len(header_a)) + ":|" + "-" * max(18, len(header_b)) + ":|--:|")
        for key, label in (
            ("median_expectancy_eur", "median exp €"),
            ("panel_net_eur", "panel net €"),
            ("median_trades", "median_trades"),
        ):
            block = deltas.get(key) or {}
            dig = 1 if key == "median_trades" else 4
            lines.append(
                f"| {label} | {_fmt(block.get('ref'), dig)} | "
                f"{_fmt(block.get('improve'), dig)} | {_fmt(block.get('delta'), dig)} |"
            )
        nexp = deltas.get("n_exp_gt_0") or {}
        lines.append(
            f"| n exp>0 / 7 | {nexp.get('ref')} | {nexp.get('improve')} | "
            f"{nexp.get('delta')} |"
        )
        lines.append(
            f"| soft promote | {soft_ref.get('verdict')} | **{soft_imp.get('verdict')}** | — |"
        )
    elif snapshot is not None and ms is not None:
        lines.append(f"| Metric | {header_a} | {header_b} | Δ |")
        lines.append("|--------|" + "-" * 18 + ":|" + "-" * 18 + ":|--:|")
        lines.append(
            f"| median exp € | {_fmt(snapshot['median_expectancy_eur'])} | "
            f"{_fmt(ms.get('median_expectancy_eur'))} | "
            f"{_fmt(None if ms.get('median_expectancy_eur') is None else q(float(ms['median_expectancy_eur']) - snapshot['median_expectancy_eur']))} |"
        )
        lines.append(
            f"| panel net € | {_fmt(snapshot['panel_net_eur'])} | "
            f"{_fmt(ms.get('panel_net_eur'))} | "
            f"{_fmt(None if ms.get('panel_net_eur') is None else q(float(ms['panel_net_eur']) - snapshot['panel_net_eur']))} |"
        )
        lines.append(
            f"| median_trades | {_fmt(snapshot['median_trades'], 1)} | "
            f"{_fmt(ms.get('median_trades'), 1)} | — |"
        )
        lines.append(
            f"| n exp>0 / 7 | {snapshot['n_exp_gt_0']} | {ms.get('n_exp_gt_0')} | — |"
        )
        lines.append(
            f"| soft promote | {snapshot['verdict']} | **{soft_imp.get('verdict')}** | — |"
        )
    lines.append("")


def render_results_markdown(
    provisional: dict[str, Any],
    improve: dict[str, Any],
    *,
    scalp_4h: dict[str, Any] | None = None,
    scalp_donchian: dict[str, Any] | None = None,
    scalp_breakout: dict[str, Any] | None = None,
    scalp_rsi_mr: dict[str, Any] | None = None,
    deltas_vs_55: dict[str, Any] | None = None,
    deltas_vs_57: dict[str, Any] | None = None,
    deltas_vs_61: dict[str, Any] | None = None,
    deltas_vs_62: dict[str, Any] | None = None,
    deltas_vs_59: dict[str, Any] | None = None,
    cascade_bundle: dict[str, Any] | None = None,
) -> str:
    """Full phase1/63 doc with lock + scored results (+ cascade if PASS)."""
    if deltas_vs_55 is None:
        deltas_vs_55 = deltas_vs_ref(
            provisional, improve, ref_id=SCALP_PROVISIONAL_ID, improve_id=SCALP_IMPROVE_ID
        )
    soft = improve.get("soft_promote") or {}
    soft_pass = bool(soft.get("pass"))
    ps = provisional.get("summary") or {}
    ms = improve.get("summary") or {}
    soft_p = provisional.get("soft_promote") or {}
    soft_4 = (scalp_4h or {}).get("soft_promote") or {"verdict": SCALP_4H_SNAPSHOT_57["verdict"]}
    soft_61 = (scalp_donchian or {}).get("soft_promote") or {
        "verdict": SCALP_DONCHIAN_SNAPSHOT_61["verdict"]
    }
    soft_62 = (scalp_breakout or {}).get("soft_promote") or {
        "verdict": SCALP_BREAKOUT_SNAPSHOT_62["verdict"]
    }
    soft_59 = (scalp_rsi_mr or {}).get("soft_promote") or {
        "verdict": SCALP_RSI_MR_SNAPSHOT_59["verdict"]
    }

    lines: list[str] = []
    lines.append("# 63 — rise_panel_v1 Scalp: DOGE **1H EMA12/21** long/flat (€20)")
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. Soft PASS ≠ Scalp-arm."
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
        "**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md); "
        "Scalp 4H [`57-rise-panel-scalp-improve-4h-ema.md`](./57-rise-panel-scalp-improve-4h-ema.md); "
        "Scalp Donchian [`61-rise-panel-scalp-donchian20-10-1h.md`](./61-rise-panel-scalp-donchian20-10-1h.md); "
        "Scalp BreakoutV1 [`62-rise-panel-scalp-breakoutv1-1h.md`](./62-rise-panel-scalp-breakoutv1-1h.md); "
        "Scalp RSI MR [`59-rise-panel-scalp-rsi14-mr-1h.md`](./59-rise-panel-scalp-rsi14-mr-1h.md). "
        "**Plain EMA12/21** long/flat (NOT 12/30; no RSI; no daily-bull). Do not re-run #58/#60."
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
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED compare targets")
    lines.append("")
    lines.append(f"**scalp_provisional_id (#55):** `{SCALP_PROVISIONAL_ID}`  ")
    lines.append("(soft_promote **FAIL** — provisional stand-in)")
    lines.append("")
    lines.append("- Rule: 1H EMA12/30 long/flat + daily EMA bull entry gate. Never short.")
    lines.append("- Bar: DOGE-USDT **1H**. Sleeve: Scalp **€20**.")
    lines.append(
        "- #55 snapshot (reported): exp>0 **4**/7 · median_trades=**18** · "
        "panel_net≈**€44.70**."
    )
    lines.append("")
    lines.append(f"**scalp_4h_id (#57):** `{SCALP_4H_ID}`  ")
    lines.append("(soft_promote **PASS** — EMA12/30 long/flat on **4H**)")
    lines.append("")
    lines.append(
        "- #57 snapshot (reported): exp>0 **6**/7 · median_trades=**7** · "
        "panel_net≈**€41.81** · median exp≈**€1.05**."
    )
    lines.append("")
    lines.append(f"**scalp_donchian_id (#61):** `{SCALP_DONCHIAN_ID}`  ")
    lines.append("(soft_promote **PASS** — Donchian 20/10 long/flat on **1H**)")
    lines.append("")
    lines.append(
        "- #61 snapshot (reported): exp>0 **6**/7 · median_trades=**29** · "
        "panel_net≈**€26.62** · cascade≈**€474.23**."
    )
    lines.append("")
    lines.append(f"**scalp_breakout_id (#62):** `{SCALP_BREAKOUT_ID}`  ")
    lines.append("(soft_promote **PASS** — BreakoutV1 long/flat on **1H**)")
    lines.append("")
    lines.append(
        "- #62 snapshot (reported): exp>0 **5**/7 · median_trades=**26** · "
        "panel_net≈**€25.20** · cascade≈**€472.81**."
    )
    lines.append("")
    lines.append(f"**scalp_rsi_mr_id (#59):** `{SCALP_RSI_MR_ID}`  ")
    lines.append("(soft_promote **PASS** — RSI(14) MR long/flat on **1H**)")
    lines.append("")
    lines.append(
        "- #59 snapshot (reported): exp>0 **5**/7 · median_trades=**7** · "
        "panel_net≈**€18.24** · cascade≈**€465.85**."
    )
    lines.append("")
    lines.append("### Provisional Scalp per window (re-scored)")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in provisional.get("rows") or []:
        wid = r.get("window_id", "?")
        lines.append(
            f"| {wid} | {r.get('n_trades', 0)} | {_fmt(r.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(r.get('net_return_eur'))} | {_fmt(r.get('max_dd_eur'))} | "
            f"{_fmt(r.get('time_in_market'))} | {_fmt(r.get('bh_net_return_eur'))} | "
            f"{_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (provisional Scalp re-score):**")
    lines.append(
        f"- windows with exp>0: **{ps.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{ps.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(ps.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(ps.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(ps.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(ps.get('worst_dd_eur'))}**")
    lines.append(
        f"- soft_promote: **{soft_p.get('verdict', '—')}** (`{SOFT_PROMOTE_GATE}`)"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. LOCKED Scalp family (BEFORE scoring)")
    lines.append("")
    lines.append(
        "**ONE family only — NOT grinding EMA periods / TF / costs. No RSI. No daily-bull.**"
    )
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**scalp_improve_id:** `{SCALP_IMPROVE_ID}`  ")
    lines.append(
        f"**compare_to:** `{SCALP_PROVISIONAL_ID}`, `{SCALP_4H_ID}`, "
        f"`{SCALP_DONCHIAN_ID}`, `{SCALP_BREAKOUT_ID}`, `{SCALP_RSI_MR_ID}`"
    )
    lines.append(
        "**Plain EMA12/21:** Mid/Scalp EMA long/flat family with periods **12/21** "
        "(NOT 12/30). Decision bar **1H**. No daily-bull. No RSI."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append("- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.")
    lines.append(f"- EMA periods: **fast={FAST}, slow={SLOW}** (NOT 12/30).")
    lines.append("- **Long/flat:** closed-bar EMA12 > EMA21 → long; else flat. Never short.")
    lines.append("- **No** daily-bull EMA filter / regime gate.")
    lines.append("- **No** RSI / Donchian / ATR / Breakout knobs this trial.")
    lines.append("- Insufficient history → flat.")
    lines.append("- Fill: signal close → next open. Size: full Scalp sleeve €20 when long.")
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append("- **No** EMA period / TF / cost grind on FAIL.")
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        "Provisional Scalp 1H+daily-bull (#55) soft FAIL (exp>0 4/7; best panel_net≈€44.70). "
        "Scalp #57 4H EMA12/30 soft PASS; #61 Donchian / #62 BreakoutV1 / #59 RSI MR also soft PASS. "
        "#58/#60 archived FAIL (do not re-run). This trial ports **plain EMA12/21** "
        "(TradingView-style twin, Mid 4H spirit without daily-bull) onto Scalp €20 / locked rise panel / 1H."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_scalp_ema1221_1h_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_scalp_ema1221_1h_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.scalp_doge_ema1221_1h` "
        "(thin wrapper around `EmaTrendV1` 12/21)"
    )
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, "
        "cascade compound (#55 rules) on PASS only; patterns from #57/#61/#62"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_scalp_ema1221_1h.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Scalp EMA12/21 1H €20 on same 7")
    lines.append("")
    lines.append(f"**scalp_improve_id:** `{SCALP_IMPROVE_ID}`")
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
    lines.append("**Panel summary (Scalp EMA12/21 1H):**")
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
        f"### Soft promote (Scalp EMA12/21): **{soft.get('verdict', '—')}** "
        f"(`{SOFT_PROMOTE_GATE}`)"
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

    if deltas_vs_57 is None and scalp_4h is not None:
        deltas_vs_57 = deltas_vs_ref(
            scalp_4h, improve, ref_id=SCALP_4H_ID, improve_id=SCALP_IMPROVE_ID
        )
    if deltas_vs_61 is None and scalp_donchian is not None:
        deltas_vs_61 = deltas_vs_ref(
            scalp_donchian, improve, ref_id=SCALP_DONCHIAN_ID, improve_id=SCALP_IMPROVE_ID
        )
    if deltas_vs_62 is None and scalp_breakout is not None:
        deltas_vs_62 = deltas_vs_ref(
            scalp_breakout, improve, ref_id=SCALP_BREAKOUT_ID, improve_id=SCALP_IMPROVE_ID
        )
    if deltas_vs_59 is None and scalp_rsi_mr is not None:
        deltas_vs_59 = deltas_vs_ref(
            scalp_rsi_mr, improve, ref_id=SCALP_RSI_MR_ID, improve_id=SCALP_IMPROVE_ID
        )

    _delta_table(
        lines,
        title="### Honesty deltas vs provisional Scalp #55 (EMA12/21 − provisional)",
        header_a="Provisional 1H €20",
        header_b="Scalp EMA12/21 1H €20",
        deltas=deltas_vs_55,
        soft_ref=soft_p,
        soft_imp=soft,
    )
    _delta_table(
        lines,
        title="### Honesty deltas vs Scalp #57 4H (EMA12/21 − 4H)",
        header_a="Scalp 4H €20 (#57)",
        header_b="Scalp EMA12/21 1H €20",
        deltas=deltas_vs_57,
        soft_ref=soft_4,
        soft_imp=soft,
        snapshot=SCALP_4H_SNAPSHOT_57,
        ms=ms,
    )
    _delta_table(
        lines,
        title="### Honesty deltas vs Scalp #61 Donchian (EMA12/21 − Donchian)",
        header_a="Scalp Donchian 1H €20 (#61)",
        header_b="Scalp EMA12/21 1H €20",
        deltas=deltas_vs_61,
        soft_ref=soft_61,
        soft_imp=soft,
        snapshot=SCALP_DONCHIAN_SNAPSHOT_61,
        ms=ms,
    )
    _delta_table(
        lines,
        title="### Honesty deltas vs Scalp #62 BreakoutV1 (EMA12/21 − Breakout)",
        header_a="Scalp BreakoutV1 1H €20 (#62)",
        header_b="Scalp EMA12/21 1H €20",
        deltas=deltas_vs_62,
        soft_ref=soft_62,
        soft_imp=soft,
        snapshot=SCALP_BREAKOUT_SNAPSHOT_62,
        ms=ms,
    )
    _delta_table(
        lines,
        title="### Honesty deltas vs Scalp #59 RSI MR (EMA12/21 − RSI MR)",
        header_a="Scalp RSI MR 1H €20 (#59)",
        header_b="Scalp EMA12/21 1H €20",
        deltas=deltas_vs_59,
        soft_ref=soft_59,
        soft_imp=soft,
        snapshot=SCALP_RSI_MR_SNAPSHOT_59,
        ms=ms,
    )

    if soft_pass and cascade_bundle is not None:
        lines.append("---")
        lines.append("")
        lines.append("## E. Cascade compound (PASS → substitute Scalp, provisional_scalp=false)")
        lines.append("")
        lines.append(
            "Same cascade rules as phase1/55: window-end surplus-share 7:2:1, "
            "one-way Scalp→Mid→Core; PaperSettings 5+5 bps; next-open; place_orders false."
        )
        lines.append("")
        narr = cascade_bundle.get("panel_narrative") or {}
        sleeve = narr.get("panel_sleeve_nets_pre_cascade_eur") or {}
        combined = narr.get("panel_combined_net_pre_cascade_eur")
        lines.append(f"- **compound_id:** `{cascade_bundle.get('compound_id')}`")
        lines.append(
            f"- **provisional_scalp:** `{cascade_bundle.get('provisional_scalp')}`"
        )
        lines.append(f"- **Scalp system:** `{SCALP_IMPROVE_ID}` (1H EMA12/21)")
        lines.append(f"- combined net pre-cascade: **{_fmt(combined)}** €")
        lines.append(
            f"- per-sleeve net (panel sum): Core **{_fmt(sleeve.get('core'))}** · "
            f"Mid **{_fmt(sleeve.get('mid'))}** · Scalp **{_fmt(sleeve.get('scalp'))}** €"
        )
        lines.append("")
        lines.append("### Compare to #55 / #57 / #61 / #62 / #59 panel nets")
        lines.append("")
        lines.append(
            "| Sleeve | #55 (provisional) | #57 (4H) | #61 (Donchian) | #62 (Breakout) | #59 (RSI MR) | #63 (EMA12/21) | Δ vs #55 | Δ vs #57 | Δ vs #61 | Δ vs #62 | Δ vs #59 |"
        )
        lines.append(
            "|--------|------------------:|---------:|---------------:|---------------:|-------------:|---------------:|---------:|---------:|---------:|---------:|---------:|"
        )
        c63 = float(sleeve.get("core") or 0)
        m63 = float(sleeve.get("mid") or 0)
        s63 = float(sleeve.get("scalp") or 0)
        comb63 = float(combined or 0)
        lines.append(
            f"| Core | 363.9983 | 363.9983 | 363.9983 | 363.9983 | 363.9983 | {_fmt(c63)} | "
            f"{_fmt(q(c63 - 363.9983))} | {_fmt(q(c63 - 363.9983))} | {_fmt(q(c63 - 363.9983))} | "
            f"{_fmt(q(c63 - 363.9983))} | {_fmt(q(c63 - 363.9983))} |"
        )
        lines.append(
            f"| Mid | 83.6104 | 83.6104 | 83.6104 | 83.6104 | 83.6104 | {_fmt(m63)} | "
            f"{_fmt(q(m63 - 83.6104))} | {_fmt(q(m63 - 83.6104))} | {_fmt(q(m63 - 83.6104))} | "
            f"{_fmt(q(m63 - 83.6104))} | {_fmt(q(m63 - 83.6104))} |"
        )
        lines.append(
            f"| Scalp | 44.7022 | 41.8052 | 26.6195 | 25.2045 | 18.2424 | {_fmt(s63)} | "
            f"{_fmt(q(s63 - 44.7022))} | {_fmt(q(s63 - 41.8052))} | {_fmt(q(s63 - 26.6195))} | "
            f"{_fmt(q(s63 - 25.2045))} | {_fmt(q(s63 - 18.2424))} |"
        )
        lines.append(
            f"| Combined | {CASCADE_55_COMBINED} | {CASCADE_57_COMBINED} | {CASCADE_61_COMBINED} | "
            f"{CASCADE_62_COMBINED} | {CASCADE_59_COMBINED} | {_fmt(comb63)} | "
            f"{_fmt(q(comb63 - CASCADE_55_COMBINED))} | {_fmt(q(comb63 - CASCADE_57_COMBINED))} | "
            f"{_fmt(q(comb63 - CASCADE_61_COMBINED))} | {_fmt(q(comb63 - CASCADE_62_COMBINED))} | "
            f"{_fmt(q(comb63 - CASCADE_59_COMBINED))} |"
        )
        lines.append("")
        lines.append(
            "Reports: `data/reports/rise_panel_v1_cascade_compound_scalp_ema1221_1h.json`"
        )
        lines.append("")
    else:
        lines.append("---")
        lines.append("")
        lines.append("## E. Archive (soft_promote FAIL → no grind / no next-family auto)")
        lines.append("")
        lines.append(
            "No EMA period / TF / cost grind. No automatic next-family start. "
            "Archive this candidate. Parent will ping coordinator for the next family."
        )
        lines.append("")
        lines.append("### Hunt-queue suggestion (md only — parent pings coordinator)")
        lines.append("")
        lines.append(
            "- MACD / histogram · Supertrend · VWAP reclaim · "
            "(do not re-run #58/#60; do not grind 12/21→12/30)."
        )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not an EMA 12/30 period twin grind (periods locked 12/21).")
    lines.append("- Not a daily-bull EMA filter / RSI add-on.")
    lines.append("- Not a change to R1–R7 window dates.")
    lines.append("- Not a rewrite of `core_style_return` A∧B on phase1/38.")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not Scalp-arming. Soft PASS ≠ Scalp-arm. Live ≤€20.")
    lines.append("- Not a claim that past rise windows forecast the next bull.")
    lines.append("- Not a re-run of archived #58/#60.")
    lines.append("- Mid 4H stays Mid baseline.")
    lines.append("")
    lines.append("`not_a_forecast: true`. `place_orders: false`.")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "CASCADE_55_COMBINED",
    "CASCADE_57_COMBINED",
    "CASCADE_59_COMBINED",
    "CASCADE_61_COMBINED",
    "CASCADE_62_COMBINED",
    "SCALP_4H_ID",
    "SCALP_BREAKOUT_ID",
    "SCALP_DONCHIAN_ID",
    "SCALP_IMPROVE_ID",
    "SCALP_PROVISIONAL_ID",
    "SCALP_RSI_MR_ID",
    "SCALP_BREAKOUT_SNAPSHOT_62",
    "SCALP_DONCHIAN_SNAPSHOT_61",
    "SCALP_RSI_MR_SNAPSHOT_59",
    "deltas_vs_ref",
    "render_results_markdown",
    "run_scalp_4h_improve",
    "run_scalp_ema1221_1h",
    "run_scalp_provisional_1h",
    "write_report_json",
]
