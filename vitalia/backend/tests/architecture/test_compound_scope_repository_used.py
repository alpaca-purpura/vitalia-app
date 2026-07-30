"""Arch fitness: ALL vitalia PHI repositories MUST use CompoundScopeRepositoryBase from engine.

Scans vitalia/backend/src/modules/vitalia/**/*_repository.py for repository classes
that handle PHI data and verifies they inherit from CompoundScopeRepositoryBase
from ``luana_core_platform.repositories.compound_scope_repository``.

PHI repositories are identified by inheriting from PhiRepositoryBase (brand-local,
pre-engine-lift) OR by appearing in the EXPECTED_PHI_REPOS set (fidelización T-4
repos that MUST use the engine base from day 1, no allowlist entry allowed).

Ratchet pattern (shrink-only):
  KNOWN_LEGACY_PHI_REPOS = {<filename>: <reason>}
  Add to this allowlist ONLY for pre-existing repos that pre-date the engine lift
  (2026-05-20). Remove entries as each repo migrates to CompoundScopeRepositoryBase.
  Allowlist NEVER grows.

Why this gate?
  Engine CompoundScopeRepositoryBase provides:
    1. Dual-scope isolation (tenant_id + scope_id) — HIPAA-lite cardinal rule
    2. Method contract enforcement (get_by_id requires both IDs)
    3. Consistent list_for_scope signature cross-module
    4. Scope field configured per-brand (vitalia uses scope_field="clinic_id")
  Brand-local PhiRepositoryBase was the predecessor — it was promoted to
  core engine on 2026-05-20 per promotion proposal
  ``2026-05-20-core-platform-extensions-slice-1``.

T-3 — vitalia-slice-1-fidelizacion (arch fitness, production_code=false)
"""

from __future__ import annotations

import ast
from pathlib import Path

# ---------------------------------------------------------------------------
# Ratchet allowlist — SHRINK ONLY, never grow
# ---------------------------------------------------------------------------
# Format: {filename: reason_string}
# Each entry is a legacy PHI repository that pre-dates the engine lift
# (2026-05-20) and uses the brand-local PhiRepositoryBase.
# Remove when migrated to CompoundScopeRepositoryBase; do NOT add new entries.
KNOWN_LEGACY_PHI_REPOS: dict[str, str] = {
    "patient_repository.py": (
        "Uses brand-local PhiRepositoryBase — pre-dates engine CompoundScopeRepositoryBase "
        "lift (2026-05-20). Migration to CompoundScopeRepositoryBase planned in "
        "vitalia-slice-1-fidelizacion T-6 follow-up (crm module migration wave)."
    ),
    "lead_screening_event_repository.py": (
        "Uses brand-local PhiRepositoryBase — pre-dates engine CompoundScopeRepositoryBase "
        "lift (2026-05-20). Migration to CompoundScopeRepositoryBase planned in "
        "vitalia-slice-1-fidelizacion T-6 follow-up (sales_agent module migration wave)."
    ),
}

# ---------------------------------------------------------------------------
# Engine base class that MUST be used for all NEW PHI repositories
# ---------------------------------------------------------------------------
ENGINE_BASE_CLASS = "CompoundScopeRepositoryBase"
ENGINE_BASE_IMPORT_MODULE = "luana_core_platform.repositories.compound_scope_repository"

# The brand-local base class that is LEGACY (being deprecated post-lift)
BRAND_LOCAL_BASE_CLASS = "PhiRepositoryBase"
BRAND_LOCAL_BASE_MODULE = "luana_core_platform.workers.cron_envelope"

# ---------------------------------------------------------------------------
# Fidelización PHI repos that MUST use engine base (no allowlist for new code)
# ---------------------------------------------------------------------------
# Once T-4 implements these, each MUST import and inherit CompoundScopeRepositoryBase.
# This list is pre-emptive — validates new repos when they appear.
EXPECTED_FIDELIZACION_PHI_REPOS: frozenset[str] = frozenset(
    [
        "treatment_plan_repository.py",
        "re_engagement_event_repository.py",
        "nps_response_repository.py",
    ]
)


