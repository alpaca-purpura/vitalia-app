"""Fitness gate: vitalia copilot extractors inherit shared base.

T-extractors-1 acceptance A1 verifier (per ``06-tickets.yaml::T-extractors-1``).

Any class under ``src/modules/vitalia/copilot/extractors/`` whose name ends in
``Extractor`` MUST inherit from
``luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator`` so
wave scheduling + progress emission stays DRY across modules and brands per
``.claude/rules/anti-duplication.md`` SSoT.

This is the vitalia-scoped twin of the AISALESHT
``tests/architecture/test_extraction_orchestrator_inheritance.py`` (which
scopes to ``src/modules/*/application/*.py``). The vitalia layout puts
extractors under ``copilot/extractors/`` (vertical-medical-specific D1 DDD),
so the directory glob differs.

Detection: parse each ``*.py`` AST under the extractors directory; any
``ClassDef`` whose name ends in ``Extractor`` must declare an allowed base.

Ratchet allowlist (``KNOWN_EXTRACTORS_WITHOUT_BASE``) shrink-only.
"""

from __future__ import annotations

import ast
from pathlib import Path

EXTRACTORS_DIR = Path(__file__).resolve().parents[2] / "src" / "modules" / "vitalia" / "copilot" / "extractors"

# Ratchet allowlist — class names permitted to skip the base class.
# Must shrink only. Justify any addition with a commit message reference.
KNOWN_EXTRACTORS_WITHOUT_BASE: set[str] = set()

_ALLOWED_BASES = {
    "BaseExtractionOrchestrator",
    "base_orchestrator.BaseExtractionOrchestrator",
    "extraction.BaseExtractionOrchestrator",
    "luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator",
}


def _collect_extractor_classes() -> list[tuple[str, ast.ClassDef]]:
    """Return (rel_path, class_node) for every ``*Extractor`` class under
    ``vitalia/copilot/extractors/``.

    Excludes private helpers (leading underscore) and the ``_schemas.py``
    file (Pydantic models, not orchestrators).
    """
    results: list[tuple[str, ast.ClassDef]] = []
    if not EXTRACTORS_DIR.exists():
        return results
    for py_file in sorted(EXTRACTORS_DIR.glob("*.py")):
        # Skip schema / private helper modules.
        if py_file.name in {"__init__.py", "_schemas.py"}:
            continue
        rel = py_file.relative_to(EXTRACTORS_DIR.parents[3])  # repo-root relative
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith("Extractor"):
                results.append((str(rel), node))
    return results


def test_every_vitalia_extractor_inherits_base() -> None:
    """Every ``*Extractor`` class MUST declare BaseExtractionOrchestrator."""
    violations: list[str] = []

    for rel, cls in _collect_extractor_classes():
        base_names = {ast.unparse(b) for b in cls.bases}
        if base_names & _ALLOWED_BASES:
            continue
        if cls.name in KNOWN_EXTRACTORS_WITHOUT_BASE:
            continue
        violations.append(
            f"{rel}:{cls.name} — does not inherit from BaseExtractionOrchestrator. "
            "Subclass it from luana_core_extraction.base_orchestrator so wave "
            "scheduling + progress emission stays DRY across modules.",
        )

    assert not violations, "\n".join(violations)
