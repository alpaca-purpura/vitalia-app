"""Tests for POST /inbox/transcribe — audio transcription endpoint.

TDD: covers SC-02 (low confidence fallback) + happy path + 403.

downstream-regression-na: brand-local vitalia inbox router test
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


def _make_app() -> FastAPI:
    """Build minimal test app with inbox router."""
    from src.modules.vitalia.inbox.api.router import router as inbox_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(inbox_router, prefix="/api/v1/vitalia/inbox")
    return app


TENANT_ID = uuid4()
CLINIC_ID = uuid4()
USER_ID = uuid4()
VALID_TOKEN = "Bearer valid-test-token"


@pytest.fixture()
def mock_clinic_ctx_doctor() -> MagicMock:
    """Doctor context."""
    ctx = MagicMock()
    ctx.user_id = str(USER_ID)
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.role = "doctor"
    ctx.email = "doc@vitalia.test"
    ctx.name = "Dr. Test"
    return ctx


# ---------------------------------------------------------------------------
# SC-02 — low confidence → fallback_triggered=True, transcription_text=None
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_low_confidence_fallback(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SC-02: Whisper returns confidence <0.5 → fallback_triggered=True, text=None."""
    from src.modules.vitalia.inbox.application.services.whisper_transcribe_service import (
        TranscribeResult,
    )

    result = TranscribeResult(
        transcription_text=None,
        transcription_confidence=0.3,
        fallback_triggered=True,
    )
    transcribe_svc = AsyncMock()
    transcribe_svc.transcribe.return_value = result

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_transcribe_service",
        lambda: transcribe_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/transcribe",
            json={"audio_url": "https://cdn.vitalia.test/audio/sample.ogg"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["fallback_triggered"] is True
    assert body["transcription_text"] is None
    assert body["transcription_confidence"] == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# Happy path — high confidence transcription → fallback_triggered=False
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcribe_high_confidence_200(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Happy path: Whisper confidence ≥ 0.5 → transcription_text populated."""
    from src.modules.vitalia.inbox.application.services.whisper_transcribe_service import (
        TranscribeResult,
    )

    result = TranscribeResult(
        transcription_text="Me duele el diente izquierdo.",
        transcription_confidence=0.92,
        fallback_triggered=False,
    )
    transcribe_svc = AsyncMock()
    transcribe_svc.transcribe.return_value = result

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_transcribe_service",
        lambda: transcribe_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/transcribe",
            json={"audio_url": "https://cdn.vitalia.test/audio/sample.ogg"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["fallback_triggered"] is False
    assert body["transcription_text"] == "Me duele el diente izquierdo."


# ---------------------------------------------------------------------------
# 403 — marketing role cannot transcribe PHI audio
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcribe_403_marketing_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """Marketing role cannot access PHI transcription endpoint → 403."""
    ctx = MagicMock()
    ctx.user_id = str(uuid4())
    ctx.tenant_id = TENANT_ID
    ctx.role = "marketing"

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=ctx),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/transcribe",
            json={"audio_url": "https://cdn.vitalia.test/audio/sample.ogg"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 403
