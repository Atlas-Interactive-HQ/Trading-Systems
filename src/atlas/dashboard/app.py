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
from atlas.dashboard.reader import DashboardSnapshot, bundled_fixtures_dir, load_snapshot, redact
from atlas.paper.eval import load_eval_reports

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
) -> tuple[Path, bool, bool, bool]:
    if use_fixtures:
        return bundled_fixtures_dir(), True, False, False
    if use_shadow:
        if data_dir is not None:
            return Path(data_dir), False, False, True
        return Path(cfg.data_dir) / "shadow", False, False, True
    if use_replay:
        if data_dir is not None:
            return Path(data_dir), False, True, False
        return Path(cfg.data_dir) / "replay", False, True, False
    if data_dir is not None:
        return Path(data_dir), False, False, False
    return Path(cfg.data_dir), False, False, False


def create_app(
    *,
    data_dir: str | Path | None = None,
    config_path: str | Path | None = None,
    use_fixtures: bool = False,
    use_replay: bool = False,
    use_shadow: bool = False,
) -> FastAPI:
    cfg = load_config(config_path)
    resolved, fixtures, replay, shadow = _resolve_data_dir(
        data_dir,
        cfg,
        use_fixtures=use_fixtures,
        use_replay=use_replay,
        use_shadow=use_shadow,
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
    reports = Path(cfg.data_dir)
    if not reports.is_absolute():
        reports = Path.cwd() / reports
    app.state.reports_dir = reports / "reports"

    def snapshot() -> DashboardSnapshot:
        return load_snapshot(
            app.state.data_dir,
            cfg=app.state.cfg,
            using_fixtures=bool(app.state.use_fixtures),
            using_replay=bool(app.state.use_replay),
            using_shadow=bool(app.state.use_shadow),
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
                    "md_label": sample.get("md_label"),
                    "rows": rows,
                }
            )
        return page(request, "eval.html", {"evals": evals})

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
