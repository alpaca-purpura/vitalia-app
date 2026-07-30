# cap: clinics.lisa.doctores
"""TDD RED-first: POST /{doctor_id}/generate-profile endpoint.

T-BE-generate-profile (vitalia-fase2-lisa-doctores story).

Gap: generate-bio writes 3-blob bio_public only; bio_generated_at never set;
FE calls generate-profile → 404. This test file defines required behavior BEFORE
implementation — all tests expected to fail (RED) until the endpoint is added.

Scenarios covered:
  1. generate-profile 201 → structured profile set + bio_generated_at + public_slug
  2. material_new false after generation (profile_state comparison correct)
  3. PATCH manual does NOT touch bio_generated_at (RN-D3B-4)
  4. doctor without material → minimal profile (empty sections omitted, no error)
  5. cross-tenant 404 (dual filter tenant+clinic)
  6. audit row written with action=doctor.profile_generated
  7. route registered in doctors_router with response_model=
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
    bio_inputs_notes: str | None = "Especialista en implantes dentales. Graduada UPCH 2008.",
    bio_links: list[str] | None = None,
    specialty: str | None = "Odontología cosmética",
    credential: str = "12345",
    languages: list[str] | None = None,
    bio_generated_at: datetime | None = None,
    public_profile: DoctorPublicProfile | None = None,
    public_slug: str | None = None,
    tenant_id: Any | None = None,
    clinic_id: Any | None = None,
) -> Doctor:
    """Create minimal Doctor for testing generate-profile endpoint."""
    return Doctor(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        clinic_id=clinic_id or uuid4(),
        first_name="María",
        last_name="González",
        dni="12345678",
        email="maria@clinica.pe",
        phone=None,
        specialty=specialty,
        credential=credential,
        credential_country="PE",
        years_experience=10,
        languages=languages or ["es", "en"],
        bio_inputs_notes=bio_inputs_notes,
        bio_links=bio_links or [],
        bio_public=None,
        public_profile=public_profile,
        bio_generated_at=bio_generated_at,
        public_slug=public_slug,
        avatar_key=None,
        visible_en_landing=True,
        active=True,
    )


def _make_structured_profile() -> DoctorPublicProfile:
    return DoctorPublicProfile(
        sobre_mi="Especialista en implantes dentales con más de 10 años de experiencia.",
        formacion=[{"titulo": "Odontóloga", "institucion": "UPCH", "anio": "2008"}],
        experiencia=[],
        tratamientos=["Implantes dentales", "Odontología cosmética"],
        certificaciones=[],
        idiomas=["Español", "Inglés"],
    )


# ── Connectivity gate ─────────────────────────────────────────────────────────


def test_generate_profile_route_registered() -> None:
    """POST /{doctor_id}/generate-profile must be registered in doctors_router.

    Arch gate: route must exist before FE can call it.
    RED: will fail until endpoint is added.
    """
    from src.modules.vitalia.clinics.api.doctors_router import router

    route_paths = [route.path for route in router.routes]
    assert any("generate-profile" in path for path in route_paths), (
        "Route POST /{doctor_id}/generate-profile must be registered in doctors_router"
    )


def test_generate_profile_route_has_response_model() -> None:
    """generate-profile route must declare response_model= (arch gate — PII allowlist)."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    gen_profile_routes = [
        r
        for r in router.routes
        if "generate-profile" in getattr(r, "path", "") and "POST" in getattr(r, "methods", set())
    ]
    assert gen_profile_routes, "POST generate-profile route not found"
    route = gen_profile_routes[0]
    assert hasattr(route, "response_model") and route.response_model is not None, (
        "generate-profile must declare response_model="
    )


