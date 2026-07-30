"""Architecture fitness: no `/home/chris/` hardcoded paths in test files (BF2 ratchet 2026-05-16).

Cross-brand portability gate. Tests must not contain absolute paths tied to
any specific developer's home directory (`/home/chris/` is a legacy username
from the pre-multibrand-reorg laptop). Hardcoded paths break baselines on:

- New dev machines (different user)
- CI runners (different home)
- Worktrees and parallel sessions

Replacement patterns (per BF2 2026-05-16):

- Workspace-relative (preferred for test artifacts inside the repo):
  ``_WORKSPACE_ROOT = next(p for p in Path(__file__).resolve().parents
                            if (p / "AGENTS.md").is_file())``
- AISALESHT museum (legacy `ap_sales_agent/` reference outside repo):
  ``Path(os.environ.get("AISALESHT_PATH", "/home/chalreme/Documentos/ap_sales_agent"))``
  with skipif when the path is absent (dev machines without the museum).
- Cosmetic doc examples: ``$WS/`` placeholder.

Allowlist: this file (which documents the offending substring as a literal),
plus an empty allowlist tuple (shrink-only ratchet — additions require an
explicit justification commit).
"""

from __future__ import annotations

from pathlib import Path

_WORKSPACE_ROOT: Path = Path(__file__).resolve().parents[3]
_LEGACY_USER_PATH = "/home/chris/"

# Shrink-only allowlist. This test file itself appears here because it
# documents the offending substring as a literal. Add to this set ONLY with
# explicit `// allowlist-justification:` commit message rationale.
_ALLOWLIST: frozenset[Path] = frozenset({
    _WORKSPACE_ROOT / "core" / "tests" / "architecture" / "test_no_hardcoded_chris_paths_in_tests.py",
})


def _iter_test_files() -> list[Path]:
    """Discover every Python test file across the workspace."""
    test_files: list[Path] = []
    # All `tests/` directories under any brand or core package
    for tests_dir in _WORKSPACE_ROOT.glob("*/backend/tests"):
        test_files.extend(tests_dir.rglob("test_*.py"))
        test_files.extend(tests_dir.rglob("smoke_*.py"))
        test_files.extend(tests_dir.rglob("conftest.py"))
    for tests_dir in _WORKSPACE_ROOT.glob("core/luana-core-*/tests"):
        test_files.extend(tests_dir.rglob("test_*.py"))
        test_files.extend(tests_dir.rglob("conftest.py"))
    for tests_dir in _WORKSPACE_ROOT.glob("core/tests"):
        test_files.extend(tests_dir.rglob("test_*.py"))
        test_files.extend(tests_dir.rglob("conftest.py"))
        test_files.extend(tests_dir.rglob("_generate_*.py"))
    # Filter out __pycache__
    return [p for p in test_files if "__pycache__" not in p.parts]


def test_no_hardcoded_chris_paths_in_test_files() -> None:
    """Test files must not contain hardcoded `/home/chris/` absolute paths.

    Use ``_WORKSPACE_ROOT`` derivation, env vars (e.g. ``AISALESHT_PATH``)
    or relative paths. See module docstring for canonical replacements.
    """
    offenders: list[str] = []
    for path in _iter_test_files():
        if path in _ALLOWLIST:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if _LEGACY_USER_PATH in text:
            line_numbers = [
                i + 1 for i, line in enumerate(text.splitlines()) if _LEGACY_USER_PATH in line
            ]
            offenders.append(
                f"  {path.relative_to(_WORKSPACE_ROOT)} (lines: {line_numbers[:3]}{'...' if len(line_numbers) > 3 else ''})"
            )

    assert not offenders, (
        f"Found `/home/chris/` hardcoded paths in {len(offenders)} test file(s). "
        "Replace with `_WORKSPACE_ROOT` derivation (see test_no_hardcoded_chris_paths_in_tests.py "
        "module docstring for canonical patterns). Offenders:\n" + "\n".join(offenders)
    )
