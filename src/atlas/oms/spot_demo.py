"""OKX EEA SPOT demo OMS — paper plumbing only.

HARD RULES
- mode=demo only. Live clients raise LiveTradingBlocked at construction.
- Trade path always goes through OkxEeaClient (x-simulated-trading:1 + allow_trade).
- Fail closed if totalEq is 0 (demo funds missing — claim in OKX Demo UI).
- Risk: €200 paper scale, 5% daily kill, 1–2% per trade, one position.
- Never log secrets.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from atlas.common.time import utc_date_str, utc_ms
from atlas.okx.client import LiveTradingBlocked, OkxEeaClient, PaperTradeDisabled
from atlas.okx.instruments import (
    PREFERRED_SPOT_QUOTES,
    SPOT_BACKUP_BASES,
    SPOT_PRIMARY_BASES,
    assert_spot_inst_id,
    assert_xperp_inst_id,
)
from atlas.paper.risk import (
    RISK_FRAC_MAX,
    RISK_FRAC_MIN,
    PaperConfigError,
    size_order as paper_size_order,
)
from atlas.paper.types import Side

log = logging.getLogger("atlas.oms.spot_demo")

PAPER_EQUITY_EUR = 200.0
DAILY_KILL_FRAC = 0.05
PER_TRADE_RISK_FRAC = 0.015  # locked 1–2% band
ONE_POSITION = True
TINY_NOTIONAL_EUR = 2.0
XPERP_LEVERAGE_MAX = 2.0
QUOTE_CCYS = ("USDT", "USD", "USDC", "EUR")
DEMO_FUNDS_HINT = (
    "demo funds missing: totalEq=0. Claim demo funds in the OKX Demo Trading UI "
    "(Trade → Demo Trading), then re-run the snapshot."
)
_SECRET_KEYS = (
    "api_key",
    "api_secret",
    "passphrase",
    "secret",
    "ok-access-key",
    "ok-access-sign",
    "ok-access-timestamp",
    "ok-access-passphrase",
    "private_key",
    "token",
)
_ACCT_LV = {
    "1": "simple",
    "2": "single_currency_margin",
    "3": "multi_currency_margin",
    "4": "portfolio_margin",
}


class DemoFundsMissing(RuntimeError):
    """Raised when demo totalEq is 0 / missing. Caller must claim demo funds."""


class OmsRiskBlocked(RuntimeError):
    """Raised when risk gates refuse an order (kill, one-position, size)."""


def parse_eq(value: object) -> float:
    """Parse OKX equity/size strings. Empty/None → 0. Unparseable → 0 (fail closed)."""
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _dec(value: object, default: str = "0") -> Decimal:
    s = str(value if value is not None else default).strip() or default
    try:
        return Decimal(s)
    except Exception:  # noqa: BLE001
        return Decimal(default)


def fmt_dec(value: Decimal) -> str:
    s = format(value, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        return value
    n = (value / step).to_integral_value(rounding=ROUND_DOWN)
    return n * step


def round_px(value: Decimal, tick: Decimal, *, side: str) -> Decimal:
    """Buy limits round down (further from fill); sell limits round up."""
    if tick <= 0:
        return value
    n = value / tick
    if str(side).lower() == "buy":
        q = n.to_integral_value(rounding=ROUND_DOWN)
    else:
        q = n.to_integral_value(rounding=ROUND_HALF_UP)
        # sell further from fill = round up
        if q * tick < value:
            q += 1
    return q * tick


def okx_ack_ok(payload: Mapping[str, Any] | None) -> bool:
    """True when OKX envelope code=0 and row sCode is 0/empty."""
    if not isinstance(payload, Mapping):
        return False
    if str(payload.get("code")) != "0":
        return False
    data = payload.get("data") or []
    if isinstance(data, list) and data and isinstance(data[0], dict):
        sc = str(data[0].get("sCode") or "")
        return sc in {"0", ""}
    return True


def cap_xperp_leverage(leverage: float, hard_cap: float = XPERP_LEVERAGE_MAX) -> float:
    cap = min(float(hard_cap), float(XPERP_LEVERAGE_MAX))
    lev = float(leverage)
    if lev <= 0:
        raise PaperConfigError(f"leverage must be positive, got {leverage}")
    return min(lev, cap)


def risk_equity(total_eq: float, paper_scale: float = PAPER_EQUITY_EUR) -> float:
    if total_eq <= 0 or paper_scale <= 0:
        return 0.0
    return min(float(total_eq), float(paper_scale))


def validate_per_trade_risk_frac(per_trade_risk_frac: float) -> None:
    if not (RISK_FRAC_MIN - 1e-12 <= per_trade_risk_frac <= RISK_FRAC_MAX + 1e-12):
        raise PaperConfigError(
            f"per_trade_risk_frac must be in [{RISK_FRAC_MIN}, {RISK_FRAC_MAX}]; "
            f"got {per_trade_risk_frac}"
        )


def daily_kill_decision(
    *,
    day_start_total_eq: float,
    current_total_eq: float,
    paper_scale: float = PAPER_EQUITY_EUR,
    daily_kill_frac: float = DAILY_KILL_FRAC,
) -> dict[str, Any]:
    """5% of the €200 paper scale (or of smaller totalEq) as an absolute daily loss."""
    start_risk = risk_equity(day_start_total_eq, paper_scale)
    if start_risk <= 0:
        return {
            "killed": True,
            "reason": "non_positive_day_start",
            "loss": 0.0,
            "threshold": 0.0,
            "start_risk": start_risk,
        }
    threshold = start_risk * daily_kill_frac
    loss = day_start_total_eq - current_total_eq
    killed = loss + 1e-12 >= threshold
    return {
        "killed": killed,
        "reason": "daily_loss" if killed else "ok",
        "loss": loss,
        "threshold": threshold,
        "start_risk": start_risk,
    }


def redact_record(obj: Any) -> Any:
    """Drop secret-like keys from nested dicts/lists before journal/print."""
    if isinstance(obj, Mapping):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if str(k).lower() in _SECRET_KEYS or str(k).lower().startswith("ok-access"):
                out[str(k)] = "***"
            else:
                out[str(k)] = redact_record(v)
        return out
    if isinstance(obj, list):
        return [redact_record(x) for x in obj]
    return obj


def non_zero_ccys(details: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in details:
        eq = parse_eq(row.get("eq"))
        cash = parse_eq(row.get("cashBal"))
        avail = parse_eq(row.get("availBal"))
        frozen = parse_eq(row.get("frozenBal"))
        if abs(eq) > 0 or abs(cash) > 0 or abs(avail) > 0 or abs(frozen) > 0:
            out.append(
                {
                    "ccy": str(row.get("ccy") or ""),
                    "eq": str(row.get("eq") or "0"),
                    "cashBal": str(row.get("cashBal") or "0"),
                    "availBal": str(row.get("availBal") or "0"),
                    "frozenBal": str(row.get("frozenBal") or "0"),
                }
            )
    return out


def universe_base_positions(
    details: Sequence[Mapping[str, Any]],
    *,
    bases: Iterable[str] = SPOT_PRIMARY_BASES + SPOT_BACKUP_BASES,
    dust: float = 1e-12,
) -> list[dict[str, Any]]:
    wanted = {b.upper() for b in bases}
    held: list[dict[str, Any]] = []
    for row in details:
        ccy = str(row.get("ccy") or "").upper()
        if ccy not in wanted:
            continue
        eq = parse_eq(row.get("eq"))
        cash = parse_eq(row.get("cashBal"))
        avail = parse_eq(row.get("availBal"))
        qty = max(eq, cash, avail)
        if qty > dust:
            held.append({"ccy": ccy, "eq": eq, "cashBal": cash, "availBal": avail})
    return held


def quote_avail(
    details: Sequence[Mapping[str, Any]],
    quote: str,
) -> float:
    q = quote.upper()
    for row in details:
        if str(row.get("ccy") or "").upper() == q:
            for key in ("availBal", "cashBal", "eq"):
                v = parse_eq(row.get(key))
                if v > 0:
                    return v
            return 0.0
    return 0.0


@dataclass(frozen=True)
class SizePlan:
    allowed: bool
    reason: str
    inst_id: str = ""
    side: str = "buy"
    ord_type: str = "limit"
    px: str | None = None
    sz: str = "0"
    notional: float = 0.0
    risk_equity: float = 0.0
    risk_budget: float = 0.0
    min_notional: float = 0.0
    last_px: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return redact_record(d)


def size_spot_buy(
    *,
    total_eq: float,
    last_px: float,
    min_sz: float,
    lot_sz: float,
    available_quote: float,
    paper_scale: float = PAPER_EQUITY_EUR,
    per_trade_risk_frac: float = PER_TRADE_RISK_FRAC,
    tiny_notional: float | None = TINY_NOTIONAL_EUR,
    inst_id: str = "",
) -> SizePlan:
    """Size a tiny spot BUY within 1–2% of the €200 paper book."""
    try:
        validate_per_trade_risk_frac(per_trade_risk_frac)
    except PaperConfigError as exc:
        return SizePlan(allowed=False, reason=str(exc), inst_id=inst_id)
    if total_eq <= 0:
        return SizePlan(
            allowed=False,
            reason="demo_funds_missing",
            inst_id=inst_id,
            extra={"hint": DEMO_FUNDS_HINT},
        )
    if last_px <= 0 or min_sz <= 0:
        return SizePlan(allowed=False, reason="invalid_px_or_min_sz", inst_id=inst_id)
    req = risk_equity(total_eq, paper_scale)
    if req <= 0:
        return SizePlan(allowed=False, reason="non_positive_equity", inst_id=inst_id)
    risk_budget = req * per_trade_risk_frac
    hard_cap = risk_budget
    target = hard_cap if tiny_notional is None else min(hard_cap, float(tiny_notional))
    min_notional = min_sz * last_px
    if min_notional > hard_cap + 1e-12:
        return SizePlan(
            allowed=False,
            reason="min_sz_exceeds_risk",
            inst_id=inst_id,
            risk_equity=req,
            risk_budget=risk_budget,
            min_notional=min_notional,
            last_px=last_px,
        )
    if min_notional > target:
        target = min_notional
    if available_quote + 1e-12 < min_notional:
        return SizePlan(
            allowed=False,
            reason="insufficient_quote",
            inst_id=inst_id,
            risk_equity=req,
            risk_budget=risk_budget,
            min_notional=min_notional,
            last_px=last_px,
            extra={"available_quote": available_quote},
        )
    notional = min(target, available_quote, req)
    raw_sz = Decimal(str(notional / last_px))
    step = _dec(lot_sz) if lot_sz > 0 else Decimal("1")
    sz = floor_to_step(raw_sz, step)
    min_sz_d = _dec(min_sz)
    if sz < min_sz_d:
        sz = min_sz_d
        notional = float(sz) * last_px
        if notional > hard_cap + 1e-9:
            return SizePlan(
                allowed=False,
                reason="rounded_min_sz_exceeds_risk",
                inst_id=inst_id,
                risk_equity=req,
                risk_budget=risk_budget,
                min_notional=min_notional,
                last_px=last_px,
            )
    if sz <= 0:
        return SizePlan(allowed=False, reason="zero_qty", inst_id=inst_id)
    notional = float(sz) * last_px
    return SizePlan(
        allowed=True,
        reason="sized",
        inst_id=inst_id,
        side="buy",
        sz=fmt_dec(sz),
        notional=notional,
        risk_equity=req,
        risk_budget=risk_budget,
        min_notional=min_notional,
        last_px=last_px,
    )


def size_xperp(
    *,
    last_px: float,
    ct_val: float,
    min_sz: float,
    lot_sz: float,
    paper_scale: float = PAPER_EQUITY_EUR,
    per_trade_risk_frac: float = PER_TRADE_RISK_FRAC,
    tiny_notional: float | None = TINY_NOTIONAL_EUR,
    leverage: float = XPERP_LEVERAGE_MAX,
    stop: float | None = None,
    side: str = "buy",
    inst_id: str = "",
) -> SizePlan:
    """Size an X-Perp order in contracts, 1–2% of the €200 book, leverage ≤2x."""
    try:
        validate_per_trade_risk_frac(per_trade_risk_frac)
        lev = cap_xperp_leverage(leverage)
    except PaperConfigError as exc:
        return SizePlan(allowed=False, reason=str(exc), inst_id=inst_id, side=side)
    if last_px <= 0 or ct_val <= 0 or min_sz <= 0:
        return SizePlan(allowed=False, reason="invalid_px_or_contract", inst_id=inst_id, side=side)
    req = float(paper_scale)
    if req <= 0:
        return SizePlan(allowed=False, reason="non_positive_equity", inst_id=inst_id, side=side)
    risk_budget = req * per_trade_risk_frac
    contract_notional = ct_val * last_px
    min_notional = min_sz * contract_notional
    target = risk_budget
    if tiny_notional is not None:
        target = min(target, float(tiny_notional))
    if stop is not None and stop > 0:
        side_e = Side.LONG if str(side).lower() == "buy" else Side.SHORT
        decision = paper_size_order(
            equity=req,
            entry=last_px,
            stop=float(stop),
            side=side_e,
            per_trade_risk_frac=per_trade_risk_frac,
            leverage_default=lev,
            leverage_hard_cap=XPERP_LEVERAGE_MAX,
        )
        if not decision.allowed:
            return SizePlan(
                allowed=False,
                reason=decision.reason,
                inst_id=inst_id,
                side=side,
                risk_equity=req,
                risk_budget=risk_budget,
                last_px=last_px,
            )
        target = min(target, decision.notional)
    # Prefer the tiny/risk-budget notional; never exceed leverage * paper equity.
    notional_cap = min(max(target, 0.0), lev * req)
    if min_notional > notional_cap + 1e-9 and min_notional > risk_budget + 1e-9:
        # allow min contract if it still fits leverage * paper and is near tiny
        if min_notional > lev * req + 1e-9:
            return SizePlan(
                allowed=False,
                reason="min_sz_exceeds_risk",
                inst_id=inst_id,
                side=side,
                risk_equity=req,
                risk_budget=risk_budget,
                min_notional=min_notional,
                last_px=last_px,
            )
    use_notional = max(target, min_notional) if min_notional <= lev * req + 1e-9 else target
    use_notional = min(use_notional, lev * req)
    raw_sz = Decimal(str(use_notional / contract_notional))
    step = _dec(lot_sz) if lot_sz > 0 else Decimal("1")
    sz = floor_to_step(raw_sz, step)
    min_sz_d = _dec(min_sz)
    if sz < min_sz_d:
        sz = min_sz_d
    if sz <= 0:
        return SizePlan(allowed=False, reason="zero_qty", inst_id=inst_id, side=side)
    notional = float(sz) * contract_notional
    if notional > lev * req + 1e-6:
        return SizePlan(
            allowed=False,
            reason="rounded_min_sz_exceeds_leverage",
            inst_id=inst_id,
            side=side,
            risk_equity=req,
            risk_budget=risk_budget,
            min_notional=min_notional,
            last_px=last_px,
        )
    return SizePlan(
        allowed=True,
        reason="sized",
        inst_id=inst_id,
        side=side,
        sz=fmt_dec(sz),
        notional=notional,
        risk_equity=req,
        risk_budget=risk_budget,
        min_notional=min_notional,
        last_px=last_px,
        extra={
            "ctVal": ct_val,
            "contract_notional": contract_notional,
            "leverage": lev,
            "tdMode": "isolated",
        },
    )


class OmsJournal:
    """Append-only JSONL under data/oms/{UTC-date}/. Never writes secrets."""

    def __init__(self, data_dir: str | Path, run_id: str) -> None:
        self.data_dir = Path(data_dir)
        self.run_id = run_id
        self._lock = threading.Lock()
        self._seq = 0
        self.root = self.data_dir / "oms"

    def _path(self, channel: str, ts_ms: int) -> Path:
        directory = self.root / utc_date_str(ts_ms)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{channel}.jsonl"

    def append(self, channel: str, record: dict[str, Any], *, ts_ms: int | None = None) -> Path:
        ts = int(ts_ms if ts_ms is not None else record.get("ts_ms") or utc_ms())
        with self._lock:
            self._seq += 1
            seq = self._seq
        row = redact_record(
            {"run_id": self.run_id, "seq": seq, **record, "ts_ms": ts}
        )
        path = self._path(channel, ts)
        line = json.dumps(row, separators=(",", ":"), ensure_ascii=False, default=str)
        with self._lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return path


@dataclass
class AccountSnapshot:
    total_eq: float
    total_eq_raw: str
    acct_lv: str
    acct_lv_name: str
    pos_mode: str
    non_zero: list[dict[str, Any]]
    details: list[dict[str, Any]]
    code: str
    msg: str
    http_status: object = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def funds_ok(self) -> bool:
        return self.code == "0" and self.total_eq > 0

    def public_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "msg": self.msg,
            "totalEq": self.total_eq_raw,
            "totalEq_num": self.total_eq,
            "demo_funds_ok": self.funds_ok,
            "account_mode": {
                "acctLv": self.acct_lv,
                "acctLv_name": self.acct_lv_name,
                "posMode": self.pos_mode,
            },
            "non_zero_ccys": self.non_zero,
            "http_status": self.http_status,
        }


class SpotDemoOms:
    """High-level demo SPOT OMS: refresh, kill, size, place/cancel, journal."""

    def __init__(
        self,
        client: OkxEeaClient,
        *,
        data_dir: str | Path = "data",
        run_id: str = "oms-spot-demo",
        paper_equity_eur: float = PAPER_EQUITY_EUR,
        daily_kill_frac: float = DAILY_KILL_FRAC,
        per_trade_risk_frac: float = PER_TRADE_RISK_FRAC,
        one_position: bool = ONE_POSITION,
        tiny_notional_eur: float = TINY_NOTIONAL_EUR,
        primary: Sequence[str] = SPOT_PRIMARY_BASES,
        backup: Sequence[str] = SPOT_BACKUP_BASES,
        quotes: Sequence[str] = PREFERRED_SPOT_QUOTES,
    ) -> None:
        if client.mode != "demo":
            raise LiveTradingBlocked(
                "SpotDemoOms is demo-only; live remains order-blocked"
            )
        validate_per_trade_risk_frac(per_trade_risk_frac)
        self.client = client
        self.paper_equity_eur = float(paper_equity_eur)
        self.daily_kill_frac = float(daily_kill_frac)
        self.per_trade_risk_frac = float(per_trade_risk_frac)
        self.one_position = bool(one_position)
        self.tiny_notional_eur = float(tiny_notional_eur)
        self.primary = tuple(primary)
        self.backup = tuple(backup)
        self.quotes = tuple(quotes)
        self.journal = OmsJournal(data_dir, run_id)
        self.state_path = Path(data_dir) / "oms" / "state.json"
        self._state: dict[str, Any] = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        if self.state_path.is_file():
            try:
                raw = json.loads(self.state_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    return raw
            except (OSError, json.JSONDecodeError):
                log.warning("oms state unreadable; starting fresh (path only, no secrets)")
        return {
            "utc_day": None,
            "day_start_total_eq": None,
            "paper_day_start": None,
            "paper_pnl": 0.0,
            "killed": False,
            "kill_reason": None,
            "open_inst": None,
            "open_side": None,
            "open_ord_id": None,
            "open_venue": None,
        }

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = redact_record(dict(self._state))
        self.state_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _rollover(self, total_eq: float, ts_ms: int) -> None:
        day = utc_date_str(ts_ms)
        if self._state.get("utc_day") != day:
            self._state["utc_day"] = day
            self._state["day_start_total_eq"] = total_eq
            self._state["paper_day_start"] = risk_equity(total_eq, self.paper_equity_eur)
            self._state["paper_pnl"] = 0.0
            self._state["killed"] = False
            self._state["kill_reason"] = None
            self._save_state()

    def refresh_account(self, *, fail_closed_zero: bool = True) -> AccountSnapshot:
        bal = self.client.get_balance()
        cfg = self.client.get_account_config()
        data = bal.get("data") or []
        top = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
        details = top.get("details") or []
        if not isinstance(details, list):
            details = []
        total_raw = top.get("totalEq")
        total_eq = parse_eq(total_raw)
        cfg_rows = cfg.get("data") or []
        cfg0 = (
            cfg_rows[0]
            if isinstance(cfg_rows, list) and cfg_rows and isinstance(cfg_rows[0], dict)
            else {}
        )
        acct_lv = str(cfg0.get("acctLv") or "")
        snap = AccountSnapshot(
            total_eq=total_eq,
            total_eq_raw="" if total_raw is None else str(total_raw),
            acct_lv=acct_lv,
            acct_lv_name=_ACCT_LV.get(acct_lv, acct_lv or "unknown"),
            pos_mode=str(cfg0.get("posMode") or ""),
            non_zero=non_zero_ccys(details),
            details=[dict(x) for x in details if isinstance(x, dict)],
            code=str(bal.get("code", "")),
            msg=str(bal.get("msg") or ""),
            http_status=bal.get("_http_status"),
            extra={"config_code": str(cfg.get("code", ""))},
        )
        ts = utc_ms()
        self._rollover(total_eq, ts)
        self.journal.append(
            "snapshots",
            {"kind": "account", "mode": "demo", **snap.public_dict()},
            ts_ms=ts,
        )
        if fail_closed_zero and (snap.code != "0" or total_eq <= 0):
            raise DemoFundsMissing(DEMO_FUNDS_HINT)
        return snap

    def check_kill(self, snap: AccountSnapshot) -> dict[str, Any]:
        # Kill is on the €200 paper book + OMS P&L, not faucet-wallet MTM.
        start = parse_eq(self._state.get("paper_day_start"))
        if start <= 0:
            start = risk_equity(snap.total_eq, self.paper_equity_eur)
            self._state["paper_day_start"] = start
            self._state["paper_pnl"] = parse_eq(self._state.get("paper_pnl"))
        pnl = parse_eq(self._state.get("paper_pnl"))
        current_paper = start + pnl
        decision = daily_kill_decision(
            day_start_total_eq=start,
            current_total_eq=current_paper,
            paper_scale=self.paper_equity_eur,
            daily_kill_frac=self.daily_kill_frac,
        )
        decision["paper_eq"] = current_paper
        decision["paper_pnl"] = pnl
        if decision["killed"]:
            self._state["killed"] = True
            self._state["kill_reason"] = decision["reason"]
            self._save_state()
        elif self._state.get("killed") and self._state.get("kill_reason") == "daily_loss":
            decision = {
                **decision,
                "killed": True,
                "reason": self._state.get("kill_reason") or "daily_kill",
            }
        self.journal.append("events", {"kind": "kill_check", **decision})
        return decision

    def _clear_open_inst(self, reason: str) -> None:
        prev = self._state.get("open_inst")
        prev_ord = self._state.get("open_ord_id")
        if prev is None and not prev_ord:
            return
        self._state["open_inst"] = None
        self._state["open_side"] = None
        self._state["open_ord_id"] = None
        self._state["open_order_id"] = None
        self._state["open_venue"] = None
        if "positions" in self._state:
            self._state["positions"] = {}
        self._save_state()
        self.journal.append(
            "events",
            {
                "kind": "open_inst_cleared",
                "reason": reason,
                "prev_open_inst": prev,
                "prev_open_ord_id": prev_ord,
            },
        )

    def _pending_in_universe(
        self,
        inst_ids: set[str],
        inst_types: Sequence[str] = ("SPOT", "FUTURES"),
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for inst_type in inst_types:
            raw = self.client.get_orders_pending(inst_type=str(inst_type))
            rows = raw.get("data") or []
            for row in rows if isinstance(rows, list) else []:
                if not isinstance(row, dict):
                    continue
                inst = str(row.get("instId") or "")
                if inst_ids and inst not in inst_ids:
                    continue
                ord_id = str(row.get("ordId") or "")
                key = (inst, ord_id)
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    {
                        "instId": inst,
                        "ordId": ord_id,
                        "state": str(row.get("state") or ""),
                        "side": str(row.get("side") or ""),
                        "sz": str(row.get("sz") or ""),
                        "instType": str(inst_type),
                    }
                )
        return out

    def _nonzero_positions(self, inst_ids: set[str]) -> list[dict[str, Any]]:
        """X-Perp (FUTURES) positions with non-zero pos. Spot cash is not listed here."""
        try:
            raw = self.client.get_positions(inst_type="FUTURES")
        except Exception:  # noqa: BLE001
            return []
        if str(raw.get("code")) != "0":
            return []
        rows = raw.get("data") or []
        out: list[dict[str, Any]] = []
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            inst = str(row.get("instId") or "")
            if inst_ids and inst not in inst_ids:
                continue
            pos = parse_eq(row.get("pos"))
            if abs(pos) <= 1e-12:
                continue
            out.append({"instId": inst, "pos": pos, "posSide": str(row.get("posSide") or "")})
        return out

    def reconcile_open_inst(
        self,
        inst_ids: set[str] | None = None,
        inst_types: Sequence[str] = ("SPOT", "FUTURES"),
    ) -> dict[str, Any]:
        """Clear sticky open_inst after cancel / pending-empty / filled-flat.

        Keep open_inst only while a universe pending order exists or a
        non-zero FUTURES position remains (one directional position).
        """
        ids = inst_ids or set()
        pending = self._pending_in_universe(ids, inst_types)
        if pending:
            inst = str(pending[0].get("instId") or "") or self._state.get("open_inst")
            if inst and self._state.get("open_inst") != inst:
                self._state["open_inst"] = inst
                self._state["open_ord_id"] = pending[0].get("ordId")
                self._save_state()
            return {"cleared": False, "reason": "pending", "pending": pending}
        held = self._nonzero_positions(ids)
        if held:
            inst = str(held[0].get("instId") or "")
            if inst:
                self._state["open_inst"] = inst
                self._save_state()
            return {"cleared": False, "reason": "open_position", "held": held}
        had = self._state.get("open_inst") or self._state.get("open_ord_id")
        if had:
            self._clear_open_inst("pending_empty")
            return {"cleared": True, "reason": "pending_empty", "pending": []}
        return {"cleared": False, "reason": "already_flat", "pending": []}

    def clear_stale_open_state(self, inst_ids: set[str] | None = None) -> dict[str, Any]:
        """Drop leftover open_inst (foreign symbol / empty pending) before a new session."""
        ids = inst_ids or set()
        if self._state.get("open_ord_id") is None and self._state.get("open_order_id"):
            self._state["open_ord_id"] = self._state.get("open_order_id")
        open_inst = self._state.get("open_inst")
        if open_inst and ids and open_inst not in ids:
            self._clear_open_inst("stale_foreign_inst")
        return self.reconcile_open_inst(ids)

    def gate_new_entry(
        self,
        snap: AccountSnapshot,
        *,
        inst_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        if snap.total_eq <= 0:
            return {"allowed": False, "reason": "demo_funds_missing", "hint": DEMO_FUNDS_HINT}
        kill = self.check_kill(snap)
        if kill.get("killed") or self._state.get("killed"):
            return {"allowed": False, "reason": "daily_kill", "kill": kill}
        if not self.one_position:
            return {"allowed": True, "reason": "ok"}
        held = universe_base_positions(snap.details)
        recon = self.reconcile_open_inst(inst_ids or set())
        pending = list(recon.get("pending") or [])
        if pending:
            return {
                "allowed": False,
                "reason": "one_position_pending",
                "pending": pending,
                "held": held,
                "open_inst": self._state.get("open_inst"),
            }
        open_inst = self._state.get("open_inst")
        if open_inst:
            return {
                "allowed": False,
                "reason": "one_position",
                "open_inst": open_inst,
                "held": held,
                "recon": recon,
            }
        # Faucet / leftover wallet inventory is reported, not a hard gate.
        # One-position applies to OMS-tracked open_inst, pending, and FUTURES pos.
        return {"allowed": True, "reason": "ok", "held": held, "recon": recon}

    def resolve_symbol(self, symbol: str | None = None) -> dict[str, Any]:
        resolved = self.client.resolve_spot_universe(
            primary=self.primary, backup=self.backup, quotes=self.quotes
        )
        rows = {str(r.get("instId")): r for r in resolved.get("resolved") or []}
        by_base = {str(r.get("base")).upper(): r for r in resolved.get("resolved") or []}
        if symbol:
            inst = assert_spot_inst_id(symbol)
            row = rows.get(inst)
            if row is None:
                # allow explicit instId even if not in resolved, but still SPOT shape
                raw = self.client.get_instruments("SPOT")
                for cand in raw.get("data") or []:
                    if str(cand.get("instId") or "").upper() == inst:
                        b, q = inst.split("-")
                        row = {
                            "instId": inst,
                            "base": str(cand.get("baseCcy") or b),
                            "quote": str(cand.get("quoteCcy") or q),
                            "minSz": cand.get("minSz"),
                            "lotSz": cand.get("lotSz"),
                            "tickSz": cand.get("tickSz"),
                            "state": cand.get("state"),
                        }
                        break
            if row is None:
                raise OmsRiskBlocked(f"symbol {inst} not in EEA SPOT catalogue")
            return row
        for base in list(self.primary) + list(self.backup):
            if base.upper() in by_base:
                return by_base[base.upper()]
        raise OmsRiskBlocked("no SPOT universe instrument resolved")

    def choose_inst(self, snap: AccountSnapshot | str | None = None, symbol: str | None = None) -> dict[str, Any]:
        if isinstance(snap, str):
            symbol, snap = snap, None
        if symbol:
            return self.resolve_symbol(symbol)
        if snap is None:
            return self.resolve_symbol(None)
        resolved = self.client.resolve_spot_universe(
            primary=self.primary, backup=self.backup, quotes=self.quotes
        )
        rows = list(resolved.get("resolved") or [])
        for base in list(self.primary) + list(self.backup):
            matches = [r for r in rows if str(r.get("base") or "").upper() == str(base).upper()]
            funded = []
            for r in matches:
                qccy = str(r.get("quote") or r.get("quoteCcy") or "")
                if quote_avail(snap.details, qccy) > 0:
                    funded.append(r)
            if funded:
                return funded[0]
            if matches:
                return matches[0]
        return self.resolve_symbol(None)

    def last_price(self, inst_id: str) -> float:
        raw = self.client.get_ticker(inst_id)
        rows = raw.get("data") or []
        if not rows or not isinstance(rows[0], dict):
            raise OmsRiskBlocked(f"no ticker for {inst_id}")
        last = parse_eq(rows[0].get("last"))
        if last <= 0:
            raise OmsRiskBlocked(f"non-positive last px for {inst_id}")
        return last

    def size_order(
        self,
        snap: AccountSnapshot,
        inst: Mapping[str, Any],
        *,
        last_px: float,
        tiny: bool = True,
        px: float | None = None,
        side: str = "buy",
        ord_type: str = "limit",
    ) -> SizePlan:
        quote = str(inst.get("quote") or inst.get("quoteCcy") or "USDT")
        avail = quote_avail(snap.details, quote)
        plan = size_spot_buy(
            total_eq=snap.total_eq,
            last_px=last_px,
            min_sz=parse_eq(inst.get("minSz")) or 0.0,
            lot_sz=parse_eq(inst.get("lotSz")) or 0.0,
            available_quote=avail,
            paper_scale=self.paper_equity_eur,
            per_trade_risk_frac=self.per_trade_risk_frac,
            tiny_notional=self.tiny_notional_eur if tiny else None,
            inst_id=str(inst.get("instId") or ""),
        )
        extra = dict(plan.extra)
        extra["available_quote"] = avail
        extra["quote"] = quote
        limit_px = None
        if ord_type == "limit" and last_px > 0:
            raw_px = Decimal(str(px if px is not None else last_px))
            tick = _dec(inst.get("tickSz") or "0.00000001")
            limit_px = fmt_dec(round_px(raw_px, tick, side=side))
        plan = SizePlan(
            allowed=plan.allowed,
            reason=plan.reason,
            inst_id=plan.inst_id,
            side=side,
            ord_type=ord_type,
            px=limit_px,
            sz=plan.sz,
            notional=plan.notional,
            risk_equity=plan.risk_equity,
            risk_budget=plan.risk_budget,
            min_notional=plan.min_notional,
            last_px=last_px,
            extra=extra,
        )
        self.journal.append("decisions", {"kind": "size", **plan.as_dict()})
        return plan

    def place(
        self,
        plan: SizePlan,
        *,
        dry_run: bool = True,
        cl_ord_id: str | None = None,
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "kind": "place",
            "dry_run": dry_run,
            "plan": plan.as_dict(),
            "allow_trade": bool(self.client.allow_trade),
            "mode": self.client.mode,
        }
        if not plan.allowed:
            record["skipped"] = True
            record["reason"] = plan.reason
            self.journal.append("orders", record)
            raise OmsRiskBlocked(plan.reason)
        if dry_run:
            record["placed"] = False
            record["reason"] = "dry_run"
            self.journal.append("orders", record)
            return record
        if self.client.mode != "demo":
            raise LiveTradingBlocked("spot place refused: live is order-blocked")
        if not self.client.allow_trade:
            raise PaperTradeDisabled(
                "spot place requires demo client with allow_trade=True"
            )
        if plan.ord_type == "market":
            payload = self.client.place_spot_market(
                plan.inst_id, plan.side, plan.sz, cl_ord_id=cl_ord_id
            )
        else:
            if not plan.px:
                raise OmsRiskBlocked("limit order missing px")
            payload = self.client.place_spot_limit(
                plan.inst_id, plan.side, plan.sz, plan.px, cl_ord_id=cl_ord_id
            )
        record["placed"] = True
        record["response"] = redact_record(
            {k: payload.get(k) for k in ("code", "msg", "data") if k in payload}
        )
        record["http_status"] = payload.get("_http_status")
        data = payload.get("data") or []
        s_code = None
        if isinstance(data, list) and data and isinstance(data[0], dict):
            s_code = str(data[0].get("sCode") or "")
        if str(payload.get("code")) == "0" and s_code in {"0", ""}:
            self._state["open_inst"] = plan.inst_id
            self._state["open_side"] = plan.side
            self._state["open_venue"] = "spot"
            ord_id = ""
            if isinstance(data, list) and data and isinstance(data[0], dict):
                ord_id = str(data[0].get("ordId") or "")
            self._state["open_ord_id"] = ord_id or None
            self._save_state()
        self.journal.append("orders", record)
        return record

    def cancel(self, inst_id: str, ord_id: str) -> dict[str, Any]:
        if self.client.mode != "demo":
            raise LiveTradingBlocked("spot cancel refused: live is order-blocked")
        # Accept SPOT BASE-QUOTE or X-Perp instIds (cancel is venue-agnostic).
        inst = str(inst_id).strip()
        try:
            inst = assert_spot_inst_id(inst)
        except ValueError:
            inst = assert_xperp_inst_id(inst)
        payload = self.client.cancel_order(instId=inst, ordId=str(ord_id))
        record = {
            "kind": "cancel",
            "instId": inst,
            "ordId": ord_id,
            "response": redact_record(
                {k: payload.get(k) for k in ("code", "msg", "data") if k in payload}
            ),
        }
        if okx_ack_ok(payload):
            tracked = self._state.get("open_inst")
            tracked_ord = self._state.get("open_ord_id")
            if tracked in (None, inst) or tracked_ord in (None, str(ord_id)):
                self._clear_open_inst("cancelled")
            record["open_inst_cleared"] = True
        else:
            record["open_inst_cleared"] = False
        self.journal.append("orders", record)
        return record

    def get_order(self, inst_id: str, ord_id: str) -> dict[str, Any]:
        return self.client.get_order(inst_id, ord_id=ord_id)

    def set_xperp_leverage(
        self,
        inst_id: str,
        leverage: float = XPERP_LEVERAGE_MAX,
        *,
        mgn_mode: str = "isolated",
    ) -> dict[str, Any]:
        if self.client.mode != "demo":
            raise LiveTradingBlocked("set-leverage refused: live is order-blocked")
        lev = cap_xperp_leverage(leverage)
        mode = str(mgn_mode or "isolated").lower()
        if mode != "isolated":
            # Isolated preferred; still allow explicit cross only if ≤2x.
            mode = "isolated" if mode not in {"isolated", "cross"} else mode
        payload = self.client.set_leverage(inst_id, fmt_dec(_dec(lev)), mgn_mode=mode)
        record = {
            "kind": "set_leverage",
            "instId": inst_id,
            "lever": lev,
            "mgnMode": mode,
            "response": redact_record(
                {k: payload.get(k) for k in ("code", "msg", "data") if k in payload}
            ),
        }
        self.journal.append("orders", record)
        if not okx_ack_ok(payload):
            raise OmsRiskBlocked(
                f"set-leverage failed code={payload.get('code')} msg={payload.get('msg')}"
            )
        return record

    def size_xperp_order(
        self,
        inst: Mapping[str, Any],
        *,
        last_px: float,
        side: str = "buy",
        stop: float | None = None,
        tiny: bool = True,
        px: float | None = None,
        ord_type: str = "limit",
        leverage: float = XPERP_LEVERAGE_MAX,
    ) -> SizePlan:
        plan = size_xperp(
            last_px=last_px,
            ct_val=parse_eq(inst.get("ctVal")) or 0.0,
            min_sz=parse_eq(inst.get("minSz")) or 0.0,
            lot_sz=parse_eq(inst.get("lotSz")) or 1.0,
            paper_scale=self.paper_equity_eur,
            per_trade_risk_frac=self.per_trade_risk_frac,
            tiny_notional=self.tiny_notional_eur if tiny else None,
            leverage=leverage,
            stop=stop,
            side=side,
            inst_id=str(inst.get("instId") or ""),
        )
        extra = dict(plan.extra)
        extra["tdMode"] = "isolated"
        extra["posMode"] = "net"
        limit_px = None
        if ord_type == "limit" and last_px > 0:
            raw_px = Decimal(str(px if px is not None else last_px))
            tick = _dec(inst.get("tickSz") or "0.00000001")
            limit_px = fmt_dec(round_px(raw_px, tick, side=side))
        plan = SizePlan(
            allowed=plan.allowed,
            reason=plan.reason,
            inst_id=plan.inst_id,
            side=side,
            ord_type=ord_type,
            px=limit_px,
            sz=plan.sz,
            notional=plan.notional,
            risk_equity=plan.risk_equity,
            risk_budget=plan.risk_budget,
            min_notional=plan.min_notional,
            last_px=last_px,
            extra=extra,
        )
        self.journal.append("decisions", {"kind": "size_xperp", **plan.as_dict()})
        return plan

    def place_xperp(
        self,
        plan: SizePlan,
        *,
        dry_run: bool = True,
        cl_ord_id: str | None = None,
        td_mode: str = "isolated",
        leverage: float = XPERP_LEVERAGE_MAX,
        set_leverage: bool = True,
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "kind": "place_xperp",
            "dry_run": dry_run,
            "plan": plan.as_dict(),
            "allow_trade": bool(self.client.allow_trade),
            "mode": self.client.mode,
            "tdMode": td_mode,
        }
        if not plan.allowed:
            record["skipped"] = True
            record["reason"] = plan.reason
            self.journal.append("orders", record)
            raise OmsRiskBlocked(plan.reason)
        if dry_run:
            record["placed"] = False
            record["reason"] = "dry_run"
            self.journal.append("orders", record)
            return record
        if self.client.mode != "demo":
            raise LiveTradingBlocked("xperp place refused: live is order-blocked")
        if not self.client.allow_trade:
            raise PaperTradeDisabled(
                "xperp place requires demo client with allow_trade=True"
            )
        mode = str(td_mode or "isolated").lower()
        if mode != "isolated":
            mode = "isolated"
        if set_leverage:
            record["set_leverage"] = self.set_xperp_leverage(
                plan.inst_id, leverage, mgn_mode=mode
            )
        if plan.ord_type == "market":
            payload = self.client.place_xperp_market(
                plan.inst_id, plan.side, plan.sz, td_mode=mode, cl_ord_id=cl_ord_id
            )
        else:
            if not plan.px:
                raise OmsRiskBlocked("limit order missing px")
            payload = self.client.place_xperp_limit(
                plan.inst_id, plan.side, plan.sz, plan.px, td_mode=mode, cl_ord_id=cl_ord_id
            )
        record["placed"] = True
        record["response"] = redact_record(
            {k: payload.get(k) for k in ("code", "msg", "data") if k in payload}
        )
        record["http_status"] = payload.get("_http_status")
        data = payload.get("data") or []
        s_code = None
        if isinstance(data, list) and data and isinstance(data[0], dict):
            s_code = str(data[0].get("sCode") or "")
        if str(payload.get("code")) == "0" and s_code in {"0", ""}:
            self._state["open_inst"] = plan.inst_id
            self._state["open_side"] = plan.side
            self._state["open_venue"] = "xperp"
            ord_id = ""
            if isinstance(data, list) and data and isinstance(data[0], dict):
                ord_id = str(data[0].get("ordId") or "")
            self._state["open_ord_id"] = ord_id or None
            self._save_state()
        self.journal.append("orders", record)
        return record

