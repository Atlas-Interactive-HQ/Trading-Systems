# 76 — Scalp-HFT v1 compact rule card

**Source:** Codex §23 · locked with [`75-scalp-hft-v1-design.md`](./75-scalp-hft-v1-design.md)  
**Mode:** PAPER ONLY · `not_a_forecast` · `config/default.yaml` untouched · live orders impossible by implementation

---

```
NAME              Scalp-HFT v1 / EMA-VAMP
MODE              PAPER ONLY
SIGNAL CLOCK      1 second (closed samples)
MARKET DATA       OKX ~100ms L2 books; top 5 levels used for VAMP
TREND             EMA12 / EMA21 on midpoint
EDGE              VAMP5 displacement → 60s z-score

LONG              EMA12 > EMA21
                  VAMP5 > mid
                  vamp_z >= +1.0
                  confirmed in 2 of last 3 seconds

SHORT             exact inverse
                  (EMA12 < EMA21; VAMP5 < mid; vamp_z <= -1.0; 2-of-3)

ENTRY             post-only at BBO
                  1s TTL
                  never chase
                  wait for terminal cancel before re-quote

LEVERAGE          isolated
                  highest verified allowed
                  absolute cap 10x
                  unverified → NO TRADE

SIZE              fixed normalized margin_unit = 1.0
                  one position
                  no compounding / no size-up after win or loss

HARD STOP         -20% net margin ROI  (= -1R)
HARD TP           +100% net margin ROI (= +5R)
SOFT EXIT         EMA invalidation OR vamp_z crosses 0
                  2-of-3 confirmation
TIME STOP         60 seconds
NORMAL EXIT       maker attempt up to 1s, then taker
HARD / KILL EXIT  immediate simulated taker
COOLDOWN          5 seconds

MARTINGALE        forbidden
PYRAMIDING        forbidden
R1–R7 TUNING      forbidden
LIVE ORDERS       impossible by implementation
DEFAULT.YAML      untouched
FORECAST STATUS   not_a_forecast
```

---

**Net margin ROI** includes mark PnL − fees − slippage − funding.  
**Layer A vs B:** see [`75`](./75-scalp-hft-v1-design.md) §13 and [`77`](./77-scalp-hft-v1-eval-plan.md). Soft PASS N/A until Layer B OKX forward paper.
