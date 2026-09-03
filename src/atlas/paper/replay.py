"""Historical Phase A replay: similar-regime window, signal-only. No orders.

Public OKX EEA candles only. Journals under data/replay/ tagged
source=historical-replay. Replay ≠ a live Phase A week. Similar-regime ≠
future performance. Never claims profitability.
"""

from __future__ import annotations

import json
import logging
import math
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

from atlas.collectors.base import new_run_id
from atlas.common.time import utc_date_str, utc_ms
from atlas.oms.doge_demo_loop import (
    LOCKED_SPOT_INST,
    PUBLIC_XPERP_MD_INST,
    parse_venue_arg,
    scan_signals,
    signal_to_dict,
    venues_from_config,
)
from atlas.oms.spot_demo import PAPER_EQUITY_EUR, redact_record
from atlas.paper.engine import strategy_from_app_config
from atlas.paper.md import (
    OKX_REST,
    USER_AGENT,
    PaperDataError,
    bar_ms,
    fetch_okx_candles,
    fetch_okx_history_candles,
    merge_bars,
    resample_1h,
)
from atlas.paper.types import Bar, Signal, Side
from atlas.strategy.breakout import BreakoutV1

log = logging.getLogger("atlas.paper.replay")

SOURCE = "historical-replay"
# Relative Euclidean across 4 fingerprint features. Above this we still use
# the best candidate but mark match_quality=poor (do not invent a prettier window).
POOR_MATCH_THRESHOLD = 0.45
DAY_MS = 24 * 60 * 60 * 1000
BARS_15M_PER_DAY = 96


class ReplayError(RuntimeError):
    """Replay cannot proceed without inventing data."""


@dataclass
class RegimeFingerprint:
    start_ms: int
    end_ms: int
    n_bars: int
    realized_vol: float
    range_pct: float
    net_trend: float
    n_signals: int
    n_long: int
    n_short: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WindowMatch:
    now: RegimeFingerprint
    candidate: RegimeFingerprint
    score: float
    match_quality: str  # ok | poor
    n_candidates: int
    step_bars: int
    excluded_overlap: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "now": self.now.as_dict(),
            "candidate": self.candidate.as_dict(),
            "score": self.score,
            "match_quality": self.match_quality,
            "poor_match_threshold": POOR_MATCH_THRESHOLD,
            "n_candidates": self.n_candidates,
            "step_bars": self.step_bars,
            "excluded_overlap": self.excluded_overlap,
            "note": (
                "lower score is closer. similar-regime ≠ future performance. "
                "replay is not a live Phase A week."
            ),
        }


@dataclass
class ReplayLeg:
    venue: str
    inst_id: str
    md_inst_id: str
    n_bars_15m: int
    n_bars_1h: int
    n_signals: int
    n_long: int
    n_short: int
    fetched_start_ms: int | None
    fetched_end_ms: int | None
    requested_start_ms: int | None
    requested_end_ms: int | None
    span_incomplete: bool
    fetch_error: str | None
    match: dict[str, Any] | None
    signals: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReplayJournal:
    """Append-only JSONL under data/replay/{UTC-date}/. Distinct from data/oms/."""

    def __init__(self, data_dir: str | Path, run_id: str, *, source: str | None = None) -> None:
        self.data_dir = Path(data_dir)
        self.run_id = run_id
        self.source = source or SOURCE
        self._lock = threading.Lock()
        self._seq = 0
        self.root = self.data_dir / "replay"

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
                "source": self.source,
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
        payload = redact_record({"source": self.source, **summary})
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
        return path


def _log_returns(closes: Sequence[float]) -> list[float]:
    out: list[float] = []
    for a, b in zip(closes, closes[1:]):
        if a <= 0 or b <= 0:
            continue
        out.append(math.log(b / a))
    return out


