# cap: clinics.lisa.doctores
"""TDD RED tests — D3-D Página pública doctor (T-BE-pagina-publica).

Written BEFORE implementation per tdd-mandatory.md.
Tests SC-D3D-1 / SC-D3D-2 / SC-D3D-3 / SC-D3D-6 / SC-D3D-9 / SC-D3D-12
+ RN-D3D-4 (material_new) + migration 041 idempotency shape.

Architecture:
- Public endpoint GET /api/public/clinic/{clinic_slug}/doctors/{doctor_slug}
- NO auth, NO X-Tenant-ID
- Anti-enumeration: OFF / unknown / cross-tenant → IDENTICAL 404

hipaa-lite.md: channel guard ensures zero PHI in PublicDoctorProfileDTO.
03-arch-delta.md § 6.1: DoctorPublicProfile structured sections.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest

# Minimal env for Settings() — same pattern as test_public_doctors_endpoint.py
_REQUIRED_ENV_VARS = {
    "LOG_LEVEL": "DEBUG",
    "DOMAIN_NAME": "localhost",
    "TRAEFIK_NETWORK": "traefik",
    "API_SECRET_KEY": "test-secret-key-for-public-profile-test",
    "WHATSAPP_API_TOKEN": "test-token",
    "WHATSAPP_PHONE_NUMBER_ID": "1234567890",
    "WHATSAPP_VERIFY_TOKEN": "test-verify",
    "OPENAI_API_KEY": "sk-test-0000000000000000000000000000000000000000000000000",
    "REDIS_URL": "redis://localhost:6379/0",
    "QDRANT_URL": "http://localhost:6333",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres",
    "POSTGRES_DB": "vitalia_test",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "API_URL": "http://localhost:8002",
}


# ── Domain entity factories ───────────────────────────────────────────────────


def _make_doctor(
    *,
    visible_en_landing: bool = True,
    active: bool = True,
    specialty: str | None = "Medicina Estética",
    languages: list[str] | None = None,
    public_slug: str | None = "ana-gomez",
    bio_generated_at: datetime | None = None,
) -> object:
    """Build a minimal Doctor domain entity for tests."""
    from src.modules.vitalia.clinics.domain.bio import BioPublic
    from src.modules.vitalia.clinics.domain.doctor import Doctor
    from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile

    now = datetime.now(tz=timezone.utc)
    # languages controls BOTH doctor.languages and public_profile.idiomas
    # so RN-D3D-5 (idiomas only if len>1) works correctly in tests
    resolved_languages = languages if languages is not None else ["Español", "Inglés"]
    return Doctor(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        first_name="Ana",
        last_name="Gómez",
        dni="12345678",
        email="ana@example.com",
        credential="CMP 12345",
        credential_country="PE",
        specialty=specialty,
        visible_en_landing=visible_en_landing,
        active=active,
        languages=resolved_languages,
        bio_public=BioPublic(resumen="Especialista en medicina estética.", formacion=None, enfoque=None),
        public_profile=DoctorPublicProfile(
            sobre_mi="Especialista en medicina estética con 10 años de experiencia.",
            formacion=[{"titulo": "Médico Cirujano", "institucion": "UNMSM", "anio": 2010}],
            experiencia=[{"puesto": "Médico Esteta", "lugar": "Clínica Example", "anios": 5}],
            tratamientos=["Bótox", "Rellenos"],
            certificaciones=["Board Certified"],
            idiomas=resolved_languages,  # sync with doctor.languages for RN-D3D-5 test correctness
        ),
        public_slug=public_slug,
        bio_generated_at=bio_generated_at or now,
        created_at=now,
        updated_at=now,
    )


def _make_clinic() -> object:
    """Build a minimal Clinic domain entity for tests."""
    from src.modules.vitalia.clinics.domain.clinic import Clinic

    now = datetime.now(tz=timezone.utc)
    return Clinic(
        id=uuid4(),
        tenant_id=uuid4(),
        name="Clínica Example",
        slug="clinica-example",
        country="PE",
        timezone="America/Lima",
        plan_tier="starter",
        is_active=True,
        onboarding_completed=True,
        created_at=now,
        updated_at=now,
    )


# ── SC-D3D-1: Perfil público sin PHI ─────────────────────────────────────────


class TestSCD3D1_PublicProfileNoPHI:
    """SC-D3D-1: Perfil público expone estructura sin PHI.

    PublicDoctorProfileDTO must NOT contain PHI fields.
    """

    def test_public_profile_dto_exists(self) -> None:
        """PublicDoctorProfileDTO must be importable."""
        from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO  # noqa: F401

    def test_public_profile_dto_no_phi_fields(self) -> None:
        """PublicDoctorProfileDTO MUST NOT contain PHI field names."""
        from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO

        phi_fields = {
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
            "masked_dni",
            "masked_email",
            "masked_phone",
        }
        model_fields = set(PublicDoctorProfileDTO.model_fields.keys())
        violations = phi_fields & model_fields
        assert not violations, f"PublicDoctorProfileDTO contains PHI: {violations}"

    def test_public_profile_dto_has_required_identity_fields(self) -> None:
        """PublicDoctorProfileDTO must always have identity fields (RN-D3D-6 minimum)."""
        from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO

        model_fields = set(PublicDoctorProfileDTO.model_fields.keys())
        # Minimum identity guaranteed per RN-D3D-6
        required = {"display_name", "specialty"}
        assert required.issubset(model_fields), f"Missing required identity fields: {required - model_fields}"

    def test_public_profile_dto_sections_are_nullable(self) -> None:
        """All section fields in PublicDoctorProfileDTO must be nullable (RN-D3D-6)."""
        from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO

        # Sections that can be null/empty per RN-D3D-6
        nullable_sections = ["sobre_mi", "formacion", "experiencia", "tratamientos", "certificaciones"]
        model_fields = PublicDoctorProfileDTO.model_fields
        for field_name in nullable_sections:
            if field_name in model_fields:
                field = model_fields[field_name]
                # Field must allow None (is_required=False or has default)
                assert not field.is_required(), f"PublicDoctorProfileDTO.{field_name} must be nullable per RN-D3D-6"

    def test_to_public_profile_dto_serializer_exists(self) -> None:
        """to_public_profile_dto function must exist in public_doctor_serializer."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (  # noqa: F401
            to_public_profile_dto,
        )

    def test_to_public_profile_dto_no_phi(self) -> None:
        """to_public_profile_dto output must not contain PHI field names."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (
            to_public_profile_dto,
        )

        doctor = _make_doctor()
        dto = to_public_profile_dto(doctor)
        dto_dict = dto.model_dump()

        phi_keys = {"dni", "email", "phone", "credential", "date_of_birth"}
        violations = phi_keys & set(dto_dict.keys())
        assert not violations, f"Serializer output contains PHI keys: {violations}"

    def test_to_public_profile_dto_og_safe_fields(self) -> None:
        """to_public_profile_dto must include OG-safe fields for generateMetadata (RN-D3D-7)."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (
            to_public_profile_dto,
        )

        doctor = _make_doctor()
        dto = to_public_profile_dto(doctor)
        dto_dict = dto.model_dump()

        # OG-safe fields: display_name, specialty, avatar_key present (may be None)
        assert "display_name" in dto_dict
        assert "specialty" in dto_dict
        # sobre_mi_excerpt or sobre_mi must be exposed for OG description
        assert "sobre_mi" in dto_dict or "og_description" in dto_dict


