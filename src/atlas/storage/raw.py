"""Append-only raw JSONL writer: data/raw/{venue}/{date}/{channel}.jsonl"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from atlas.common.time import utc_date_str, utc_ms
from atlas.schemas.raw import RawEnvelope


class JsonlRawWriter:
    """Thread-safe append-only JSONL writer partitioned by venue/date."""

    def __init__(self, data_dir: str | Path, venue: str) -> None:
        self.data_dir = Path(data_dir)
        self.venue = venue
        self._lock = threading.Lock()
        self._handles: dict[str, Any] = {}

    def _path(self, channel: str, receive_ts: int) -> Path:
        date = utc_date_str(receive_ts)
        # Align with user request: data/raw/{venue}/{date}/
        # Also keep channel in filename for easy grepping.
        safe_ch = channel.replace("/", "_")
        directory = self.data_dir / "raw" / self.venue / date
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{safe_ch}.jsonl"

    def write(self, envelope: RawEnvelope) -> Path:
        path = self._path(envelope.channel, envelope.receive_ts)
        line = json.dumps(envelope.to_jsonl_dict(), separators=(",", ":"), ensure_ascii=False)
        with self._lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return path

    def write_dict(
        self,
        *,
        channel: str,
        payload: Any,
        local_seq: int,
        ingest_run_id: str,
        exchange_ts: int | None = None,
        receive_ts: int | None = None,
        venue_instrument_id: str | None = None,
        transport: str = "rest",
        schema_version: str = "raw.envelope.v1",
        is_gap: bool = False,
        gap_reason: str | None = None,
    ) -> Path:
        env = RawEnvelope(
            venue=self.venue,
            channel=channel,
            venue_instrument_id=venue_instrument_id,
            exchange_ts=exchange_ts,
            receive_ts=receive_ts if receive_ts is not None else utc_ms(),
            local_seq=local_seq,
            ingest_run_id=ingest_run_id,
            schema_version=schema_version,
            transport=transport,
            is_gap=is_gap,
            gap_reason=gap_reason,
            payload=payload,
        )
        return self.write(env)

    def close(self) -> None:
        with self._lock:
            self._handles.clear()
