"""T-8: notify_router tests — template-only WhatsApp + ComplianceService guard + audit log.

TDD: tests define the router contract BEFORE implementation.
Coverage:
  A1: template_id=empty → FreeTextNotificationError → 422 (test_template_only_accepted)
  A2: ComplianceService raises BlockedChannelError → NotificationBlockedError → 422
  A3: audit log row written on sent (action=reminder_sent)
  A4: audit log row written on blocked (action=reminder_blocked)
  A5: growth_studio_event "reminder_sent" emitted on success

All tests use mocked NotifyService and GrowthStudioEmitter (pure unit — no Postgres).
HTTP layer tested via httpx.AsyncClient + FastAPI test app (in-process).

Per 05-guidelines TDD-mandatory + vitalia/.claude/rules/hipaa-lite.md.

Acceptance criteria (06-tickets.yaml T-8):
  A1: Free-text template NOT in catalog → 400/422
  A2: Template contains PHI → ComplianceService.BlockedChannelError → 422
  A3: Happy path → send + audit row reminder_sent
  A4: Blocked path → audit row reminder_blocked
  A5: growth_studio_event "reminder_sent" emitted

downstream-regression-na: brand-local router test for vitalia scheduling notify
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
APPT_ID = uuid4()
USER_ID = uuid4()

_VALID_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "doctor",
}

_VALID_BODY = {
    "template_id": "recordatorio_manana",
    "channel": "whatsapp",
    "scheduled_for": None,
    "locale": "es-PE",
}


# ---------------------------------------------------------------------------
# App factory (isolated test app with mocked DI)
# ---------------------------------------------------------------------------


def _build_test_app(
    *,
    service_mock: MagicMock | None = None,
    emitter_mock: MagicMock | None = None,
) -> FastAPI:
    """Build a minimal FastAPI test app with the notify router mounted.

    Uses dependency override for get_async_session (no real DB needed).
    Patches _make_notify_service to inject the service mock.
    """
    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.vitalia.scheduling.api.notify_router import router

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/scheduling")

    # Override DB session dep (no real Postgres)
    async def _fake_session():
        session = MagicMock(spec=AsyncSession)
        yield session

    # HB-80: the notify handler now uses the committing session — override that one.
    from src.db import get_async_session_committing

    app.dependency_overrides[get_async_session_committing] = _fake_session

    return app


# ---------------------------------------------------------------------------
# Helper: patch both NotifyService factory AND GrowthStudioEmitter
# ---------------------------------------------------------------------------


def _patch_notify_service(service_mock: MagicMock):
    """Context manager: replace _make_notify_service in router module."""
    return patch(
        "src.modules.vitalia.scheduling.api.notify_router._make_notify_service",
        return_value=service_mock,
    )


def _patch_emitter():
    """Context manager: replace GrowthStudioEmitter in router module."""
    emitter_mock = MagicMock()
    emitter_mock.emit_event = AsyncMock(return_value=None)
    return patch(
        "src.modules.vitalia.scheduling.api.notify_router.GrowthStudioEmitter",
        return_value=emitter_mock,
    ), emitter_mock


def _make_notify_service_mock(*, raise_exc: Exception | None = None) -> MagicMock:
    """Create a NotifyService mock.

    Args:
        raise_exc: If set, send_notification raises this exception.
                   If None, returns {"status": "sent", ...} dict.
    """
    svc = MagicMock()
    if raise_exc is not None:
        svc.send_notification = AsyncMock(side_effect=raise_exc)
    else:
        svc.send_notification = AsyncMock(
            return_value={"status": "sent", "template_id": "recordatorio_manana", "channel": "whatsapp"}
        )
    return svc


# ---------------------------------------------------------------------------
# A1: Template-only enforcement — free-text rejected
# ---------------------------------------------------------------------------


class TestTemplateOnlyAccepted:
    """A1: template_id=empty → FreeTextNotificationError → 422.

    Q15 cement: WhatsApp template-only (no free-text body allowed).
    Free text risks PHI leakage in channel body.
    """

    @pytest.mark.asyncio
    async def test_empty_template_id_rejected(self):
        """Empty template_id returns 422 Unprocessable Entity.

        FreeTextNotificationError maps to HTTP 422 in the router.
        """
        from src.modules.vitalia.scheduling.domain.exceptions import FreeTextNotificationError

        service_mock = _make_notify_service_mock(raise_exc=FreeTextNotificationError("template_id required"))
        app = _build_test_app()

        with _patch_notify_service(service_mock):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json={**_VALID_BODY, "template_id": ""},
                    headers=_VALID_HEADERS,
                )

        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    @pytest.mark.asyncio
    async def test_whitespace_only_template_id_rejected(self):
        """Whitespace-only template_id also returns 422.

        Pydantic min_length=1 or FreeTextNotificationError catches this.
        """
        from src.modules.vitalia.scheduling.domain.exceptions import FreeTextNotificationError

        service_mock = _make_notify_service_mock(raise_exc=FreeTextNotificationError("template_id required"))
        app = _build_test_app()

        with _patch_notify_service(service_mock):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json={**_VALID_BODY, "template_id": "   "},
                    headers=_VALID_HEADERS,
                )

        # Pydantic min_length=1 catches before service; also 422 from service
        assert resp.status_code in (422, 400), f"Expected 422/400, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_valid_template_id_accepted(self):
        """Valid non-empty template_id returns 200 success.

        Template-only gate passes when template_id is non-empty string.
        """
        service_mock = _make_notify_service_mock()
        app = _build_test_app()

        with (
            _patch_notify_service(service_mock),
            patch("src.modules.vitalia.scheduling.api.notify_router.GrowthStudioEmitter") as em_cls,
        ):
            em_cls.return_value.emit_event = AsyncMock(return_value=None)
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=_VALID_HEADERS,
                )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body.get("status") == "sent"
        assert body.get("template_id") == _VALID_BODY["template_id"]


# ---------------------------------------------------------------------------
# A2: ComplianceService blocks PHI message
# ---------------------------------------------------------------------------


class TestComplianceServiceBlocksPHIMessage:
    """A2: ComplianceService raises BlockedChannelError → NotificationBlockedError → 422.

    Per hipaa-lite.md: unencrypted channel (whatsapp_free) is blocked.
    ComplianceService.validate_outbound_message raises BlockedChannelError.
    NotifyService re-raises as NotificationBlockedError.
    Router maps to 422 Unprocessable Entity.
    """

    @pytest.mark.asyncio
    async def test_compliance_service_blocks_phi_message(self):
        """ComplianceService block raises 422 with compliance message."""
        from src.modules.vitalia.scheduling.domain.exceptions import NotificationBlockedError

        service_mock = _make_notify_service_mock(
            raise_exc=NotificationBlockedError(
                appointment_id=APPT_ID,
                reason="PHI en canal no encriptado (whatsapp_free)",
            )
        )
        app = _build_test_app()

        with _patch_notify_service(service_mock):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=_VALID_HEADERS,
                )

        assert resp.status_code == 422, f"Expected 422 (blocked), got {resp.status_code}: {resp.text}"
        body = resp.json()
        # Response must mention compliance block
        detail = body.get("detail", "")
        assert "bloqueada" in detail.lower() or "compliance" in detail.lower() or "blocked" in detail.lower(), (
            f"Expected compliance block message in detail, got: {detail!r}"
        )

    @pytest.mark.asyncio
    async def test_blocked_channel_still_returns_422_not_500(self):
        """BlockedChannelError from compliance NEVER surfaces as 500.

        Internal exception must be mapped cleanly to 422 by the router.
        """
        from src.modules.vitalia.scheduling.domain.exceptions import NotificationBlockedError

        service_mock = _make_notify_service_mock(
            raise_exc=NotificationBlockedError(
                appointment_id=APPT_ID,
                reason="PHI en canal SMS",
            )
        )
        app = _build_test_app()

        with _patch_notify_service(service_mock):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=_VALID_HEADERS,
                )

        assert resp.status_code != 500, "BlockedChannelError must NOT become HTTP 500"
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# A3: Audit log row — reminder_sent
# ---------------------------------------------------------------------------


class TestAuditLogReminderSent:
    """A3: Audit log row written on successful send.

    HIPAA-lite mandate: every notification attempt (sent or blocked)
    must produce an audit row. This test verifies the SENT path.
    """

    @pytest.mark.asyncio
    async def test_audit_log_reminder_sent(self):
        """NotifyService.send_notification called → audit written inside service.

        The audit write happens inside NotifyService (already tested in
        test_notify_service.py). This test verifies the router correctly
        calls send_notification with expected args, triggering the audit.
        """
        service_mock = _make_notify_service_mock()
        app = _build_test_app()

        with (
            _patch_notify_service(service_mock),
            patch("src.modules.vitalia.scheduling.api.notify_router.GrowthStudioEmitter") as em_cls,
        ):
            em_cls.return_value.emit_event = AsyncMock(return_value=None)
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=_VALID_HEADERS,
                )

        assert resp.status_code == 200
        # Verify service was called with correct args (including tenant+clinic for dual filter)
        service_mock.send_notification.assert_called_once()
        call_kwargs = service_mock.send_notification.call_args.kwargs
        assert str(call_kwargs["appointment_id"]) == str(APPT_ID)
        assert str(call_kwargs["tenant_id"]) == str(TENANT_ID)
        assert str(call_kwargs["clinic_id"]) == str(CLINIC_ID)
        assert call_kwargs["template_id"] == _VALID_BODY["template_id"]
        assert call_kwargs["channel"] == _VALID_BODY["channel"]

    @pytest.mark.asyncio
    async def test_audit_uses_dual_filter(self):
        """Router passes BOTH tenant_id AND clinic_id to NotifyService.

        HIPAA-lite dual filter: audit log must include both scope fields.
        Router must NOT pass only tenant_id (missing clinic = compliance fail).
        """
        service_mock = _make_notify_service_mock()
        app = _build_test_app()

        other_clinic = uuid4()
        headers = {**_VALID_HEADERS, "X-Clinic-ID": str(other_clinic)}

        with (
            _patch_notify_service(service_mock),
            patch("src.modules.vitalia.scheduling.api.notify_router.GrowthStudioEmitter") as em_cls,
        ):
            em_cls.return_value.emit_event = AsyncMock(return_value=None)
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=headers,
                )

        assert resp.status_code == 200
        call_kwargs = service_mock.send_notification.call_args.kwargs
        # clinic_id must match the header, not default or None
        assert str(call_kwargs["clinic_id"]) == str(other_clinic)


# ---------------------------------------------------------------------------
# A4: Audit log row — reminder_blocked
# ---------------------------------------------------------------------------


class TestAuditLogReminderBlocked:
    """A4: Audit log row written even when ComplianceService blocks.

    Per HIPAA-lite: blocked notification attempts are auditable
    (suspicious access pattern). Audit must still be written.
    The audit write for BLOCKED path happens inside NotifyService.
    Router test verifies the blocked path still reaches 422.
    """

    @pytest.mark.asyncio
    async def test_audit_log_reminder_blocked(self):
        """Router returns 422 on block; service was called (= audit written inside).

        NotifyService writes audit BEFORE raising NotificationBlockedError.
        This test verifies the router propagates 422 correctly.
        """
        from src.modules.vitalia.scheduling.domain.exceptions import NotificationBlockedError

        service_mock = _make_notify_service_mock(
            raise_exc=NotificationBlockedError(
                appointment_id=APPT_ID,
                reason="whatsapp_free channel blocked",
            )
        )
        app = _build_test_app()

        with _patch_notify_service(service_mock):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=_VALID_HEADERS,
                )

        assert resp.status_code == 422
        # Service must have been called (= audit happens inside service before raise)
        service_mock.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_written_on_not_found(self):
        """Router returns 404 for cross-clinic appointment; service called (= audit written).

        AppointmentNotFoundError from cross-clinic access: service writes audit
        before raising (per HIPAA-lite suspicious access log).
        """
        from src.modules.vitalia.scheduling.domain.exceptions import AppointmentNotFoundError

        service_mock = _make_notify_service_mock(
            raise_exc=AppointmentNotFoundError(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
            )
        )
        app = _build_test_app()

        with _patch_notify_service(service_mock):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=_VALID_HEADERS,
                )

        assert resp.status_code == 404
        service_mock.send_notification.assert_called_once()


# ---------------------------------------------------------------------------
# A5: Telemetry event emitted
# ---------------------------------------------------------------------------


class TestTelemetryEventEmitted:
    """A5: growth_studio_event "reminder_sent" emitted on successful send.

    Per 03-arch § 10: 7 critical funnel events. "reminder_sent" is #7.
    GrowthStudioEmitter.emit_event called with event_type="reminder_sent".
    Fire-forget: failure does NOT propagate (emitter swallows internally).
    """

    @pytest.mark.asyncio
    async def test_telemetry_event_emitted_on_success(self):
        """GrowthStudioEmitter.emit_event called with reminder_sent on 200."""
        service_mock = _make_notify_service_mock()
        app = _build_test_app()

        with (
            _patch_notify_service(service_mock),
            patch("src.modules.vitalia.scheduling.api.notify_router.GrowthStudioEmitter") as em_cls,
        ):
            emitter_instance = MagicMock()
            emitter_instance.emit_event = AsyncMock(return_value=None)
            em_cls.return_value = emitter_instance

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=_VALID_HEADERS,
                )

        assert resp.status_code == 200
        # Verify GrowthStudioEmitter was called with correct event_type
        emitter_instance.emit_event.assert_called_once()
        call_kwargs = emitter_instance.emit_event.call_args.kwargs
        assert call_kwargs.get("event_type") == "reminder_sent", (
            f"Expected event_type='reminder_sent', got: {call_kwargs.get('event_type')!r}"
        )
        # Verify entity_id = appointment_id
        assert str(call_kwargs.get("entity_id")) == str(APPT_ID), (
            f"Expected entity_id={APPT_ID}, got: {call_kwargs.get('entity_id')}"
        )

    @pytest.mark.asyncio
    async def test_telemetry_not_emitted_when_blocked(self):
        """GrowthStudioEmitter NOT called when compliance blocks.

        When NotificationBlockedError is raised, the router returns 422
        before reaching the emit block. No telemetry for blocked sends.
        """
        from src.modules.vitalia.scheduling.domain.exceptions import NotificationBlockedError

        service_mock = _make_notify_service_mock(raise_exc=NotificationBlockedError(reason="blocked"))
        app = _build_test_app()

        with (
            _patch_notify_service(service_mock),
            patch("src.modules.vitalia.scheduling.api.notify_router.GrowthStudioEmitter") as em_cls,
        ):
            emitter_instance = MagicMock()
            emitter_instance.emit_event = AsyncMock(return_value=None)
            em_cls.return_value = emitter_instance

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=_VALID_HEADERS,
                )

        assert resp.status_code == 422
        # emitter.emit_event must NOT have been called (blocked path returns before emit)
        emitter_instance.emit_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_telemetry_emitter_failure_does_not_propagate(self):
        """If GrowthStudioEmitter.emit_event raises, router still returns 200.

        Fire-forget contract: telemetry failures NEVER affect the user response.
        """
        service_mock = _make_notify_service_mock()
        app = _build_test_app()

        with (
            _patch_notify_service(service_mock),
            patch("src.modules.vitalia.scheduling.api.notify_router.GrowthStudioEmitter") as em_cls,
        ):
            emitter_instance = MagicMock()
            # Simulate emitter failure (should be swallowed)
            emitter_instance.emit_event = AsyncMock(side_effect=RuntimeError("DB unavailable"))
            em_cls.return_value = emitter_instance

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=_VALID_HEADERS,
                )

        # Despite emitter failure, response is 200 (fire-forget)
        assert resp.status_code == 200, f"Expected 200 despite emitter failure, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# RBAC enforcement
# ---------------------------------------------------------------------------


class TestRBACEnforcement:
    """Router denies non-PHI roles with 403."""

    @pytest.mark.asyncio
    async def test_unauthorized_role_rejected(self):
        """Role 'marketing' → 403 Forbidden (not a PHI role)."""
        service_mock = _make_notify_service_mock()
        app = _build_test_app()
        headers = {**_VALID_HEADERS, "X-User-Role": "marketing"}

        with _patch_notify_service(service_mock):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=headers,
                )

        assert resp.status_code == 403
        # Service must NOT be called (rejected at RBAC gate)
        service_mock.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_doctor_role_allowed(self):
        """Role 'doctor' → 200 (PHI role permitted)."""
        service_mock = _make_notify_service_mock()
        app = _build_test_app()
        headers = {**_VALID_HEADERS, "X-User-Role": "doctor"}

        with (
            _patch_notify_service(service_mock),
            patch("src.modules.vitalia.scheduling.api.notify_router.GrowthStudioEmitter") as em_cls,
        ):
            em_cls.return_value.emit_event = AsyncMock(return_value=None)
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=headers,
                )

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_valeria_assistant_role_allowed(self):
        """Role 'valeria_assistant' → 200 (PHI role permitted per 03-arch § 5.1)."""
        service_mock = _make_notify_service_mock()
        app = _build_test_app()
        headers = {**_VALID_HEADERS, "X-User-Role": "valeria_assistant"}

        with (
            _patch_notify_service(service_mock),
            patch("src.modules.vitalia.scheduling.api.notify_router.GrowthStudioEmitter") as em_cls,
        ):
            em_cls.return_value.emit_event = AsyncMock(return_value=None)
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/v1/scheduling/appointments/{APPT_ID}/notify",
                    json=_VALID_BODY,
                    headers=headers,
                )

        assert resp.status_code == 200
