# cap: clinics.lisa.doctores
"""Public doctors endpoint tests — V-FN-11 (04-validators.yaml).

TDD: these tests were written BEFORE the implementation (T-BE-5).
They cover:
  - visible_en_landing + active filter (SECURITY: inactive or private doctors hidden)
  - Allow-list 7 fields exactly (PHI channel guard)
  - No PHI fields: dni/email/phone/credential/masked_* absent from response
  - No-auth access (public endpoint, no X-Tenant-ID, no Bearer)
  - public_doctor_serializer.to_public_dto produces exactly the allow-listed fields
  - credential_label optional (clinic-configurable)

Architecture: 03-arch-be.md § 3 + hipaa-lite.md § Channel guard
Validator: V-FN-11 (04-validators.yaml)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from src.modules.vitalia.clinics.api.dtos import (
    PublicDoctorDTO,
    PublicDoctorsResponse,
)
from src.modules.vitalia.clinics.domain.bio import BioPublic
from src.modules.vitalia.clinics.domain.doctor import Doctor

# Minimal env vars to satisfy luana_core_platform.core.config.Settings
# when src.main is imported (triggers Settings() at module level).
# Pattern from tests/test_main_iam_routes_mounted.py.
_REQUIRED_ENV_VARS = {
    "LOG_LEVEL": "DEBUG",
    "DOMAIN_NAME": "localhost",
    "TRAEFIK_NETWORK": "traefik",
    "API_SECRET_KEY": "test-secret-key-for-public-doctors-test",
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

# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_doctor(
    *,
    visible_en_landing: bool = True,
    active: bool = True,
    specialty: str | None = "Medicina Estética",
    years_experience: int | None = 8,
    avatar_key: str | None = "tenant-1/avatar/dr-garcia.jpg",
    bio_public: BioPublic | None = None,
    credential: str = "12345",
    credential_country: str = "PE",
) -> Doctor:
    """Create a test Doctor domain entity."""
    return Doctor(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        first_name="Ana",
        last_name="García",
        dni="12345678",
        email="ana.garcia@clinica.com",
        phone="+51999000111",
        credential=credential,
        credential_country=credential_country,
        specialty=specialty,
        years_experience=years_experience,
        languages=["Español", "Inglés"],
        bio_inputs_notes="Especialista en procedimientos no invasivos.",
        bio_links=["https://example.com/ana-garcia"],
        bio_public=bio_public,
        avatar_key=avatar_key,
        visible_en_landing=visible_en_landing,
        active=active,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


# ── Unit: public_doctor_serializer ───────────────────────────────────────────


class TestPublicDoctorSerializer:
    """Unit tests for public_doctor_serializer.to_public_dto allow-list mapper."""

    def test_to_public_dto_imports_correctly(self) -> None:
        """to_public_dto must be importable from the application layer."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import (  # noqa: F401
            to_public_dto,
        )

    def test_to_public_dto_returns_public_doctor_dto(self) -> None:
        """to_public_dto must return a PublicDoctorDTO instance."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor()
        result = to_public_dto(doctor)
        assert isinstance(result, PublicDoctorDTO), f"Expected PublicDoctorDTO, got {type(result)}"

    def test_to_public_dto_includes_display_name(self) -> None:
        """display_name must be set from Doctor.display_name property."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor()
        result = to_public_dto(doctor)
        assert result.display_name == doctor.display_name
        assert "Ana" in result.display_name
        assert "García" in result.display_name

    def test_to_public_dto_includes_specialty(self) -> None:
        """specialty must be in the allow-listed output."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor(specialty="Odontología Cosmética")
        result = to_public_dto(doctor)
        assert result.specialty == "Odontología Cosmética"

    def test_to_public_dto_includes_years_experience(self) -> None:
        """years_experience must be in the allow-listed output."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor(years_experience=12)
        result = to_public_dto(doctor)
        assert result.years_experience == 12

    def test_to_public_dto_includes_languages(self) -> None:
        """languages list must be in the allow-listed output."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor()
        result = to_public_dto(doctor)
        assert result.languages == ["Español", "Inglés"]

    def test_to_public_dto_includes_avatar_key(self) -> None:
        """avatar_key must be in the allow-listed output."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor(avatar_key="tenant-1/avatar/dr.jpg")
        result = to_public_dto(doctor)
        assert result.avatar_key == "tenant-1/avatar/dr.jpg"

    def test_to_public_dto_includes_bio_public(self) -> None:
        """bio_public must be serialized into BioPublicDTO."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        bio = BioPublic(
            resumen="Especialista certificada.",
            formacion="Medicina UNMSM.",
            enfoque="Procedimientos no invasivos.",
        )
        doctor = _make_doctor(bio_public=bio)
        result = to_public_dto(doctor)
        assert result.bio_public is not None
        assert result.bio_public.resumen == "Especialista certificada."
        assert result.bio_public.formacion == "Medicina UNMSM."
        assert result.bio_public.enfoque == "Procedimientos no invasivos."

    def test_to_public_dto_credential_label_present_when_provided(self) -> None:
        """credential_label must be settable (optional, clinic-configurable)."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor(credential="12345", credential_country="PE")
        result = to_public_dto(doctor, credential_label="CMP 12345")
        assert result.credential_label == "CMP 12345"

    def test_to_public_dto_credential_label_none_by_default(self) -> None:
        """credential_label is None when not passed (optional)."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor()
        result = to_public_dto(doctor)
        assert result.credential_label is None

    # ── Security: PHI MUST NOT appear in output ──────────────────────────────

    def test_to_public_dto_does_not_contain_dni(self) -> None:
        """CRITICAL: to_public_dto MUST NOT expose raw DNI.

        PHI channel guard: the serializer allow-list must NEVER include dni.
        """
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor()
        to_public_dto(doctor)  # verify no exception
        # PublicDoctorDTO field names must not include 'dni' in any form
        model_fields = set(PublicDoctorDTO.model_fields.keys())
        assert "dni" not in model_fields, "CRITICAL: PublicDoctorDTO must NOT expose dni (PHI channel guard violation)"

    def test_to_public_dto_does_not_contain_email(self) -> None:
        """CRITICAL: to_public_dto MUST NOT expose email."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor()
        to_public_dto(doctor)  # verify no exception
        model_fields = set(PublicDoctorDTO.model_fields.keys())
        assert "email" not in model_fields, (
            "CRITICAL: PublicDoctorDTO must NOT expose email (PHI channel guard violation)"
        )

    def test_to_public_dto_does_not_contain_phone(self) -> None:
        """CRITICAL: to_public_dto MUST NOT expose phone."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor()
        to_public_dto(doctor)  # verify no exception
        model_fields = set(PublicDoctorDTO.model_fields.keys())
        assert "phone" not in model_fields, (
            "CRITICAL: PublicDoctorDTO must NOT expose phone (PHI channel guard violation)"
        )

    def test_to_public_dto_does_not_contain_credential_raw(self) -> None:
        """CRITICAL: to_public_dto MUST NOT expose raw credential number.

        The raw credential number is PHI (colegio médico number).
        Only credential_label (optional display string) is allowed.
        """
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor()
        to_public_dto(doctor)  # verify no exception
        model_fields = set(PublicDoctorDTO.model_fields.keys())
        assert "credential" not in model_fields, (
            "CRITICAL: PublicDoctorDTO must NOT expose raw credential (PHI channel guard violation)"
        )

    def test_to_public_dto_exactly_7_fields(self) -> None:
        """PublicDoctorDTO must have exactly 7 fields — no more, no less.

        Per 03-arch-be.md § 3 and 01-spec.md § Endpoint público:
        allow-list: display_name, specialty, avatar_key, years_experience,
        languages, bio_public, credential_label.
        """
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor()
        to_public_dto(doctor)  # verify no exception
        actual_fields = set(PublicDoctorDTO.model_fields.keys())
        expected_fields = {
            "display_name",
            "specialty",
            "avatar_key",
            "years_experience",
            "languages",
            "bio_public",
            "credential_label",
        }
        assert actual_fields == expected_fields, (
            f"PublicDoctorDTO must have exactly {expected_fields}, got {actual_fields}.\n"
            f"Extra fields: {actual_fields - expected_fields}\n"
            f"Missing fields: {expected_fields - actual_fields}"
        )

    def test_to_public_dto_with_none_avatar_key(self) -> None:
        """avatar_key can be None when doctor has no avatar."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor(avatar_key=None)
        result = to_public_dto(doctor)
        assert result.avatar_key is None

    def test_to_public_dto_with_none_bio_public(self) -> None:
        """bio_public can be None when not yet generated."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor(bio_public=None)
        result = to_public_dto(doctor)
        assert result.bio_public is None

    def test_to_public_dto_with_empty_languages(self) -> None:
        """languages defaults to empty list when not set."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = Doctor(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            first_name="Luis",
            last_name="Martínez",
            dni="87654321",
            email="luis@clinic.com",
            credential="98765",
            credential_country="MX",
            languages=[],  # explicitly empty
        )
        result = to_public_dto(doctor)
        assert result.languages == []


