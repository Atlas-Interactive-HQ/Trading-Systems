"""OKX EEA PUBLIC market-data collector.

REST: https://eea.okx.com  (public /api/v5/public/...)
WS:   wss://wseea.okx.com:8443/ws/v5/public

Public only — no API keys / no x-simulated-trading header.
Paper OMS later = OKX EEA demo (separate; requires demo keys — not this module).
Docs: https://my.okx.com/docs-v5/en/
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from atlas.common.config import AppConfig, VenueConfig, assert_public_only_path, refuse_if_secrets_present
from atlas.common.time import parse_exchange_ts_ms, utc_ms
from atlas.collectors.base import SequenceTracker, new_run_id, sleep_backoff
from atlas.storage.raw import JsonlRawWriter

log = logging.getLogger("atlas.collectors.okx_eea")

WS_DOCS = "https://my.okx.com/docs-v5/en/#overview-websocket-overview"


class OkxEeaPublicCollector:
    def __init__(self, cfg: AppConfig, venue_key: str = "okx_eea") -> None:
        refuse_if_secrets_present(cfg)
        if venue_key not in cfg.venues:
            raise KeyError(f"venue {venue_key!r} missing from config")
        self.cfg = cfg
        self.vcfg: VenueConfig = cfg.venues[venue_key]
        self.writer = JsonlRawWriter(cfg.data_dir, self.vcfg.venue)
        self.run_id = new_run_id("okx")
        self.seq = SequenceTracker("okx_eea")
        self._stop_at: float | None = None

    def _public_url(self, path: str, params: dict[str, str] | None = None) -> str:
        # OKX unauthenticated market data lives under /public/* and /market/*.
        allowed = ("/api/v5/public/", "/api/v5/market/")
        if not any(path.startswith(p) for p in allowed):
            raise PermissionError(
                f"OKX public collector only allows /api/v5/public/* or /api/v5/market/*, got {path!r}"
            )
        assert_public_only_path(path)
        base = self.vcfg.rest_base.rstrip("/")
        url = base + path
        if params:
            url = url + "?" + urlencode(params)
        assert_public_only_path(url)
        return url

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

    def _get(self, client: httpx.Client, path: str, params: dict[str, str] | None = None) -> Any:
        url = self._public_url(path, params)
        r = client.get(url, timeout=30.0)
        r.raise_for_status()
        return r.json()

    def fetch_instruments(self, client: httpx.Client) -> None:
        for inst_type in ("SWAP", "FUTURES"):
            data = self._get(
                client, "/api/v5/public/instruments", {"instType": inst_type}
            )
            self._write(f"instruments_{inst_type.lower()}", data, transport="rest")
            rows = data.get("data") or []
            log.info("instruments %s count=%s code=%s", inst_type, len(rows), data.get("code"))

    def fetch_tickers(self, client: httpx.Client) -> None:
        # EEA host: use /api/v5/market/ticker(s) (public, no auth).
        # /api/v5/public/tickers returned 404 on eea.okx.com (2026-09-01 probe).
        wanted = list(dict.fromkeys(list(self.vcfg.symbols) + list(self.vcfg.xperp_symbols)))
        for inst in wanted:
            data = self._get(client, "/api/v5/market/ticker", {"instId": inst})
            self._write("ticker", data, transport="rest", instrument=inst)
            for row in data.get("data") or []:
                ex_ts = parse_exchange_ts_ms(row.get("ts"))
                self._write(
                    "ticker_row",
                    row,
                    exchange_ts=ex_ts,
                    instrument=row.get("instId") or inst,
                    transport="rest",
                )
            # mark price (public)
            try:
                mark = self._get(client, "/api/v5/public/mark-price", {"instId": inst})
                for row in mark.get("data") or []:
                    ex_ts = parse_exchange_ts_ms(row.get("ts"))
                    self._write(
                        "mark_price",
                        row,
                        exchange_ts=ex_ts,
                        instrument=inst,
                        transport="rest",
                    )
            except httpx.HTTPStatusError as exc:
                log.warning("mark-price %s HTTP %s", inst, exc.response.status_code)
        # Optional batch snapshot for SWAP (same market family)
        try:
            batch = self._get(client, "/api/v5/market/tickers", {"instType": "SWAP"})
            self._write("tickers_swap", batch, transport="rest")
        except httpx.HTTPStatusError as exc:
            log.warning("market/tickers SWAP HTTP %s", exc.response.status_code)

    def fetch_funding(self, client: httpx.Client) -> None:
        for inst in list(self.vcfg.symbols) + list(self.vcfg.xperp_symbols):
            # funding-rate is public
            try:
                data = self._get(
                    client, "/api/v5/public/funding-rate", {"instId": inst}
                )
            except httpx.HTTPStatusError as exc:
                log.warning("funding-rate %s HTTP %s", inst, exc.response.status_code)
                continue
            rows = data.get("data") or []
            for row in rows:
                ex_ts = parse_exchange_ts_ms(
                    row.get("fundingTime") or row.get("ts") or row.get("nextFundingTime")
                )
                self._write(
                    "funding_rate",
                    row,
                    exchange_ts=ex_ts,
                    instrument=inst,
                    transport="rest",
                )
            log.info("funding_rate %s rows=%s", inst, len(rows))

    def run_rest_poll(self, duration_sec: float = 60.0) -> dict[str, Any]:
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
                        self.fetch_funding(client)
                        first = False
                    self.fetch_tickers(client)
                    # refresh funding occasionally
                    if self.seq.local_seq % 20 == 0:
                        self.fetch_funding(client)
                    attempt = 0
                except Exception as exc:  # noqa: BLE001
                    log.exception("OKX REST poll error: %s", exc)
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
        log.info("okx REST poll finished: %s", summary)
        return summary

    async def run_ws_stub(self, duration_sec: float = 15.0) -> dict[str, Any]:
        """Optional public WS for books5 / trades.

        Subscribe schema per OKX v5 public WS docs:
        {"op":"subscribe","args":[{"channel":"trades","instId":"BTC-USDT-SWAP"}, ...]}
        Docs: https://my.okx.com/docs-v5/en/
        """
        refuse_if_secrets_present(self.cfg)
        try:
            import websockets  # type: ignore
        except ImportError:
            log.warning("websockets not installed; skipping WS stub")
            return {"ws": "skipped", "reason": "no_websockets"}

        log.info("OKX WS stub; docs: %s", WS_DOCS)
        stop_at = time.monotonic() + max(0.0, duration_sec)
        attempt = 0
        frames = 0
        symbols = list(self.vcfg.symbols) or ["BTC-USDT-SWAP"]
        args = []
        for inst in symbols:
            args.append({"channel": "trades", "instId": inst})
            args.append({"channel": "bbo-tbt", "instId": inst})
            args.append({"channel": "books5", "instId": inst})

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
                    sub = {"op": "subscribe", "args": args}
                    await ws.send(json.dumps(sub))
                    self._write("ws_subscribe", sub, transport="ws")
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
                        channel = "ws_frame"
                        instrument = None
                        ex_ts = None
                        if isinstance(msg, dict):
                            arg = msg.get("arg") or {}
                            if isinstance(arg, dict):
                                ch = arg.get("channel")
                                instrument = arg.get("instId")
                                if ch:
                                    channel = f"ws_{ch}"
                            # seq gap if present
                            data_rows = msg.get("data")
                            if isinstance(data_rows, list) and data_rows:
                                first = data_rows[0]
                                if isinstance(first, dict):
                                    ex_ts = parse_exchange_ts_ms(first.get("ts"))
                                    # seqId is exchange-global across book feeds. books5/bbo-tbt
                                    # are thinned snapshots — apparent skips are normal, not gaps.
                                    # Contiguous gap detection belongs on books-l2-tbt (TODO if needed).
                                    # Docs: https://my.okx.com/docs-v5/en/
                                    seq_val = first.get("seqId")
                                    ch_name = arg.get("channel") if isinstance(arg, dict) else None
                                    if isinstance(seq_val, int) and ch_name in {
                                        "books-l2-tbt",
                                        "books50-l2-tbt",
                                    }:
                                        stream_key = f"{ch_name}:{instrument or ''}"
                                        gap = self.seq.observe_venue_seq(seq_val, stream_key=stream_key)
                                        if gap:
                                            self._write(
                                                "sequence_gap",
                                                gap,
                                                transport="ws",
                                                is_gap=True,
                                                gap_reason="venue_seq_gap",
                                                instrument=instrument,
                                            )
                            if msg.get("event") == "error":
                                log.warning("OKX WS error event: %s", msg)
                        self.writer.write_dict(
                            channel=channel,
                            payload=msg,
                            local_seq=self.seq.next_local(),
                            ingest_run_id=self.run_id,
                            exchange_ts=ex_ts,
                            receive_ts=receive_ts,
                            venue_instrument_id=instrument,
                            transport="ws",
                            schema_version=self.cfg.schema_version_raw,
                        )
                        frames += 1
            except Exception as exc:  # noqa: BLE001
                log.warning("OKX WS disconnect/error (attempt=%s): %s", attempt, exc)
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
        log.info("okx WS stub finished: %s", summary)
        return summary

    def run(self, duration_sec: float = 60.0, enable_ws: bool = False) -> dict[str, Any]:
        rest_summary = self.run_rest_poll(duration_sec=duration_sec)
        ws_summary: dict[str, Any] = {"ws": "disabled"}
        if enable_ws:
            ws_dur = min(15.0, max(5.0, duration_sec / 2))
            ws_summary = asyncio.run(self.run_ws_stub(duration_sec=ws_dur))
        return {"rest": rest_summary, "ws": ws_summary}
