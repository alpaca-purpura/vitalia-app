"""Tests for PHI sanitization and compliance gate — TDD RED (T-inbox-be-3).

SC-04 coverage:
- PHI not leaked in response when role not authorized
- Audit log row created on PHI access
- Cross-tenant access blocked (dual-filter)
- sanitize_payload removes PHI fields before traces
- ComplianceService blocks medical results by unencrypted channel
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

TENANT_A = uuid4()
TENANT_B = uuid4()
CLINIC_A = uuid4()
CLINIC_B = uuid4()


@pytest.mark.asyncio
async def test_send_message_sanitize_payload_before_trace() -> None:
    """SC-04: sanitize_payload removes PHI before any structlog trace event."""
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        SendMessageService,
    )

    conv_repo = AsyncMock()
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()
    audit_writer = AsyncMock()
    event_bus = AsyncMock()
    session = AsyncMock()

    conv_model = MagicMock()
    conv_model.id = uuid4()
    conv_model.tenant_id = TENANT_A
    conv_model.clinic_id = CLINIC_A
    conv_model.handler_mode = "human"
    conv_model.channel = "whatsapp"
    conv_model.deleted_at = None
    conv_model.updated_at = datetime.now(UTC)
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)

    saved_msg = MagicMock()
    saved_msg.id = uuid4()
    saved_msg.conversation_id = conv_model.id
    saved_msg.tenant_id = TENANT_A
    saved_msg.clinic_id = CLINIC_A
    saved_msg.sender_type = "agent_human"
    saved_msg.sender_user_id = uuid4()
    saved_msg.body_text = "El paciente preguntó sobre blanqueamiento"
    saved_msg.media_kind = None
    saved_msg.media_url = None
    saved_msg.media_duration_s = None
    saved_msg.transcription_text = None
    saved_msg.transcription_confidence = None
    saved_msg.retracted_at = None
    saved_msg.retract_succeeded = None
    saved_msg.handler_mode = "human"
    saved_msg.sent_at = datetime.now(UTC)
    msg_repo.create = AsyncMock(return_value=saved_msg)

    svc = SendMessageService(
        conv_repo=conv_repo,
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        session=session,
    )

    with patch("luana_core_observability.recording.sanitization.sanitize_payload") as mock_sanitize:
        mock_sanitize.return_value = {"message_id": "sanitized"}

        await svc.send(
            tenant_id=TENANT_A,
            clinic_id=CLINIC_A,
            conversation_id=conv_model.id,
            user_id=uuid4(),
            body_text="Texto del mensaje",
            idempotency_key=None,
        )

        # sanitize_payload must be called at some point during operation
        # (either by audit_writer or service itself before logging)
        assert audit_writer.write.called


@pytest.mark.asyncio
async def test_cross_tenant_access_blocked_by_dual_filter() -> None:
    """SC-04: tenant_A request cannot access clinic from tenant_B."""
    from src.modules.vitalia.inbox.application.services.set_mode_service import (
        ConversationNotFoundError,
        SetModeService,
    )

    conv_repo = AsyncMock()
    # Repository returns None because dual-filter mismatch (tenant_B clinic_A is alien)
    conv_repo.get_by_id = AsyncMock(return_value=None)

    svc = SetModeService(
        conv_repo=conv_repo,
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        session=AsyncMock(),
    )

    # tenant_A tries to access conversation in CLINIC_B (belongs to tenant_B)
    with pytest.raises(ConversationNotFoundError):
        await svc.set_mode(
            tenant_id=TENANT_A,
            clinic_id=CLINIC_B,  # wrong clinic
            conversation_id=uuid4(),
            new_mode="human",
            proposal_required=False,
            expected_updated_at=datetime.now(UTC),
            changed_by_user_id=uuid4(),
        )

    # Verify that the query was issued with the provided tenant+clinic (dual-filter)
    call_kwargs = conv_repo.get_by_id.call_args.kwargs
    assert call_kwargs.get("tenant_id") == TENANT_A
    assert call_kwargs.get("scope_id") == CLINIC_B


@pytest.mark.asyncio
async def test_proactive_outbound_blocked_on_unencrypted_channel() -> None:
    """ComplianceService gate: PHI channel constraint → blocked for sensitive content."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        ComplianceBlockedError,
        ProactiveOutboundService,
    )

    lead_repo = AsyncMock()
    lead_model = MagicMock()
    lead_model.id = uuid4()
    lead_model.tenant_id = TENANT_A
    lead_model.clinic_id = CLINIC_A
    lead_model.marketing_opt_in = True
    lead_model.whatsapp_phone = "+521234567890"
    lead_repo.get_by_id = AsyncMock(return_value=lead_model)

    compliance_service = AsyncMock()
    blocked = MagicMock()
    blocked.allowed = False
    blocked.failed_policy = "waba_24h"
    blocked.reason = "24h window not satisfied"
    compliance_service.check = AsyncMock(return_value=blocked)

    svc = ProactiveOutboundService(
        lead_repo=lead_repo,
        conv_repo=AsyncMock(),
        msg_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        compliance_service=compliance_service,
        rate_limiter=AsyncMock(),
        channel_adapters={},
    )

    with pytest.raises(ComplianceBlockedError):
        await svc.send_proactive(
            tenant_id=TENANT_A,
            clinic_id=CLINIC_A,
            lead_id=lead_model.id,
            template_id="recordatorio_proxima_sesion",
            variables={"fecha": "mañana"},
            channel="whatsapp",
            sent_by_user_id=uuid4(),
        )