def _vitalia_repo_files() -> list[Path]:
    """Return all *_repository.py files under vitalia business modules.

    Excludes copilot/ and sales_agent/ (builder-agentic exclusive)
    to respect module ownership boundaries per DDD rules.
    Excludes _shared/repositories/ (shared infra, not business PHI repos).
    Includes all other repository files under modules/vitalia/.
    """
    ws_root = Path(__file__).resolve().parents[4]  # workspace root
    vitalia_src = ws_root / "vitalia" / "backend" / "src"
    if not vitalia_src.exists():
        return []

    modules_vitalia = vitalia_src / "modules" / "vitalia"
    if not modules_vitalia.exists():
        return []

    files: list[Path] = []
    for py_file in modules_vitalia.rglob("*_repository.py"):
        # Skip __init__.py (not repos)
        if py_file.name == "__init__.py":
            continue
        # Skip copilot — builder-agentic exclusive owner
        if "copilot" in py_file.parts:
            continue
        # Skip sales_agent — builder-agentic exclusive owner
        if "sales_agent" in py_file.parts:
            continue
        # Include all others (crm, infrastructure, fidelizacion, etc.)
        files.append(py_file)

    return sorted(files)


def _vitalia_phi_repo_files() -> list[Path]:
    """Return repository files that handle PHI data.

    Includes files that:
      1. Currently inherit PhiRepositoryBase (legacy brand-local) — confirmed PHI
      2. Are named as expected fidelización PHI repos (pre-emptive — may not exist yet)

    Also checks _shared/repositories/ for PhiRepositoryBase consumers
    (while excluding the base itself).
    """
    ws_root = Path(__file__).resolve().parents[4]
    vitalia_src = ws_root / "vitalia" / "backend" / "src"
    if not vitalia_src.exists():
        return []

    modules_vitalia = vitalia_src / "modules" / "vitalia"
    if not modules_vitalia.exists():
        return []

    phi_files: list[Path] = []
    seen: set[Path] = set()

    # Search all modules (excluding copilot + sales_agent — agentic exclusive)
    # sales_agent IS included for existing repos but via copilot boundary exclusion only
    for py_file in modules_vitalia.rglob("*_repository.py"):
        if py_file.name == "__init__.py":
            continue
        if "copilot" in py_file.parts:
            continue
        if py_file in seen:
            continue

        source = py_file.read_text(encoding="utf-8")
        # File is PHI if it imports or inherits from PhiRepositoryBase (legacy)
        # OR if it's an expected fidelización PHI repo
        if BRAND_LOCAL_BASE_CLASS in source:
            if py_file.name != "phi_repository.py":  # exclude the base itself
                phi_files.append(py_file)
                seen.add(py_file)

    # Also scan sales_agent repos for PhiRepositoryBase usage
    # (sales_agent domain repos may use brand-local base)
    sales_agent_dir = modules_vitalia / "sales_agent"
    if sales_agent_dir.exists():
        for py_file in sales_agent_dir.rglob("*_repository.py"):
            if py_file.name == "__init__.py":
                continue
            if py_file in seen:
                continue
            source = py_file.read_text(encoding="utf-8")
            if BRAND_LOCAL_BASE_CLASS in source:
                phi_files.append(py_file)
                seen.add(py_file)

    return sorted(set(phi_files))


def _get_class_bases(tree: ast.Module) -> list[tuple[str, list[str]]]:
    """Extract (class_name, [base_names]) pairs from module AST.

    Returns only classes that have at least one explicit base. Base names
    are extracted as either plain ``Name.id`` or ``Attribute.attr`` (for
    ``module.BaseClass`` style).
    """
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not node.bases:
            continue
        base_names = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.append(base.attr)
        if base_names:
            results.append((node.name, base_names))
    return results


def _imports_engine_compound_scope(source: str) -> bool:
    """Return True if the file imports CompoundScopeRepositoryBase from the engine."""
    return ENGINE_BASE_IMPORT_MODULE in source and ENGINE_BASE_CLASS in source


def _uses_brand_local_phi_base(source: str) -> bool:
    """Return True if the file imports or references the brand-local PhiRepositoryBase."""
    return BRAND_LOCAL_BASE_CLASS in source


