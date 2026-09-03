"""Phase D: compare a candidate eval profile against the frozen baseline.

Research only. ``not_a_forecast``. The pass rule is decided up front and asserted
in code here — never in prose after seeing the numbers.

Pass (research only) — a candidate passes when, on BOTH primary named windows
(2020-09 and 2023-09), its holdout-30% expectancy after costs is *strictly greater*
(less negative or positive) than the baseline's AND its holdout max drawdown is not
worse than the baseline's by more than 10% relative. Stress rows are documented,
and a "better" expectancy under 2× fees that comes with fewer trades / earlier kill
is flagged as a confound — it is never counted as a win.

Fail — keep the baseline. Say FAIL plainly.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from atlas.paper.named_windows import Q4_WINDOW_IDS
from atlas.paper.profiles import BASELINE

COMPARE_SOURCE = "paper-eval-compare"
PRIMARY_WINDOWS: tuple[str, ...] = ("2020-09", "2023-09")
SECONDARY_WINDOWS: tuple[str, ...] = ("similar",)
SEASONAL_WINDOWS: tuple[str, ...] = tuple(Q4_WINDOW_IDS)
MAX_DD_REL_TOLERANCE = 0.10

SLICES: tuple[tuple[str, str], ...] = (
    ("holdout", "holdout 30%"),
    ("in_sample", "in-sample 70%"),
    ("full", "full"),
)
METRICS: tuple[str, ...] = (
    "n_trades",
    "n_would_place",
    "n_kill_days",
    "n_blocked_daily_cap",
    "expectancy_after_costs_eur",
    "max_dd_eur",
    "fee_drag_eur",
    "win_rate",
)
STRESSES: tuple[tuple[str, str], ...] = (
    ("2x_fees", "2× fees"),
    ("1bar_entry_delay", "1-bar entry delay"),
    ("miss_10pct_entries", "10% missed entries"),
)

PASS_RULE_TEXT = (
    "PASS (research only) iff on BOTH 2020-09 and 2023-09: candidate holdout-30% expectancy "
    "after costs is strictly greater than baseline (less negative or positive) AND candidate "
    "holdout max DD <= baseline holdout max DD × 1.10. A holdout with zero trades has no "
    "expectancy and fails closed. Stress is documented, never scored: a less-negative "
    "expectancy under 2× fees is never a win — with fewer trades / more kill-days it is kill "
    "truncation; with the same trade set it is smaller positions on a poorer equity path (sizing "
    "scales with equity). similar (June) and Q4 months are secondary and do not rewrite this rule."
)

STRESS_CAVEAT_TEXT = (
    "2× fees does not change signals, so any difference in n_trades or n_kill_days between the "
    "full run and the 2× run comes from the equity path: higher fees drain the book faster, the "
    "5% daily kill trips earlier, positions are flattened and the rest of that UTC day is blocked. "
    "Fewer, earlier-killed trades can make expectancy per trade read LESS negative under 2× fees "
    "while the book is simply dying sooner. A second mechanism needs no truncation: sizing scales "
    "with equity (risk budget = 1.5% of equity), so a poorer equity path under 2× fees means smaller "
    "positions and smaller € losses per trade — the same trade set reads less negative in €/trade. "
    "Read 2× fees on a comparable basis: fee drag per trade should be ≈2× the base "
    "(fee_per_trade_ratio), and total fee drag € should be worse or equal unless truncation removed "
    "trades. Fees cannot improve a strategy: never read a less-negative 2× expectancy as a win."
)


def _num(x: Any) -> float | None:
    if x is None or isinstance(x, bool):
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _pick(m: Mapping[str, Any] | None) -> dict[str, Any]:
    m = m or {}
    return {k: m.get(k) for k in METRICS}


def _delta(base: Mapping[str, Any], cand: Mapping[str, Any]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for k in METRICS:
        b, c = _num(base.get(k)), _num(cand.get(k))
        out[k] = None if b is None or c is None else round(c - b, 8)
    return out


def index_samples(samples: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for s in samples:
        sid = str(s.get("sample_id") or "").strip()
        if sid:
            out[sid] = dict(s)
    return out


def role_for(sample_id: str) -> str:
    if sample_id in PRIMARY_WINDOWS:
        return "primary"
    if sample_id in SECONDARY_WINDOWS or sample_id == "similar-regime":
        return "secondary"
    if sample_id in SEASONAL_WINDOWS:
        return "seasonal"
    return "other"


def stress_notes(sample: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Per-stress comparable-basis notes for ONE profile's sample row."""
    if not sample or not sample.get("ok"):
        return {}
    full = sample.get("full") or {}
    stress = sample.get("stress") or {}
    n_full = int(full.get("n_trades") or 0)
    k_full = int(full.get("n_kill_days") or 0)
    e_full = _num(full.get("expectancy_after_costs_eur"))
    f_full = _num(full.get("fee_drag_eur")) or 0.0
    fpt_full = (f_full / n_full) if n_full else None
    out: dict[str, dict[str, Any]] = {}
    for key, _title in STRESSES:
        s = stress.get(key) or {}
        n_s = int(s.get("n_trades") or 0)
        k_s = int(s.get("n_kill_days") or 0)
        e_s = _num(s.get("expectancy_after_costs_eur"))
        f_s = _num(s.get("fee_drag_eur")) or 0.0
        fpt_s = (f_s / n_s) if n_s else None
        less_negative = e_full is not None and e_s is not None and e_s > e_full
        trade_set_differs = n_s != n_full or k_s != k_full
        # Fees never change signals → for 2× fees a different trade set is purely the
        # kill/equity path (truncation). Delay/miss change the trade set by construction.
        confound = key == "2x_fees" and trade_set_differs
        # Same trade set yet less-negative €/trade under 2× fees: sizing scales with
        # equity (risk budget = 1.5% of equity), so a poorer equity path means smaller
        # positions and smaller € losses. Also not a win.
        equity_path = key == "2x_fees" and less_negative and not trade_set_differs
        mechanism = None
        if less_negative and key == "2x_fees":
            mechanism = "kill_truncation" if trade_set_differs else "equity_path_sizing"
        out[key] = {
            "n_trades_full": n_full,
            "n_trades_stress": n_s,
            "n_trades_delta": n_s - n_full,
            "n_kill_days_full": k_full,
            "n_kill_days_stress": k_s,
            "expectancy_full": e_full,
            "expectancy_stress": e_s,
            "expectancy_less_negative_than_full": bool(less_negative),
            "fee_drag_full": round(f_full, 8),
            "fee_drag_stress": round(f_s, 8),
            "fee_drag_total_worse_or_equal": bool(f_s + 1e-9 >= f_full),
            "fee_per_trade_full": None if fpt_full is None else round(fpt_full, 8),
            "fee_per_trade_stress": None if fpt_s is None else round(fpt_s, 8),
            "fee_per_trade_ratio": (
                None if not fpt_full or fpt_s is None else round(fpt_s / fpt_full, 4)
            ),
            "max_dd_full": _num(full.get("max_dd_eur")),
            "max_dd_stress": _num(s.get("max_dd_eur")),
            "trade_set_differs": bool(trade_set_differs),
            "kill_truncation_confound": bool(confound),
            "equity_path_confound": bool(equity_path),
            "false_win_mechanism": mechanism,
            # ANY less-negative 2× fees expectancy is a false-win risk; fees cannot help.
            "false_win_risk": bool(less_negative and key == "2x_fees"),
        }
    return out


