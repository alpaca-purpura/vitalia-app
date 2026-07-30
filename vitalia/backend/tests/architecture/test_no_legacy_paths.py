"""Architecture fitness: zero imports from legacy pre-multibrand-reorg paths.

Post multibrand reorg 2026-05-15, the path `backend/src/shared/` does NOT exist.
All shared abstractions live in `core/luana-core-*/` packages.

This test performs an AST + grep scan of vitalia backend source to ensure
no import references the legacy `backend.src.shared.*` or `backend.src.modules.core.*`
paths (which belonged to the pre-reorg single-brand Nicolify monolith).

If violations found → migrate import to appropriate `core/luana-core-*/` package.

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import ast
from pathlib import Path

# WS root is 5 levels up from this file:
# vitalia/backend/tests/architecture/test_no_legacy_paths.py
WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_SRC = WS_ROOT / "vitalia" / "backend" / "src"

# Legacy paths that MUST NOT be imported post multibrand-reorg 2026-05-15
LEGACY_IMPORT_PREFIXES: tuple[str, ...] = (
    # Pre-reorg shared lived here (now in core/luana-core-*/):
    "backend.src.shared",
    "backend.src.modules.core",
    # Absolute path references that would only work in legacy single-brand layout:
    "src.shared",  # still present if code accidentally uses relative to `backend/`
)

# Additional patterns detected via string scan (not AST) for safety:
LEGACY_PATH_STRINGS: tuple[str, ...] = (
    "from backend.src.shared",
    "import backend.src.shared",
    "from backend.src.modules.core",
    "import backend.src.modules.core",
)

# Known baseline violations (frozen at T-infra-4 creation — shrink-only per arch ratchet).
# Each entry is the relative path from WS_ROOT to the file.
KNOWN_LEGACY_PATH_VIOLATIONS: frozenset[str] = frozenset(
    [
        # Add violating files here if baseline scan finds them.
        # Format: "vitalia/backend/src/modules/vitalia/some/path.py"
    ]
)


def _get_py_sources() -> list[Path]:
    """Return all .py files under vitalia/backend/src/."""
    if not VITALIA_SRC.exists():
        return []
    return list(VITALIA_SRC.rglob("*.py"))


def _relative_path(p: Path) -> str:
    return str(p.relative_to(WS_ROOT))


class TestNoLegacyPaths:
    """Vitalia backend source must not reference legacy pre-multibrand-reorg paths."""

    def test_vitalia_src_exists(self) -> None:
        """Sanity: vitalia/backend/src/ must exist."""
        assert VITALIA_SRC.exists(), "vitalia/backend/src/ directory not found. Expected post multibrand-reorg layout."

    def test_no_legacy_backend_src_shared_imports(self) -> None:
        """No file may import from `backend.src.shared.*` (legacy pre-reorg path).

        Post multibrand reorg 2026-05-15, shared abstractions live in:
          - `core/luana-core-observability/` → sanitize_payload, BaseCallbackHandler
          - `core/luana-core-platform/` → TenantLocale, config, events
          - `core/luana-core-events/` → DomainEvent, outbox
          - `core/luana-core-extraction/` → BaseExtractionOrchestrator
          - etc.
        """
        violations: list[str] = []

        for py_file in _get_py_sources():
            source = py_file.read_text(encoding="utf-8")

            # String scan (catches dynamic imports and commented-out code that
            # was accidentally left uncommented):
            for legacy_pattern in LEGACY_PATH_STRINGS:
                if legacy_pattern in source:
                    rel = _relative_path(py_file)
                    if rel not in KNOWN_LEGACY_PATH_VIOLATIONS:
                        violations.append(f"{rel}: contains legacy import pattern '{legacy_pattern}'")

        assert violations == [], (
            "Legacy pre-multibrand-reorg import paths detected.\n"
            "All shared abstractions must be imported from core/luana-core-*/ packages.\n"
            "Per CLAUDE.md § 'Migración status 2026-05-15':\n\n"
            + "\n".join(violations)
            + "\n\nFix: replace `from backend.src.shared.X import Y` with "
            "the correct `from luana_core_X import Y` import.\n"
            "If this is a false positive, add the file to KNOWN_LEGACY_PATH_VIOLATIONS "
            "in test_no_legacy_paths.py (shrink-only ratchet)."
        )

    def test_no_ast_legacy_import_nodes(self) -> None:
        """AST-level scan: no import/from-import nodes reference legacy modules.

        More precise than string scan — catches aliased imports and
        from-import chains.
        """
        violations: list[str] = []

        for py_file in _get_py_sources():
            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue  # Syntax errors caught by ruff lint gate

            for node in ast.walk(tree):
                module_str: str | None = None

                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_str = alias.name
                        if any(module_str.startswith(p) for p in LEGACY_IMPORT_PREFIXES):
                            rel = _relative_path(py_file)
                            if rel not in KNOWN_LEGACY_PATH_VIOLATIONS:
                                violations.append(f"{rel}:{node.lineno}: legacy import `{module_str}`")

                elif isinstance(node, ast.ImportFrom):
                    module_str = node.module or ""
                    if any(module_str.startswith(p) for p in LEGACY_IMPORT_PREFIXES):
                        rel = _relative_path(py_file)
                        if rel not in KNOWN_LEGACY_PATH_VIOLATIONS:
                            violations.append(f"{rel}:{node.lineno}: legacy from-import `{module_str}`")

        assert violations == [], (
            "AST-level legacy import violations detected "
            "(post multibrand-reorg 2026-05-15):\n"
            + "\n".join(violations)
            + "\n\nMigrate to appropriate `luana_core_*` package import."
        )

    def test_no_src_shared_local_reference(self) -> None:
        """No vitalia source may reference `src.shared` local-style import.

        `src.shared` was valid inside the legacy single-brand `backend/` working
        directory. Post reorg, shared code lives in `luana_core_*` installed packages.
        """
        violations: list[str] = []

        for py_file in _get_py_sources():
            source = py_file.read_text(encoding="utf-8")

            # Check for local-style legacy pattern
            if "from src.shared" in source or "import src.shared" in source:
                rel = _relative_path(py_file)
                if rel not in KNOWN_LEGACY_PATH_VIOLATIONS:
                    violations.append(f"{rel}: references `src.shared` (legacy local-style import)")

        # Note: `src.modules.vitalia.*` local imports are OK — that is the brand module itself.
        # Only `src.shared` is the banned pattern.
        assert violations == [], (
            "Legacy `src.shared` import detected:\n"
            + "\n".join(violations)
            + "\n\nReplace with corresponding `luana_core_*` import "
            "per multibrand reorg 2026-05-15."
        )
