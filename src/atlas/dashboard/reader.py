"""Read local paper/OMS journals for the dashboard. Never loads exchange keys."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from atlas.common.config import AppConfig, load_config
from atlas.common.time import utc_ms
from atlas.oms.doge_demo_loop import LOCKED_SPOT_INST, LOCKED_XPERP_INST

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SECRET_KEYS = {
    "api_key",
    "api_secret",
    "passphrase",
    "secret",
    "ok-access-key",
    "ok-access-sign",
    "ok-access-timestamp",
    "ok-access-passphrase",
    "private_key",
    "token",
    "password",
    "authorization",
}
_SECRET_NAME_FRAGMENTS = (
    "okx-eea",
    "secret",
    "credential",
    "passphrase",
    "private_key",
)
SIGNAL_KINDS = frozenset({"breakout_signal", "breakout_current"})
SESSION_KINDS = frozenset({"doge_demo_session_start", "doge_demo_session_end"})
ORDER_CANCEL_HINTS = frozenset({"cancel", "cancelled", "canceled"})
DEFAULT_LIMIT = 200


def bundled_fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


def redact(obj: Any) -> Any:
    """Mask secret-like keys. Never returns raw key material."""
    if isinstance(obj, Mapping):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in _SECRET_KEYS or lk.startswith("ok-access") or "passphrase" in lk:
                out[str(k)] = "***"
            elif any(frag in lk for frag in ("api_key", "api_secret", "private_key")):
                out[str(k)] = "***"
            else:
                out[str(k)] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


def fmt_ts_ms(ts_ms: int | None) -> str | None:
    if ts_ms is None:
        return None
    try:
        ts = int(ts_ms)
    except (TypeError, ValueError):
        return None
    if ts <= 0:
        return None
    dt = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _is_secret_filename(name: str) -> bool:
    lower = name.lower()
    return any(frag in lower for frag in _SECRET_NAME_FRAGMENTS)


def _safe_journal_file(path: Path) -> bool:
    if not path.is_file():
        return False
    name = path.name
    if _is_secret_filename(name):
        return False
    return name.endswith(".jsonl") or name.endswith(".json")


@dataclass
class ParseError:
    path: str
    line: int | None
    error: str


@dataclass
class SignalRow:
    ts_ms: int | None
    ts_utc: str | None
    kind: str
    venue: str
    symbol: str
    side: str
    stop: float | None
    reason: str
    bar_ts_ms: int | None
    run_id: str | None
    extras: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class JournalRow:
    ts_ms: int | None
    ts_utc: str | None
    channel: str
    kind: str
    venue: str
    inst_id: str
    run_id: str | None
    summary: str
    record: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["record"] = redact(self.record)
        return d


@dataclass
class Overview:
    paper_equity_eur: float
    daily_kill_frac: float
    per_trade_risk_frac: float
    kill_status: str
    kill_reason: str | None
    killed: bool
    mode: str
    mode_label: str
    last_session_ts_ms: int | None
    last_session_utc: str | None
    last_session_ok: bool | None
    last_run_id: str | None
    paper_pnl: float | None
    open_inst: str | None
    open_side: str | None
    utc_day: str | None
    n_signals: int
    n_orders: int
    universe_spot: str
    universe_xperp: str
    empty: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthItem:
    id: str
    label: str
    status: str  # ok | warn | fail
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthReport:
    status: str
    items: list[HealthItem]
    n_parse_errors: int
    generated_at_ms: int
    secrets_loaded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "items": [i.as_dict() for i in self.items],
            "n_parse_errors": self.n_parse_errors,
            "generated_at_ms": self.generated_at_ms,
            "generated_at_utc": fmt_ts_ms(self.generated_at_ms),
            "secrets_loaded": False,
        }


@dataclass
class OmsActivity:
    decisions: list[JournalRow]
    orders: list[JournalRow]
    cancels: list[JournalRow]
    events: list[JournalRow]
    snapshots: list[JournalRow]
    empty: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "decisions": [r.as_dict() for r in self.decisions],
            "orders": [r.as_dict() for r in self.orders],
            "cancels": [r.as_dict() for r in self.cancels],
            "events": [r.as_dict() for r in self.events],
            "snapshots": [r.as_dict() for r in self.snapshots],
            "empty": self.empty,
        }


@dataclass
class DashboardSnapshot:
    overview: Overview
    signals: list[SignalRow]
    latest_by_venue: dict[str, SignalRow | None]
    oms: OmsActivity
    health: HealthReport
    generated_at_ms: int
    data_dir: str
    using_fixtures: bool

    @property
    def generated_at_utc(self) -> str | None:
        return fmt_ts_ms(self.generated_at_ms)

    def as_dict(self) -> dict[str, Any]:
        return redact(
            {
                "overview": self.overview.as_dict(),
                "signals": [s.as_dict() for s in self.signals],
                "latest_by_venue": {
                    k: (v.as_dict() if v is not None else None)
                    for k, v in self.latest_by_venue.items()
                },
                "oms": self.oms.as_dict(),
                "health": self.health.as_dict(),
                "generated_at_ms": self.generated_at_ms,
                "generated_at_utc": fmt_ts_ms(self.generated_at_ms),
                "data_dir": self.data_dir,
                "using_fixtures": self.using_fixtures,
            }
        )


def _dated_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out = [p for p in root.iterdir() if p.is_dir() and _DATE_RE.match(p.name)]
    return sorted(out, key=lambda p: p.name)


def _read_json_file(path: Path, errors: list[ParseError]) -> dict[str, Any] | None:
    if not _safe_journal_file(path):
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(ParseError(str(path), None, f"{type(exc).__name__}: {exc}"))
        return None
    if not isinstance(raw, dict):
        errors.append(ParseError(str(path), None, "expected object"))
        return None
    return redact(raw)


def _read_jsonl(path: Path, errors: list[ParseError]) -> list[dict[str, Any]]:
    if not _safe_journal_file(path):
        return []
    rows: list[dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(ParseError(str(path), None, f"{type(exc).__name__}: {exc}"))
        return []
    for i, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(ParseError(str(path), i, f"{type(exc).__name__}: {exc}"))
            continue
        if not isinstance(obj, dict):
            errors.append(ParseError(str(path), i, "expected object"))
            continue
        rows.append(redact(obj))
    return rows


def _ts(row: Mapping[str, Any]) -> int | None:
    raw = row.get("ts_ms")
    try:
        if raw is None:
            return None
        return int(raw)
    except (TypeError, ValueError):
        return None


def _sort_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (_ts(r) or 0, int(r.get("seq") or 0)), reverse=True)


def _kind(row: Mapping[str, Any]) -> str:
    return str(row.get("kind") or row.get("type") or "")


def _venue(row: Mapping[str, Any]) -> str:
    v = row.get("venue")
    if v:
        return str(v)
    extras = row.get("extras")
    if isinstance(extras, Mapping) and extras.get("venue"):
        return str(extras.get("venue"))
    return ""


def _inst(row: Mapping[str, Any]) -> str:
    for key in ("instId", "inst_id", "symbol", "open_inst"):
        val = row.get(key)
        if val:
            return str(val)
    return str(row.get("mdInstId") or "")


def _summarize(row: Mapping[str, Any]) -> str:
    bits: list[str] = []
    kind = _kind(row)
    if kind:
        bits.append(kind)
    if row.get("placed") is True:
        bits.append("geplaatst")
    elif row.get("placed") is False:
        bits.append("niet geplaatst")
    if row.get("cancelled") is True:
        bits.append("geannuleerd")
    reason = row.get("reason")
    if reason:
        bits.append(str(reason))
    side = row.get("side")
    if side:
        bits.append(str(side))
    if row.get("dry_run") is True:
        bits.append("dry-run")
    return " · ".join(bits) if bits else "—"


def _to_journal_row(row: Mapping[str, Any], channel: str) -> JournalRow:
    ts = _ts(row)
    return JournalRow(
        ts_ms=ts,
        ts_utc=fmt_ts_ms(ts),
        channel=channel,
        kind=_kind(row),
        venue=_venue(row),
        inst_id=_inst(row),
        run_id=str(row.get("run_id")) if row.get("run_id") else None,
        summary=_summarize(row),
        record=dict(row),
    )


def _to_signal(row: Mapping[str, Any]) -> SignalRow:
    ts = _ts(row)
    stop_raw = row.get("stop")
    try:
        stop = float(stop_raw) if stop_raw is not None and str(stop_raw) != "" else None
    except (TypeError, ValueError):
        stop = None
    extras = row.get("extras") if isinstance(row.get("extras"), dict) else {}
    bar_ts = row.get("bar_ts_ms")
    try:
        bar_ts_i = int(bar_ts) if bar_ts is not None else None
    except (TypeError, ValueError):
        bar_ts_i = None
    return SignalRow(
        ts_ms=ts,
        ts_utc=fmt_ts_ms(ts),
        kind=_kind(row),
        venue=_venue(row),
        symbol=str(row.get("symbol") or _inst(row) or ""),
        side=str(row.get("side") or ""),
        stop=stop,
        reason=str(row.get("reason") or ""),
        bar_ts_ms=bar_ts_i,
        run_id=str(row.get("run_id")) if row.get("run_id") else None,
        extras=dict(extras),
    )


def _load_channel(root: Path, channel: str, errors: list[ParseError]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for day in _dated_dirs(root):
        path = day / f"{channel}.jsonl"
        if path.is_file():
            rows.extend(_read_jsonl(path, errors))
    return _sort_rows(rows)


def _load_oms_state(oms_root: Path, errors: list[ParseError]) -> dict[str, Any]:
    path = oms_root / "state.json"
    if not path.is_file():
        return {}
    return _read_json_file(path, errors) or {}


def _mode_from_events(events: list[dict[str, Any]]) -> tuple[str, str, dict[str, Any] | None]:
    sessions = [e for e in events if _kind(e) in SESSION_KINDS]
    if not sessions:
        return "idle", "geen sessie", None
    latest = sessions[0]  # already newest-first
    place = bool(latest.get("place_orders"))
    dry = latest.get("dry_run")
    if place:
        return "demo-orders", "demo (orders-pad)", latest
    if dry is False and latest.get("mode") == "demo":
        return "demo-orders", "demo (orders-pad)", latest
    return "signal-only", "alleen signalen", latest


def _kill_from_state(state: Mapping[str, Any]) -> tuple[bool, str, str | None]:
    if not state:
        return False, "onbekend", None
    killed = bool(state.get("killed"))
    reason = state.get("kill_reason")
    reason_s = str(reason) if reason not in (None, "") else None
    if killed:
        return True, "getript", reason_s
    return False, "vrij", reason_s


def _limit(rows: list[Any], limit: int = DEFAULT_LIMIT) -> list[Any]:
    return rows[: max(0, int(limit))]


def _roll_status(items: list[HealthItem]) -> str:
    if any(i.status == "fail" for i in items):
        return "fail"
    if any(i.status == "warn" for i in items):
        return "warn"
    return "ok"


def _public_risk(cfg: AppConfig) -> dict[str, float]:
    demo = cfg.okx.doge_demo
    paper = cfg.paper
    return {
        "paper_equity_eur": float(demo.paper_equity_eur or paper.equity_eur or 200.0),
        "daily_kill_frac": float(demo.daily_kill_frac or paper.daily_kill_frac or 0.05),
        "per_trade_risk_frac": float(
            demo.per_trade_risk_frac or paper.per_trade_risk_frac or 0.015
        ),
    }


def _live_trade_blocked(cfg: AppConfig) -> bool:
    live = cfg.okx.modes.get("live")
    if live is None:
        return True
    return live.allow_trade is False


def _collector_mtime(raw_root: Path) -> tuple[int | None, str | None]:
    if not raw_root.is_dir():
        return None, None
    latest: float | None = None
    latest_name: str | None = None
    for path in raw_root.rglob("*.jsonl"):
        if _is_secret_filename(path.name):
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if latest is None or mtime > latest:
            latest = mtime
            try:
                latest_name = str(path.relative_to(raw_root))
            except ValueError:
                latest_name = path.name
    if latest is None:
        return None, None
    return int(latest * 1000), latest_name


def load_snapshot(
    data_dir: str | Path,
    *,
    cfg: AppConfig | None = None,
    config_path: str | Path | None = None,
    using_fixtures: bool = False,
    limit: int = DEFAULT_LIMIT,
) -> DashboardSnapshot:
    root = Path(data_dir)
    errors: list[ParseError] = []
    cfg = cfg or load_config(config_path)
    risk = _public_risk(cfg)
    now = utc_ms()

    oms_root = root / "oms"
    paper_root = root / "paper"
    raw_root = root / "raw"

    decisions = _load_channel(oms_root, "decisions", errors)
    orders = _load_channel(oms_root, "orders", errors)
    events = _load_channel(oms_root, "events", errors)
    snapshots = _load_channel(oms_root, "snapshots", errors)
    state = _load_oms_state(oms_root, errors)

    paper_events = _load_channel(paper_root, "events", errors)
    if paper_events:
        events = _sort_rows(events + paper_events)

    signal_rows = [_to_signal(r) for r in decisions if _kind(r) in SIGNAL_KINDS]
    signal_rows = _limit(signal_rows, limit)

    latest_by_venue: dict[str, SignalRow | None] = {"spot": None, "xperp": None}
    for row in signal_rows:
        venue = row.venue if row.venue in latest_by_venue else None
        if venue and latest_by_venue[venue] is None:
            latest_by_venue[venue] = row

    mode, mode_label, session = _mode_from_events(events)
    killed, kill_status, kill_reason = _kill_from_state(state)

    last_session_ts = _ts(session) if session else None
    last_session_ok: bool | None = None
    last_run_id: str | None = None
    if session is not None:
        if "ok" in session:
            last_session_ok = bool(session.get("ok"))
        last_run_id = str(session.get("run_id")) if session.get("run_id") else None

    paper_pnl_raw = state.get("paper_pnl") if state else None
    try:
        paper_pnl = float(paper_pnl_raw) if paper_pnl_raw is not None else None
    except (TypeError, ValueError):
        paper_pnl = None

    order_rows = [_to_journal_row(r, "orders") for r in orders]
    cancel_rows = [
        r
        for r in order_rows
        if r.kind in ORDER_CANCEL_HINTS
        or "cancel" in r.kind
        or r.record.get("cancelled") is True
        or isinstance(r.record.get("cancel"), Mapping)
    ]
    oms = OmsActivity(
        decisions=_limit([_to_journal_row(r, "decisions") for r in decisions], limit),
        orders=_limit(order_rows, limit),
        cancels=_limit(cancel_rows, limit),
        events=_limit([_to_journal_row(r, "events") for r in events], limit),
        snapshots=_limit([_to_journal_row(r, "snapshots") for r in snapshots], limit),
        empty=not (decisions or orders or events or snapshots or state),
    )

    live_blocked = _live_trade_blocked(cfg)
    col_ms, col_name = _collector_mtime(raw_root)
    n_err = len(errors)

    items: list[HealthItem] = [
        HealthItem(
            id="config",
            label="Config",
            status="ok",
            detail="default.yaml geladen (geen sleutels in dit bestand)",
        ),
        HealthItem(
            id="live_blocked",
            label="Live-handel",
            status="ok" if live_blocked else "fail",
            detail=(
                "geblokkeerd in config (allow_trade=false)"
                if live_blocked
                else "FAIL: live allow_trade staat aan — dashboard plaatst alsnog niets"
            ),
        ),
        HealthItem(
            id="secrets",
            label="Exchange-sleutels",
            status="ok",
            detail="niet geladen door dit dashboard",
        ),
        HealthItem(
            id="journals",
            label="OMS-journals",
            status="ok" if not oms.empty else "warn",
            detail=(
                f"{len(decisions)} beslissingen, {len(orders)} orders, {len(events)} events"
                if not oms.empty
                else "leeg — draai een signal-only sessie of start met --fixtures"
            ),
        ),
        HealthItem(
            id="parse",
            label="Journal-parse",
            status="fail" if n_err else "ok",
            detail=f"{n_err} fout(en)" if n_err else "geen parsefouten",
        ),
        HealthItem(
            id="session",
            label="Laatste sessie",
            status=(
                "ok"
                if last_session_ok is True
                else "fail"
                if last_session_ok is False
                else "warn"
            ),
            detail=(
                f"{mode_label} · {fmt_ts_ms(last_session_ts)}"
                if last_session_ts
                else "nog geen doge_demo_session in journals"
            ),
        ),
        HealthItem(
            id="kill",
            label="Kill-switch",
            status="fail" if killed else "ok" if state else "warn",
            detail=kill_reason or kill_status,
        ),
        HealthItem(
            id="collectors",
            label="Public MD (lokaal)",
            status="ok" if col_ms else "warn",
            detail=(
                f"laatste raw: {col_name} · {fmt_ts_ms(col_ms)}"
                if col_ms
                else "geen data/raw/*.jsonl op deze Mac"
            ),
        ),
    ]
    if using_fixtures:
        items.insert(
            3,
            HealthItem(
                id="fixtures",
                label="Bron",
                status="ok",
                detail="gebundelde sample-journals (geen echte sessie)",
            ),
        )

    health = HealthReport(
        status=_roll_status(items),
        items=items,
        n_parse_errors=n_err,
        generated_at_ms=now,
        secrets_loaded=False,
    )

    overview = Overview(
        paper_equity_eur=risk["paper_equity_eur"],
        daily_kill_frac=risk["daily_kill_frac"],
        per_trade_risk_frac=risk["per_trade_risk_frac"],
        kill_status=kill_status,
        kill_reason=kill_reason,
        killed=killed,
        mode=mode,
        mode_label=mode_label,
        last_session_ts_ms=last_session_ts,
        last_session_utc=fmt_ts_ms(last_session_ts),
        last_session_ok=last_session_ok,
        last_run_id=last_run_id,
        paper_pnl=paper_pnl,
        open_inst=str(state.get("open_inst")) if state.get("open_inst") else None,
        open_side=str(state.get("open_side")) if state.get("open_side") else None,
        utc_day=str(state.get("utc_day")) if state.get("utc_day") else None,
        n_signals=len(signal_rows),
        n_orders=len(orders),
        universe_spot=LOCKED_SPOT_INST,
        universe_xperp=LOCKED_XPERP_INST,
        empty=oms.empty,
    )

    display_dir = "fixtures" if using_fixtures else str(root)
    return DashboardSnapshot(
        overview=overview,
        signals=signal_rows,
        latest_by_venue=latest_by_venue,
        oms=oms,
        health=health,
        generated_at_ms=now,
        data_dir=display_dir,
        using_fixtures=using_fixtures,
    )
