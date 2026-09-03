"""FastAPI read-only dashboard. No order/place/cancel routes. No secrets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from atlas.common.config import AppConfig, load_config
from atlas.dashboard.reader import (
    DashboardSnapshot,
    bundled_fixtures_dir,
    fmt_ts_ms,
    load_snapshot,
    redact,
)
from atlas.paper.compare import METRICS as CMP_METRICS
from atlas.paper.compare import SLICES as CMP_SLICES
from atlas.paper.compare import evaluate_pass_rule, index_samples
from atlas.paper.ema_eval import load_ema_reports
from atlas.paper.ema_observer import load_ema_observer_rows
from atlas.paper.eval import load_eval_reports, load_profile_reports
from atlas.paper.profiles import BASELINE, PROFILES

PKG = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(PKG / "templates"))
TEMPLATES.env.filters.setdefault("pct", lambda v: f"{float(v) * 100:.1f}%")


class _DenyWritesMiddleware(BaseHTTPMiddleware):
    """Dashboard v0 is GET-only. Refuse anything that could look like an order API."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            return JSONResponse(
                {
                    "ok": False,
                    "error": "read_only",
                    "detail": "dashboard v0 accepteert geen schrijfacties of orders",
                },
                status_code=405,
            )
        path = request.url.path.lower()
        if any(frag in path for frag in ("/place", "/cancel", "/order", "/trade")):
            if not path.startswith("/static"):
                return JSONResponse(
                    {
                        "ok": False,
                        "error": "no_trading_routes",
                        "detail": "deze UI plaatst geen orders",
                    },
                    status_code=404,
                )
        return await call_next(request)


def _resolve_data_dir(
    data_dir: str | Path | None,
    cfg: AppConfig,
    *,
    use_fixtures: bool,
    use_replay: bool,
    use_shadow: bool = False,
    use_ema: bool = False,
) -> tuple[Path, bool, bool, bool, bool]:
    if use_fixtures:
        return bundled_fixtures_dir(), True, False, False, False
    if use_shadow:
        if data_dir is not None:
            return Path(data_dir), False, False, True, False
        return Path(cfg.data_dir) / "shadow", False, False, True, False
    if use_replay:
        if data_dir is not None:
            return Path(data_dir), False, True, False, False
        return Path(cfg.data_dir) / "replay", False, True, False, False
    if use_ema:
        if data_dir is not None:
            return Path(data_dir), False, False, False, True
        return Path(cfg.data_dir) / "ema", False, False, False, True
    if data_dir is not None:
        return Path(data_dir), False, False, False, False
    return Path(cfg.data_dir), False, False, False, False


_CMP_TITLES = {
    "n_trades": "n_trades",
    "n_would_place": "n_would_place",
    "n_kill_days": "n_kill_days",
    "n_blocked_daily_cap": "n_blocked_daily_cap",
    "expectancy_after_costs_eur": "expectancy after costs (€/trade)",
    "max_dd_eur": "max DD (€)",
    "fee_drag_eur": "fee drag (€)",
    "win_rate": "win rate",
}


def _fmt_metric(key: str, value: Any) -> str:
    if value is None:
        return "—"
    if key == "expectancy_after_costs_eur":
        return f"{float(value):.4f}"
    if key in ("max_dd_eur", "fee_drag_eur"):
        return f"{float(value):.2f}"
    if key == "win_rate":
        return f"{100.0 * float(value):.1f}%"
    return str(int(value))


