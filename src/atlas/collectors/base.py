"""Shared collector helpers: sequencing, gap logging, backoff."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field


log = logging.getLogger("atlas.collectors")


@dataclass
class SequenceTracker:
    """Track local monotonic seq + optional venue sequence gaps (per stream key)."""

    name: str
    local_seq: int = 0
    last_venue_seq: int | None = None
    gap_count: int = 0
    events: list[dict] = field(default_factory=list)
    _last_by_key: dict[str, int] = field(default_factory=dict)

    def next_local(self) -> int:
        self.local_seq += 1
        return self.local_seq

    def observe_venue_seq(self, venue_seq: int | None, stream_key: str | None = None) -> dict | None:
        if venue_seq is None:
            return None
        key = stream_key or self.name
        last = self._last_by_key.get(key, self.last_venue_seq if stream_key is None else None)
        gap: dict | None = None
        if last is not None and venue_seq > last + 1:
            gap = {
                "stream": key,
                "expected_next": last + 1,
                "got": venue_seq,
                "skipped": venue_seq - last - 1,
            }
            self.gap_count += 1
            self.events.append(gap)
            log.warning(
                "sequence gap on %s: expected_next=%s got=%s skipped=%s",
                key,
                gap["expected_next"],
                gap["got"],
                gap["skipped"],
            )
        elif last is not None and venue_seq < last:
            gap = {
                "stream": key,
                "reason": "non_monotonic",
                "last": last,
                "got": venue_seq,
            }
            self.gap_count += 1
            self.events.append(gap)
            log.warning(
                "non-monotonic sequence on %s: last=%s got=%s",
                key,
                last,
                venue_seq,
            )
        self._last_by_key[key] = venue_seq
        if stream_key is None:
            self.last_venue_seq = venue_seq
        return gap


def new_run_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def sleep_backoff(attempt: int, base: float = 1.0, cap: float = 30.0) -> None:
    delay = min(cap, base * (2 ** max(0, attempt)))
    # simple jitter-ish via fractional attempt
    time.sleep(delay)
