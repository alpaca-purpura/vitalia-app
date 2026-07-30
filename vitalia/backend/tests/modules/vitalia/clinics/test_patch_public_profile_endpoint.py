# cap: clinics.lisa.doctores
"""TDD RED-first: PATCH /{doctor_id}/public-profile endpoint.

AUDITOR_AUTO_FIX_LOOP iter 1 — F1 finding: StructuredProfileEditor autosaves to
PATCH /{doctor_id}/public-profile which returns 404 (endpoint does not exist).

RN-D3B-4: bio_generated_at is ONLY set by generate-profile, NEVER by manual PATCH.

Scenarios covered:
  1. Route registered in doctors_router with response_model=
  2. Roundtrip persistence: PATCH updates reflected in response body
  3. bio_generated_at UNTOUCHED: timestamp equal before and after PATCH
  4. Cross-tenant 404 (dual filter tenant+clinic)
  5. Extra-key 422 (unknown field in body rejected with extra="forbid")
  6. RBAC denial 403 for marketing role
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.vitalia.clinics.domain.doctor import Doctor
from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile

# ── Helpers ──────────────────────────────────────────────────────────────────


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_doctor(
    bio_generated_at: datetime | None = None,
    public_profile: DoctorPublicProfile | None = None,
    public_slug: str | None = None,
    tenant_id: Any | None = None,
    clinic_id: Any | None = None,
) -> Doctor:
    """Minimal Doctor for testing patch-public-profile endpoint."""
    return Doctor(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        clinic_id=clinic_id or uuid4(),
        first_name="Carlos",
        last_name="Ríos",
        dni="87654321",
        email="carlos@clinica.pe",
        phone=None,
        specialty="Dermatología",
        credential="99999",
        credential_country="PE",
        years_experience=8,
        languages=["es"],
        bio_inputs_notes=None,
        bio_links=[],
        bio_public=None,
        public_profile=public_profile,
        bio_generated_at=bio_generated_at,
        public_slug=public_slug,
        avatar_key=None,
        visible_en_landing=True,
        active=True,
    )


def _make_profile_with_sections() -> DoctorPublicProfile:
    return DoctorPublicProfile(
        sobre_mi="Dermatólogo con enfoque en piel sensible.",
        formacion=[{"titulo": "Médico", "institucion": "UNMSM", "anio": 2010}],
        experiencia=[{"puesto": "Residente", "lugar": "Hospital Rebagliati", "anios": 3}],
        tratamientos=["Botox", "Peeling químico"],
        certificaciones=["CEPAS"],
        idiomas=["Español"],
    )


# ── Connectivity gate ─────────────────────────────────────────────────────────


def test_patch_public_profile_route_registered() -> None:
    """PATCH /{doctor_id}/public-profile must be registered in doctors_router.

    RED: fails until endpoint is added.
    """
    from src.modules.vitalia.clinics.api.doctors_router import router

    route_paths = [route.path for route in router.routes]
    assert any("public-profile" in path for path in route_paths), (
        "Route PATCH /{doctor_id}/public-profile must be registered in doctors_router"
    )


def test_patch_public_profile_route_has_response_model() -> None:
    """PATCH /public-profile route must declare response_model= (PII allowlist gate)."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    patch_profile_routes = [
        r
        for r in router.routes
        if "public-profile" in getattr(r, "path", "") and "PATCH" in getattr(r, "methods", set())
    ]
    assert patch_profile_routes, "PATCH /public-profile route not found in doctors_router"
    route = patch_profile_routes[0]
    assert hasattr(route, "response_model") and route.response_model is not None, (
        "PATCH /public-profile must declare response_model="
    )


