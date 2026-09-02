"""Signed OKX EEA REST client with hard paper / live gates.

HARD RULES
- live: never send trade/order/cancel/amend. Read-only account/config/positions OK.
- demo: always send x-simulated-trading:1. Trade methods require allow_trade=True.
- Trading endpoints are allowed ONLY when mode=demo AND simulated header AND allow_trade.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal, Mapping
from urllib.parse import urlencode

import httpx

from atlas.okx.credentials import OkxCredentials, load_okx_credentials
from atlas.okx.instruments import (
    DEFAULT_UNIVERSE,
    SPOT_BACKUP_BASES,
    SPOT_PRIMARY_BASES,
    assert_spot_inst_id,
    assert_xperp_inst_id,
    filter_xperp,
    resolve_spot_universe,
    resolve_xperp_universe,
)
from atlas.okx.signing import iso8601_ms, sign_okx_v5

log = logging.getLogger("atlas.okx.client")

Mode = Literal["demo", "live"]

EEA_REST_BASE = "https://eea.okx.com"
USER_AGENT = "atlas-trading/0.1 (OKX-EEA; paper-first; +read-or-demo-only)"
SIMULATED_HEADER = "x-simulated-trading"

# Mutating trade paths — blocked in live; demo requires allow_trade.
_TRADE_PATH_MARKERS = (
    "/api/v5/trade/order",
    "/api/v5/trade/cancel-order",
    "/api/v5/trade/amend-order",
    "/api/v5/trade/batch-orders",
    "/api/v5/trade/cancel-batch-orders",
    "/api/v5/trade/amend-batch-orders",
    "/api/v5/trade/close-position",
    "/api/v5/trade/order-algo",
    "/api/v5/trade/cancel-algos",
    "/api/v5/trade/amend-algos",
    "/api/v5/trade/cancel-advance-algos",
    "/api/v5/trade/easy-convert",
    "/api/v5/trade/oneclick-repay",
    "/api/v5/account/set-leverage",
)


class LiveTradingBlocked(RuntimeError):
    """Raised when live mode would send a trading request. Never place live orders."""


class PaperTradeDisabled(RuntimeError):
    """Raised when demo trade is attempted without explicit allow_trade=True."""


def _path_only(path: str) -> str:
    return path.split("?", 1)[0].lower()


def is_trading_endpoint(method: str, path: str) -> bool:
    p = _path_only(path)
    m = method.upper()
    if m in {"POST", "PUT", "PATCH", "DELETE"} and "/api/v5/trade/" in p:
        return True
    if m in {"POST", "PUT", "PATCH", "DELETE"}:
        for marker in _TRADE_PATH_MARKERS:
            if p == marker or p.startswith(marker + "/"):
                return True
    # POST aliases without /trade/ prefix should not exist; still catch order verbs
    if m in {"POST", "PUT", "PATCH", "DELETE"}:
        for frag in ("/order", "/cancel", "/amend"):
            if "/api/v5/trade" in p and frag in p:
                return True
    return False


class OkxEeaClient:
    """EEA REST client. Live is read-only. Paper trades need demo + header + allow_trade."""

    def __init__(
        self,
        mode: Mode,
        allow_trade: bool = False,
        *,
        credentials: OkxCredentials | None = None,
        secrets_path: str | None = None,
        rest_base: str = EEA_REST_BASE,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        http: httpx.Client | None = None,
    ) -> None:
        if mode not in ("demo", "live"):
            raise ValueError(f"mode must be 'demo' or 'live', got {mode!r}")
        if mode == "live" and allow_trade:
            raise LiveTradingBlocked(
                "allow_trade is forbidden in live mode — never place live orders"
            )
        self.mode: Mode = mode
        self.allow_trade = bool(allow_trade) and mode == "demo"
        self.rest_base = rest_base.rstrip("/")
        self.credentials = credentials or load_okx_credentials(mode, secrets_path)
        self._owns_http = http is None
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._http = http or httpx.Client(
            base_url=self.rest_base,
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> "OkxEeaClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _assert_request_allowed(self, method: str, path: str) -> None:
        trading = is_trading_endpoint(method, path)
        if self.mode == "live":
            if trading or method.upper() not in {"GET", "HEAD"}:
                raise LiveTradingBlocked(
                    f"live mode is read-only; refused {method.upper()} {path.split('?', 1)[0]}"
                )
            return
        # demo
        if trading and not self.allow_trade:
            raise PaperTradeDisabled(
                "demo trading endpoints require allow_trade=True "
                "(and x-simulated-trading:1 is always sent in demo mode)"
            )

    def _auth_headers(
        self,
        method: str,
        request_path: str,
        body: str,
        *,
        timestamp: str | None = None,
    ) -> dict[str, str]:
        ts = timestamp or iso8601_ms()
        sign = sign_okx_v5(
            ts, method, request_path, body, self.credentials.api_secret
        )
        headers = {
            "OK-ACCESS-KEY": self.credentials.api_key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": self.credentials.passphrase,
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.mode == "demo":
            headers[SIMULATED_HEADER] = "1"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        signed: bool = True,
    ) -> dict[str, Any]:
        method_u = method.upper()
        path_with_q = path
        if params:
            qs = urlencode({k: v for k, v in params.items() if v is not None})
            if qs:
                path_with_q = f"{path}?{qs}"
        body_str = ""
        if body is not None and method_u not in {"GET", "HEAD"}:
            body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        self._assert_request_allowed(method_u, path_with_q)
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if signed:
            headers = self._auth_headers(method_u, path_with_q, body_str)
        log.info(
            "okx request mode=%s signed=%s simulated=%s method=%s path=%s",
            self.mode,
            signed,
            headers.get(SIMULATED_HEADER) == "1",
            method_u,
            path.split("?", 1)[0],
        )
        url = self.rest_base + path_with_q
        resp = self._http.request(
            method_u,
            url,
            headers=headers,
            content=body_str.encode("utf-8") if body_str else None,
        )
        try:
            payload = resp.json()
        except ValueError:
            payload = {"code": str(resp.status_code), "msg": resp.text[:200], "data": []}
        if not isinstance(payload, dict):
            payload = {"code": str(resp.status_code), "msg": "non-object JSON", "data": payload}
        payload.setdefault("_http_status", resp.status_code)
        return payload

    # --- public (unsigned) ---

    def get_instruments(self, inst_type: str = "FUTURES") -> dict[str, Any]:
        return self._request(
            "GET",
            "/api/v5/public/instruments",
            params={"instType": inst_type},
            signed=False,
        )

    def get_account_instruments(self, inst_type: str = "FUTURES") -> dict[str, Any]:
        """Signed catalogue (demo: x-simulated-trading). Use for order-routable instIds."""
        return self._request(
            "GET",
            "/api/v5/account/instruments",
            params={"instType": inst_type},
            signed=True,
        )

    def resolve_universe(
        self,
        *,
        primary: tuple[str, ...] = ("BTC", "DOGE", "PEPE"),
        backup: tuple[str, ...] = ("SOL",),
    ) -> dict[str, Any]:
        raw = self.get_instruments("FUTURES")
        rows = raw.get("data") or []
        filtered = filter_xperp(rows, bases=primary + backup)
        resolved = resolve_xperp_universe(rows, primary=primary, backup=backup)
        resolved["okx_code"] = raw.get("code")
        resolved["okx_msg"] = raw.get("msg")
        resolved["n_filtered"] = len(filtered)
        resolved["universe"] = list(DEFAULT_UNIVERSE)
        return resolved

    def get_ticker(self, inst_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            "/api/v5/market/ticker",
            params={"instId": inst_id},
            signed=False,
        )

    def resolve_spot_universe(
        self,
        *,
        primary: tuple[str, ...] = SPOT_PRIMARY_BASES,
        backup: tuple[str, ...] = SPOT_BACKUP_BASES,
        quotes: tuple[str, ...] = ("USDT", "USD"),
    ) -> dict[str, Any]:
        raw = self.get_instruments("SPOT")
        rows = raw.get("data") or []
        resolved = resolve_spot_universe(
            rows, primary=primary, backup=backup, quotes=quotes
        )
        resolved["okx_code"] = raw.get("code")
        resolved["okx_msg"] = raw.get("msg")
        resolved["universe"] = list(primary) + list(backup)
        return resolved

    # --- private read-only ---

    def get_balance(self, ccy: str | None = None) -> dict[str, Any]:
        params = {"ccy": ccy} if ccy else None
        return self._request("GET", "/api/v5/account/balance", params=params)

    def get_account_config(self) -> dict[str, Any]:
        return self._request("GET", "/api/v5/account/config")

    def get_positions(
        self,
        inst_type: str | None = "FUTURES",
        inst_id: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {}
        if inst_type:
            params["instType"] = inst_type
        if inst_id:
            params["instId"] = inst_id
        return self._request(
            "GET",
            "/api/v5/account/positions",
            params=params or None,
        )

    def get_order(
        self,
        inst_id: str,
        *,
        ord_id: str | None = None,
        cl_ord_id: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {"instId": inst_id}
        if ord_id:
            params["ordId"] = ord_id
        if cl_ord_id:
            params["clOrdId"] = cl_ord_id
        return self._request("GET", "/api/v5/trade/order", params=params)

    def get_orders_pending(
        self,
        inst_type: str = "SPOT",
        inst_id: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {"instType": inst_type}
        if inst_id:
            params["instId"] = inst_id
        return self._request("GET", "/api/v5/trade/orders-pending", params=params)

    # --- trading (demo + allow_trade only; live always raises) ---

    def place_order(self, **body: Any) -> dict[str, Any]:
        return self._request("POST", "/api/v5/trade/order", body=body)

    def cancel_order(self, **body: Any) -> dict[str, Any]:
        return self._request("POST", "/api/v5/trade/cancel-order", body=body)

    def amend_order(self, **body: Any) -> dict[str, Any]:
        return self._request("POST", "/api/v5/trade/amend-order", body=body)

    def place_spot_market(
        self,
        inst_id: str,
        side: str,
        sz: str,
        *,
        tgt_ccy: str = "base_ccy",
        cl_ord_id: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """SPOT market order. Demo + allow_trade only; always tdMode=cash."""
        inst = assert_spot_inst_id(inst_id)
        extra.pop("tdMode", None)
        extra.pop("td_mode", None)
        extra.pop("ordType", None)
        body: dict[str, Any] = {
            "instId": inst,
            "tdMode": "cash",
            "side": str(side).lower(),
            "ordType": "market",
            "sz": str(sz),
            "tgtCcy": tgt_ccy,
            **extra,
        }
        if cl_ord_id:
            body["clOrdId"] = cl_ord_id
        body["tdMode"] = "cash"
        return self.place_order(**body)

    def place_spot_limit(
        self,
        inst_id: str,
        side: str,
        sz: str,
        px: str,
        *,
        cl_ord_id: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """SPOT limit order. Demo + allow_trade only; always tdMode=cash."""
        inst = assert_spot_inst_id(inst_id)
        extra.pop("tdMode", None)
        extra.pop("td_mode", None)
        extra.pop("ordType", None)
        body: dict[str, Any] = {
            "instId": inst,
            "tdMode": "cash",
            "side": str(side).lower(),
            "ordType": "limit",
            "sz": str(sz),
            "px": str(px),
            **extra,
        }
        if cl_ord_id:
            body["clOrdId"] = cl_ord_id
        body["tdMode"] = "cash"
        return self.place_order(**body)

    def set_leverage(
        self,
        inst_id: str,
        lever: str | float | int,
        *,
        mgn_mode: str = "isolated",
    ) -> dict[str, Any]:
        """Demo-only. Isolated preferred. Caller must cap lever at 2x."""
        inst = assert_xperp_inst_id(inst_id)
        mode = str(mgn_mode or "isolated").lower()
        if mode not in {"isolated", "cross"}:
            raise ValueError(f"mgnMode must be isolated or cross, got {mgn_mode!r}")
        body = {
            "instId": inst,
            "lever": str(lever),
            "mgnMode": mode,
        }
        return self._request("POST", "/api/v5/account/set-leverage", body=body)

    def place_xperp_limit(
        self,
        inst_id: str,
        side: str,
        sz: str,
        px: str,
        *,
        td_mode: str = "isolated",
        cl_ord_id: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """X-Perp FUTURES limit. Demo + allow_trade only; tdMode=isolated preferred; net mode."""
        inst = assert_xperp_inst_id(inst_id)
        extra.pop("tdMode", None)
        extra.pop("td_mode", None)
        extra.pop("ordType", None)
        extra.pop("posSide", None)
        extra.pop("pos_side", None)
        mode = str(td_mode or "isolated").lower()
        if mode not in {"isolated", "cross"}:
            raise ValueError(f"tdMode must be isolated or cross, got {td_mode!r}")
        body: dict[str, Any] = {
            "instId": inst,
            "tdMode": mode,
            "side": str(side).lower(),
            "ordType": "limit",
            "sz": str(sz),
            "px": str(px),
            **extra,
        }
        if cl_ord_id:
            body["clOrdId"] = cl_ord_id
        body["tdMode"] = mode
        return self.place_order(**body)

    def place_xperp_market(
        self,
        inst_id: str,
        side: str,
        sz: str,
        *,
        td_mode: str = "isolated",
        cl_ord_id: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """X-Perp FUTURES market. Demo + allow_trade only; isolated preferred; net mode."""
        inst = assert_xperp_inst_id(inst_id)
        extra.pop("tdMode", None)
        extra.pop("td_mode", None)
        extra.pop("ordType", None)
        extra.pop("posSide", None)
        extra.pop("pos_side", None)
        mode = str(td_mode or "isolated").lower()
        if mode not in {"isolated", "cross"}:
            raise ValueError(f"tdMode must be isolated or cross, got {td_mode!r}")
        body: dict[str, Any] = {
            "instId": inst,
            "tdMode": mode,
            "side": str(side).lower(),
            "ordType": "market",
            "sz": str(sz),
            **extra,
        }
        if cl_ord_id:
            body["clOrdId"] = cl_ord_id
        body["tdMode"] = mode
        return self.place_order(**body)