def _std(xs: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / n  # population
    return math.sqrt(var)


def slice_bars(bars: Sequence[Bar], start_ms: int, end_ms: int) -> list[Bar]:
    """Bars with ts_open_ms in [start_ms, end_ms). Closed only."""
    return [b for b in bars if start_ms <= b.ts_open_ms < end_ms and b.closed]


def fingerprint(
    bars_15m: Sequence[Bar],
    bars_1h: Sequence[Bar],
    strategy: BreakoutV1,
) -> RegimeFingerprint:
    if not bars_15m:
        raise ReplayError("fingerprint needs 15m bars")
    for b in bars_15m:
        if not b.closed:
            raise ReplayError("open bar in fingerprint window (fail closed)")
        b.validate()
    closes = [b.close for b in bars_15m]
    first = closes[0]
    if first <= 0:
        raise ReplayError("non-positive first close")
    rets = _log_returns(closes)
    hi = max(b.high for b in bars_15m)
    lo = min(b.low for b in bars_15m)
    sigs = scan_signals(strategy, list(bars_15m), list(bars_1h))
    n_long = sum(1 for s in sigs if s.side is Side.LONG)
    n_short = sum(1 for s in sigs if s.side is Side.SHORT)
    return RegimeFingerprint(
        start_ms=int(bars_15m[0].ts_open_ms),
        end_ms=int(bars_15m[-1].ts_close_ms),
        n_bars=len(bars_15m),
        realized_vol=float(_std(rets)),
        range_pct=float((hi - lo) / first),
        net_trend=float((closes[-1] - first) / first),
        n_signals=len(sigs),
        n_long=n_long,
        n_short=n_short,
    )


def _rel(a: float, b: float) -> float:
    return (a - b) / max(abs(a), abs(b), 1e-12)


def match_score(now: RegimeFingerprint, cand: RegimeFingerprint) -> float:
    """Lower is closer. Four features from the brief, equal weight."""
    parts = (
        _rel(now.realized_vol, cand.realized_vol),
        _rel(now.range_pct, cand.range_pct),
        _rel(now.net_trend, cand.net_trend),
        _rel(float(now.n_signals), float(cand.n_signals)),
    )
    return math.sqrt(sum(p * p for p in parts) / 4.0)


def iter_candidate_windows(
    bars: Sequence[Bar],
    *,
    window_bars: int,
    step_bars: int,
    exclude_start_ms: int,
    exclude_end_ms: int,
) -> list[list[Bar]]:
    """Sliding windows that do not overlap the 'now' interval."""
    if window_bars < 2 or step_bars < 1:
        raise ReplayError("window_bars/step_bars invalid")
    out: list[list[Bar]] = []
    n = len(bars)
    i = 0
    while i + window_bars <= n:
        chunk = list(bars[i : i + window_bars])
        w_start = chunk[0].ts_open_ms
        w_end = chunk[-1].ts_close_ms
        overlaps = not (w_end <= exclude_start_ms or w_start >= exclude_end_ms)
        if not overlaps:
            out.append(chunk)
        i += step_bars
    return out


def pick_similar_window(
    bars_15m: Sequence[Bar],
    bars_1h: Sequence[Bar],
    strategy: BreakoutV1,
    *,
    window_bars: int,
    step_bars: int | None = None,
) -> WindowMatch:
    """Fingerprint last `window_bars`, search earlier non-overlapping windows."""
    if len(bars_15m) < window_bars * 2:
        raise ReplayError(
            f"need at least {window_bars * 2} 15m bars for now+candidate, got {len(bars_15m)}"
        )
    step = step_bars if step_bars is not None else BARS_15M_PER_DAY
    now_bars = list(bars_15m[-window_bars:])
    now_fp = fingerprint(now_bars, bars_1h, strategy)
    candidates = iter_candidate_windows(
        bars_15m,
        window_bars=window_bars,
        step_bars=step,
        exclude_start_ms=now_fp.start_ms,
        exclude_end_ms=now_fp.end_ms,
    )
    if not candidates:
        raise ReplayError("no non-overlapping candidate windows (do not invent a window)")
    best: tuple[float, list[Bar], RegimeFingerprint] | None = None
    for chunk in candidates:
        fp = fingerprint(chunk, bars_1h, strategy)
        score = match_score(now_fp, fp)
        if best is None or score < best[0]:
            best = (score, chunk, fp)
    assert best is not None
    score, _chunk, cand_fp = best
    quality = "poor" if score > POOR_MATCH_THRESHOLD else "ok"
    return WindowMatch(
        now=now_fp,
        candidate=cand_fp,
        score=float(score),
        match_quality=quality,
        n_candidates=len(candidates),
        step_bars=step,
    )


def _count_sides(sigs: Sequence[Signal]) -> tuple[int, int]:
    n_long = sum(1 for s in sigs if s.side is Side.LONG)
    n_short = sum(1 for s in sigs if s.side is Side.SHORT)
    return n_long, n_short


def md_inst_for_venue(cfg: Any, venue_key: str) -> tuple[str, str]:
    """Return (order_inst_id, public_md_inst_id). Replay uses MD id only."""
    specs = venues_from_config(cfg, venue_key)
    spec = specs[0]
    md = spec.candles_inst_id
    if venue_key == "xperp":
        md = spec.md_inst_id or PUBLIC_XPERP_MD_INST
        if md.upper() == spec.inst_id.upper() and "310516" in spec.inst_id:
            md = PUBLIC_XPERP_MD_INST
    return spec.inst_id, md


def fetch_venue_history(
    client: Any,
    inst_id: str,
    *,
    rest_base: str,
    start_ms: int,
    end_ms: int,
    pause_s: float,
) -> tuple[list[Bar], list[Bar], str | None]:
    """15m + 1H closed history. 1H falls back to resample. No keys."""
    err: str | None = None
    b15: list[Bar] = []
    try:
        hist = fetch_okx_history_candles(
            client,
            inst_id,
            "15m",
            rest_base=rest_base,
            start_ms=start_ms,
            end_ms=end_ms,
            pause_s=pause_s,
        )
        b15.extend(hist)
    except (PaperDataError, Exception) as exc:  # noqa: BLE001 — record, don't fake
        err = f"history-candles:{type(exc).__name__}:{exc}"
    try:
        recent = fetch_okx_candles(client, inst_id, "15m", rest_base=rest_base, limit=300)
        recent = [b for b in recent if start_ms <= b.ts_open_ms < end_ms]
        b15 = merge_bars(b15, recent)
    except (PaperDataError, Exception) as exc:  # noqa: BLE001
        extra = f"candles:{type(exc).__name__}:{exc}"
        err = f"{err}; {extra}" if err else extra
    if not b15:
        return [], [], err or "empty_15m"
    try:
        h1 = fetch_okx_history_candles(
            client,
            inst_id,
            "1H",
            rest_base=rest_base,
            start_ms=start_ms,
            end_ms=end_ms,
            pause_s=pause_s,
        )
    except (PaperDataError, Exception) as exc:  # noqa: BLE001
        err = (err + "; " if err else "") + f"1h:{type(exc).__name__}:{exc}"
        h1 = resample_1h(b15)
    if not h1:
        h1 = resample_1h(b15)
    return b15, h1, err


def run_replay(
    cfg: Any,
    *,
    venue: str = "both",
    lookback_days: int = 90,
    window_days: int = 7,
    data_dir: str | Path = "data",
    rest_base: str | None = None,
    client: Any | None = None,
    bars_by_venue: dict[str, tuple[list[Bar], list[Bar]]] | None = None,
    pause_s: float = 0.12,
    run_id: str | None = None,
    now_ms: int | None = None,
) -> dict[str, Any]:
    """Signal-only historical replay. Never places orders.

    `bars_by_venue` injects closed bars for tests (no network). Keys: spot|xperp.
    """
    if lookback_days < window_days * 2:
        raise ReplayError("lookback_days must be >= 2 * window_days so a candidate exists")
    keys = parse_venue_arg(venue)
    rid = run_id or new_run_id("replay")
    journal = ReplayJournal(data_dir, rid)
    ts = int(now_ms if now_ms is not None else utc_ms())
    demo = getattr(getattr(cfg, "okx", None), "doge_demo", None)
    paper_eq = float(getattr(demo, "paper_equity_eur", PAPER_EQUITY_EUR) or PAPER_EQUITY_EUR)
    strategy = strategy_from_app_config(cfg)
    window_bars = int(window_days) * BARS_15M_PER_DAY
    lookback_ms = int(lookback_days) * DAY_MS
    window_ms = int(window_days) * DAY_MS
    start_ms = ts - lookback_ms
    rest = (rest_base or getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip(
        "/"
    )

    journal.append(
        "events",
        {
            "kind": "historical_replay_start",
            "place_orders": False,
            "venue": venue,
            "venues": list(keys),
            "lookback_days": lookback_days,
            "window_days": window_days,
            "paper_equity_eur": paper_eq,
            "daily_kill_frac": float(getattr(demo, "daily_kill_frac", 0.05) or 0.05),
            "per_trade_risk_frac": float(getattr(demo, "per_trade_risk_frac", 0.015) or 0.015),
            "ranging": False,
            "pepe_enabled": False,
            "source": SOURCE,
        },
        ts_ms=ts,
    )

    own_client = False
    http = client
    if bars_by_venue is None and http is None:
        import httpx

        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
        own_client = True

    legs: list[ReplayLeg] = []
    errors: list[str] = []
    try:
        for key in keys:
            order_inst, md_inst = md_inst_for_venue(cfg, key)
            fetch_err: str | None = None
            if bars_by_venue is not None:
                pair = bars_by_venue.get(key)
                if not pair:
                    fetch_err = f"missing injected bars for {key}"
                    b15, b1h = [], []
                else:
                    b15, b1h = pair
            else:
                assert http is not None
                b15, b1h, fetch_err = fetch_venue_history(
                    http,
                    md_inst,
                    rest_base=rest,
                    start_ms=start_ms,
                    end_ms=ts,
                    pause_s=pause_s,
                )
            if fetch_err:
                errors.append(f"{key}:{fetch_err}")
            fetched_start = b15[0].ts_open_ms if b15 else None
            fetched_end = b15[-1].ts_close_ms if b15 else None
            span_incomplete = False
            if fetched_start is not None and fetched_start > start_ms + bar_ms("15m"):
                span_incomplete = True
                errors.append(
                    f"{key}:span_short requested_start_ms={start_ms} got={fetched_start}"
                )

            match_d: dict[str, Any] | None = None
            replay_15: list[Bar] = []
            replay_1h: list[Bar] = list(b1h)
            need = window_bars * 2
            window_bars_eff = window_bars
            if 0 < len(b15) < need:
                # Venue returned a shorter span — do not invent bars. Shrink the
                # window so a candidate still exists, and record it.
                min_w = max(strategy.warmup_bars() + 8, 32)
                window_bars_eff = max(min_w, len(b15) // 2)
                if len(b15) >= window_bars_eff * 2:
                    errors.append(
                        f"{key}:window_shrunk requested_bars={window_bars} "
                        f"used_bars={window_bars_eff} n={len(b15)}"
                    )
                else:
                    window_bars_eff = window_bars
            if len(b15) >= window_bars_eff * 2:
                try:
                    match = pick_similar_window(
                        b15, b1h, strategy, window_bars=window_bars_eff
                    )
                    match_d = match.as_dict()
                    match_d["window_bars_requested"] = window_bars
                    match_d["window_bars_used"] = window_bars_eff
                    replay_15 = [
                        b
                        for b in b15
                        if match.candidate.start_ms <= b.ts_open_ms
                        and b.ts_close_ms <= match.candidate.end_ms
                    ]
                    if match.match_quality == "poor":
                        errors.append(
                            f"{key}:poor_match score={match.score:.4f} "
                            f"(threshold {POOR_MATCH_THRESHOLD}); used best candidate anyway"
                        )
                except ReplayError as exc:
                    fetch_err = f"{fetch_err + '; ' if fetch_err else ''}match:{exc}"
                    errors.append(f"{key}:match:{exc}")
            elif b15:
                fetch_err = (
                    f"{fetch_err + '; ' if fetch_err else ''}"
                    f"not_enough_bars n={len(b15)} need>={window_bars * 2}"
                )
                errors.append(f"{key}:{fetch_err}")

            sigs: list[Signal] = []
            if replay_15:
                sigs = scan_signals(strategy, replay_15, replay_1h)
                for sig in sigs:
                    journal.append(
                        "decisions",
                        {
                            "kind": "breakout_signal",
                            **signal_to_dict(sig, venue=key),
                            "place_orders": False,
                            "mdInstId": md_inst,
                            "instId": order_inst,
                        },
                        ts_ms=sig.bar_ts_ms,
                    )

            n_long, n_short = _count_sides(sigs)
            legs.append(
                ReplayLeg(
                    venue=key,
                    inst_id=order_inst,
                    md_inst_id=md_inst,
                    n_bars_15m=len(replay_15) if replay_15 else len(b15),
                    n_bars_1h=len(replay_1h),
                    n_signals=len(sigs),
                    n_long=n_long,
                    n_short=n_short,
                    fetched_start_ms=fetched_start,
                    fetched_end_ms=fetched_end,
                    requested_start_ms=start_ms,
                    requested_end_ms=ts,
                    span_incomplete=span_incomplete,
                    fetch_error=fetch_err,
                    match=match_d,
                    signals=[signal_to_dict(s, venue=key) for s in sigs],
                )
            )
    finally:
        if own_client and http is not None:
            http.close()

    summary: dict[str, Any] = {
        "ok": any(leg.match is not None for leg in legs),
        "dry_run": True,
        "place_orders": False,
        "mode": "historical-replay",
        "source": SOURCE,
        "run_id": rid,
        "venue": venue,
        "lookback_days": lookback_days,
        "window_days": window_days,
        "paper_equity_eur": paper_eq,
        "n_signals": sum(leg.n_signals for leg in legs),
        "n_long": sum(leg.n_long for leg in legs),
        "n_short": sum(leg.n_short for leg in legs),
        "errors": errors,
        "legs": [leg.as_dict() for leg in legs],
        "disclaimer": (
            "paper/research only. replay is not a live Phase A week. "
            "similar-regime ≠ future performance. no profitability claimed."
        ),
    }
    # Strip signal lists from printed/journal summary bulk — keep counts. Full
    # signals stay in decisions.jsonl. Still include compact signal rows? User
    # asked n_signals long/short per venue in the JSON summary, not every row.
    for leg in summary["legs"]:
        leg.pop("signals", None)
    journal.append("events", {"kind": "historical_replay_end", **summary}, ts_ms=ts)
    journal.write_summary(summary, ts_ms=ts)
    summary["log_dir"] = str(journal.root / utc_date_str(ts))
    return summary
