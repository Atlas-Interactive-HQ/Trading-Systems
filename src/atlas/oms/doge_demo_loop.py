"""DOGE demo loop: public 15m breakout → OKX EEA demo OMS (paper only).

Locked universe: DOGE-USD (spot, tdMode=cash) and
DOGE-USD_UM_XPERP-310516 (FUTURES xperp, isolated, leverage ≤2x, net).
PEPE is deferred. Live trading is never allowed.

Default is signal-only (journal under data/oms/). Orders require an explicit
place flag AND a demo client with allow_trade=True.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

import httpx

from atlas.collectors.base import new_run_id
from atlas.common.time import utc_ms
from atlas.okx.client import PaperTradeDisabled
from atlas.oms.spot_demo import (
    PAPER_EQUITY_EUR,
    XPERP_LEVERAGE_MAX,
    OmsJournal,
    SpotDemoOms,
    cap_xperp_leverage,
    fmt_dec,
    round_px,
    _dec,
)
from atlas.paper.engine import strategy_from_app_config
from atlas.paper.md import (
    PaperDataError,
    USER_AGENT,
    bars_1h_at_or_before,
    fetch_okx_candles,
    resample_1h,
)
from atlas.okx.instruments import base_from_row, is_xperp
from atlas.paper.types import Bar, Signal
from atlas.strategy.breakout import BreakoutV1

log = logging.getLogger("atlas.oms.doge_demo")

LOCKED_SPOT_INST = "DOGE-USD"
LOCKED_XPERP_INST = "DOGE-USD_UM_XPERP-310516"
# Public EEA listing (candles/ticker). Never use this instId for demo orders.
PUBLIC_XPERP_MD_INST = "DOGE-USD_UM_XPERP-310404"
VENUE_KEYS = ("spot", "xperp", "both")


class VenueRoutingError(ValueError):
    """Unknown venue flag or PEPE/non-DOGE route refused."""


@dataclass(frozen=True)
class VenueSpec:
    key: str  # spot | xperp
    inst_id: str  # ORDER instId (demo-tradable)
    inst_type: str
    td_mode: str
    rule_type: str | None = None
    leverage: float | None = None
    md_inst_id: str | None = None  # public candles; may differ from order instId

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["md_inst_id"] = self.md_inst_id or self.inst_id
        return d

    @property
    def candles_inst_id(self) -> str:
        return self.md_inst_id or self.inst_id


def parse_venue_arg(venue: str) -> tuple[str, ...]:
    v = str(venue or "").strip().lower()
    if v == "both":
        return ("spot", "xperp")
    if v in ("spot", "xperp"):
        return (v,)
    raise VenueRoutingError(f"--venue must be spot|xperp|both, got {venue!r}")


def _assert_doge_only(inst_id: str) -> str:
    s = str(inst_id or "").strip().upper()
    if s.startswith("PEPE"):
        raise VenueRoutingError("PEPE is deferred; locked universe is DOGE only")
    if not s.startswith("DOGE"):
        raise VenueRoutingError(f"locked DOGE universe only, got {inst_id!r}")
    return s


def venues_from_config(cfg: Any, venue: str = "both") -> list[VenueSpec]:
    """Resolve locked DOGE legs. Never returns PEPE."""
    keys = parse_venue_arg(venue)
    demo = getattr(getattr(cfg, "okx", None), "doge_demo", None)
    out: list[VenueSpec] = []
    for key in keys:
        if key == "spot":
            inst = LOCKED_SPOT_INST
            inst_type = "SPOT"
            td_mode = "cash"
            rule_type = None
            leverage = None
            if demo is not None:
                inst = str(getattr(demo.spot, "inst_id", inst) or inst)
                inst_type = str(getattr(demo.spot, "inst_type", inst_type) or inst_type)
                td_mode = str(getattr(demo.spot, "td_mode", td_mode) or td_mode)
            inst = _assert_doge_only(inst)
            out.append(
                VenueSpec(
                    key="spot",
                    inst_id=inst,
                    inst_type=inst_type.upper(),
                    td_mode=td_mode.lower(),
                    rule_type=rule_type,
                    leverage=None,
                    md_inst_id=inst,
                )
            )
        elif key == "xperp":
            inst = LOCKED_XPERP_INST
            inst_type = "FUTURES"
            td_mode = "isolated"
            rule_type = "xperp"
            leverage = XPERP_LEVERAGE_MAX
            if demo is not None:
                inst = str(getattr(demo.xperp, "inst_id", inst) or inst)
                inst_type = str(getattr(demo.xperp, "inst_type", inst_type) or inst_type)
                td_mode = str(getattr(demo.xperp, "td_mode", td_mode) or td_mode)
                rule_type = str(getattr(demo.xperp, "rule_type", rule_type) or rule_type)
                raw_lev = getattr(demo.xperp, "leverage", None)
                if raw_lev is None:
                    raw_lev = getattr(demo, "leverage", leverage)
                leverage = cap_xperp_leverage(float(raw_lev or leverage))
            inst = _assert_doge_only(inst)
            md_inst = None
            if demo is not None:
                md_inst = getattr(demo.xperp, "md_inst_id", None)
                md_inst = str(md_inst).strip() if md_inst else None
            out.append(
                VenueSpec(
                    key="xperp",
                    inst_id=inst,
                    inst_type=inst_type.upper(),
                    td_mode="isolated" if td_mode.lower() != "cross" else "isolated",
                    rule_type=str(rule_type).lower(),
                    leverage=float(leverage),
                    md_inst_id=md_inst,
                )
            )
    if getattr(demo, "pepe_enabled", False):
        raise VenueRoutingError("pepe_enabled is locked off (PEPE deferred)")
    if getattr(demo, "ranging", False):
        raise VenueRoutingError("ranging is locked off")
    return out


def signal_to_dict(sig: Signal, *, venue: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "symbol": sig.symbol,
        "side": sig.side.value,
        "stop": sig.stop,
        "reason": sig.reason,
        "bar_ts_ms": sig.bar_ts_ms,
        "extras": dict(sig.extras or {}),
    }
    if venue:
        row["venue"] = venue
    return row


def scan_signals(
    strategy: BreakoutV1,
    bars_15m: Sequence[Bar],
    bars_1h: Sequence[Bar],
) -> list[Signal]:
    """Walk closed 15m history (no lookahead). 1h filter is causal."""
    warmup = strategy.warmup_bars()
    out: list[Signal] = []
    if len(bars_15m) <= warmup:
        return out
    for i in range(warmup, len(bars_15m)):
        window = list(bars_15m[: i + 1])
        last = window[-1]
        if not last.closed:
            continue
        h1 = bars_1h_at_or_before(list(bars_1h), last.ts_close_ms)
        sig = strategy.on_closed_bar(window, h1)
        if sig is not None:
            out.append(sig)
    return out


def is_public_only_xperp(inst_id: str) -> bool:
    """True for the public EEA listing that is not demo-order-routable."""
    return str(inst_id or "").strip().upper() == PUBLIC_XPERP_MD_INST.upper()


def pick_doge_xperp_inst(
    rows: Sequence[dict[str, Any]],
    configured: str,
) -> tuple[str, str]:
    """ORDER-path picker. Prefer configured demo instId. Never return public 310404."""
    want = str(configured or LOCKED_XPERP_INST).strip() or LOCKED_XPERP_INST
    live: list[str] = []
    for row in rows:
        if not is_xperp(row):
            continue
        if base_from_row(row) != "DOGE":
            continue
        inst = str(row.get("instId") or "")
        if not inst:
            continue
        if is_public_only_xperp(inst):
            continue
        if inst.upper() == want.upper():
            return inst, "configured"
        if str(row.get("state") or "").lower() == "live":
            live.append(inst)
    for inst in live:
        if inst.upper() == LOCKED_XPERP_INST.upper():
            return inst, "locked_demo"
    # Keep configured (310516). Do NOT fall back to public 310404.
    return want, "configured_missing"


def pick_doge_xperp_md_inst(
    rows: Sequence[dict[str, Any]],
    preferred: str,
    *,
    fallback: str = PUBLIC_XPERP_MD_INST,
) -> tuple[str, str]:
    """Public-candle picker. Prefer order instId if it has a public listing; else live public."""
    want = str(preferred or "").strip().upper()
    live: list[str] = []
    for row in rows:
        if not is_xperp(row):
            continue
        if base_from_row(row) != "DOGE":
            continue
        inst = str(row.get("instId") or "")
        if not inst:
            continue
        if inst.upper() == want:
            return inst, "configured"
        if str(row.get("state") or "").lower() == "live":
            live.append(inst)
    fb = str(fallback or PUBLIC_XPERP_MD_INST).strip()
    for inst in live:
        if inst.upper() == fb.upper():
            return inst, "public_fallback"
    if live:
        return live[0], "catalogue_live"
    if fb:
        return fb, "hardcoded_public_fallback"
    return preferred or PUBLIC_XPERP_MD_INST, "configured_missing"


def far_limit_px(
    last_px: float,
    side: str,
    tick: Decimal,
    offset_frac: float,
) -> str:
    if last_px <= 0:
        raise ValueError("last_px must be positive")
    off = float(offset_frac)
    if off <= 0 or off >= 1:
        off = 0.40
    if str(side).lower() == "buy":
        raw = last_px * (1.0 - off)
    else:
        raw = last_px * (1.0 + off)
    if raw <= 0:
        raw = last_px * 0.5
    return fmt_dec(round_px(Decimal(str(raw)), tick, side=side))


class DogeDemoLoop:
    """Fetch public candles, run breakout L+S, optionally place demo orders."""

    def __init__(
        self,
        cfg: Any,
        *,
        data_dir: str | Path,
        oms: SpotDemoOms | None = None,
        run_id: str | None = None,
        rest_base: str = "https://eea.okx.com",
    ) -> None:
        self.cfg = cfg
        self.data_dir = Path(data_dir)
        self.oms = oms
        self.run_id = run_id or new_run_id("doge-demo")
        self.rest_base = rest_base.rstrip("/")
        self.journal = oms.journal if oms is not None else OmsJournal(self.data_dir, self.run_id)
        self.strategy = strategy_from_app_config(cfg)

    def _http(self) -> httpx.Client:
        return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)

    def _resolve_xperp_specs(
        self, specs: list[VenueSpec], client: httpx.Client
    ) -> list[VenueSpec]:
        """Split public MD instId vs demo order instId.

        Orders always stay on the demo-tradable id (310516) from
        GET /api/v5/account/instruments (x-simulated-trading). Public
        310404 is allowed only as a candle/ticker fallback.
        """
        if not any(s.key == "xperp" for s in specs):
            return [
                s if s.md_inst_id else VenueSpec(
                    key=s.key,
                    inst_id=s.inst_id,
                    inst_type=s.inst_type,
                    td_mode=s.td_mode,
                    rule_type=s.rule_type,
                    leverage=s.leverage,
                    md_inst_id=s.inst_id,
                )
                for s in specs
            ]
        public_rows: list[dict[str, Any]] = []
        url = f"{self.rest_base}/api/v5/public/instruments"
        try:
            r = client.get(url, params={"instType": "FUTURES"})
            r.raise_for_status()
            payload = r.json()
            public_rows = list(payload.get("data") or [])
        except (httpx.HTTPError, ValueError) as exc:
            self.journal.append(
                "events",
                {
                    "kind": "xperp_catalogue_error",
                    "source": "public",
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )

        account_rows: list[dict[str, Any]] | None = None
        if self.oms is not None:
            try:
                raw = self.oms.client.get_account_instruments("FUTURES")
                account_rows = list(raw.get("data") or [])
                self.journal.append(
                    "events",
                    {
                        "kind": "xperp_account_instruments",
                        "okx_code": raw.get("code"),
                        "n": len(account_rows),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                self.journal.append(
                    "events",
                    {
                        "kind": "xperp_catalogue_error",
                        "source": "account",
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
                account_rows = None

        out: list[VenueSpec] = []
        for spec in specs:
            if spec.key != "xperp":
                if spec.md_inst_id is None:
                    spec = VenueSpec(
                        key=spec.key,
                        inst_id=spec.inst_id,
                        inst_type=spec.inst_type,
                        td_mode=spec.td_mode,
                        rule_type=spec.rule_type,
                        leverage=spec.leverage,
                        md_inst_id=spec.inst_id,
                    )
                out.append(spec)
                continue

            if account_rows is not None:
                order_inst, order_reason = pick_doge_xperp_inst(account_rows, spec.inst_id)
            else:
                order_inst, order_reason = spec.inst_id, "configured_no_account_catalogue"
            if is_public_only_xperp(order_inst):
                order_inst = LOCKED_XPERP_INST
                order_reason = "refused_public_310404"

            md_fallback = spec.md_inst_id or PUBLIC_XPERP_MD_INST
            if public_rows:
                md_inst, md_reason = pick_doge_xperp_md_inst(
                    public_rows, order_inst, fallback=md_fallback
                )
            else:
                md_inst, md_reason = md_fallback, "public_fallback_no_catalogue"

            self.journal.append(
                "events",
                {
                    "kind": "xperp_inst_resolved",
                    "configured": spec.inst_id,
                    "order_inst": order_inst,
                    "order_reason": order_reason,
                    "md_inst": md_inst,
                    "md_reason": md_reason,
                    "resolved": order_inst,
                    "reason": order_reason,
                },
            )
            out.append(
                VenueSpec(
                    key=spec.key,
                    inst_id=order_inst,
                    inst_type=spec.inst_type,
                    td_mode=spec.td_mode,
                    rule_type=spec.rule_type,
                    leverage=spec.leverage,
                    md_inst_id=md_inst,
                )
            )
        return out

    def fetch_bars(
        self,
        inst_id: str,
        *,
        n_15m: int,
        client: httpx.Client,
    ) -> tuple[list[Bar], list[Bar], str | None]:
        warmup = self.strategy.warmup_bars() + 8
        limit = min(300, max(n_15m + warmup, 50))
        err: str | None = None
        try:
            rows = fetch_okx_candles(
                client, inst_id, "15m", rest_base=self.rest_base, limit=limit
            )
        except (PaperDataError, httpx.HTTPError) as exc:
            return [], [], f"{type(exc).__name__}: {exc}"
        if not rows:
            return [], [], "empty_15m"
        if len(rows) > n_15m:
            rows = rows[-n_15m:]
        try:
            h1 = fetch_okx_candles(
                client,
                inst_id,
                "1H",
                rest_base=self.rest_base,
                limit=min(300, max(50, n_15m // 4 + 16)),
            )
        except (PaperDataError, httpx.HTTPError) as exc:
            err = f"1h:{type(exc).__name__}:{exc}"
            h1 = resample_1h(rows)
        if not h1:
            h1 = resample_1h(rows)
        return rows, h1, err

    def run(
        self,
        *,
        venue: str = "both",
        place_orders: bool = False,
        bars: int = 96,
        live_demo_orders: bool | None = None,
        plumbing_if_no_signal: bool = False,
    ) -> dict[str, Any]:
        if live_demo_orders is not None:
            place_orders = bool(live_demo_orders) or place_orders
        if place_orders:
            if self.oms is None:
                raise PaperTradeDisabled("place_orders requires a demo SpotDemoOms")
            if self.oms.client.mode != "demo":
                raise PaperTradeDisabled("place_orders is demo-only")
            if not self.oms.client.allow_trade:
                raise PaperTradeDisabled(
                    "place_orders requires demo client allow_trade=True"
                )
        specs = venues_from_config(self.cfg, venue)
        demo = getattr(getattr(self.cfg, "okx", None), "doge_demo", None)
        offset = float(getattr(demo, "far_limit_offset_frac", 0.40) or 0.40)
        ts = utc_ms()
        self.journal.append(
            "events",
            {
                "kind": "doge_demo_session_start",
                "place_orders": bool(place_orders),
                "venue": venue,
                "venues": [s.as_dict() for s in specs],
                "bars": bars,
                "paper_equity_eur": float(getattr(demo, "paper_equity_eur", PAPER_EQUITY_EUR)),
                "ranging": False,
                "pepe_enabled": False,
                "plumbing_if_no_signal": bool(plumbing_if_no_signal),
            },
            ts_ms=ts,
        )
        if place_orders and self.oms is not None:
            universe_ids = {s.inst_id for s in venues_from_config(self.cfg, "both")}
            self.oms.clear_stale_open_state(universe_ids)
        legs: list[dict[str, Any]] = []
        all_signals: list[dict[str, Any]] = []
        with self._http() as client:
            specs = self._resolve_xperp_specs(specs, client)
            scanned: list[tuple[VenueSpec, list[Bar], list[Bar], str | None, float, list, Any]] = []
            for spec in specs:
                md_id = spec.candles_inst_id
                b15, b1h, fetch_err = self.fetch_bars(md_id, n_15m=bars, client=client)
                used_md = md_id
                if not b15 and spec.key == "xperp" and md_id != PUBLIC_XPERP_MD_INST:
                    b15, b1h, err2 = self.fetch_bars(
                        PUBLIC_XPERP_MD_INST, n_15m=bars, client=client
                    )
                    if b15:
                        used_md = PUBLIC_XPERP_MD_INST
                        fetch_err = fetch_err
                        spec = VenueSpec(
                            key=spec.key,
                            inst_id=spec.inst_id,
                            inst_type=spec.inst_type,
                            td_mode=spec.td_mode,
                            rule_type=spec.rule_type,
                            leverage=spec.leverage,
                            md_inst_id=PUBLIC_XPERP_MD_INST,
                        )
                        self.journal.append(
                            "events",
                            {
                                "kind": "xperp_md_fallback",
                                "tried": md_id,
                                "used": PUBLIC_XPERP_MD_INST,
                                "prior_error": fetch_err,
                            },
                        )
                    else:
                        fetch_err = fetch_err or err2
                elif used_md != spec.inst_id:
                    spec = VenueSpec(
                        key=spec.key,
                        inst_id=spec.inst_id,
                        inst_type=spec.inst_type,
                        td_mode=spec.td_mode,
                        rule_type=spec.rule_type,
                        leverage=spec.leverage,
                        md_inst_id=used_md,
                    )
                last_px = float(b15[-1].close) if b15 else 0.0
                sigs = scan_signals(self.strategy, b15, b1h) if b15 else []
                current = None
                if b15:
                    h1 = bars_1h_at_or_before(b1h, b15[-1].ts_close_ms)
                    current = self.strategy.on_closed_bar(b15, h1)
                scanned.append((spec, b15, b1h, fetch_err, last_px, sigs, current))

            any_current = any(item[6] is not None for item in scanned)
            for spec, b15, b1h, fetch_err, last_px, sigs, current in scanned:
                sig_rows = [signal_to_dict(s, venue=spec.key) for s in sigs]
                for row in sig_rows:
                    self.journal.append("decisions", {"kind": "breakout_signal", **row})
                    all_signals.append(row)
                current_row = (
                    signal_to_dict(current, venue=spec.key) if current is not None else None
                )
                if current_row:
                    self.journal.append(
                        "decisions", {"kind": "breakout_current", **current_row}
                    )
                place_record: dict[str, Any] | None = None
                if place_orders and current is not None:
                    place_record = self._place_from_signal(
                        spec, current, last_px, offset_frac=offset
                    )
                elif place_orders and plumbing_if_no_signal and not any_current:
                    place_record = self._place_plumbing(
                        spec, last_px, offset_frac=offset, reason="no_current_signal"
                    )
                elif place_orders:
                    place_record = {
                        "placed": False,
                        "reason": "no_current_signal",
                        "venue": spec.key,
                        "instId": spec.inst_id,
                        "mdInstId": spec.candles_inst_id,
                    }
                    self.journal.append("orders", {"kind": "skip", **place_record})
                legs.append(
                    {
                        "venue": spec.key,
                        "instId": spec.inst_id,
                        "mdInstId": spec.candles_inst_id,
                        "instType": spec.inst_type,
                        "tdMode": spec.td_mode,
                        "n_bars_15m": len(b15),
                        "n_bars_1h": len(b1h),
                        "last_px": last_px,
                        "last_bar_ts_ms": b15[-1].ts_close_ms if b15 else None,
                        "fetch_error": fetch_err,
                        "n_signals": len(sig_rows),
                        "signals": sig_rows,
                        "current": current_row,
                        "place": place_record,
                    }
                )
        summary = {
            "ok": True,
            "dry_run": not place_orders,
            "mode": "demo",
            "place_orders": bool(place_orders),
            "plumbing_if_no_signal": bool(plumbing_if_no_signal),
            "historical_signals_only": bool(
                place_orders and plumbing_if_no_signal and not any(
                    leg.get("current") for leg in legs
                )
            ),
            "run_id": self.run_id,
            "venue": venue,
            "n_signals": len(all_signals),
            "signals": all_signals,
            "legs": legs,
        }
        self.journal.append("events", {"kind": "doge_demo_session_end", **summary})
        return summary

    def _place_from_signal(
        self,
        spec: VenueSpec,
        sig: Signal,
        last_px: float,
        *,
        offset_frac: float,
    ) -> dict[str, Any]:
        assert self.oms is not None
        snap = self.oms.refresh_account(fail_closed_zero=True)
        universe_ids = {s.inst_id for s in venues_from_config(self.cfg, "both")}
        gate = self.oms.gate_new_entry(snap, inst_ids=universe_ids)
        record: dict[str, Any] = {
            "venue": spec.key,
            "instId": spec.inst_id,
            "signal": signal_to_dict(sig, venue=spec.key),
            "gate": gate,
            "placed": False,
        }
        if not gate.get("allowed"):
            record["reason"] = gate.get("reason")
            self.journal.append("orders", {"kind": "skip_gate", **record})
            return record
        if spec.key == "xperp" and is_public_only_xperp(spec.inst_id):
            raise VenueRoutingError(
                "xperp orders must use demo 310516, not public 310404"
            )
        side = sig.side.buy_sell
        if spec.key == "spot":
            inst = self.oms.resolve_symbol(spec.inst_id)
            tick = _dec(inst.get("tickSz") or "0.00000001")
            px = float(far_limit_px(last_px, side, tick, offset_frac))
            plan = self.oms.size_order(
                snap, inst, last_px=last_px, tiny=True, px=px, side=side, ord_type="limit"
            )
            placed = self.oms.place(plan, dry_run=False)
        else:
            meta = self._xperp_meta(spec.inst_id)
            tick = _dec(meta.get("tickSz") or "0.00000001")
            px_s = far_limit_px(last_px, side, tick, offset_frac)
            plan = self.oms.size_xperp_order(
                meta,
                last_px=last_px,
                side=side,
                stop=sig.stop,
                tiny=True,
                px=float(px_s),
                ord_type="limit",
                leverage=spec.leverage or XPERP_LEVERAGE_MAX,
            )
            placed = self.oms.place_xperp(
                plan,
                dry_run=False,
                td_mode="isolated",
                leverage=spec.leverage or XPERP_LEVERAGE_MAX,
                set_leverage=True,
            )
        record["placed"] = bool(placed.get("placed"))
        record["plan"] = plan.as_dict()
        record["place"] = {
            k: placed.get(k)
            for k in ("dry_run", "placed", "reason", "response", "http_status")
            if k in placed
        }
        record["ordId"] = _ord_id_from_place(placed)
        return record

    def _place_plumbing(
        self,
        spec: VenueSpec,
        last_px: float,
        *,
        offset_frac: float,
        reason: str = "no_current_signal",
    ) -> dict[str, Any]:
        """Far-limit min-size place+cancel on the same OMS path as live signals."""
        assert self.oms is not None
        record: dict[str, Any] = {
            "kind": "plumbing",
            "venue": spec.key,
            "instId": spec.inst_id,
            "mdInstId": spec.candles_inst_id,
            "placed": False,
            "cancelled": False,
            "reason": reason,
            "historical_signals_only": True,
        }
        if last_px <= 0:
            record["reason"] = "no_px"
            self.journal.append("orders", {"kind": "skip_plumbing", **record})
            return record
        if spec.key == "xperp" and is_public_only_xperp(spec.inst_id):
            record["reason"] = "refused_public_310404"
            self.journal.append("orders", {"kind": "skip_plumbing", **record})
            return record
        snap = self.oms.refresh_account(fail_closed_zero=True)
        universe_ids = {s.inst_id for s in venues_from_config(self.cfg, "both")}
        self.oms.clear_stale_open_state(universe_ids)
        gate = self.oms.gate_new_entry(snap, inst_ids=universe_ids)
        record["gate"] = gate
        if not gate.get("allowed"):
            record["reason"] = gate.get("reason")
            self.journal.append("orders", {"kind": "skip_gate", **record})
            return record
        side = "buy"
        if spec.key == "spot":
            inst = self.oms.resolve_symbol(spec.inst_id)
            tick = _dec(inst.get("tickSz") or "0.00000001")
            px = float(far_limit_px(last_px, side, tick, offset_frac))
            plan = self.oms.size_order(
                snap, inst, last_px=last_px, tiny=True, px=px, side=side, ord_type="limit"
            )
            placed = self.oms.place(plan, dry_run=False)
        else:
            meta = self._xperp_meta(spec.inst_id)
            tick = _dec(meta.get("tickSz") or "0.00000001")
            px_s = far_limit_px(last_px, side, tick, offset_frac)
            plan = self.oms.size_xperp_order(
                meta,
                last_px=last_px,
                side=side,
                tiny=True,
                px=float(px_s),
                ord_type="limit",
                leverage=spec.leverage or XPERP_LEVERAGE_MAX,
            )
            placed = self.oms.place_xperp(
                plan,
                dry_run=False,
                td_mode="isolated",
                leverage=spec.leverage or XPERP_LEVERAGE_MAX,
                set_leverage=True,
            )
        record["placed"] = bool(placed.get("placed"))
        record["plan"] = plan.as_dict()
        record["place"] = {
            k: placed.get(k)
            for k in ("dry_run", "placed", "reason", "response", "http_status")
            if k in placed
        }
        ord_id = _ord_id_from_place(placed)
        record["ordId"] = ord_id
        if record["placed"] and ord_id:
            cancel = self.oms.cancel(spec.inst_id, ord_id)
            record["cancel"] = {
                k: cancel.get(k)
                for k in ("ordId", "instId", "open_inst_cleared", "response")
                if k in cancel
            }
            record["cancelled"] = bool(cancel.get("open_inst_cleared"))
        self.journal.append("orders", record)
        return record

    def _xperp_meta(self, inst_id: str) -> dict[str, Any]:
        """Contract meta for the ORDER instId. Prefer demo account/instruments."""
        assert self.oms is not None
        want = inst_id.upper()
        found: dict[str, Any] | None = None
        try:
            raw = self.oms.client.get_account_instruments("FUTURES")
            rows = raw.get("data") or []
            for row in rows if isinstance(rows, list) else []:
                if isinstance(row, dict) and str(row.get("instId") or "").upper() == want:
                    found = row
                    break
        except Exception:  # noqa: BLE001
            found = None
        if found is None:
            try:
                raw = self.oms.client.get_instruments("FUTURES")
                rows = raw.get("data") or []
                for row in rows if isinstance(rows, list) else []:
                    if isinstance(row, dict) and str(row.get("instId") or "").upper() == want:
                        found = row
                        break
            except Exception:  # noqa: BLE001
                found = None
        if found is not None:
            return {
                "instId": inst_id,
                "instType": found.get("instType") or "FUTURES",
                "ctVal": found.get("ctVal"),
                "minSz": found.get("minSz"),
                "lotSz": found.get("lotSz"),
                "tickSz": found.get("tickSz"),
                "ruleType": found.get("ruleType"),
                "state": found.get("state"),
            }
        return {
            "instId": inst_id,
            "instType": "FUTURES",
            "ctVal": "10",
            "minSz": "1",
            "lotSz": "1",
            "tickSz": "0.00001",
            "ruleType": "xperp",
        }


def _ord_id_from_place(placed: Mapping[str, Any] | None) -> str:
    if not isinstance(placed, dict):
        return ""
    resp = placed.get("response") or {}
    data = resp.get("data") or []
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return str(data[0].get("ordId") or "")
    return str(placed.get("ordId") or "")


__all__ = [
    "LOCKED_SPOT_INST",
    "LOCKED_XPERP_INST",
    "PUBLIC_XPERP_MD_INST",
    "DogeDemoLoop",
    "VenueRoutingError",
    "VenueSpec",
    "far_limit_px",
    "is_public_only_xperp",
    "parse_venue_arg",
    "pick_doge_xperp_inst",
    "pick_doge_xperp_md_inst",
    "scan_signals",
    "signal_to_dict",
    "venues_from_config",
]
