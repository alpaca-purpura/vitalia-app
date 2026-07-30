"""Architecture fitness: §3 protected surfaces NOT refactored (sha256 snapshot).

Per 03-arch.md §7.8 + sales-agent-expert SKILL.md §3.

13 files lift verbatim from AISALESHT backend/src/modules/sales_agent/.
Their sha256 hashes must match the captured snapshot
`_snapshots/sales_agent_protected_surfaces_v1.json` (post-sed + post-ruff
at lift moment T-1..T-15).

§3 surfaces are PRODUCTION-CRITICAL:
- Live ops Closer Studio API + WS + Streamlit dependencies
- SmartBufferService CPM tuned producción LATAM
- OutputManager.process_response chunking calibrated
- Enrollment service + domain + model + API end-to-end producción
- Webhook adapters (Telegram/WhatsApp/IG/Manychat) auth + signature frágil
- follow_up_engine cadence math + tz tenant
- PromptVersionModel DB-backed tenant override
- tool_call_dedup.py anti-loop post fbc79125

Tocar §3 → preguntar al usuario (sales-agent-expert SKILL.md §3 cardinal).

V-AG-8 validator. Hash-stable invariant — defensive cement.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

CORE_DIR = Path(__file__).parents[2]
SALES_AGENT_SRC = CORE_DIR / "luana-core-sales-agent" / "src" / "luana_core_sales_agent"
SNAPSHOT_PATH = CORE_DIR / "tests" / "architecture" / "_snapshots" / "sales_agent_protected_surfaces_v1.json"


def _load_snapshot() -> dict[str, str]:
    """Load snapshot JSON; strip `_metadata` key, return file → hash mapping."""
    data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_snapshot_file_exists():
    """Snapshot JSON file must exist (Story 7 T-18 captured)."""
    assert SNAPSHOT_PATH.exists(), (
        f"§3 protected surfaces snapshot missing: {SNAPSHOT_PATH}. Captured during Story 7 T-18 lift moment."
    )


def test_protected_surfaces_hash_stable():
    """All 13 canonical §3 files match captured sha256 hashes.

    Drift = refactor of protected surface = halt (per sales-agent-expert
    SKILL.md §3 cardinal: tocar §3 → preguntar al usuario).
    """
    expected = _load_snapshot()

    violations: list[str] = []
    missing: list[str] = []

    for relative_path, expected_hash in expected.items():
        full_path = SALES_AGENT_SRC / relative_path
        if not full_path.exists():
            missing.append(relative_path)
            continue
        actual_hash = _sha256(full_path)
        if actual_hash != expected_hash:
            violations.append(
                f"{relative_path}: expected {expected_hash[:16]}..., got {actual_hash[:16]}...",
            )

    assert not missing, "§3 protected surface FILE(S) MISSING (hash-stable invariant broken):\n" + "\n".join(missing)

    assert not violations, (
        "V-AG-8 violation: §3 protected surfaces HASH DRIFT detected.\n"
        "Per sales-agent-expert SKILL.md §3 cardinal: these files lift "
        "verbatim from AISALESHT. Tocar §3 → preguntar al usuario.\n\n"
        "Drift in:\n" + "\n".join(violations)
    )


def test_protected_surfaces_coverage_complete():
    """Snapshot covers all 13 canonical §3 files (per 03-arch.md §7.8)."""
    expected_count = 13
    actual = _load_snapshot()
    assert len(actual) == expected_count, (
        f"Snapshot expected to cover {expected_count} §3 files, got {len(actual)}. Update T-18 doc if scope changed."
    )
