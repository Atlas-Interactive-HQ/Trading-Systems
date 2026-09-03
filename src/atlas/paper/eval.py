"""Phase D-lite: costed paper evaluation. Research only.

Primary score: expectancy after costs on the €200 book.
not_a_forecast: true. Do not headline PnL. Do not retune BreakoutV1.
Reuses PaperEngine / ShadowEngine — no second ledger.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from atlas.collectors.base import new_run_id
from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.engine import PaperEngine, PaperSettings, PaperSummary, strategy_from_app_config
from atlas.paper.md import OKX_REST, USER_AGENT, persist_candles
from atlas.paper.named_windows import (
    NAMED_WINDOWS,
    RESEARCH_SPOT_MD,
    expand_window_ids,
    fetch_closed_history,
    parse_windows_arg,
)
from atlas.paper.replay import ReplayError, fetch_venue_history, md_inst_for_venue
from atlas.paper.shadow import ShadowEngine, latest_replay_summary, shadow_settings, windows_from_replay_summary
from atlas.paper.types import Bar, q

EVAL_SOURCE = "paper-eval"
SPLIT_FRAC = 0.70  # first 70% in-sample; last 30% holdout. Never tuned after seeing scores.
MISS_SEED = 20260903
STRESS_MISS_FRAC = 0.10


class NullJournal:
    """Discard engine journals during eval (reports go to data/reports/)."""

    def append(self, channel: str, record: dict[str, Any], *, ts_ms: int | None = None) -> Path:
        return Path(".")

    def write_summary(self, summary: dict[str, Any], *, ts_ms: int) -> Path:
        return Path(".")

    def dir_for(self, ts_ms: int) -> Path:
        return Path(".")


@dataclass
class SliceMetrics:
    label: str
    n_bars: int
    n_trades: int
    n_would_place: int
    n_entries: int
    n_kill_days: int
    n_kills: int
    expectancy_after_costs_eur: float | None
    max_dd_eur: float
    fee_drag_eur: float
    fee_drag_frac: float | None
    turnover_notional_eur: float
    turnover_vs_book: float | None
    win_rate: float | None
    start_equity_eur: float
    end_equity_eur: float
    realized_pnl_eur: float
    not_a_forecast: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def chronological_split(
    bars: list[Bar], *, frac: float = SPLIT_FRAC
) -> tuple[list[Bar], list[Bar]]:
    """First frac in-sample, remainder holdout. Cut is floor(n*frac); never searched."""
    if not (0.0 < frac < 1.0):
        raise ReplayError(f"split frac must be in (0,1), got {frac}")
    n = len(bars)
    cut = int(n * frac)
    return list(bars[:cut]), list(bars[cut:])


def _win_rate(wins: int, trades: int) -> float | None:
    if trades <= 0:
        return None
    return q(wins / trades)


def _expectancy(realized: float, trades: int) -> float | None:
    if trades <= 0:
        return None
    return q(realized / trades)


def metrics_from_run(
    paper: PaperSummary,
    *,
    n_would_place: int,
    label: str,
) -> SliceMetrics:
    start = float(paper.start_equity)
    extra = paper.extra or {}
    max_dd = float(extra.get("max_dd") or 0.0)
    n_kill_days = int(extra.get("n_kill_days") or 0)
    turnover = float(extra.get("turnover_notional") or 0.0)
    fees = float(paper.fees_paid)
    return SliceMetrics(
        label=label,
        n_bars=int(paper.n_bars),
        n_trades=int(paper.n_trades),
        n_would_place=int(n_would_place),
        n_entries=int(paper.n_entries),
        n_kill_days=n_kill_days,
        n_kills=int(paper.n_kills),
        expectancy_after_costs_eur=_expectancy(float(paper.realized_pnl), int(paper.n_trades)),
        max_dd_eur=q(max_dd),
        fee_drag_eur=q(fees),
        fee_drag_frac=q(fees / start) if start else None,
        turnover_notional_eur=q(turnover),
        turnover_vs_book=q(turnover / start) if start else None,
        win_rate=_win_rate(int(paper.wins), int(paper.n_trades)),
        start_equity_eur=start,
        end_equity_eur=float(paper.end_equity),
        realized_pnl_eur=float(paper.realized_pnl),
        not_a_forecast=True,
    )


def _slice_1h(bars_1h: list[Bar], window_15: list[Bar]) -> list[Bar]:
    if not window_15:
        return []
    start = window_15[0].ts_open_ms
    end = window_15[-1].ts_close_ms
    return [b for b in bars_1h if b.ts_close_ms <= end and b.ts_open_ms >= start - 48 * 3600 * 1000]


def run_slice(
    *,
    bars_by_symbol: dict[str, list[Bar]],
    bars_1h_by_symbol: dict[str, list[Bar]],
    settings: PaperSettings,
    strategy: Any,
    venue_by_symbol: dict[str, str],
    label: str,
    run_id: str | None = None,
) -> SliceMetrics:
    if not bars_by_symbol or not any(bars_by_symbol.values()):
        return SliceMetrics(
            label=label,
            n_bars=0,
            n_trades=0,
            n_would_place=0,
            n_entries=0,
            n_kill_days=0,
            n_kills=0,
            expectancy_after_costs_eur=None,
            max_dd_eur=0.0,
            fee_drag_eur=0.0,
            fee_drag_frac=None,
            turnover_notional_eur=0.0,
            turnover_vs_book=None,
            win_rate=None,
            start_equity_eur=settings.equity_eur,
            end_equity_eur=settings.equity_eur,
            realized_pnl_eur=0.0,
        )
    rid = run_id or new_run_id("eval")
    eng = ShadowEngine(
        settings,
        strategy,
        journal=NullJournal(),
        run_id=rid,
        data_dir="data",
        venue_by_symbol=venue_by_symbol,
    )
    paper = eng.run(bars_by_symbol, bars_1h_by_symbol, universe=list(bars_by_symbol.keys()))
    return metrics_from_run(paper, n_would_place=eng.n_would_place, label=label)


def split_symbols(
    bars_by_symbol: dict[str, list[Bar]],
    bars_1h_by_symbol: dict[str, list[Bar]],
    *,
    frac: float = SPLIT_FRAC,
) -> tuple[dict[str, list[Bar]], dict[str, list[Bar]], dict[str, list[Bar]], dict[str, list[Bar]]]:
    """Split every symbol on the primary clock (longest 15m series)."""
    if not bars_by_symbol:
        return {}, {}, {}, {}
    primary = max(bars_by_symbol.items(), key=lambda kv: len(kv[1]))[0]
    ins, hold = chronological_split(bars_by_symbol[primary], frac=frac)
    cut_ts = ins[-1].ts_close_ms if ins else 0

    def _cut(bars: list[Bar], *, holdout: bool) -> list[Bar]:
        if holdout:
            return [b for b in bars if b.ts_open_ms > cut_ts]
        return [b for b in bars if b.ts_close_ms <= cut_ts]

    ins_15 = {s: _cut(b, holdout=False) for s, b in bars_by_symbol.items()}
    hold_15 = {s: _cut(b, holdout=True) for s, b in bars_by_symbol.items()}
    ins_1h = {s: _slice_1h(bars_1h_by_symbol.get(s) or [], ins_15.get(s) or []) for s in bars_by_symbol}
    hold_1h = {s: _slice_1h(bars_1h_by_symbol.get(s) or [], hold_15.get(s) or []) for s in bars_by_symbol}
    return ins_15, ins_1h, hold_15, hold_1h


def _copy_settings(base: PaperSettings, **kw: Any) -> PaperSettings:
    d = asdict(base)
    d.update(kw)
    return PaperSettings(**d)


def evaluate_bars(
    *,
    sample_id: str,
    bars_by_symbol: dict[str, list[Bar]],
    bars_1h_by_symbol: dict[str, list[Bar]],
    settings: PaperSettings,
    strategy: Any,
    venue_by_symbol: dict[str, str] | None = None,
    md_label: str = "",
) -> dict[str, Any]:
    vmap = venue_by_symbol or {s: "spot" for s in bars_by_symbol}
    full = run_slice(
        bars_by_symbol=bars_by_symbol,
        bars_1h_by_symbol=bars_1h_by_symbol,
        settings=settings,
        strategy=strategy,
        venue_by_symbol=vmap,
        label="full",
        run_id=new_run_id(f"eval-{sample_id}-full"),
    )
    ins_15, ins_1h, hold_15, hold_1h = split_symbols(bars_by_symbol, bars_1h_by_symbol)
    ins = run_slice(
        bars_by_symbol=ins_15,
        bars_1h_by_symbol=ins_1h,
        settings=settings,
        strategy=strategy,
        venue_by_symbol=vmap,
        label="in_sample_70",
        run_id=new_run_id(f"eval-{sample_id}-is"),
    )
    hold = run_slice(
        bars_by_symbol=hold_15,
        bars_1h_by_symbol=hold_1h,
        settings=settings,
        strategy=strategy,
        venue_by_symbol=vmap,
        label="holdout_30",
        run_id=new_run_id(f"eval-{sample_id}-oos"),
    )
    fee2 = run_slice(
        bars_by_symbol=bars_by_symbol,
        bars_1h_by_symbol=bars_1h_by_symbol,
        settings=_copy_settings(settings, fee_rate=float(settings.fee_rate) * 2.0),
        strategy=strategy,
        venue_by_symbol=vmap,
        label="stress_2x_fees",
        run_id=new_run_id(f"eval-{sample_id}-fee2"),
    )
    delay = run_slice(
        bars_by_symbol=bars_by_symbol,
        bars_1h_by_symbol=bars_1h_by_symbol,
        settings=_copy_settings(settings, entry_delay_bars=1),
        strategy=strategy,
        venue_by_symbol=vmap,
        label="stress_1bar_delay",
        run_id=new_run_id(f"eval-{sample_id}-delay"),
    )
    miss = run_slice(
        bars_by_symbol=bars_by_symbol,
        bars_1h_by_symbol=bars_1h_by_symbol,
        settings=_copy_settings(
            settings, miss_entry_frac=STRESS_MISS_FRAC, miss_seed=MISS_SEED
        ),
        strategy=strategy,
        venue_by_symbol=vmap,
        label="stress_miss_10pct",
        run_id=new_run_id(f"eval-{sample_id}-miss"),
    )
    n_primary = len(next(iter(bars_by_symbol.values()))) if bars_by_symbol else 0
    cut = int(n_primary * SPLIT_FRAC)
    return {
        "ok": True,
        "place_orders": False,
        "source": EVAL_SOURCE,
        "sample_id": sample_id,
        "md_label": md_label,
        "not_a_forecast": True,
        "split": {
            "frac_in_sample": SPLIT_FRAC,
            "rule": "first 70% of 15m bars by time, last 30% holdout; cut never searched",
            "n_bars_full": n_primary,
            "n_bars_in_sample": cut,
            "n_bars_holdout": max(0, n_primary - cut),
        },
        "full": full.as_dict(),
        "in_sample": ins.as_dict(),
        "holdout": hold.as_dict(),
        "stress": {
            "2x_fees": fee2.as_dict(),
            "1bar_entry_delay": delay.as_dict(),
            "miss_10pct_entries": miss.as_dict(),
            "miss_seed": MISS_SEED,
        },
        "disclaimer": (
            "research only. not_a_forecast. named-window / similar-regime ≠ future performance. "
            "do not headline PnL. do not promote to Phase C or live from this score."
        ),
    }


def _cache_path(data_dir: Path, sample_id: str, symbol: str, bar: str) -> Path:
    safe = symbol.replace("/", "_")
    return Path(data_dir) / "eval_cache" / f"{sample_id}_{safe}_{bar}.jsonl"


def _try_load_cache(path: Path, symbol: str, bar: str) -> list[Bar]:
    from atlas.paper.md import load_jsonl_candles, PaperDataError

    if not path.is_file() or path.stat().st_size <= 0:
        return []
    try:
        return load_jsonl_candles(path, symbol=symbol, bar=bar)
    except PaperDataError:
        return []


def load_similar_bars(
    cfg: Any,
    data_dir: Path,
    *,
    client: Any | None = None,
    pause_s: float = 0.12,
) -> tuple[dict[str, list[Bar]], dict[str, list[Bar]], dict[str, str], str]:
    summary = latest_replay_summary(data_dir)
    windows = windows_from_replay_summary(summary) if summary else {}
    if not windows:
        raise ReplayError("no similar-regime replay summary; run replay+shadow first")
    rest = (getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip("/")
    own = False
    http = client
    if http is None:
        import httpx

        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
        own = True
    bars_15: dict[str, list[Bar]] = {}
    bars_1h: dict[str, list[Bar]] = {}
    vmap: dict[str, str] = {}
    try:
        for key, win in windows.items():
            md = str(win.get("md_inst_id") or md_inst_for_venue(cfg, key)[1])
            cache = _cache_path(data_dir, "similar", md, "15m")
            cached = _try_load_cache(cache, md, "15m")
            start_ms = int(win["start_ms"])
            end_ms = int(win["end_ms"])
            if cached:
                b15 = [b for b in cached if start_ms <= b.ts_open_ms and b.ts_close_ms <= end_ms]
                from atlas.paper.md import resample_1h

                b1h = resample_1h(b15)
            else:
                pad = 48 * 60 * 60 * 1000
                b15_all, b1h, err = fetch_venue_history(
                    http,
                    md,
                    rest_base=rest,
                    start_ms=start_ms - pad,
                    end_ms=end_ms + 1,
                    pause_s=pause_s,
                )
                if err and not b15_all:
                    raise ReplayError(f"similar {key}: {err}")
                b15 = [b for b in b15_all if start_ms <= b.ts_open_ms and b.ts_close_ms <= end_ms]
                if b15:
                    persist_candles(cache, b15)
            if not b15:
                continue
            sym = b15[0].symbol
            bars_15[sym] = b15
            bars_1h[sym] = list(b1h)
            vmap[sym] = key
    finally:
        if own and http is not None:
            http.close()
    if not bars_15:
        raise ReplayError("similar-regime window produced no bars")
    return bars_15, bars_1h, vmap, "DOGE-USD + xperp MD 310404 (similar-regime June)"


def load_named_bars(
    cfg: Any,
    data_dir: Path,
    window_id: str,
    *,
    client: Any | None = None,
    pause_s: float = 0.12,
) -> tuple[dict[str, list[Bar]], dict[str, list[Bar]], dict[str, str], str]:
    win = parse_windows_arg(window_id)[0]
    rest = (getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip("/")
    cache = _cache_path(data_dir, window_id, RESEARCH_SPOT_MD, "15m")
    cached = _try_load_cache(cache, RESEARCH_SPOT_MD, "15m")
    if cached:
        b15 = [
            b
            for b in cached
            if win.start_ms <= b.ts_open_ms and b.ts_close_ms <= win.end_ms_exclusive
        ]
        from atlas.paper.md import resample_1h

        b1h = resample_1h(b15)
        err = None
    else:
        own = False
        http = client
        if http is None:
            import httpx

            http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
            own = True
        try:
            b15, b1h, err = fetch_closed_history(
                http,
                RESEARCH_SPOT_MD,
                start_ms=win.start_ms,
                end_ms=win.end_ms_exclusive,
                rest_base=rest,
                pause_s=pause_s,
            )
        finally:
            if own and http is not None:
                http.close()
        if b15:
            persist_candles(cache, b15)
    if not b15:
        raise ReplayError(f"named window {window_id} empty ({err})")
    return (
        {RESEARCH_SPOT_MD: b15},
        {RESEARCH_SPOT_MD: b1h},
        {RESEARCH_SPOT_MD: "spot"},
        f"research MD {RESEARCH_SPOT_MD} (not OMS DOGE-USD); window {win.label}",
    )


def run_paper_eval(
    cfg: Any,
    *,
    samples: list[str],
    data_dir: str | Path = "data",
    pause_s: float = 0.12,
    client: Any | None = None,
    bars_by_sample: dict[str, tuple[dict[str, list[Bar]], dict[str, list[Bar]], dict[str, str], str]]
    | None = None,
) -> dict[str, Any]:
    settings = shadow_settings(cfg)
    strategy = strategy_from_app_config(cfg)
    root = Path(data_dir)
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    samples = expand_window_ids(list(samples))
    for sid in samples:
        key = sid.strip()
        try:
            if bars_by_sample and key in bars_by_sample:
                b15, b1h, vmap, label = bars_by_sample[key]
            elif key in ("similar", "similar-regime"):
                b15, b1h, vmap, label = load_similar_bars(
                    cfg, root, client=client, pause_s=pause_s
                )
            elif key in NAMED_WINDOWS:
                b15, b1h, vmap, label = load_named_bars(
                    cfg, root, key, client=client, pause_s=pause_s
                )
            else:
                raise ReplayError(f"unknown sample {key!r}")
            row = evaluate_bars(
                sample_id=key,
                bars_by_symbol=b15,
                bars_1h_by_symbol=b1h,
                settings=settings,
                strategy=strategy,
                venue_by_symbol=vmap,
                md_label=label,
            )
        except ReplayError as exc:
            errors.append(f"{key}:{exc}")
            row = {
                "ok": False,
                "sample_id": key,
                "place_orders": False,
                "error": str(exc),
                "not_a_forecast": True,
            }
        results.append(row)
        out = reports_dir / f"eval_{key}.json"
        out.write_text(
            json.dumps(redact_record(row), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
    bundle = {
        "ok": any(r.get("ok") for r in results),
        "place_orders": False,
        "source": EVAL_SOURCE,
        "not_a_forecast": True,
        "samples": results,
        "errors": errors,
        "disclaimer": (
            "research only. expectancy after costs is not a forecast and not a Phase C/live gate."
        ),
    }
    (reports_dir / "eval_bundle.json").write_text(
        json.dumps(redact_record(bundle), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return bundle


def render_eval_markdown(
    bundle: dict[str, Any],
    *,
    heading: str = "13 — Paper eval (Phase D-lite)",
    extra_intro: str | None = None,
) -> str:
    lines = [
        f"# {heading.lstrip('# ').strip()}",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live from this score.",
        "",
    ]
    if extra_intro:
        lines.append(extra_intro.rstrip())
        lines.append("")
    lines.extend(
        [
            "Primary score: **expectancy after costs** on the €200 paper book. Split is chronological 70/30 (cut never searched). Stress uses the same engine path (2× fees, 1-bar entry delay, 10% missed entries seed 20260903).",
            "",
            "Named-window / similar-regime ≠ future performance. BreakoutV1 params were not retuned.",
            "",
        ]
    )
    for sample in bundle.get("samples") or []:
        sid = sample.get("sample_id")
        lines.append(f"## {sid}")
        lines.append("")
        if not sample.get("ok"):
            lines.append(f"Skipped: `{sample.get('error')}`. No fake fills.")
            lines.append("")
            continue
        lines.append(f"MD: {sample.get('md_label')}")
        split = sample.get("split") or {}
        lines.append(
            f"Bars: full {split.get('n_bars_full')} · IS {split.get('n_bars_in_sample')} · holdout {split.get('n_bars_holdout')}."
        )
        lines.append("")
        lines.append(
            "| Slice | n_trades | n_would_place | n_kill_days | expectancy after costs (€/trade) | max DD (€) | fee drag (€) | turnover/book |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for key, title in (
            ("full", "full"),
            ("in_sample", "in-sample 70%"),
            ("holdout", "holdout 30%"),
        ):
            m = sample.get(key) or {}
            exp = m.get("expectancy_after_costs_eur")
            exp_s = "—" if exp is None else f"{exp:.4f}"
            tnb = m.get("turnover_vs_book")
            tnb_s = "—" if tnb is None else f"{tnb:.2f}"
            lines.append(
                f"| {title} | {m.get('n_trades')} | {m.get('n_would_place')} | {m.get('n_kill_days')} | {exp_s} | {m.get('max_dd_eur')} | {m.get('fee_drag_eur')} | {tnb_s} |"
            )
        lines.append("")
        lines.append("Win rate (secondary):")
        for key, title in (("full", "full"), ("in_sample", "IS"), ("holdout", "holdout")):
            m = sample.get(key) or {}
            wr = m.get("win_rate")
            wr_s = "—" if wr is None else f"{100 * wr:.1f}%"
            lines.append(f"- {title}: {wr_s}")
        lines.append("")
        lines.append("Stress (full sample):")
        lines.append("")
        lines.append("| Stress | n_trades | expectancy after costs | max DD (€) | fee drag (€) |")
        lines.append("|---|---:|---:|---:|---:|")
        stress = sample.get("stress") or {}
        for key, title in (
            ("2x_fees", "2× fees"),
            ("1bar_entry_delay", "1-bar entry delay"),
            ("miss_10pct_entries", "10% missed entries"),
        ):
            m = stress.get(key) or {}
            exp = m.get("expectancy_after_costs_eur")
            exp_s = "—" if exp is None else f"{exp:.4f}"
            lines.append(
                f"| {title} | {m.get('n_trades')} | {exp_s} | {m.get('max_dd_eur')} | {m.get('fee_drag_eur')} |"
            )
        lines.append("")
        lines.append("`not_a_forecast: true`.")
        lines.append("")
    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not a Phase C recommendation.")
    lines.append("- Not a live-trading recommendation.")
    lines.append("- Not a claim that the locked breakout has edge.")
    lines.append("")
    return "\n".join(lines) + "\n"


def load_eval_reports(reports_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(reports_dir)
    if not root.is_dir():
        return []
    bundle = root / "eval_bundle.json"
    if bundle.is_file():
        try:
            raw = json.loads(bundle.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("samples"), list):
                return list(raw["samples"])
        except (OSError, json.JSONDecodeError):
            pass
    out: list[dict[str, Any]] = []
    for p in sorted(root.glob("eval_*.json")):
        if p.name == "eval_bundle.json":
            continue
        try:
            row = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(row, dict):
            out.append(row)
    return out
