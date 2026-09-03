"""Public candle loader for local paper. Unsigned REST only. Fail closed.

Sources (in `auto` order):
  1. Local JSONL under data/paper/candles/ or collected data/raw/**/candles*.jsonl
  2. OKX EEA public GET /api/v5/market/candles (SWAP linear, then spot fallback)
  3. Kraken Futures public charts (BTC backup)

Never sends API keys or x-simulated-trading. OKX demo 50001 is irrelevant here.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode

import httpx

from atlas.common.config import assert_public_only_path
from atlas.common.time import parse_exchange_ts_ms
from atlas.paper.types import Bar

log = logging.getLogger("atlas.paper.md")

USER_AGENT = "atlas-trading/0.1.5 (local-paper; public-md; no-keys)"
OKX_REST = "https://eea.okx.com"
KRAKEN_CHARTS = "https://futures.kraken.com/api/charts/v1"
OKX_CANDLES_PATH = "/api/v5/market/candles"
OKX_HISTORY_CANDLES_PATH = "/api/v5/market/history-candles"
# OKX docs: history-candles max 100 per request; /market/candles allows up to 300.
OKX_HISTORY_LIMIT_MAX = 100
OKX_CANDLES_LIMIT_MAX = 300

BAR_MS = {
    "15m": 15 * 60 * 1000,
    "1H": 60 * 60 * 1000,
    "1h": 60 * 60 * 1000,
    "1D": 24 * 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
}

SPOT_FALLBACK = {
    "BTC-USDT-SWAP": ("BTC-USDT", "BTC-USDC"),
    "DOGE-USDT-SWAP": ("DOGE-USDT", "DOGE-USDC"),
    "PEPE-USDT-SWAP": ("PEPE-USDT", "PEPE-USDC"),
    "SOL-USDT-SWAP": ("SOL-USDT", "SOL-USDC"),
}

KRAKEN_SYMBOL = {
    "BTC-USDT-SWAP": "PF_XBTUSD",
    "BTC-USDT": "PF_XBTUSD",
}


class PaperDataError(RuntimeError):
    """Missing or unusable market data — fail closed."""


def bar_ms(bar: str) -> int:
    if bar not in BAR_MS:
        raise PaperDataError(f"unsupported bar {bar!r}; use 15m, 1H, or 1D")
    return BAR_MS[bar]


def okx_bar(bar: str) -> str:
    if bar.lower() in ("1h", "1H"):
        return "1H"
    if bar == "15m":
        return "15m"
    if bar.lower() in ("1d", "1D"):
        return "1D"
    raise PaperDataError(f"unsupported bar {bar!r}")


def _to_bar(
    *,
    symbol: str,
    ts_open_ms: int,
    o: float,
    h: float,
    l: float,
    c: float,
    vol: float,
    bar: str,
    source: str,
    closed: bool,
) -> Bar:
    b = Bar(
        symbol=symbol,
        ts_open_ms=int(ts_open_ms),
        ts_close_ms=int(ts_open_ms) + bar_ms(bar),
        open=float(o),
        high=float(h),
        low=float(l),
        close=float(c),
        volume=float(vol or 0.0),
        closed=bool(closed),
        source=source,
    )
    b.validate()
    return b


def parse_okx_candle_row(row: Any, *, symbol: str, bar: str, source: str) -> Bar | None:
    if not isinstance(row, (list, tuple)) or len(row) < 5:
        return None
    ts = parse_exchange_ts_ms(row[0])
    if ts is None:
        return None
    confirm = True
    if len(row) >= 9:
        confirm = str(row[8]) == "1"
    elif len(row) >= 6 and str(row[-1]) in ("0", "1"):
        confirm = str(row[-1]) == "1"
    try:
        o, h, l, c = float(row[1]), float(row[2]), float(row[3]), float(row[4])
        vol = float(row[5]) if len(row) > 5 and row[5] not in ("", None) else 0.0
    except (TypeError, ValueError):
        return None
    if not confirm:
        return None
    try:
        return _to_bar(
            symbol=symbol,
            ts_open_ms=ts,
            o=o,
            h=h,
            l=l,
            c=c,
            vol=vol,
            bar=bar,
            source=source,
            closed=True,
        )
    except ValueError:
        return None


def parse_bar_dict(row: dict[str, Any], *, default_symbol: str, bar: str, source: str) -> Bar | None:
    sym = str(row.get("symbol") or row.get("instId") or default_symbol)
    ts = parse_exchange_ts_ms(
        row.get("ts_open_ms") or row.get("ts") or row.get("time") or row.get("timestamp")
    )
    if ts is None:
        return None
    try:
        o = float(row.get("open") if row.get("open") is not None else row["o"])
        h = float(row.get("high") if row.get("high") is not None else row["h"])
        l = float(row.get("low") if row.get("low") is not None else row["l"])
        c = float(row.get("close") if row.get("close") is not None else row["c"])
        vol = float(row.get("volume") or row.get("vol") or 0.0)
    except (KeyError, TypeError, ValueError):
        return None
    closed = row.get("closed", True)
    if str(row.get("confirm", "1")) == "0":
        closed = False
    if not closed:
        return None
    try:
        return _to_bar(
            symbol=sym,
            ts_open_ms=ts,
            o=o,
            h=h,
            l=l,
            c=c,
            vol=vol,
            bar=bar,
            source=source,
            closed=True,
        )
    except ValueError:
        return None


def merge_bars(*groups: Iterable[Bar]) -> list[Bar]:
    """Dedupe by ts_open_ms, sort ascending. Closed bars only (validate)."""
    return _dedupe_sort([b for g in groups for b in g])


def _dedupe_sort(bars: Iterable[Bar]) -> list[Bar]:
    by_ts: dict[int, Bar] = {}
    for b in bars:
        by_ts[b.ts_open_ms] = b
    out = [by_ts[k] for k in sorted(by_ts)]
    for b in out:
        b.validate()
    return out


def load_jsonl_candles(path: Path, *, symbol: str, bar: str) -> list[Bar]:
    if not path.is_file():
        raise PaperDataError(f"candle JSONL not found: {path}")
    bars: list[Bar] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PaperDataError(f"{path}:{line_no} invalid JSON") from exc
            payload = obj
            inst = symbol
            source = f"jsonl:{path.name}"
            if isinstance(obj, dict) and "payload" in obj:
                payload = obj["payload"]
                inst = str(obj.get("venue_instrument_id") or symbol)
                source = f"jsonl:{obj.get('venue') or path.name}"
            rows: list[Any]
            if isinstance(payload, dict) and isinstance(payload.get("data"), list):
                rows = payload["data"]
            elif isinstance(payload, list):
                rows = payload
            else:
                rows = [payload]
            for row in rows:
                parsed: Bar | None = None
                if isinstance(row, dict):
                    parsed = parse_bar_dict(row, default_symbol=inst, bar=bar, source=source)
                else:
                    parsed = parse_okx_candle_row(row, symbol=inst, bar=bar, source=source)
                if parsed is not None:
                    bars.append(parsed)
    if not bars:
        raise PaperDataError(f"no closed candles in {path}")
    return _dedupe_sort(bars)


def discover_jsonl(data_dir: Path, symbol: str, bar: str) -> Path | None:
    safe = symbol.replace("/", "_")
    candidates = [
        data_dir / "paper" / "candles" / f"{safe}_{bar}.jsonl",
        data_dir / "paper" / "candles" / f"{safe}.jsonl",
    ]
    raw = data_dir / "raw"
    if raw.is_dir():
        candidates.extend(sorted(raw.glob(f"**/candles*{safe}*.jsonl")))
        candidates.extend(sorted(raw.glob("**/candles.jsonl")))
        candidates.extend(sorted(raw.glob("**/history-candles.jsonl")))
    for p in candidates:
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None


def _http_get_json(client: httpx.Client, url: str) -> Any:
    r = client.get(url, timeout=30.0)
    r.raise_for_status()
    return r.json()


def parse_okx_candles_payload(
    payload: Any,
    *,
    symbol: str,
    bar: str,
    source: str,
) -> list[Bar]:
    """Parse an OKX candles envelope. Fail closed on bad payloads. Closed bars only."""
    if not isinstance(payload, dict):
        raise PaperDataError(f"OKX candles non-object for {symbol}")
    code = str(payload.get("code", ""))
    if code not in ("0", "0.0", ""):
        raise PaperDataError(f"OKX candles {symbol} code={code} msg={payload.get('msg')}")
    rows = payload.get("data")
    if rows is None:
        raise PaperDataError(f"OKX candles {symbol} missing data")
    if not isinstance(rows, list):
        raise PaperDataError(f"OKX candles {symbol} data is not a list")
    bars: list[Bar] = []
    for row in rows:
        parsed = parse_okx_candle_row(row, symbol=symbol, bar=bar, source=source)
        if parsed is not None:
            bars.append(parsed)
    return _dedupe_sort(bars)


def fetch_okx_candles(
    client: httpx.Client,
    symbol: str,
    bar: str,
    *,
    rest_base: str = OKX_REST,
    limit: int = 300,
) -> list[Bar]:
    """Recent closed candles via GET /api/v5/market/candles (now). No keys."""
    path = OKX_CANDLES_PATH
    assert_public_only_path(path)
    params = {
        "instId": symbol,
        "bar": okx_bar(bar),
        "limit": str(min(OKX_CANDLES_LIMIT_MAX, max(1, limit))),
    }
    url = rest_base.rstrip("/") + path + "?" + urlencode(params)
    payload = _http_get_json(client, url)
    return parse_okx_candles_payload(payload, symbol=symbol, bar=bar, source="okx_eea")


def fetch_okx_history_candles_page(
    client: httpx.Client,
    symbol: str,
    bar: str,
    *,
    rest_base: str = OKX_REST,
    after: int | None = None,
    before: int | None = None,
    limit: int = OKX_HISTORY_LIMIT_MAX,
) -> tuple[list[Bar], int]:
    """One page of GET /api/v5/market/history-candles. Public, unsigned.

    OKX: `after` = records *earlier than* ts; `before` = records *newer than* ts.
    Max limit is 100. Closed bars only (unconfirmed rows dropped by the parser).
    Returns (closed_bars, raw_row_count) so pagination does not stop just
    because the current (unconfirmed) candle was dropped.
    """
    path = OKX_HISTORY_CANDLES_PATH
    assert_public_only_path(path)
    params: dict[str, str] = {
        "instId": symbol,
        "bar": okx_bar(bar),
        "limit": str(min(OKX_HISTORY_LIMIT_MAX, max(1, int(limit)))),
    }
    if after is not None:
        params["after"] = str(int(after))
    if before is not None:
        params["before"] = str(int(before))
    url = rest_base.rstrip("/") + path + "?" + urlencode(params)
    payload = _http_get_json(client, url)
    if not isinstance(payload, dict):
        raise PaperDataError(f"OKX history-candles non-object for {symbol}")
    raw = payload.get("data")
    raw_n = len(raw) if isinstance(raw, list) else 0
    bars = parse_okx_candles_payload(
        payload, symbol=symbol, bar=bar, source="okx_eea_history"
    )
    return bars, raw_n


def fetch_okx_history_candles(
    client: httpx.Client,
    symbol: str,
    bar: str,
    *,
    rest_base: str = OKX_REST,
    start_ms: int | None = None,
    end_ms: int | None = None,
    limit: int = OKX_HISTORY_LIMIT_MAX,
    max_pages: int = 200,
    pause_s: float = 0.12,
) -> list[Bar]:
    """Paginate history-candles from `end_ms` backward until `start_ms`.

    Does not invent bars. Empty/bad pages fail closed (or stop pagination if
    some bars already arrived). Rate-limit pause defaults to 0.12s (OKX 20/2s).
    Short-page detection uses the *raw* row count, not closed-bar count.
    """
    page_limit = min(OKX_HISTORY_LIMIT_MAX, max(1, int(limit)))
    after: int | None = int(end_ms) if end_ms is not None else None
    collected: list[Bar] = []
    pages = 0
    while pages < max_pages:
        page, raw_n = fetch_okx_history_candles_page(
            client,
            symbol,
            bar,
            rest_base=rest_base,
            after=after,
            limit=page_limit,
        )
        pages += 1
        if raw_n == 0 and not page:
            break
        collected.extend(page)
        if not page:
            break
        oldest = min(b.ts_open_ms for b in page)
        if start_ms is not None and oldest <= int(start_ms):
            break
        if raw_n < page_limit:
            break
        if after is not None and oldest >= after:
            break
        after = oldest
        if pause_s > 0:
            time.sleep(pause_s)
    bars = _dedupe_sort(collected)
    if start_ms is not None:
        bars = [b for b in bars if b.ts_open_ms >= int(start_ms)]
    if end_ms is not None:
        bars = [b for b in bars if b.ts_open_ms < int(end_ms)]
    if not bars:
        raise PaperDataError(
            f"OKX history-candles empty for {symbol} {bar} "
            f"(start_ms={start_ms} end_ms={end_ms} pages={pages})"
        )
    return bars


def fetch_kraken_candles(
    client: httpx.Client,
    symbol: str,
    bar: str,
    *,
    limit: int = 300,
) -> list[Bar]:
    ksym = KRAKEN_SYMBOL.get(symbol)
    if not ksym:
        raise PaperDataError(f"no Kraken public chart mapping for {symbol}")
    # resolution in seconds. Path uses /trade/ as tick type (public charts), not a private API.
    res = {900: "900", 3_600_000: "3600"}.get(bar_ms(bar), str(bar_ms(bar) // 1000))
    url = f"{KRAKEN_CHARTS}/trade/{ksym}/{res}"
    payload = _http_get_json(client, url)
    candles = []
    if isinstance(payload, dict):
        candles = payload.get("candles") or payload.get("data") or []
        if isinstance(payload.get("result"), dict):
            candles = payload["result"].get("candles") or candles
    if not isinstance(candles, list) or not candles:
        raise PaperDataError(f"Kraken charts empty for {ksym}")
    bars: list[Bar] = []
    for row in candles:
        if not isinstance(row, dict):
            continue
        parsed = parse_bar_dict(row, default_symbol=symbol, bar=bar, source="kraken_deriv")
        if parsed is not None:
            bars.append(parsed)
    bars = _dedupe_sort(bars)
    if limit and len(bars) > limit:
        bars = bars[-limit:]
    if not bars:
        raise PaperDataError(f"Kraken charts unusable for {ksym}")
    return bars


def persist_candles(path: Path, bars: list[Bar]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for b in bars:
            f.write(
                json.dumps(
                    {
                        "symbol": b.symbol,
                        "ts_open_ms": b.ts_open_ms,
                        "ts_close_ms": b.ts_close_ms,
                        "open": b.open,
                        "high": b.high,
                        "low": b.low,
                        "close": b.close,
                        "volume": b.volume,
                        "closed": True,
                        "source": b.source,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )


def load_symbol_bars(
    *,
    symbol: str,
    bar: str,
    source: str,
    data_dir: Path,
    client: httpx.Client | None,
    rest_base: str,
    limit: int,
    jsonl_path: Path | None = None,
) -> list[Bar]:
    """Load closed bars. Fail closed if nothing usable."""
    src = source.lower()
    if jsonl_path is not None:
        return load_jsonl_candles(jsonl_path, symbol=symbol, bar=bar)

    if src in ("auto", "jsonl"):
        found = discover_jsonl(data_dir, symbol, bar)
        if found is not None:
            log.info("using local candles %s for %s %s", found, symbol, bar)
            return load_jsonl_candles(found, symbol=symbol, bar=bar)
        if src == "jsonl":
            raise PaperDataError(f"no local JSONL candles for {symbol} {bar}")

    if client is None:
        raise PaperDataError("no HTTP client and no local candles")

    errors: list[str] = []
    if src in ("auto", "okx_eea"):
        tried = [symbol, *SPOT_FALLBACK.get(symbol, ())]
        for inst in tried:
            try:
                bars = fetch_okx_candles(
                    client, inst, bar, rest_base=rest_base, limit=limit
                )
            except (PaperDataError, httpx.HTTPError) as exc:
                errors.append(f"okx:{inst}:{type(exc).__name__}:{exc}")
                log.warning("OKX candles failed %s %s: %s", inst, bar, exc)
                continue
            if bars:
                if inst != symbol:
                    bars = [
                        Bar(
                            symbol=symbol,
                            ts_open_ms=b.ts_open_ms,
                            ts_close_ms=b.ts_close_ms,
                            open=b.open,
                            high=b.high,
                            low=b.low,
                            close=b.close,
                            volume=b.volume,
                            closed=True,
                            source=b.source + f"|via:{inst}",
                        )
                        for b in bars
                    ]
                persist_candles(
                    data_dir / "paper" / "candles" / f"{symbol.replace('/', '_')}_{bar}.jsonl",
                    bars,
                )
                return bars
            errors.append(f"okx:{inst}:empty")

    if src in ("auto", "kraken"):
        try:
            bars = fetch_kraken_candles(client, symbol, bar, limit=limit)
            persist_candles(
                data_dir / "paper" / "candles" / f"{symbol.replace('/', '_')}_{bar}.jsonl",
                bars,
            )
            return bars
        except (PaperDataError, httpx.HTTPError) as exc:
            errors.append(f"kraken:{type(exc).__name__}:{exc}")
            log.warning("Kraken candles failed %s %s: %s", symbol, bar, exc)

    raise PaperDataError(
        f"no public candles for {symbol} {bar} (fail closed). attempts: {errors or ['none']}"
    )


def bars_1h_at_or_before(bars_1h: list[Bar], ts_close_ms: int) -> list[Bar]:
    """Causal 1h history: only bars whose close is <= 15m decision close."""
    return [b for b in bars_1h if b.ts_close_ms <= ts_close_ms]


def resample_1h(bars_15m: list[Bar]) -> list[Bar]:
    """Build 1h bars from complete 15m hours only (4 bars). Incomplete hours dropped."""
    hour_ms = BAR_MS["1H"]
    buckets: dict[int, list[Bar]] = {}
    for b in bars_15m:
        key = (b.ts_open_ms // hour_ms) * hour_ms
        buckets.setdefault(key, []).append(b)
    out: list[Bar] = []
    for key in sorted(buckets):
        rows = sorted(buckets[key], key=lambda x: x.ts_open_ms)
        if len(rows) != 4:
            continue
        if rows[0].ts_open_ms != key:
            continue
        try:
            out.append(
                _to_bar(
                    symbol=rows[0].symbol,
                    ts_open_ms=key,
                    o=rows[0].open,
                    h=max(x.high for x in rows),
                    l=min(x.low for x in rows),
                    c=rows[-1].close,
                    vol=sum(x.volume for x in rows),
                    bar="1H",
                    source="resample_15m",
                    closed=True,
                )
            )
        except ValueError:
            continue
    return out
