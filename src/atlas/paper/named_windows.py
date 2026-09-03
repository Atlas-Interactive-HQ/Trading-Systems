"""Named backtest windows (calendar spans). Not similar-regime matching.

Research MD for 2020/2023: DOGE-USDT (labeled; not OMS spot DOGE-USD).
X-Perp public 310404 has no history on these dates → skip, do not invent bars.
Optional DOGE-USDT-SWAP is a separate research-perp leg (not X-Perp, not orderable).

Named-window ≠ forecast. Replay ≠ live Phase A week. No orders.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from atlas.collectors.base import new_run_id
from atlas.common.time import utc_date_str, utc_ms
from atlas.oms.doge_demo_loop import (
    LOCKED_SPOT_INST,
    PUBLIC_XPERP_MD_INST,
    parse_venue_arg,
    scan_signals,
    signal_to_dict,
)
from atlas.oms.spot_demo import PAPER_EQUITY_EUR
from atlas.paper.engine import strategy_from_app_config
from atlas.paper.md import (
    OKX_REST,
    USER_AGENT,
    PaperDataError,
    fetch_okx_history_candles,
    resample_1h,
)
from atlas.paper.replay import ReplayError, ReplayJournal, _count_sides
from atlas.paper.types import Bar

NAMED_SOURCE = "named-window"
OMS_SPOT_INST = LOCKED_SPOT_INST  # DOGE-USD — not used as MD for these windows
RESEARCH_SPOT_MD = "DOGE-USDT"
RESEARCH_PERP_MD = "DOGE-USDT-SWAP"
XPERP_MD = PUBLIC_XPERP_MD_INST
NAMED_HISTORY_MAX_PAGES = 400  # ~7 months of 15m ≈ 200 pages; leave headroom

# Inclusive UTC calendar dates. end_ms is exclusive (day after last inclusive day).
# 2020-09 / 2023-09 remain the original multi-month research spans (not calendar September).
# YYYY-10/11/12 are true calendar months (Q4 seasonal definition for coming months).
Q4_YEARS = (2020, 2023, 2024)
Q4_MONTHS = (10, 11, 12)
Q4_TOKENS = frozenset({"q4", "q4-months"})


def calendar_month_spec(year: int, month: int) -> dict[str, str]:
    """UTC calendar month: 1st → last day (Oct 31 / Nov 30 / Dec 31)."""
    last = calendar.monthrange(year, month)[1]
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-{last:02d}"
    wid = f"{year:04d}-{month:02d}"
    return {
        "id": wid,
        "start": start,
        "end": end,
        "label": f"{start} → {end} UTC",
    }


def _build_named_windows() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {
        "2020-09": {
            "id": "2020-09",
            "start": "2020-09-01",
            "end": "2021-03-31",
            "label": "2020-09-01 → 2021-03-31 UTC",
        },
        "2023-09": {
            "id": "2023-09",
            "start": "2023-09-01",
            "end": "2024-03-31",
            "label": "2023-09-01 → 2024-03-31 UTC",
        },
        # Non-bull stress windows for daily EMA (not similar-regime matching).
        "2022-bear": {
            "id": "2022-bear",
            "start": "2022-01-01",
            "end": "2022-12-31",
            "label": "2022-01-01 → 2022-12-31 UTC",
        },
        "2022-h1": {
            "id": "2022-h1",
            "start": "2022-01-01",
            "end": "2022-06-30",
            "label": "2022-01-01 → 2022-06-30 UTC",
        },
        "2023-chop": {
            "id": "2023-chop",
            "start": "2023-01-01",
            "end": "2023-08-31",
            "label": "2023-01-01 → 2023-08-31 UTC",
        },
    }
    for year in Q4_YEARS:
        for month in Q4_MONTHS:
            spec = calendar_month_spec(year, month)
            out[spec["id"]] = spec
    return out


NAMED_WINDOWS: dict[str, dict[str, str]] = _build_named_windows()
Q4_WINDOW_IDS: tuple[str, ...] = tuple(
    f"{year}-{month:02d}" for year in Q4_YEARS for month in Q4_MONTHS
)


@dataclass(frozen=True)
class NamedWindow:
    id: str
    start: str
    end: str
    label: str

    @property
    def start_ms(self) -> int:
        return _utc_day_ms(self.start)

    @property
    def end_ms_exclusive(self) -> int:
        """First instant after the inclusive end date (UTC)."""
        dt = datetime.strptime(self.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return int((dt + timedelta(days=1)).timestamp() * 1000)


def _utc_day_ms(yyyy_mm_dd: str) -> int:
    dt = datetime.strptime(yyyy_mm_dd, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def expand_window_ids(raw: str | list[str]) -> list[str]:
    """Expand comma lists and the `q4` token. Unknown ids are left as-is."""
    parts = str(raw).split(",") if isinstance(raw, str) else list(raw)
    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        key = str(part).strip()
        if not key:
            continue
        chunk = list(Q4_WINDOW_IDS) if key in Q4_TOKENS else [key]
        for item in chunk:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
    return out


def parse_windows_arg(raw: str) -> list[NamedWindow]:
    """Parse '2020-09,2023-09' or 'q4'. Unknown ids fail closed."""
    if not str(raw or "").strip():
        raise ReplayError("--windows is empty")
    out: list[NamedWindow] = []
    for key in expand_window_ids(raw):
        spec = NAMED_WINDOWS.get(key)
        if spec is None:
            known = ", ".join(sorted(NAMED_WINDOWS))
            raise ReplayError(f"unknown named window {key!r}; known: {known}")
        out.append(NamedWindow(**spec))
    if not out:
        raise ReplayError("no named windows parsed")
    return out


def spot_research_md() -> dict[str, Any]:
    """Spot MD for named windows. Never silently uses DOGE-USD."""
    return {
        "venue": "spot",
        "md_inst_id": RESEARCH_SPOT_MD,
        "oms_inst_id": OMS_SPOT_INST,
        "research_md": True,
        "orderable": False,
        "label": (
            f"research MD {RESEARCH_SPOT_MD}; not OMS spot instId {OMS_SPOT_INST}"
        ),
    }


def xperp_named_status() -> dict[str, Any]:
    return {
        "venue": "xperp",
        "md_inst_id": XPERP_MD,
        "status": "unavailable",
        "research_md": False,
        "orderable": False,
        "label": (
            f"{XPERP_MD} has no public history on named windows; "
            "skipped (fail closed, no invented bars)"
        ),
    }


def research_perp_md() -> dict[str, Any]:
    return {
        "venue": "research_perp",
        "md_inst_id": RESEARCH_PERP_MD,
        "research_md": True,
        "orderable": False,
        "label": (
            f"research perp {RESEARCH_PERP_MD}; not X-Perp {XPERP_MD}; not orderable"
        ),
    }


def fetch_closed_history(
    client: Any,
    inst_id: str,
    *,
    start_ms: int,
    end_ms: int,
    rest_base: str,
    pause_s: float,
    max_pages: int = NAMED_HISTORY_MAX_PAGES,
) -> tuple[list[Bar], list[Bar], str | None]:
    """history-candles only (`after` = end_ms, walk backward). No /market/candles merge."""
    err: str | None = None
    try:
        b15 = fetch_okx_history_candles(
            client,
            inst_id,
            "15m",
            rest_base=rest_base,
            start_ms=start_ms,
            end_ms=end_ms,
            pause_s=pause_s,
            max_pages=max_pages,
        )
    except (PaperDataError, Exception) as exc:  # noqa: BLE001 — empty is a skip, not a fake
        return [], [], f"{type(exc).__name__}:{exc}"
    try:
        h1 = fetch_okx_history_candles(
            client,
            inst_id,
            "1H",
            rest_base=rest_base,
            start_ms=start_ms,
            end_ms=end_ms,
            pause_s=pause_s,
            max_pages=max_pages,
        )
    except (PaperDataError, Exception) as exc:  # noqa: BLE001
        err = f"1h:{type(exc).__name__}:{exc}"
        h1 = resample_1h(b15)
    if not h1:
        h1 = resample_1h(b15)
    return b15, h1, err


def _span_meta(
    requested_start: int,
    requested_end: int,
    bars: list[Bar],
) -> dict[str, Any]:
    if not bars:
        return {
            "requested_start_ms": requested_start,
            "requested_end_ms": requested_end,
            "fetched_start_ms": None,
            "fetched_end_ms": None,
            "n_bars_15m": 0,
            "span_incomplete": True,
            "empty": True,
        }
    got_start = bars[0].ts_open_ms
    got_end = bars[-1].ts_close_ms
    incomplete = got_start > requested_start + 15 * 60 * 1000 or got_end < requested_end - 15 * 60 * 1000
    return {
        "requested_start_ms": requested_start,
        "requested_end_ms": requested_end,
        "fetched_start_ms": got_start,
        "fetched_end_ms": got_end,
        "n_bars_15m": len(bars),
        "span_incomplete": bool(incomplete),
        "empty": False,
    }


def _replay_one_leg(
    *,
    journal: ReplayJournal,
    strategy: Any,
    venue_key: str,
    md_inst: str,
    b15: list[Bar],
    b1h: list[Bar],
    window: NamedWindow,
    md_meta: dict[str, Any],
    fetch_err: str | None,
) -> dict[str, Any]:
    span = _span_meta(window.start_ms, window.end_ms_exclusive, b15)
    if not b15:
        return {
            "venue": venue_key,
            "status": "skipped",
            "reason": fetch_err or "empty",
            **md_meta,
            **span,
            "n_signals": 0,
            "n_long": 0,
            "n_short": 0,
            "place_orders": False,
        }
    sigs = scan_signals(strategy, b15, b1h)
    n_long, n_short = _count_sides(sigs)
    for sig in sigs:
        journal.append(
            "decisions",
            {
                "kind": "breakout_signal",
                **signal_to_dict(sig, venue=venue_key),
                "window_id": window.id,
                "mdInstId": md_inst,
                "research_md": True,
                "place_orders": False,
            },
            ts_ms=sig.bar_ts_ms,
        )
    return {
        "venue": venue_key,
        "status": "ok",
        **md_meta,
        **span,
        "n_bars_1h": len(b1h),
        "n_signals": len(sigs),
        "n_long": n_long,
        "n_short": n_short,
        "fetch_error": fetch_err,
        "place_orders": False,
        "window_id": window.id,
    }


def run_named_replay(
    cfg: Any,
    *,
    windows: str | list[NamedWindow],
    venue: str = "spot",
    data_dir: str | Path = "data",
    rest_base: str | None = None,
    client: Any | None = None,
    bars_by_window: dict[str, dict[str, tuple[list[Bar], list[Bar]]]] | None = None,
    pause_s: float = 0.12,
    try_research_perp: bool = True,
    now_ms: int | None = None,
) -> dict[str, Any]:
    """Replay locked breakout on calendar windows. No similar-regime. No orders."""
    specs = windows if isinstance(windows, list) else parse_windows_arg(windows)
    keys = parse_venue_arg(venue)
    ts = int(now_ms if now_ms is not None else utc_ms())
    rid = new_run_id("named")
    journal = ReplayJournal(data_dir, rid, source=NAMED_SOURCE)
    strategy = strategy_from_app_config(cfg)
    demo = getattr(getattr(cfg, "okx", None), "doge_demo", None)
    paper_eq = float(getattr(demo, "paper_equity_eur", PAPER_EQUITY_EUR) or PAPER_EQUITY_EUR)
    rest = (rest_base or getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip(
        "/"
    )

    journal.append(
        "events",
        {
            "kind": "named_window_replay_start",
            "place_orders": False,
            "venue": venue,
            "window_ids": [w.id for w in specs],
            "paper_equity_eur": paper_eq,
            "research_spot_md": RESEARCH_SPOT_MD,
            "oms_spot_inst": OMS_SPOT_INST,
        },
        ts_ms=ts,
    )

    own_client = False
    http = client
    if bars_by_window is None and http is None:
        import httpx

        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
        own_client = True

    window_rows: list[dict[str, Any]] = []
    try:
        for win in specs:
            legs: list[dict[str, Any]] = []
            errors: list[str] = []
            if "xperp" in keys:
                legs.append({**xperp_named_status(), "window_id": win.id, "place_orders": False})
            if "spot" in keys:
                meta = spot_research_md()
                injected = None
                if bars_by_window is not None:
                    injected = (bars_by_window.get(win.id) or {}).get("spot")
                if injected is not None:
                    b15, b1h = injected
                    fetch_err = None if b15 else "empty_injected"
                else:
                    assert http is not None
                    b15, b1h, fetch_err = fetch_closed_history(
                        http,
                        RESEARCH_SPOT_MD,
                        start_ms=win.start_ms,
                        end_ms=win.end_ms_exclusive,
                        rest_base=rest,
                        pause_s=pause_s,
                    )
                if fetch_err and not b15:
                    errors.append(f"spot:{fetch_err}")
                legs.append(
                    _replay_one_leg(
                        journal=journal,
                        strategy=strategy,
                        venue_key="spot",
                        md_inst=RESEARCH_SPOT_MD,
                        b15=b15,
                        b1h=b1h,
                        window=win,
                        md_meta=meta,
                        fetch_err=fetch_err,
                    )
                )
            if try_research_perp:
                meta = research_perp_md()
                injected = None
                if bars_by_window is not None:
                    injected = (bars_by_window.get(win.id) or {}).get("research_perp")
                if injected is not None:
                    b15, b1h = injected
                    fetch_err = None if b15 else "empty_injected"
                elif http is not None:
                    b15, b1h, fetch_err = fetch_closed_history(
                        http,
                        RESEARCH_PERP_MD,
                        start_ms=win.start_ms,
                        end_ms=win.end_ms_exclusive,
                        rest_base=rest,
                        pause_s=pause_s,
                    )
                else:
                    b15, b1h, fetch_err = [], [], "no_client"
                if not b15:
                    legs.append(
                        {
                            **meta,
                            "status": "unavailable",
                            "reason": fetch_err or "empty",
                            "window_id": win.id,
                            "n_signals": 0,
                            "n_long": 0,
                            "n_short": 0,
                            "place_orders": False,
                            **_span_meta(win.start_ms, win.end_ms_exclusive, b15),
                        }
                    )
                else:
                    legs.append(
                        _replay_one_leg(
                            journal=journal,
                            strategy=strategy,
                            venue_key="research_perp",
                            md_inst=RESEARCH_PERP_MD,
                            b15=b15,
                            b1h=b1h,
                            window=win,
                            md_meta=meta,
                            fetch_err=fetch_err,
                        )
                    )
            n_sig = sum(int(leg.get("n_signals") or 0) for leg in legs)
            n_long = sum(int(leg.get("n_long") or 0) for leg in legs)
            n_short = sum(int(leg.get("n_short") or 0) for leg in legs)
            any_ok = any(leg.get("status") == "ok" for leg in legs)
            row = {
                "window_id": win.id,
                "label": win.label,
                "ok": any_ok,
                "place_orders": False,
                "source": NAMED_SOURCE,
                "n_signals": n_sig,
                "n_long": n_long,
                "n_short": n_short,
                "legs": legs,
                "errors": errors,
            }
            window_rows.append(row)
    finally:
        if own_client and http is not None:
            http.close()

    summary: dict[str, Any] = {
        "ok": any(w.get("ok") for w in window_rows),
        "dry_run": True,
        "place_orders": False,
        "mode": "named-window",
        "source": NAMED_SOURCE,
        "run_id": rid,
        "venue": venue,
        "window_ids": [w.id for w in specs],
        "paper_equity_eur": paper_eq,
        "n_signals": sum(int(w.get("n_signals") or 0) for w in window_rows),
        "n_long": sum(int(w.get("n_long") or 0) for w in window_rows),
        "n_short": sum(int(w.get("n_short") or 0) for w in window_rows),
        "windows": window_rows,
        "disclaimer": (
            "paper/research only. named-window ≠ forecast. "
            f"spot MD is {RESEARCH_SPOT_MD}, not OMS {OMS_SPOT_INST}. "
            "xperp skipped on these dates. replay ≠ live Phase A week."
        ),
    }
    journal.append(
        "events",
        {"kind": "named_window_replay_end", "window_id": ",".join(w.id for w in specs), **summary},
        ts_ms=ts,
    )
    journal.write_summary(summary, ts_ms=ts)
    summary["log_dir"] = str(journal.root / utc_date_str(ts))
    return summary


def run_named_shadow(
    cfg: Any,
    *,
    windows: str | list[NamedWindow],
    venue: str = "spot",
    data_dir: str | Path = "data",
    rest_base: str | None = None,
    client: Any | None = None,
    bars_by_window: dict[str, dict[str, tuple[list[Bar], list[Bar]]]] | None = None,
    pause_s: float = 0.12,
    try_research_perp: bool = True,
    now_ms: int | None = None,
) -> dict[str, Any]:
    """Shadow each named window independently. No orders. No similar-regime default."""
    from atlas.paper.shadow import run_shadow

    specs = windows if isinstance(windows, list) else parse_windows_arg(windows)
    ts = int(now_ms if now_ms is not None else utc_ms())
    rest = (rest_base or getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip(
        "/"
    )
    keys = parse_venue_arg(venue)

    own_client = False
    http = client
    if bars_by_window is None and http is None:
        import httpx

        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
        own_client = True

    window_rows: list[dict[str, Any]] = []
    try:
        for win in specs:
            bars_by_venue: dict[str, tuple[list[Bar], list[Bar]]] = {}
            errors: list[str] = []
            legs_meta: list[dict[str, Any]] = []
            if "xperp" in keys:
                legs_meta.append({**xperp_named_status(), "window_id": win.id})
            if "spot" in keys:
                meta = spot_research_md()
                injected = None
                if bars_by_window is not None:
                    injected = (bars_by_window.get(win.id) or {}).get("spot")
                if injected is not None:
                    b15, b1h = injected
                    fetch_err = None if b15 else "empty_injected"
                else:
                    assert http is not None
                    b15, b1h, fetch_err = fetch_closed_history(
                        http,
                        RESEARCH_SPOT_MD,
                        start_ms=win.start_ms,
                        end_ms=win.end_ms_exclusive,
                        rest_base=rest,
                        pause_s=pause_s,
                    )
                if not b15:
                    errors.append(f"spot:{fetch_err or 'empty'}")
                    legs_meta.append(
                        {
                            **meta,
                            "status": "skipped",
                            "reason": fetch_err or "empty",
                            "window_id": win.id,
                            **_span_meta(win.start_ms, win.end_ms_exclusive, b15),
                        }
                    )
                else:
                    bars_by_venue["spot"] = (b15, b1h)
                    legs_meta.append({**meta, "status": "ok", "window_id": win.id, **_span_meta(win.start_ms, win.end_ms_exclusive, b15)})
            if try_research_perp:
                injected = None
                if bars_by_window is not None:
                    injected = (bars_by_window.get(win.id) or {}).get("research_perp")
                if injected is not None:
                    b15, b1h = injected
                    fetch_err = None if b15 else "empty_injected"
                elif http is not None:
                    b15, b1h, fetch_err = fetch_closed_history(
                        http,
                        RESEARCH_PERP_MD,
                        start_ms=win.start_ms,
                        end_ms=win.end_ms_exclusive,
                        rest_base=rest,
                        pause_s=pause_s,
                    )
                else:
                    b15, b1h, fetch_err = [], [], "no_client"
                if b15:
                    bars_by_venue["research_perp"] = (b15, b1h)
                    legs_meta.append(
                        {**research_perp_md(), "status": "ok", "window_id": win.id, **_span_meta(win.start_ms, win.end_ms_exclusive, b15)}
                    )
                else:
                    legs_meta.append(
                        {
                            **research_perp_md(),
                            "status": "unavailable",
                            "reason": fetch_err or "empty",
                            "window_id": win.id,
                        }
                    )

            if not bars_by_venue:
                window_rows.append(
                    {
                        "window_id": win.id,
                        "label": win.label,
                        "ok": False,
                        "place_orders": False,
                        "source": NAMED_SOURCE,
                        "n_signals": 0,
                        "n_would_place": 0,
                        "n_blocked_by_reason": {},
                        "legs": legs_meta,
                        "errors": errors or ["no_bars"],
                    }
                )
                continue

            shadow_venue = "spot" if "spot" in bars_by_venue and "research_perp" not in bars_by_venue else (
                "both" if len(bars_by_venue) > 1 else next(iter(bars_by_venue))
            )
            # run_shadow keys are spot|xperp|both only. Map research_perp as extra symbol via bars.
            # parse_venue_arg rejects unknown. Pass venue=spot and include only spot in bars_by_venue
            # plus research_perp under a fake key? parse_venue_arg("spot") only iterates spot.
            # Put research_perp bars under a second key only if we extend parse...
            # Simplest: shadow spot only for named windows; research_perp replay-only unless
            # we pass bars as additional symbols... run_shadow uses parse_venue_arg then
            # bars_by_venue.get(key) for key in keys.
            #
            # For named shadow, only shadow the spot research MD (DOGE-USDT). Perp research
            # stays replay-only unless we add it as a second run.
            spot_only = {}
            if "spot" in bars_by_venue:
                spot_only["spot"] = bars_by_venue["spot"]
            if not spot_only:
                window_rows.append(
                    {
                        "window_id": win.id,
                        "ok": False,
                        "place_orders": False,
                        "source": NAMED_SOURCE,
                        "n_would_place": 0,
                        "legs": legs_meta,
                        "errors": errors + ["no_spot_bars_for_shadow"],
                    }
                )
                continue
            sh = run_shadow(
                cfg,
                venue="spot",
                data_dir=data_dir,
                bars_by_venue=spot_only,
                pause_s=0.0,
                now_ms=ts,
                journal_source=NAMED_SOURCE,
                extra_event={"window_id": win.id, "mode": "named-window"},
            )
            window_rows.append(
                {
                    "window_id": win.id,
                    "label": win.label,
                    "ok": bool(sh.get("ok")),
                    "place_orders": False,
                    "source": NAMED_SOURCE,
                    "n_signals": sh.get("n_signals"),
                    "n_would_place": sh.get("n_would_place"),
                    "n_blocked": sh.get("n_blocked"),
                    "n_blocked_by_reason": sh.get("n_blocked_by_reason"),
                    "n_open": sh.get("n_open"),
                    "n_flatten": sh.get("n_flatten"),
                    "n_kills": sh.get("n_kills"),
                    "legs": legs_meta,
                    "errors": errors,
                    "research": sh.get("research"),
                    "log_dir": sh.get("log_dir"),
                }
            )
    finally:
        if own_client and http is not None:
            http.close()

    return {
        "ok": any(w.get("ok") for w in window_rows),
        "dry_run": True,
        "place_orders": False,
        "mode": "named-window",
        "source": NAMED_SOURCE,
        "venue": venue,
        "window_ids": [w.id for w in specs],
        "n_signals": sum(int(w.get("n_signals") or 0) for w in window_rows),
        "n_would_place": sum(int(w.get("n_would_place") or 0) for w in window_rows),
        "windows": window_rows,
        "disclaimer": (
            "paper/research only. named-window ≠ forecast. "
            "shadow ≠ Phase C. research fields are not_a_forecast."
        ),
    }
