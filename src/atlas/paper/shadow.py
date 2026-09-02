"""Phase B shadow: same breakout signals, paper risk decides would-place vs blocked.

No auto-place. No demo/live orders. Reuses PaperEngine sequencing and
atlas.paper.risk sizing. Journals under data/shadow/ tagged source=shadow-replay.
Shadow ≠ gated micro-demo (Phase C). Replay/shadow ≠ a live Phase A week.
"""

from __future__ import annotations

import json
import logging
import threading
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from atlas.collectors.base import new_run_id
from atlas.common.time import utc_date_str, utc_ms
from atlas.oms.doge_demo_loop import parse_venue_arg, signal_to_dict
from atlas.oms.spot_demo import PAPER_EQUITY_EUR, redact_record
from atlas.paper.engine import PaperEngine, PaperSettings, strategy_from_app_config
from atlas.paper.md import OKX_REST, USER_AGENT, bars_1h_at_or_before
from atlas.paper.ledger import Ledger
from atlas.paper.replay import (
    ReplayError,
    fetch_venue_history,
    md_inst_for_venue,
    run_replay,
)
from atlas.paper.risk import gate_new_entry, size_order
from atlas.paper.types import Bar, Order, q

log = logging.getLogger("atlas.paper.shadow")

SOURCE = "shadow-replay"
HYPOTHETICAL = "hypothetical paper fill (fee+slip); not a venue fill; not_a_forecast"


def _map_block_reason(raw: str) -> str:
    if raw in ("daily_kill", "daily_loss", "non_positive_day_start"):
        return "kill"
    if raw == "one_position":
        return "one_position"
    if raw in ("sized", "ok"):
        return "ok"
    if raw in (
        "invalid_equity_or_entry",
        "invalid_stop",
        "stop_not_below_entry",
        "stop_not_above_entry",
        "zero_stop_distance",
        "zero_notional",
        "zero_qty",
        "liquidity_cap",
        "leverage_hard_cap",
        "non_positive_equity",
    ):
        return "size"
    return raw or "blocked"


class ShadowJournal:
    """Append-only JSONL under data/shadow/{UTC-date}/. Duck-types PaperJournal."""

    def __init__(self, data_dir: str | Path, run_id: str) -> None:
        self.data_dir = Path(data_dir)
        self.run_id = run_id
        self._lock = threading.Lock()
        self._seq = 0
        self.root = self.data_dir / "shadow"

    def _path(self, channel: str, ts_ms: int) -> Path:
        directory = self.root / utc_date_str(ts_ms)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{channel}.jsonl"

    def append(self, channel: str, record: dict[str, Any], *, ts_ms: int | None = None) -> Path:
        ts = int(ts_ms if ts_ms is not None else record.get("ts_ms") or utc_ms())
        with self._lock:
            self._seq += 1
            seq = self._seq
        row = redact_record(
            {
                "run_id": self.run_id,
                "seq": seq,
                "source": SOURCE,
                "place_orders": False,
                **record,
                "ts_ms": ts,
            }
        )
        path = self._path(channel, ts)
        line = json.dumps(row, separators=(",", ":"), ensure_ascii=False, default=str)
        with self._lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return path

    def write_summary(self, summary: dict[str, Any], *, ts_ms: int) -> Path:
        directory = self.root / utc_date_str(ts_ms)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"summary_{self.run_id}.json"
        payload = redact_record({"source": SOURCE, "place_orders": False, **summary})
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
        return path

    def dir_for(self, ts_ms: int) -> Path:
        return self.root / utc_date_str(ts_ms)


