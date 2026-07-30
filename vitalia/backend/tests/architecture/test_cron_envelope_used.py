"""Arch fitness: ALL vitalia cron-decorated functions MUST use @cron_envelope from engine.

Scans vitalia/backend/src/modules/vitalia/**/*.py for functions decorated with any
cron-like decorator (@idempotent_cron, custom schedule decorators, etc.) and verifies
that the ONLY accepted decorator is @cron_envelope imported from
``luana_core_platform.workers.cron_envelope``.

Ratchet pattern (shrink-only):
  KNOWN_LEGACY_CRONS = {<function_name>: <reason>}
  Add to this allowlist ONLY for pre-existing code that has not yet been migrated.
  Remove entries as each cron migrates to @cron_envelope. Allowlist NEVER grows.

Why this gate?
  Engine @cron_envelope provides:
    1. Idempotency deduplication (Redis-backed, best-effort)
    2. OTel tracing (graceful degrade)
    3. structlog audit on completion
    4. Sentry capture on exception (graceful degrade)
  Brand-local alternatives (@idempotent_cron, @cron_job, etc.) fragment this
  cross-cutting concern — engine abstraction SSoT enforced per anti-duplication.md.

T-3 — vitalia-slice-1-fidelizacion (arch fitness, production_code=false)
"""

from __future__ import annotations

import ast
from pathlib import Path

# ---------------------------------------------------------------------------
# Ratchet allowlist — SHRINK ONLY, never grow
# ---------------------------------------------------------------------------
# Format: {function_name: reason_string}
# Each entry is a legacy cron that has not yet been migrated to @cron_envelope.
# Remove when migrated; do NOT add new entries.
KNOWN_LEGACY_CRONS: dict[str, str] = {
    "lucas_weekly_recommendations": (
        "Uses brand-local @idempotent_cron — pre-dates engine cron_envelope lift (2026-05-20). "
        "Migration to @cron_envelope planned in vitalia-slice-1-fidelizacion T-6 follow-up."
    ),
}

# ---------------------------------------------------------------------------
# Decorator names that ARE NOT @cron_envelope — violations when detected
# ---------------------------------------------------------------------------
# Any function decorated with one of these is a violation UNLESS it appears
# in KNOWN_LEGACY_CRONS allowlist.
NON_ENGINE_CRON_DECORATORS: frozenset[str] = frozenset(
    [
        "idempotent_cron",  # brand-local _shared/workers/base.py (pre-lift legacy)
        "cron_job",  # generic naming that may appear in future code
        "periodic_task",  # celery-style
        "scheduled_task",  # custom patterns
        "arq_cron",  # alternative arq decorator names
    ]
)

# The ONLY accepted cron decorator (from engine)
ENGINE_CRON_DECORATOR = "cron_envelope"
ENGINE_CRON_IMPORT_MODULE = "luana_core_platform.workers.cron_envelope"


def _vitalia_worker_files() -> list[Path]:
    """Return all *.py files under vitalia workers directories.

    Scans both the pre-existing _shared/workers/jobs/ directory and the new
    fidelizacion module workers directory.
    """
    ws_root = Path(__file__).resolve().parents[4]  # workspace root
    vitalia_src = ws_root / "vitalia" / "backend" / "src"
    if not vitalia_src.exists():
        return []

    # Search across all workers/* directories in vitalia modules
    worker_dirs = [
        vitalia_src / "modules" / "vitalia" / "_shared" / "workers" / "jobs",
        vitalia_src / "modules" / "vitalia" / "fidelizacion" / "application" / "workers",
    ]

    files: list[Path] = []
    for worker_dir in worker_dirs:
        if worker_dir.exists():
            files.extend(p for p in worker_dir.rglob("*.py") if p.name != "__init__.py")

    # Also sweep any *.py with cron-like imports across all vitalia source
    for py_file in vitalia_src.rglob("*.py"):
        if py_file in files:
            continue
        source = py_file.read_text(encoding="utf-8")
        if any(dec in source for dec in NON_ENGINE_CRON_DECORATORS):
            files.append(py_file)

    return list({f for f in files})  # deduplicate


def _get_decorated_functions(tree: ast.Module) -> list[tuple[str, list[str]]]:
    """Extract (function_name, [decorator_names]) pairs from module AST.

    Returns only functions that have at least one decorator. Decorator names
    are extracted as either plain ``Name.id`` or ``Attribute.attr`` (for
    ``module.decorator`` style).
    """
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.decorator_list:
            continue
        dec_names = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                dec_names.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                dec_names.append(dec.attr)
            elif isinstance(dec, ast.Call):
                # @decorator_name(args...) style
                if isinstance(dec.func, ast.Name):
                    dec_names.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    dec_names.append(dec.func.attr)
        if dec_names:
            results.append((node.name, dec_names))
    return results


def _imports_engine_cron_envelope(source: str) -> bool:
    """Return True if the file imports cron_envelope from the engine package."""
    return ENGINE_CRON_IMPORT_MODULE in source and ENGINE_CRON_DECORATOR in source