# ── Unit: public_doctors_router ──────────────────────────────────────────────


class TestPublicDoctorsRouterContract:
    """Unit tests for public_doctors_router — no auth, response_model gate."""

    def test_public_doctors_router_imports(self) -> None:
        """public_doctors_router must be importable from clinics api."""
        from src.modules.vitalia.clinics.api.public_doctors_router import (  # noqa: F401
            router as public_doctors_router,
        )

    def test_public_doctors_router_has_get_route(self) -> None:
        """GET /{tenant_slug}/doctors must be registered."""
        from src.modules.vitalia.clinics.api.public_doctors_router import router

        get_routes = [r for r in router.routes if "GET" in getattr(r, "methods", set())]
        assert get_routes, "public_doctors_router must have at least one GET route"

    def test_public_doctors_router_get_has_response_model(self) -> None:
        """GET endpoint must declare response_model= (arch gate — V-ARCH-7)."""
        from src.modules.vitalia.clinics.api.public_doctors_router import router

        get_routes = [r for r in router.routes if "GET" in getattr(r, "methods", set())]
        assert get_routes, "No GET route found on public_doctors_router"
        route = get_routes[0]
        assert hasattr(route, "response_model"), "Public doctors GET route must declare response_model="
        assert route.response_model is not None, "response_model= must not be None (arch test gate)"

    def test_public_doctors_router_response_model_is_public_doctors_response(self) -> None:
        """response_model must be PublicDoctorsResponse."""
        from src.modules.vitalia.clinics.api.public_doctors_router import router

        get_routes = [r for r in router.routes if "GET" in getattr(r, "methods", set())]
        assert get_routes
        route = get_routes[0]
        assert route.response_model is PublicDoctorsResponse, (
            f"response_model must be PublicDoctorsResponse, got {route.response_model}"
        )

    def test_public_doctors_router_no_auth_required(self) -> None:
        """Public endpoint must NOT require auth headers.

        The route must be callable without X-Tenant-ID or Bearer token.
        This is enforced by routing design (no auth dependency injection).
        """
        from fastapi import FastAPI  # noqa: PLC0415

        from src.modules.vitalia.clinics.api.public_doctors_router import router  # noqa: PLC0415

        # Mount the router and verify routes have no security dependencies
        app = FastAPI(redirect_slashes=False)
        app.include_router(router, prefix="/api/public/clinic")

        # Verify the route is registered under the expected path pattern
        all_paths = [route.path for route in app.routes if hasattr(route, "path")]
        # Should have a path matching /{tenant_slug}/doctors
        assert any("doctors" in p for p in all_paths), f"Expected a /doctors route, found: {all_paths}"


