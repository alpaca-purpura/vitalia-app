# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""PHI fields SSoT — Vitalia HIPAA-lite compliance.

22 canonical PHI (Protected Health Information) fields as defined in
vitalia/.claude/rules/hipaa-lite.md § PHI fields canónicos.

This module is the Single Source of Truth for:
  - PII scanner profile `compliance_level: hipaa_lite`
  - sanitize_phi_payload field list
  - Architecture fitness tests for PHI handling

NEVER add PHI fields outside this file — any new medical-semantic field
MUST be added here + hipaa-lite.md updated in the same PR.

downstream-regression-na: brand-local SSoT for vitalia PHI field catalog
"""

from __future__ import annotations

# Top-level PHI field names (present at root of payload dict)
PHI_FIELDS_TOP_LEVEL: frozenset[str] = frozenset(
    [
        "diagnosis",
        "treatment_plan",
        "medication",
        "dosage",
        "allergies",
        "symptoms",
        "medical_notes",
        "lab_results",
        "vital_signs",
        "imaging_url",
        "xray_filename",
        "ultrasound_report",
        "previous_treatments",
        "family_history",
        "surgical_history",
    ]
)

# PHI sub-fields under the "patient" key
PHI_FIELDS_PATIENT: frozenset[str] = frozenset(
    [
        "name",
        "dni",
        "cuit",
        "date_of_birth",
        "phone",
        "email",
        "address",
    ]
)

# All 22 PHI fields as dotted paths (for reference / documentation)
PHI_FIELD_PATHS: tuple[str, ...] = (
    "patient.name",
    "patient.dni",
    "patient.cuit",
    "patient.date_of_birth",
    "patient.phone",
    "patient.email",
    "patient.address",
    "diagnosis",
    "treatment_plan",
    "medication",
    "dosage",
    "allergies",
    "symptoms",
    "medical_notes",
    "lab_results",
    "vital_signs",
    "imaging_url",
    "xray_filename",
    "ultrasound_report",
    "previous_treatments",
    "family_history",
    "surgical_history",
)

# Unencrypted channels — PHI MUST NOT be transmitted over these
BLOCKED_PHI_CHANNELS: frozenset[str] = frozenset(
    [
        "whatsapp_free",
        "sms",
        "email_plaintext",
    ]
)

# Channels where PHI transmission is permitted
ALLOWED_PHI_CHANNELS: frozenset[str] = frozenset(
    [
        "portal_secure",
        "whatsapp_business_encrypted",
        "https_api",
    ]
)

# RBAC — roles permitted to access PHI
PHI_ALLOWED_ROLES: frozenset[str] = frozenset(
    [
        "doctor",
        "nurse",
        "admin_clinic",
    ]
)

REDACTED_PLACEHOLDER: str = "[REDACTED-PHI]"