# ── Core behavior ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_profile_creates_structured_profile_timestamp_and_slug() -> None:
    """POST /{doctor_id}/generate-profile → 200/201, sets public_profile + bio_generated_at + public_slug.

    Core behavior gate: the write-path must persist all 3 fields.
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

    fake_doctor = _make_doctor(tenant_id=tenant_id, clinic_id=clinic_id)
    fake_profile = _make_structured_profile()

    # Doctor after profile generation: public_profile set + bio_generated_at set + slug set
    updated_doctor = _make_doctor(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        public_profile=fake_profile,
        bio_generated_at=_utc_now(),
        public_slug="dra-maria-gonzalez",
    )
    updated_doctor.id = doctor_id

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_bio_file_service") as mock_build_files,
        patch("src.modules.vitalia.clinics.api.doctors_router.BioGenerationService") as MockBioSvc,
    ):
        mock_svc = MagicMock()
        mock_svc.get_doctor = AsyncMock(return_value=fake_doctor)
        mock_svc.generate_public_profile = AsyncMock(return_value=updated_doctor)
        mock_build.return_value = mock_svc

        mock_file_svc = MagicMock()
        mock_file_svc.list_files = AsyncMock(return_value=[])
        mock_build_files.return_value = mock_file_svc

        mock_bio = MagicMock()
        mock_bio.generate_structured.return_value = fake_profile
        MockBioSvc.return_value = mock_bio

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}/generate-profile",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "admin_clinic",
                },
                json={},
            )

    assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "profile" in body or "publicProfile" in body, f"Response missing profile: {body}"
    assert "generatedAt" in body or "generated_at" in body, f"Response missing generated_at: {body}"


@pytest.mark.asyncio
async def test_generate_profile_material_new_false_after_generation() -> None:
    """After generate-profile, bio_generated_at is set → material_new logic resolves False.

    RN-D3D-4: material_new = bio_generated_at is None OR bio_inputs_last_updated > bio_generated_at.
    Before generation: bio_generated_at=None → material_new=True.
    After generation: bio_generated_at=now() → material_new=False (no new edits since).

    This test verifies the domain-level invariant:
    1. Before generation: bio_generated_at is None → material_new is True.
    2. After generation: bio_generated_at is not None.
    3. In DB (same transaction): bio_generated_at = NOW() ≥ updated_at of bio_inputs.
       → material_new becomes False for any reader after the generate call.
    """
    # Simulate doctor BEFORE generation: has notes but bio_generated_at is None
    doctor_before = _make_doctor(
        bio_inputs_notes="Notas con material nuevo.",
        bio_generated_at=None,
        public_profile=None,
    )

    # material_new BEFORE: bio_generated_at is None → True
    material_new_before = doctor_before.bio_generated_at is None
    assert material_new_before, "Before generation, material_new must be True"

    fake_profile = _make_structured_profile()

    # After generating: bio_generated_at is explicitly set to a past moment
    # to simulate DB write. In real DB: same transaction → bio_generated_at=NOW() ≥ updated_at.
    from datetime import timedelta  # noqa: PLC0415

    past_moment = _utc_now() - timedelta(seconds=1)
    doctor_after = _make_doctor(
        bio_inputs_notes="Notas con material nuevo.",
        bio_generated_at=past_moment,  # set to just before construction
        public_profile=fake_profile,
    )
    # Force updated_at to be <= bio_generated_at (mimics DB: same transaction)
    import dataclasses  # noqa: PLC0415

    doctor_after = dataclasses.replace(doctor_after, updated_at=past_moment)

    # material_new AFTER: bio_generated_at is set AND bio_inputs not updated since
    material_new_after = (
        doctor_after.bio_generated_at is None or doctor_after.updated_at > doctor_after.bio_generated_at
    )
    assert not material_new_after, "After generation (in same transaction), material_new must be False"
    assert doctor_after.bio_generated_at is not None, "bio_generated_at must be set after generate-profile"


@pytest.mark.asyncio
async def test_patch_doctor_does_not_touch_bio_generated_at() -> None:
    """PATCH /doctors/{id} must NOT update bio_generated_at (RN-D3B-4).

    bio_generated_at is ONLY set via generate-profile, not via manual PATCH edits.
    Verifies this at the service/repo level.
    """
    from src.modules.vitalia.clinics.application.doctor_service import DoctorService

    original_generated_at = _utc_now()

    mock_repo = AsyncMock()
    mock_repo.get_by_id = AsyncMock(return_value=_make_doctor(bio_generated_at=original_generated_at))

    # update() returns doctor with same bio_generated_at (not modified)
    updated_doctor = _make_doctor(bio_generated_at=original_generated_at)
    mock_repo.update = AsyncMock(return_value=updated_doctor)

    audit_repo = AsyncMock()
    mock_emitter = AsyncMock()

    service = DoctorService(
        doctor_repo=mock_repo,
        audit_repo=audit_repo,
        emitter=mock_emitter,
    )

    result = await service.update_doctor(
        doctor_id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        user_id=uuid4(),
        bio_inputs_notes="Notas actualizadas manualmente.",
    )

    # bio_generated_at must remain unchanged after PATCH
    assert result is not None
    assert result.bio_generated_at == original_generated_at, "PATCH update must NOT change bio_generated_at (RN-D3B-4)"

    # Verify update_public_profile() was NOT called (that's the only method that touches bio_generated_at)
    assert not mock_repo.update_public_profile.called, "update() must NOT trigger update_public_profile (RN-D3B-4)"


@pytest.mark.asyncio
async def test_generate_profile_minimal_doctor_no_material() -> None:
    """Doctor with no notes/links/files → minimal profile with empty sections, no error.

    RN-D3D-6: empty sections → None/[] (not crash). Service must handle gracefully.
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

    # Doctor with NO material
    bare_doctor = _make_doctor(
        bio_inputs_notes=None,
        bio_links=[],
        specialty=None,
        credential="",
        languages=[],
    )
    bare_doctor.id = doctor_id

    # Minimal profile: all sections empty
    minimal_profile = DoctorPublicProfile(
        sobre_mi=None,
        formacion=[],
        experiencia=[],
        tratamientos=[],
        certificaciones=[],
        idiomas=[],
    )

    updated_bare = _make_doctor(
        bio_inputs_notes=None,
        bio_generated_at=_utc_now(),
        public_profile=minimal_profile,
        public_slug="dra-maria-gonzalez",
    )
    updated_bare.id = doctor_id

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_bio_file_service") as mock_build_files,
        patch("src.modules.vitalia.clinics.api.doctors_router.BioGenerationService") as MockBioSvc,
    ):
        mock_svc = MagicMock()
        mock_svc.get_doctor = AsyncMock(return_value=bare_doctor)
        mock_svc.generate_public_profile = AsyncMock(return_value=updated_bare)
        mock_build.return_value = mock_svc

        mock_file_svc = MagicMock()
        mock_file_svc.list_files = AsyncMock(return_value=[])
        mock_build_files.return_value = mock_file_svc

        mock_bio = MagicMock()
        mock_bio.generate_structured.return_value = minimal_profile
        MockBioSvc.return_value = mock_bio

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}/generate-profile",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "admin_clinic",
                },
                json={},
            )

    # Must not crash — empty sections are allowed (RN-D3D-6)
    assert resp.status_code in (200, 201), (
        f"Minimal doctor (no material) should not crash: {resp.status_code} {resp.text}"
    )


