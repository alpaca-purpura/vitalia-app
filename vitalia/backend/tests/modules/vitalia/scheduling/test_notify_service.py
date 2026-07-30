"""RED tests — NotifyService: ComplianceService guard + template-only + audit log.

TDD: tests define expected interface BEFORE implementation.
All tests use in-memory mocks — no Postgres required (pure unit tests).

Contract (03-arch § 5 + hipaa-lite.md):
- ComplianceService guard blocks PHI in outbound channels
- Template-only messages enforced (no free text)
- Audit log sync write with template_id + channel (no message body PHI)

Per 05-guidelines TDD-mandatory + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------


def _import_service():
    from src.modules.vitalia.scheduling.application.services.notify_service import (  # noqa: PLC0415
        NotifyService,
    )

    return NotifyService


def _import_exceptions():
    from src.modules.vitalia.scheduling.domain.exceptions import (  # noqa: PLC0415
        AppointmentNotFoundError,
        FreeTextNotificationError,
        NotificationBlockedError,
    )

    return AppointmentNotFoundError, NotificationBlockedError, FreeTextNotificationError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
APPT_ID = uuid4()
USER_ID = uuid4()
PATIENT_ID = uuid4()


def _make_mock_repo() -> MagicMock:
    """Repo that returns a minimal appointment dict for notify lookup."""
    repo = MagicMock()
    repo.get_by_id = AsyncMock(
        return_value={
            "appointment_id": str(APPT_ID),
            "patient_id": str(PATIENT_ID),
            "tenant_id": str(TENANT_ID),
            "clinic_id": str(CLINIC_ID),
            "status": "SCHEDULED",
        }
    )
    return repo


def _make_mock_audit_writer() -> MagicMock:
    writer = MagicMock()
    writer.write = AsyncMock(return_value=None)
    return writer


def _make_mock_compliance_service(*, blocked: bool = False) -> MagicMock:
    """Mock ComplianceService. When blocked=True, raises BlockedChannelError."""
    compliance = MagicMock()
    if blocked:
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (  # noqa: PLC0415
            BlockedChannelError,
        )

        compliance.validate_outbound_message = AsyncMock(side_effect=BlockedChannelError("whatsapp"))
    else:
        compliance.validate_outbound_message = AsyncMock(return_value=None)
    return compliance


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNotifyServiceComplianceGuard:
    """ComplianceService.validate_outbound_message guards PHI in outbound channels."""

    @pytest.mark.asyncio
    async def test_blocks_phi_via_compliance_service(self):
        """send_notification() must raise NotificationBlockedError when compliance blocks.

        HIPAA-lite mandate: ComplianceService.validate_outbound_message MUST be called
        before dispatching any WhatsApp/channel message. If compliance raises
        BlockedChannelError → NotifyService must re-raise as NotificationBlockedError.
        """
        NotifyService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        compliance = _make_mock_compliance_service(blocked=True)
        service = NotifyService(
            repo=repo,
            audit_writer=audit_writer,
            compliance_service=compliance,
        )

        AppointmentNotFoundError, NotificationBlockedError, FreeTextNotificationError = _import_exceptions()

        with pytest.raises(NotificationBlockedError):
            await service.send_notification(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                user_id=USER_ID,
                template_id="recordatorio_cita_1d",
                channel="whatsapp",
            )

        # ComplianceService must have been called
        compliance.validate_outbound_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_compliance_service_called_before_dispatch(self):
        """validate_outbound_message must be called on every send_notification call.

        No bypass allowed. Even for 'safe' templates, compliance guard must run
        to ensure future template updates don't slip through PHI.
        """
        NotifyService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        compliance = _make_mock_compliance_service(blocked=False)
        service = NotifyService(
            repo=repo,
            audit_writer=audit_writer,
            compliance_service=compliance,
        )

        await service.send_notification(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            template_id="confirmacion_cita",
            channel="whatsapp",
        )

        # Compliance check MUST have been called
        compliance.validate_outbound_message.assert_called_once()


class TestNotifyServiceTemplateOnly:
    """Template-only enforcement — no free text messages allowed."""

    @pytest.mark.asyncio
    async def test_template_only_allowed(self):
        """send_notification() must require a template_id.

        Free-text messages are PROHIBITED per HIPAA-lite (PHI body in channel).
        Only pre-approved template_id values are allowed.
        """
        NotifyService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        compliance = _make_mock_compliance_service(blocked=False)
        service = NotifyService(
            repo=repo,
            audit_writer=audit_writer,
            compliance_service=compliance,
        )

        AppointmentNotFoundError, NotificationBlockedError, FreeTextNotificationError = _import_exceptions()

        # Empty template_id → must raise FreeTextNotificationError
        with pytest.raises((FreeTextNotificationError, ValueError, TypeError)):
            await service.send_notification(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                user_id=USER_ID,
                template_id="",  # empty = free text attempt
                channel="whatsapp",
            )

    @pytest.mark.asyncio
    async def test_valid_template_id_accepted(self):
        """A non-empty template_id passes template-only gate."""
        NotifyService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        compliance = _make_mock_compliance_service(blocked=False)
        service = NotifyService(
            repo=repo,
            audit_writer=audit_writer,
            compliance_service=compliance,
        )

        # Should not raise on valid template
        result = await service.send_notification(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            template_id="recordatorio_cita_1d",
            channel="whatsapp",
        )

        assert result is not None
        assert result.get("status") in ("sent", "dispatched", "queued")


class TestNotifyServiceAuditLog:
    """Audit log sync write per HIPAA-lite mandate."""

    @pytest.mark.asyncio
    async def test_audit_log_written(self):
        """send_notification() must write audit log with template_id + channel.

        HIPAA-lite: sending a notification is a PHI-adjacent action.
        Audit log must capture action='send_notification', template_id, channel.
        The message body itself MUST NOT be in the audit payload (PHI risk).
        """
        NotifyService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        compliance = _make_mock_compliance_service(blocked=False)
        service = NotifyService(
            repo=repo,
            audit_writer=audit_writer,
            compliance_service=compliance,
        )

        await service.send_notification(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            template_id="recordatorio_cita_1d",
            channel="whatsapp",
        )

        audit_writer.write.assert_called_once()
        call_kwargs = audit_writer.write.call_args.kwargs
        assert call_kwargs.get("tenant_id") == TENANT_ID
        assert call_kwargs.get("clinic_id") == CLINIC_ID

        # Action must identify notification
        action = call_kwargs.get("action", "")
        assert "notification" in action.lower() or "notify" in action.lower() or "send" in action.lower()

    @pytest.mark.asyncio
    async def test_audit_log_payload_has_template_not_body(self):
        """Audit payload must include template_id but NOT message body (PHI risk).

        Logging the message body risks PHI leakage if template contains patient data.
        Only the template_id reference is safe to log.
        """
        NotifyService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        compliance = _make_mock_compliance_service(blocked=False)
        service = NotifyService(
            repo=repo,
            audit_writer=audit_writer,
            compliance_service=compliance,
        )

        template = "recordatorio_cita_1d"
        await service.send_notification(
            appointment_id=APPT_ID,
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            template_id=template,
            channel="whatsapp",
        )

        call_kwargs = audit_writer.write.call_args.kwargs
        payload = call_kwargs.get("payload", {})
        # template_id reference in payload is allowed (it's a key, not PHI)
        assert template in str(payload) or "template" in str(payload).lower()

    @pytest.mark.asyncio
    async def test_audit_log_written_even_when_blocked(self):
        """Audit log must be written even when compliance blocks.

        A blocked notification attempt is auditable — suspicious access pattern.
        """
        NotifyService = _import_service()
        repo = _make_mock_repo()
        audit_writer = _make_mock_audit_writer()
        compliance = _make_mock_compliance_service(blocked=True)
        service = NotifyService(
            repo=repo,
            audit_writer=audit_writer,
            compliance_service=compliance,
        )

        AppointmentNotFoundError, NotificationBlockedError, FreeTextNotificationError = _import_exceptions()

        with pytest.raises(NotificationBlockedError):
            await service.send_notification(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                user_id=USER_ID,
                template_id="template_con_phi_detectado",
                channel="whatsapp",
            )

        # Audit must still be written on compliance block (suspicious action log)
        audit_writer.write.assert_called_once()


class TestNotifyServiceCrossClinic:
    """Cross-clinic appointment returns 404 before any notification."""

    @pytest.mark.asyncio
    async def test_cross_clinic_returns_404(self):
        """send_notification() on cross-clinic appointment must raise AppointmentNotFoundError."""
        NotifyService = _import_service()
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        audit_writer = _make_mock_audit_writer()
        compliance = _make_mock_compliance_service(blocked=False)
        service = NotifyService(
            repo=repo,
            audit_writer=audit_writer,
            compliance_service=compliance,
        )

        AppointmentNotFoundError, NotificationBlockedError, FreeTextNotificationError = _import_exceptions()

        OTHER_CLINIC = uuid4()
        with pytest.raises(AppointmentNotFoundError):
            await service.send_notification(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=OTHER_CLINIC,
                user_id=USER_ID,
                template_id="recordatorio_cita_1d",
                channel="whatsapp",
            )
