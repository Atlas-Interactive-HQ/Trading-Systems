"""rise_panel_v1 Track B — three-system parallel compounding + surplus cascade.

LOCKED windows R1–R7 from atlas.paper.rise_panel (phase1/54). Do NOT change dates.
Systems v1:
  Core  €140 — DOGE-USDT 1D EMA12/30 long/flat
  Mid   €40  — DOGE-USDT 4H EMA12/30 long/flat (soft_promote PASS #54)
  Scalp €20  — prefer turnover: DOGE-USDT 1H EMA12/30 + daily EMA bull (#48 spirit)
               If soft_promote FAIL → provisional_scalp=True (still report equity honestly)

Cascade (paper): window-end surplus-share rebalance to 7:2:1, one-way Scalp→Mid→Core.
Compounding: each sleeve walk sizes from sleeve cash (compound up); no martingale.
Costs: PaperSettings 5+5 bps; next-open; place_orders false; not_a_forecast.
NEVER mutates config/default.yaml.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import (
    CORE_START_EUR,
    MID_START_EUR,
    MIN_TRANSFER_EUR,
    SCALP_START_EUR,
    SHARE_CORE,
    SHARE_MID,
    SHARE_SCALP,
    TOTAL_START_EUR,
    apply_walk_ends_then_surplus,
)
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    BASELINE_ID,
    CORE_BAR,
    MID_BAR_CANDIDATE,
    MID_CANDIDATE_ID,
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
from atlas.paper.rise_panel_eval import run_ema_on_window
from atlas.paper.scalp_doge_ema_1h_eval import walk_long_flat_1h_daily_bull
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import q
from atlas.strategy.scalp_doge_ema_1h import (
    BAR as SCALP_BAR,
    FAMILY as SCALP_FAMILY,
    FAST,
    SLOW,
    ScalpDogeEma1hParams,
    ScalpDogeEma1hV1,
)

SOURCE = "rise_panel_cascade_compound"
COMPOUND_ID = "rise_panel_v1_cascade_compound_721"
SCALP_CANDIDATE_ID = "rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20"
SCALP_STANDIN_LABEL = "scalp_doge_ema_1h_daily_bull"
WARMUP_DAILY = 40
WARMUP_PAD_4H_DAYS = 10
WARMUP_PAD_1H_DAYS = 3
DAY_MS = 24 * 60 * 60 * 1000

CASCADE_RULE = {
    "name": "window_end_surplus_share_721",
    "direction": "scalp→mid→core",
    "one_way": True,
    "no_downward_refill": True,
    "target_shares": {"core": SHARE_CORE, "mid": SHARE_MID, "scalp": SHARE_SCALP},
    "ratio": "7:2:1",
    "trigger": (
        "After each R-window's three independent compounded walks, snapshot sleeve "
        "end equities onto CascadeLedger, then surplus_share_rebalance: for Scalp "
        "then Mid, if sleeve_equity > target_share * total_book + min_transfer (€1), "
        "transfer surplus upward. Core never sends. No mid-window refill."
    ),
    "min_transfer_eur": MIN_TRANSFER_EUR,
    "compounding": (
        "Within each sleeve walk, size tracks sleeve cash (full sleeve when long / "
        "cash when flat) — compound up on closed trades. No martingale / no size-up-on-loss."
    ),
    "window_independence": (
        "Each R1–R7 window starts fresh at Core €140 / Mid €40 / Scalp €20 "
        "(panel windows are scored independently; no cross-window capital carry)."
    ),
}


def _as_cascade(w: RiseWindow) -> CascadeWindow:
    return CascadeWindow(id=w.id, start=w.start, end=w.end, set_id="rise", label=w.label)


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _fail_row(window: RiseWindow, *, arm: str, error: str) -> dict[str, Any]:
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
        "start_equity_eur": None,
        "end_equity_eur": None,
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_scalp_1h_on_window(
    *,
    bars_1h: list,
    daily_bars: list,
    window: RiseWindow,
    equity: float,
    fee_rate: float,
    slippage_bps: float,
) -> dict[str, Any]:
    """Scalp DOGE 1H EMA12/30 + daily bull entry gate on one rise window."""
    settings = EmaBookSettings(
        equity_eur=float(equity),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    strat = ScalpDogeEma1hV1(ScalpDogeEma1hParams(), daily_bars=daily_bars)
    trade_bars = [b for b in bars_1h if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade_bars) < 12:
        return _fail_row(window, arm="scalp_ema_1h_daily_bull", error="insufficient 1H bars")
    walk = walk_long_flat_1h_daily_bull(
        bars_1h,
        strategy=strat,
        settings=settings,
        trade_start_ms=window.start_ms,
        trade_end_ms=window.end_ms_exclusive,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    return {
        "ok": True,
        "window_id": window.id,
        "start": window.start,
        "end": window.end,
        "character": window.character,
        "asset": ASSET,
        "bar": SCALP_BAR,
        "arm": "scalp_ema_1h_daily_bull",
        "family": SCALP_FAMILY,
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
        "n_blocked_by_daily_bull": walk.get("n_blocked_by_daily_bull"),
        "not_a_forecast": True,
        "place_orders": False,
    }


def _compound_window_row(
    *,
    window: RiseWindow,
    core: dict[str, Any],
    mid: dict[str, Any],
    scalp: dict[str, Any],
) -> dict[str, Any]:
    """Apply window-end surplus cascade; report pre/post equities + transfers."""
    if not (core.get("ok") and mid.get("ok") and scalp.get("ok")):
        return {
            "ok": False,
            "fail_closed": True,
            "window_id": window.id,
            "start": window.start,
            "end": window.end,
            "error": "sleeve fail-closed (missing MD or insufficient bars)",
            "core": core,
            "mid": mid,
            "scalp": scalp,
            "not_a_forecast": True,
            "place_orders": False,
        }

    core_end = float(core["end_equity_eur"])
    mid_end = float(mid["end_equity_eur"])
    scalp_end = float(scalp["end_equity_eur"])
    pre_total = q(core_end + mid_end + scalp_end)
    led = apply_walk_ends_then_surplus(
        core_end_eur=core_end,
        mid_end_eur=mid_end,
        scalp_end_eur=scalp_end,
        ts_ms=window.end_ms_exclusive - 1,
        reason="window_end_surplus_share_721",
    )
    transfers = [t.as_dict() for t in led.transfers]
    post = {
        "core": led.core.equity_eur,
        "mid": led.mid.equity_eur,
        "scalp": led.scalp.equity_eur,
        "total": led.total_equity_eur(),
    }
    sleeve_nets = {
        "core": q(core_end - CORE_START_EUR),
        "mid": q(mid_end - MID_START_EUR),
        "scalp": q(scalp_end - SCALP_START_EUR),
    }
    combined_net_pre = q(pre_total - TOTAL_START_EUR)
    # Combined book DD approx: sum of sleeve max DDs is NOT joint DD; report per-sleeve
    # and a book marked DD proxy = max over sleeves of (start_sleeve - (end - max_dd))? 
    # Honest: report per-sleeve max_dd and book_net only; no invented joint path DD.
    book_max_dd_proxy = q(
        float(core.get("max_dd_eur") or 0)
        + float(mid.get("max_dd_eur") or 0)
        + float(scalp.get("max_dd_eur") or 0)
    )
    return {
        "ok": True,
        "window_id": window.id,
        "start": window.start,
        "end": window.end,
        "character": window.character,
        "start_allocation_eur": {
            "core": CORE_START_EUR,
            "mid": MID_START_EUR,
            "scalp": SCALP_START_EUR,
            "total": TOTAL_START_EUR,
            "ratio": "7:2:1",
        },
        "pre_cascade_end_eur": {
            "core": q(core_end),
            "mid": q(mid_end),
            "scalp": q(scalp_end),
            "total": pre_total,
        },
        "post_cascade_end_eur": post,
        "sleeve_net_eur_pre_cascade": sleeve_nets,
        "combined_net_eur_pre_cascade": combined_net_pre,
        "combined_net_eur_post_cascade": q(post["total"] - TOTAL_START_EUR),
        "transfers": transfers,
        "n_transfers": len(transfers),
        "transfer_sum_eur": q(sum(t["amount_eur"] for t in transfers)),
        "per_sleeve_max_dd_eur": {
            "core": core.get("max_dd_eur"),
            "mid": mid.get("max_dd_eur"),
            "scalp": scalp.get("max_dd_eur"),
        },
        "book_max_dd_eur_sum_proxy": book_max_dd_proxy,
        "book_max_dd_note": (
            "Sum of per-sleeve max DD (NOT a joint marked path DD — sleeves run "
            "independent walks; do not treat as simultaneous book drawdown)."
        ),
        "core": core,
        "mid": mid,
        "scalp": scalp,
        "cascade_rule": CASCADE_RULE["name"],
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_cascade_compound_panel(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Run Core+Mid+Scalp on locked R1–R7 with window-end surplus cascade."""
    fee_rate, slip = _paper_costs(cfg)
    window_rows: list[dict[str, Any]] = []
    core_rows: list[dict[str, Any]] = []
    mid_rows: list[dict[str, Any]] = []
    scalp_rows: list[dict[str, Any]] = []
    errors: list[str] = []

    for w in panel_windows():
        cw = _as_cascade(w)
        core = mid = scalp = None
        try:
            bars_1d = fetch_bars(
                cw, ASSET, CORE_BAR, data_dir=data_dir, rest_base=rest_base,
                pause_s=pause_s, pad_days=WARMUP_DAILY,
            )
            core = run_ema_on_window(
                bars=bars_1d, window=w, equity=CORE_START_EUR,
                fee_rate=fee_rate, slippage_bps=slip, bar=CORE_BAR, arm="core_ema12_30",
            )
        except ReplayError as exc:
            errors.append(f"{w.id} core: {exc}")
            core = _fail_row(w, arm="core_ema12_30", error=str(exc))

        try:
            bars_4h = fetch_bars(
                cw, ASSET, MID_BAR_CANDIDATE, data_dir=data_dir, rest_base=rest_base,
                pause_s=pause_s, pad_days=WARMUP_PAD_4H_DAYS,
            )
            mid = run_ema_on_window(
                bars=bars_4h, window=w, equity=MID_START_EUR,
                fee_rate=fee_rate, slippage_bps=slip, bar=MID_BAR_CANDIDATE,
                arm="mid_ema12_30_4h",
            )
        except ReplayError as exc:
            errors.append(f"{w.id} mid: {exc}")
            mid = _fail_row(w, arm="mid_ema12_30_4h", error=str(exc))

        try:
            bars_1h = fetch_bars(
                cw, ASSET, SCALP_BAR, data_dir=data_dir, rest_base=rest_base,
                pause_s=pause_s, pad_days=WARMUP_PAD_1H_DAYS,
            )
            # Daily bars for bull filter (reuse 1D fetch if core ok else fetch).
            if core and core.get("ok"):
                daily_bars = bars_1d  # type: ignore[name-defined]
            else:
                daily_bars = fetch_bars(
                    cw, ASSET, CORE_BAR, data_dir=data_dir, rest_base=rest_base,
                    pause_s=pause_s, pad_days=WARMUP_DAILY,
                )
            scalp = run_scalp_1h_on_window(
                bars_1h=bars_1h, daily_bars=daily_bars, window=w,
                equity=SCALP_START_EUR, fee_rate=fee_rate, slippage_bps=slip,
            )
        except ReplayError as exc:
            errors.append(f"{w.id} scalp: {exc}")
            scalp = _fail_row(w, arm="scalp_ema_1h_daily_bull", error=str(exc))

        assert core is not None and mid is not None and scalp is not None
        core_rows.append(core)
        mid_rows.append(mid)
        scalp_rows.append(scalp)
        window_rows.append(_compound_window_row(window=w, core=core, mid=mid, scalp=scalp))

    scalp_soft = soft_promote_score(scalp_rows)
    provisional_scalp = not bool(scalp_soft.get("pass"))
    mid_soft = soft_promote_score(mid_rows)
    core_summary = panel_summary_table(core_rows)
    mid_summary = panel_summary_table(mid_rows)
    scalp_summary = panel_summary_table(scalp_rows)

    ok_windows = [r for r in window_rows if r.get("ok")]
    panel_start = q(TOTAL_START_EUR * len(ok_windows)) if ok_windows else 0.0
    panel_end_pre = q(sum(float(r["pre_cascade_end_eur"]["total"]) for r in ok_windows))
    panel_end_post = q(sum(float(r["post_cascade_end_eur"]["total"]) for r in ok_windows))
    panel_transfers = q(sum(float(r.get("transfer_sum_eur") or 0) for r in ok_windows))
    panel_n_transfers = sum(int(r.get("n_transfers") or 0) for r in ok_windows)
    panel_sleeve_nets = {
        "core": q(sum(float((r.get("sleeve_net_eur_pre_cascade") or {}).get("core") or 0) for r in ok_windows)),
        "mid": q(sum(float((r.get("sleeve_net_eur_pre_cascade") or {}).get("mid") or 0) for r in ok_windows)),
        "scalp": q(sum(float((r.get("sleeve_net_eur_pre_cascade") or {}).get("scalp") or 0) for r in ok_windows)),
    }
    worst_book_dd_proxy = None
    dds = [r.get("book_max_dd_eur_sum_proxy") for r in ok_windows if r.get("book_max_dd_eur_sum_proxy") is not None]
    if dds:
        worst_book_dd_proxy = q(max(float(d) for d in dds))

    return {
        "ok": all(r.get("ok") for r in window_rows) and len(window_rows) == 7,
        "compound_id": COMPOUND_ID,
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "systems": {
            "core": {
                "id": BASELINE_ID,
                "bar": CORE_BAR,
                "strategy": f"ema{FAST}_{SLOW}_long_flat",
                "sleeve_start_eur": CORE_START_EUR,
            },
            "mid": {
                "id": MID_CANDIDATE_ID,
                "bar": MID_BAR_CANDIDATE,
                "strategy": f"ema{FAST}_{SLOW}_long_flat",
                "sleeve_start_eur": MID_START_EUR,
                "soft_promote_prior": "PASS (#54)",
            },
            "scalp": {
                "id": SCALP_CANDIDATE_ID,
                "bar": SCALP_BAR,
                "strategy": SCALP_FAMILY,
                "sleeve_start_eur": SCALP_START_EUR,
                "standin_label": SCALP_STANDIN_LABEL,
                "prefer": "turnover Scalp with real trades (1H EMA + daily bull)",
                "provisional_scalp": provisional_scalp,
                "soft_promote": scalp_soft,
            },
        },
        "provisional_scalp": provisional_scalp,
        "cascade_rule": CASCADE_RULE,
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "windows_locked": justification_rows(),
        "window_rows": window_rows,
        "core_rows": core_rows,
        "mid_rows": mid_rows,
        "scalp_rows": scalp_rows,
        "core_summary": core_summary,
        "mid_summary": mid_summary,
        "scalp_summary": scalp_summary,
        "mid_soft_promote": mid_soft,
        "scalp_soft_promote": scalp_soft,
        "panel_narrative": {
            "n_ok_windows": len(ok_windows),
            "panel_start_equity_eur_sum": panel_start,
            "panel_end_equity_pre_cascade_eur_sum": panel_end_pre,
            "panel_end_equity_post_cascade_eur_sum": panel_end_post,
            "panel_combined_net_pre_cascade_eur": q(panel_end_pre - panel_start) if ok_windows else None,
            "panel_combined_net_post_cascade_eur": q(panel_end_post - panel_start) if ok_windows else None,
            "panel_transfer_sum_eur": panel_transfers,
            "panel_n_transfers": panel_n_transfers,
            "panel_sleeve_nets_pre_cascade_eur": panel_sleeve_nets,
            "worst_book_max_dd_eur_sum_proxy": worst_book_dd_proxy,
            "note": (
                "Panel sums treat each R-window as an independent €200 start "
                "(7×€200 = €1400 notionally across the panel). Cascade transfers "
                "are intra-window only."
            ),
        },
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "config_default_yaml_untouched": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
    }


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_phase55_markdown(bundle: dict[str, Any]) -> str:
    lines: list[str] = []
    scalp_sys = (bundle.get("systems") or {}).get("scalp") or {}
    prov = bool(bundle.get("provisional_scalp"))
    lines.append("# 55 — rise_panel_v1 Track B cascade compound (Core/Mid/Scalp)")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append("**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; paper only.")
    lines.append(f"**Panel:** `{PANEL_LABEL}` (R1–R7 dates **locked** in phase1/54 — unchanged).")
    lines.append(f"**compound_id:** `{COMPOUND_ID}`")
    lines.append(
        "**Parent:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) · "
        "[`34-three-tier-cascade.md`](./34-three-tier-cascade.md) · "
        "[`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md)"
    )
    lines.append("")
    if prov:
        lines.append(
            f"> **`provisional_scalp: true`** — Scalp stand-in "
            f"`{SCALP_STANDIN_LABEL}` did **not** soft-promote on rise_panel_v1. "
            "Full compound equity / transfers / DD still reported honestly below."
        )
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Systems v1 (parallel)")
    lines.append("")
    lines.append("| Sleeve | Start € | Share | System |")
    lines.append("|--------|--------:|------:|--------|")
    lines.append("| Core | 140 | 70% | DOGE-USDT **1D** EMA12/30 long/flat |")
    lines.append("| Mid | 40 | 20% | DOGE-USDT **4H** EMA12/30 long/flat (soft_promote PASS #54) |")
    lines.append(
        f"| Scalp | 20 | 10% | DOGE-USDT **1H** EMA12/30 + daily EMA bull "
        f"(`{SCALP_STANDIN_LABEL}`) "
        + ("**PROVISIONAL**" if prov else "soft_promote PASS")
        + " |"
    )
    lines.append("| **Total** | **200** | **7:2:1** | One-way Scalp→Mid→Core |")
    lines.append("")
    lines.append("### Scalp choice")
    lines.append("")
    lines.append(
        f"- **Chosen:** `{SCALP_CANDIDATE_ID}` — turnover Scalp with real trades "
        "(not n≈0 BH twin). Prefer 1H EMA + daily filter over 15m breakout for MD/pad reuse."
    )
    lines.append(f"- **`provisional_scalp`:** `{str(prov).lower()}`")
    soft = bundle.get("scalp_soft_promote") or {}
    lines.append(
        f"- Soft-promote (`{SOFT_PROMOTE_GATE}`): **{soft.get('verdict', '—')}** "
        f"(median_trades={_fmt(soft.get('median_trades'), 1)}, "
        f"exp>0={soft.get('n_expectancy_gt_0')}/7, "
        f"panel_net={_fmt(soft.get('panel_net_eur'))})"
    )
    lines.append(f"- Note: {SOFT_PROMOTE_NOTE}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Cascade + compounding rules (LOCKED for this trial)")
    lines.append("")
    cr = bundle.get("cascade_rule") or CASCADE_RULE
    lines.append(f"- **Direction:** `{cr.get('direction')}` — one-way; no downward refill.")
    lines.append(
        f"- **Surplus trigger:** `{cr.get('name')}` — at each window end, "
        "rebalance surplus to target shares 7:2:1 when "
        "`sleeve_equity > target_share * total + min_transfer (€1)`."
    )
    lines.append(f"- **Documented rule:** {cr.get('trigger')}")
    lines.append(f"- **Compounding:** {cr.get('compounding')}")
    lines.append(f"- **Windows:** {cr.get('window_independence')}")
    lines.append("- **Costs:** PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.")
    lines.append("- **Fail-closed** on missing MD / insufficient bars.")
    lines.append("- **No martingale.**")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED panel dates (unchanged from #54)")
    lines.append("")
    lines.append(
        "| Id | Start (UTC) | End (UTC, incl.) | Approx end-to-end % | Character |"
    )
    lines.append(
        "|----|-------------|------------------|--------------------:|-----------|"
    )
    for w in RISE_PANEL_V1:
        lines.append(
            f"| {w.id} | {w.start} | {w.end} | **+{w.approx_move_pct:.1f}%** | {w.character} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. Per-window compound results (measured)")
    lines.append("")
    lines.append(
        "| Id | Start € | End pre € | End post € | Comb net pre € | "
        "Transfers n/€ | Core net € | Mid net € | Scalp net € | "
        "DDΣ proxy € | Scalp n |"
    )
    lines.append(
        "|----|--------:|----------:|-----------:|---------------:|"
        "---------------:|----------:|---------:|-----------:|"
        "------------:|--------:|"
    )
    for r in bundle.get("window_rows") or []:
        wid = r.get("window_id", "?")
        if not r.get("ok"):
            lines.append(
                f"| {wid} | 200 | — | — | — | — | — | — | — | — | "
                f"FAIL ({r.get('error', 'fail_closed')}) |"
            )
            continue
        pre = r["pre_cascade_end_eur"]
        post = r["post_cascade_end_eur"]
        nets = r["sleeve_net_eur_pre_cascade"]
        lines.append(
            f"| {wid} | {_fmt(TOTAL_START_EUR, 1)} | {_fmt(pre['total'])} | {_fmt(post['total'])} | "
            f"{_fmt(r.get('combined_net_eur_pre_cascade'))} | "
            f"{r.get('n_transfers')}/{_fmt(r.get('transfer_sum_eur'))} | "
            f"{_fmt(nets.get('core'))} | {_fmt(nets.get('mid'))} | {_fmt(nets.get('scalp'))} | "
            f"{_fmt(r.get('book_max_dd_eur_sum_proxy'))} | "
            f"{(r.get('scalp') or {}).get('n_trades', 0)} |"
        )
    lines.append("")
    lines.append(
        "> DDΣ proxy = sum of per-sleeve max DD (not joint marked path). "
        "Transfers are window-end surplus-share only."
    )
    lines.append("")
    lines.append("### Per-sleeve detail (pre-cascade walk metrics)")
    lines.append("")
    lines.append(
        "| Id | Core n/net/DD | Mid n/net/DD | Scalp n/exp/net/DD |"
    )
    lines.append("|----|--------------:|-------------:|-------------------:|")
    for r in bundle.get("window_rows") or []:
        wid = r.get("window_id", "?")
        c, m, s = r.get("core") or {}, r.get("mid") or {}, r.get("scalp") or {}
        lines.append(
            f"| {wid} | {c.get('n_trades', 0)}/{_fmt(c.get('net_return_eur'))}/"
            f"{_fmt(c.get('max_dd_eur'))} | "
            f"{m.get('n_trades', 0)}/{_fmt(m.get('net_return_eur'))}/{_fmt(m.get('max_dd_eur'))} | "
            f"{s.get('n_trades', 0)}/{_fmt(s.get('expectancy_after_costs_eur'))}/"
            f"{_fmt(s.get('net_return_eur'))}/{_fmt(s.get('max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Full-panel narrative")
    lines.append("")
    narr = bundle.get("panel_narrative") or {}
    lines.append(f"- **ok windows:** {narr.get('n_ok_windows')}/7")
    lines.append(
        f"- **panel start equity (sum of independent window starts):** "
        f"**{_fmt(narr.get('panel_start_equity_eur_sum'))}** € "
        f"(= n_ok × €200)"
    )
    lines.append(
        f"- **panel end equity pre-cascade (sum):** "
        f"**{_fmt(narr.get('panel_end_equity_pre_cascade_eur_sum'))}** €"
    )
    lines.append(
        f"- **panel end equity post-cascade (sum):** "
        f"**{_fmt(narr.get('panel_end_equity_post_cascade_eur_sum'))}** € "
        "(same total — surplus moves between sleeves only)"
    )
    lines.append(
        f"- **combined net pre-cascade:** **{_fmt(narr.get('panel_combined_net_pre_cascade_eur'))}** €"
    )
    lines.append(
        f"- **transfers:** n={narr.get('panel_n_transfers')} · sum **{_fmt(narr.get('panel_transfer_sum_eur'))}** € "
        "(Scalp→Mid / Mid→Core)"
    )
    sn = narr.get("panel_sleeve_nets_pre_cascade_eur") or {}
    lines.append(
        f"- **per-sleeve net (pre-cascade, panel sum):** "
        f"Core **{_fmt(sn.get('core'))}** · Mid **{_fmt(sn.get('mid'))}** · "
        f"Scalp **{_fmt(sn.get('scalp'))}** €"
    )
    lines.append(
        f"- **worst window DDΣ proxy:** **{_fmt(narr.get('worst_book_max_dd_eur_sum_proxy'))}** €"
    )
    lines.append(f"- {narr.get('note', '')}")
    lines.append("")
    lines.append("### Soft-promote snapshots (informational for Core; Mid prior PASS; Scalp gate)")
    lines.append("")
    cs = bundle.get("core_summary") or {}
    ms = bundle.get("mid_summary") or {}
    ss = bundle.get("scalp_summary") or {}
    lines.append(
        f"- Core: median_trades={_fmt(cs.get('median_trades'), 1)} · "
        f"exp>0={cs.get('n_exp_gt_0')}/7 · panel_net={_fmt(cs.get('panel_net_eur'))}"
    )
    lines.append(
        f"- Mid: median_trades={_fmt(ms.get('median_trades'), 1)} · "
        f"exp>0={ms.get('n_exp_gt_0')}/7 · panel_net={_fmt(ms.get('panel_net_eur'))} · "
        f"soft={(bundle.get('mid_soft_promote') or {}).get('verdict')}"
    )
    lines.append(
        f"- Scalp: median_trades={_fmt(ss.get('median_trades'), 1)} · "
        f"exp>0={ss.get('n_exp_gt_0')}/7 · panel_net={_fmt(ss.get('panel_net_eur'))} · "
        f"soft={soft.get('verdict')} · **provisional_scalp={str(prov).lower()}**"
    )
    lines.append("")
    lines.append("### Combined expectancy narrative")
    lines.append("")
    lines.append(
        "Expectancy is per-sleeve after costs (€/closed trade). Core on 1D often has "
        "low n (open-hold through rise legs). Mid 4H and Scalp 1H supply turnover. "
        "Cascade does not create edge — it only moves surplus capital upward after walks. "
        "Panel combined net is the sum of independent window book nets (pre-cascade). "
        f"Scalp soft-promote is **{soft.get('verdict', '—')}**"
        + ("; treat Scalp as **provisional** stand-in for Track B compound reporting." if prov else ".")
    )
    lines.append("")
    lines.append("`not_a_forecast: true`.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_cascade_compound_eval.py`")
    lines.append(
        "- Module: `atlas.paper.rise_panel_cascade_eval` · cascade surplus: "
        "`atlas.paper.cascade.surplus_share_rebalance` / `apply_walk_ends_then_surplus`"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_cascade_compound.py`")
    lines.append("- Reports: `data/reports/rise_panel_v1_cascade_compound.json`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not a change to R1–R7 window dates.")
    lines.append("- Not a claim that cascade surplus creates alpha.")
    lines.append("- Not a silent rewrite of `core_style_return` A∧B.")
    if prov:
        lines.append(
            "- **Scalp is provisional** — do not treat soft-promote FAIL as board CONFIRMED."
        )
    lines.append("")
    lines.append("`not_a_forecast: true`. `place_orders: false`. `config/default.yaml` untouched.")
    lines.append("")
    return "\n".join(lines)


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redact_record(bundle), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
