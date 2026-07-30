# cap: clinics.lisa.doctores
"""TDD RED-first: GET /{doctor_id} must populate profileState + publicProfile + publicSlug.

T-BE-detail-profile-state (vitalia-fase2-lisa-doctores story).

Gap: DoctorDetailDTO has profile_state field but _to_detail_dto never populates it.
Also missing public_profile and public_slug in DoctorDetailDTO.

Scenarios:
  1. DoctorDetailDTO has public_profile + public_slug fields
  2. ProfileStateDTO camelCase aliases correct (generatedAt/materialNew/materialNewCount)
  3. GET detail after generate-profile: profileState.generatedAt populated, materialNew=False
  4. GET detail after uploading file post-generation: materialNew=True, materialNewCount=1
  5. GET detail without generated profile but with material: materialNew=True (no generated_at)
  6. publicProfile camelCase (sobreMi, formacion, etc.) in JSON response
  7. GET detail without any generation: profileState=None (not null sentinel, just absent)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.vitalia.clinics.domain.doctor import Doctor
from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile

# ── Helpers ───────────────────────────────────────────────────────────────────


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_doctor(
    bio_generated_at: datetime | None = None,
    public_profile: DoctorPublicProfile | None = None,
    public_slug: str | None = None,
    tenant_id: Any | None = None,
    clinic_id: Any | None = None,
) -> Doctor:
    d = Doctor(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        clinic_id=clinic_id or uuid4(),
        first_name="Ana",
        last_name="García Mendoza",
        dni="12345678",
        email="dra.ana@clinica.pe",
        phone=None,
        specialty="Odontología cosmética",
        credential="CMP-12345",
        credential_country="PE",
        years_experience=12,
        languages=["es", "en"],
        bio_inputs_notes="Especialista en implantes con 12 años de experiencia.",
        bio_links=[],
        bio_public=None,
        public_profile=public_profile,
        bio_generated_at=bio_generated_at,
        public_slug=public_slug,
        avatar_key=None,
        visible_en_landing=True,
        active=True,
    )
    return d


def _make_bio_file_domain(uploaded_at: datetime):
    """Create a minimal DoctorBioFile-like object for testing."""
    from src.modules.vitalia.clinics.domain.bio_file import DoctorBioFile  # noqa: PLC0415

    return DoctorBioFile(
        id=uuid4(),
        doctor_id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        storage_key="bio_doc/test.pdf",
        filename="cv_dra_ana.pdf",
        size_bytes=204800,
        content_type="application/pdf",
        uploaded_at=uploaded_at,
    )


def _make_structured_profile() -> DoctorPublicProfile:
    return DoctorPublicProfile(
        sobre_mi="Especialista en odontología cosmética con más de 12 años de experiencia.",
        formacion=[{"titulo": "Odontóloga", "institucion": "UPCH", "anio": "2010"}],
        experiencia=[{"puesto": "Directora", "lugar": "Clínica Sonrisa", "anios": 8}],
        tratamientos=["Implantes dentales", "Blanqueamiento", "Carillas"],
        certificaciones=["Certificación AEEDC"],
        idiomas=["Español", "Inglés"],
    )


# ── 1. DTO structural gates ───────────────────────────────────────────────────


def test_doctor_detail_dto_has_public_profile_field() -> None:
    """DoctorDetailDTO must have public_profile: PublicDoctorProfileDTO | None field.

    RED: fails until field is added to DoctorDetailDTO.
    FE DoctorPaginaView reads doctor.publicProfile.{sobreMi, formacion, ...}.
    """
    from src.modules.vitalia.clinics.api.dtos import DoctorDetailDTO

    fields = DoctorDetailDTO.model_fields
    assert "public_profile" in fields, "DoctorDetailDTO must have 'public_profile' field for FE DoctorPaginaView"


def test_doctor_detail_dto_has_public_slug_field() -> None:
    """DoctorDetailDTO must have public_slug: str | None field.

    RED: fails until field is added to DoctorDetailDTO.
    FE uses publicSlug to build the doctor page URL.
    """
    from src.modules.vitalia.clinics.api.dtos import DoctorDetailDTO

    fields = DoctorDetailDTO.model_fields
    assert "public_slug" in fields, "DoctorDetailDTO must have 'public_slug' field (alias: publicSlug for FE URL)"


# ── 2. ProfileStateDTO camelCase aliases ──────────────────────────────────────


def test_profile_state_dto_generated_at_alias_is_camel() -> None:
    """ProfileStateDTO must serialize generated_at → generatedAt (camelCase wire contract).

    FE DoctorPaginaView reads doctor.profileState.generatedAt.
    """
    from src.modules.vitalia.clinics.api.dtos import ProfileStateDTO

    now = _utc_now()
    dto = ProfileStateDTO(generated_at=now, material_new=False, material_new_count=0)
    payload = dto.model_dump(by_alias=True)
    assert "generatedAt" in payload, (
        f"ProfileStateDTO must alias generated_at → generatedAt; got keys: {list(payload.keys())}"
    )
    assert "materialNew" in payload, (
        f"ProfileStateDTO must alias material_new → materialNew; got keys: {list(payload.keys())}"
    )
    assert "materialNewCount" in payload, (
        f"ProfileStateDTO must alias material_new_count → materialNewCount; got keys: {list(payload.keys())}"
    )


# ── 3. GET detail post-generation: profileState populated, materialNew=False ──


@pytest.mark.asyncio
async def test_get_detail_after_generation_profile_state_populated() -> None:
    """GET /{doctor_id} after generate-profile: profileState.generatedAt populated, materialNew False.

    Scenario: doctor has bio_generated_at set, no files uploaded after generation.
    Expected: profileState = {generatedAt: <ts>, materialNew: false, materialNewCount: 0}.
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()
    generated_at = _utc_now() - timedelta(minutes=10)

    profile = _make_structured_profile()
    doctor = _make_doctor(
        bio_generated_at=generated_at,
        public_profile=profile,
        public_slug="dra-ana-garcia-mendoza",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )
    doctor.id = doctor_id

    # No bio files uploaded after generation
    bio_files: list = []

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_bio_file_service") as mock_build_files,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_clinic_repository") as mock_build_clinic,
    ):
        mock_svc = MagicMock()
        mock_svc.get_doctor = AsyncMock(return_value=doctor)
        mock_build.return_value = mock_svc

        mock_file_svc = MagicMock()
        mock_file_svc.list_files = AsyncMock(return_value=bio_files)
        mock_build_files.return_value = mock_file_svc
        _clinic = MagicMock()
        _clinic.slug = "sonrisas-lima"
        mock_build_clinic.return_value = MagicMock(get_by_id=AsyncMock(return_value=_clinic))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                },
            )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()

    # profileState must be populated
    assert "profileState" in body, f"Response must contain 'profileState'; got keys: {list(body.keys())}"
    ps = body["profileState"]
    assert ps is not None, "profileState must not be null after generate-profile"
    assert "generatedAt" in ps, f"profileState must have generatedAt; got: {ps}"
    assert ps["generatedAt"] is not None, "generatedAt must be non-null after generation"
    assert ps["materialNew"] is False, f"materialNew must be False (no files uploaded after gen); got: {ps}"
    assert ps["materialNewCount"] == 0, f"materialNewCount must be 0; got: {ps}"


