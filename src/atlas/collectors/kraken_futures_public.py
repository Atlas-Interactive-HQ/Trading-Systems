"""Kraken Futures PUBLIC market-data collector.

REST base: https://futures.kraken.com/derivatives/api/v3
WS:        wss://futures.kraken.com/ws/v1

Public only — no API keys. Private/trading paths are refused.
Demo matching engine retired 2026-07-14; public MD remains on futures.kraken.com.
See phase1/07-venue-preflight-notes.md.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import httpx

from atlas.common.config import AppConfig, VenueConfig, assert_public_only_path, refuse_if_secrets_present
from atlas.common.time import parse_exchange_ts_ms, utc_ms
from atlas.collectors.base import SequenceTracker, new_run_id, sleep_backoff
from atlas.storage.raw import JsonlRawWriter

log = logging.getLogger("atlas.collectors.kraken_futures")

# Documented public REST paths (relative to rest_base)
PUBLIC_REST = {
    "instruments": "/instruments",
    "tickers": "/tickers",
    "ticker": "/tickers/{symbol}",
}

# WS feed names — see Kraken Futures WS docs.
# TODO(ws): confirm exact subscribe JSON against
# https://docs.kraken.com/api-reference/websocket-v1 / futures WS guide.
WS_FEEDS_TODO = (
    "https://docs.kraken.com/api-reference/websocket-v1",
    "https://docs.kraken.com/exchange/guides/overview",
)


class KrakenFuturesPublicCollector:
    def __init__(self, cfg: AppConfig, venue_key: str = "kraken_futures") -> None:
        refuse_if_secrets_present(cfg)
        if venue_key not in cfg.venues:
            raise KeyError(f"venue {venue_key!r} missing from config")
        self.cfg = cfg
        self.vcfg: VenueConfig = cfg.venues[venue_key]
        self.writer = JsonlRawWriter(cfg.data_dir, self.vcfg.venue)
        self.run_id = new_run_id("kraken")
        self.seq = SequenceTracker("kraken_futures")
        self._stop_at: float | None = None

    def _url(self, path: str) -> str:
        assert_public_only_path(path)
        base = self.vcfg.rest_base.rstrip("/")
        if not path.startswith("/"):
            path = "/" + path
        full = base + path
        assert_public_only_path(full)
        return full

    def _write(
        self,
        channel: str,
        payload: Any,
        *,
        exchange_ts: int | None = None,
        instrument: str | None = None,
        transport: str = "rest",
        is_gap: bool = False,
        gap_reason: str | None = None,
    ) -> None:
        self.writer.write_dict(
            channel=channel,
            payload=payload,
            local_seq=self.seq.next_local(),
            ingest_run_id=self.run_id,
            exchange_ts=exchange_ts,
            receive_ts=utc_ms(),
            venue_instrument_id=instrument,
            transport=transport,
            schema_version=self.cfg.schema_version_raw,
            is_gap=is_gap,
            gap_reason=gap_reason,
        )

    def fetch_instruments(self, client: httpx.Client) -> dict[str, Any]:
        url = self._url(PUBLIC_REST["instruments"])
        receive_before = utc_ms()
        r = client.get(url, timeout=30.0)
        r.raise_for_status()
        data = r.json()
        self._write("instruments", data, exchange_ts=None, transport="rest")
        log.info("instruments snapshot ok status=%s bytes≈%s", r.status_code, len(r.content))
        _ = receive_before
        return data

    def fetch_tickers(self, client: httpx.Client) -> dict[str, Any]:
        url = self._url(PUBLIC_REST["tickers"])
        r = client.get(url, timeout=30.0)
        r.raise_for_status()
        data = r.json()
        # Prefer per-symbol rows for configured symbols; still store full snapshot once
        self._write("tickers", data, transport="rest")
        tickers = data.get("tickers") or []
        wanted = set(self.vcfg.symbols)
        for t in tickers:
            sym = t.get("symbol")
            if wanted and sym not in wanted:
                continue
            # Kraken futures ticker often has time / lastTime fields — best effort
            ex_ts = parse_exchange_ts_ms(t.get("time") or t.get("lastTime") or t.get("timestamp"))
            self._write("ticker", t, exchange_ts=ex_ts, instrument=sym, transport="rest")
        log.info(
            "tickers snapshot ok symbols_matched=%s",
            sum(1 for t in tickers if t.get("symbol") in wanted) if wanted else len(tickers),
        )
        return data

    def run_rest_poll(self, duration_sec: float = 60.0) -> dict[str, Any]:
        """Poll instruments once, then tickers until duration elapses."""
        refuse_if_secrets_present(self.cfg)
        self._stop_at = time.monotonic() + max(0.0, duration_sec)
        attempt = 0
        started = utc_ms()
        with httpx.Client(headers={"User-Agent": "atlas-trading/0.1 public-md"}) as client:
            first = True
            while True:
                try:
                    if first:
                        self.fetch_instruments(client)
                        first = False
                    self.fetch_tickers(client)
                    attempt = 0
                except Exception as exc:  # noqa: BLE001 — log & backoff for smoke resilience
                    log.exception("REST poll error: %s", exc)
                    self._write(
                        "collector_error",
                        {"error": str(exc), "type": type(exc).__name__},
                        is_gap=True,
                        gap_reason="rest_error",
                    )
                    sleep_backoff(attempt)
                    attempt += 1
                if time.monotonic() >= (self._stop_at or 0):
                    break
                # sleep remaining poll interval but don't overrun stop
                remaining = (self._stop_at or 0) - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(self.vcfg.rest_poll_sec, remaining))
        summary = {
            "venue": self.vcfg.venue,
            "run_id": self.run_id,
            "local_seq": self.seq.local_seq,
            "gap_count": self.seq.gap_count,
            "started_ms": started,
            "ended_ms": utc_ms(),
            "data_dir": str(self.writer.data_dir),
        }
        log.info("kraken REST poll finished: %s", summary)
        return summary

    async def run_ws_stub(self, duration_sec: float = 15.0) -> dict[str, Any]:
        """Optional short WS subscribe for ticker/trade.

        Implemented conservatively: connect, send documented-style subscribe for
        ticker on configured symbols, record frames, reconnect simply on drop.
        If protocol details differ, REST remains the solid path; this logs TODO
        citations from WS_FEEDS_TODO.
        """
        refuse_if_secrets_present(self.cfg)
        try:
            import websockets  # type: ignore
        except ImportError:
            log.warning("websockets not installed; skipping WS stub")
            return {"ws": "skipped", "reason": "no_websockets"}

        log.info(
            "WS stub starting; confirm subscribe schema against: %s",
            ", ".join(WS_FEEDS_TODO),
        )
        stop_at = time.monotonic() + max(0.0, duration_sec)
        attempt = 0
        frames = 0
        while time.monotonic() < stop_at:
            try:
                assert_public_only_path(self.vcfg.ws_url)
                async with websockets.connect(
                    self.vcfg.ws_url,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=8_000_000,
                ) as ws:
                    attempt = 0
                    # Kraken Futures classic subscribe form (product feed)
                    # Docs may use {"event":"subscribe","feed":"ticker","product_ids":[...]}
                    sub = {
                        "event": "subscribe",
                        "feed": "ticker",
                        "product_ids": list(self.vcfg.symbols),
                    }
                    await ws.send(json.dumps(sub))
                    self._write("ws_subscribe", sub, transport="ws")
                    # Also try trade feed
                    sub_trade = {
                        "event": "subscribe",
                        "feed": "trade",
                        "product_ids": list(self.vcfg.symbols),
                    }
                    await ws.send(json.dumps(sub_trade))
                    self._write("ws_subscribe", sub_trade, transport="ws")

                    while time.monotonic() < stop_at:
                        timeout = max(0.1, stop_at - time.monotonic())
                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                        except asyncio.TimeoutError:
                            break
                        receive_ts = utc_ms()
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            msg = {"_raw": raw if isinstance(raw, str) else str(raw)}
                        feed = None
                        product = None
                        venue_seq = None
                        if isinstance(msg, dict):
                            feed = msg.get("feed") or msg.get("event")
                            product = msg.get("product_id") or msg.get("symbol")
                            venue_seq = msg.get("seq") or msg.get("sequence")
                            if isinstance(venue_seq, str) and venue_seq.isdigit():
                                venue_seq = int(venue_seq)
                            gap = self.seq.observe_venue_seq(
                                int(venue_seq) if isinstance(venue_seq, int) else None
                            )
                            if gap:
                                self._write(
                                    "sequence_gap",
                                    gap,
                                    transport="ws",
                                    is_gap=True,
                                    gap_reason="venue_seq_gap",
                                    instrument=str(product) if product else None,
                                )
                        channel = f"ws_{feed}" if feed else "ws_frame"
                        ex_ts = None
                        if isinstance(msg, dict):
                            ex_ts = parse_exchange_ts_ms(
                                msg.get("time") or msg.get("timestamp") or msg.get("t")
                            )
                        self.writer.write_dict(
                            channel=channel,
                            payload=msg,
                            local_seq=self.seq.next_local(),
                            ingest_run_id=self.run_id,
                            exchange_ts=ex_ts,
                            receive_ts=receive_ts,
                            venue_instrument_id=str(product) if product else None,
                            transport="ws",
                            schema_version=self.cfg.schema_version_raw,
                        )
                        frames += 1
            except Exception as exc:  # noqa: BLE001
                log.warning("WS disconnect/error (attempt=%s): %s", attempt, exc)
                self._write(
                    "ws_error",
                    {"error": str(exc), "attempt": attempt},
                    transport="ws",
                    is_gap=True,
                    gap_reason="ws_reconnect",
                )
                if time.monotonic() >= stop_at:
                    break
                sleep_backoff(attempt, base=1.0, cap=15.0)
                attempt += 1
        summary = {"ws_frames": frames, "gap_count": self.seq.gap_count, "run_id": self.run_id}
        log.info("kraken WS stub finished: %s", summary)
        return summary

    def run(self, duration_sec: float = 60.0, enable_ws: bool = False) -> dict[str, Any]:
        rest_summary = self.run_rest_poll(duration_sec=duration_sec)
        ws_summary: dict[str, Any] = {"ws": "disabled"}
        if enable_ws:
            # Short WS window overlapping / after REST; use min(15, duration)
            ws_dur = min(15.0, max(5.0, duration_sec / 2))
            ws_summary = asyncio.run(self.run_ws_stub(duration_sec=ws_dur))
        return {"rest": rest_summary, "ws": ws_summary}