class TestCronEnvelopeUsed:
    """Architecture gate: cron-decorated functions MUST use engine @cron_envelope.

    Ratchet policy:
      - Pass: all cron-decorated functions use @cron_envelope OR are in allowlist.
      - Fail: any cron-decorated function uses a non-engine decorator without allowlist entry.

    Shrink-only: KNOWN_LEGACY_CRONS shrinks as migrations happen; it never grows.
    """

    def test_no_non_engine_cron_decorators(self) -> None:
        """All cron-decorated functions MUST use engine @cron_envelope (or be allowlisted).

        Scans worker files for any function decorated with a non-engine cron decorator.
        Violations must appear in KNOWN_LEGACY_CRONS allowlist.
        """
        violations: list[str] = []
        unlisted_legacy: list[str] = []

        for file_path in _vitalia_worker_files():
            source = file_path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(file_path))
            except SyntaxError:
                continue  # Syntax errors caught by ruff

            for fn_name, dec_names in _get_decorated_functions(tree):
                for dec_name in dec_names:
                    if dec_name not in NON_ENGINE_CRON_DECORATORS:
                        continue
                    # Found a non-engine cron decorator
                    if fn_name not in KNOWN_LEGACY_CRONS:
                        violations.append(
                            f"{file_path.relative_to(Path(__file__).resolve().parents[4])}"
                            f"::{fn_name} — uses @{dec_name} (non-engine cron decorator). "
                            f"MUST migrate to @cron_envelope from {ENGINE_CRON_IMPORT_MODULE} "
                            f"OR add to KNOWN_LEGACY_CRONS allowlist with migration plan. "
                            f"See anti-duplication.md § engine consumption."
                        )
                    else:
                        # Allowlisted — record for audit (helps catch when migration done)
                        unlisted_legacy.append(
                            f"{file_path.relative_to(Path(__file__).resolve().parents[4])}"
                            f"::{fn_name} — allowlisted legacy: {KNOWN_LEGACY_CRONS[fn_name]}"
                        )

        assert violations == [], (
            "NON-ENGINE cron decorator violations detected — RATCHET FAIL:\n"
            + "\n".join(violations)
            + "\n\nAction required:\n"
            "  1. Migrate to: from luana_core_platform.workers.cron_envelope import cron_envelope\n"
            "  2. Apply @cron_envelope('<brand>.cron.<name>') decorator\n"
            "  3. Remove entry from KNOWN_LEGACY_CRONS (allowlist shrinks only)\n"
            "\nSee: .claude/rules/anti-duplication.md § engine consumption\n"
            "     03-arch-be.md § 4.1 Cron implementation pattern"
        )

    def test_fidelizacion_workers_use_engine_cron_envelope(self) -> None:
        """NEW fidelización worker files MUST use @cron_envelope (no allowlist for new code).

        Once T-6 implements the 6 fidelización workers, each MUST import and use
        @cron_envelope from engine — no brand-local decorator allowed.

        This test is a pre-emptive ratchet: it passes (SKIP) when the worker files
        do not exist yet (before T-6), and FAILS if they exist but don't use the
        engine decorator.
        """
        ws_root = Path(__file__).resolve().parents[4]
        fidelizacion_workers_dir = (
            ws_root / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "fidelizacion" / "application" / "workers"
        )

        if not fidelizacion_workers_dir.exists():
            # T-6 not yet implemented — test passes (not a violation to be empty)
            return

        expected_workers = [
            "multi_session_gap_sweep.py",
            "follow_up_due_sweep.py",
            "maintenance_due_sweep.py",
            "absence_sweep.py",
            "nps_post_treatment_sweep.py",
            "re_engagement_response_timeout_sweep.py",
        ]

        violations: list[str] = []

        for worker_name in expected_workers:
            worker_path = fidelizacion_workers_dir / worker_name
            if not worker_path.exists():
                continue  # Not yet created — not a violation

            source = worker_path.read_text(encoding="utf-8")

            # Must import from engine (not brand-local)
            if not _imports_engine_cron_envelope(source):
                violations.append(
                    f"{worker_name}: does not import cron_envelope from "
                    f"{ENGINE_CRON_IMPORT_MODULE}. "
                    f"Add: from luana_core_platform.workers.cron_envelope import cron_envelope"
                )
                continue

            # Must NOT use non-engine decorators
            try:
                tree = ast.parse(source, filename=str(worker_path))
            except SyntaxError:
                continue

            for fn_name, dec_names in _get_decorated_functions(tree):
                for dec_name in dec_names:
                    if dec_name in NON_ENGINE_CRON_DECORATORS:
                        violations.append(
                            f"{worker_name}::{fn_name} — uses non-engine @{dec_name}. "
                            f"New fidelización workers MUST use @cron_envelope (no allowlist for new code)."
                        )

        assert violations == [], (
            "Fidelización worker cron_envelope enforcement failures:\n"
            + "\n".join(violations)
            + "\n\nAll new fidelización workers MUST use @cron_envelope from engine.\n"
            "Reference implementation: 03-arch-be.md § 4.1 Cron implementation pattern\n"
            "Engine package: luana_core_platform.workers.cron_envelope"
        )

    def test_allowlist_does_not_grow(self) -> None:
        """KNOWN_LEGACY_CRONS must never exceed the established baseline.

        This test encodes the ratchet count so CI catches if someone adds
        a new entry instead of migrating. Update this number DOWN as migrations
        happen, NEVER up.
        """
        baseline_count = 1  # lucas_weekly_recommendations only
        actual_count = len(KNOWN_LEGACY_CRONS)
        assert actual_count <= baseline_count, (
            f"KNOWN_LEGACY_CRONS grew from baseline {baseline_count} to {actual_count}. "
            "Ratchet allowlist must shrink-only — NEVER add new entries. "
            "Migrate new cron functions to @cron_envelope from engine instead of adding to allowlist."
        )

    def test_engine_cron_envelope_importable(self) -> None:
        """Engine cron_envelope decorator must be importable from luana_core_platform."""
        try:
            from luana_core_platform.workers.cron_envelope import cron_envelope  # noqa: PLC0415

            assert callable(cron_envelope), "cron_envelope must be a callable decorator factory"
        except ImportError as exc:
            raise AssertionError(
                f"luana_core_platform.workers.cron_envelope not importable: {exc}\n"
                "Verify luana-core-platform is installed in workspace venv (uv sync from WS root)."
            ) from exc
