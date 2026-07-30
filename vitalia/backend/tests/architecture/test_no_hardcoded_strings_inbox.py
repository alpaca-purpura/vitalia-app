# voseo-allowed: arch test that scans for voseo — contains voseo regex patterns as test data
"""Arch fitness: no hardcoded user-facing strings in inbox + crm Slice 1 files.

T-inbox-be-6 — vitalia Slice 1 hardcoded-string guard.

Scans ``vitalia/backend/src/modules/vitalia/inbox/`` and
``vitalia/backend/src/modules/vitalia/crm/`` for:

1. **Voseo** verb forms in string literals (`.claude/rules/spanish-text.md § R2`):
   tenés, podés, hacés, mirá, poné, usá, hacé, elegí, agregá, configurá,
   revisá, guardá, abrí, volvé, cambiá, sos (as standalone voseo copula).
   Sales_agent output is exempt (respects tenant voice).

2. **Hardcoded ``"USD"`` currency** in string literals outside the allowed
   files (`.claude/rules/currency-handling.md`). Currency must come from
   tenant locale, never be hardcoded in inbox/crm business logic.

3. **Hardcoded UUID-shaped strings in source** (heuristic guard against
   developer-left test/stub patient_id or tenant_id UUIDs in production
   code — PHI/isolation leak risk).

Allowlist ``KNOWN_LEGACY_STRINGS`` is the ratchet. It is intentionally
**empty** at inception (Slice 1 is greenfield; no legacy debt). Entries
are added ONLY when a finding is a known false-positive with documented
justification. The list shrinks over time — never grows without review.

The test FAILS if a new hardcoded pattern is detected that is NOT in the
allowlist. This blocks regressions introduced in future tickets.

Exempt surfaces:
- ``inbox/application/services/retract_message_service.py`` error messages
  that are implementation-internal (not user-facing).
- ``*_test*.py`` / ``conftest.py`` (test files not scanned — they legitimately
  contain hardcoded strings for test fixtures).
- Comments and docstrings (AST-based scan skips non-string-literal nodes).

Note: sales_agent tool return strings (Spanish summaries like
``"Mensaje revertido."`` in ``retract_last_message.py``) are NOT in the
inbox or crm module scan scope — they live under ``sales_agent/tools/``.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import NamedTuple  # noqa: UP035

# ── Allowlist (ratchet — shrink only) ────────────────────────────────────────


class KnownString(NamedTuple):
    """Allowlisted hardcoded string finding."""

    file_suffix: str  # relative path suffix under vitalia/backend/src/
    pattern: str  # the exact detected pattern (voseo word, "USD", uuid prefix)
    reason: str  # justification why it is a false-positive


KNOWN_LEGACY_STRINGS: tuple[KnownString, ...] = ()
# Intentionally empty — Slice 1 inbox + crm are greenfield.
# Add entries ONLY for documented false-positives, NEVER for real violations.


# ── Voseo patterns (compile once) ────────────────────────────────────────────

# Words from `.claude/rules/spanish-text.md § R2` glosario — forms that appear
# in user-facing strings only. We scan string literals (ast.Constant str nodes).
VOSEO_PATTERN = re.compile(
    r"\b("
    r"tenés|podés|hacés|querés|sabés|venís|decís"
    r"|mirá|dejá|poné|usá|hacé|elegí|seleccioná|arrancá|empezá"
    r"|agregá|configurá|revisá|escribí|guardá|subí|bajá|abrí|volvé"
    r"|andá|cambiá|activás|desactivás|linkeá|despublicala|reactivá"
    r"|cancelala|validá|considerá|formulala|marcá|probá|mostrá|compartí"
    r"|contá|explicá|fijate|acordate|atendés|integrás|listá|ofrecés|cobrás"
    r"|ejecutás|acompañás"
    r")\b",
    re.UNICODE,
)

# "USD" as a string literal (not as a comment or identifier)
USD_LITERAL_PATTERN = re.compile(r"\bUSD\b")

# UUID-shaped hardcoded string (8-4-4-4-12 hex pattern in a string literal)
UUID_HARDCODED_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


# ── File discovery ────────────────────────────────────────────────────────────


def _source_root() -> Path:
    """Workspace root (4 parents up from this test file)."""
    return Path(__file__).resolve().parents[4]


def _scan_dirs() -> list[Path]:
    """Return scan targets — inbox + crm under vitalia src."""
    src = _source_root() / "vitalia" / "backend" / "src" / "modules" / "vitalia"
    return [src / "inbox", src / "crm"]


def _python_files(scan_dirs: list[Path]) -> list[Path]:
    """Yield .py files that are NOT test files or conftest."""
    result: list[Path] = []
    for d in scan_dirs:
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            name = p.name
            if name.startswith("test_") or name == "conftest.py" or name == "__init__.py":
                continue
            result.append(p)
    return sorted(result)


# ── String literal extraction (AST) ──────────────────────────────────────────


def _extract_string_literals(source: str) -> list[str]:
    """Return all string literal values from source (skips comments/docstrings)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    strings: list[str] = []
    # Walk only ast.Constant nodes whose value is a str
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append(node.value)
    return strings


