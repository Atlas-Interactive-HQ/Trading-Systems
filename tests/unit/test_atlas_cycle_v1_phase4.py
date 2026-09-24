"""Phase 4 package checks. Docs and the gate summary. No edge pass.

Does not re-run the synthetic walks. Those numbers stay in the Phase 2 and
Phase 3 docs. This file checks that the final package still says so.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

DOCS = Path("docs/atlas_cycle_v1")
SCRIPT = Path("scripts/run_atlas_cycle_v1_gate_summary.py")
DEFAULT_YAML = Path("config/default.yaml")
PINNED_SHA = "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"


def _summary():
    spec = importlib.util.spec_from_file_location("gate_summary", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gate_table_statuses_stay_honest() -> None:
    module = _summary()
    rows = module.parse_gate_table((DOCS / "GATE_STATUS.md").read_text(encoding="utf-8"))
    assert module.validate(rows) is None
    by_id = {row["id"]: row["status"] for row in rows}
    assert by_id["G6"] == "INSUFFICIENT_EVIDENCE"
    assert by_id["G7"] == "INSUFFICIENT_EVIDENCE"
    assert by_id["G8"] == "INSUFFICIENT_EVIDENCE"
    assert by_id["G9"] == "INSUFFICIENT_EVIDENCE"
    assert by_id["G10"] == "FAIL"
    assert by_id["G11"] == "PENDING_FORWARD_EVIDENCE"
    assert by_id["G14"] == "PASS"
    assert by_id["G15"] == "PASS"
    assert by_id["G16"] == "INSUFFICIENT_EVIDENCE"
    broken = [dict(row) for row in rows]
    broken[6]["status"] = "PASS"
    assert module.validate(broken) is not None


def test_gate_summary_script_prints_and_refuses_live(tmp_path: Path) -> None:
    paper = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert paper.returncode == 0, paper.stderr
    payload = json.loads(paper.stdout)
    assert len(payload) == 17
    assert payload[7]["status"] == "INSUFFICIENT_EVIDENCE"
    live = subprocess.run(
        [sys.executable, str(SCRIPT), "--execution-mode", "LIVE"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert live.returncode == 2
    assert "LIVE" in (live.stdout + live.stderr).upper()
    assert live.stdout == ""


def test_final_package_docs_and_default_yaml() -> None:
    comparison = (DOCS / "FINAL_COMPARISON.md").read_text(encoding="utf-8")
    opened = (DOCS / "OPEN_EVIDENCE.md").read_text(encoding="utf-8")
    modules = (DOCS / "MODULE_STATUS.md").read_text(encoding="utf-8")
    runbook = (DOCS / "PAPER_RUNBOOK.md").read_text(encoding="utf-8")
    assert "synthetic exploration" in comparison
    assert "DOGE-only paper candidate skeleton" in comparison
    assert "INSUFFICIENT_EVIDENCE" in comparison
    assert "-0.79689688" in comparison
    assert "-0.37567744" in comparison
    assert "0.09970840" in comparison
    assert "5.94558006" in comparison
    assert "PENDING_FORWARD_EVIDENCE" in opened
    assert "Elapsed forward calendar days: **0**" in opened
    assert "200 OOS DOGE cycles" in opened
    assert "300 OOS scalps" in opened
    assert "30 calendar days" in opened
    assert "listing_verified" in opened
    assert "DOGE paper path | ON" in modules
    assert "Scalp strategy | OFF" in modules
    assert "LIVE execution | OFF" in modules
    assert "BTC auto-buy, live | OFF" in modules
    assert "200, 500 en 1000" in runbook
    assert "Ctrl-C" in runbook
    assert "geen 30 dagen" in runbook.lower() or "0 forward-kalenderdagen" in runbook
    digest = hashlib.sha256(DEFAULT_YAML.read_bytes()).hexdigest()
    assert digest == PINNED_SHA