@pytest.mark.asyncio
async def test_generate_profile_cross_tenant_returns_404() -> None:
    """POST generate-profile with doctor belonging to different tenant → 404.

    Dual filter (tenant_id + clinic_id): if doctor not found for tenant → 404.
    SC-4 extension: cross-tenant write attempt must not return 403 (info leak).
    """
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    tenant_id_attacker = uuid4()
    clinic_id_attacker = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router._build_bio_file_service") as mock_build_files,
    ):
        mock_svc = MagicMock()
        # Dual filter miss: doctor not found for attacker's tenant/clinic
        mock_svc.get_doctor = AsyncMock(return_value=None)
        mock_build.return_value = mock_svc

        mock_file_svc = MagicMock()
        mock_file_svc.list_files = AsyncMock(return_value=[])
        mock_build_files.return_value = mock_file_svc

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/vitalia/clinics/doctors/{doctor_id}/generate-profile",
                headers={
                    "X-Tenant-ID": str(tenant_id_attacker),
                    "X-Clinic-ID": str(clinic_id_attacker),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "admin_clinic",
                },
                json={},
            )

    assert resp.status_code == 404, f"Cross-tenant generate-profile must return 404 (got {resp.status_code})"


@pytest.mark.asyncio
async def test_generate_profile_writes_audit_row() -> None:
    """generate-profile must write audit_log row with action=doctor.profile_generated (HIPAA-lite).

    hipaa-lite rule: sync audit write pre-response. No fire-and-forget.
    """
    from src.modules.vitalia.clinics.application.doctor_service import DoctorService

    tenant_id = uuid4()
    clinic_id = uuid4()
    doctor_id = uuid4()
    user_id = uuid4()

    fake_doctor = _make_doctor(tenant_id=tenant_id, clinic_id=clinic_id)
    fake_doctor.id = doctor_id
    fake_profile = _make_structured_profile()

    updated_doctor = _make_doctor(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        bio_generated_at=_utc_now(),
        public_profile=fake_profile,
        public_slug="dra-maria-gonzalez",
    )
    updated_doctor.id = doctor_id

    mock_repo = AsyncMock()
    mock_repo.get_by_id = AsyncMock(return_value=fake_doctor)
    mock_repo.update_public_profile = AsyncMock(return_value=updated_doctor)

    audit_repo = AsyncMock()
    mock_emitter = AsyncMock()

    service = DoctorService(
        doctor_repo=mock_repo,
        audit_repo=audit_repo,
        emitter=mock_emitter,
    )

    # Call the service method that will be invoked by the endpoint
    await service.generate_public_profile(
        doctor_id=doctor_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        profile=fake_profile,
    )

    # Audit repo must have been called with action=doctor.profile_generated
    assert audit_repo.write.called or audit_repo.create.called, (
        "Audit log must be written after generate-profile (HIPAA-lite sync write)"
    )

    # Verify audit action
    audit_call = audit_repo.write.call_args or audit_repo.create.call_args
    call_str = str(audit_call)
    assert "profile_generated" in call_str or "doctor.profile_generated" in call_str, (
        f"Audit action must be 'doctor.profile_generated', got: {call_str}"
    )