def _profile_comparison(profiles: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    """Baseline vs each candidate profile, read-only. None when <2 profiles on disk."""
    if len(profiles) < 2 or BASELINE not in profiles:
        return None
    base_idx = index_samples(profiles[BASELINE])
    out_candidates: list[dict[str, Any]] = []
    for name, rows in profiles.items():
        if name == BASELINE or name not in PROFILES:
            continue  # stray directories are not candidates; only named profiles render
        cand_idx = index_samples(rows)
        rule = evaluate_pass_rule(base_idx, cand_idx)
        samples: list[dict[str, Any]] = []
        for sid in sorted(set(base_idx) & set(cand_idx), key=lambda s: (s != "similar", s)):
            b, c = base_idx[sid], cand_idx[sid]
            if not (b.get("ok") and c.get("ok")):
                continue
            metric_rows = []
            for key in CMP_METRICS:
                cells = []
                for skey, _t in CMP_SLICES:
                    cells.append(_fmt_metric(key, (b.get(skey) or {}).get(key)))
                    cells.append(_fmt_metric(key, (c.get(skey) or {}).get(key)))
                metric_rows.append({"metric": _CMP_TITLES.get(key, key), "cells": cells})
            samples.append(
                {
                    "sample_id": sid,
                    "md_label": c.get("md_label") or b.get("md_label"),
                    "role": "primary" if sid in rule.get("windows", []) else "secondary",
                    "rows": metric_rows,
                }
            )
        out_candidates.append(
            {
                "name": name,
                "overlay": (rows[0].get("profile_overlay") if rows else None) or {},
                "verdict": rule.get("verdict"),
                "windows": rule.get("windows"),
                "per_window": rule.get("per_window"),
                "samples": samples,
            }
        )
    if not out_candidates:
        return None
    return {
        "baseline": BASELINE,
        "slice_titles": [t for _k, t in CMP_SLICES],
        "candidates": out_candidates,
    }


def create_app(
    *,
    data_dir: str | Path | None = None,
    config_path: str | Path | None = None,
    use_fixtures: bool = False,
    use_replay: bool = False,
    use_shadow: bool = False,
    use_ema: bool = False,
) -> FastAPI:
    cfg = load_config(config_path)
    resolved, fixtures, replay, shadow, ema = _resolve_data_dir(
        data_dir,
        cfg,
        use_fixtures=use_fixtures,
        use_replay=use_replay,
        use_shadow=use_shadow,
        use_ema=use_ema,
    )

    app = FastAPI(
        title="Atlas Trading Systems — dashboard v0",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(_DenyWritesMiddleware)
    app.mount("/static", StaticFiles(directory=str(PKG / "static")), name="static")
    app.state.data_dir = resolved
    app.state.cfg = cfg
    app.state.use_fixtures = fixtures
    app.state.use_replay = replay
    app.state.use_shadow = shadow
    app.state.use_ema = ema
    reports = Path(cfg.data_dir)
    if not reports.is_absolute():
        reports = Path.cwd() / reports
    app.state.reports_dir = reports / "reports"
    app.state.ema_dir = resolved if ema else reports / "ema"

    def snapshot() -> DashboardSnapshot:
        return load_snapshot(
            app.state.data_dir,
            cfg=app.state.cfg,
            using_fixtures=bool(app.state.use_fixtures),
            using_replay=bool(app.state.use_replay),
            using_shadow=bool(app.state.use_shadow),
            using_ema=bool(app.state.use_ema),
        )

    def page(request: Request, template: str, extra: dict[str, Any] | None = None) -> HTMLResponse:
        snap = snapshot()
        ctx: dict[str, Any] = {
            "request": request,
            "snap": snap,
            "overview": snap.overview,
            "signals": snap.signals,
            "latest": snap.latest_by_venue,
            "oms": snap.oms,
            "health": snap.health,
            "page": template.replace(".html", ""),
        }
        if extra:
            ctx.update(extra)
        return TEMPLATES.TemplateResponse(request, template, ctx)

    @app.get("/", response_class=HTMLResponse)
    def overview(request: Request) -> HTMLResponse:
        return page(request, "overview.html")

    @app.get("/signals", response_class=HTMLResponse)
    def signals(request: Request) -> HTMLResponse:
        return page(request, "signals.html")

    @app.get("/oms", response_class=HTMLResponse)
    def oms(request: Request) -> HTMLResponse:
        return page(request, "oms.html")

    @app.get("/health", response_class=HTMLResponse)
    def health(request: Request) -> HTMLResponse:
        return page(request, "health.html")

    @app.get("/eval", response_class=HTMLResponse)
    def eval_page(request: Request) -> HTMLResponse:
        raw = load_eval_reports(app.state.reports_dir)
        evals: list[dict[str, Any]] = []
        for sample in raw:
            if not sample.get("ok"):
                evals.append(
                    {
                        "sample_id": sample.get("sample_id"),
                        "ok": False,
                        "error": sample.get("error"),
                    }
                )
                continue
            rows = []
            for key, label in (
                ("full", "full"),
                ("in_sample", "in-sample 70%"),
                ("holdout", "holdout 30%"),
                ):
                m = sample.get(key) or {}
                rows.append(
                    {
                        "label": label,
                        "n_trades": m.get("n_trades"),
                        "n_would_place": m.get("n_would_place"),
                        "n_kill_days": m.get("n_kill_days"),
                        "expectancy_after_costs_eur": m.get("expectancy_after_costs_eur"),
                        "max_dd_eur": m.get("max_dd_eur"),
                        "fee_drag_eur": m.get("fee_drag_eur"),
                    }
                )
            for skey, slabel in (
                ("2x_fees", "stress 2× fees"),
                ("1bar_entry_delay", "stress 1-bar delay"),
                ("miss_10pct_entries", "stress miss 10%"),
            ):
                m = (sample.get("stress") or {}).get(skey) or {}
                rows.append(
                    {
                        "label": slabel,
                        "n_trades": m.get("n_trades"),
                        "n_would_place": m.get("n_would_place"),
                        "n_kill_days": m.get("n_kill_days"),
                        "expectancy_after_costs_eur": m.get("expectancy_after_costs_eur"),
                        "max_dd_eur": m.get("max_dd_eur"),
                        "fee_drag_eur": m.get("fee_drag_eur"),
                    }
                )
            evals.append(
                {
                    "sample_id": sample.get("sample_id"),
                    "ok": True,
                    "profile": sample.get("profile") or BASELINE,
                    "md_label": sample.get("md_label"),
                    "rows": rows,
                }
            )
        comparison = _profile_comparison(load_profile_reports(app.state.reports_dir))
        ema_raw = load_ema_reports(app.state.reports_dir)
        ema_evals: list[dict[str, Any]] = []
        for sample in ema_raw:
            if not sample.get("ok"):
                ema_evals.append(
                    {
                        "sample_id": sample.get("sample_id"),
                        "ok": False,
                        "error": sample.get("error"),
                    }
                )
                continue
            hold = sample.get("holdout") or {}
            bh = hold.get("buy_and_hold") or {}
            ema_evals.append(
                {
                    "sample_id": sample.get("sample_id"),
                    "ok": True,
                    "symbol": sample.get("symbol"),
                    "strategy": sample.get("strategy"),
                    "md_label": sample.get("md_label"),
                    "n_trades": hold.get("n_trades"),
                    "net_return_eur": hold.get("net_return_eur"),
                    "max_dd_eur": hold.get("max_dd_eur"),
                    "bh_max_dd_eur": bh.get("max_dd_eur"),
                    "time_in_market": hold.get("time_in_market"),
                }
            )
        observer_rows = load_ema_observer_rows(app.state.ema_dir)
        latest_obs = next((r for r in observer_rows if r.get("kind") in ("ema_state", "ema_decision")), None)
        ema_observer = None
        if latest_obs or observer_rows:
            ema_observer = {
                "desired": (latest_obs or {}).get("desired"),
                "symbol": (latest_obs or {}).get("symbol"),
                "strategy": (latest_obs or {}).get("strategy"),
                "ema_fast": (latest_obs or {}).get("ema_fast"),
                "ema_slow": (latest_obs or {}).get("ema_slow"),
                "last_close": (latest_obs or {}).get("last_close"),
                "as_of_bar_ts_open_ms": (latest_obs or {}).get("as_of_bar_ts_open_ms"),
                "as_of_utc": fmt_ts_ms((latest_obs or {}).get("as_of_bar_ts_open_ms")),
                "paper_shadow": bool((latest_obs or {}).get("paper_shadow")),
                "rows": observer_rows[:20],
            }
        return page(
            request,
            "eval.html",
            {
                "evals": evals,
                "comparison": comparison,
                "ema_evals": ema_evals,
                "ema_observer": ema_observer,
            },
        )

    @app.get("/api/snapshot")
    def api_snapshot() -> JSONResponse:
        return JSONResponse(redact(snapshot().as_dict()))

    @app.get("/api/overview")
    def api_overview() -> JSONResponse:
        snap = snapshot()
        return JSONResponse(redact({"overview": snap.overview.as_dict(), "health": snap.health.as_dict()}))

    @app.get("/api/signals")
    def api_signals() -> JSONResponse:
        snap = snapshot()
        return JSONResponse(
            redact(
                {
                    "signals": [s.as_dict() for s in snap.signals],
                    "latest_by_venue": {
                        k: (v.as_dict() if v is not None else None)
                        for k, v in snap.latest_by_venue.items()
                    },
                }
            )
        )

    @app.get("/api/oms")
    def api_oms() -> JSONResponse:
        return JSONResponse(redact(snapshot().oms.as_dict()))

    @app.get("/api/health")
    def api_health() -> JSONResponse:
        return JSONResponse(redact(snapshot().health.as_dict()))

    return app