class ShadowEngine(PaperEngine):
    """PaperEngine + per-signal would-place / blocked journal. Never talks to OKX."""

    def __init__(self, *args: Any, venue_by_symbol: Mapping[str, str] | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.venue_by_symbol = dict(venue_by_symbol or {})
        self.n_signals = 0
        self.n_would_place = 0
        self.n_no_signal = 0
        self.blocked: Counter[str] = Counter()

    def _venue(self, symbol: str) -> str:
        return self.venue_by_symbol.get(symbol, "")

    def _on_skip_enter(self, ledger, hist, bars_1h_by_symbol, symbols, bar_i) -> None:
        self._consider_signals(ledger, hist, bars_1h_by_symbol, symbols, allow_queue=False)

    def _maybe_enter(self, ledger, hist, bars_1h_by_symbol, symbols, bar_i) -> None:
        self._consider_signals(ledger, hist, bars_1h_by_symbol, symbols, allow_queue=True)

    def _consider_signals(
        self,
        ledger: Ledger,
        hist: Mapping[str, list[Bar]],
        bars_1h_by_symbol: Mapping[str, Sequence[Bar]],
        symbols: Sequence[str],
        *,
        allow_queue: bool,
    ) -> None:
        queued = False
        for symbol in symbols:
            h = hist.get(symbol) or []
            if len(h) < self.strategy.warmup_bars():
                continue
            last = h[-1]
            native_1h = list(bars_1h_by_symbol.get(symbol) or [])
            h1 = bars_1h_at_or_before(native_1h, last.ts_close_ms) if native_1h else []
            sig = self.strategy.on_closed_bar(h, h1 or None)
            if sig is None:
                self.n_no_signal += 1
                self.blocked["no_signal"] += 1
                continue
            self.n_signals += 1
            self.journal.append(
                "decisions",
                {
                    "kind": "breakout_signal",
                    **signal_to_dict(sig, venue=self._venue(symbol) or None),
                    "hypothetical": True,
                },
                ts_ms=last.ts_close_ms,
            )
            gate = gate_new_entry(ledger, one_position=self.settings.one_position)
            block: str | None = None
            gate_tag = gate.reason
            if not gate.allowed:
                block = _map_block_reason(gate.reason)
            elif ledger.killed:
                block = "kill"
                gate_tag = ledger.kill_reason or "daily_kill"
            elif not allow_queue or queued or self._pending is not None:
                block = "one_position"
                gate_tag = "one_position"
            if block:
                self.blocked[block] += 1
                self._log_shadow_decision(
                    last,
                    symbol,
                    sig,
                    allowed=False,
                    blocked_reason=block,
                    gate=gate_tag,
                    sized=None,
                    equity=ledger.equity,
                )
                continue
            sized = size_order(
                equity=ledger.equity,
                entry=last.close,
                stop=sig.stop,
                side=sig.side,
                per_trade_risk_frac=self.settings.per_trade_risk_frac,
                leverage_default=self.settings.leverage_default,
                leverage_hard_cap=self.settings.leverage_hard_cap,
                liquidity_cap=self.settings.liquidity_cap_eur,
            )
            if not sized.allowed:
                self._rejects += 1
                self.blocked["size"] += 1
                self._log_shadow_decision(
                    last,
                    symbol,
                    sig,
                    allowed=False,
                    blocked_reason="size",
                    gate="ok",
                    sized=sized,
                    equity=ledger.equity,
                )
                continue
            self.n_would_place += 1
            self._log_shadow_decision(
                last,
                symbol,
                sig,
                allowed=True,
                blocked_reason=None,
                gate="ok",
                sized=sized,
                equity=ledger.equity,
            )
            if allow_queue and not queued and self._pending is None:
                self._pending = Order(
                    symbol=symbol,
                    side=sig.side,
                    qty=sized.qty,
                    kind="entry",
                    reason=sig.reason,
                    stop=sig.stop,
                    decision_ts_ms=last.ts_close_ms,
                    cloid=self._cloid(),
                )
                queued = True

    def _log_shadow_decision(
        self,
        last: Bar,
        symbol: str,
        sig: Any,
        *,
        allowed: bool,
        blocked_reason: str | None,
        gate: str,
        sized: Any,
        equity: float,
    ) -> None:
        rec: dict[str, Any] = {
            "kind": "would_place" if allowed else "blocked",
            "blocked_reason": blocked_reason,
            "action": f"enter_{sig.side.value}",
            "symbol": symbol,
            "venue": self._venue(symbol),
            "reason": sig.reason,
            "stop": sig.stop,
            "ref_close": last.close,
            "allowed": allowed,
            "gate": gate,
            "equity": equity,
            "paper_equity_scale_eur": self.settings.equity_eur,
            "hypothetical": True,
            "place_orders": False,
            "extras": sig.extras,
        }
        if sized is not None:
            rec.update(
                {
                    "size_reason": sized.reason,
                    "qty": sized.qty,
                    "notional": sized.notional,
                    "leverage": sized.leverage,
                    "risk_budget": sized.risk_budget,
                }
            )
        self._log("decisions", rec, last.ts_close_ms)
        if not allowed:
            self._log("events", {"type": "reject", **rec}, last.ts_close_ms)


def shadow_settings(cfg: Any) -> PaperSettings:
    """€200 book, 5% kill, 1–2%/trade, one position, X-Perp isolated ≤2x."""
    base = PaperSettings.from_app_config(cfg)
    demo = getattr(getattr(cfg, "okx", None), "doge_demo", None)
    if demo is not None:
        base.equity_eur = float(getattr(demo, "paper_equity_eur", base.equity_eur) or base.equity_eur)
        base.daily_kill_frac = float(getattr(demo, "daily_kill_frac", base.daily_kill_frac) or base.daily_kill_frac)
        base.per_trade_risk_frac = float(
            getattr(demo, "per_trade_risk_frac", base.per_trade_risk_frac) or base.per_trade_risk_frac
        )
        cap = float(getattr(demo, "leverage_hard_cap", 2.0) or 2.0)
        base.leverage_hard_cap = min(cap, 2.0)
        lev = float(getattr(demo, "leverage", base.leverage_default) or base.leverage_default)
        base.leverage_default = min(lev, base.leverage_hard_cap)
    else:
        base.leverage_hard_cap = min(base.leverage_hard_cap, 2.0)
        base.leverage_default = min(base.leverage_default, base.leverage_hard_cap)
    base.one_position = True
    return base


def latest_replay_summary(data_dir: str | Path) -> dict[str, Any] | None:
    root = Path(data_dir) / "replay"
    if not root.is_dir():
        return None
    found: list[tuple[float, dict[str, Any]]] = []
    for path in root.glob("*/summary_*.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict) or not raw.get("ok"):
            continue
        if raw.get("source") != "historical-replay":
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        found.append((mtime, raw))
    if not found:
        return None
    found.sort(key=lambda x: x[0])
    return found[-1][1]


def windows_from_replay_summary(summary: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for leg in summary.get("legs") or []:
        if not isinstance(leg, dict):
            continue
        match = leg.get("match") or {}
        cand = match.get("candidate") or {}
        venue = str(leg.get("venue") or "")
        start = cand.get("start_ms")
        end = cand.get("end_ms")
        if not venue or start is None or end is None:
            continue
        out[venue] = {
            "start_ms": int(start),
            "end_ms": int(end),
            "md_inst_id": str(leg.get("md_inst_id") or ""),
            "inst_id": str(leg.get("inst_id") or ""),
            "score": match.get("score"),
            "match_quality": match.get("match_quality"),
            "now": match.get("now"),
            "candidate": cand,
        }
    return out


def _expectancy_after_costs(*, realized_pnl: float, n_trades: int) -> float | None:
    if n_trades <= 0:
        return None
    return q(realized_pnl / n_trades)


def run_shadow(
    cfg: Any,
    *,
    venue: str = "both",
    data_dir: str | Path = "data",
    rest_base: str | None = None,
    client: Any | None = None,
    bars_by_venue: dict[str, tuple[list[Bar], list[Bar]]] | None = None,
    pause_s: float = 0.12,
    run_id: str | None = None,
    now_ms: int | None = None,
    lookback_days: int = 90,
    window_days: int = 7,
) -> dict[str, Any]:
    """Signal → paper risk → would-place or blocked. Never places orders."""
    keys = parse_venue_arg(venue)
    rid = run_id or new_run_id("shadow")
    journal = ShadowJournal(data_dir, rid)
    ts = int(now_ms if now_ms is not None else utc_ms())
    settings = shadow_settings(cfg)
    strategy = strategy_from_app_config(cfg)
    rest = (rest_base or getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip(
        "/"
    )

    replay_sum = None if bars_by_venue is not None else latest_replay_summary(data_dir)
    windows = windows_from_replay_summary(replay_sum) if replay_sum else {}
    used_replay = bool(windows)
    errors: list[str] = []

    if bars_by_venue is None and not windows:
        log.info("no replay summary; running historical match first")
        try:
            replay_sum = run_replay(
                cfg,
                venue=venue,
                lookback_days=lookback_days,
                window_days=window_days,
                data_dir=data_dir,
                rest_base=rest,
                client=client,
                pause_s=pause_s,
                now_ms=now_ms,
            )
        except ReplayError as exc:
            raise ReplayError(f"shadow needs a replay window: {exc}") from exc
        windows = windows_from_replay_summary(replay_sum or {})
        if not windows:
            raise ReplayError("replay produced no candidate windows (do not invent bars)")
        used_replay = True

    journal.append(
        "events",
        {
            "kind": "shadow_replay_start",
            "place_orders": False,
            "venue": venue,
            "venues": list(keys),
            "paper_equity_eur": settings.equity_eur,
            "daily_kill_frac": settings.daily_kill_frac,
            "per_trade_risk_frac": settings.per_trade_risk_frac,
            "leverage_hard_cap": settings.leverage_hard_cap,
            "one_position": True,
            "used_replay_summary": used_replay,
            "windows": {k: windows.get(k) for k in keys if k in windows},
            "hypothetical": True,
        },
        ts_ms=ts,
    )

    own_client = False
    http = client
    if bars_by_venue is None and http is None:
        import httpx

        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
        own_client = True

    bars_by_symbol: dict[str, list[Bar]] = {}
    bars_1h_by_symbol: dict[str, list[Bar]] = {}
    venue_by_symbol: dict[str, str] = {}
    window_meta: dict[str, Any] = {}

    try:
        for key in keys:
            order_inst, md_inst = md_inst_for_venue(cfg, key)
            win = windows.get(key) if windows else None
            if bars_by_venue is not None:
                pair = bars_by_venue.get(key)
                if not pair:
                    errors.append(f"{key}:missing_injected_bars")
                    continue
                b15, b1h = pair
            else:
                if win is None:
                    errors.append(f"{key}:no_replay_window")
                    continue
                md = str(win.get("md_inst_id") or md_inst)
                assert http is not None
                start_ms = int(win["start_ms"])
                end_ms = int(win["end_ms"])
                # 1h pad before the window for the stub filter; 15m stays the candidate.
                pad = 48 * 60 * 60 * 1000
                b15_all, b1h, fetch_err = fetch_venue_history(
                    http,
                    md,
                    rest_base=rest,
                    start_ms=start_ms - pad,
                    end_ms=end_ms + 1,
                    pause_s=pause_s,
                )
                if fetch_err:
                    errors.append(f"{key}:{fetch_err}")
                b15 = [
                    b
                    for b in b15_all
                    if start_ms <= b.ts_open_ms and b.ts_close_ms <= end_ms
                ]
                if not b15:
                    errors.append(f"{key}:empty_candidate_window")
                    continue
            sym = b15[0].symbol if b15 else md_inst
            bars_by_symbol[sym] = b15
            bars_1h_by_symbol[sym] = list(b1h)
            venue_by_symbol[sym] = key
            window_meta[key] = {
                "md_inst_id": md_inst,
                "inst_id": order_inst,
                "n_bars_15m": len(b15),
                "n_bars_1h": len(b1h),
                "start_ms": b15[0].ts_open_ms if b15 else None,
                "end_ms": b15[-1].ts_close_ms if b15 else None,
                "match": win,
            }
    finally:
        if own_client and http is not None:
            http.close()

    if not bars_by_symbol:
        raise ReplayError("shadow has no bars (do not invent). Run replay first.")

    engine = ShadowEngine(
        settings,
        strategy,
        journal=journal,
        run_id=rid,
        data_dir=str(data_dir),
        venue_by_symbol=venue_by_symbol,
    )
    paper = engine.run(bars_by_symbol, bars_1h_by_symbol, universe=list(bars_by_symbol.keys()))

    n_trades = paper.n_trades
    research = {
        "not_a_forecast": True,
        "hypothetical": True,
        "label": HYPOTHETICAL,
        "start_equity_eur": paper.start_equity,
        "end_equity_eur": paper.end_equity,
        "realized_pnl_eur": paper.realized_pnl,
        "fees_paid_eur": paper.fees_paid,
        "n_trades": n_trades,
        "expectancy_after_costs_eur": _expectancy_after_costs(
            realized_pnl=paper.realized_pnl, n_trades=n_trades
        ),
        "killed": paper.killed,
    }

    blocked = dict(engine.blocked)
    summary: dict[str, Any] = {
        "ok": True,
        "dry_run": True,
        "place_orders": False,
        "mode": "shadow-replay",
        "source": SOURCE,
        "run_id": rid,
        "venue": venue,
        "paper_equity_eur": settings.equity_eur,
        "daily_kill_frac": settings.daily_kill_frac,
        "per_trade_risk_frac": settings.per_trade_risk_frac,
        "leverage_hard_cap": settings.leverage_hard_cap,
        "one_position": True,
        "n_signals": engine.n_signals,
        "n_would_place": engine.n_would_place,
        "n_blocked": int(sum(blocked.values())),
        "n_blocked_by_reason": blocked,
        "n_open": paper.n_entries,
        "n_flatten": paper.n_trades,
        "n_kills": paper.n_kills,
        "windows": window_meta,
        "errors": errors,
        "research": research,
        "disclaimer": (
            "paper/research only. shadow is not Phase C auto-demo. "
            "replay/shadow ≠ live Phase A week. similar-regime ≠ future performance. "
            "research.end_equity is hypothetical, not profit."
        ),
    }
    journal.append("events", {"kind": "shadow_replay_end", **summary}, ts_ms=ts)
    journal.write_summary(summary, ts_ms=ts)
    summary["log_dir"] = str(journal.root / utc_date_str(ts))
    return summary
