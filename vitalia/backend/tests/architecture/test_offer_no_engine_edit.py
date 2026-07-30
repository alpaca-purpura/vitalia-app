"""Architecture gate (shrink-only ratchet): offer/ engine import boundary.

Rationale:
  The vitalia offer module SHOULD consume the engine (luana_core_offer_studio)
  ONLY via the adapter layer (infrastructure/adapters/) and its declared ports.
  Direct `luana_core_offer_studio.domain.*` imports from application layer or
  API layer are technical debt pointing toward tighter encapsulation.

  This test is a SHRINK-ONLY ratchet: new files outside the allowlist that
  import engine domain symbols directly will fail. As adapters are refactored
  to fully encapsulate engine types, remove entries from KNOWN_VIOLATIONS.

  Goal progression:
    Sub-phase A (now):  6 files in allowlist   → PASS
    Sub-phase B:        Reduce to adapters only → remove app/ + api/ entries
    Future:             0 violations            → remove this file

Validator ID: be_arch_offer_engine_boundary (04-validators.yaml T-8)
story-origin: vitalia-fase2-lisa-servicios T-8
"""
# cap: lisa.servicios

from __future__ import annotations

import re
from pathlib import Path

import pytest

WS = Path(__file__).parents[4]  # → luana-vitalia/
OFFER_SRC = WS / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "offer"

# ---------------------------------------------------------------------------
# Shrink-only allowlist (documented current state — Sub-phase A baseline)
# ---------------------------------------------------------------------------
# Files that currently import luana_core_offer_studio.domain.* directly.
# Each entry carries a comment explaining why it's currently necessary.
# To reduce: refactor the file to consume via infrastructure/adapters/, then
# remove its entry here. A removed entry that still has the import = FAIL.
# ---------------------------------------------------------------------------

KNOWN_VIOLATIONS: frozenset[str] = frozenset(
    {
        # Adapter layer — expected to import engine types directly (wraps them)
        "vitalia/backend/src/modules/vitalia/offer/infrastructure/adapters/offer_engine_adapter.py",
        "vitalia/backend/src/modules/vitalia/offer/infrastructure/adapters/knowledge_source_adapter.py",
        # Port declaration — defines the engine contract at the application boundary
        "vitalia/backend/src/modules/vitalia/offer/application/ports/offer_engine_port.py",
        # Factory service — creates engine Offer objects; candidate for delegation to adapter
        "vitalia/backend/src/modules/vitalia/offer/application/services/medical_offer_factory.py",
        # Catalog service — uses OfferStatus enum for filtering; refactoring target B
        "vitalia/backend/src/modules/vitalia/offer/application/services/catalog_service.py",
        # DTOs — re-exports OfferStatus to avoid engine leak through API; refactoring target B
        "vitalia/backend/src/modules/vitalia/offer/api/dtos.py",
    }
)

# Pattern matches any import of luana_core_offer_studio (engine package)
_ENGINE_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+luana_core_offer_studio", re.MULTILINE)


def _relative(p: Path) -> str:
    """Return path relative to workspace root as forward-slash string."""
    return p.relative_to(WS).as_posix()


def test_offer_src_dir_exists() -> None:
    """offer/ source directory must exist (sanity check)."""
    assert OFFER_SRC.exists(), f"offer/ source not found at {OFFER_SRC}. Check workspace root resolution."


def test_no_new_direct_engine_domain_imports() -> None:
    """No file outside the KNOWN_VIOLATIONS allowlist imports luana_core_offer_studio directly.

    NEW violations = files importing engine domain directly that are NOT in
    KNOWN_VIOLATIONS. To fix: consume engine symbols via
    infrastructure/adapters/offer_engine_adapter.py instead.

    Shrink protocol: once you encapsulate a file's engine dependency behind the
    adapter, REMOVE its entry from KNOWN_VIOLATIONS above — the test will keep
    passing AND the allowlist shrinks.
    """
    if not OFFER_SRC.exists():
        pytest.skip("offer/ source not yet created")

    new_violations: list[str] = []

    for py_file in OFFER_SRC.rglob("*.py"):
        rel = _relative(py_file)
        if rel in KNOWN_VIOLATIONS:
            continue  # allowed per current baseline
        content = py_file.read_text(encoding="utf-8")
        if _ENGINE_IMPORT_RE.search(content):
            new_violations.append(rel)

    assert not new_violations, (
        "New direct luana_core_offer_studio imports detected outside the allowlist.\n"
        "Consume engine types via infrastructure/adapters/offer_engine_adapter.py instead.\n"
        "If this is an intentional new adapter file, add it to KNOWN_VIOLATIONS with rationale.\n\n"
        "New violations:\n" + "\n".join(f"  {v}" for v in new_violations)
    )


def test_known_violations_still_exist() -> None:
    """Verify each entry in KNOWN_VIOLATIONS actually imports engine types.

    If this test fails for a file, it means that file was refactored to no
    longer import engine types directly — REMOVE it from KNOWN_VIOLATIONS.
    This makes the ratchet shrink automatically when encapsulation improves.
    """
    if not OFFER_SRC.exists():
        pytest.skip("offer/ source not yet created")

    stale_entries: list[str] = []

    for known_rel in sorted(KNOWN_VIOLATIONS):
        known_path = WS / known_rel
        if not known_path.exists():
            stale_entries.append(f"{known_rel} (file not found)")
            continue
        content = known_path.read_text(encoding="utf-8")
        if not _ENGINE_IMPORT_RE.search(content):
            stale_entries.append(f"{known_rel} (no longer imports engine — remove from KNOWN_VIOLATIONS)")

    assert not stale_entries, (
        "Stale entries in KNOWN_VIOLATIONS — the following files no longer import\n"
        "luana_core_offer_studio directly. Remove them from the allowlist to shrink it:\n\n"
        + "\n".join(f"  {e}" for e in stale_entries)
    )
