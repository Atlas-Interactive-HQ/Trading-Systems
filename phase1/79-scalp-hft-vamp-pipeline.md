# 79 — Scalp-HFT 1s VAMP-5 pipeline (Layer B books5 replay)

**Status:** engineering · **paper / metrics-only**  
**Lane:** Scalp-HFT Layer B (feature resample)  
**Forecast status:** `not_a_forecast`  
**Live execution:** forbidden (`PAPER_ONLY`; no private WS; no OMS)  
**Config:** `config/default.yaml` **untouched**  
**Upstream:** [#72](https://github.com/Atlas-Interactive-HQ/Trading-Systems/pull/72) design · [#73](https://github.com/Atlas-Interactive-HQ/Trading-Systems/pull/73) Layer B capture  
**Companions:** [`75`](./75-scalp-hft-v1-design.md) · [`76`](./76-scalp-hft-v1-rule-card.md) · [`77`](./77-scalp-hft-v1-eval-plan.md) · [`78`](./78-scalp-hft-layer-b-capture.md)

---

## 1. Goal

Replay captured OKX EEA `books5` JSONL for `DOGE-USD_UM_XPERP-310404` into a causal **1s closed-clock** feature series:

| Column | Definition |
|--------|------------|
| `mid` | `(best_bid + best_ask) / 2` |
| `vamp5` | `(Σ Pbid·Qask + Σ Pask·Qbid) / (ΣQbid+ΣQask)` top-5 |
| `vamp_edge_bps` | `10000 * (vamp5 - mid) / mid` |
| `vamp_z` | 60s rolling z-score of edge; **None / INVALID** if std ≤ 0 or warmup |
| `ema12` / `ema21` | EMA on mid; None until period samples |

**Schema = metrics only.** No fills, no PnL, no expectancy, no soft-PASS claim.

---

## 2. Code

| Path | Role |
|------|------|
| `src/atlas/scalp_hft/vamp.py` | VAMP / EMA / z-score + 1s resample + csv/parquet writers |
| `scripts/replay_scalp_hft_vamp1s.py` | CLI replay → `results/scalp_hft_v1/layer_b_samples/` |
| `tests/unit/test_scalp_hft_vamp.py` | Synthetic book frames (no network) |

Output default: `results/scalp_hft_v1/layer_b_samples/vamp1s_<inst>_<date>.{csv,parquet}`.  
Parquet is written when `pyarrow` is importable; CSV is always written (stdlib).

---

## 3. How to run

```bash
# Unit tests (no network)
pytest tests/unit/test_scalp_hft_vamp.py -q

# Replay smoke / date folder (gitignored raw under data/raw/okx_eea/)
python scripts/replay_scalp_hft_vamp1s.py --date 2026-09-11

# Explicit path
python scripts/replay_scalp_hft_vamp1s.py -i data/raw/okx_eea/2026-09-11/ws_books5.jsonl
```

If no `ws_books5.jsonl` exists, the script exits 2 and prints a capture hint:

```bash
python scripts/run_okx_public.py --capture --ws-only --duration-sec 30
```

---

## 4. Clock / staleness

1. Parse `raw.envelope.v1` `ws_books5` lines; skip subscribe/error frames.
2. Prefer book `ts` (else `exchange_ts` / `receive_ts`) → `ts_s = floor(ts_ms/1000)`.
3. Last update inside a UTC second wins for that closed second.
4. Empty seconds between first and last book second **carry forward** last book with `book_stale=true` (fail-closed for trading; still useful for feature continuity).
5. Insufficient top-5 → `vamp_valid=false`; EMAs only update when mid is finite.

Warmup: `vamp_z` needs 60 causal 1s edges; EMA12/21 need 12/21 mids. Short smoke captures will show `n_vamp_z_valid=0` — expected.

---

## 5. Smoke replay (this box, 2026-09-11)

Input: `data/raw/okx_eea/2026-09-11/ws_books5.jsonl` (PR #73 smoke; gitignored raw).

| Metric | Count |
|--------|------:|
| `n_samples_1s` | 45 |
| `n_vamp_valid` | 45 |
| `n_vamp_z_valid` | 0 (span ~44s < 60s z window — expected) |
| `n_ema12_ready` | 34 |
| `n_ema21_ready` | 25 |
| `n_book_stale` | 20 |

Wrote `results/scalp_hft_v1/layer_b_samples/vamp1s_DOGE-USD_UM_XPERP-310404_2026-09-11.{csv,parquet}` (local; not committed). **Metrics only — not expectancy.**

---

## 6. Explicit non-goals

- No Layer A R1–R7 scored HFT eval
- No paper OMS / simulator fills
- No `lock.json` hash freeze
- No mutation of Mid #71 or `config/default.yaml`
- No invented PnL under `results/scalp_hft_v1/R*/`