def evaluate_pass_rule(
    base_idx: Mapping[str, Mapping[str, Any]],
    cand_idx: Mapping[str, Mapping[str, Any]],
    *,
    windows: Iterable[str] = PRIMARY_WINDOWS,
    dd_tol: float = MAX_DD_REL_TOLERANCE,
) -> dict[str, Any]:
    wins = [str(w) for w in windows]
    per: dict[str, dict[str, Any]] = {}
    for w in wins:
        b = base_idx.get(w)
        c = cand_idx.get(w)
        if not b or not c or not b.get("ok") or not c.get("ok"):
            per[w] = {
                "available": False,
                "pass": False,
                "why": "baseline or candidate eval missing/not ok for this window (fail closed)",
            }
            continue
        bh = b.get("holdout") or {}
        ch = c.get("holdout") or {}
        bn = int(bh.get("n_trades") or 0)
        cn = int(ch.get("n_trades") or 0)
        be, ce = _num(bh.get("expectancy_after_costs_eur")), _num(ch.get("expectancy_after_costs_eur"))
        bdd, cdd = _num(bh.get("max_dd_eur")), _num(ch.get("max_dd_eur"))
        # Fail closed on anything that cannot be scored: a zero-trade holdout (no expectancy
        # to compare, whatever number the row carries), or a missing expectancy / max DD.
        fail_closed: list[str] = []
        if bn <= 0 or cn <= 0:
            fail_closed.append(f"zero-trade holdout (baseline n={bn}, candidate n={cn})")
        if be is None or ce is None:
            fail_closed.append("missing holdout expectancy")
        if bdd is None or cdd is None:
            fail_closed.append("missing holdout max DD")
        exp_ok = not fail_closed and ce > be  # type: ignore[operator]
        dd_ok = not fail_closed and cdd <= bdd * (1.0 + dd_tol) + 1e-9  # type: ignore[operator]
        per[w] = {
            "available": True,
            "baseline_holdout_expectancy": be,
            "candidate_holdout_expectancy": ce,
            "expectancy_delta": None if be is None or ce is None else round(ce - be, 8),
            "expectancy_strictly_greater": bool(exp_ok),
            "baseline_holdout_max_dd": bdd,
            "candidate_holdout_max_dd": cdd,
            "max_dd_rel_change": None if not bdd or cdd is None else round((cdd - bdd) / bdd, 6),
            "max_dd_within_tolerance": bool(dd_ok),
            "fail_closed_reasons": fail_closed,
            "baseline_holdout_n_trades": bh.get("n_trades"),
            "candidate_holdout_n_trades": ch.get("n_trades"),
            "baseline_holdout_n_kill_days": bh.get("n_kill_days"),
            "candidate_holdout_n_kill_days": ch.get("n_kill_days"),
            "candidate_holdout_n_blocked_daily_cap": ch.get("n_blocked_daily_cap"),
            "pass": bool(exp_ok and dd_ok),
        }
    all_pass = bool(wins) and all(per[w].get("pass") for w in wins)
    return {
        "rule_text": PASS_RULE_TEXT,
        "windows": wins,
        "max_dd_rel_tolerance": dd_tol,
        "expectancy_strictly_greater_required": True,
        "per_window": per,
        "pass": all_pass,
        "verdict": "PASS" if all_pass else "FAIL",
        "not_a_forecast": True,
    }