# ── 4. GET detail after file upload post-generation: materialNew=True ─────────


@pytest.mark.asyncio
async def test_get_detail_after_file_upload_material_new_true() -> None:
    """GET /{doctor_id} after uploading a file post-generation: materialNew=True, materialNewCount=1.

    Scenario: bio_generated_at=T, then file uploaded at T+5min.
    Expected: profileState.materialNew=True, materialNewCount=1.
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()

    generated_at = _utc_now() - timedelta(hours=1)
    profile = _make_structured_profile()
    doctor = _make_doctor(
        bio_generated_at=generated_at,
        public_profile=profile,
        public_slug="dra-ana-garcia-mendoza",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )
    doctor.id = doctor_id

    # 1 file uploaded AFTER generation
    file_uploaded_after = _make_bio_file_domain(uploaded_at=_utc_now() - timedelta(minutes=30))
    bio_files = [file_uploaded_after]

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_bio_file_service") as mock_build_files,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_clinic_repository") as mock_build_clinic,
    ):
        mock_svc = MagicMock()
        mock_svc.get_doctor = AsyncMock(return_value=doctor)
        mock_build.return_value = mock_svc

        mock_file_svc = MagicMock()
        mock_file_svc.list_files = AsyncMock(return_value=bio_files)
        mock_build_files.return_value = mock_file_svc
        _clinic = MagicMock()
        _clinic.slug = "sonrisas-lima"
        mock_build_clinic.return_value = MagicMock(get_by_id=AsyncMock(return_value=_clinic))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                },
            )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    ps = body.get("profileState")
    assert ps is not None, "profileState must be present"
    assert ps["materialNew"] is True, f"materialNew must be True (file uploaded after gen); got: {ps}"
    assert ps["materialNewCount"] == 1, f"materialNewCount must be 1; got: {ps}"


# ── 5. GET detail without generated profile + with material: materialNew=True ─


@pytest.mark.asyncio
async def test_get_detail_no_generation_with_material_profile_state_none() -> None:
    """GET /{doctor_id} when no profile generated yet: profileState=None.

    Scenario: bio_generated_at=None (never generated), has notes.
    Per task spec: profile_state is None when never generated.
    FE must null-guard this and show 'Borrador / sin generar'.

    Note: task spec says profileState=None (not {materialNew:True}) when never generated.
    The FE checks profileState.generatedAt to show the 'generate' button.
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()

    # Never generated (bio_generated_at=None), but has bio material
    doctor = _make_doctor(
        bio_generated_at=None,
        public_profile=None,
        public_slug=None,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )
    doctor.id = doctor_id

    # Has a file uploaded, but no generation yet
    file = _make_bio_file_domain(uploaded_at=_utc_now() - timedelta(hours=2))
    bio_files = [file]

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_bio_file_service") as mock_build_files,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_clinic_repository") as mock_build_clinic,
    ):
        mock_svc = MagicMock()
        mock_svc.get_doctor = AsyncMock(return_value=doctor)
        mock_build.return_value = mock_svc

        mock_file_svc = MagicMock()
        mock_file_svc.list_files = AsyncMock(return_value=bio_files)
        mock_build_files.return_value = mock_file_svc
        _clinic = MagicMock()
        _clinic.slug = "sonrisas-lima"
        mock_build_clinic.return_value = MagicMock(get_by_id=AsyncMock(return_value=_clinic))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                },
            )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    # profileState must be None when never generated
    assert body.get("profileState") is None, (
        f"profileState must be null when bio_generated_at=None; got: {body.get('profileState')}"
    )


