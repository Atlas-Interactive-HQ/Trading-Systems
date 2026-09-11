"""1s VAMP-5 feature pipeline for Scalp-HFT Layer B (paper-only).

Metrics only — no trading, no PnL, no live OMS.
Design: phase1/75 §5, research/scalp_hft_v1_sketch.py, phase1/78 §6, phase1/79.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Sequence

PAPER_ONLY = True

VAMP_LEVELS = 5
VAMP_Z_WINDOW = 60
EMA_FAST = 12
EMA_SLOW = 21
# phase1/75 KILL_LATENCY: exchange data >1s behind decision → no entry.
HEALTH_STALE_MS = 1000

# Schema: feature metrics only (no PnL / fills / expectancy).
# book_stale is a LEGACY alias of carried_forward (not health_stale).
SAMPLE_COLUMNS: tuple[str, ...] = (
    "ts_s",
    "inst_id",
    "mid",
    "vamp5",
    "vamp_edge_bps",
    "vamp_z",
    "ema12",
    "ema21",
    "best_bid",
    "best_ask",
    "book_stale",
    "n_bid_levels",
    "n_ask_levels",
    "vamp_valid",
    "carried_forward",
    "book_age_ms",
    "health_stale",
    "last_book_ts_ms",
    "ts_rewind",
)


@dataclass
class BookTop5:
    bids: list[tuple[float, float]] = field(default_factory=list)  # (px, qty)
    asks: list[tuple[float, float]] = field(default_factory=list)


@dataclass(frozen=True)
class Vamp1sSample:
    ts_s: int
    inst_id: str
    mid: Optional[float]
    vamp5: Optional[float]
    vamp_edge_bps: Optional[float]
    vamp_z: Optional[float]  # None when warmup or INVALID (std<=0)
    ema12: Optional[float]
    ema21: Optional[float]
    best_bid: Optional[float]
    best_ask: Optional[float]
    book_stale: bool  # LEGACY alias of carried_forward — NOT health_stale
    n_bid_levels: int
    n_ask_levels: int
    vamp_valid: bool
    carried_forward: bool = False
    book_age_ms: Optional[int] = None
    health_stale: bool = False
    last_book_ts_ms: Optional[int] = None
    ts_rewind: bool = False

    def to_row(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in SAMPLE_COLUMNS}


@dataclass
class Books5IngestStats:
    """Honest ingest counters for Layer B books5 JSONL (no invented PnL)."""

    n_lines: int = 0
    n_json_errors: int = 0
    n_subscribe_or_control: int = 0
    n_data_frames: int = 0
    n_parse_skips: int = 0
    n_book_events: int = 0
    seq_id_samples: int = 0
    seq_id_non_monotonic: int = 0
    seq_id_skips: int = 0  # thinned books5: skips expected, not hard gaps
    local_seq_non_monotonic: int = 0
    ts_ms_min: Optional[int] = None
    ts_ms_max: Optional[int] = None
    inst_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_lines": self.n_lines,
            "n_json_errors": self.n_json_errors,
            "n_subscribe_or_control": self.n_subscribe_or_control,
            "n_data_frames": self.n_data_frames,
            "n_parse_skips": self.n_parse_skips,
            "n_book_events": self.n_book_events,
            "seq_id_samples": self.seq_id_samples,
            "seq_id_non_monotonic": self.seq_id_non_monotonic,
            "seq_id_skips": self.seq_id_skips,
            "seq_id_note": (
                "books5 seqId may skip (thinned snapshots); not treated as hard gaps"
            ),
            "local_seq_non_monotonic": self.local_seq_non_monotonic,
            "ts_ms_min": self.ts_ms_min,
            "ts_ms_max": self.ts_ms_max,
            "inst_ids": list(self.inst_ids),
        }


@dataclass
class ReplayGapStats:
    """1s clock coverage after resample."""

    n_samples_1s: int = 0
    n_seconds_with_update: int = 0
    n_seconds_stale_carry: int = 0
    n_carried_forward: int = 0
    n_health_stale: int = 0
    n_ts_rewind: int = 0
    n_vamp_valid: int = 0
    n_vamp_z_valid: int = 0
    n_ema12_ready: int = 0
    n_ema21_ready: int = 0
    book_age_ms_min: Optional[int] = None
    book_age_ms_max: Optional[int] = None
    ts_s_first: Optional[int] = None
    ts_s_last: Optional[int] = None
    span_seconds: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_samples_1s": self.n_samples_1s,
            "n_seconds_with_update": self.n_seconds_with_update,
            "n_seconds_stale_carry": self.n_seconds_stale_carry,
            "n_carried_forward": self.n_carried_forward,
            "n_health_stale": self.n_health_stale,
            "n_ts_rewind": self.n_ts_rewind,
            "n_vamp_valid": self.n_vamp_valid,
            "n_vamp_z_valid": self.n_vamp_z_valid,
            "n_ema12_ready": self.n_ema12_ready,
            "n_ema21_ready": self.n_ema21_ready,
            "book_age_ms_min": self.book_age_ms_min,
            "book_age_ms_max": self.book_age_ms_max,
            "health_stale_threshold_ms": HEALTH_STALE_MS,
            "ts_s_first": self.ts_s_first,
            "ts_s_last": self.ts_s_last,
            "span_seconds": self.span_seconds,
            "stale_policy": (
                "empty seconds between first/last carry forward last book "
                "(carried_forward=True; book_stale is a legacy alias of that). "
                "book_age_ms = decision_ts_ms(ts_s*1000) − last valid books5 exchange ts. "
                f"health_stale = book_age_ms > {HEALTH_STALE_MS}. "
                "Trading health uses health_stale + reconnect + timestamp continuity "
                "— NOT carried_forward alone. Never invent depth. "
                "books5 seqId skips are NOT missing packets."
            ),
        }


def calculate_vamp(top5: BookTop5, levels: int = VAMP_LEVELS) -> float:
    """VAMP5 = (Σ Pbid_i*Qask_i + Σ Pask_i*Qbid_i) / (ΣQbid+ΣQask)."""
    bids = top5.bids[:levels]
    asks = top5.asks[:levels]
    if len(bids) < levels or len(asks) < levels:
        raise ValueError("insufficient depth for VAMP")
    num = 0.0
    den = 0.0
    for (pb, qb), (pa, qa) in zip(bids, asks):
        num += pb * qa + pa * qb
        den += qb + qa
    if den <= 0:
        raise ValueError("invalid VAMP denominator")
    return num / den


def vamp_edge_bps(vamp5: float, mid: float) -> float:
    if mid <= 0 or not math.isfinite(mid):
        raise ValueError("invalid mid for vamp_edge_bps")
    return 10_000.0 * (vamp5 - mid) / mid


def mid_from_book(top5: BookTop5) -> float:
    if not top5.bids or not top5.asks:
        raise ValueError("empty book for mid")
    return (top5.bids[0][0] + top5.asks[0][0]) / 2.0


class RollingZScore:
    """Causal rolling z-score; None while warming or when std invalid → INVALID."""

    def __init__(self, window: int = VAMP_Z_WINDOW) -> None:
        if window < 2:
            raise ValueError("window must be >= 2")
        self.window = window
        self._buf: list[float] = []

    def update(self, x: float) -> Optional[float]:
        self._buf.append(x)
        if len(self._buf) > self.window:
            self._buf = self._buf[-self.window :]
        if len(self._buf) < self.window:
            return None
        mean = sum(self._buf) / len(self._buf)
        var = sum((v - mean) ** 2 for v in self._buf) / len(self._buf)
        if var <= 0 or not math.isfinite(var):
            return None  # INVALID → NO TRADE
        std = var**0.5
        return (x - mean) / std


class EMA:
    """Causal EMA; None until `period` updates have been seen."""

    def __init__(self, period: int) -> None:
        if period < 1:
            raise ValueError("period must be >= 1")
        self.period = period
        self.value: Optional[float] = None
        self._n = 0
        self._alpha = 2.0 / (period + 1)

    def update(self, x: float) -> Optional[float]:
        self._n += 1
        if self.value is None:
            self.value = x
        else:
            self.value = self._alpha * x + (1.0 - self._alpha) * self.value
        if self._n < self.period:
            return None
        return self.value


def _level_px_qty(level: Sequence[Any]) -> tuple[float, float]:
    """OKX books5 level: [px, sz, deprecated, nOrders]."""
    px = float(level[0])
    qty = float(level[1])
    if not math.isfinite(px) or not math.isfinite(qty) or px <= 0 or qty < 0:
        raise ValueError(f"invalid book level: {level!r}")
    return px, qty


def parse_books5_levels(
    bids_raw: Sequence[Sequence[Any]],
    asks_raw: Sequence[Sequence[Any]],
    *,
    levels: int = VAMP_LEVELS,
) -> BookTop5:
    bids = [_level_px_qty(lv) for lv in bids_raw[:levels]]
    asks = [_level_px_qty(lv) for lv in asks_raw[:levels]]
    return BookTop5(bids=bids, asks=asks)


def extract_books5_from_envelope(
    envelope: dict[str, Any],
) -> list[tuple[int, str, BookTop5, Optional[int]]]:
    """Parse raw.envelope.v1 ws_books5 line → list of (ts_ms, inst_id, book, seqId).

    Skips subscribe/error frames without `data`.
    """
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return []
    out: list[tuple[int, str, BookTop5, Optional[int]]] = []
    for snap in data:
        if not isinstance(snap, dict):
            continue
        bids_raw = snap.get("bids") or []
        asks_raw = snap.get("asks") or []
        if not bids_raw or not asks_raw:
            continue
        try:
            book = parse_books5_levels(bids_raw, asks_raw)
        except (TypeError, ValueError, IndexError):
            continue
        inst = str(
            snap.get("instId")
            or envelope.get("venue_instrument_id")
            or (payload.get("arg") or {}).get("instId")
            or ""
        )
        ts_ms: Optional[int] = None
        raw_ts = snap.get("ts")
        if raw_ts is not None:
            try:
                ts_ms = int(raw_ts)
            except (TypeError, ValueError):
                ts_ms = None
        if ts_ms is None:
            et = envelope.get("exchange_ts")
            if et is not None:
                try:
                    ts_ms = int(et)
                except (TypeError, ValueError):
                    ts_ms = None
        if ts_ms is None:
            rt = envelope.get("receive_ts")
            if rt is not None:
                try:
                    ts_ms = int(rt)
                except (TypeError, ValueError):
                    ts_ms = None
        if ts_ms is None:
            continue
        seq_id: Optional[int] = None
        raw_seq = snap.get("seqId")
        if raw_seq is not None:
            try:
                seq_id = int(raw_seq)
            except (TypeError, ValueError):
                seq_id = None
        out.append((ts_ms, inst, book, seq_id))
    return out


def iter_books5_events(
    paths: Iterable[Path],
    *,
    stats: Optional[Books5IngestStats] = None,
) -> Iterator[tuple[int, str, BookTop5]]:
    """Yield (ts_ms, inst_id, book); optionally accumulate ingest stats."""
    if stats is None:
        stats = Books5IngestStats()
    prev_seq: Optional[int] = None
    prev_local: Optional[int] = None
    seen_inst: set[str] = set()

    for path in paths:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                stats.n_lines += 1
                try:
                    env = json.loads(line)
                except json.JSONDecodeError:
                    stats.n_json_errors += 1
                    continue
                if not isinstance(env, dict):
                    stats.n_json_errors += 1
                    continue

                local = env.get("local_seq")
                if local is not None:
                    try:
                        loc_i = int(local)
                        if prev_local is not None and loc_i < prev_local:
                            stats.local_seq_non_monotonic += 1
                        prev_local = loc_i
                    except (TypeError, ValueError):
                        pass

                payload = env.get("payload")
                if not isinstance(payload, dict):
                    stats.n_parse_skips += 1
                    continue
                if "data" not in payload:
                    stats.n_subscribe_or_control += 1
                    continue
                if not isinstance(payload.get("data"), list) or not payload["data"]:
                    stats.n_subscribe_or_control += 1
                    continue

                stats.n_data_frames += 1
                extracted = extract_books5_from_envelope(env)
                if not extracted:
                    stats.n_parse_skips += 1
                    continue
                for ts_ms, inst, book, seq_id in extracted:
                    stats.n_book_events += 1
                    if inst and inst not in seen_inst:
                        seen_inst.add(inst)
                        stats.inst_ids.append(inst)
                    if stats.ts_ms_min is None or ts_ms < stats.ts_ms_min:
                        stats.ts_ms_min = ts_ms
                    if stats.ts_ms_max is None or ts_ms > stats.ts_ms_max:
                        stats.ts_ms_max = ts_ms
                    if seq_id is not None:
                        stats.seq_id_samples += 1
                        if prev_seq is not None:
                            if seq_id < prev_seq:
                                stats.seq_id_non_monotonic += 1
                            elif seq_id > prev_seq + 1:
                                stats.seq_id_skips += 1
                        prev_seq = seq_id
                    yield (ts_ms, inst, book)


def summarize_samples(samples: Sequence[Vamp1sSample]) -> ReplayGapStats:
    out = ReplayGapStats()
    if not samples:
        return out
    out.n_samples_1s = len(samples)
    out.n_seconds_with_update = sum(1 for s in samples if not s.carried_forward)
    out.n_seconds_stale_carry = sum(1 for s in samples if s.carried_forward)
    out.n_carried_forward = out.n_seconds_stale_carry
    out.n_health_stale = sum(1 for s in samples if s.health_stale)
    out.n_ts_rewind = sum(1 for s in samples if s.ts_rewind)
    out.n_vamp_valid = sum(1 for s in samples if s.vamp_valid)
    out.n_vamp_z_valid = sum(1 for s in samples if s.vamp_z is not None)
    out.n_ema12_ready = sum(1 for s in samples if s.ema12 is not None)
    out.n_ema21_ready = sum(1 for s in samples if s.ema21 is not None)
    ages = [s.book_age_ms for s in samples if s.book_age_ms is not None]
    if ages:
        out.book_age_ms_min = min(ages)
        out.book_age_ms_max = max(ages)
    out.ts_s_first = samples[0].ts_s
    out.ts_s_last = samples[-1].ts_s
    out.span_seconds = out.ts_s_last - out.ts_s_first + 1
    return out


@dataclass
class _BookState:
    book: BookTop5
    inst_id: str
    last_update_ts_ms: int


def replay_books5_to_1s(
    events: Iterable[tuple[int, str, BookTop5]],
    *,
    vamp_levels: int = VAMP_LEVELS,
    z_window: int = VAMP_Z_WINDOW,
    ema_fast: int = EMA_FAST,
    ema_slow: int = EMA_SLOW,
    fill_missing_seconds: bool = True,
) -> list[Vamp1sSample]:
    """Resample books5 updates onto a causal 1s closed UTC clock.

    For each closed second ``t``, the last book observed with
    ``floor(ts_ms/1000) == t`` is used when present. If
    ``fill_missing_seconds`` is True, empty seconds between the first and
    last observed second carry forward the last book (feature continuity)
    and set ``carried_forward=True`` (legacy ``book_stale`` alias).

    Trading health uses ``health_stale`` (book_age_ms > HEALTH_STALE_MS),
    not carried_forward alone. books5 seqId skips are not missing packets.
    """
    assert PAPER_ONLY is True

    ema12 = EMA(ema_fast)
    ema21 = EMA(ema_slow)
    zscore = RollingZScore(z_window)

    samples: list[Vamp1sSample] = []
    state: Optional[_BookState] = None
    pending: list[tuple[int, str, BookTop5]] = sorted(
        ((int(ts), inst, book) for ts, inst, book in events),
        key=lambda x: x[0],
    )
    if not pending:
        return samples

    by_sec: dict[int, list[tuple[int, str, BookTop5]]] = {}
    for ts_ms, inst, book in pending:
        sec = ts_ms // 1000
        by_sec.setdefault(sec, []).append((ts_ms, inst, book))

    first_sec = min(by_sec)
    last_sec = max(by_sec)

    last_seen_book_ts: Optional[int] = None

    def emit_for_second(sec: int, book_state: _BookState, carried: bool) -> Vamp1sSample:
        nonlocal last_seen_book_ts
        book = book_state.book
        n_bid = len(book.bids)
        n_ask = len(book.asks)
        mid: Optional[float] = None
        vamp5: Optional[float] = None
        edge: Optional[float] = None
        z: Optional[float] = None
        e12: Optional[float] = None
        e21: Optional[float] = None
        vamp_valid = False
        best_bid = book.bids[0][0] if book.bids else None
        best_ask = book.asks[0][0] if book.asks else None
        try:
            mid = mid_from_book(book)
            vamp5 = calculate_vamp(book, levels=vamp_levels)
            edge = vamp_edge_bps(vamp5, mid)
            vamp_valid = True
        except ValueError:
            mid = mid if mid is not None else (
                (best_bid + best_ask) / 2.0
                if best_bid is not None and best_ask is not None
                else None
            )
        if mid is not None and math.isfinite(mid):
            e12 = ema12.update(mid)
            e21 = ema21.update(mid)
        if edge is not None and math.isfinite(edge):
            z = zscore.update(edge)
        last_book_ts = int(book_state.last_update_ts_ms)
        decision_ts_ms = int(sec) * 1000
        book_age_ms = max(0, decision_ts_ms - last_book_ts)
        health_stale = book_age_ms > HEALTH_STALE_MS
        ts_rewind = last_seen_book_ts is not None and last_book_ts < last_seen_book_ts
        last_seen_book_ts = last_book_ts
        return Vamp1sSample(
            ts_s=sec,
            inst_id=book_state.inst_id,
            mid=mid,
            vamp5=vamp5,
            vamp_edge_bps=edge,
            vamp_z=z,
            ema12=e12,
            ema21=e21,
            best_bid=best_bid,
            best_ask=best_ask,
            book_stale=carried,  # legacy alias of carried_forward
            n_bid_levels=n_bid,
            n_ask_levels=n_ask,
            vamp_valid=vamp_valid,
            carried_forward=carried,
            book_age_ms=book_age_ms,
            health_stale=health_stale,
            last_book_ts_ms=last_book_ts,
            ts_rewind=ts_rewind,
        )

    if fill_missing_seconds:
        sec_iter: Iterable[int] = range(first_sec, last_sec + 1)
    else:
        sec_iter = sorted(by_sec)

    for sec in sec_iter:
        updates = by_sec.get(sec)
        if updates:
            # Last update within the closed second wins.
            ts_ms, inst, book = updates[-1]
            state = _BookState(book=book, inst_id=inst, last_update_ts_ms=ts_ms)
            samples.append(emit_for_second(sec, state, carried=False))
        elif state is not None:
            samples.append(emit_for_second(sec, state, carried=True))
    return samples


def replay_books5_jsonl_to_1s(
    paths: Sequence[Path | str],
    *,
    ingest_stats: Optional[Books5IngestStats] = None,
    **kwargs: Any,
) -> list[Vamp1sSample]:
    path_list = [Path(p) for p in paths]
    stats = ingest_stats if ingest_stats is not None else Books5IngestStats()
    return replay_books5_to_1s(
        iter_books5_events(path_list, stats=stats),
        **kwargs,
    )


def write_samples_csv(samples: Sequence[Vamp1sSample], path: Path | str) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(SAMPLE_COLUMNS))
        writer.writeheader()
        for s in samples:
            row = s.to_row()
            writer.writerow({k: ("" if v is None else v) for k, v in row.items()})
    return len(samples)


def write_samples_parquet(samples: Sequence[Vamp1sSample], path: Path | str) -> int:
    """Write parquet if pyarrow is installed; else raise ImportError."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "pyarrow required for parquet output; install pyarrow or use CSV"
        ) from e

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [s.to_row() for s in samples]
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path)
    return len(samples)


def write_samples(
    samples: Sequence[Vamp1sSample],
    out_dir: Path | str,
    *,
    stem: str = "vamp1s",
    formats: Sequence[str] = ("csv", "parquet"),
) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for fmt in formats:
        if fmt == "csv":
            p = out_dir / f"{stem}.csv"
            write_samples_csv(samples, p)
            written["csv"] = p
        elif fmt == "parquet":
            p = out_dir / f"{stem}.parquet"
            try:
                write_samples_parquet(samples, p)
                written["parquet"] = p
            except ImportError:
                # CSV is enough; parquet optional without bloating core deps.
                pass
        else:
            raise ValueError(f"unsupported format: {fmt}")
    return written