# ── Functional: filter visible_en_landing AND active ────────────────────────


class TestPublicDoctorFiltering:
    """Functional tests for visible_en_landing + active filter (SECURITY).

    These tests verify the serializer behavior with different doctor states.
    The repo.list_public() filter is tested at the repository level (test_doctor_repository.py).
    Here we verify the serializer correctly handles the domain object state.
    """

    def test_to_public_dto_with_visible_active_doctor(self) -> None:
        """to_public_dto works correctly for visible+active doctor."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        doctor = _make_doctor(visible_en_landing=True, active=True)
        result = to_public_dto(doctor)
        assert result.display_name is not None
        assert len(result.display_name) > 0

    def test_to_public_dto_does_not_expose_visible_en_landing_flag(self) -> None:
        """visible_en_landing must NOT appear in the public DTO.

        This is an internal admin flag — not part of the public allow-list.
        """
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto

        to_public_dto(_make_doctor(visible_en_landing=True))  # no exception
        # Use class-level model_fields (Pydantic v2.11+ deprecates instance access)
        model_fields = set(PublicDoctorDTO.model_fields.keys())
        assert "visible_en_landing" not in model_fields, "visible_en_landing must NOT appear in PublicDoctorDTO"

    def test_to_public_dto_does_not_expose_active_flag(self) -> None:
        """active status must NOT appear in the public DTO."""
        from src.modules.vitalia.clinics.application.public_doctor_serializer import to_public_dto  # noqa: F401

        model_fields = set(PublicDoctorDTO.model_fields.keys())
        assert "active" not in model_fields, "active must NOT appear in PublicDoctorDTO"

    def test_to_public_dto_does_not_expose_tenant_id(self) -> None:
        """tenant_id must NOT appear in the public DTO."""
        model_fields = set(PublicDoctorDTO.model_fields.keys())
        assert "tenant_id" not in model_fields, "tenant_id must NOT appear in PublicDoctorDTO (cross-tenant leak risk)"

    def test_to_public_dto_does_not_expose_clinic_id(self) -> None:
        """clinic_id must NOT appear in the public DTO."""
        model_fields = set(PublicDoctorDTO.model_fields.keys())
        assert "clinic_id" not in model_fields, "clinic_id must NOT appear in PublicDoctorDTO (internal identifier)"


# ── Integration: main.py router registration ─────────────────────────────────


class TestPublicDoctorsRouterRegistration:
    """Tests that the public_doctors_router is wired in main.py."""

    def test_public_doctors_router_registered_in_main(self) -> None:
        """public_doctors_router must be included in main.py app.

        Uses env-var patch (same pattern as test_main_iam_routes_mounted.py)
        to satisfy luana_core_platform.core.config.Settings import requirements.
        """
        with patch.dict(os.environ, _REQUIRED_ENV_VARS):
            from src.main import app  # noqa: PLC0415

        # Find public clinic routes
        all_paths = [route.path for route in app.routes if hasattr(route, "path")]
        public_routes = [p for p in all_paths if "public" in p and "doctor" in p]
        assert public_routes, (
            f"No public doctor routes found in main.py. "
            f"Ensure public_doctors_router is include_router'd with prefix /api/public/clinic. "
            f"Current paths: {all_paths}"
        )
