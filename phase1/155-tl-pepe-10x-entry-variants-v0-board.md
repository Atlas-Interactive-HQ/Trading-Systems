# 155 — TL-PEPE-10X-ENTRY-VARIANTS-v0 · paper expectancy board

**Stance:** LABELED RESEARCH paper. `not_a_forecast: true`. Never places orders.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft ≠ arm · Scalp **PAUSED** · `place_orders: false` · no live PEPE.
**Trial:** `TL-PEPE-10X-ENTRY-VARIANTS-v0` · window `SHADOW_PEPE_XPERP_155_v0`.
**Lock card:** `/workspace/briefs/LOCK-TL-PEPE-10X-ENTRY-VARIANTS-v0-2026-09-18.md` §3 **LOCKED**.

> Soft ≠ arm · Dual HARD_PASS **N/A** (single window) · **not a forecast** · no S1 DOGE transplant · no USDT-proxy.

---

## 1. MD confirm (Ops native · no USDT-proxy)

| Inst | n_bars | first_ts_open_utc | last_ts_open_utc | gaps |
|------|--------|-------------------|------------------|------|
| PEPE-USD_UM_XPERP-310404 | 4089 | 2026-04-01T04:00:00Z | 2026-09-18T12:00:00Z | 0 contiguous |

Ops path: `/workspace/ts-live-ops/md/pepe-xperp-155/` · listing-limited (listTime ~2026-04-01).
Repo symlink: `data/paper/candles/pepe_xperp_155/` → Ops.

## 2. Window lock (pre-score)

| Field | Value |
|-------|-------|
| window_id | `SHADOW_PEPE_XPERP_155_v0` |
| warmup_from | `2026-04-01T04:00:00Z` |
| scored_start | `2026-04-02T01:00:00Z` (≥21 bars after first; EMA21/RSI14/RVOL20 valid) |
| end_exclusive | `2026-09-18T00:00:00Z` (SAH-style exclusive end) |
| length_days | 168.96 (≥90 OK=True) |
| listing_limited | true · contiguous · no USDT-proxy |
| size_ct | 225 (mid ~200–250) · ctVal=1000000.0 · 10× iso note |
| costs | 5+5 bps · fill next-open · SL honor intrabar |

## 3. Per-arm table E1–E4

| Arm | TP | n | exp $/t | exp R | term $ | BH $ | fee $ | mix (W/L/wr) | occ | n_forced | SL/TP | verdict |
|-----|----|---|---------|-------|--------|------|-------|--------------|-----|----------|-------|---------|
| E1 | TP_3R | 38 | 2.46662171 | 0.21267373 | 93.731625 | 21.699 | 25.518375 | 12/26/0.31578947 | 0.19852035 | 0 | 26/12 | `Window_PASS` |
| E2 | TP_5R | 37 | 2.08599324 | 0.23920589 | 110.136375 | 21.699 | 26.7075 | 8/29/0.21621622 | 0.28532676 | 1 | 29/8 | `Window_PASS` |
| E3 | TP_3R | 21 | 2.98167857 | 0.27980136 | 62.61525 | 21.699 | 13.88475 | 7/14/0.33333333 | 0.13292232 | 0 | 14/7 | `Window_PASS` |
| E4 | TP_5R | 15 | -4.382475 | -0.25612303 | -65.737125 | 21.699 | 9.487125 | 2/13/0.13333333 | 0.20887793 | 0 | 13/2 | `FAIL` |

**Verdict rule:** Window_PASS iff completed expectancy after costs > 0 (document n). Else FAIL. Dual HARD N/A. Soft ≠ arm always.

## 4. Gate summary

| Arm | Verdict | Dual HARD | Soft≠arm |
|-----|---------|-----------|----------|
| E1 | Window_PASS | N/A (single window) | true |
| E2 | Window_PASS | N/A (single window) | true |
| E3 | Window_PASS | N/A (single window) | true |
| E4 | FAIL | N/A (single window) | true |

- WINDOW_PASS: ['E1', 'E2', 'E3']
- FAIL: ['E4']
- HARD_PASS (dual): [] — N/A
- SOFT_NOTE: []

## 5. Integrity

- `config/default.yaml` sha256: `5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef`
- `place_orders: false` · Scalp PAUSED · no live PEPE · no S1 DOGE transplant · no grind
- Native PEPE xperp MD only · usdt_proxy=false
- BH = fixed 225 ct buy-hold on scored window (benchmark only)

## 6. Paths

- Results JSON: `results/tl_pepe_10x_entry_variants_v0.json`
- Registry: `phase1/registry/155-tl-pepe-10x-entry-variants-v0-preregister.json`
- This note: `phase1/155-tl-pepe-10x-entry-variants-v0-board.md`
- Walker: `src/atlas/paper/tl_pepe_10x_entry_variants_v0.py`
- MD: `data/paper/candles/pepe_xperp_155/` → Ops `/workspace/ts-live-ops/md/pepe-xperp-155/`

*End board. Paper only. Soft ≠ arm. not_a_forecast. STOP.*