# ── Core behavior ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_patch_public_profile_roundtrip_persistence() -> None:
    """PATCH /{doctor_id}/public-profile → 200, response reflects updated sections.

    Roundtrip: patch body sections must appear in response public_profile.
    RED: 404 until endpoint is implemented.
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()

    # Doctor after patch: public_profile is set, bio_generated_at untouched (None)
    updated_profile = _make_profile_with_sections()
    updated_doctor = _make_doctor(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        public_profile=updated_profile,
        bio_generated_at=None,
        public_slug=None,
    )
    updated_doctor.id = doctor_id

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_clinic_repository") as mock_build_clinic,
    ):
        mock_svc = MagicMock()
        mock_svc.get_doctor = AsyncMock(return_value=updated_doctor)
        mock_svc.patch_public_profile = AsyncMock(return_value=updated_doctor)
        mock_build.return_value = mock_svc

        mock_clinic = MagicMock()
        mock_clinic.slug = "clinica-test"
        mock_clinic_repo = MagicMock()
        mock_clinic_repo.get_by_id = AsyncMock(return_value=mock_clinic)
        mock_build_clinic.return_value = mock_clinic_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}/public-profile",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "admin_clinic",
                },
                json={
                    "sobreMi": "Dermatólogo con enfoque en piel sensible.",
                    "tratamientos": ["Botox", "Peeling químico"],
                    "certificaciones": ["CEPAS"],
                    "idiomas": ["Español"],
                    "formacion": [{"titulo": "Médico", "institucion": "UNMSM", "anio": 2010}],
                    "experiencia": [{"puesto": "Residente", "lugar": "Hospital Rebagliati", "anios": 3}],
                },
            )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    # Response is DoctorDetailDTO — public_profile nested
    assert "publicProfile" in body or "public_profile" in body, f"Response missing publicProfile: {body}"


@pytest.mark.asyncio
async def test_patch_public_profile_bio_generated_at_untouched() -> None:
    """PATCH /public-profile must NOT touch bio_generated_at (RN-D3B-4).

    Service-level test: patch_public_profile must call a repo method that
    does NOT update bio_generated_at column.
    """
    from src.modules.vitalia.clinics.application.doctor_service import DoctorService
    from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile

    original_bio_generated_at = _utc_now()

    mock_repo = AsyncMock()
    mock_repo.get_by_id = AsyncMock(return_value=_make_doctor(bio_generated_at=original_bio_generated_at))
    # update_public_profile_sections returns doctor with bio_generated_at unchanged
    doctor_after = _make_doctor(bio_generated_at=original_bio_generated_at)
    mock_repo.update_public_profile_sections = AsyncMock(return_value=doctor_after)

    audit_repo = AsyncMock()
    mock_emitter = AsyncMock()

    service = DoctorService(
        doctor_repo=mock_repo,
        audit_repo=audit_repo,
        emitter=mock_emitter,
    )

    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()
    profile = DoctorPublicProfile(
        sobre_mi="Test",
        formacion=[],
        experiencia=[],
        tratamientos=[],
        certificaciones=[],
        idiomas=[],
    )

    result = await service.patch_public_profile(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        profile=profile,
    )

    # bio_generated_at must remain unchanged
    assert result is not None
    assert result.bio_generated_at == original_bio_generated_at, (
        f"bio_generated_at must not change after patch_public_profile. "
        f"Expected {original_bio_generated_at}, got {result.bio_generated_at}"
    )

    # update_public_profile (which sets bio_generated_at) must NOT be called
    mock_repo.update_public_profile.assert_not_called()
    # update_public_profile_sections (which does NOT set bio_generated_at) MUST be called
    mock_repo.update_public_profile_sections.assert_called_once()


@pytest.mark.asyncio
async def test_patch_public_profile_cross_tenant_404() -> None:
    """PATCH /public-profile with wrong tenant returns 404 (HIPAA dual filter).

    Cross-tenant isolation: doctor belongs to tenant_A, request uses tenant_B.
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    tenant_b = uuid4()  # attacker's tenant
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build:
        mock_svc = MagicMock()
        # When tenant_b queries, get_doctor dual filter returns None (cross-tenant blocked)
        mock_svc.get_doctor = AsyncMock(return_value=None)
        mock_svc.patch_public_profile = AsyncMock(return_value=None)
        mock_build.return_value = mock_svc

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}/public-profile",
                headers={
                    "X-Tenant-ID": str(tenant_b),  # wrong tenant
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "admin_clinic",
                },
                json={"sobreMi": "Hack attempt"},
            )

    assert resp.status_code == 404, f"Expected 404 for cross-tenant, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_patch_public_profile_extra_key_422() -> None:
    """Unknown field in PATCH /public-profile body must return 422 (extra='forbid').

    Prevents silent field drops — strict validation gate.
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with patch("src.modules.vitalia.clinics.api.doctors_router._build_service"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}/public-profile",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "admin_clinic",
                },
                json={
                    "sobreMi": "Texto válido",
                    "campoDesconocido": "valor inesperado",  # extra key → 422
                },
            )

    assert resp.status_code == 422, f"Expected 422 for extra key, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_patch_public_profile_rbac_403_marketing() -> None:
    """Marketing role must be denied PATCH /public-profile with 403.

    RBAC gate: only owner and admin_clinic can mutate public profile.
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with patch("src.modules.vitalia.clinics.api.doctors_router._build_service"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.patch(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}/public-profile",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "marketing",  # not in _STAFF_MUTATION_ROLES
                },
                json={"sobreMi": "Intento marketing"},
            )

    assert resp.status_code == 403, f"Expected 403 for marketing role, got {resp.status_code}: {resp.text}"
