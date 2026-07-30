# cap: iam.iam-scaffold-slice-1
# story-origin: TBD
"""Vitalia role definitions and PHI access control.

Domain layer — pure Python, no framework imports.
"""

from __future__ import annotations

from enum import Enum


class VitaliaRole(str, Enum):
    """Roles available in the Vitalia platform.

    OWNER: Clinic chain owner — administrative, no direct PHI access.
    ADMIN_CLINIC: Clinic administrator — can access PHI for operational purposes.
    DOCTOR: Medical doctor — full PHI access.
    NURSE: Nursing staff — PHI access for care coordination.
    RECEPTIONIST: Front desk — scheduling only, no PHI.
    MARKETING: Marketing team — analytics only, no PHI.
    PATIENT: Patient — access to own records only (separate flow).
    """

    OWNER = "owner"
    ADMIN_CLINIC = "admin_clinic"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"
    MARKETING = "marketing"
    PATIENT = "patient"


# Roles permitted to access Protected Health Information (PHI).
# Only 3 roles — per HIPAA-lite rule and arch spec § 3.4.
PHI_ALLOWED_ROLES: frozenset[VitaliaRole] = frozenset(
    {
        VitaliaRole.ADMIN_CLINIC,
        VitaliaRole.DOCTOR,
        VitaliaRole.NURSE,
    }
)


def is_phi_allowed(role: VitaliaRole | str) -> bool:
    """Return True if the given role is allowed to access PHI.

    Args:
        role: Either a VitaliaRole enum member or its string value.

    Returns:
        True if role is in PHI_ALLOWED_ROLES, False otherwise.
    """
    if isinstance(role, str):
        try:
            role = VitaliaRole(role)
        except ValueError:
            return False
    return role in PHI_ALLOWED_ROLES
