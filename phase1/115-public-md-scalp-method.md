# 115 — Public-MD Scalp paper method (method-only lock)

**Stance:** Research / method lock only. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`.
**Live:** ≤€20 **HALTED** until **session-ja**. Soft PASS ≠ arm. **This PR does not arm.**
**Path:** `public_md_scalp_paper_v1` / lock_id `public_md_scalp_method`.
**Scoring:** **FORBIDDEN** in this PR. No rise_panel R1–R7 on memes. No Soft PASS gate applied to this path.
**S1:** DOGE Dual Thrust / RVOL numbers **MUST NOT** be copied onto any meme `instId`.
**114:** PR [#97](https://github.com/Atlas-Interactive-HQ/Trading-Systems/pull/97) is the multi-coin **watch** overlay — **115 is the public-MD method**, not a second watch lock. Cross-link; do not overwrite 114.

Code constants: `atlas.paper.public_md_scalp` — `PUBLIC_MD_SCALP_METHOD` / id `public_md_scalp_method`.

---

## Why this lock

Coordinator LOCK A+B (2026-09-12): document a **METHOD-ONLY** public market-data Scalp **paper** path.

- Data = OKX EEA **public** `market/candles` + public `instruments` / `ticker` only.
- **No** signed demo OMS. **No** live POST.
- Candle availability ≠ edge. Snapshot ≠ expectancy.
- Public MD ≠ DEMO_CLEAR ≠ arm.

**Soft PASS ≠ arm. HALTED. not_a_forecast.**

---

## Rule card (LOCKED — method only)

| Field | Lock |
|-------|------|
| **lock_id** | `public_md_scalp_method` |
| **path_name** | `public_md_scalp_paper_v1` |
| **Data** | `https://eea.okx.com` public REST only (candles + instruments/ticker) |
| **Bars** | **1H** primary for Scalp paper; **4H / 1D** allowed as regime **context**, not a score |
| **Costs** | Do not invent a new cost model. If fills are mentioned, cite existing `PaperSettings` **5+5 bps** (`fee_rate: 0.0005`, `slippage_bps: 5.0` in `config/default.yaml`) — **115 does not re-score with it** |
| **Compounding** | Paper sleeve-cash-after-closed-wins only; **no** martingale / **no** size-up-on-loss |
| **3×SL→28m** | [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) applies **once a meme system exists** — do **not** invent PEPE/PUMP params here |
| **Scoring** | **FORBIDDEN** — no R1–R7, no Soft PASS gate on this path |
| **S1 transplant** | **False** — never copy DOGE Dual Thrust / RVOL onto meme `instId`s |
| **demo_oms / place_orders / live_arm** | **False** |
| **default_yaml_untouched** | **True** |
| **halted** | **True** (until session-ja) |
| **soft_pass_neq_arm** | **True** |
| **not_a_forecast** | **True** |
| **score_forbidden** | **True** |

### Explicit non-goals

