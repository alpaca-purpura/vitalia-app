# cap: clinics.lisa.doctores
"""Architecture gate: PublicDoctorProfileDTO must NOT serialize PHI fields.

Channel guard test — PublicDoctorProfileDTO is the allow-list DTO for the
structured public profile endpoint:
  GET /api/public/clinic/{tenant_slug}/doctors/{doctor_slug}

PHI fields (dni, email, phone, credential, date_of_birth) MUST NOT appear.
Per 03-arch-delta.md § 6.1 + hipaa-lite.md § Channel guards.
Per RN-D3D-6: all profile sections nullable.
Per RN-D3D-5: idiomas only exposed if len > 1 (enforced in serializer).

Validator ID: V-ARCH-D3D (T-BE-pagina-publica).
"""

from __future__ import annotations

# PHI fields that MUST NOT appear in PublicDoctorProfileDTO
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
        # masked variants also forbidden (should be excluded entirely from public DTO)
        "masked_dni",
        "masked_email",
        "masked_phone",
        # internal routing fields forbidden in public DTO
        "tenant_id",
        "clinic_id",
        "active",
        "visible_en_landing",
    }
)

# Expected allow-listed fields for PublicDoctorProfileDTO
_EXPECTED_ALLOWED_FIELDS: frozenset[str] = frozenset(
    {
        "display_name",
        "specialty",
        "avatar_key",
        "sobre_mi",
        "formacion",
        "experiencia",
        "tratamientos",
        "certificaciones",
        "idiomas",
    }
)


def test_public_doctor_profile_dto_exists() -> None:
    """PublicDoctorProfileDTO must be importable from clinics api dtos."""
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO  # noqa: F401


def test_public_doctor_profile_dto_no_phi_fields() -> None:
    """PublicDoctorProfileDTO MUST NOT contain PHI field names.

    Channel guard: this DTO is serialized to unauthenticated callers.
    ANY PHI field in the model fields = hard FAIL.
    """
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO

    model_fields = set(PublicDoctorProfileDTO.model_fields.keys())
    violations = _FORBIDDEN_PHI_FIELDS & model_fields

    assert not violations, (
        f"PublicDoctorProfileDTO contains PHI fields that MUST be excluded: {violations}.\n"
        f"PublicDoctorProfileDTO is the channel guard for the public profile endpoint.\n"
        f"Per hipaa-lite.md: channel guards use explicit allow-lists — never ORM-mapped directly.\n"
        f"Remove {violations} from PublicDoctorProfileDTO immediately."
    )


def test_public_doctor_profile_dto_has_identity_fields() -> None:
    """PublicDoctorProfileDTO must have minimum identity fields (RN-D3D-6)."""
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO

    model_fields = set(PublicDoctorProfileDTO.model_fields.keys())
    # Minimum identity: display_name always present
    assert "display_name" in model_fields, "PublicDoctorProfileDTO missing display_name (minimum identity per RN-D3D-6)"


def test_public_doctor_profile_dto_has_expected_sections() -> None:
    """PublicDoctorProfileDTO must include the expected allow-listed section fields."""
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO

    model_fields = set(PublicDoctorProfileDTO.model_fields.keys())
    missing = _EXPECTED_ALLOWED_FIELDS - model_fields
    assert not missing, (
        f"PublicDoctorProfileDTO is missing expected allow-listed fields: {missing}.\n"
        f"Per 03-arch-delta.md § 6.1: PublicDoctorProfileDTO sections: {_EXPECTED_ALLOWED_FIELDS}"
    )


def test_public_doctor_profile_dto_all_sections_nullable() -> None:
    """All profile section fields in PublicDoctorProfileDTO must be nullable (RN-D3D-6).

    Minimum identity is display_name — all other fields may be None.
    """
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO

    nullable_sections = ["sobre_mi", "formacion", "experiencia", "tratamientos", "certificaciones", "idiomas"]
    model_fields = PublicDoctorProfileDTO.model_fields
    for field_name in nullable_sections:
        if field_name in model_fields:
            field = model_fields[field_name]
            assert not field.is_required(), (
                f"PublicDoctorProfileDTO.{field_name} must be nullable/optional per RN-D3D-6.\n"
                f"Partial profile (no sections yet) must be valid."
            )


def test_profile_state_dto_exists() -> None:
    """ProfileStateDTO must be importable from clinics api dtos."""
    from src.modules.vitalia.clinics.api.dtos import ProfileStateDTO  # noqa: F401


def test_profile_state_dto_no_phi_fields() -> None:
    """ProfileStateDTO must NOT contain PHI field names."""
    from src.modules.vitalia.clinics.api.dtos import ProfileStateDTO

    model_fields = set(ProfileStateDTO.model_fields.keys())
    violations = _FORBIDDEN_PHI_FIELDS & model_fields

    assert not violations, (
        f"ProfileStateDTO contains PHI fields: {violations}.\n"
        f"ProfileStateDTO is exposed in DoctorDetailDTO (admin) — PHI must never appear."
    )


def test_doctor_detail_dto_has_profile_state() -> None:
    """DoctorDetailDTO must include profile_state for RN-D3D-4 material_new detection."""
    from src.modules.vitalia.clinics.api.dtos import DoctorDetailDTO

    model_fields = set(DoctorDetailDTO.model_fields.keys())
    assert "profile_state" in model_fields, (
        "DoctorDetailDTO missing profile_state field required by RN-D3D-4.\n"
        "Clinic admin needs profile_state to know if profile is stale."
    )


def test_to_public_profile_dto_exists() -> None:
    """to_public_profile_dto function must exist in public_doctor_serializer."""
    from src.modules.vitalia.clinics.application.public_doctor_serializer import (  # noqa: F401
        to_public_profile_dto,
    )


def test_doctor_public_profile_domain_entity_exists() -> None:
    """DoctorPublicProfile domain entity must exist (pure Python, no framework)."""
    from src.modules.vitalia.clinics.domain.public_profile import (  # noqa: F401
        DoctorPublicProfile,
        ExperienciaItem,
        FormacionItem,
    )


def test_doctor_entity_has_new_fields() -> None:
    """Doctor entity must have public_profile, bio_generated_at, public_slug fields."""
    from src.modules.vitalia.clinics.domain.doctor import Doctor

    fields = {name for name in Doctor.__dataclass_fields__}
    required_new = {"public_profile", "bio_generated_at", "public_slug"}
    missing = required_new - fields
    assert not missing, (
        f"Doctor domain entity missing new D3-D fields: {missing}.\n"
        f"Migration 041 adds these columns — domain entity must match."
    )


def test_doctor_repository_has_get_by_public_slug() -> None:
    """DoctorRepository must have get_by_public_slug method (required by D3-D router)."""
    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
        DoctorRepository,
    )

    assert hasattr(DoctorRepository, "get_by_public_slug"), (
        "DoctorRepository.get_by_public_slug() method missing.\n"
        "Required by public profile router GET /{clinic_slug}/doctors/{doctor_slug}."
    )


def test_generic_404_detail_constant_exists() -> None:
    """Anti-enumeration sentinel must be defined in public_doctors_router."""
    from src.modules.vitalia.clinics.api.public_doctors_router import (
        _GENERIC_PROFILE_404_DETAIL,
    )

    assert _GENERIC_PROFILE_404_DETAIL == "Perfil no disponible", (
        f"Generic 404 detail must be 'Perfil no disponible' for anti-enumeration (RN-D3D-9).\n"
        f"Got: '{_GENERIC_PROFILE_404_DETAIL}'"
    )
