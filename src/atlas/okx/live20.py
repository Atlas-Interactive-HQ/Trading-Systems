"""Manual ≤€20 DOGE-USDC practice round-trip. Limit only. Never market. Never transfer.

Default is snapshot-only. Mutating requires explicit sell/buy/roundtrip flags AND
a client with tiny_live+allow_trade. Notional sz*px must be ≤ TINY_LIVE_NOTIONAL_CAP
(20). Script default max-notional is 10 for first practice.

not_a_forecast. Not Phase C. Not a weekday routine.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Callable

from atlas.common.time import utc_date_str, utc_ms
from atlas.okx.client import (
    TINY_LIVE_NOTIONAL_CAP,
    OkxEeaClient,
    estimate_spot_limit_notional,
)
from atlas.okx.instruments import assert_spot_inst_id
from atlas.oms.spot_demo import redact_record

LOCKED_INST = "DOGE-USDC"
DEFAULT_SZ = "50"
PRACTICE_NOTIONAL_DEFAULT = 10.0
QUOTE_FEE_BUFFER = 0.995
FILLED_STATES = frozenset({"filled"})
DONE_STATES = frozenset({"filled", "canceled", "cancelled", "mmp_canceled"})
SOURCE = "live20-roundtrip"
SOURCE_EXIT = "live20-resting-exits"


def _row0(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") or []
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    return {}


def ticker_book(payload: dict[str, Any]) -> dict[str, float | None]:
    row = _row0(payload)
    out: dict[str, float | None] = {"last": None, "bid": None, "ask": None}

    def f(key: str) -> float | None:
        raw = row.get(key)
        try:
            v = float(raw)
        except (TypeError, ValueError):
            return None
        return v if v > 0 else None

    out["last"] = f("last")
    out["bid"] = f("bidPx") or f("bid")
    out["ask"] = f("askPx") or f("ask")
    return out


def avail_ccy(payload: dict[str, Any], ccy: str) -> float:
    row = _row0(payload)
    details = row.get("details") or []
    if not isinstance(details, list):
        return 0.0
    want = ccy.upper()
    for d in details:
        if not isinstance(d, dict):
            continue
        if str(d.get("ccy") or "").upper() != want:
            continue
        for key in ("availBal", "availEq", "cashBal", "eq"):
            try:
                val = float(d.get(key) or 0)
            except (TypeError, ValueError):
                continue
            if val > 0:
                return val
        return 0.0
    return 0.0


def public_balance(payload: dict[str, Any]) -> dict[str, Any]:
    row = _row0(payload)
    details = []
    for d in row.get("details") or []:
        if not isinstance(d, dict):
            continue
        details.append(
            {
                "ccy": d.get("ccy"),
                "eq": d.get("eq"),
                "availBal": d.get("availBal"),
                "cashBal": d.get("cashBal"),
                "frozenBal": d.get("frozenBal"),
            }
        )
    return {
        "code": payload.get("code"),
        "msg": payload.get("msg"),
        "totalEq": row.get("totalEq"),
        "details": details,
    }


def public_asset(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") or []
    rows = []
    if isinstance(data, list):
        for d in data:
            if not isinstance(d, dict):
                continue
            rows.append(
                {
                    "ccy": d.get("ccy"),
                    "bal": d.get("bal"),
                    "availBal": d.get("availBal"),
                    "frozenBal": d.get("frozenBal"),
                }
            )
    return {"code": payload.get("code"), "msg": payload.get("msg"), "data": rows}


def order_view(payload: dict[str, Any]) -> dict[str, Any]:
    row = _row0(payload)
    return {
        "ordId": row.get("ordId"),
        "state": str(row.get("state") or ""),
        "side": row.get("side"),
        "px": row.get("px"),
        "sz": row.get("sz"),
        "accFillSz": row.get("accFillSz"),
        "avgPx": row.get("avgPx"),
        "fee": row.get("fee"),
        "feeCcy": row.get("feeCcy"),
        "code": payload.get("code"),
        "sCode": row.get("sCode"),
        "sMsg": row.get("sMsg"),
    }


def pending_public(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") or []
    rows: list[dict[str, Any]] = []
    if not isinstance(data, list):
        return rows
    for d in data:
        if not isinstance(d, dict):
            continue
        rows.append(
            {
                "ordId": d.get("ordId"),
                "instId": d.get("instId"),
                "side": d.get("side"),
                "px": d.get("px"),
                "sz": d.get("sz"),
                "state": d.get("state"),
                "ordType": d.get("ordType"),
            }
        )
    return rows


def mid_px(book: dict[str, float | None]) -> float | None:
    bid = book.get("bid")
    ask = book.get("ask")
    if bid is not None and ask is not None and float(bid) > 0 and float(ask) > 0:
        return (float(bid) + float(ask)) / 2.0
    last = book.get("last")
    if last is not None and float(last) > 0:
        return float(last)
    return None


def clamp_max_notional(raw: float) -> float:
    cap = float(TINY_LIVE_NOTIONAL_CAP)
    v = float(raw)
    if v <= 0:
        return min(PRACTICE_NOTIONAL_DEFAULT, cap)
    return min(v, cap)


class Live20Journal:
    """Append-only JSONL under data/live20/{UTC-date}/. No secrets."""

    def __init__(self, data_dir: str | Path, *, source: str = SOURCE) -> None:
        self.root = Path(data_dir) / "live20"
        self.source = str(source or SOURCE)
        self._lock = threading.Lock()
        self._seq = 0

    def append(self, channel: str, record: dict[str, Any], *, ts_ms: int | None = None) -> Path:
        ts = int(ts_ms if ts_ms is not None else utc_ms())
        with self._lock:
            self._seq += 1
            seq = self._seq
        row = redact_record(
            {
                "source": self.source,
                "seq": seq,
                "place_orders": False,
                "not_a_forecast": True,
                **record,
                "ts_ms": ts,
                "source": self.source,
            }
        )
        directory = self.root / utc_date_str(ts)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{channel}.jsonl"
        line = json.dumps(row, separators=(",", ":"), ensure_ascii=False, default=str)
        with self._lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return path


def ensure_issues_stub(data_dir: str | Path) -> Path:
    """Local gitignored issues log. Created empty-ish if missing; never contains secrets."""
    path = Path(data_dir) / "reports" / "live-20-issues.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(
            "# live-20 issues (local, gitignored)\n\n"
            "Append dated notes after a manual practice round-trip. No secrets. Not a forecast.\n",
            encoding="utf-8",
        )
    return path


def snapshot(client: OkxEeaClient, inst_id: str) -> dict[str, Any]:
    inst = assert_spot_inst_id(inst_id)
    base, quote = inst.split("-", 1)
    trading = client.get_balance()
    funding = client.get_asset_balances()
    ticker = client.get_ticker(inst)
    pending = client.get_orders_pending(inst_type="SPOT", inst_id=inst)
    book = ticker_book(ticker)
    return {
        "instId": inst,
        "base": base,
        "quote": quote,
        "last": book["last"],
        "bid": book["bid"],
        "ask": book["ask"],
        "avail_base": avail_ccy(trading, base),
        "avail_quote": avail_ccy(trading, quote),
        "trading_balance": public_balance(trading),
        "funding_balances": public_asset(funding),
        "pending_n": len(pending.get("data") or []) if isinstance(pending.get("data"), list) else 0,
        "pending_code": pending.get("code"),
        "pending_orders": pending_public(pending),
    }


def poll_order(
    client: OkxEeaClient,
    inst_id: str,
    ord_id: str,
    *,
    timeout_s: float,
    poll_s: float,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    deadline = time.monotonic() + max(0.0, float(timeout_s))
    last: dict[str, Any] = {"state": "", "ordId": ord_id}
    while True:
        payload = client.get_order(inst_id, ord_id=ord_id)
        last = order_view(payload)
        last["raw_code"] = payload.get("code")
        state = str(last.get("state") or "").lower()
        if state in DONE_STATES:
            last["timed_out"] = False
            return last
        if time.monotonic() >= deadline:
            last["timed_out"] = True
            return last
        if poll_s > 0:
            sleep(poll_s)
        else:
            last["timed_out"] = True
            return last


def _place_limit(
    client: OkxEeaClient,
    *,
    inst: str,
    side: str,
    sz: str,
    px: float,
    max_notional: float,
) -> dict[str, Any]:
    if str(side).lower() not in {"buy", "sell"}:
        return {"ok": False, "error": f"illegal side {side!r} (fail closed, no order)"}
    notional = estimate_spot_limit_notional(sz, px)
    if notional is None:
        return {"ok": False, "error": "could not estimate notional (fail closed, no order)"}
    if notional > TINY_LIVE_NOTIONAL_CAP:
        return {
            "ok": False,
            "error": (
                f"notional {notional:.4f} exceeds client cap {TINY_LIVE_NOTIONAL_CAP:g} "
                "(fail closed, no order)"
            ),
            "notional": notional,
        }
    if notional > max_notional:
        return {
            "ok": False,
            "error": (
                f"notional {notional:.4f} exceeds --max-notional {max_notional:g} "
                "(fail closed, no order)"
            ),
            "notional": notional,
        }
    placed = client.place_spot_limit(inst, str(side).lower(), str(sz), str(px))
    row = order_view(placed)
    s_code = str(row.get("sCode") or "")
    ok = str(placed.get("code")) == "0" and s_code in {"0", ""} and bool(row.get("ordId"))
    return {
        "ok": ok,
        "notional": notional,
        "px": px,
        "sz": str(sz),
        "side": str(side).lower(),
        "ordId": row.get("ordId"),
        "place": row,
        "code": placed.get("code"),
        "msg": placed.get("msg"),
    }


def run_roundtrip(
    client: OkxEeaClient,
    *,
    sell: bool,
    buy: bool,
    sz: str = DEFAULT_SZ,
    quote_sz: str | None = None,
    inst_id: str = LOCKED_INST,
    max_notional: float = PRACTICE_NOTIONAL_DEFAULT,
    timeout_s: float = 20.0,
    poll_s: float = 0.4,
    data_dir: str | Path = "data",
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Snapshot; optional aggressive-limit sell and/or buy-back. Never market."""
    mutate = bool(sell or buy)
    max_n = clamp_max_notional(max_notional)
    journal = Live20Journal(data_dir)
    issues = ensure_issues_stub(data_dir)
    try:
        inst = assert_spot_inst_id(inst_id)
    except ValueError as exc:
        return {
            "ok": False,
            "dry_run": not mutate,
            "error": str(exc),
            "place_orders": False,
            "not_a_forecast": True,
        }
    snap = snapshot(client, inst)
    result: dict[str, Any] = {
        "ok": True,
        "dry_run": not mutate,
        "mode": client.mode,
        "tiny_live": bool(getattr(client, "tiny_live", False)),
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE,
        "instId": inst,
        "sz": str(sz),
        "max_notional": max_n,
        "notional_cap": TINY_LIVE_NOTIONAL_CAP,
        "snapshot": snap,
        "sold": False,
        "bought": False,
        "n_posts": 0,
        "issues_log": str(issues),
        "disclaimer": (
            "live20 practice. not_a_forecast. not Phase C. not a routine. "
            "limit only. never market. never asset transfer. cap 20 unchanged."
        ),
    }
    journal.append(
        "events",
        {
            "kind": "session_start",
            "dry_run": not mutate,
            "sell": sell,
            "buy": buy,
            "instId": inst,
            "sz": str(sz),
            "avail_base": snap.get("avail_base"),
            "avail_quote": snap.get("avail_quote"),
        },
    )
    if not mutate:
        result["note"] = (
            "read-only. mutating requires --sell-fill and/or --buy-back, or --roundtrip."
        )
        return result

    n_posts = 0
    sell_filled = False
    if sell:
        bid = snap.get("bid")
        if bid is None:
            result["ok"] = False
            result["error"] = "no bidPx (fail closed, no sell)"
            journal.append("events", {"kind": "error", "error": result["error"]})
            return result
        try:
            size = float(sz)
        except (TypeError, ValueError):
            result["ok"] = False
            result["error"] = "invalid --sz (fail closed, no sell)"
            return result
        if float(snap.get("avail_base") or 0) < size:
            result["ok"] = False
            result["error"] = (
                f"avail {snap.get('avail_base')} < sz {size} (fail closed, no sell)"
            )
            journal.append("events", {"kind": "error", "error": result["error"]})
            return result
        intent = {
            "kind": "intent",
            "side": "sell",
            "instId": inst,
            "sz": str(sz),
            "px": bid,
            "ordType": "limit",
        }
        journal.append("events", intent)
        placed = _place_limit(
            client, inst=inst, side="sell", sz=str(sz), px=float(bid), max_notional=max_n
        )
        n_posts += 1
        result["sell_place"] = placed
        if not placed.get("ok"):
            result["ok"] = False
            result["error"] = placed.get("error") or "sell place failed"
            result["n_posts"] = n_posts
            journal.append("events", {"kind": "sell_place_fail", **placed})
            return result
        polled = poll_order(
            client,
            inst,
            str(placed.get("ordId")),
            timeout_s=timeout_s,
            poll_s=poll_s,
            sleep=sleep,
        )
        result["sell_order"] = polled
        journal.append(
            "events",
            {
                "kind": "sell_poll",
                "ordId": placed.get("ordId"),
                "state": polled.get("state"),
                "accFillSz": polled.get("accFillSz"),
                "avgPx": polled.get("avgPx"),
                "fee": polled.get("fee"),
                "feeCcy": polled.get("feeCcy"),
                "timed_out": polled.get("timed_out"),
            },
        )
        state = str(polled.get("state") or "").lower()
        if polled.get("timed_out") and state not in DONE_STATES:
            cancel = client.cancel_order(instId=inst, ordId=str(placed.get("ordId")))
            n_posts += 1
            result["sell_cancel"] = order_view(cancel)
            journal.append("events", {"kind": "sell_timeout_cancel", "ordId": placed.get("ordId")})
        sell_filled = state in FILLED_STATES
        result["sold"] = sell_filled
        if buy and not sell_filled:
            result["ok"] = False
            result["error"] = "sell did not fill; buy-back skipped"
            result["n_posts"] = n_posts
            return result

    if buy:
        snap2 = snapshot(client, inst)
        result["snapshot_after_sell"] = {
            "avail_base": snap2.get("avail_base"),
            "avail_quote": snap2.get("avail_quote"),
            "bid": snap2.get("bid"),
            "ask": snap2.get("ask"),
        }
        ask = snap2.get("ask")
        if ask is None:
            result["ok"] = False
            result["error"] = "no askPx (fail closed, no buy)"
            result["n_posts"] = n_posts
            return result
        if quote_sz not in (None, ""):
            try:
                quote = float(quote_sz)
            except (TypeError, ValueError):
                result["ok"] = False
                result["error"] = "invalid --quote-sz (fail closed, no buy)"
                result["n_posts"] = n_posts
                return result
        else:
            quote = float(snap2.get("avail_quote") or 0.0)
        quote = quote * QUOTE_FEE_BUFFER
        if quote <= 0:
            result["ok"] = False
            result["error"] = "no USDC (or quote) available for buy-back (fail closed)"
            result["n_posts"] = n_posts
            journal.append("events", {"kind": "error", "error": result["error"]})
            return result
        buy_sz = quote / float(ask)
        if buy_sz <= 0:
            result["ok"] = False
            result["error"] = "buy sz <= 0 (fail closed)"
            result["n_posts"] = n_posts
            return result
        buy_sz_s = f"{buy_sz:.8f}".rstrip("0").rstrip(".")
        intent = {
            "kind": "intent",
            "side": "buy",
            "instId": inst,
            "sz": buy_sz_s,
            "px": ask,
            "ordType": "limit",
            "quote": quote,
        }
        journal.append("events", intent)
        placed = _place_limit(
            client, inst=inst, side="buy", sz=buy_sz_s, px=float(ask), max_notional=max_n
        )
        n_posts += 1
        result["buy_place"] = placed
        if not placed.get("ok"):
            result["ok"] = False
            result["error"] = placed.get("error") or "buy place failed"
            result["n_posts"] = n_posts
            journal.append("events", {"kind": "buy_place_fail", **placed})
            return result
        polled = poll_order(
            client,
            inst,
            str(placed.get("ordId")),
            timeout_s=timeout_s,
            poll_s=poll_s,
            sleep=sleep,
        )
        result["buy_order"] = polled
        journal.append(
            "events",
            {
                "kind": "buy_poll",
                "ordId": placed.get("ordId"),
                "state": polled.get("state"),
                "accFillSz": polled.get("accFillSz"),
                "avgPx": polled.get("avgPx"),
                "fee": polled.get("fee"),
                "feeCcy": polled.get("feeCcy"),
                "timed_out": polled.get("timed_out"),
            },
        )
        state = str(polled.get("state") or "").lower()
        if polled.get("timed_out") and state not in DONE_STATES:
            cancel = client.cancel_order(instId=inst, ordId=str(placed.get("ordId")))
            n_posts += 1
            result["buy_cancel"] = order_view(cancel)
            journal.append("events", {"kind": "buy_timeout_cancel", "ordId": placed.get("ordId")})
        result["bought"] = state in FILLED_STATES
        if not result["bought"]:
            result["ok"] = False
            result["error"] = "buy did not fill"
            result["n_posts"] = n_posts
            return result

    result["n_posts"] = n_posts
    result["ok"] = True
    if sell:
        result["ok"] = bool(result.get("sold"))
    if buy:
        result["ok"] = bool(result.get("ok") and result.get("bought"))
    journal.append(
        "events",
        {
            "kind": "session_end",
            "ok": result["ok"],
            "sold": result.get("sold"),
            "bought": result.get("bought"),
            "n_posts": n_posts,
        },
    )
    result["journals"] = {"root": str(journal.root)}
    return result


