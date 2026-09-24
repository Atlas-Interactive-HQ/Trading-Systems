# PAPER RUNBOOK — Atlas Cycle v1

**LIVE HOLD.** Geen live orders. Geen echte transfers. Geen BTC verkopen. Bestaande PEPE-bescherming niet aanraken.

`PAPER_PASS ≠ live-arm`. Soft PASS ≠ arm. Een groene unit test is geen toestemming om te armen.

`config/default.yaml` niet wijzigen. Cycle-config staat alleen in `config/strategies/atlas_cycle_v1.yaml`.

## Wat dit pad wel en niet doet

- Wel: Decimal-ledger, settlement na een platte cycle, unitized risk, synthetische DOGE-smoke, weigering van `LIVE`.
- Niet: OKX private fills, nieuws/LLM in de beslissing, shorts, averaging-down, martingale, auto coin rotation, ML.
- Scalp staat uit (`scalp.enabled: false`) tot feasibility meer is dan **INSUFFICIENT_EVIDENCE**.
- Live vrije USDC uit de upload van 2026-09-24 (0.69) is **INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM**. De smoke print dat label. Verhoog de leverage niet om het te omzeilen.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Python ≥ 3.12. Geen API-keys. De smoke doet geen netwerk.

## Tests

```bash
python -m pytest tests/unit/test_atlas_cycle_v1_settlement.py tests/unit/test_atlas_cycle_v1_gates.py tests/unit/test_atlas_cycle_v1_phase2.py tests/unit/test_atlas_cycle_v1_phase3.py -q
```

De settlement-file is het rekenvoorbeeld: verlies → carryforward L, gedeeltelijk herstel → nog geen BTC-pending, daarna B = 0.60 × W. Zie `DESIGN_DECISIONS.md`.

## Smoke (alleen PAPER / BACKTEST)

```bash
python scripts/run_atlas_cycle_v1_smoke.py
python scripts/run_atlas_cycle_v1_smoke.py --execution-mode BACKTEST --out /tmp/atlas_cycle_v1_smoke.json
```

Succes print `PAPER smoke ok` en schrijft een summary. De candles zijn synthetisch (`atlas.paper.atlas_cycle.synthetic`), geen venue-cache. Een ronde die op de stop eindigt is een wiring-check, geen edge.

LIVE moet stoppen met een non-zero exit **voordat** er een fill of summary bestaat:

```bash
python scripts/run_atlas_cycle_v1_smoke.py --execution-mode LIVE
echo $?   # 2
```

Hetzelfde geldt voor `ATLAS_CYCLE_EXECUTION_MODE=LIVE` zonder expliciete paper-override.

Artefacts onder `results/atlas_cycle_v1/runs/` zijn gitignored.

## DOGE-only backtest (Variant A)

Zelfde LIVE HOLD. Scalp blijft uit. Leverage blijft 2x. `config/default.yaml` niet aanraken.

```bash
python scripts/run_atlas_cycle_v1_doge_backtest.py
python scripts/run_atlas_cycle_v1_doge_backtest.py --out /tmp/atlas_cycle_v1_phase2.json
```

Het script loopt `synthetic_doge_regimes`: 16.000 gesloten 15m-bars, chronologisch 50% dev / 25% val / 25% holdout. Eerste retest en direct-breakout draaien apart, met dezelfde exits en kosten. De yaml-warm-up van 250 gesloten 4H-bars blijft staan.

De smoke hierboven is een kortere wiring-check (`warmup_4h` 60 alleen in dat proces). Die telt niet als de Phase 2-score.

Uitkomst en tabellen: `docs/atlas_cycle_v1/PHASE2_DOGE.md`. Op deze synthetische reeks is het label **INSUFFICIENT_EVIDENCE** (minder dan 200 OOS-cycles, bootstrap-interval kruist 0). `entry_frozen` blijft `first_retest`. Holdout is berekend en is geen PASS. Er is geen publieke DOGE-download; `fetch_okx_history_candles` wordt niet aangeroepen.

LIVE stopt weer vóór een fill:

```bash
python scripts/run_atlas_cycle_v1_doge_backtest.py --execution-mode LIVE
echo $?   # 2
```

## Scalp-vergelijking (Phase 3, paper)

Zelfde LIVE HOLD. `scalp.enabled` blijft false. `entry_frozen` blijft `first_retest`. Leverage blijft 2x / max 3x. `config/default.yaml` niet aanraken.

```bash
python scripts/run_atlas_cycle_v1_phase3.py
python scripts/run_atlas_cycle_v1_phase3.py --out /tmp/atlas_cycle_v1_phase3.json
```

Het script loopt dezelfde synthetische DOGE-reeks als Phase 2, plus uitgelijnde synthetische scalp-paden voor SOL, ETH en PEPE. Varianten B en C draaien in-memory. De yaml blijft variant A en `SCALP_OFF`.

Uitkomst: `docs/atlas_cycle_v1/PHASE3_SCALP.md` en `docs/atlas_cycle_v1/PHASE3_ABCD.md`. Op deze reeks is het label **INSUFFICIENT_EVIDENCE** (0 OOS scalps, 20 OOS DOGE-cycles). De freeze is **SCALP_OFF**. Holdout is geen PASS. Er is geen publieke candle-download.

LIVE stopt vóór een fill:

```bash
python scripts/run_atlas_cycle_v1_phase3.py --execution-mode LIVE
echo $?   # 2
```

## Leesvolgorde

1. `docs/atlas_cycle_v1/CURRENT_STATE.md` — wat bekend was op 2026-09-24, inclusief **ONBEKEND**.
2. `docs/atlas_cycle_v1/FEASIBILITY.md` — waarom live vol systeem niet kan.
3. `docs/atlas_cycle_v1/DESIGN_DECISIONS.md` — hergebruik versus nieuw, en de §18-rekenregels.
4. `docs/atlas_cycle_v1/GATE_STATUS.md` — eerlijke PASS / FAIL / INSUFFICIENT_EVIDENCE / PENDING_FORWARD_EVIDENCE.
5. `docs/atlas_cycle_v1/PHASE2_DOGE.md` — DOGE-ablatie op synthetische regimes. Geen live-arm.
6. `docs/atlas_cycle_v1/PHASE3_SCALP.md` en `PHASE3_ABCD.md` — scalp-kandidaten en A/B/C/D. Freeze blijft `SCALP_OFF`.

Forward paper blijft **PENDING_FORWARD_EVIDENCE** tot er een echt vooruitlopend paper-journaal is. Deze smoke telt daar niet voor.
