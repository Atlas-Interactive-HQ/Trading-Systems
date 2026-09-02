#!/usr/bin/env python3
"""Public FUTURES xperp probe for BTC/DOGE/PEPE (primary) + SOL (backup)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import httpx  # noqa: E402

from atlas.common.config import load_config  # noqa: E402
from atlas.okx.client import EEA_REST_BASE, USER_AGENT  # noqa: E402
from atlas.okx.instruments import (  # noqa: E402
    BACKUP_BASES,
    PRIMARY_BASES,
    filter_xperp,
    is_xperp,
    resolve_xperp_universe,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="OKX EEA public xperp universe probe")
    p.add_argument("--config", default=None)
    p.add_argument("--out-dir", default=None, help="Report directory (default data/reports)")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    rest_base = (cfg.okx.rest_base if cfg.okx else EEA_REST_BASE).rstrip("/")
    primary = tuple(cfg.okx.universe.primary)
    backup = tuple(cfg.okx.universe.backup)
    inst_type = cfg.okx.universe.inst_type
    rule_type = cfg.okx.universe.rule_type
    collateral = cfg.okx.universe.collateral

    url = f"{rest_base}/api/v5/public/instruments"
    params = {"instType": inst_type}
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        r = httpx.get(url, params=params, headers=headers, timeout=30.0)
        r.raise_for_status()
        payload = r.json()
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1

    rows = payload.get("data") or []
    xperp_all = [row for row in rows if is_xperp(row)]
    wanted = filter_xperp(xperp_all, bases=primary + backup)
    resolved = resolve_xperp_universe(rows, primary=primary, backup=backup)

    now = datetime.now(timezone.utc)
    report = {
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rest_base": rest_base,
        "endpoint": "/api/v5/public/instruments",
        "inst_type": inst_type,
        "rule_type": rule_type,
        "universe_preference": {
            "primary": list(primary),
            "backup": list(backup),
            "collateral": collateral,
        },
        "okx_code": payload.get("code"),
        "okx_msg": payload.get("msg"),
        "n_futures": len(rows),
        "n_xperp": len(xperp_all),
        "n_wanted": len(wanted),
        "resolved": resolved["resolved"],
        "missing": resolved["missing"],
        "collateral_note": (
            "Preference is USDC collateral. Live EEA xperp catalogue currently "
            "reports settleCcy=USD for BTC/DOGE/PEPE/SOL (USDC not listed as settleCcy)."
        ),
    }

    out_dir = Path(args.out_dir) if args.out_dir else Path(cfg.data_dir) / "reports"
    if not out_dir.is_absolute():
        out_dir = _ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"okx-eea-xperp-universe-{now.strftime('%Y-%m-%d')}"
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# OKX EEA X-Perp universe ({now.strftime('%Y-%m-%d')} UTC)",
        "",
        f"- REST: `{rest_base}`",
        f"- Filter: `instType={inst_type}` `ruleType={rule_type}`",
        f"- Primary: {', '.join(primary)} · backup: {', '.join(backup)} · collateral pref: {collateral}",
        f"- Catalogue: {report['n_futures']} FUTURES, {report['n_xperp']} xperp",
        f"- OKX code: `{report['okx_code']}` msg: `{report['okx_msg'] or ''}`",
        "",
        "## Resolved",
        "",
        "| role | base | instId | settle | minSz | ctVal | lever | state |",
        "|------|------|--------|--------|-------|-------|-------|-------|",
    ]
    for row in report["resolved"]:
        lines.append(
            "| {role} | {base} | `{instId}` | {settleCcy} | {minSz} | {ctVal} {ctValCcy} | {lever} | {state} |".format(
                **{k: row.get(k) or "" for k in (
                    "role", "base", "instId", "settleCcy", "minSz", "ctVal", "ctValCcy", "lever", "state"
                )}
            )
        )
    if report["missing"]:
        lines += ["", f"**Missing:** {', '.join(report['missing'])}"]
    lines += ["", report["collateral_note"], ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "ok": report["okx_code"] == "0" and not report["missing"],
        "json_report": str(json_path),
        "md_report": str(md_path),
        "n_futures": report["n_futures"],
        "n_xperp": report["n_xperp"],
        "resolved_instIds": [r.get("instId") for r in report["resolved"]],
        "missing": report["missing"],
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