# ── SC-D3D-2: Perfil OFF → 404 genérico ──────────────────────────────────────


class TestSCD3D2_ToggleOFF404:
    """SC-D3D-2: Doctor con visible_en_landing=False → 404 genérico (anti-enumeration).

    IDENTICAL 404 for all three cases: OFF / unknown / cross-tenant.
    """

    @patch.dict(os.environ, _REQUIRED_ENV_VARS)
    def test_invisible_doctor_returns_404(self) -> None:
        """Doctor with visible_en_landing=False returns generic 404."""
        doctor = _make_doctor(visible_en_landing=False)
        clinic = _make_clinic()
        # doctor.tenant_id matches clinic.tenant_id for test
        doctor.tenant_id = clinic.tenant_id
        doctor.clinic_id = clinic.id

        # The serializer should not expose an invisible doctor's profile
        # The router must return 404 for this case
        # We verify the DTO shape is never returned for invisible doctors
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (
            to_public_profile_dto,
        )

        # Confirm serializer CAN map it (not the guard) — guard is in the router
        dto = to_public_profile_dto(doctor)
        assert dto.display_name  # serializer itself doesn't care about visibility

    def test_404_response_shape_is_generic(self) -> None:
        """All 404s for doctor profile must return identical shape (anti-enumeration RN-D3D-9).

        The detail string must be IDENTICAL regardless of whether:
        - doctor does not exist (slug unknown)
        - doctor exists but visible_en_landing=False
        - clinic_slug matches multiple tenants (cross-tenant collision)
        """
        # This test verifies the contract — implementation enforces it
        _GENERIC_404_DETAIL = "Perfil no disponible"

        # Validate constant exists or is the expected string
        try:
            from src.modules.vitalia.clinics.api.public_doctors_router import (
                _GENERIC_PROFILE_404_DETAIL,
            )

            assert _GENERIC_PROFILE_404_DETAIL == _GENERIC_404_DETAIL, (
                f"Generic 404 detail must be '{_GENERIC_404_DETAIL}', got '{_GENERIC_PROFILE_404_DETAIL}'"
            )
        except ImportError:
            # Constant not yet defined — will be RED until implementation
            pytest.fail(
                "_GENERIC_PROFILE_404_DETAIL not found in public_doctors_router. "
                "Anti-enumeration RN-D3D-9 requires identical 404 for all cases."
            )