# ── 6. publicProfile camelCase in JSON response ────────────────────────────────


@pytest.mark.asyncio
async def test_get_detail_public_profile_camel_case_in_response() -> None:
    """GET /{doctor_id} with generated profile: publicProfile + publicSlug in camelCase JSON.

    FE reads doctor.publicProfile.sobreMi, doctor.publicSlug for the profile view.
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()

    generated_at = _utc_now() - timedelta(minutes=5)
    profile = _make_structured_profile()
    doctor = _make_doctor(
        bio_generated_at=generated_at,
        public_profile=profile,
        public_slug="dra-ana-garcia-mendoza",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )
    doctor.id = doctor_id

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_bio_file_service") as mock_build_files,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_clinic_repository") as mock_build_clinic,
    ):
        mock_svc = MagicMock()
        mock_svc.get_doctor = AsyncMock(return_value=doctor)
        mock_build.return_value = mock_svc

        mock_file_svc = MagicMock()
        mock_file_svc.list_files = AsyncMock(return_value=[])
        mock_build_files.return_value = mock_file_svc
        _clinic = MagicMock()
        _clinic.slug = "sonrisas-lima"
        mock_build_clinic.return_value = MagicMock(get_by_id=AsyncMock(return_value=_clinic))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                },
            )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()

    # publicProfile must be present in camelCase
    assert "publicProfile" in body, f"Response must contain 'publicProfile' (camelCase); got keys: {list(body.keys())}"
    pp = body["publicProfile"]
    assert pp is not None, "publicProfile must not be null when profile is generated"
    assert "sobreMi" in pp, f"publicProfile must contain 'sobreMi' (camelCase); got keys: {list(pp.keys())}"

    # publicSlug must be present
    assert "publicSlug" in body, f"Response must contain 'publicSlug' (camelCase); got keys: {list(body.keys())}"
    assert body["publicSlug"] == "dra-ana-garcia-mendoza", f"publicSlug must match; got: {body.get('publicSlug')}"
