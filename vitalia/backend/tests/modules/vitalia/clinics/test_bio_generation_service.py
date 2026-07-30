# cap: clinics.lisa.doctores
"""Tests for BioGenerationService — TDD RED-first.

V-FN-9: Bio-gen produces 3 sections ONLY from provided material (no-invent guardrail);
        LLM fail -> fallback empty sections + Spanish neutro error message.

03-arch D-4: BioGenerationService is deterministic single-shot extractive service,
             NOT agentic (R23 N/A). Lives in clinics/application/. Sonnet-eligible.

All LLM calls are mocked — no real API calls in unit tests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.vitalia.clinics.application.bio_generation_service import (
    BIO_GENERATION_FALLBACK_MESSAGE,
    BioGenerationService,
)
from src.modules.vitalia.clinics.domain.bio import BioPublic
from src.modules.vitalia.clinics.domain.doctor import Doctor

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_doctor(
    bio_inputs_notes: str | None = None,
    bio_links: list[str] | None = None,
) -> Doctor:
    """Create minimal Doctor with optional bio inputs."""
    return Doctor(
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        first_name="María",
        last_name="González",
        dni="12345678",
        email="maria@clinica.pe",
        phone=None,
        specialty="Odontología cosmética",
        credential="12345",
        credential_country="PE",
        years_experience=10,
        languages=["es", "en"],
        bio_inputs_notes=bio_inputs_notes,
        bio_links=bio_links or [],
        bio_public=None,
        avatar_key=None,
        visible_en_landing=True,
        active=True,
    )


def _make_llm_response(
    resumen: str = "Resumen",
    formacion: str = "Formación",
    enfoque: str = "Enfoque",
) -> str:
    """Return a well-formed JSON LLM response for 3 bio sections."""
    import json

    return json.dumps(
        {
            "resumen": resumen,
            "formacion": formacion,
            "enfoque": enfoque,
        }
    )


# ── Core no-invent guardrail (V-FN-9 first) ──────────────────────────────────


def test_generate_returns_bio_public_from_notes() -> None:
    """Service returns BioPublic with 3 sections when LLM responds correctly.

    V-FN-9: output only references provided material.
    The mock LLM is configured to return content derived from notes.
    """
    doctor = _make_doctor(
        bio_inputs_notes="Especialista en implantes dentales. Graduada UPCH 2008.",
        bio_links=["https://linkedin.com/in/mariagonzalez"],
    )

    mock_llm = MagicMock()
    mock_llm.generate_response.return_value = _make_llm_response(
        resumen="Dra. María González es especialista en implantes dentales.",
        formacion="Graduada de la UPCH en 2008.",
        enfoque="Implantes y rehabilitación oral.",
    )

    svc = BioGenerationService(llm_service=mock_llm)
    result = svc.generate(doctor)

    assert isinstance(result, BioPublic)
    assert result.resumen is not None
    assert result.formacion is not None
    assert result.enfoque is not None
    # LLM was called exactly once (single-shot)
    mock_llm.generate_response.assert_called_once()


def test_generate_sends_material_in_prompt() -> None:
    """The prompt passed to the LLM contains the provided material (notes + links).

    V-FN-9: guardrail — prompt must instruct LLM to use only provided material.
    """
    notes = "Médico con 15 años en estética facial."
    link = "https://example.com/cv"
    doctor = _make_doctor(bio_inputs_notes=notes, bio_links=[link])

    call_args: list[Any] = []

    def capture_call(**kwargs: Any) -> str:
        call_args.append(kwargs)
        return _make_llm_response()

    mock_llm = MagicMock()
    mock_llm.generate_response.side_effect = lambda messages, system_prompt=None, model_type="smart", **kw: (
        _make_llm_response()
    )

    svc = BioGenerationService(llm_service=mock_llm)
    svc.generate(doctor)

    # Check that the call included material
    call = mock_llm.generate_response.call_args
    # The prompt material must contain the doctor's notes and links
    prompt_combined = str(call)
    assert notes in prompt_combined or link in prompt_combined


def test_generate_prompt_includes_no_invent_guardrail() -> None:
    """Prompt must contain no-invent guardrail instruction.

    V-FN-9: 'usa SOLO el material' must appear in system_prompt.
    """
    doctor = _make_doctor(bio_inputs_notes="Notas del doctor.")

    mock_llm = MagicMock()
    mock_llm.generate_response.return_value = _make_llm_response()

    svc = BioGenerationService(llm_service=mock_llm)
    svc.generate(doctor)

    call = mock_llm.generate_response.call_args
    # Extract system_prompt from call kwargs or positional
    system_prompt = call.kwargs.get("system_prompt") or (call.args[1] if len(call.args) > 1 else "")
    # Must instruct not to invent
    assert system_prompt is not None
    sp_lower = system_prompt.lower()
    assert "solo" in sp_lower or "únicamente" in sp_lower or "no inventes" in sp_lower


def test_generate_empty_inputs_returns_placeholder_sections() -> None:
    """Doctor with no bio_inputs_notes and empty bio_links.

    LLM is called, but sections may be empty/placeholders.
    Service must not raise — empty input is valid.
    """
    doctor = _make_doctor(bio_inputs_notes=None, bio_links=[])

    mock_llm = MagicMock()
    # LLM returns empty strings (no material to work with)
    mock_llm.generate_response.return_value = _make_llm_response(resumen="", formacion="", enfoque="")

    svc = BioGenerationService(llm_service=mock_llm)
    result = svc.generate(doctor)

    assert isinstance(result, BioPublic)
    # No crash — graceful handling of empty material
    mock_llm.generate_response.assert_called_once()


# ── Fallback on LLM failure (V-FN-9 second half) ────────────────────────────


def test_fallback_on_llm_exception_returns_empty_bio() -> None:
    """LLM raises exception -> service returns empty BioPublic + no exception raised.

    V-FN-9: fallback empty sections on LLM fail.
    tessl__graceful-degradation: never break autosave of rest of profile.
    """
    doctor = _make_doctor(bio_inputs_notes="Especialista certificada.")

    mock_llm = MagicMock()
    mock_llm.generate_response.side_effect = Exception("LLM timeout")

    svc = BioGenerationService(llm_service=mock_llm)
    result = svc.generate(doctor)

    # Returns empty BioPublic — no exception propagated
    assert isinstance(result, BioPublic)
    assert result.is_empty()


def test_fallback_error_message_is_set() -> None:
    """On LLM failure, service sets error_message attribute on BioPublic fallback.

    The caller (endpoint) uses this to return an error message to the FE.
    """
    doctor = _make_doctor(bio_inputs_notes="Info del doctor.")

    mock_llm = MagicMock()
    mock_llm.generate_response.side_effect = TimeoutError("LLM timeout")

    svc = BioGenerationService(llm_service=mock_llm)
    result, error_message = svc.generate_with_error(doctor)

    assert result.is_empty()
    assert error_message is not None
    assert len(error_message) > 0
    # Message must be Spanish neutro
    assert "bio" in error_message.lower() or "intentar" in error_message.lower() or "generar" in error_message.lower()


def test_fallback_message_no_voseo() -> None:
    """Fallback error message must use Spanish neutro (no voseo).

    spanish-text.md: user-facing strings must not contain voseo.
    """
    msg = BIO_GENERATION_FALLBACK_MESSAGE.lower()
    # voseo-allowed: citations of voseo patterns as test assertions (not user-facing strings)
    assert "tenés" not in msg
    assert "podés" not in msg
    assert "intentá" not in msg


def test_fallback_on_json_parse_error() -> None:
    """LLM returns malformed JSON -> fallback to empty BioPublic without raising.

    Defensive: LLM output might not conform to expected JSON schema.
    """
    doctor = _make_doctor(bio_inputs_notes="Notas.")

    mock_llm = MagicMock()
    mock_llm.generate_response.return_value = "This is not JSON: {broken"

    svc = BioGenerationService(llm_service=mock_llm)
    result = svc.generate(doctor)

    assert isinstance(result, BioPublic)
    # Graceful fallback on malformed response
    assert result.is_empty()


def test_fallback_on_missing_sections_in_response() -> None:
    """LLM returns valid JSON but with missing sections -> partial BioPublic.

    Service must handle partial output gracefully.
    """
    import json

    doctor = _make_doctor(bio_inputs_notes="Especialista.")

    mock_llm = MagicMock()
    # Only resumen present, others missing
    mock_llm.generate_response.return_value = json.dumps({"resumen": "Solo el resumen está presente."})

    svc = BioGenerationService(llm_service=mock_llm)
    result = svc.generate(doctor)

    assert isinstance(result, BioPublic)
    assert result.resumen == "Solo el resumen está presente."
    assert result.formacion is None
    assert result.enfoque is None


# ── Endpoint integration (generate-bio route) ────────────────────────────────


@pytest.mark.asyncio
async def test_generate_bio_endpoint_route_exists() -> None:
    """POST /{id}/generate-bio route is registered with response_model=GenerateBioResponse.

    Verifies the route is declared in the router (arch gate compliance).
    """
    from src.modules.vitalia.clinics.api.doctors_router import router

    route_paths = [route.path for route in router.routes]
    assert any("generate-bio" in path for path in route_paths), (
        "Route POST /{doctor_id}/generate-bio must be registered in doctors_router"
    )


@pytest.mark.asyncio
async def test_generate_bio_endpoint_returns_200_on_success() -> None:
    """Endpoint returns 200 with valid GenerateBioResponse structure.

    response_model=GenerateBioResponse must be declared on the route.
    Tests the endpoint directly with AsyncClient + dependency override.
    """
    from unittest.mock import AsyncMock

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import (
        _get_db,
        router,
    )

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    fake_doctor_id = uuid4()
    tenant_id = uuid4()
    clinic_id = uuid4()
    user_id = uuid4()

    fake_doctor = _make_doctor(bio_inputs_notes="Especialista con 10 años de experiencia.")
    fake_bio = BioPublic(
        resumen="Médica especialista.",
        formacion="Graduada UPCH.",
        enfoque="Medicina estética.",
    )

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    # Patch the service and bio gen service at the module level
    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router.BioGenerationService") as MockBioSvc,
    ):
        mock_svc = MagicMock()
        mock_svc.get_doctor = AsyncMock(return_value=fake_doctor)
        mock_svc.update_doctor = AsyncMock(return_value=fake_doctor)
        mock_build.return_value = mock_svc

        mock_bio_instance = MagicMock()
        mock_bio_instance.generate_with_error.return_value = (fake_bio, None)
        MockBioSvc.return_value = mock_bio_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/vitalia/clinics/doctors/{fake_doctor_id}/generate-bio",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "admin_clinic",
                },
                json={},
            )

        # 200 with bio sections in response
        assert resp.status_code == 200
        body = resp.json()
        assert "bio" in body
        assert body["bio"]["resumen"] == "Médica especialista."


@pytest.mark.asyncio
async def test_generate_bio_endpoint_fallback_on_llm_error() -> None:
    """Endpoint returns 200 with empty bio + error_message when LLM fails.

    V-FN-9: fallback must not break — returns 200 with empty sections and message.
    """
    from unittest.mock import AsyncMock

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    fake_doctor_id = uuid4()
    tenant_id = uuid4()
    clinic_id = uuid4()
    user_id = uuid4()

    fake_doctor = _make_doctor(bio_inputs_notes="Notas.")
    empty_bio = BioPublic()

    async def _fake_db():  # noqa: ANN202
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        yield mock_session

    app.dependency_overrides[_get_db] = _fake_db

    with (
        patch("src.modules.vitalia.clinics.api.doctors_router._build_service") as mock_build,
        patch("src.modules.vitalia.clinics.api.doctors_router.BioGenerationService") as MockBioSvc,
    ):
        mock_svc = MagicMock()
        mock_svc.get_doctor = AsyncMock(return_value=fake_doctor)
        mock_build.return_value = mock_svc

        mock_bio_instance = MagicMock()
        mock_bio_instance.generate_with_error.return_value = (
            empty_bio,
            BIO_GENERATION_FALLBACK_MESSAGE,
        )
        MockBioSvc.return_value = mock_bio_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/vitalia/clinics/doctors/{fake_doctor_id}/generate-bio",
                headers={
                    "X-Tenant-ID": str(tenant_id),
                    "X-Clinic-ID": str(clinic_id),
                    "X-User-ID": str(user_id),
                    "X-User-Role": "admin_clinic",
                },
                json={},
            )

        # Must return 200 (not 500) — fallback doesn't break the endpoint
        assert resp.status_code == 200
        body = resp.json()
        assert "bio" in body
        assert "error_message" in body
        assert body["error_message"] == BIO_GENERATION_FALLBACK_MESSAGE
        # Bio sections are empty
        assert body["bio"]["resumen"] is None