- Not a second [`114`](./114-scalp-multi-coin-watch-2026-09-12.md) watch lock (that is PR #97).
- Not Mid **#71** / Core **CASH** / BTC hold changes ([`113`](./113-kaje-architecture-2026-09-12.md)).
- Not an expectancy, panel €, or PEPE-like PnL invention.
- Not pagination beyond the measured one-page candle facts below.

---

## Universe (Research screen + Ops DEMO_BLOCK)

Do **not** invent `instId`s. Dual-list = spot USDC + listed X-Perp MD id.

### Primary dual-list

| Spot | X-Perp (public MD) | Notes |
|------|--------------------|-------|
| `PUMP-USDC` | `PUMP-USD_UM_XPERP-310404` | DEMO_BLOCK on demo key; public-MD path still allowed |
| `TRUMP-USDC` | `TRUMP-USD_UM_XPERP-310704` | DEMO_BLOCK on demo key; public-MD path still allowed |
| `WIF-USDC` | `WIF-USD_UM_XPERP-310815` | DEMO still pending Ops |

### Secondary dual-list

| Spot | X-Perp (public MD) | Snapshot note (2026-09-12 ~01:55 UTC) |
|------|--------------------|----------------------------------------|
| `SHIB-USDC` | `SHIB-USD_UM_XPERP-310801` | Thin X-Perp on that snapshot |
| `BONK-USDC` | `BONK-USD_UM_XPERP-310725` | Wide X-Perp spread on that snapshot |

### Public-only OK

| Spot | X-Perp (public MD) | Notes |
|------|--------------------|-------|
| `PEPE-USDC` | `PEPE-USD_UM_XPERP-310404` | DEMO_BLOCK / place `51001` — **not** primary paper-OMS; **public-MD OK** |

### Spot-only watch (no X-Perp this probe)

- `BOME-USDC`
- `FLOKI-USDC`

### Exclude / not on EEA catalogue this probe

| Class | Names |
|-------|-------|
| **Exclude** | **DOGE** (Mid #71 family) |
| **Not on EEA catalogue this probe** | FARTCOIN, BRETT, POPCAT, MOG |

---

## Measured method facts (cite only these)

Public REST `https://eea.okx.com` **2026-09-12**:

| Fact | Measured |
|------|----------|
| instruments + ticker screen | ~**01:55 UTC** (spot spread/vol snapshot) — already used for rank; **do not** turn snapshot into expectancy |
| candles smoke `limit=5` | **1H / 4H / 1D** `code=0` for all names above (spot + listed X-Perp) |
| One page candles `limit=300` bar=`1H` ~**02:00 UTC** | `n=300`, newest `2026-09-12T02:00:00Z`, oldest_on_this_page `2026-08-30T15:00:00Z` for PUMP/TRUMP/WIF/PEPE/SHIB/BONK **USDC** and PUMP/WIF **X-Perp** |
| Older history | **UNVERIFIED** (no pagination beyond one page) |
| Demo-tradable | **PEPE, PUMP, TRUMP = DEMO_BLOCK** (Ops: demo `/account/instruments` empty + place `51001`). **WIF / SHIB / BONK** DEMO still **pending Ops**. Public MD ≠ DEMO_CLEAR ≠ arm |

**Do not invent history before `2026-08-30T15:00:00Z`.** Do not treat candle availability as edge.

---

## Relation to board / other locks

| Item | Status under this lock |
|------|-------------------------|
| [`114`](./114-scalp-multi-coin-watch-2026-09-12.md) / PR #97 | **Watch** overlay — cross-link only; 115 does not overwrite |
| Scalp **S1** provisional DEV ([`108`](./108-dev-board-research-lock.md)) | Untouched; **no** transplant onto memes |
| Mid **#71** primary | Untouched |
| Core **CASH** / BTC hold ([`113`](./113-kaje-architecture-2026-09-12.md)) | Untouched |
| [`112`](./112-scalp-s1-3sl-28m-cooldown-lock.md) 3×SL→28m | Applies later **once a meme system exists** — not param invention here |
| Soft PASS | Still **≠ arm**; **not** applied as a gate on this path |

---

## What this PR does / does not

**Does**

- Lock the public-MD Scalp **paper method** (`public_md_scalp_paper_v1` / `public_md_scalp_method`).
- Freeze constants + `card()` in `atlas.paper.public_md_scalp`.
- Record measured candle / DEMO_BLOCK facts and mark deeper history **UNVERIFIED**.
- Cross-link 114 (watch) vs 115 (method).

**Does not**

- Change `config/default.yaml` or flip `pepe_enabled`.
- Place orders / arm live / open a signed demo OMS path.
- Score or invent expectancy / panel € / PEPE-like PnL.
- Apply Soft PASS as a gate; promote Soft PASS to arm.
- Transplant S1 Dual Thrust / RVOL onto any meme `instId`.
- Edit PR #97 / open a second 114.
- Invent history before `2026-08-30T15:00:00Z` or paginate beyond the measured page.

---

## Honesty / invalidation

- Method-only ≠ implemented meme Scalp system ≠ GREEN CANDIDATE.
- Soft PASS ≠ arm. HALTED until session-ja.
- Public MD ≠ DEMO_CLEAR ≠ arm. DEMO_BLOCK on PEPE/PUMP/TRUMP does not revoke public-MD research.
- Candle `code=0` / `n=300` ≠ edge. Snapshot spreads ≠ expectancy.
- Older candle history remains **UNVERIFIED** until a later measured pagination PR.
- Do not attach R1–R7 metrics or invented PnL to this note.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED. method-only. lock-only.