def _fail_closed(result: dict[str, Any], journal: Live20Journal, error: str) -> dict[str, Any]:
    result["ok"] = False
    result["error"] = error
    journal.append("events", {"kind": "error", "error": error})
    return result


def run_resting_exits(
    client: OkxEeaClient,
    *,
    place_tp: bool = False,
    place_protect: bool = False,
    cancel_ord: str | None = None,
    cancel_all: bool = False,
    px: float | None = None,
    tp_pct: float | None = None,
    sz: str | None = None,
    inst_id: str = LOCKED_INST,
    max_notional: float = PRACTICE_NOTIONAL_DEFAULT,
    data_dir: str | Path = "data",
) -> dict[str, Any]:
    """Read-only snapshot, or place/cancel resting limit exits. Never market. Never auto-cancel a new place."""
    cancel_id = str(cancel_ord).strip() if cancel_ord not in (None, "") else ""
    mutate = bool(place_tp or place_protect or cancel_id or cancel_all)
    max_n = clamp_max_notional(max_notional)
    journal = Live20Journal(data_dir, source=SOURCE_EXIT)
    try:
        inst = assert_spot_inst_id(inst_id)
    except ValueError as exc:
        return {
            "ok": False,
            "dry_run": not mutate,
            "error": str(exc),
            "place_orders": False,
            "not_a_forecast": True,
            "source": SOURCE_EXIT,
        }
    snap = snapshot(client, inst)
    book = {"last": snap.get("last"), "bid": snap.get("bid"), "ask": snap.get("ask")}
    mid = mid_px(book)  # type: ignore[arg-type]
    result: dict[str, Any] = {
        "ok": True,
        "dry_run": not mutate,
        "mode": client.mode,
        "tiny_live": bool(getattr(client, "tiny_live", False)),
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE_EXIT,
        "instId": inst,
        "max_notional": max_n,
        "notional_cap": TINY_LIVE_NOTIONAL_CAP,
        "snapshot": snap,
        "mid": mid,
        "n_posts": 0,
        "placed": [],
        "canceled": [],
        "left_resting": True,
        "disclaimer": (
            "live20 resting exits. not_a_forecast. not Phase C. not a weekday auto-TP. "
            "limit only. never market. never exchange stop. leave resting (no auto-cancel). "
            "cap 20 unchanged. protect-limit is NOT a stop-loss."
        ),
    }
    journal.append(
        "events",
        {
            "kind": "session_start",
            "dry_run": not mutate,
            "place_tp": place_tp,
            "place_protect": place_protect,
            "cancel_ord": cancel_id or None,
            "cancel_all": cancel_all,
            "instId": inst,
            "sz": sz,
            "pending_n": snap.get("pending_n"),
        },
    )
    if not mutate:
        result["note"] = (
            "read-only. mutating requires --place-tp, --place-protect-limit, "
            "--cancel-ord, and/or --cancel-all-pending."
        )
        result["journals"] = {"root": str(journal.root)}
        return result

    # Fail closed on incomplete flags *before* any POST.
    if place_tp and place_protect:
        if tp_pct is None or px is None:
            return _fail_closed(
                result,
                journal,
                "place-tp + place-protect-limit needs --tp-pct (TP) and --px (protect) (fail closed, no POST)",
            )
    elif place_tp:
        has_px = px is not None
        has_pct = tp_pct is not None
        if has_px == has_pct:
            return _fail_closed(
                result,
                journal,
                "--place-tp requires exactly one of --px or --tp-pct (fail closed, no POST)",
            )
    elif place_protect:
        if px is None:
            return _fail_closed(
                result,
                journal,
                "--place-protect-limit requires --px below mid (fail closed, no POST)",
            )
        if tp_pct is not None:
            return _fail_closed(
                result,
                journal,
                "--place-protect-limit does not take --tp-pct (fail closed, no POST)",
            )

    if place_tp or place_protect:
        if sz in (None, ""):
            return _fail_closed(
                result, journal, "place requires --sz N (fail closed, no POST)"
            )
        try:
            size = float(sz)
        except (TypeError, ValueError):
            return _fail_closed(result, journal, "invalid --sz (fail closed, no POST)")
        if size <= 0:
            return _fail_closed(result, journal, "invalid --sz (fail closed, no POST)")

    if (place_tp or place_protect) and mid is None:
        return _fail_closed(result, journal, "no mid (bid/ask/last) (fail closed, no POST)")

    tp_px: float | None = None
    protect_px: float | None = None
    if place_tp:
        if tp_pct is not None:
            try:
                pct = float(tp_pct)
            except (TypeError, ValueError):
                return _fail_closed(result, journal, "invalid --tp-pct (fail closed, no POST)")
            if pct <= 0:
                return _fail_closed(
                    result, journal, "--tp-pct must be > 0 (fail closed, no POST)"
                )
            tp_px = float(mid) * (1.0 + pct / 100.0)  # type: ignore[arg-type]
        else:
            try:
                tp_px = float(px)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return _fail_closed(result, journal, "invalid --px (fail closed, no POST)")
        if tp_px <= float(mid):  # type: ignore[arg-type]
            return _fail_closed(
                result,
                journal,
                f"TP px {tp_px} must be above mid {mid} (fail closed, no POST)",
            )
    if place_protect:
        try:
            protect_px = float(px)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return _fail_closed(result, journal, "invalid --px (fail closed, no POST)")
        if protect_px >= float(mid):  # type: ignore[arg-type]
            return _fail_closed(
                result,
                journal,
                f"protect px {protect_px} must be below mid {mid} (limit-only, NOT a stop) "
                "(fail closed, no POST)",
            )

    n_posts = 0

    def _cancel_one(oid: str) -> dict[str, Any]:
        nonlocal n_posts
        cancel = client.cancel_order(instId=inst, ordId=str(oid))
        n_posts += 1
        view = order_view(cancel)
        rec = {"ok": str(cancel.get("code")) == "0", "ordId": oid, "cancel": view}
        journal.append("events", {"kind": "cancel", "ordId": oid, **view})
        result["canceled"].append(rec)
        return rec

    if cancel_id:
        pending_ids = {str(r.get("ordId") or "") for r in (snap.get("pending_orders") or [])}
        pending_inst = {
            str(r.get("ordId") or ""): str(r.get("instId") or "")
            for r in (snap.get("pending_orders") or [])
        }
        if pending_inst.get(cancel_id) not in (inst, "", None) and cancel_id in pending_ids:
            return _fail_closed(
                result,
                journal,
                f"ordId {cancel_id} is not {inst} (fail closed, no POST)",
            )
        _cancel_one(cancel_id)

    if cancel_all:
        for row in snap.get("pending_orders") or []:
            oid = str(row.get("ordId") or "")
            row_inst = str(row.get("instId") or inst)
            if not oid or row_inst != inst:
                continue
            if cancel_id and oid == cancel_id:
                continue
            _cancel_one(oid)

    if place_tp and tp_px is not None:
        journal.append(
            "events",
            {
                "kind": "intent",
                "role": "tp",
                "side": "sell",
                "instId": inst,
                "sz": str(sz),
                "px": tp_px,
                "ordType": "limit",
                "leave_resting": True,
            },
        )
        placed = _place_limit(
            client, inst=inst, side="sell", sz=str(sz), px=float(tp_px), max_notional=max_n
        )
        n_posts += 1
        result["tp_place"] = placed
        result["placed"].append({"role": "tp", **placed})
        journal.append("events", {"kind": "tp_place", "leave_resting": True, **placed})
        if not placed.get("ok"):
            result["ok"] = False
            result["error"] = placed.get("error") or "tp place failed"
            result["n_posts"] = n_posts
            result["journals"] = {"root": str(journal.root)}
            return result

    if place_protect and protect_px is not None:
        journal.append(
            "events",
            {
                "kind": "intent",
                "role": "protect_limit",
                "side": "sell",
                "instId": inst,
                "sz": str(sz),
                "px": protect_px,
                "ordType": "limit",
                "leave_resting": True,
                "not_a_stop": True,
            },
        )
        placed = _place_limit(
            client,
            inst=inst,
            side="sell",
            sz=str(sz),
            px=float(protect_px),
            max_notional=max_n,
        )
        n_posts += 1
        result["protect_place"] = placed
        result["placed"].append({"role": "protect_limit", **placed})
        journal.append(
            "events",
            {"kind": "protect_place", "leave_resting": True, "not_a_stop": True, **placed},
        )
        if not placed.get("ok"):
            result["ok"] = False
            result["error"] = placed.get("error") or "protect place failed"
            result["n_posts"] = n_posts
            result["journals"] = {"root": str(journal.root)}
            return result

    result["n_posts"] = n_posts
    result["ok"] = True
    result["left_resting"] = True
    journal.append(
        "events",
        {
            "kind": "session_end",
            "ok": True,
            "n_posts": n_posts,
            "left_resting": True,
            "n_placed": len(result["placed"]),
            "n_canceled": len(result["canceled"]),
        },
    )
    result["journals"] = {"root": str(journal.root)}
    return result
