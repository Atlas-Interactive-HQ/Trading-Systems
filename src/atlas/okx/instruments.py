"""Resolve EEA X-Perp instruments (FUTURES + ruleType=xperp)."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

PRIMARY_BASES = ("BTC", "DOGE", "PEPE")
BACKUP_BASES = ("SOL",)
DEFAULT_UNIVERSE = PRIMARY_BASES + BACKUP_BASES
PREFERRED_SETTLE = ("USDC", "USD")  # USDC preferred; EEA catalogue currently USD


def base_from_row(row: Mapping[str, Any]) -> str:
    uly = str(row.get("uly") or "")
    if "-" in uly:
        return uly.split("-", 1)[0].upper()
    inst_id = str(row.get("instId") or "")
    if "-" in inst_id:
        return inst_id.split("-", 1)[0].upper()
    family = str(row.get("instFamily") or "")
    if "-" in family:
        return family.split("-", 1)[0].upper()
    return inst_id.upper()


def is_xperp(row: Mapping[str, Any]) -> bool:
    return str(row.get("ruleType") or "").lower() == "xperp"


def filter_xperp(
    rows: Sequence[Mapping[str, Any]],
    *,
    bases: Iterable[str] = DEFAULT_UNIVERSE,
) -> list[dict[str, Any]]:
    wanted = {b.upper() for b in bases}
    out: list[dict[str, Any]] = []
    for row in rows:
        if not is_xperp(row):
            continue
        if base_from_row(row) in wanted:
            out.append(dict(row))
    return out


def _settle_rank(row: Mapping[str, Any]) -> int:
    settle = str(row.get("settleCcy") or "").upper()
    try:
        return PREFERRED_SETTLE.index(settle)
    except ValueError:
        return len(PREFERRED_SETTLE)


def pick_for_base(rows: Sequence[Mapping[str, Any]], base: str) -> dict[str, Any] | None:
    candidates = [r for r in rows if base_from_row(r) == base.upper() and is_xperp(r)]
    if not candidates:
        return None
    live = [r for r in candidates if str(r.get("state") or "").lower() == "live"]
    pool = live or candidates
    pool.sort(key=_settle_rank)
    return dict(pool[0])


def resolve_xperp_universe(
    rows: Sequence[Mapping[str, Any]],
    *,
    primary: Sequence[str] = PRIMARY_BASES,
    backup: Sequence[str] = BACKUP_BASES,
) -> dict[str, Any]:
    """Map BTC/DOGE/PEPE (primary) + SOL (backup) to a single xperp instId each."""
    resolved: list[dict[str, Any]] = []
    missing: list[str] = []
    for role, bases in (("primary", primary), ("backup", backup)):
        for base in bases:
            picked = pick_for_base(rows, base)
            if picked is None:
                missing.append(base)
                continue
            resolved.append(
                {
                    "role": role,
                    "base": base.upper(),
                    "instId": picked.get("instId"),
                    "instFamily": picked.get("instFamily"),
                    "uly": picked.get("uly"),
                    "settleCcy": picked.get("settleCcy"),
                    "ctVal": picked.get("ctVal"),
                    "ctValCcy": picked.get("ctValCcy"),
                    "minSz": picked.get("minSz"),
                    "lotSz": picked.get("lotSz"),
                    "tickSz": picked.get("tickSz"),
                    "lever": picked.get("lever"),
                    "state": picked.get("state"),
                    "ruleType": picked.get("ruleType"),
                    "instType": picked.get("instType"),
                }
            )
    return {
        "resolved": resolved,
        "missing": missing,
        "n_input": len(rows),
        "n_xperp_input": sum(1 for r in rows if is_xperp(r)),
    }


# --- SPOT (EEA public catalogue) ---

SPOT_PRIMARY_BASES = ("DOGE", "PEPE", "BTC")
SPOT_BACKUP_BASES = ("SOL",)
SPOT_DEFAULT_UNIVERSE = SPOT_PRIMARY_BASES + SPOT_BACKUP_BASES
PREFERRED_SPOT_QUOTES = ("USDT", "USD")  # USDT first; USD if USDT missing


def is_spot_row(row: Mapping[str, Any]) -> bool:
    return str(row.get("instType") or "").upper() == "SPOT"


def spot_base_quote(row: Mapping[str, Any]) -> tuple[str, str]:
    base = str(row.get("baseCcy") or "").upper()
    quote = str(row.get("quoteCcy") or "").upper()
    if base and quote:
        return base, quote
    inst_id = str(row.get("instId") or "")
    parts = inst_id.split("-")
    if len(parts) == 2:
        return parts[0].upper(), parts[1].upper()
    return base, quote


def assert_spot_inst_id(inst_id: str) -> str:
    """SPOT instIds are BASE-QUOTE (exactly one hyphen). Refuse SWAP/FUTURES."""
    s = str(inst_id or "").strip().upper()
    parts = s.split("-")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"spot instId must be BASE-QUOTE (e.g. DOGE-USDT), got {inst_id!r}"
        )
    return f"{parts[0]}-{parts[1]}"


def assert_xperp_inst_id(inst_id: str) -> str:
    """X-Perp FUTURES instIds contain XPERP (e.g. DOGE-USD_UM_XPERP-310516)."""
    s = str(inst_id or "").strip().upper()
    if "XPERP" not in s or "-" not in s or len(s.split("-")) < 2:
        raise ValueError(
            "xperp instId expected like DOGE-USD_UM_XPERP-310516, "
            f"got {inst_id!r}"
        )
    if len(s.split("-")) == 2:
        raise ValueError(
            f"xperp instId must not be a SPOT BASE-QUOTE pair, got {inst_id!r}"
        )
    return s


def _spot_quote_rank(quote: str, quotes: Sequence[str]) -> int:
    q = quote.upper()
    wanted = [c.upper() for c in quotes]
    try:
        return wanted.index(q)
    except ValueError:
        return len(wanted)


def pick_spot_for_base(
    rows: Sequence[Mapping[str, Any]],
    base: str,
    *,
    quotes: Sequence[str] = PREFERRED_SPOT_QUOTES,
) -> dict[str, Any] | None:
    want = base.upper()
    candidates: list[dict[str, Any]] = []
    for row in rows:
        if not is_spot_row(row) and str(row.get("instType") or ""):
            continue
        b, q = spot_base_quote(row)
        if b != want:
            continue
        if q not in {c.upper() for c in quotes}:
            continue
        candidates.append(dict(row))
    if not candidates:
        return None
    live = [r for r in candidates if str(r.get("state") or "").lower() == "live"]
    pool = live or candidates
    pool.sort(key=lambda r: _spot_quote_rank(spot_base_quote(r)[1], quotes))
    return dict(pool[0])


def resolve_spot_universe(
    rows: Sequence[Mapping[str, Any]],
    *,
    primary: Sequence[str] = SPOT_PRIMARY_BASES,
    backup: Sequence[str] = SPOT_BACKUP_BASES,
    quotes: Sequence[str] = PREFERRED_SPOT_QUOTES,
) -> dict[str, Any]:
    """Map DOGE/PEPE/BTC (primary) + SOL (backup) to one SPOT instId each."""
    resolved: list[dict[str, Any]] = []
    missing: list[str] = []
    for role, bases in (("primary", primary), ("backup", backup)):
        for base in bases:
            picked = pick_spot_for_base(rows, base, quotes=quotes)
            if picked is None:
                missing.append(base.upper())
                continue
            b, q = spot_base_quote(picked)
            resolved.append(
                {
                    "role": role,
                    "base": b,
                    "quote": q,
                    "instId": picked.get("instId"),
                    "instType": picked.get("instType") or "SPOT",
                    "state": picked.get("state"),
                    "minSz": picked.get("minSz"),
                    "lotSz": picked.get("lotSz"),
                    "tickSz": picked.get("tickSz"),
                    "baseCcy": picked.get("baseCcy") or b,
                    "quoteCcy": picked.get("quoteCcy") or q,
                }
            )
    return {
        "resolved": resolved,
        "missing": missing,
        "n_input": len(rows),
        "n_spot_input": sum(1 for r in rows if is_spot_row(r) or not str(r.get("instType") or "")),
        "quotes": list(quotes),
    }
