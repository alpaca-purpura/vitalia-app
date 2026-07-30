# cap: clinics.lisa.doctores
"""Architecture gate: PublicDoctorDTO must NOT serialize PHI fields.

Channel guard test — PublicDoctorDTO is the allow-list DTO for the public
/api/public/clinic/{slug}/doctors endpoint (no auth). PHI fields (dni, email,
phone, credential, date_of_birth) MUST NOT appear in the model fields.

Per 03-arch-be.md § 3: PublicDoctorDTO allow-list 7 fields only.
Per hipaa-lite.md: channel guard prevents PHI leakage through public endpoint.

Validator ID: V-ARCH-7 (04-validators.yaml).
"""

from __future__ import annotations

import pytest

# PHI fields that MUST NOT appear in PublicDoctorDTO
_FORBIDDEN_PHI_FIELDS: frozenset[str] = frozenset(
    {
        "dni",
        "dni_encrypted",
        "email",
        "email_encrypted",
        "phone",
        "phone_encrypted",
        "credential",
        "credential_encrypted",
        "date_of_birth",
        "address",
        "medical_notes",
        "diagnosis",
        # masked variants also forbidden in public DTO (should be excluded entirely)
        "masked_dni",
        "masked_email",
        "masked_phone",
    }
)

# Expected allow-listed fields for PublicDoctorDTO (7 max)
_EXPECTED_ALLOWED_FIELDS: frozenset[str] = frozenset(
    {
        "display_name",
        "specialty",
        "avatar_key",
        "years_experience",
        "languages",
        "bio_public",
        "credential_label",
    }
)


def test_public_doctor_dto_exists() -> None:
    """PublicDoctorDTO must be importable from clinics api dtos."""
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorDTO  # noqa: F401


def test_public_doctor_dto_no_phi_fields() -> None:
    """PublicDoctorDTO MUST NOT contain PHI field names.

    Channel guard: this DTO is serialized to unauthenticated callers.
    ANY PHI field in the model fields = hard FAIL.
    """
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorDTO

    model_fields = set(PublicDoctorDTO.model_fields.keys())
    violations = _FORBIDDEN_PHI_FIELDS & model_fields

    assert not violations, (
        f"PublicDoctorDTO contains PHI fields that MUST be excluded: {violations}.\n"
        f"PublicDoctorDTO is the channel guard for the public /api/public/... endpoint.\n"
        f"Per hipaa-lite.md: channel guards use explicit allow-lists — never ORM-mapped directly.\n"
        f"Remove {violations} from PublicDoctorDTO immediately."
    )


def test_public_doctor_dto_has_allowed_fields() -> None:
    """PublicDoctorDTO must include the expected allow-listed fields."""
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorDTO

    model_fields = set(PublicDoctorDTO.model_fields.keys())

    missing = _EXPECTED_ALLOWED_FIELDS - model_fields
    assert not missing, (
        f"PublicDoctorDTO is missing expected allow-listed fields: {missing}.\n"
        f"Per 03-arch-be.md § 3: PublicDoctorDTO has 7 allow-listed fields: "
        f"{_EXPECTED_ALLOWED_FIELDS}"
    )


def test_public_doctor_dto_only_has_allowed_fields() -> None:
    """PublicDoctorDTO must not have extra unexpected fields."""
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorDTO

    model_fields = set(PublicDoctorDTO.model_fields.keys())
    unexpected = model_fields - _EXPECTED_ALLOWED_FIELDS

    assert not unexpected, (
        f"PublicDoctorDTO has unexpected extra fields: {unexpected}.\n"
        f"Only these fields are in the allow-list: {_EXPECTED_ALLOWED_FIELDS}.\n"
        f"Each addition requires explicit review: does it contain PHI? Does it leak tenant data?"
    )


def test_public_doctor_serializer_exists() -> None:
    """public_doctor_serializer module must exist (allow-list mapper)."""
    try:
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (  # noqa: F401
            to_public_dto,
        )
    except ImportError:
        pytest.skip("public_doctor_serializer.py not yet created (T-BE-5 scope)")