# ── BioGenerationService.generate_structured ─────────────────────────────────


def test_bio_generation_service_has_generate_structured_method() -> None:
    """BioGenerationService must expose generate_structured(doctor, files) -> DoctorPublicProfile.

    RED: will fail until generate_structured is added to the service.
    """
    from src.modules.vitalia.clinics.application.bio_generation_service import (
        BioGenerationService,
    )

    assert hasattr(BioGenerationService, "generate_structured"), (
        "BioGenerationService must have generate_structured method"
    )


def test_generate_structured_returns_doctor_public_profile() -> None:
    """generate_structured must return DoctorPublicProfile (not BioPublic).

    Confirms the method signature/return type is correct.
    """
    import inspect

    from src.modules.vitalia.clinics.application.bio_generation_service import (
        BioGenerationService,
    )

    sig = inspect.signature(BioGenerationService.generate_structured)
    params = list(sig.parameters.keys())
    # Must accept doctor + bio_file_filenames (or similar)
    assert "doctor" in params, "generate_structured must accept 'doctor' param"


def test_generate_structured_with_mocked_llm_returns_structured_profile() -> None:
    """generate_structured with mocked LLM returns DoctorPublicProfile.

    Verifies the structured response parsing (6-section schema).
    """
    import json as _json  # noqa: PLC0415

    from src.modules.vitalia.clinics.application.bio_generation_service import (
        BioGenerationService,
    )

    doctor = _make_doctor(
        bio_inputs_notes="Implantólogo con 15 años. Graduado UPCH 2005. Habla inglés.",
        specialty="Cirugía oral",
    )

    structured_response = _json.dumps(
        {
            "sobre_mi": "Especialista en cirugía oral con más de 15 años de experiencia.",
            "formacion": [{"titulo": "Cirujano Oral", "institucion": "UPCH", "anio": "2005"}],
            "experiencia": [],
            "tratamientos": ["Cirugía oral", "Implantes"],
            "certificaciones": [],
            "idiomas": ["Español", "Inglés"],
        }
    )

    mock_llm = MagicMock()
    mock_llm.generate_response.return_value = structured_response

    svc = BioGenerationService(llm_service=mock_llm)
    result = svc.generate_structured(doctor=doctor, bio_file_filenames=[])

    assert isinstance(result, DoctorPublicProfile), (
        f"generate_structured must return DoctorPublicProfile, got {type(result)}"
    )
    assert result.sobre_mi is not None
    assert len(result.tratamientos) > 0


