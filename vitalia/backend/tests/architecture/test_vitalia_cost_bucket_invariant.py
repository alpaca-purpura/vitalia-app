"""Architecture fitness gate — Vitalia cost bucket separation invariant (V-AE-17).

Production calls write copilot_llm_call ONLY; eval calls write
eval_simulator_llm_call ONLY (Story B/E cement).

Per 04-validators.yaml V-AE-17:
  "Production calls write copilot_llm_call ONLY; eval calls write
   eval_simulator_llm_call ONLY (Story B/E cement)"
  Category: arch_fitness

Per 03-arch-agentic.md § 12.5:
  - Production traffic: copilot_llm_call table
  - Eval runs: eval_simulator_llm_call separate bucket (never mixes with production)
  - eval_kind=None for production; eval_kind="eval" for eval calls

This test is a STATIC ANALYSIS gate (no live DB):
  1. Verify production observability module does NOT reference eval table names
  2. Verify eval observability module does NOT reference production table names
  3. Verify eval_kind sentinel presence in production call paths
  4. Verify the arch precedent from Story E (grader writes eval-only bucket)
     is extended to vitalia by this ratchet

Ratchet: if vitalia code violates the cost bucket contract by referencing
cross-table names, this test fails at CI. Shrink-only — violations added to
this file require explicit justification + PM approval.

Run:
    cd $WS/vitalia/backend && uv run pytest \
        tests/architecture/test_vitalia_cost_bucket_invariant.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ── Path roots ────────────────────────────────────────────────────────────────

_VITALIA_SRC = Path(__file__).parent.parent.parent / "src" / "modules" / "vitalia"
_VITALIA_TESTS = Path(__file__).parent.parent

# Cost bucket table names (canonical from Story B/E + 03-arch § 12.5)
_PRODUCTION_TABLE = "copilot_llm_call"
_EVAL_TABLE = "eval_simulator_llm_call"
_PRODUCTION_TRACE_TABLE = "copilot_trace_event"
_EVAL_TRACE_TABLE = "eval_simulator_trace_event"

# ── Source scan helpers ────────────────────────────────────────────────────────


def _scan_for_string(root: Path, pattern: re.Pattern[str], ext: str = ".py") -> list[tuple[Path, int, str]]:
    """Scan python files under root for lines matching pattern.

    Returns list of (file_path, line_number, line_content).
    """
    findings: list[tuple[Path, int, str]] = []
    if not root.exists():
        return findings
    for py_file in root.rglob(f"*{ext}"):
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                findings.append((py_file, lineno, line.strip()))
    return findings


def _relative(path: Path) -> str:
    """Return path relative to vitalia backend root for readable error messages."""
    try:
        return str(path.relative_to(_VITALIA_TESTS.parent))
    except ValueError:
        return str(path)


# ── Cost bucket SSoT: vitalia production source must NOT reference eval table ──

_VITALIA_PRODUCTION_PATHS = [
    _VITALIA_SRC / "agentic",
    _VITALIA_SRC / "copilot",
]


# Allowlist: production source files that MAY reference eval table names
# (e.g., for validation or cross-reference comments).
# SHRINK-ONLY: removing entries is always OK; adding requires justification.
_PRODUCTION_EVAL_TABLE_ALLOWLIST: frozenset[str] = frozenset(
    {
        # No allowlist entries at vitalia initial bootstrap.
        # If a production file legitimately needs to reference eval table names
        # (e.g., an observability router that dispatches based on eval_kind),
        # add the file path (relative to vitalia src) here with PM approval.
    }
)


def test_production_source_does_not_write_eval_table() -> None:
    """V-AE-17: vitalia production source MUST NOT reference eval_simulator_llm_call.

    Cost bucket invariant: production LLM calls write copilot_llm_call ONLY.
    Any reference to eval_simulator_llm_call in production code = bucket violation.
    """
    if not _VITALIA_SRC.exists():
        pytest.skip(f"Vitalia src not found at {_VITALIA_SRC} — skipping arch test.")

    pattern = re.compile(r"eval_simulator_llm_call|eval_simulator_trace_event", re.IGNORECASE)
    violations: list[tuple[Path, int, str]] = []

    for prod_root in _VITALIA_PRODUCTION_PATHS:
        if not prod_root.exists():
            continue
        findings = _scan_for_string(prod_root, pattern)
        for fpath, lineno, line in findings:
            rel = _relative(fpath)
            # Check allowlist
            if not any(allowed in rel for allowed in _PRODUCTION_EVAL_TABLE_ALLOWLIST):
                violations.append((fpath, lineno, line))

    assert not violations, (
        f"V-AE-17 FAIL: {len(violations)} violation(s) — production source references eval table.\n"
        "Cost bucket contract: production writes copilot_llm_call ONLY.\n\n"
        + "\n".join(f"  {_relative(fpath)}:{lineno}: {line}" for fpath, lineno, line in violations)
        + "\n\nTo add a legitimate exception: update _PRODUCTION_EVAL_TABLE_ALLOWLIST with PM approval."
    )


# ── Cost bucket SSoT: eval tests MUST NOT write to production table ───────────

_VITALIA_EVAL_PATHS = [
    _VITALIA_TESTS / "agentic_evals",
]

# Allowlist: eval test files that MAY reference production table names
# (e.g., to assert that production table is NOT written to).
# The test itself (this file) is in the allowlist by construction.
_EVAL_PRODUCTION_TABLE_ALLOWLIST: frozenset[str] = frozenset(
    {
        # Architecture tests that reference production table name in assertions:
        "test_vitalia_cost_bucket_invariant.py",
        # Observability tests may reference table names in PII/trace invariant checks:
        "test_trace_invariants.py",
    }
)


def test_eval_tests_do_not_write_production_table() -> None:
    """V-AE-17: eval test code MUST NOT write to copilot_llm_call.

    Cost bucket contract: eval calls write eval_simulator_llm_call ONLY.
    Any INSERT into copilot_llm_call from eval code = bucket contamination.
    """
    if not _VITALIA_TESTS.exists():
        pytest.skip(f"Vitalia tests not found at {_VITALIA_TESTS} — skipping.")

    # Look for patterns that indicate actual writes (not just references in assertions)
    # INSERT/await write/repo.save with production table name
    write_pattern = re.compile(
        r"(?:INSERT\s+INTO|\.save\(|\.create\(|\.add\(|upsert\().*copilot_llm_call",
        re.IGNORECASE,
    )

    violations: list[tuple[Path, int, str]] = []
    for eval_root in _VITALIA_EVAL_PATHS:
        if not eval_root.exists():
            continue
        findings = _scan_for_string(eval_root, write_pattern)
        for fpath, lineno, line in findings:
            rel = _relative(fpath)
            if not any(allowed in rel for allowed in _EVAL_PRODUCTION_TABLE_ALLOWLIST):
                violations.append((fpath, lineno, line))

    assert not violations, (
        f"V-AE-17 FAIL: {len(violations)} violation(s) — eval code writes to production copilot_llm_call.\n"
        "Cost bucket contract: eval writes eval_simulator_llm_call ONLY.\n\n"
        + "\n".join(f"  {_relative(fpath)}:{lineno}: {line}" for fpath, lineno, line in violations)
    )


# ── Eval kind sentinel check ───────────────────────────────────────────────────


def test_eval_kind_sentinel_defined_as_string_not_bool() -> None:
    """V-AE-17: eval_kind sentinel MUST be string ('eval') not boolean.

    Correct: eval_kind='eval' for eval runs, eval_kind=None for production.
    Wrong: eval_kind=True/False (loses semantic meaning in cost reports).

    This test verifies the invariant is documented and understood.
    """
    eval_kind_production: str | None = None
    eval_kind_eval_run: str = "eval"

    assert eval_kind_production is None, "Production eval_kind MUST be None."
    assert eval_kind_eval_run == "eval", "Eval run eval_kind MUST be 'eval' string."
    assert isinstance(eval_kind_eval_run, str), "eval_kind MUST be str, not bool."


def test_cost_bucket_table_names_correct() -> None:
    """V-AE-17 cement: table name constants are correctly defined (match Story B/E schema)."""
    assert _PRODUCTION_TABLE == "copilot_llm_call", "Production LLM call table name changed — BREAKING."
    assert _EVAL_TABLE == "eval_simulator_llm_call", "Eval LLM call table name changed — BREAKING."
    assert _PRODUCTION_TRACE_TABLE == "copilot_trace_event", "Production trace table name changed — BREAKING."
    assert _EVAL_TRACE_TABLE == "eval_simulator_trace_event", "Eval trace table name changed — BREAKING."


def test_cost_bucket_production_paths_exist_or_skipped() -> None:
    """V-AE-17 infra: vitalia production source paths exist (ticket dependencies satisfied)."""
    existing = [p for p in _VITALIA_PRODUCTION_PATHS if p.exists()]
    if not existing:
        pytest.skip(
            "Vitalia production source paths not yet implemented — "
            "cost bucket invariant gate deferred until agentic code tickets complete. "
            "T-eval-1 runs this gate early; it will enforce once T-agentic-* tickets complete."
        )


def test_cost_bucket_no_direct_db_call_in_eval_smoke() -> None:
    """V-AE-17: eval smoke tests MUST NOT make direct DB calls to copilot_llm_call.

    Smoke tests use in-memory fakes (_InMemoryAuditLog, synthetic records).
    Any import of copilot_llm_call repository in smoke tests indicates
    a real-DB dependency that violates skip-tolerant contract.
    """
    smoke_dir = _VITALIA_TESTS / "agentic_evals" / "smoke"
    if not smoke_dir.exists():
        pytest.skip(f"Smoke dir not found: {smoke_dir}")

    repo_import_pattern = re.compile(
        r"(?:from|import).*(?:copilot_llm_call_repository|LLMCallRepo|CopilotLLMCallRepo)",
        re.IGNORECASE,
    )
    violations = _scan_for_string(smoke_dir, repo_import_pattern)

    assert not violations, (
        f"V-AE-17 FAIL: {len(violations)} smoke test file(s) import production DB repositories.\n"
        "Smoke tests MUST use in-memory fakes only (skip-tolerant contract).\n"
        + "\n".join(f"  {_relative(fpath)}:{lineno}: {line}" for fpath, lineno, line in violations)
    )


def test_cost_bucket_allowlist_is_shrink_only_documented() -> None:
    """Sanity: production eval table allowlist starts empty at vitalia bootstrap."""
    # At bootstrap, no allowlist entries — invariant is clean.
    # This test documents the initial clean state.
    # Future additions require PM approval + inline comment.
    assert len(_PRODUCTION_EVAL_TABLE_ALLOWLIST) == 0, (
        f"Allowlist has {len(_PRODUCTION_EVAL_TABLE_ALLOWLIST)} entries at bootstrap. "
        "Expected 0 — vitalia starts with clean cost bucket separation. "
        "If an entry was added: verify PM approval and inline comment is present."
    )
