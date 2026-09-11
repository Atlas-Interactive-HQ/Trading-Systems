# 105 — Portfolio philosophy + CORE-MAJOR-v1 (later)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** ≤€20 **HALTED**. Soft PASS ≠ arm. No hyperopt. No R1–R7 coin-pick.
**Board:** step **F** of [`106`](./106-research-governance-board.md) — **only after** Mid/S1 SHADOW + robustness ([`101`](./101-shadow-contiguous-methodology.md), [`103`](./103-edge-vs-luck-stress.md)).

**Not scored in this PR.**

---

## STRATEGY GREEN ≠ PORTFOLIO GREEN

A sleeve can be a research GREEN CANDIDATE and still deserve **allocation 0**.

| Statement | Meaning |
|-----------|---------|
| Strategy green | The **locked card** survived SHADOW + edge-vs-luck + stress under the pre-registered gates. Still `not_a_forecast`. Still Soft PASS ≠ arm. |
| Portfolio green | The **book** (Core / Mid / Scalp / HFT / CASH) has a validated reason to take risk in that sleeve at €200 scale. |
| No validated edge | Allocation **0**. The sleeve is **CASH**. **CASH is valid.** |

Do not fill Core €140 / Mid €40 / Scalp €20 because those numbers exist in [`38`](./38-eur200-three-stream-confirmation.md). Those are **sleeves**, not mandates to be long. An empty Mid while #71 is still SHADOW-pending is correct.

Code: `atlas.research.portfolio.sleeve_allocation`.

---

## CORE-MAJOR-v1 — later hypothesis

**Id:** `core_major_v1_btc_eth_identical_params_slow_trend_vol_targeted`

| Lock | Detail |
|------|--------|
| Assets | **BTC + ETH** (not a DOGE R1–R7 coin-pick) |
| Params | **Identical** on both names |
| Style | Slow trend |
| Sizing | Vol-targeted (formula locked in the future lock note, not here) |
| Status | **later** — registered only |
| Prerequisites | Mid #71 SHADOW + robustness; S1 SHADOW + robustness ([`103`](./103-edge-vs-luck-stress.md)) |
| Forbidden now | Scoring, R1–R7 on BTC/ETH as a hunt, param asymmetry, using P4a/P4b liquidity ranks as a Core coin-pick |

CORE-MAJOR is **not** CORE-R1, not C3, not a Donchian continuation, not a rescue of C1/C2. Donchian C3/C4 stay **STOPPED** ([`94`](./94-core-r1-lock.md)).

Do not start CORE-MAJOR because Core V2 PASS on R1–R7 looked large. That panel is rise-biased and one-interval dominated ([`90`](./90-evaluation-integrity-audit.md), [`97`](./97-rise-panel-core-r1-ema-atr-trail-1d.md)).

---

## Honesty / invalidation

- Do not score CORE-MAJOR in this PR.
- Do not treat CASH as “doing nothing wrong” in a shame sense — it is the default.
- Do not invent a BTC/ETH panel or a vol-target multiplier here.
- `not_a_forecast: true`. `place_orders: false`.