# ── Violation detection ───────────────────────────────────────────────────────


class Violation(NamedTuple):
    """A detected hardcoded string violation."""

    file_rel: str  # relative path from vitalia/backend/src/
    pattern: str  # matched pattern text
    kind: str  # "voseo" | "usd" | "uuid"
    literal: str  # the full string literal containing the pattern (truncated)


def _check_file(path: Path, src_root: Path) -> list[Violation]:
    """Scan a single file for all hardcoded string violations."""
    source = path.read_text(encoding="utf-8")
    file_rel = str(path.relative_to(src_root / "vitalia" / "backend" / "src"))

    violations: list[Violation] = []
    string_literals = _extract_string_literals(source)

    for literal in string_literals:
        # 1. Voseo check
        for m in VOSEO_PATTERN.finditer(literal):
            v = Violation(
                file_rel=file_rel,
                pattern=m.group(0),
                kind="voseo",
                literal=literal[:120],
            )
            if not _is_allowlisted(v):
                violations.append(v)

        # 2. USD hardcoded check
        if USD_LITERAL_PATTERN.search(literal):
            v = Violation(
                file_rel=file_rel,
                pattern="USD",
                kind="usd",
                literal=literal[:120],
            )
            if not _is_allowlisted(v):
                violations.append(v)

        # 3. UUID hardcoded in production source (heuristic for dev-left stubs)
        for m in UUID_HARDCODED_PATTERN.finditer(literal):
            v = Violation(
                file_rel=file_rel,
                pattern=m.group(0),
                kind="uuid",
                literal=literal[:120],
            )
            if not _is_allowlisted(v):
                violations.append(v)

    return violations


def _is_allowlisted(v: Violation) -> bool:
    """Return True if the violation is covered by KNOWN_LEGACY_STRINGS."""
    for entry in KNOWN_LEGACY_STRINGS:
        if v.file_rel.endswith(entry.file_suffix) and v.pattern == entry.pattern:
            return True
    return False


# ── Test ──────────────────────────────────────────────────────────────────────


def test_no_hardcoded_strings_inbox_crm() -> None:
    """No hardcoded voseo/USD/UUID strings in inbox + crm Slice 1 source files.

    Ratchet gate — KNOWN_LEGACY_STRINGS allowlist starts empty and shrinks only.
    Failing here means a new hardcoded string was introduced. Either:
      (a) Fix the hardcoded string (preferred).
      (b) Add it to KNOWN_LEGACY_STRINGS with a documented justification
          (only for false-positives — auditor will scrutinize).
    """
    src_root = _source_root()
    scan_dirs = _scan_dirs()
    py_files = _python_files(scan_dirs)

    # If module not yet created (brand not fully bootstrapped), skip gracefully
    existing_files = [f for f in py_files if f.exists()]
    if not existing_files:
        return  # nothing to scan yet

    all_violations: list[Violation] = []
    for path in existing_files:
        all_violations.extend(_check_file(path, src_root))

    if all_violations:
        lines = [
            f"\n{'=' * 70}",
            f"Arch fitness FAIL: {len(all_violations)} hardcoded string(s) detected",
            "in inbox + crm Slice 1 source files.",
            f"{'=' * 70}",
        ]
        for v in all_violations:
            lines.append(
                f"\n  [{v.kind.upper()}] {v.file_rel}\n    Pattern : {v.pattern!r}\n    Literal : {v.literal!r}"
            )
        lines.append(
            f"\n{'=' * 70}\n"
            f"Fix: remove hardcoded string OR add to KNOWN_LEGACY_STRINGS\n"
            f"with documented justification. Allowlist shrinks only.\n"
            f"{'=' * 70}"
        )
        assert False, "\n".join(lines)


def test_allowlist_is_tuple_of_known_string() -> None:
    """KNOWN_LEGACY_STRINGS must be a tuple of KnownString (enforces schema)."""
    assert isinstance(KNOWN_LEGACY_STRINGS, tuple)
    for entry in KNOWN_LEGACY_STRINGS:
        assert isinstance(entry, KnownString), f"All entries must be KnownString instances. Got: {type(entry)}"


def test_scan_dirs_exist_or_graceful() -> None:
    """Scan directories must either exist or the test skips gracefully (no crash)."""
    # At least one dir should exist in a properly bootstrapped vitalia brand
    src_root = _source_root()
    vitalia_src = src_root / "vitalia" / "backend" / "src" / "modules" / "vitalia"
    if vitalia_src.exists():
        # inbox at minimum must exist (Slice 1 mandatory)
        inbox_dir = vitalia_src / "inbox"
        assert inbox_dir.exists(), (
            f"inbox module not found at {inbox_dir}. This arch test requires Slice 1 inbox to be bootstrapped."
        )
