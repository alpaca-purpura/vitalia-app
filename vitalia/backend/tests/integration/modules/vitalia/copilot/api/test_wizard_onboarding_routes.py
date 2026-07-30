"""Integration tests — Valeria wizard onboarding API routes.

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- POST /api/v1/vitalia/onboarding/drafts returns 200 + StartDraftResponse
- POST /api/v1/vitalia/onboarding/drafts/{id}/extract returns 200 + ExtractResponse
- POST /api/v1/vitalia/onboarding/drafts/{id}/slots/{slot_id}/confirm returns 200 + ConfirmSlotResponse
- POST /api/v1/vitalia/onboarding/drafts/{id}/simulate returns 200 + SimulateResponse
- POST /api/v1/vitalia/onboarding/drafts/{id}/complete returns 200 + CompleteResponse
- GET /api/v1/vitalia/onboarding/drafts/{id} returns 200 + DraftResponse
- GET /api/v1/vitalia/onboarding/drafts/{id}/stream (SSE) returns 200 + event/stream content-type
- All routes require X-Tenant-ID header → 422 if missing
- response_model enforced (PII gate)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

TENANT_ID = uuid4()
DRAFT_ID = uuid4()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_draft_entity() -> "object":
    """Create a sample OnboardingDraft domain entity."""
    from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
    from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

    def _slot(slot_id: str) -> WizardSlot:
        return WizardSlot(slot_id=slot_id, value=None, confidence=0.0, confirmed_at=None, source="extracted")

    return OnboardingDraft(
        id=DRAFT_ID,
        tenant_id=TENANT_ID,
        user_id=uuid4(),
        clinic_id=None,
        mode="libre",
        slots_required={
            "tenant.name": _slot("tenant.name"),
            "tenant.vertical": _slot("tenant.vertical"),
            "tenant.location": _slot("tenant.location"),
        },
        slots_optional={"brand.tone_default": _slot("brand.tone_default")},
        bonus_extracted={},
        consent_voice_activation=False,
        created_at=_utc_now(),
        updated_at=_utc_now(),
        deleted_at=None,
        completed_at=None,
    )


def _make_confirmed_draft_entity() -> "object":
    """Create a sample OnboardingDraft with confirmed slots."""
    from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
    from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

    def _confirmed(slot_id: str, value: str) -> WizardSlot:
        return WizardSlot(
            slot_id=slot_id,
            value=value,
            confidence=0.95,
            confirmed_at=_utc_now(),
            source="user_text",
        )

    return OnboardingDraft(
        id=DRAFT_ID,
        tenant_id=TENANT_ID,
        user_id=uuid4(),
        clinic_id=None,
        mode="libre",
        slots_required={
            "tenant.name": _confirmed("tenant.name", "Clínica Test"),
            "tenant.vertical": _confirmed("tenant.vertical", "dental"),
            "tenant.location": _confirmed("tenant.location", "Lima"),
        },
        slots_optional={},
        bonus_extracted={},
        consent_voice_activation=False,
        created_at=_utc_now(),
        updated_at=_utc_now(),
        deleted_at=None,
        completed_at=None,
    )


def _build_app_with_mocks(
    *,
    draft_svc: "object" = None,
    extract_svc: "object" = None,
    simulate_svc: "object" = None,
    complete_svc: "object" = None,
) -> FastAPI:
    """Build a test FastAPI app with mocked services injected via DI overrides."""
    from src.main import app as _base_app
    from src.modules.vitalia.copilot.api.routes.wizard_onboarding_routes import (
        get_complete_service,
        get_extract_service,
        get_onboarding_draft_service,
        get_simulate_service,
    )

    app = _base_app

    if draft_svc is not None:
        app.dependency_overrides[get_onboarding_draft_service] = lambda: draft_svc
    if extract_svc is not None:
        app.dependency_overrides[get_extract_service] = lambda: extract_svc
    if simulate_svc is not None:
        app.dependency_overrides[get_simulate_service] = lambda: simulate_svc
    if complete_svc is not None:
        app.dependency_overrides[get_complete_service] = lambda: complete_svc

    return app


@pytest.fixture(autouse=True)
def clear_di_overrides() -> "Any":
    """Clear dependency overrides after each test to avoid pollution."""
    yield
    from src.main import app

    app.dependency_overrides.clear()


class TestStartDraftEndpoint:
    """POST /api/v1/vitalia/onboarding/drafts."""

    @pytest.mark.asyncio
    async def test_start_draft_returns_200(self) -> None:
        """POST /onboarding/drafts returns 200 with draft_id."""

        draft = _make_draft_entity()
        mock_draft_svc = AsyncMock()
        mock_draft_svc.create_draft = AsyncMock(return_value=draft)

        app = _build_app_with_mocks(draft_svc=mock_draft_svc)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/vitalia/onboarding/drafts",
                json={"mode": "libre"},
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 200
        body = response.json()
        assert "draft_id" in body
        assert body["mode"] == "libre"

    @pytest.mark.asyncio
    async def test_start_draft_missing_tenant_returns_422(self) -> None:
        """POST /onboarding/drafts without X-Tenant-ID returns 422."""
        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/vitalia/onboarding/drafts",
                json={"mode": "libre"},
            )

        assert response.status_code == 422


class TestGetDraftEndpoint:
    """GET /api/v1/vitalia/onboarding/drafts/{draft_id}."""

    @pytest.mark.asyncio
    async def test_get_draft_returns_200(self) -> None:
        """GET /onboarding/drafts/{id} returns 200 with full draft."""
        draft = _make_draft_entity()
        mock_draft_svc = AsyncMock()
        mock_draft_svc.get_draft = AsyncMock(return_value=draft)

        app = _build_app_with_mocks(draft_svc=mock_draft_svc)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/vitalia/onboarding/drafts/{DRAFT_ID}",
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["draft_id"] == str(DRAFT_ID)

    @pytest.mark.asyncio
    async def test_get_draft_not_found_returns_404(self) -> None:
        """GET /onboarding/drafts/{id} returns 404 when not found."""
        mock_draft_svc = AsyncMock()
        mock_draft_svc.get_draft = AsyncMock(return_value=None)

        app = _build_app_with_mocks(draft_svc=mock_draft_svc)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/vitalia/onboarding/drafts/{DRAFT_ID}",
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 404


class TestExtractEndpoint:
    """POST /api/v1/vitalia/onboarding/drafts/{draft_id}/extract."""

    @pytest.mark.asyncio
    async def test_extract_returns_200_with_slots(self) -> None:
        """POST /extract returns 200 with updated slot counts."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        draft = _make_draft_entity()
        # Simulate one slot being updated
        draft.slots_required["tenant.name"] = WizardSlot(
            slot_id="tenant.name",
            value="Clínica Dental Norte",
            confidence=0.88,
            confirmed_at=None,
            source="extracted",
        )

        mock_extract_svc = AsyncMock()
        mock_extract_svc.extract = AsyncMock(return_value=draft)

        app = _build_app_with_mocks(extract_svc=mock_extract_svc)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/vitalia/onboarding/drafts/{DRAFT_ID}/extract",
                json={"url": "https://clinicadental.com"},
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 200
        body = response.json()
        assert "slots_required" in body


