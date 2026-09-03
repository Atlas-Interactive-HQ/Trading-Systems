"""Forward EMA long/flat paper observer. Journals only. Never places orders.

Default: signal/state on the last *closed* 1D bar. Optional `--paper-shadow`
advances a 1× hypothetical ledger with next-open fills (same math as the
historical walker). Distinct from Phase A DOGE (`data/oms/`) and Phase B
shadow (`data/shadow/`).

not_a_forecast. OOS CLEAR ≠ live. Not Phase C.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from atlas.collectors.base import new_run_id
from atlas.common.time import utc_date_str, utc_ms
from atlas.paper.ema_eval import DAY_MS, EmaBookSettings, WARMUP_DAYS
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.md import OKX_REST, USER_AGENT, PaperDataError, fetch_okx_candles
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1, ema_series

EMA_OBSERVER_SOURCE = "ema-paper-observer"
EMA_OBSERVER_SYMBOL = "BTC-USDT"
EMA_OBSERVER_BAR = "1D"
LOOKBACK_DAYS = 90
STATE_NAME = "state.json"

KIND_STATE = "ema_state"
KIND_DECISION = "ema_decision"
KIND_FILL = "ema_paper_fill"
KIND_START = "ema_paper_session_start"
KIND_END = "ema_paper_session_end"

DISCLAIMER = (
    "observer only. no exchange orders. research/paper. not_a_forecast. "
    "OOS CLEAR ≠ live. does not replace Phase A DOGE breakout. not Phase C."
)


def ema_root(data_dir: str | Path) -> Path:
    """Journals live under data/ema/, never data/oms/ or data/shadow/."""
    return Path(data_dir) / "ema"


def closed_bars_only(bars: list[Bar]) -> list[Bar]:
    return [b for b in bars if b.closed]


def fetch_recent_daily(
    symbol: str = EMA_OBSERVER_SYMBOL,
    *,
    rest_base: str = OKX_REST,
    lookback_days: int = LOOKBACK_DAYS,
    client: Any | None = None,
) -> list[Bar]:
    """Recent closed 1D bars via public OKX EEA candles. No keys, no trade client."""
    if lookback_days < 1:
        raise ReplayError("lookback_days must be >= 1")
    limit = min(300, max(int(lookback_days), WARMUP_DAYS + 5, 40))
    own = False
    http = client
    if http is None:
        import httpx

        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
        own = True
    try:
        bars = fetch_okx_candles(http, symbol, EMA_OBSERVER_BAR, rest_base=rest_base, limit=limit)
    except (PaperDataError, Exception) as exc:  # noqa: BLE001
        raise ReplayError(f"daily {symbol} empty ({type(exc).__name__}:{exc})") from exc
    finally:
        if own and http is not None:
            http.close()
    bars = closed_bars_only(bars)
    if not bars:
        raise ReplayError(f"daily {symbol} empty (fail closed)")
    cutoff = bars[-1].ts_open_ms - int(lookback_days) * DAY_MS
    bars = [b for b in bars if b.ts_open_ms >= cutoff]
    if not bars:
        raise ReplayError(f"daily {symbol} empty after lookback (fail closed)")
    return bars


def snapshot_from_bars(bars: list[Bar], strategy: EmaTrendV1) -> dict[str, Any]:
    """Current long|flat from the last closed bar. Never short. No lookahead."""
    closed = closed_bars_only(list(bars))
    if not closed:
        raise ReplayError("empty daily history (fail closed)")
    last = closed[-1]
    want = strategy.desired_state(closed)
    if want not in (LONG, FLAT):
        raise ReplayError(f"illegal EMA state {want!r} (never short)")
    closes = [float(b.close) for b in closed]
    fast = ema_series(closes, strategy.params.fast)
    slow = ema_series(closes, strategy.params.slow)
    return {
        "desired": want,
        "ema_fast": fast[-1],
        "ema_slow": slow[-1],
        "last_close": q(last.close),
        "last_open": q(last.open),
        "as_of_bar_ts_open_ms": int(last.ts_open_ms),
        "as_of_bar_ts_close_ms": int(last.ts_close_ms),
        "symbol": last.symbol,
        "n_bars": len(closed),
        "strategy": strategy.label,
        "fast": strategy.params.fast,
        "slow": strategy.params.slow,
        "place_orders": False,
        "not_a_forecast": True,
        "source": EMA_OBSERVER_SOURCE,
    }


def default_ledger(settings: EmaBookSettings, *, symbol: str = EMA_OBSERVER_SYMBOL) -> dict[str, Any]:
    start = float(settings.equity_eur)
    return {
        "source": EMA_OBSERVER_SOURCE,
        "symbol": symbol,
        "cash": q(start),
        "qty": 0.0,
        "entry_px": 0.0,
        "entry_fee": 0.0,
        "pending": None,
        "pending_from_ts_close_ms": None,
        "last_bar_ts_open_ms": None,
        "last_bar_ts_close_ms": None,
        "desired": FLAT,
        "have": FLAT,
        "fees": 0.0,
        "n_trades": 0,
        "n_entries": 0,
        "peak": q(start),
        "max_dd": 0.0,
        "start_equity_eur": start,
        "leverage": 1.0,
        "place_orders": False,
        "not_a_forecast": True,
        "paper_shadow": True,
    }


def load_ledger(path: Path, settings: EmaBookSettings, *, symbol: str) -> dict[str, Any]:
    if not path.is_file():
        return default_ledger(settings, symbol=symbol)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_ledger(settings, symbol=symbol)
    if not isinstance(raw, dict) or raw.get("source") != EMA_OBSERVER_SOURCE:
        return default_ledger(settings, symbol=symbol)
    base = default_ledger(settings, symbol=symbol)
    base.update(raw)
    base["source"] = EMA_OBSERVER_SOURCE
    base["place_orders"] = False
    base["not_a_forecast"] = True
    base["paper_shadow"] = True
    base["leverage"] = 1.0
    if base.get("pending") not in (LONG, FLAT, None):
        base["pending"] = None
    if float(base.get("qty") or 0.0) < 0:
        raise ReplayError("negative qty in EMA ledger (never short)")
    return base


def save_ledger(path: Path, ledger: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(ledger)
    payload["source"] = EMA_OBSERVER_SOURCE
    payload["place_orders"] = False
    payload["not_a_forecast"] = True
    payload.pop("paper_pnl", None)  # never a PnL hero field
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def _fill_pending(
    ledger: dict[str, Any],
    bar: Bar,
    settings: EmaBookSettings,
) -> dict[str, Any] | None:
    pending = ledger.get("pending")
    if pending is None:
        return None
    if pending not in (LONG, FLAT):
        raise ReplayError(f"illegal pending {pending!r} (never short)")
    qty = float(ledger.get("qty") or 0.0)
    cash = float(ledger.get("cash") or 0.0)
    rec: dict[str, Any] | None = None
    if pending == LONG and qty == 0.0:
        px = apply_slippage(bar.open, "buy", settings.slippage_bps)
        denom = px * (1.0 + settings.fee_rate)
        new_qty = q(cash / denom) if denom > 0 else 0.0
        fee = fee_on_notional(new_qty * px, settings.fee_rate)
        ledger["cash"] = q(cash - new_qty * px - fee)
        ledger["qty"] = new_qty
        ledger["entry_px"] = px
        ledger["entry_fee"] = fee
        ledger["fees"] = q(float(ledger.get("fees") or 0.0) + fee)
        ledger["n_entries"] = int(ledger.get("n_entries") or 0) + 1
        rec = {
            "kind": KIND_FILL,
            "side": "buy",
            "qty": new_qty,
            "price": px,
            "fee": fee,
            "ref_price": q(bar.open),
            "reason": "next_open",
        }
    elif pending == FLAT and qty > 0.0:
        px = apply_slippage(bar.open, "sell", settings.slippage_bps)
        fee = fee_on_notional(qty * px, settings.fee_rate)
        entry_px = float(ledger.get("entry_px") or 0.0)
        entry_fee = float(ledger.get("entry_fee") or 0.0)
        net = q(qty * (px - entry_px) - entry_fee - fee)
        ledger["cash"] = q(cash + qty * px - fee)
        ledger["fees"] = q(float(ledger.get("fees") or 0.0) + fee)
        ledger["n_trades"] = int(ledger.get("n_trades") or 0) + 1
        ledger["qty"] = 0.0
        ledger["entry_px"] = 0.0
        ledger["entry_fee"] = 0.0
        rec = {
            "kind": KIND_FILL,
            "side": "sell",
            "qty": q(qty),
            "price": px,
            "fee": fee,
            "ref_price": q(bar.open),
            "pnl": net,
            "reason": "next_open",
        }
    ledger["pending"] = None
    ledger["pending_from_ts_close_ms"] = None
    if rec is None:
        return None
    rec.update(
        {
            "source": EMA_OBSERVER_SOURCE,
            "symbol": bar.symbol,
            "bar": EMA_OBSERVER_BAR,
            "bar_ts_open_ms": int(bar.ts_open_ms),
            "bar_ts_close_ms": int(bar.ts_close_ms),
            "hypothetical": True,
            "place_orders": False,
            "not_a_forecast": True,
            "leverage": 1.0,
        }
    )
    return rec


def _mark_equity(ledger: dict[str, Any], bar: Bar) -> float:
    qty = float(ledger.get("qty") or 0.0)
    cash = float(ledger.get("cash") or 0.0)
    mark = q(cash + (qty * bar.close if qty > 0 else 0.0))
    peak = float(ledger.get("peak") or mark)
    if mark > peak:
        peak = mark
        ledger["peak"] = q(peak)
    dd = peak - mark
    if dd > float(ledger.get("max_dd") or 0.0):
        ledger["max_dd"] = q(dd)
    return mark


def seed_forward_ledger(
    ledger: dict[str, Any],
    snap: dict[str, Any],
) -> dict[str, Any]:
    """First shadow run: record now, queue next-open if already long. No backfill."""
    ledger["desired"] = snap["desired"]
    ledger["have"] = FLAT
    ledger["last_bar_ts_open_ms"] = snap["as_of_bar_ts_open_ms"]
    ledger["last_bar_ts_close_ms"] = snap["as_of_bar_ts_close_ms"]
    if snap["desired"] == LONG:
        ledger["pending"] = LONG
        ledger["pending_from_ts_close_ms"] = snap["as_of_bar_ts_close_ms"]
    else:
        ledger["pending"] = None
        ledger["pending_from_ts_close_ms"] = None
    return ledger


def advance_shadow(
    bars: list[Bar],
    ledger: dict[str, Any],
    strategy: EmaTrendV1,
    settings: EmaBookSettings,
) -> list[dict[str, Any]]:
    """Fill pending at new bar OPENs, then re-decide on that closed bar.

    Skips bars already processed (`last_bar_ts_open_ms`). Never shorts.
    """
    closed = closed_bars_only(list(bars))
    last_open = ledger.get("last_bar_ts_open_ms")
    fills: list[dict[str, Any]] = []
    for i, bar in enumerate(closed):
        if last_open is not None and int(bar.ts_open_ms) <= int(last_open):
            continue
        rec = _fill_pending(ledger, bar, settings)
        if rec is not None:
            fills.append(rec)
        _mark_equity(ledger, bar)
        hist = closed[: i + 1]
        want = strategy.desired_state(hist)
        if want not in (LONG, FLAT):
            raise ReplayError(f"illegal EMA state {want!r} (never short)")
        have = LONG if float(ledger.get("qty") or 0.0) > 0.0 else FLAT
        ledger["desired"] = want
        ledger["have"] = have
        if want != have:
            ledger["pending"] = want
            ledger["pending_from_ts_close_ms"] = int(bar.ts_close_ms)
        else:
            ledger["pending"] = None
            ledger["pending_from_ts_close_ms"] = None
        ledger["last_bar_ts_open_ms"] = int(bar.ts_open_ms)
        ledger["last_bar_ts_close_ms"] = int(bar.ts_close_ms)
    return fills


class EmaPaperJournal:
    """Append-only JSONL under data/ema/{UTC-date}/. Distinct from oms/ and shadow/."""

    def __init__(self, root: str | Path, run_id: str) -> None:
        self.root = Path(root)
        self.run_id = run_id
        self._lock = threading.Lock()
        self._seq = 0

    def _path(self, channel: str, ts_ms: int) -> Path:
        directory = self.root / utc_date_str(ts_ms)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{channel}.jsonl"

    def append(self, channel: str, record: dict[str, Any], *, ts_ms: int | None = None) -> Path:
        ts = int(ts_ms if ts_ms is not None else record.get("ts_ms") or utc_ms())
        with self._lock:
            self._seq += 1
            seq = self._seq
        row = {
            "run_id": self.run_id,
            "seq": seq,
            "source": EMA_OBSERVER_SOURCE,
            "place_orders": False,
            "not_a_forecast": True,
            **record,
            "ts_ms": ts,
            "source": EMA_OBSERVER_SOURCE,
            "place_orders": False,
            "not_a_forecast": True,
        }
        path = self._path(channel, ts)
        line = json.dumps(row, separators=(",", ":"), ensure_ascii=False, default=str)
        with self._lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return path


def _common_fields(snap: dict[str, Any], *, paper_shadow: bool) -> dict[str, Any]:
    return {
        "source": EMA_OBSERVER_SOURCE,
        "strategy": snap.get("strategy"),
        "symbol": snap.get("symbol") or EMA_OBSERVER_SYMBOL,
        "bar": EMA_OBSERVER_BAR,
        "venue": "okx-eea-public",
        "desired": snap.get("desired"),
        "side": snap.get("desired"),  # dashboard SignalRow; long|flat, never short
        "ema_fast": snap.get("ema_fast"),
        "ema_slow": snap.get("ema_slow"),
        "last_close": snap.get("last_close"),
        "as_of_bar_ts_open_ms": snap.get("as_of_bar_ts_open_ms"),
        "as_of_bar_ts_close_ms": snap.get("as_of_bar_ts_close_ms"),
        "bar_ts_ms": snap.get("as_of_bar_ts_close_ms"),
        "paper_shadow": bool(paper_shadow),
        "leverage": 1.0,
        "place_orders": False,
        "not_a_forecast": True,
        "disclaimer": DISCLAIMER,
    }


def run_ema_paper_session(
    cfg: Any,
    *,
    data_dir: str | Path = "data",
    symbol: str = EMA_OBSERVER_SYMBOL,
    paper_shadow: bool = False,
    lookback_days: int = LOOKBACK_DAYS,
    bars: list[Bar] | None = None,
    client: Any | None = None,
    run_id: str | None = None,
    now_ms: int | None = None,
) -> dict[str, Any]:
    """One observer pass. Public MD only. Never constructs a trade client."""
    from atlas.paper.engine import PaperSettings

    settings = EmaBookSettings.from_paper(PaperSettings.from_app_config(cfg))
    strategy = EmaTrendV1(EmaTrendParams(fast=12, slow=30))
    rest = (getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip("/")
    root = ema_root(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    rid = run_id or new_run_id("ema-obs")
    ts = int(now_ms if now_ms is not None else utc_ms())
    journal = EmaPaperJournal(root, rid)

    if bars is None:
        bars = fetch_recent_daily(
            symbol, rest_base=rest, lookback_days=lookback_days, client=client
        )
    bars = closed_bars_only(list(bars))
    if not bars:
        raise ReplayError("empty daily history (fail closed)")

    snap = snapshot_from_bars(bars, strategy)
    fills: list[dict[str, Any]] = []
    ledger: dict[str, Any] | None = None
    state_path = root / STATE_NAME

    if paper_shadow:
        ledger = load_ledger(state_path, settings, symbol=symbol)
        if ledger.get("last_bar_ts_open_ms") is None:
            ledger = seed_forward_ledger(ledger, snap)
        else:
            fills = advance_shadow(bars, ledger, strategy, settings)
            snap = snapshot_from_bars(bars, strategy)
            ledger["desired"] = snap["desired"]
            ledger["have"] = LONG if float(ledger.get("qty") or 0.0) > 0.0 else FLAT
        save_ledger(state_path, ledger)

    start_rec = {
        "kind": KIND_START,
        **_common_fields(snap, paper_shadow=paper_shadow),
        "lookback_days": lookback_days,
        "n_bars": snap.get("n_bars"),
        "ok": True,
        "dry_run": True,
        "mode": "ema-paper-observer",
    }
    events_path = journal.append("events", start_rec, ts_ms=ts)

    decision = {
        "kind": KIND_DECISION,
        **_common_fields(snap, paper_shadow=paper_shadow),
        "reason": "ema12_gt_ema30" if snap["desired"] == LONG else "ema12_le_ema30_flat",
        "n_bars": snap.get("n_bars"),
    }
    if ledger is not None:
        decision["have"] = ledger.get("have")
        decision["pending"] = ledger.get("pending")
        decision["qty"] = ledger.get("qty")
        decision["cash"] = ledger.get("cash")
    decisions_path = journal.append("decisions", decision, ts_ms=ts)

    state_row = {
        "kind": KIND_STATE,
        **_common_fields(snap, paper_shadow=paper_shadow),
        "reason": decision["reason"],
        "n_bars": snap.get("n_bars"),
    }
    journal.append("decisions", state_row, ts_ms=ts)

    fill_paths: list[str] = []
    for fill in fills:
        p = journal.append("events", fill, ts_ms=ts)
        fill_paths.append(str(p))

    end_rec = {
        "kind": KIND_END,
        **_common_fields(snap, paper_shadow=paper_shadow),
        "ok": True,
        "dry_run": True,
        "mode": "ema-paper-observer",
        "n_fills": len(fills),
        "n_bars": snap.get("n_bars"),
    }
    if ledger is not None:
        end_rec["have"] = ledger.get("have")
        end_rec["pending"] = ledger.get("pending")
        end_rec["qty"] = ledger.get("qty")
        end_rec["cash"] = ledger.get("cash")
        end_rec["n_entries"] = ledger.get("n_entries")
        end_rec["n_trades"] = ledger.get("n_trades")
    journal.append("events", end_rec, ts_ms=ts)

    public: dict[str, Any] = {
        "ok": True,
        "place_orders": False,
        "not_a_forecast": True,
        "source": EMA_OBSERVER_SOURCE,
        "strategy": snap.get("strategy"),
        "symbol": snap.get("symbol"),
        "bar": EMA_OBSERVER_BAR,
        "desired": snap.get("desired"),
        "ema_fast": snap.get("ema_fast"),
        "ema_slow": snap.get("ema_slow"),
        "last_close": snap.get("last_close"),
        "as_of_bar_ts_open_ms": snap.get("as_of_bar_ts_open_ms"),
        "as_of_bar_ts_close_ms": snap.get("as_of_bar_ts_close_ms"),
        "paper_shadow": bool(paper_shadow),
        "n_fills": len(fills),
        "run_id": rid,
        "journals": {
            "root": str(root),
            "decisions": str(decisions_path),
            "events": str(events_path),
            "state": str(state_path) if paper_shadow else None,
        },
        "disclaimer": DISCLAIMER,
    }
    if ledger is not None:
        public["hypothetical_ledger"] = {
            "cash": ledger.get("cash"),
            "qty": ledger.get("qty"),
            "have": ledger.get("have"),
            "pending": ledger.get("pending"),
            "n_entries": ledger.get("n_entries"),
            "n_trades": ledger.get("n_trades"),
            "leverage": 1.0,
            "note": "hypothetical 1× next-open fills. not a PnL headline. not live.",
        }
    return public


def load_ema_observer_rows(ema_dir: str | Path, *, limit: int = 50) -> list[dict[str, Any]]:
    """Newest-first decisions from data/ema/{date}/decisions.jsonl."""
    root = Path(ema_dir)
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for day in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name):
        path = day / "decisions.jsonl"
        if not path.is_file():
            continue
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
            if isinstance(obj, dict) and obj.get("source") == EMA_OBSERVER_SOURCE:
                rows.append(obj)
    rows.sort(key=lambda r: (int(r.get("ts_ms") or 0), int(r.get("seq") or 0)), reverse=True)
    return rows[: max(0, int(limit))]