def compare_profiles(
    base_samples: Iterable[Mapping[str, Any]],
    cand_samples: Iterable[Mapping[str, Any]],
    *,
    base_name: str = BASELINE,
    cand_name: str,
    base_overlay: Mapping[str, Any] | None = None,
    cand_overlay: Mapping[str, Any] | None = None,
    cand_description: str = "",
    cand_notes: Iterable[str] = (),
    cand_baseline_note: str = "",
) -> dict[str, Any]:
    base_idx = index_samples(base_samples)
    cand_idx = index_samples(cand_samples)
    ordered: list[str] = []
    for group in (PRIMARY_WINDOWS, SECONDARY_WINDOWS, SEASONAL_WINDOWS):
        for w in group:
            if (w in base_idx or w in cand_idx) and w not in ordered:
                ordered.append(w)
    for w in sorted(set(base_idx) | set(cand_idx)):
        if w not in ordered:
            ordered.append(w)

    rows: list[dict[str, Any]] = []
    for sid in ordered:
        b = base_idx.get(sid)
        c = cand_idx.get(sid)
        ok = bool(b and c and b.get("ok") and c.get("ok"))
        row: dict[str, Any] = {
            "sample_id": sid,
            "role": role_for(sid),
            "ok": ok,
            "in_baseline": bool(b and b.get("ok")),
            "in_candidate": bool(c and c.get("ok")),
            "md_label": (c or b or {}).get("md_label"),
            "split": (c or b or {}).get("split"),
            "not_a_forecast": True,
        }
        if ok:
            assert b is not None and c is not None
            slices: dict[str, Any] = {}
            for key, _title in SLICES:
                bm, cm = _pick(b.get(key)), _pick(c.get(key))
                slices[key] = {"baseline": bm, "candidate": cm, "delta": _delta(bm, cm)}
            row["slices"] = slices
            row["stress"] = {
                "baseline": {k: _pick((b.get("stress") or {}).get(k)) for k, _ in STRESSES},
                "candidate": {k: _pick((c.get("stress") or {}).get(k)) for k, _ in STRESSES},
            }
            row["stress_notes"] = {"baseline": stress_notes(b), "candidate": stress_notes(c)}
        rows.append(row)

    return {
        "ok": True,
        "place_orders": False,
        "not_a_forecast": True,
        "source": COMPARE_SOURCE,
        "baseline": {"name": base_name, "overlay": dict(base_overlay or {})},
        "candidate": {
            "name": cand_name,
            "overlay": dict(cand_overlay or {}),
            "description": cand_description,
            "notes": list(cand_notes),
            "baseline_note": cand_baseline_note,
        },
        "roles": {
            "primary": list(PRIMARY_WINDOWS),
            "secondary": list(SECONDARY_WINDOWS),
            "seasonal": list(SEASONAL_WINDOWS),
        },
        "pass_rule": evaluate_pass_rule(base_idx, cand_idx),
        "samples": rows,
        "stress_caveat": STRESS_CAVEAT_TEXT,
        "disclaimer": (
            "research only. not_a_forecast. a PASS here is not a Phase C or live recommendation; "
            "a FAIL keeps the frozen baseline. named-window ≠ future performance."
        ),
    }