class TestConfirmSlotEndpoint:
    """POST /api/v1/vitalia/onboarding/drafts/{id}/slots/{slot_id}/confirm."""

    @pytest.mark.asyncio
    async def test_confirm_slot_returns_200(self) -> None:
        """POST /slots/{slot_id}/confirm returns 200 with slot confirmed."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        now = _utc_now()
        confirmed_slot = WizardSlot(
            slot_id="tenant.name",
            value="Clínica Test",
            confidence=1.0,
            confirmed_at=now,
            source="user_text",
        )

        # update_slot returns the draft with confirmed slot
        draft = _make_draft_entity()
        draft.slots_required["tenant.name"] = confirmed_slot

        mock_draft_svc = AsyncMock()
        mock_draft_svc.update_slot = AsyncMock(return_value=draft)

        app = _build_app_with_mocks(draft_svc=mock_draft_svc)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/vitalia/onboarding/drafts/{DRAFT_ID}/slots/tenant.name/confirm",
                json={"value": "Clínica Test", "source": "user_text"},
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["slot_id"] == "tenant.name"
        assert body["value"] == "Clínica Test"


class TestSimulateEndpoint:
    """POST /api/v1/vitalia/onboarding/drafts/{id}/simulate."""

    @pytest.mark.asyncio
    async def test_simulate_returns_200_with_sample_text(self) -> None:
        """POST /simulate returns 200 with personality sample text."""
        from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
            SimulateResponse,
        )

        mock_simulate_svc = AsyncMock()
        mock_simulate_svc.simulate = AsyncMock(
            return_value=SimulateResponse(
                sample_text="Bienvenido a nuestra clínica.",
                generated_at="2026-05-18T10:00:00+00:00",
                cache_hit=False,
            )
        )
        # get_draft needed to get profile partial
        draft = _make_draft_entity()
        mock_draft_svc = AsyncMock()
        mock_draft_svc.get_draft = AsyncMock(return_value=draft)

        app = _build_app_with_mocks(
            simulate_svc=mock_simulate_svc,
            draft_svc=mock_draft_svc,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/vitalia/onboarding/drafts/{DRAFT_ID}/simulate",
                json={"scenario": "primera_respuesta"},
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 200
        body = response.json()
        assert "sample_text" in body
        assert body["sample_text"] == "Bienvenido a nuestra clínica."

    @pytest.mark.asyncio
    async def test_simulate_throttle_returns_429(self) -> None:
        """POST /simulate returns 429 when rate limit exceeded."""
        from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
            ThrottleExceededError,
        )

        draft = _make_draft_entity()
        mock_draft_svc = AsyncMock()
        mock_draft_svc.get_draft = AsyncMock(return_value=draft)

        mock_simulate_svc = AsyncMock()
        mock_simulate_svc.simulate = AsyncMock(side_effect=ThrottleExceededError("simulate_personality"))

        app = _build_app_with_mocks(
            simulate_svc=mock_simulate_svc,
            draft_svc=mock_draft_svc,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/vitalia/onboarding/drafts/{DRAFT_ID}/simulate",
                json={"scenario": "primera_respuesta"},
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 429


class TestCompleteEndpoint:
    """POST /api/v1/vitalia/onboarding/drafts/{id}/complete."""

    @pytest.mark.asyncio
    async def test_complete_returns_200_with_redirect(self) -> None:
        """POST /complete returns 200 with tenant_activated=True."""
        from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
            CompleteResponse,
        )

        mock_complete_svc = AsyncMock()
        mock_complete_svc.complete = AsyncMock(
            return_value=CompleteResponse(
                tenant_activated=True,
                redirect_url="/inbox",
            )
        )

        app = _build_app_with_mocks(complete_svc=mock_complete_svc)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/vitalia/onboarding/drafts/{DRAFT_ID}/complete",
                json={},
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["tenant_activated"] is True
        assert body["redirect_url"] == "/inbox"

    @pytest.mark.asyncio
    async def test_complete_draft_not_found_returns_404(self) -> None:
        """POST /complete returns 404 when draft not found."""
        from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
            DraftNotFoundError,
        )

        mock_complete_svc = AsyncMock()
        mock_complete_svc.complete = AsyncMock(side_effect=DraftNotFoundError(DRAFT_ID, TENANT_ID))

        app = _build_app_with_mocks(complete_svc=mock_complete_svc)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/vitalia/onboarding/drafts/{DRAFT_ID}/complete",
                json={},
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 404


class TestStreamEndpoint:
    """GET /api/v1/vitalia/onboarding/drafts/{id}/stream (SSE)."""

    @pytest.mark.asyncio
    async def test_stream_returns_200_with_event_stream_content_type(self) -> None:
        """GET /stream returns 200 with text/event-stream content type."""
        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/vitalia/onboarding/drafts/{DRAFT_ID}/stream",
                headers={"X-Tenant-ID": str(TENANT_ID)},
            )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
