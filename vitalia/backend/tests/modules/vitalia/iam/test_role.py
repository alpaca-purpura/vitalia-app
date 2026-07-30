"""Tests for VitaliaRole enum + PHI access allowlist mapping.

TDD: RED tests defined before implementation (T-infra-9).

downstream-regression-na: brand-local IAM role tests, no cross-brand consumers
"""

from __future__ import annotations

from src.modules.vitalia.iam.domain.role import (
    PHI_ALLOWED_ROLES,
    VitaliaRole,
    is_phi_allowed,
)


class TestVitaliaRoleEnum:
    """VitaliaRole enum values and coverage."""

    def test_owner_role_exists(self) -> None:
        assert VitaliaRole.OWNER.value == "owner"

    def test_admin_clinic_role_exists(self) -> None:
        assert VitaliaRole.ADMIN_CLINIC.value == "admin_clinic"

    def test_doctor_role_exists(self) -> None:
        assert VitaliaRole.DOCTOR.value == "doctor"

    def test_nurse_role_exists(self) -> None:
        assert VitaliaRole.NURSE.value == "nurse"

    def test_receptionist_role_exists(self) -> None:
        assert VitaliaRole.RECEPTIONIST.value == "receptionist"

    def test_marketing_role_exists(self) -> None:
        assert VitaliaRole.MARKETING.value == "marketing"

    def test_patient_role_exists(self) -> None:
        assert VitaliaRole.PATIENT.value == "patient"

    def test_all_seven_roles_defined(self) -> None:
        values = {r.value for r in VitaliaRole}
        assert values == {"owner", "admin_clinic", "doctor", "nurse", "receptionist", "marketing", "patient"}


class TestPhiAccessAllowlist:
    """PHI access allowlist: doctor, nurse, admin_clinic only."""

    def test_phi_allowed_roles_set_contains_doctor(self) -> None:
        assert "doctor" in PHI_ALLOWED_ROLES

    def test_phi_allowed_roles_set_contains_nurse(self) -> None:
        assert "nurse" in PHI_ALLOWED_ROLES

    def test_phi_allowed_roles_set_contains_admin_clinic(self) -> None:
        assert "admin_clinic" in PHI_ALLOWED_ROLES

    def test_phi_allowed_roles_excludes_marketing(self) -> None:
        assert "marketing" not in PHI_ALLOWED_ROLES

    def test_phi_allowed_roles_excludes_patient(self) -> None:
        assert "patient" not in PHI_ALLOWED_ROLES

    def test_phi_allowed_roles_excludes_receptionist(self) -> None:
        assert "receptionist" not in PHI_ALLOWED_ROLES

    def test_phi_allowed_roles_excludes_owner(self) -> None:
        """Owner does not have direct PHI access — use admin_clinic for clinical data."""
        assert "owner" not in PHI_ALLOWED_ROLES

    def test_is_phi_allowed_returns_true_for_doctor(self) -> None:
        assert is_phi_allowed(VitaliaRole.DOCTOR) is True

    def test_is_phi_allowed_returns_true_for_nurse(self) -> None:
        assert is_phi_allowed(VitaliaRole.NURSE) is True

    def test_is_phi_allowed_returns_true_for_admin_clinic(self) -> None:
        assert is_phi_allowed(VitaliaRole.ADMIN_CLINIC) is True

    def test_is_phi_allowed_returns_false_for_marketing(self) -> None:
        assert is_phi_allowed(VitaliaRole.MARKETING) is False

    def test_is_phi_allowed_returns_false_for_patient(self) -> None:
        assert is_phi_allowed(VitaliaRole.PATIENT) is False

    def test_is_phi_allowed_accepts_string_value(self) -> None:
        assert is_phi_allowed("doctor") is True  # type: ignore[arg-type]

    def test_phi_allowed_roles_cardinality(self) -> None:
        """Exactly 3 roles allowed PHI access — no accidental expansion."""
        assert len(PHI_ALLOWED_ROLES) == 3