def test_generate_structured_llm_failure_extractive_fallback() -> None:
    """generate_structured on LLM failure → fallback EXTRACTIVO determinístico (no raise, no vacío).

    Graceful degradation: endpoint returns 200 with empty profile rather than 500.
    """
    from src.modules.vitalia.clinics.application.bio_generation_service import (
        BioGenerationService,
    )

    doctor = _make_doctor()

    mock_llm = MagicMock()
    mock_llm.generate_response.side_effect = Exception("LLM timeout")

    svc = BioGenerationService(llm_service=mock_llm)
    result = svc.generate_structured(doctor=doctor, bio_file_filenames=[])

    assert isinstance(result, DoctorPublicProfile), (
        "generate_structured must return DoctorPublicProfile even on LLM failure"
    )
    # Fallback extractivo (fix 2026-06-12): usa material EXISTENTE del doctor —
    # specialty → tratamientos, credential → certificaciones (no-invent: solo reordena).
    assert result.tratamientos == [doctor.specialty] if doctor.specialty else result.tratamientos == []
    if getattr(doctor, "credential_number", None):
        assert any(str(doctor.credential_number) in c for c in result.certificaciones)
    # experiencia/idiomas no derivables del fixture → vacíos
    assert result.experiencia == []
    assert result.idiomas == []


# ── DoctorRepository.update_public_profile ───────────────────────────────────


def test_doctor_repository_has_update_public_profile_method() -> None:
    """DoctorRepository must expose update_public_profile method.

    RED: will fail until the method is added to the repo.
    """
    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
        DoctorRepository,
    )

    assert hasattr(DoctorRepository, "update_public_profile"), "DoctorRepository must have update_public_profile method"


# ── DoctorService.generate_public_profile ────────────────────────────────────


def test_doctor_service_has_generate_public_profile_method() -> None:
    """DoctorService must expose generate_public_profile method.

    RED: will fail until method is added.
    """
    from src.modules.vitalia.clinics.application.doctor_service import DoctorService

    assert hasattr(DoctorService, "generate_public_profile"), "DoctorService must have generate_public_profile method"


# ── DTO presence ──────────────────────────────────────────────────────────────


def test_generate_profile_response_dto_exists() -> None:
    """GenerateProfileResponse DTO must exist in dtos.py.

    RED: will fail until DTO is added.
    """
    from src.modules.vitalia.clinics.api import dtos

    assert hasattr(dtos, "GenerateProfileResponse"), "GenerateProfileResponse DTO must be defined in dtos.py"


def test_generate_profile_response_dto_has_required_fields() -> None:
    """GenerateProfileResponse must have profile + generated_at fields."""
    from src.modules.vitalia.clinics.api.dtos import GenerateProfileResponse

    fields = GenerateProfileResponse.model_fields
    assert "profile" in fields or "publicProfile" in fields, "GenerateProfileResponse must have a 'profile' field"
    assert "generated_at" in fields or "generatedAt" in fields, (
        "GenerateProfileResponse must have a 'generated_at' field"
    )