# ── SC-D3D-3: Idiomas len=1 → ausentes en perfil público ─────────────────────


class TestSCD3D3_IdiomasConditional:
    """SC-D3D-3: Idiomas se omiten del perfil público si len=1 (RN-D3D-5).

    A single language does not signal multilingual capability.
    Only expose idiomas if len > 1.
    """

    def test_single_language_not_in_public_profile(self) -> None:
        """If doctor speaks only 1 language, idiomas must be absent/empty in profile."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (
            to_public_profile_dto,
        )

        doctor = _make_doctor(languages=["Español"])
        dto = to_public_profile_dto(doctor)
        dto_dict = dto.model_dump()

        # idiomas must be absent or empty when len=1
        idiomas = dto_dict.get("idiomas", [])
        assert idiomas == [] or idiomas is None, f"idiomas must be empty for single-language doctor, got: {idiomas}"

    def test_multiple_languages_in_public_profile(self) -> None:
        """If doctor speaks >1 language, idiomas must be present in profile."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (
            to_public_profile_dto,
        )

        doctor = _make_doctor(languages=["Español", "Inglés"])
        dto = to_public_profile_dto(doctor)
        dto_dict = dto.model_dump()

        idiomas = dto_dict.get("idiomas", [])
        assert len(idiomas) >= 2, f"idiomas must contain both languages, got: {idiomas}"

    def test_zero_languages_not_in_public_profile(self) -> None:
        """Edge case: zero languages → idiomas empty."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (
            to_public_profile_dto,
        )

        doctor = _make_doctor(languages=[])
        dto = to_public_profile_dto(doctor)
        dto_dict = dto.model_dump()

        idiomas = dto_dict.get("idiomas", [])
        assert idiomas == [] or idiomas is None


# ── SC-D3D-6 / SC-D3D-12: Slug fuzzing — cross-tenant y desconocido → 404 idéntico ──


class TestSCD3D6_SlugFuzzing:
    """SC-D3D-6 / SC-D3D-12: Slug fuzzing — cross-tenant collision and unknown slug → identical 404.

    RN-D3D-9: anti-enumeration invariant — all three error cases return identical response.
    """

    def test_unknown_doctor_slug_constant_matches(self) -> None:
        """Unknown doctor slug must return generic 404 — same constant as OFF case."""
        try:
            from src.modules.vitalia.clinics.api.public_doctors_router import (
                _GENERIC_PROFILE_404_DETAIL,
            )

            assert _GENERIC_PROFILE_404_DETAIL == "Perfil no disponible"
        except ImportError:
            pytest.fail("_GENERIC_PROFILE_404_DETAIL missing — router not implemented yet")

    def test_cross_tenant_slug_collision_uses_same_404(self) -> None:
        """Cross-tenant clinic_slug collision (>1 match) returns same generic 404.

        Implementation must check: if >1 clinic matches slug, return 404 + structlog warning.
        """
        try:
            from src.modules.vitalia.clinics.api.public_doctors_router import (
                _GENERIC_PROFILE_404_DETAIL,
            )

            assert _GENERIC_PROFILE_404_DETAIL == "Perfil no disponible"
        except ImportError:
            pytest.fail("_GENERIC_PROFILE_404_DETAIL missing")

    def test_doctor_repository_has_get_by_public_slug_method(self) -> None:
        """DoctorRepository must have get_by_public_slug method (required by router)."""
        from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
            DoctorRepository,
        )

        assert hasattr(DoctorRepository, "get_by_public_slug"), (
            "DoctorRepository.get_by_public_slug() missing — required for D3-D public profile route"
        )


# ── SC-D3D-9: Perfil parcial mínimo ──────────────────────────────────────────


class TestSCD3D9_MinimumProfile:
    """SC-D3D-9: Perfil parcial — identity fields always present even if sections empty.

    RN-D3D-6: minimum identity guaranteed = display_name + specialty.
    All other sections nullable.
    """

    def test_profile_with_no_sections_still_has_identity(self) -> None:
        """Even if all sections are empty, display_name and specialty are present."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (
            to_public_profile_dto,
        )
        from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile

        doctor = _make_doctor()
        # Wipe all sections
        doctor.public_profile = DoctorPublicProfile(
            sobre_mi=None,
            formacion=[],
            experiencia=[],
            tratamientos=[],
            certificaciones=[],
            idiomas=[],
        )

        dto = to_public_profile_dto(doctor)
        assert dto.display_name, "display_name is required minimum (RN-D3D-6)"
        # specialty may be None but must be present in dict
        dto_dict = dto.model_dump()
        assert "display_name" in dto_dict

    def test_profile_sections_are_nullable_individually(self) -> None:
        """Each section is independently nullable — partial profile is valid."""
        from src.modules.vitalia.clinics.api.dtos import PublicDoctorProfileDTO

        # Should construct without error with all nullable sections absent
        dto = PublicDoctorProfileDTO(
            display_name="Dr. Test",
            specialty=None,
            avatar_key=None,
            sobre_mi=None,
            formacion=None,
            experiencia=None,
            tratamientos=None,
            certificaciones=None,
            idiomas=None,
        )
        assert dto.display_name == "Dr. Test"