# ----------------------------------------------------------------------------- markdown


def _f(x: Any, nd: int = 4) -> str:
    v = _num(x)
    return "—" if v is None else f"{v:.{nd}f}"


def _i(x: Any) -> str:
    return "—" if x is None else str(int(x))


def _pct(x: Any) -> str:
    """Signed percentage (for changes)."""
    v = _num(x)
    return "—" if v is None else f"{100.0 * v:+.1f}%"


def _rate(x: Any) -> str:
    """Unsigned percentage (for win rates)."""
    v = _num(x)
    return "—" if v is None else f"{100.0 * v:.1f}%"


def _slice_table(row: Mapping[str, Any]) -> list[str]:
    s = row.get("slices") or {}
    hold, ins, full = s.get("holdout") or {}, s.get("in_sample") or {}, s.get("full") or {}
    lines = [
        "| metric | baseline holdout | candidate holdout | Δ holdout | baseline IS | candidate IS | baseline full | candidate full |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    spec = (
        ("n_trades", "n_trades", _i),
        ("n_would_place", "n_would_place", _i),
        ("n_kill_days", "n_kill_days", _i),
        ("n_blocked_daily_cap", "n_blocked_daily_cap", _i),
        ("expectancy_after_costs_eur", "expectancy after costs (€/trade)", lambda v: _f(v, 4)),
        ("max_dd_eur", "max DD (€)", lambda v: _f(v, 2)),
        ("fee_drag_eur", "fee drag (€)", lambda v: _f(v, 2)),
        ("win_rate", "win rate (secondary)", _rate),
    )
    for key, title, fmt in spec:
        d = (hold.get("delta") or {}).get(key)
        d_s = "—" if d is None else (f"{d:+.4f}" if key in ("expectancy_after_costs_eur",) else f"{d:+.2f}" if key in ("max_dd_eur", "fee_drag_eur") else f"{100*d:+.1f}%" if key == "win_rate" else f"{int(d):+d}")
        lines.append(
            f"| {title} | {fmt((hold.get('baseline') or {}).get(key))} | {fmt((hold.get('candidate') or {}).get(key))} | {d_s} "
            f"| {fmt((ins.get('baseline') or {}).get(key))} | {fmt((ins.get('candidate') or {}).get(key))} "
            f"| {fmt((full.get('baseline') or {}).get(key))} | {fmt((full.get('candidate') or {}).get(key))} |"
        )
    return lines