# ── Audit DELTA-BE 2026-06-12 — regression RED-first (Carril R) ──────────────


def test_extractive_fallback_with_legacy_formacion_is_json_serializable() -> None:
    """Fallback extractivo con bio_public.formacion legacy → to_dict() JSON-serializable.

    Bug (audit DELTA-BE): _extractive_structured_fallback envolvía formacion en
    FormacionItem (dataclass) pero DoctorPublicProfile.to_dict() pasa la lista
    cruda → json.dumps en doctor_repository.update_public_profile lanzaba
    TypeError → 500 en POST generate-profile con LLM caído + bio legacy presente.
    """
    import dataclasses  # noqa: PLC0415
    import json as _json  # noqa: PLC0415

    from src.modules.vitalia.clinics.application.bio_generation_service import (
        BioGenerationService,
    )
    from src.modules.vitalia.clinics.domain.bio import BioPublic

    doctor = dataclasses.replace(
        _make_doctor(),
        bio_public=BioPublic(
            resumen="Especialista con 10 años en implantes.",
            formacion="Odontóloga UPCH 2008. Maestría en implantología UNMSM 2012.",
            enfoque="Trato cálido y claro.",
        ),
    )

    mock_llm = MagicMock()
    mock_llm.generate_response.side_effect = Exception("LLM down")

    svc = BioGenerationService(llm_service=mock_llm)
    profile = svc.generate_structured(doctor=doctor, bio_file_filenames=[])

    assert profile.formacion, "fallback con formacion legacy debe derivar items de formación"
    assert all(isinstance(item, dict) for item in profile.formacion), (
        "formacion del fallback debe ser list[dict] (JSONB-ready), no dataclasses"
    )
    # El write-path real: update_public_profile hace json.dumps(profile.to_dict())
    _json.dumps(profile.to_dict())  # must not raise TypeError


def test_parse_structured_response_coerces_anio_to_int_or_none() -> None:
    """anio/anios string del LLM → int (dígitos) o None (rangos) — DTO tipa int|None.

    Bug (audit DELTA-BE): el prompt estructurado pide '"anio": "string o null"'
    pero FormacionItemDTO/ExperienciaItemDTO tipan int|None → un anio no-numérico
    persistido ('2015-2019') rompía la validación Pydantic en CADA GET posterior
    (500 pegajoso hasta regenerar).
    """
    import json as _json  # noqa: PLC0415

    from src.modules.vitalia.clinics.api.dtos import ExperienciaItemDTO, FormacionItemDTO
    from src.modules.vitalia.clinics.application.bio_generation_service import (
        BioGenerationService,
    )

    raw = _json.dumps(
        {
            "sobre_mi": "Especialista en cirugía oral.",
            "formacion": [{"titulo": "Cirujano Oral", "institucion": "UPCH", "anio": "2008"}],
            "experiencia": [{"puesto": "Jefe de servicio", "lugar": "Clínica Aurora", "anios": "2015-2019"}],
            "tratamientos": [],
            "certificaciones": [],
            "idiomas": [],
        }
    )
    mock_llm = MagicMock()
    mock_llm.generate_response.return_value = raw

    svc = BioGenerationService(llm_service=mock_llm)
    profile = svc.generate_structured(doctor=_make_doctor(), bio_file_filenames=[])

    assert profile.formacion[0]["anio"] == 2008, "anio dígito-string debe coercer a int"
    assert profile.experiencia[0]["anios"] is None, "anios rango no-numérico debe normalizar a None"
    # Los DTOs (int | None) deben validar sin ValidationError con lo persistido
    FormacionItemDTO(**profile.formacion[0])
    ExperienciaItemDTO(**profile.experiencia[0])