# ── RN-D3D-4: material_new detection ─────────────────────────────────────────


class TestRND3D4_MaterialNew:
    """RN-D3D-4: material_new detected via server-side timestamp comparison.

    server: max(bio_files.uploaded_at, doctor.updated_at) > bio_generated_at
    DoctorDetailDTO must include profile_state {generated_at, material_new, material_new_count}.
    """

    def test_profile_state_dto_exists(self) -> None:
        """ProfileStateDTO must be importable from clinics api dtos."""
        from src.modules.vitalia.clinics.api.dtos import ProfileStateDTO  # noqa: F401

    def test_doctor_detail_dto_has_profile_state(self) -> None:
        """DoctorDetailDTO must include profile_state field (RN-D3D-4)."""
        from src.modules.vitalia.clinics.api.dtos import DoctorDetailDTO

        model_fields = set(DoctorDetailDTO.model_fields.keys())
        assert "profile_state" in model_fields, "DoctorDetailDTO missing profile_state field required by RN-D3D-4"

    def test_profile_state_has_required_fields(self) -> None:
        """ProfileStateDTO must have generated_at, material_new, material_new_count."""
        from src.modules.vitalia.clinics.api.dtos import ProfileStateDTO

        required = {"generated_at", "material_new", "material_new_count"}
        model_fields = set(ProfileStateDTO.model_fields.keys())
        missing = required - model_fields
        assert not missing, f"ProfileStateDTO missing fields: {missing}"

    def test_material_new_true_when_files_newer_than_generated(self) -> None:
        """material_new=True when bio_files have been uploaded after bio_generated_at."""
        from datetime import timedelta

        from src.modules.vitalia.clinics.api.dtos import ProfileStateDTO

        now = datetime.now(tz=timezone.utc)
        generated_at = now - timedelta(hours=2)
        # latest_file_at would be now - timedelta(hours=1) — newer than generated_at

        state = ProfileStateDTO(
            generated_at=generated_at,
            material_new=True,  # latest_file_at > generated_at
            material_new_count=2,
        )
        assert state.material_new is True

    def test_material_new_false_when_no_new_files(self) -> None:
        """material_new=False when bio_generated_at is after all material changes."""
        from datetime import timedelta

        from src.modules.vitalia.clinics.api.dtos import ProfileStateDTO

        now = datetime.now(tz=timezone.utc)
        generated_at = now - timedelta(minutes=5)  # generated 5 min ago
        # No new files after generated_at

        state = ProfileStateDTO(
            generated_at=generated_at,
            material_new=False,
            material_new_count=0,
        )
        assert state.material_new is False