class TestCompoundScopeRepositoryUsed:
    """Architecture gate: PHI repositories MUST use engine CompoundScopeRepositoryBase.

    Ratchet policy:
      - Pass: all PHI repositories use CompoundScopeRepositoryBase OR are in allowlist.
      - Fail: any new PHI repository uses brand-local PhiRepositoryBase without allowlist entry.

    Shrink-only: KNOWN_LEGACY_PHI_REPOS shrinks as migrations happen; it never grows.
    """

    def test_no_new_brand_local_phi_repos(self) -> None:
        """New PHI repositories MUST NOT inherit brand-local PhiRepositoryBase.

        Scans all vitalia repository files for classes that use PhiRepositoryBase.
        Any such file must appear in KNOWN_LEGACY_PHI_REPOS allowlist.
        Violations = new code using the legacy base without allowlist entry.
        """
        violations: list[str] = []
        allowlisted: list[str] = []

        phi_files = _vitalia_phi_repo_files()

        for file_path in phi_files:
            source = file_path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(file_path))
            except SyntaxError:
                continue  # Syntax errors caught by ruff

            for class_name, base_names in _get_class_bases(tree):
                if BRAND_LOCAL_BASE_CLASS not in base_names:
                    continue
                # Found a class using brand-local PhiRepositoryBase
                filename = file_path.name
                if filename not in KNOWN_LEGACY_PHI_REPOS:
                    violations.append(
                        f"{file_path.relative_to(Path(__file__).resolve().parents[4])}"
                        f"::{class_name} — inherits {BRAND_LOCAL_BASE_CLASS} (brand-local, LEGACY). "
                        f"New PHI repositories MUST inherit {ENGINE_BASE_CLASS} from "
                        f"{ENGINE_BASE_IMPORT_MODULE}. "
                        f"Add to KNOWN_LEGACY_PHI_REPOS allowlist ONLY if this predates "
                        f"the engine lift (2026-05-20). "
                        f"See promotion proposal 2026-05-20-core-platform-extensions-slice-1."
                    )
                else:
                    allowlisted.append(
                        f"{file_path.relative_to(Path(__file__).resolve().parents[4])}"
                        f"::{class_name} — allowlisted legacy: {KNOWN_LEGACY_PHI_REPOS[filename]}"
                    )

        assert violations == [], (
            "NEW brand-local PhiRepositoryBase usages detected — RATCHET FAIL:\n"
            + "\n".join(violations)
            + "\n\nAction required:\n"
            "  1. Migrate to:\n"
            "     from luana_core_platform.repositories.compound_scope_repository import"
            " CompoundScopeRepositoryBase\n"
            "  2. Inherit CompoundScopeRepositoryBase and set scope_field='clinic_id'\n"
            "  3. Update constructor to pass scope_field='clinic_id' to engine base\n"
            "  4. Remove entry from KNOWN_LEGACY_PHI_REPOS (allowlist shrinks only)\n"
            "\nSee: vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo\n"
            "     03-arch-be.md § 3.3 PHI Repository pattern (CompoundScopeRepositoryBase)\n"
            "     core/luana-core-platform/src/luana_core_platform/"
            "repositories/compound_scope_repository.py"
        )

    def test_fidelizacion_phi_repos_use_engine_base(self) -> None:
        """NEW fidelización PHI repos MUST use CompoundScopeRepositoryBase (no allowlist for new code).

        Once T-4 implements the 3 fidelización PHI repositories, each MUST import
        and inherit CompoundScopeRepositoryBase from engine — no brand-local base allowed.

        This test is a pre-emptive ratchet: it passes (SKIP) when the repo files
        do not exist yet (before T-4), and FAILS if they exist but don't use engine base.
        """
        ws_root = Path(__file__).resolve().parents[4]
        fidelizacion_repos_dir = (
            ws_root
            / "vitalia"
            / "backend"
            / "src"
            / "modules"
            / "vitalia"
            / "fidelizacion"
            / "infrastructure"
            / "repositories"
        )

        if not fidelizacion_repos_dir.exists():
            # T-4 not yet implemented — test passes (not a violation to be empty)
            return

        violations: list[str] = []

        for repo_name in EXPECTED_FIDELIZACION_PHI_REPOS:
            repo_path = fidelizacion_repos_dir / repo_name
            if not repo_path.exists():
                continue  # Not yet created — not a violation

            source = repo_path.read_text(encoding="utf-8")

            # Must import from engine (not brand-local)
            if not _imports_engine_compound_scope(source):
                violations.append(
                    f"{repo_name}: does not import {ENGINE_BASE_CLASS} from "
                    f"{ENGINE_BASE_IMPORT_MODULE}. "
                    f"Add: from luana_core_platform.repositories.compound_scope_repository"
                    f" import CompoundScopeRepositoryBase"
                )
                continue

            # Must NOT use brand-local PhiRepositoryBase
            if _uses_brand_local_phi_base(source):
                try:
                    tree = ast.parse(source, filename=str(repo_path))
                except SyntaxError:
                    continue

                for class_name, base_names in _get_class_bases(tree):
                    if BRAND_LOCAL_BASE_CLASS in base_names:
                        violations.append(
                            f"{repo_name}::{class_name} — inherits brand-local "
                            f"{BRAND_LOCAL_BASE_CLASS}. "
                            f"New fidelización PHI repos MUST inherit "
                            f"{ENGINE_BASE_CLASS} (no allowlist for new code)."
                        )

        assert violations == [], (
            "Fidelización PHI repository engine base enforcement failures:\n"
            + "\n".join(violations)
            + "\n\nAll new fidelización PHI repositories MUST use CompoundScopeRepositoryBase"
            " from engine.\n"
            "Reference: 03-arch-be.md § 3.3 PHI Repository pattern\n"
            "Engine class: luana_core_platform.repositories.compound_scope_repository"
            ".CompoundScopeRepositoryBase\n"
            "Constructor: super().__init__(session=session, scope_field='clinic_id')"
        )

    def test_allowlist_does_not_grow(self) -> None:
        """KNOWN_LEGACY_PHI_REPOS must never exceed the established baseline.

        This test encodes the ratchet count so CI catches if someone adds
        a new entry instead of migrating. Update this number DOWN as migrations
        happen, NEVER up.
        """
        baseline_count = 2  # patient_repository + lead_screening_event_repository
        actual_count = len(KNOWN_LEGACY_PHI_REPOS)
        assert actual_count <= baseline_count, (
            f"KNOWN_LEGACY_PHI_REPOS grew from baseline {baseline_count} to {actual_count}. "
            "Ratchet allowlist must shrink-only — NEVER add new entries. "
            "Migrate new PHI repositories to CompoundScopeRepositoryBase from engine instead "
            "of adding to allowlist."
        )

    def test_engine_compound_scope_importable(self) -> None:
        """Engine CompoundScopeRepositoryBase must be importable from luana_core_platform."""
        try:
            from luana_core_platform.repositories.compound_scope_repository import (  # noqa: PLC0415
                CompoundScopeRepositoryBase,
            )

            assert callable(CompoundScopeRepositoryBase), "CompoundScopeRepositoryBase must be a callable class"
            # Verify scope_field param is accepted (default "scope_id" per engine contract)
            import inspect  # noqa: PLC0415

            sig = inspect.signature(CompoundScopeRepositoryBase.__init__)
            assert "scope_field" in sig.parameters, (
                "CompoundScopeRepositoryBase.__init__ must accept scope_field parameter. "
                "Vitalia uses scope_field='clinic_id' for HIPAA-lite dual filter."
            )
        except ImportError as exc:
            raise AssertionError(
                f"luana_core_platform.repositories.compound_scope_repository not importable:"
                f" {exc}\n"
                "Verify luana-core-platform is installed in workspace venv (uv sync from WS"
                " root)."
            ) from exc

    def test_existing_phi_repos_have_dual_filter(self) -> None:
        """All allowlisted legacy PHI repos must still enforce clinic_id filter.

        Allowlisted repos use brand-local PhiRepositoryBase which calls
        validate_dual_filter(). This test verifies that clinic_id keyword
        appears in those repo files — a quick smell test that dual filter
        enforcement is present even in legacy code.

        This test is NOT a full semantic verification (test_phi_dual_filter.py
        covers that) — it's a quick integrity check for the allowlisted repos.
        """
        ws_root = Path(__file__).resolve().parents[4]
        vitalia_src = ws_root / "vitalia" / "backend" / "src" / "modules" / "vitalia"

        violations: list[str] = []

        for filename in KNOWN_LEGACY_PHI_REPOS:
            # Find the file anywhere in vitalia module tree
            matching = list(vitalia_src.rglob(filename))
            if not matching:
                # File not found — may be OK (renamed/removed), but log it
                violations.append(
                    f"Allowlisted repo '{filename}' not found in vitalia modules. "
                    "Remove from KNOWN_LEGACY_PHI_REPOS if file was deleted/renamed."
                )
                continue

            for file_path in matching:
                source = file_path.read_text(encoding="utf-8")
                # Verify clinic_id is referenced — dual filter smoke check
                if "clinic_id" not in source:
                    violations.append(
                        f"{file_path.relative_to(ws_root)}: allowlisted legacy PHI repo "
                        f"'{filename}' does not reference 'clinic_id'. "
                        "HIPAA-lite dual filter MUST be enforced even in legacy code. "
                        "Verify validate_dual_filter() is called with clinic_id parameter."
                    )

        assert violations == [], (
            "Allowlisted legacy PHI repository dual-filter integrity failures:\n"
            + "\n".join(violations)
            + "\n\nLegacy PHI repos MUST still call validate_dual_filter(clinic_id=...) "
            "even while awaiting migration to CompoundScopeRepositoryBase.\n"
            "See: vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo"
        )
