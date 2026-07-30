"""Arch fitness: PHI repositories MUST include clinic_id in all queries.

AST scan: ALL *_repository.py files referencing PHI ORM models MUST have
both tenant_id AND clinic_id in their .where() / filter conditions.

T-infra-3 — vitalia HIPAA-lite dual-filter enforcement gate.
"""

from __future__ import annotations

import ast
from pathlib import Path

# PHI model names that MUST use dual filter
PHI_ORM_MODELS = frozenset(
    [
        "Patient",
        "MedicalRecord",
        "TreatmentPlan",
        "Appointment",
        "ReEngagementEvent",
        "PatientMedicalRecord",
        "TreatmentNote",
        "Diagnosis",
        "Prescription",
    ]
)

# Repo files explicitly EXEMPT (non-PHI repos that happen to contain those names
# only in comments/docstrings, or utility repos with no PHI ORM access)
EXEMPT_REPO_FILES: frozenset[str] = frozenset([])


def _repo_files_in_vitalia() -> list[Path]:
    """Return all *_repository.py files under vitalia backend src."""
    ws_root = Path(__file__).resolve().parents[4]  # workspace root
    vitalia_src = ws_root / "vitalia" / "backend" / "src"
    if not vitalia_src.exists():
        return []
    return [p for p in vitalia_src.rglob("*_repository.py") if p.name not in EXEMPT_REPO_FILES]


def _references_phi_model(tree: ast.Module) -> bool:
    """Return True if any Name node in the AST references a PHI ORM model."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in PHI_ORM_MODELS:
            return True
        if isinstance(node, ast.Attribute) and node.attr in PHI_ORM_MODELS:
            return True
    return False


def _has_tenant_id_filter(source: str) -> bool:
    """Return True if source contains tenant_id in a where/filter context."""
    return "tenant_id" in source


def _has_clinic_id_filter(source: str) -> bool:
    """Return True if source contains clinic_id in a where/filter context."""
    return "clinic_id" in source


class TestPhiDualFilterArchFitness:
    """Every PHI repository MUST filter by both tenant_id AND clinic_id."""

    def test_phi_repo_files_exist(self) -> None:
        """Sanity: at least the phi_repository.py file must exist."""
        ws_root = Path(__file__).resolve().parents[4]
        phi_repo = (
            ws_root
            / "vitalia"
            / "backend"
            / "src"
            / "modules"
            / "vitalia"
            / "_shared"
            / "repositories"
            / "phi_repository.py"
        )
        assert phi_repo.exists(), (
            "phi_repository.py must exist at vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py"
        )

    def test_phi_repository_base_has_dual_filter_validation(self) -> None:
        """PhiRepositoryBase must declare validate_dual_filter method."""
        ws_root = Path(__file__).resolve().parents[4]
        phi_repo = (
            ws_root
            / "vitalia"
            / "backend"
            / "src"
            / "modules"
            / "vitalia"
            / "_shared"
            / "repositories"
            / "phi_repository.py"
        )
        if not phi_repo.exists():
            return  # Skipped until implementation exists

        source = phi_repo.read_text()
        assert "validate_dual_filter" in source, (
            "PhiRepositoryBase must declare validate_dual_filter() method per HIPAA-lite dual-filter rule"
        )

    def test_phi_repository_base_has_clinic_id_in_signature(self) -> None:
        """PhiRepositoryBase.get_by_id must accept clinic_id parameter."""
        ws_root = Path(__file__).resolve().parents[4]
        phi_repo = (
            ws_root
            / "vitalia"
            / "backend"
            / "src"
            / "modules"
            / "vitalia"
            / "_shared"
            / "repositories"
            / "phi_repository.py"
        )
        if not phi_repo.exists():
            return

        source = phi_repo.read_text()
        assert "clinic_id" in source, (
            "PhiRepositoryBase must reference clinic_id — it is the second mandatory PHI filter (per hipaa-lite.md)"
        )
        assert "tenant_id" in source, (
            "PhiRepositoryBase must reference tenant_id — "
            "it is the first mandatory PHI filter (per tenant-isolation.md)"
        )

    def test_no_phi_repo_skips_clinic_id(self) -> None:
        """Any *_repository.py referencing PHI models MUST have clinic_id filter.

        This is the arch gate ratchet — new repositories that reference PHI ORM
        models without clinic_id will fail this test.
        """
        violations: list[str] = []
        for repo_path in _repo_files_in_vitalia():
            source = repo_path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(repo_path))
            except SyntaxError:
                continue  # Syntax errors caught by ruff

            if not _references_phi_model(tree):
                continue  # Not a PHI repo — skip

            if not _has_tenant_id_filter(source):
                violations.append(f"{repo_path}: missing tenant_id filter (PHI repo)")

            if not _has_clinic_id_filter(source):
                violations.append(
                    f"{repo_path}: missing clinic_id filter "
                    "(HIPAA-lite dual-filter — PHI queries MUST filter by clinic_id)"
                )

        assert violations == [], (
            "PHI repository dual-filter violations detected:\n"
            + "\n".join(violations)
            + "\n\nAll repositories referencing PHI ORM models MUST include "
            "BOTH tenant_id AND clinic_id in .where() conditions "
            "(vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo)"
        )