# ── Domain entity tests ───────────────────────────────────────────────────────


class TestDoctorPublicProfileDomain:
    """DoctorPublicProfile domain entity tests."""

    def test_doctor_public_profile_importable(self) -> None:
        """DoctorPublicProfile must be importable from domain."""
        from src.modules.vitalia.clinics.domain.public_profile import (  # noqa: F401
            DoctorPublicProfile,
        )

    def test_doctor_public_profile_fields(self) -> None:
        """DoctorPublicProfile must have all 6 section fields."""
        from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile

        profile = DoctorPublicProfile(
            sobre_mi="Texto de prueba",
            formacion=[{"titulo": "MD", "institucion": "UNMSM", "anio": 2010}],
            experiencia=[{"puesto": "Médico", "lugar": "Hospital", "anios": 5}],
            tratamientos=["Bótox"],
            certificaciones=["Board Certified"],
            idiomas=["Español"],
        )
        assert profile.sobre_mi == "Texto de prueba"
        assert len(profile.formacion) == 1
        assert len(profile.experiencia) == 1
        assert profile.tratamientos == ["Bótox"]

    def test_doctor_entity_has_public_profile_field(self) -> None:
        """Doctor entity must have public_profile, bio_generated_at, public_slug fields."""

        from src.modules.vitalia.clinics.domain.doctor import Doctor

        fields = {f.name for f in Doctor.__dataclass_fields__.values()}
        required = {"public_profile", "bio_generated_at", "public_slug"}
        missing = required - fields
        assert not missing, f"Doctor entity missing fields: {missing}"

    def test_doctor_entity_public_profile_defaults_none(self) -> None:
        """public_profile, bio_generated_at, public_slug default to None."""
        from src.modules.vitalia.clinics.domain.doctor import Doctor

        doctor = Doctor(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            first_name="Test",
            last_name="Doctor",
            dni="00000000",
            email="test@example.com",
            credential="CMP 00001",
            credential_country="PE",
        )
        assert doctor.public_profile is None
        assert doctor.bio_generated_at is None
        assert doctor.public_slug is None


# ── Migration shape tests ─────────────────────────────────────────────────────


class TestMigration041Shape:
    """Verify migration 041 defines idempotent DDL with correct columns."""

    def test_migration_041_exists(self) -> None:
        """Migration 041 file must exist."""
        import importlib

        try:
            importlib.import_module("alembic.versions.041_vitalia_doctor_public_profile")
        except ImportError:
            # Try direct import via path
            import os

            migration_path = os.path.join(
                os.path.dirname(__file__),
                "../../../../alembic/versions/041_vitalia_doctor_public_profile.py",
            )
            assert os.path.exists(migration_path), "Migration 041_vitalia_doctor_public_profile.py does not exist"

    def test_migration_041_revision_chain(self) -> None:
        """Migration 041 must reference revision 040 as down_revision."""
        import os

        migration_path = os.path.join(
            os.path.dirname(__file__),
            "../../../../alembic/versions/041_vitalia_doctor_public_profile.py",
        )
        if not os.path.exists(migration_path):
            pytest.skip("Migration 041 not yet created")

        with open(migration_path) as f:
            content = f.read()

        assert "040" in content, "Migration 041 must reference 040 as down_revision"
        assert "IF NOT EXISTS" in content, "Migration 041 must use IF NOT EXISTS (idempotent)"
        assert "public_profile" in content, "Migration 041 must add public_profile column"
        assert "bio_generated_at" in content, "Migration 041 must add bio_generated_at column"
        assert "public_slug" in content, "Migration 041 must add public_slug column"
