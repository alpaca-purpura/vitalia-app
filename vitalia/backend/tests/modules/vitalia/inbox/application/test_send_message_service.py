"""Tests for SendMessageService — TDD RED (T-inbox-be-3).

SC-01 happy path coverage:
- Idempotency-Key dedup prevents duplicate inserts
- ai-path → enqueues Adrián turn (returns message stub, audit log row written)
- human-path → directly saves message row, emits MessageSent via outbox
- audit log row written pre-response (sync mandatory per hipaa-lite.md)
- MessageSent domain event emitted via outbox bus

PHI dual-filter verified via service accepting tenant_id AND clinic_id.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()
USER_ID = uuid4()
MSG_ID = uuid4()


def _make_conversation_model(handler_mode: str = "ai") -> MagicMock:
    conv = MagicMock()
    conv.id = CONV_ID
    conv.tenant_id = TENANT_ID
    conv.clinic_id = CLINIC_ID
    conv.handler_mode = handler_mode
    conv.channel = "whatsapp"
    conv.updated_at = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    conv.deleted_at = None
    return conv


def _make_message_model(msg_id: UUID | None = None) -> MagicMock:
    msg = MagicMock()
    msg.id = msg_id or MSG_ID
    msg.conversation_id = CONV_ID
    msg.tenant_id = TENANT_ID
    msg.clinic_id = CLINIC_ID
    msg.sender_type = "agent_human"
    msg.sender_user_id = USER_ID
    msg.body_text = "Hola, ¿en qué puedo ayudarte?"
    msg.media_kind = None
    msg.media_url = None
    msg.media_duration_s = None
    msg.transcription_text = None
    msg.transcription_confidence = None
    msg.retracted_at = None
    msg.retract_succeeded = None
    msg.handler_mode = "human"
    msg.sent_at = datetime(2026, 5, 20, 12, 0, 1, tzinfo=UTC)
    return msg


# ---------------------------------------------------------------------------
# Test: human path — direct send
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_human_path_saves_message_and_emits_event() -> None:
    """SC-01: human handler_mode → direct send → MessageSent event emitted."""
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        SendMessageService,
    )

    conv_repo = AsyncMock()
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()
    audit_writer = AsyncMock()
    event_bus = AsyncMock()
    session = AsyncMock()

    conv_model = _make_conversation_model(handler_mode="human")
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)

    saved_msg = _make_message_model()
    msg_repo.create = AsyncMock(return_value=saved_msg)

    svc = SendMessageService(
        conv_repo=conv_repo,
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        session=session,
    )

    result = await svc.send(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        user_id=USER_ID,
        body_text="Hola, ¿en qué puedo ayudarte?",
        idempotency_key=None,
    )

    assert result is not None
    # Audit log must be written before returning
    audit_writer.write.assert_called_once()
    # Event must be emitted
    event_bus.publish.assert_called_once()
    # Message repository create must be called
    msg_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_audit_log_written_before_return() -> None:
    """HIPAA-lite: audit log write is SYNC and happens before return value."""
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        SendMessageService,
    )

    call_order: list[str] = []

    conv_repo = AsyncMock()
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()
    event_bus = AsyncMock()
    session = AsyncMock()

    audit_writer = AsyncMock()

    async def audit_side_effect(*args: object, **kwargs: object) -> None:
        call_order.append("audit")

    async def msg_create_side_effect(*args: object, **kwargs: object) -> MagicMock:
        call_order.append("msg_create")
        return _make_message_model()

    audit_writer.write = AsyncMock(side_effect=audit_side_effect)
    msg_repo.create = AsyncMock(side_effect=msg_create_side_effect)

    conv_model = _make_conversation_model(handler_mode="human")
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)

    svc = SendMessageService(
        conv_repo=conv_repo,
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        session=session,
    )

    await svc.send(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        user_id=USER_ID,
        body_text="Test",
        idempotency_key=None,
    )

    # Audit must be written BEFORE or AFTER msg creation but BEFORE return
    # Both calls must have happened
    assert "audit" in call_order
    assert "msg_create" in call_order


@pytest.mark.asyncio
async def test_send_message_idempotency_returns_cached_on_duplicate() -> None:
    """SC-01: Idempotency-Key header prevents duplicate inserts on retry."""
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        SendMessageService,
    )

    conv_repo = AsyncMock()
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()
    audit_writer = AsyncMock()
    event_bus = AsyncMock()
    session = AsyncMock()
    idempotency_store = AsyncMock()

    # Simulate: key already claimed, return cached result
    idempotency_store.claim = AsyncMock(return_value=False)
    idempotency_store.cached_result = AsyncMock(return_value={"message_id": str(MSG_ID)})

    conv_model = _make_conversation_model(handler_mode="human")
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)

    svc = SendMessageService(
        conv_repo=conv_repo,
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        session=session,
        idempotency_store=idempotency_store,
    )

    await svc.send(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        user_id=USER_ID,
        body_text="Test",
        idempotency_key="key-abc-123",
    )

    # When idempotency cache hit, msg_repo.create should NOT be called again
    msg_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_conversation_not_found_raises_404() -> None:
    """Send to non-existent conversation raises NotFoundError."""
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        ConversationNotFoundError,
        SendMessageService,
    )

    conv_repo = AsyncMock()
    conv_repo.get_by_id = AsyncMock(return_value=None)

    svc = SendMessageService(
        conv_repo=conv_repo,
        msg_repo=AsyncMock(),
        receipt_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        session=AsyncMock(),
    )

    with pytest.raises(ConversationNotFoundError):
        await svc.send(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=uuid4(),
            user_id=USER_ID,
            body_text="Test",
            idempotency_key=None,
        )


@pytest.mark.asyncio
async def test_send_message_ai_path_emits_message_sent_event() -> None:
    """ai handler_mode: MessageSent event emitted regardless of path."""
    from src.modules.vitalia.crm.domain.events import MessageSent
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        SendMessageService,
    )

    conv_repo = AsyncMock()
    msg_repo = AsyncMock()
    receipt_repo = AsyncMock()
    audit_writer = AsyncMock()
    session = AsyncMock()

    published_events: list[object] = []

    async def capture_publish(event: object, **kwargs: object) -> None:
        published_events.append(event)

    event_bus = AsyncMock()
    event_bus.publish = AsyncMock(side_effect=capture_publish)

    conv_model = _make_conversation_model(handler_mode="ai")
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)
    msg_repo.create = AsyncMock(return_value=_make_message_model())

    svc = SendMessageService(
        conv_repo=conv_repo,
        msg_repo=msg_repo,
        receipt_repo=receipt_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        session=session,
    )

    await svc.send(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        user_id=USER_ID,
        body_text="Mensaje de prueba",
        idempotency_key=None,
    )

    assert any(isinstance(e, MessageSent) for e in published_events)
