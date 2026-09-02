"""Append-only paper journals under data/paper/{UTC-date}/."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from atlas.common.time import utc_date_str, utc_ms


class PaperJournal:
    def __init__(self, data_dir: str | Path, run_id: str) -> None:
        self.data_dir = Path(data_dir)
        self.run_id = run_id
        self._lock = threading.Lock()
        self._seq = 0
        self.root = self.data_dir / "paper"

    def _path(self, channel: str, ts_ms: int) -> Path:
        date = utc_date_str(ts_ms)
        directory = self.root / date
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
            **record,
            "ts_ms": ts,
        }
        path = self._path(channel, ts)
        line = json.dumps(row, separators=(",", ":"), ensure_ascii=False, default=str)
        with self._lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return path

    def write_summary(self, summary: dict[str, Any], *, ts_ms: int) -> Path:
        date = utc_date_str(ts_ms)
        directory = self.root / date
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"summary_{self.run_id}.json"
        # New file per run — never rewrite another run's summary.
        path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
        return path

    def dir_for(self, ts_ms: int) -> Path:
        return self.root / utc_date_str(ts_ms)
