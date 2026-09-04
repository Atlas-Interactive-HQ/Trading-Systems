"""Read-only live20 chart: public candles + fill marks from journals. No keys."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from atlas.common.time import utc_ms
from atlas.paper.md import (
    OKX_REST,
    USER_AGENT,
    PaperDataError,
    fetch_okx_candles,
    load_jsonl_candles,
    persist_candles,
)
from atlas.paper.types import Bar

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOCKED_INST = "DOGE-USDC"
LIVE20_SOURCE = "live20-roundtrip"
DEFAULT_BAR = "5m"
DEFAULT_LIMIT = 300
CACHE_TTL_MS = 60_000
FETCH_TIMEOUT_S = 8.0


@dataclass
class Live20Fill:
    ts_ms: int | None
    ts_utc: str | None
    side: str
    px: float
    sz: float | None
    ord_id: str | None
    fee: str | None
    fee_ccy: str | None
    inst_id: str
    kind: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _dated_event_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    for day in sorted(p for p in root.iterdir() if p.is_dir() and _DATE_RE.match(p.name)):
        path = day / "events.jsonl"
        if path.is_file():
            out.append(path)
    return out


def _ts_utc(ts_ms: int | None) -> str | None:
    if ts_ms is None:
        return None
    try:
        dt = datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _f(raw: Any) -> float | None:
    if raw in (None, ""):
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def load_live20_events(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _dated_event_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    rows.sort(key=lambda r: (int(r.get("ts_ms") or 0), int(r.get("seq") or 0)))
    return rows


def derive_fills(events: list[dict[str, Any]], *, inst_default: str = LOCKED_INST) -> list[Live20Fill]:
    """Filled sell/buy marks from live20 journals. Journals-only — no balances."""
    inst = inst_default
    fills: list[Live20Fill] = []
    for ev in events:
        if ev.get("instId"):
            inst = str(ev.get("instId"))
        kind = str(ev.get("kind") or "")
        state = str(ev.get("state") or "").lower()
        if kind not in {"sell_poll", "buy_poll"}:
            continue
        if state != "filled":
            continue
        px = _f(ev.get("avgPx") or ev.get("px"))
        if px is None:
            continue
        side = str(ev.get("side") or ("sell" if kind == "sell_poll" else "buy")).lower()
        if side not in {"buy", "sell"}:
            side = "sell" if kind == "sell_poll" else "buy"
        sz = _f(ev.get("accFillSz") or ev.get("sz"))
        ts = None
        try:
            ts = int(ev.get("ts_ms")) if ev.get("ts_ms") is not None else None
        except (TypeError, ValueError):
            ts = None
        fills.append(
            Live20Fill(
                ts_ms=ts,
                ts_utc=_ts_utc(ts),
                side=side,
                px=px,
                sz=sz,
                ord_id=str(ev.get("ordId") or "") or None,
                fee=str(ev.get("fee")) if ev.get("fee") is not None else None,
                fee_ccy=str(ev.get("feeCcy") or "") or None,
                inst_id=str(ev.get("instId") or inst),
                kind=kind,
            )
        )
    return fills


def journal_net_doge(fills: list[Live20Fill]) -> float:
    """Best-effort DOGE inventory from fills only (not a live balance)."""
    net = 0.0
    for f in fills:
        sz = float(f.sz or 0.0)
        if f.side == "sell":
            net -= sz
        elif f.side == "buy":
            net += sz
    return net


def last_inst_id(events: list[dict[str, Any]], fills: list[Live20Fill], default: str = LOCKED_INST) -> str:
    for f in reversed(fills):
        if f.inst_id:
            return f.inst_id
    for ev in reversed(events):
        if ev.get("instId"):
            return str(ev.get("instId"))
    return default


def _cache_path(root: Path, inst: str, bar: str) -> Path:
    safe = inst.replace("/", "_")
    return Path(root) / "md" / f"{safe}_{bar}.jsonl"


def load_public_candles(
    inst: str,
    *,
    cache_root: Path,
    bar: str = DEFAULT_BAR,
    limit: int = DEFAULT_LIMIT,
    client: httpx.Client | None = None,
    timeout_s: float = FETCH_TIMEOUT_S,
) -> tuple[list[Bar], str | None]:
    """Public unsigned candles. Fail closed to empty + error string. Never invents bars."""
    cache = _cache_path(cache_root, inst, bar)
    now = utc_ms()
    if cache.is_file() and cache.stat().st_size > 0:
        age_ms = now - int(cache.stat().st_mtime * 1000)
        if age_ms <= CACHE_TTL_MS:
            try:
                return load_jsonl_candles(cache, symbol=inst, bar=bar), None
            except PaperDataError:
                pass
    own = False
    http = client
    if http is None:
        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=timeout_s)
        own = True
    try:
        bars = fetch_okx_candles(http, inst, bar, rest_base=OKX_REST, limit=limit)
    except (PaperDataError, httpx.HTTPError, OSError) as exc:
        if cache.is_file() and cache.stat().st_size > 0:
            try:
                return load_jsonl_candles(cache, symbol=inst, bar=bar), f"stale cache ({type(exc).__name__})"
            except PaperDataError:
                pass
        return [], f"{type(exc).__name__}: {exc}"
    finally:
        if own and http is not None:
            http.close()
    if bars:
        persist_candles(cache, bars)
    return bars, None


def svg_price_chart(
    bars: list[Bar],
    fills: list[Live20Fill],
    *,
    width: int = 760,
    height: int = 280,
) -> str:
    """SVG line of closes + horizontal fill lines. Empty string if no bars."""
    if not bars:
        return ""
    pad_l, pad_r, pad_t, pad_b = 52, 12, 12, 28
    xs = list(range(len(bars)))
    closes = [float(b.close) for b in bars]
    ys = list(closes)
    for f in fills:
        ys.append(f.px)
    y_min = min(ys)
    y_max = max(ys)
    if y_max <= y_min:
        y_max = y_min + 1e-9
    inner_w = width - pad_l - pad_r
    inner_h = height - pad_t - pad_b

    def x_at(i: int) -> float:
        if len(xs) <= 1:
            return pad_l + inner_w / 2
        return pad_l + inner_w * (i / (len(xs) - 1))

    def y_at(px: float) -> float:
        return pad_t + inner_h * (1.0 - (px - y_min) / (y_max - y_min))

    pts = " ".join(f"{x_at(i):.1f},{y_at(c):.1f}" for i, c in enumerate(closes))
    lines = [
        f'<svg class="live20-chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="DOGE-USDC close with live20 fills">',
        f'<rect x="0" y="0" width="{width}" height="{height}" class="live20-chart-bg"/>',
        f'<polyline class="live20-price" fill="none" points="{pts}"/>',
    ]
    for f in fills:
        y = y_at(f.px)
        cls = "live20-fill-buy" if f.side == "buy" else "live20-fill-sell"
        lines.append(
            f'<line class="{cls}" x1="{pad_l}" x2="{width - pad_r}" y1="{y:.1f}" y2="{y:.1f}"/>'
        )
        label = f"{f.side} {f.px:g}"
        lines.append(
            f'<text class="{cls}-label" x="{width - pad_r - 4}" y="{y - 4:.1f}" text-anchor="end">{label}</text>'
        )
    lines.append(
        f'<text class="live20-axis" x="{pad_l - 6}" y="{pad_t + 10}" text-anchor="end">{y_max:.6g}</text>'
    )
    lines.append(
        f'<text class="live20-axis" x="{pad_l - 6}" y="{height - pad_b}" text-anchor="end">{y_min:.6g}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines)


def build_live20_page(
    root: Path,
    *,
    inst_default: str = LOCKED_INST,
    bars: list[Bar] | None = None,
    md_error: str | None = None,
    skip_fetch: bool = False,
) -> dict[str, Any]:
    events = load_live20_events(root)
    fills = derive_fills(events, inst_default=inst_default)
    inst = last_inst_id(events, fills, inst_default)
    err = md_error
    candle_bars = bars
    if candle_bars is None and not skip_fetch:
        candle_bars, err = load_public_candles(inst, cache_root=root)
    candle_bars = candle_bars or []
    svg = svg_price_chart(candle_bars, fills)
    net = journal_net_doge(fills)
    return {
        "inst_id": inst,
        "fills": fills,
        "fill_dicts": [f.as_dict() for f in fills],
        "n_events": len(events),
        "n_fills": len(fills),
        "n_bars": len(candle_bars),
        "bar": DEFAULT_BAR,
        "svg": svg,
        "md_error": err,
        "net_doge": net,
        "has_journals": bool(events),
        "source": LIVE20_SOURCE,
        "not_a_forecast": True,
        "place_orders": False,
    }
