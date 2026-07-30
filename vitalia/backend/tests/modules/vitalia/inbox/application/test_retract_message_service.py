"""Tests for RetractMessageService — TDD RED (T-inbox-be-3).

SC-03 coverage:
- 5min action receipt window enforced → 410 Gone if expired
- Patient replied after message → 409 Conflict
- Channel retract succeeds → retract_succeeded=True
- Channel retract fails → fallback "marcar erróneo" (retract_succeeded=False)
- Email channel → ChannelRetractUnsupportedError caught → fallback
- MessageRetracted event emitted via outbox bus
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()
MSG_ID = uuid4()
USER_ID = uuid4()


def _make_message_model(
    sender_type: str = "agent_ai",
    sent_at: datetime | None = None,
) -> MagicMock:
    msg = MagicMock()
    msg.id = MSG_ID
    msg.conversation_id = CONV_ID
    msg.tenant_id = TENANT_ID
    msg.clinic_id = CLINIC_ID
    msg.sender_type = sender_type
    msg.external_message_id = "wamid.test123"
    msg.channel = "whatsapp"
    msg.retracted_at = None
    msg.retract_succeeded = None
    msg.sent_at = sent_at or datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    return msg


def _make_receipt(expires_at: datetime, retracted_at: datetime | None = None) -> MagicMock:
    receipt = MagicMock()
    receipt.id = uuid4()
    receipt.message_id = MSG_ID
    receipt.expires_at = expires_at
    receipt.retracted_at = retracted_at
    return receipt


# ---------------------------------------------------------------------------
# 5-minute window tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retract_within_window_succeeds() -> None:
    """SC-03: retract within 5min window → retract_succeeded=True."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        RetractMessageService,
    )

    now = datetime.now(UTC)
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()
    conv_repo = AsyncMock()
    audit_writer = AsyncMock()
    event_bus = AsyncMock()

    msg_model = _make_message_model()
    msg_repo.get_by_id = AsyncMock(return_value=msg_model)

    # Receipt not yet expired
    receipt = _make_receipt(expires_at=now + timedelta(minutes=3))
    receipt_repo.get_active_for_message = AsyncMock(return_value=receipt)

    # No patient reply
    msg_repo.find_patient_reply_after = AsyncMock(return_value=None)

    # Adapter succeeds
    wa_adapter = AsyncMock()
    wa_retract = MagicMock()
    wa_retract.succeeded = True
    wa_adapter.retract_message_id = AsyncMock(return_value=wa_retract)

    updated_msg = _make_message_model()
    updated_msg.retract_succeeded = True
    msg_repo.mark_retracted = AsyncMock(return_value=updated_msg)

    svc = RetractMessageService(
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        conv_repo=conv_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        channel_adapters={"whatsapp": wa_adapter},
    )

    result = await svc.retract(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        message_id=MSG_ID,
        retracted_by_user_id=USER_ID,
        reason="user_undo",
    )

    assert result.retract_succeeded is True
    assert result.fallback_applied is False
    event_bus.publish.assert_called_once()


@pytest.mark.asyncio
async def test_retract_expired_window_raises_410() -> None:
    """SC-03: receipt expired → ActionReceiptExpiredError (→ 410 Gone)."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        ActionReceiptExpiredError,
        RetractMessageService,
    )

    now = datetime.now(UTC)
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()

    msg_model = _make_message_model()
    msg_repo.get_by_id = AsyncMock(return_value=msg_model)

    # Receipt already expired
    receipt = _make_receipt(expires_at=now - timedelta(minutes=1))
    receipt_repo.get_active_for_message = AsyncMock(return_value=receipt)

    svc = RetractMessageService(
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        conv_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        channel_adapters={},
    )

    with pytest.raises(ActionReceiptExpiredError):
        await svc.retract(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            message_id=MSG_ID,
            retracted_by_user_id=USER_ID,
            reason="user_undo",
        )


@pytest.mark.asyncio
async def test_retract_no_receipt_raises_404() -> None:
    """No active receipt → MessageNotRetractableError."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        MessageNotRetractableError,
        RetractMessageService,
    )

    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()

    msg_model = _make_message_model()
    msg_repo.get_by_id = AsyncMock(return_value=msg_model)
    receipt_repo.get_active_for_message = AsyncMock(return_value=None)

    svc = RetractMessageService(
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        conv_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        channel_adapters={},
    )

    with pytest.raises(MessageNotRetractableError):
        await svc.retract(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            message_id=MSG_ID,
            retracted_by_user_id=USER_ID,
            reason="user_undo",
        )