def _stress_table(row: Mapping[str, Any]) -> list[str]:
    notes = row.get("stress_notes") or {}
    lines = [
        "| profile | stress | n_trades full→stress | kill-days full→stress | expectancy full→stress (€/trade) | max DD stress (€) | fee drag full→stress (€) | fee/trade ratio | confound |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for prof in ("baseline", "candidate"):
        pn = notes.get(prof) or {}
        for key, title in STRESSES:
            n = pn.get(key) or {}
            if not n:
                continue
            flag = ""
            if n.get("false_win_risk") and n.get("false_win_mechanism") == "kill_truncation":
                flag = "**kill-truncation: less-negative expectancy is NOT a win**"
            elif n.get("false_win_risk"):
                flag = "**equity-path sizing (same trade/kill counts): less-negative expectancy is NOT a win**"
            elif n.get("kill_truncation_confound"):
                flag = "kill-truncation (trade set differs)"
            elif key != "2x_fees" and n.get("trade_set_differs"):
                flag = "trade set differs by construction"
            lines.append(
                f"| {prof} | {title} | {_i(n.get('n_trades_full'))}→{_i(n.get('n_trades_stress'))} "
                f"| {_i(n.get('n_kill_days_full'))}→{_i(n.get('n_kill_days_stress'))} "
                f"| {_f(n.get('expectancy_full'), 4)}→{_f(n.get('expectancy_stress'), 4)} "
                f"| {_f(n.get('max_dd_stress'), 2)} "
                f"| {_f(n.get('fee_drag_full'), 2)}→{_f(n.get('fee_drag_stress'), 2)} "
                f"| {_f(n.get('fee_per_trade_ratio'), 2) if key == '2x_fees' else '—'} | {flag} |"
            )
    return lines


def _verdict_table(rule: Mapping[str, Any]) -> list[str]:
    lines = [
        "| window | baseline holdout exp. | candidate holdout exp. | strictly greater? | baseline holdout DD | candidate holdout DD | DD change | DD within +10%? | cand. kill-days | cand. daily_cap blocked | window pass |",
        "|---|---:|---:|:---:|---:|---:|---:|:---:|---:|---:|:---:|",
    ]
    for w in rule.get("windows") or []:
        p = (rule.get("per_window") or {}).get(w) or {}
        if not p.get("available"):
            lines.append(f"| {w} | — | — | — | — | — | — | — | — | — | **FAIL** (missing) |")
            continue
        lines.append(
            f"| {w} | {_f(p.get('baseline_holdout_expectancy'), 4)} | {_f(p.get('candidate_holdout_expectancy'), 4)} "
            f"| {'yes' if p.get('expectancy_strictly_greater') else 'no'} "
            f"| {_f(p.get('baseline_holdout_max_dd'), 2)} | {_f(p.get('candidate_holdout_max_dd'), 2)} | {_pct(p.get('max_dd_rel_change'))} "
            f"| {'yes' if p.get('max_dd_within_tolerance') else 'no'} "
            f"| {_i(p.get('candidate_holdout_n_kill_days'))} | {_i(p.get('candidate_holdout_n_blocked_daily_cap'))} "
            f"| {'**PASS**' if p.get('pass') else '**FAIL**'} |"
        )
    return lines


def _confound_prose(cmp: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    for row in cmp.get("samples") or []:
        if not row.get("ok"):
            continue
        for prof in ("baseline", "candidate"):
            n = ((row.get("stress_notes") or {}).get(prof) or {}).get("2x_fees") or {}
            if not n:
                continue
            if n.get("false_win_risk") and n.get("false_win_mechanism") == "kill_truncation":
                out.append(
                    f"- `{row['sample_id']}` / {prof}: 2× fees reads {_f(n.get('expectancy_stress'), 4)} vs {_f(n.get('expectancy_full'), 4)} base "
                    f"(less negative) with n_trades {_i(n.get('n_trades_full'))}→{_i(n.get('n_trades_stress'))} and kill-days "
                    f"{_i(n.get('n_kill_days_full'))}→{_i(n.get('n_kill_days_stress'))}. Fee rate doubled (fee/trade ratio {_f(n.get('fee_per_trade_ratio'), 2)}"
                    + ("; below 2.0 because positions shrink on the poorer equity path" if (_num(n.get('fee_per_trade_ratio')) or 0) < 2.0 else "")
                    + "); the 'improvement' is the kill flattening/truncating the trade set. **Not a win.**"
                )
            elif n.get("false_win_risk"):
                out.append(
                    f"- `{row['sample_id']}` / {prof}: 2× fees reads {_f(n.get('expectancy_stress'), 4)} vs {_f(n.get('expectancy_full'), 4)} base "
                    f"(less negative) with the same n_trades ({_i(n.get('n_trades_full'))}) and kill-day count ({_i(n.get('n_kill_days_full'))}) — a count-based check — and total fee drag "
                    f"{_f(n.get('fee_drag_full'), 2)}→{_f(n.get('fee_drag_stress'), 2)}. Sizing scales with equity, so the poorer equity path under 2× fees "
                    f"shrinks positions and € losses per trade. **Not a win.**"
                )
            elif n.get("kill_truncation_confound"):
                out.append(
                    f"- `{row['sample_id']}` / {prof}: 2× fees trade set differs (n_trades {_i(n.get('n_trades_full'))}→{_i(n.get('n_trades_stress'))}, "
                    f"kill-days {_i(n.get('n_kill_days_full'))}→{_i(n.get('n_kill_days_stress'))}); expectancy {_f(n.get('expectancy_full'), 4)}→{_f(n.get('expectancy_stress'), 4)} is not on a comparable basis."
                )
            elif not n.get("fee_drag_total_worse_or_equal"):
                out.append(
                    f"- `{row['sample_id']}` / {prof}: 2× fees total fee drag is LOWER than base ({_f(n.get('fee_drag_full'), 2)}→{_f(n.get('fee_drag_stress'), 2)}) without a trade-set change — inspect."
                )
    return out or ["- No 2× fee row on any sample shows a kill-truncation confound."]


# Wording pinned per candidate so already-committed docs regenerate byte-identically
# (phase1/16 was written when "candidate_v2" was the hypothetical next trial and the
# overlay was a pair of filters). Defaults are overlay-agnostic.
WORDING_DEFAULT = {
    "fail_followup": "No follow-up candidate is proposed in this trial.",
    "not_followup": "Not a proposal for a follow-up candidate or a parameter sweep.",
    "not_edge": "Not a claim that the locked breakout, with or without this overlay, has edge.",
}
WORDING_BY_CANDIDATE = {
    "candidate_v1_filters": {
        "fail_followup": "No candidate_v2 is proposed in this trial.",
        "not_followup": "Not a candidate_v2 proposal.",
        "not_edge": "Not a claim that the locked breakout, with or without these filters, has edge.",
    },
}


def _wording(cand_name: str, key: str) -> str:
    return WORDING_BY_CANDIDATE.get(cand_name, {}).get(key) or WORDING_DEFAULT[key]

RUN_NOTE_START = "<!-- run-note:start -->"
RUN_NOTE_END = "<!-- run-note:end -->"


def extract_run_note(markdown: str) -> str | None:
    """Return the run note carried between the markers of an existing doc (None if absent)."""
    i = markdown.find(RUN_NOTE_START)
    j = markdown.find(RUN_NOTE_END)
    if i < 0 or j < 0 or j < i:
        return None
    return markdown[i + len(RUN_NOTE_START) : j].strip("\n")


def extract_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def render_candidate_markdown(
    cmp: Mapping[str, Any],
    *,
    heading: str,
    reproduce: Iterable[str] = (),
    run_note: str | None = None,
) -> str:
    cand = cmp.get("candidate") or {}
    base = cmp.get("baseline") or {}
    rule = cmp.get("pass_rule") or {}
    verdict = str(rule.get("verdict") or "FAIL")
    lines: list[str] = [
        f"# {heading.lstrip('# ').strip()}",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live from this score. A PASS is a research result on paper holdout, not a go-live signal; a FAIL keeps the frozen baseline.",
        "",
        "## Candidate",
        "",
        f"- Baseline: `{base.get('name')}` — frozen BreakoutV1 + `config/default.yaml` (no overlay{cand.get('baseline_note') or ''}).",
        f"- Candidate: `{cand.get('name')}` — overlay `{json.dumps(cand.get('overlay') or {}, sort_keys=True)}`.",
        *[f"- {note}" for note in (cand.get("notes") or [])],
        "",
        "## Pass / fail rule (decided up front)",
        "",
        str(rule.get("rule_text") or PASS_RULE_TEXT),
        "",
        f"## Verdict: **{verdict}**",
        "",
    ]
    lines.extend(_verdict_table(rule))
    lines.append("")
    if verdict == "PASS":
        lines.append("Both primary windows pass on holdout expectancy and holdout max DD. This is a research PASS on paper; it says nothing about live and does not by itself unlock Phase C. Promoting the candidate into the frozen baseline (`config/default.yaml`) is a separate decision for Atlas/Kaje, not part of this trial.")
        still_negative = [
            w for w in (rule.get("windows") or [])
            if (_num(((rule.get("per_window") or {}).get(w) or {}).get("candidate_holdout_expectancy")) or 0.0) < 0
        ]
        if still_negative:
            lines.append("")
            lines.append(
                "**Still negative.** Candidate holdout expectancy after costs is below zero on "
                + ", ".join(f"`{w}`" for w in still_negative)
                + ". PASS here means *loses less than the frozen baseline on holdout*, not *positive expectancy* and not edge."
            )
    else:
        lines.append(
            "At least one primary window fails the rule. **FAIL** — keep the frozen baseline. "
            + _wording(str(cand.get("name")), "fail_followup")
        )
    lines.append("")
    if run_note:
        # Markers let a plain re-run of the compare script carry this note over verbatim.
        lines.extend([RUN_NOTE_START, run_note.strip("\n"), RUN_NOTE_END, ""])

    def section(title: str, role: str, intro: str) -> None:
        rows = [r for r in (cmp.get("samples") or []) if r.get("role") == role]
        if not rows:
            return
        lines.extend([f"## {title}", "", intro, ""])
        for row in rows:
            lines.append(f"### {row['sample_id']}")
            lines.append("")
            if not row.get("ok"):
                lines.append(
                    f"Not comparable: in baseline={row.get('in_baseline')} / in candidate={row.get('in_candidate')}. No fake numbers."
                )
                lines.append("")
                continue
            split = row.get("split") or {}
            lines.append(f"MD: {row.get('md_label')}")
            lines.append(
                f"Bars: full {split.get('n_bars_full')} · IS {split.get('n_bars_in_sample')} · holdout {split.get('n_bars_holdout')}."
            )
            lines.append("")
            lines.extend(_slice_table(row))
            lines.append("")
            lines.append("Stress (full sample, same engine path):")
            lines.append("")
            lines.extend(_stress_table(row))
            lines.append("")
            lines.append("`not_a_forecast: true`.")
            lines.append("")

    section(
        "Primary windows (pass rule)",
        "primary",
        "Research MD DOGE-USDT (not OMS DOGE-USD). Holdout 30% is the scored slice.",
    )
    section(
        "Secondary: similar-regime June (small n)",
        "secondary",
        "Similar-regime window, DOGE-USD spot + X-Perp MD 310404. Small sample; informational only.",
    )

    seasonal = [r for r in (cmp.get("samples") or []) if r.get("role") == "seasonal"]
    if seasonal:
        lines.extend(
            [
                "## Seasonal check: Q4 months (secondary — does not rewrite the pass rule)",
                "",
                "Oct/Nov/Dec 2020/2023/2024 on DOGE-USDT. Holdout 30% per month. Informational: same season as the coming months, not a similar-regime match.",
                "",
                "| month | baseline holdout exp. | candidate holdout exp. | Δ | baseline holdout DD | candidate holdout DD | baseline kill-days (holdout) | candidate kill-days (holdout) | candidate daily_cap blocked (full) | candidate n_trades (full) vs baseline |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        better = 0
        for row in seasonal:
            if not row.get("ok"):
                lines.append(f"| {row['sample_id']} | — | — | — | — | — | — | — | — | not comparable |")
                continue
            h = (row.get("slices") or {}).get("holdout") or {}
            fu = (row.get("slices") or {}).get("full") or {}
            bh, ch, dh = h.get("baseline") or {}, h.get("candidate") or {}, h.get("delta") or {}
            d = dh.get("expectancy_after_costs_eur")
            if d is not None and d > 0:
                better += 1
            lines.append(
                f"| {row['sample_id']} | {_f(bh.get('expectancy_after_costs_eur'), 4)} | {_f(ch.get('expectancy_after_costs_eur'), 4)} "
                f"| {'—' if d is None else f'{d:+.4f}'} | {_f(bh.get('max_dd_eur'), 2)} | {_f(ch.get('max_dd_eur'), 2)} "
                f"| {_i(bh.get('n_kill_days'))} | {_i(ch.get('n_kill_days'))} | {_i((fu.get('candidate') or {}).get('n_blocked_daily_cap'))} "
                f"| {_i((fu.get('candidate') or {}).get('n_trades'))} vs {_i((fu.get('baseline') or {}).get('n_trades'))} |"
            )
        n_ok = sum(1 for r in seasonal if r.get("ok"))
        lines.append("")
        lines.append(
            f"Candidate holdout expectancy is less negative than baseline in {better} of {n_ok} Q4 months. Secondary information only; it does not change the verdict above."
        )
        lines.append("")

    lines.extend(
        [
            "## How to read the 2× fees stress (kill truncation and equity-path sizing)",
            "",
            str(cmp.get("stress_caveat") or STRESS_CAVEAT_TEXT),
            "",
            "Flagged rows in this run:",
            "",
        ]
    )
    lines.extend(_confound_prose(cmp))
    lines.append("")
    if reproduce:
        lines.extend(["## Reproduce", "", "```bash"])
        lines.extend(list(reproduce))
        lines.extend(["```", "", "JSON under gitignored `data/reports/` (`profiles/<profile>/eval_*.json`, `compare_*.json`). Cached research candles under `data/eval_cache/` are reused; nothing is refetched unless missing. Re-running the last command on the existing file carries over its H1 and the run-note section between the `run-note` markers, so it regenerates this document as committed.", ""])
    lines.extend(
        [
            "## What this is not",
            "",
            "- Not a Phase C recommendation.",
            "- Not a live-trading recommendation.",
            f"- {_wording(str(cand.get('name')), 'not_edge')}",
            f"- {_wording(str(cand.get('name')), 'not_followup')}",
            "",
        ]
    )
    return "\n".join(lines) + "\n"
