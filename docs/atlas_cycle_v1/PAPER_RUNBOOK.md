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
python -m pytest tests/unit/test_atlas_cycle_v1_settlement.py tests/unit/test_atlas_cycle_v1_gates.py -q
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

## Leesvolgorde

1. `docs/atlas_cycle_v1/CURRENT_STATE.md` — wat bekend was op 2026-09-24, inclusief **ONBEKEND**.
2. `docs/atlas_cycle_v1/FEASIBILITY.md` — waarom live vol systeem niet kan.
3. `docs/atlas_cycle_v1/DESIGN_DECISIONS.md` — hergebruik versus nieuw, en de §18-rekenregels.
4. `docs/atlas_cycle_v1/GATE_STATUS.md` — eerlijke PASS / FAIL / INSUFFICIENT_EVIDENCE / PENDING_FORWARD_EVIDENCE.

Forward paper blijft **PENDING_FORWARD_EVIDENCE** tot er een echt vooruitlopend paper-journaal is. Deze smoke telt daar niet voor.