@pytest.mark.asyncio
async def test_retract_patient_replied_raises_409() -> None:
    """Patient replied after AI message → PatientRepliedConflictError (→ 409)."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        PatientRepliedConflictError,
        RetractMessageService,
    )

    now = datetime.now(UTC)
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()

    msg_model = _make_message_model()
    msg_repo.get_by_id = AsyncMock(return_value=msg_model)

    receipt = _make_receipt(expires_at=now + timedelta(minutes=3))
    receipt_repo.get_active_for_message = AsyncMock(return_value=receipt)

    # Patient replied
    patient_reply = _make_message_model(sender_type="patient")
    msg_repo.find_patient_reply_after = AsyncMock(return_value=patient_reply)

    svc = RetractMessageService(
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        conv_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        channel_adapters={},
    )

    with pytest.raises(PatientRepliedConflictError):
        await svc.retract(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            message_id=MSG_ID,
            retracted_by_user_id=USER_ID,
            reason="user_undo",
        )


@pytest.mark.asyncio
async def test_retract_channel_fail_applies_marcar_erroneo_fallback() -> None:
    """Channel retract fails → fallback_applied=True, retract_succeeded=False."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        RetractMessageService,
    )

    now = datetime.now(UTC)
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()

    msg_model = _make_message_model()
    msg_repo.get_by_id = AsyncMock(return_value=msg_model)

    receipt = _make_receipt(expires_at=now + timedelta(minutes=3))
    receipt_repo.get_active_for_message = AsyncMock(return_value=receipt)
    msg_repo.find_patient_reply_after = AsyncMock(return_value=None)

    # Adapter fails
    wa_adapter = AsyncMock()
    wa_retract = MagicMock()
    wa_retract.succeeded = False
    wa_adapter.retract_message_id = AsyncMock(return_value=wa_retract)

    marked_msg = _make_message_model()
    marked_msg.retract_succeeded = False
    msg_repo.mark_retracted = AsyncMock(return_value=marked_msg)

    svc = RetractMessageService(
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        conv_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        channel_adapters={"whatsapp": wa_adapter},
    )

    result = await svc.retract(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        message_id=MSG_ID,
        retracted_by_user_id=USER_ID,
        reason="user_undo",
    )

    assert result.retract_succeeded is False
    assert result.fallback_applied is True


@pytest.mark.asyncio
async def test_retract_email_channel_applies_fallback() -> None:
    """Email channel → ChannelRetractUnsupportedError → fallback marcar erróneo."""
    from src.modules.vitalia.connections.email.adapter import (
        ChannelRetractUnsupportedError,
    )
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        RetractMessageService,
    )

    now = datetime.now(UTC)
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()

    # Email message
    email_msg = _make_message_model()
    email_msg.channel = "email"
    email_msg.external_message_id = "email-msg-123"
    msg_repo.get_by_id = AsyncMock(return_value=email_msg)

    receipt = _make_receipt(expires_at=now + timedelta(minutes=3))
    receipt_repo.get_active_for_message = AsyncMock(return_value=receipt)
    msg_repo.find_patient_reply_after = AsyncMock(return_value=None)

    # Email adapter raises unsupported
    email_adapter = AsyncMock()
    email_adapter.retract_message_id = AsyncMock(side_effect=ChannelRetractUnsupportedError("email-msg-123", "email"))

    marked_msg = _make_message_model()
    marked_msg.retract_succeeded = False
    msg_repo.mark_retracted = AsyncMock(return_value=marked_msg)

    svc = RetractMessageService(
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        conv_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        channel_adapters={"email": email_adapter},
    )

    result = await svc.retract(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        message_id=MSG_ID,
        retracted_by_user_id=USER_ID,
        reason="user_undo",
    )

    assert result.fallback_applied is True
    assert result.retract_succeeded is False
