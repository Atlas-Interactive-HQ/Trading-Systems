"""Raw append-only envelope schema (Pydantic)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RawEnvelope(BaseModel):
    """One JSONL line written under data/raw/{venue}/{date}/."""

    venue: str
    channel: str
    venue_instrument_id: str | None = None
    exchange_ts: int | None = None  # ms UTC, from payload when available
    receive_ts: int  # ms UTC, local I/O boundary
    local_seq: int
    ingest_run_id: str
    schema_version: str = "raw.envelope.v1"
    transport: str = "rest"  # rest | ws
    is_gap: bool = False
    gap_reason: str | None = None
    payload: dict[str, Any] | list[Any] | str | int | float | bool | None = Field(
        default=None
    )

    def to_jsonl_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
