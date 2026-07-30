"""Integration tests — inbox send → action receipt → retract → audit + event.

TDD: Written RED before full implementation exists (SC-01 end-to-end path).

Scope (03-arch-be.md §11 + 05-guidelines.md):
  test_inbox_send_retract_audit_log.py — end-to-end flow verifying:
    1. SendMessageService persists message + action receipt in DB (ai sender)
    2. Action receipt created with expires_at = sent_at + 5min
    3. RetractMessageService marks message retracted within the 5min window
    4. Audit log row written sync for both send + retract operations
    5. MessageRetracted domain event emitted via event_bus

HIPAA-lite (hipaa-lite.md § Regla cardinal):
  - PHI dual filter: tenant_id + clinic_id on all queries
  - Audit log row mandatory pre-response (sync write)
  - Cross-tenant query: tenant_A + clinic_B → 404 (no leak)
  - No PHI in structlog traces

Postgres dependency: @pytest.mark.integration (auto-skip when Postgres down).
Service-level mocks (audit_writer, event_bus, channel_adapters, idempotency_store)
are used so the tests focus on the DB layer contracts, not infra dependencies.

downstream-regression-na: brand-local vitalia inbox integration test
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Fixture helpers — minimal repo + service wiring
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
LEAD_ID = uuid4()
USER_ID = uuid4()


def _make_mock_audit_writer() -> AsyncMock:
    """Async audit writer mock that captures write calls."""
    writer = AsyncMock()
    writer.write = AsyncMock(return_value=None)
    return writer


def _make_mock_event_bus() -> AsyncMock:
    """Async event bus mock that captures publish calls."""
    bus = AsyncMock()
    bus.publish = AsyncMock(return_value=None)
    return bus


def _make_noop_channel_adapters() -> dict[str, Any]:
    """Channel adapters map with a no-op WhatsApp adapter."""
    adapter = AsyncMock()
    result = MagicMock()
    result.succeeded = True
    adapter.retract_message_id = AsyncMock(return_value=result)
    return {"whatsapp": adapter}


# ---------------------------------------------------------------------------
# Test: ConversationRepository + MessageRepository persist correctly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_conversation_and_message_insert_dual_filter(db_session: AsyncSession) -> None:
    """Verify ConversationModel + MessageModel persist with dual-filter isolation.

    Tests that inserted rows are retrievable ONLY with matching tenant_id + clinic_id.
    Cross-tenant query (wrong tenant) returns no rows.

    HIPAA-lite dual filter enforcement at the repository layer.
    """
    from sqlalchemy import select

    from src.modules.vitalia.crm.infrastructure.persistence.models.conversation_model import (
        ConversationModel,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.models.message_model import (
        MessageModel,
    )

    conv_id = uuid4()
    msg_id = uuid4()
    now = datetime.now(UTC)

    # Insert conversation
    conv = ConversationModel(
        id=conv_id,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        lead_id=LEAD_ID,
        channel="whatsapp",
        status="active",
        handler_mode="ai",
        help_needed=False,
        help_needed_reason=None,
        pause_until=None,
        last_message_at=now,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )
    db_session.add(conv)
    await db_session.flush()

    # Insert message (ai sender)
    msg = MessageModel(
        id=msg_id,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=conv_id,
        channel="whatsapp",
        external_message_id=None,
        sender_type="agent_ai",
        sender_user_id=USER_ID,
        body_text="Hola, ¿cómo te sientes después de tu cita?",
        media_kind=None,
        media_url=None,
        media_duration_s=None,
        media_phi_flagged=False,
        transcription_text=None,
        transcription_confidence=None,
        retracted_at=None,
        retracted_by_user_id=None,
        retracted_reason=None,
        retract_succeeded=None,
        handler_mode="ai",
        cache_hit_rate=None,
        llm_cost_usd=None,
        sent_at=now,
        delivered_at=None,
        read_at=None,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(msg)
    await db_session.flush()

    # Query with CORRECT tenant + clinic → should find message
    stmt_correct = (
        select(MessageModel)
        .where(MessageModel.id == msg_id)
        .where(MessageModel.tenant_id == TENANT_ID)
        .where(MessageModel.clinic_id == CLINIC_ID)
        .where(MessageModel.deleted_at.is_(None))
    )
    result_correct = await db_session.execute(stmt_correct)
    found = result_correct.scalar_one_or_none()
    assert found is not None, "Message should be found with correct tenant+clinic"
    assert found.id == msg_id
    assert found.sender_type == "agent_ai"

    # Cross-tenant query — wrong tenant_id → must return None (HIPAA-lite dual filter)
    wrong_tenant = uuid4()
    stmt_cross_tenant = (
        select(MessageModel)
        .where(MessageModel.id == msg_id)
        .where(MessageModel.tenant_id == wrong_tenant)
        .where(MessageModel.clinic_id == CLINIC_ID)
        .where(MessageModel.deleted_at.is_(None))
    )
    result_cross = await db_session.execute(stmt_cross_tenant)
    assert result_cross.scalar_one_or_none() is None, "Cross-tenant query MUST return no rows (HIPAA-lite isolation)"

    # Cross-clinic query — wrong clinic_id → must return None
    wrong_clinic = uuid4()
    stmt_cross_clinic = (
        select(MessageModel)
        .where(MessageModel.id == msg_id)
        .where(MessageModel.tenant_id == TENANT_ID)
        .where(MessageModel.clinic_id == wrong_clinic)
        .where(MessageModel.deleted_at.is_(None))
    )
    result_cross_clinic = await db_session.execute(stmt_cross_clinic)
    assert result_cross_clinic.scalar_one_or_none() is None, (
        "Cross-clinic query MUST return no rows (HIPAA-lite clinic_id filter)"
    )


# ---------------------------------------------------------------------------
# Test: ActionReceiptRepository — get_active_for_message + mark_retracted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_action_receipt_lifecycle(db_session: AsyncSession) -> None:
    """Verify ActionReceiptModel state machine: ACTIVE → RETRACTED_SUCCESS.

    Tests:
    1. Fresh receipt with expires_at=now+5min is found by get_active_for_message
    2. mark_retracted updates retracted_at + retract_succeeded
    3. Second get_active_for_message returns None (already retracted)
    4. Dual filter: wrong clinic → receipt not found
    """
    from sqlalchemy import select

    from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
        ActionReceiptRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.models.action_receipt_model import (
        ActionReceiptModel,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.models.conversation_model import (
        ConversationModel,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.models.message_model import (
        MessageModel,
    )

    conv_id = uuid4()
    msg_id = uuid4()
    receipt_id = uuid4()
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=5)

    # Insert prereqs: conversation + message
    conv = ConversationModel(
        id=conv_id,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        lead_id=LEAD_ID,
        channel="whatsapp",
        status="active",
        handler_mode="ai",
        help_needed=False,
        help_needed_reason=None,
        pause_until=None,
        last_message_at=now,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )
    db_session.add(conv)
    msg = MessageModel(
        id=msg_id,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=conv_id,
        channel="whatsapp",
        external_message_id=None,
        sender_type="agent_ai",
        sender_user_id=USER_ID,
        body_text="Mensaje de seguimiento",
        media_kind=None,
        media_url=None,
        media_duration_s=None,
        media_phi_flagged=False,
        transcription_text=None,
        transcription_confidence=None,
        retracted_at=None,
        retracted_by_user_id=None,
        retracted_reason=None,
        retract_succeeded=None,
        handler_mode="ai",
        cache_hit_rate=None,
        llm_cost_usd=None,
        sent_at=now,
        delivered_at=None,
        read_at=None,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(msg)

    # Insert action receipt (ACTIVE state)
    receipt = ActionReceiptModel(
        id=receipt_id,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        message_id=msg_id,
        conversation_id=conv_id,
        expires_at=expires_at,
        retracted_at=None,
        retract_succeeded=None,
        retract_reason=None,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )
    db_session.add(receipt)
    await db_session.flush()

    # Verify: get_active_for_message returns the receipt (within 5min window)
    receipt_repo = ActionReceiptRepository(session=db_session)
    found = await receipt_repo.get_active_for_message(
        message_id=msg_id,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
    )
    assert found is not None, "Active receipt must be found within 5min window"
    assert found.id == receipt_id
    assert found.retracted_at is None
    assert found.expires_at > datetime.now(UTC)

    # Dual filter: wrong clinic → receipt not found
    wrong_clinic = uuid4()
    not_found = await receipt_repo.get_active_for_message(
        message_id=msg_id,
        tenant_id=TENANT_ID,
        clinic_id=wrong_clinic,
    )
    assert not_found is None, "Wrong clinic_id must not find receipt (dual filter)"

    # Mark retracted (ACTIVE → RETRACTED_SUCCESS)
    success = await receipt_repo.mark_retracted(
        receipt_id=receipt_id,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        retract_succeeded=True,
        retract_reason="user_undo",
    )
    assert success is True, "mark_retracted should update 1 row"
    await db_session.flush()

    # Verify: get_active_for_message now returns None (already retracted)
    after_retract = await receipt_repo.get_active_for_message(
        message_id=msg_id,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
    )
    assert after_retract is None, "Retracted receipt must no longer appear as active"

    # Verify retracted_at is set in DB
    stmt = select(ActionReceiptModel).where(ActionReceiptModel.id == receipt_id)
    result = await db_session.execute(stmt)
    persisted = result.scalar_one()
    assert persisted.retracted_at is not None, "retracted_at must be set after mark_retracted"
    assert persisted.retract_succeeded is True
    assert persisted.retract_reason == "user_undo"


# ---------------------------------------------------------------------------
# Test: SendMessageService — audit log write + event publish (mocked infra)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_service_audit_log_and_event(db_session: AsyncSession) -> None:
    """Verify SendMessageService calls audit_writer.write + event_bus.publish.

    Integration-level test: uses real DB for conversation, but mocks audit_writer
    and event_bus (they have no real implementations wired in test env).

    HIPAA-lite: audit_writer.write must be called with action='inbox.message.sent'.
    MessageSent event must be published via event_bus.publish.
    """
    from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
        ConversationRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
        MessageRepository,
    )
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        SendMessageService,
    )

    # Stub ActionReceiptRepository — create() not yet implemented; use AsyncMock
    mock_receipt_repo = AsyncMock()
    receipt_id = uuid4()
    mock_receipt = MagicMock()
    mock_receipt.id = receipt_id
    mock_receipt.expires_at = datetime.now(UTC) + timedelta(minutes=5)
    mock_receipt_repo.create = AsyncMock(return_value=mock_receipt)

    audit_writer = _make_mock_audit_writer()
    event_bus = _make_mock_event_bus()

    # Insert conversation in real DB
    conv_id = uuid4()
    now = datetime.now(UTC)
    from src.modules.vitalia.crm.infrastructure.persistence.models.conversation_model import (
        ConversationModel,
    )

    conv = ConversationModel(
        id=conv_id,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        lead_id=LEAD_ID,
        channel="whatsapp",
        status="active",
        handler_mode="ai",
        help_needed=False,
        help_needed_reason=None,
        pause_until=None,
        last_message_at=now,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )
    db_session.add(conv)
    await db_session.flush()

    conv_repo = ConversationRepository(session=db_session)
    msg_repo = MessageRepository(session=db_session)

    svc = SendMessageService(
        conv_repo=conv_repo,
        msg_repo=msg_repo,
        receipt_repo=mock_receipt_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        session=db_session,
        idempotency_store=None,
    )

    result = await svc.send(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=conv_id,
        user_id=USER_ID,
        body_text="Seguimiento post-tratamiento.",
    )

    # Verify message was persisted
    assert result.message_id is not None
    assert result.sender_type == "agent_ai"  # conv.handler_mode == 'ai'

    # HIPAA-lite: audit log must be written (sync)
    audit_writer.write.assert_called_once()
    call_kwargs = audit_writer.write.call_args.kwargs
    assert call_kwargs["tenant_id"] == TENANT_ID
    assert call_kwargs["clinic_id"] == CLINIC_ID
    assert call_kwargs["action"] == "inbox.message.sent"
    assert call_kwargs["resource_type"] == "inbox.message"

    # MessageSent event published
    event_bus.publish.assert_called_once()
    published_event = event_bus.publish.call_args.args[0]
    assert published_event.event_name == "message_sent"
    assert published_event.tenant_id == TENANT_ID
    assert published_event.clinic_id == CLINIC_ID


# ---------------------------------------------------------------------------
# Test: RetractMessageService — end-to-end with mock repos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retract_message_service_within_window_emits_event(db_session: AsyncSession) -> None:
    """Verify RetractMessageService within 5min emits MessageRetracted + audit log.

    Uses mock repos for msg_repo (mark_retracted not yet on MessageRepository)
    and receipt_repo (get_active_for_message via mock).

    Validates:
    1. RetractResult.retract_succeeded=True when channel adapter succeeds
    2. Audit log written with action='inbox.message.retracted'
    3. MessageRetracted event emitted with correct tenant + clinic context
    4. PatientRepliedConflictError NOT raised (no patient reply in mock)
    """
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        RetractMessageService,
    )

    conv_id = uuid4()
    msg_id = uuid4()
    receipt_id = uuid4()
    now = datetime.now(UTC)

    # Mock message with whatsapp channel + no patient reply
    mock_msg = MagicMock()
    mock_msg.id = msg_id
    mock_msg.channel = "whatsapp"
    mock_msg.external_message_id = "wamid.abc123"
    mock_msg.tenant_id = TENANT_ID
    mock_msg.clinic_id = CLINIC_ID

    # Mock repos
    mock_msg_repo = AsyncMock()
    mock_msg_repo.get_by_id = AsyncMock(return_value=mock_msg)
    mock_msg_repo.find_patient_reply_after = AsyncMock(return_value=None)
    mock_msg_repo.mark_retracted = AsyncMock(return_value=True)

    mock_receipt = MagicMock()
    mock_receipt.id = receipt_id
    mock_receipt.expires_at = now + timedelta(minutes=5)  # within window
    mock_receipt_repo = AsyncMock()
    mock_receipt_repo.get_active_for_message = AsyncMock(return_value=mock_receipt)

    mock_conv_repo = AsyncMock()

    audit_writer = _make_mock_audit_writer()
    event_bus = _make_mock_event_bus()
    channel_adapters = _make_noop_channel_adapters()

    svc = RetractMessageService(
        msg_repo=mock_msg_repo,
        receipt_repo=mock_receipt_repo,
        conv_repo=mock_conv_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        channel_adapters=channel_adapters,
        session=db_session,
    )

    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        RetractResult,
    )

    result = await svc.retract(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=conv_id,
        message_id=msg_id,
        retracted_by_user_id=USER_ID,
        reason="user_undo",
    )

    # Verify retraction result
    assert isinstance(result, RetractResult)
    assert result.retract_succeeded is True
    assert result.message_id == msg_id
    assert result.retracted_at is not None
    assert result.retract_reason == "user_undo"

    # HIPAA-lite: audit log written sync pre-response
    audit_writer.write.assert_called_once()
    audit_kwargs = audit_writer.write.call_args.kwargs
    assert audit_kwargs["action"] == "inbox.message.retracted"
    assert audit_kwargs["tenant_id"] == TENANT_ID
    assert audit_kwargs["clinic_id"] == CLINIC_ID

    # MessageRetracted event published
    event_bus.publish.assert_called_once()
    event = event_bus.publish.call_args.args[0]
    assert event.event_name == "message_retracted"
    assert event.tenant_id == TENANT_ID
    assert event.clinic_id == CLINIC_ID
    assert event.retract_succeeded is True


@pytest.mark.asyncio
async def test_retract_message_service_expired_receipt_raises(db_session: AsyncSession) -> None:
    """RetractMessageService raises ActionReceiptExpiredError when 5min window elapsed.

    Boundary condition: expires_at = 1 second ago → expired → 410 Gone.
    Audit log must NOT be written (error path, no PHI mutation).
    """
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        ActionReceiptExpiredError,
        RetractMessageService,
    )

    msg_id = uuid4()
    now = datetime.now(UTC)

    mock_msg = MagicMock()
    mock_msg.id = msg_id
    mock_msg.channel = "whatsapp"
    mock_msg.external_message_id = "wamid.expired"

    # Expired receipt (1 second ago)
    mock_receipt = MagicMock()
    mock_receipt.id = uuid4()
    mock_receipt.expires_at = now - timedelta(seconds=1)

    mock_msg_repo = AsyncMock()
    mock_msg_repo.get_by_id = AsyncMock(return_value=mock_msg)

    mock_receipt_repo = AsyncMock()
    mock_receipt_repo.get_active_for_message = AsyncMock(return_value=mock_receipt)

    audit_writer = _make_mock_audit_writer()
    event_bus = _make_mock_event_bus()

    svc = RetractMessageService(
        msg_repo=mock_msg_repo,
        receipt_repo=mock_receipt_repo,
        conv_repo=AsyncMock(),
        audit_writer=audit_writer,
        event_bus=event_bus,
        channel_adapters={},
        session=db_session,
    )

    with pytest.raises(ActionReceiptExpiredError) as exc_info:
        await svc.retract(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=uuid4(),
            message_id=msg_id,
            retracted_by_user_id=USER_ID,
            reason="user_undo",
        )

    assert exc_info.value.message_id == msg_id
    assert exc_info.value.expired_at == mock_receipt.expires_at

    # Audit log must NOT be written for expired window (no PHI mutation occurred)
    audit_writer.write.assert_not_called()
    event_bus.publish.assert_not_called()


@pytest.mark.asyncio
async def test_retract_message_service_patient_replied_conflict(db_session: AsyncSession) -> None:
    """RetractMessageService raises PatientRepliedConflictError when patient replied after AI msg.

    SC-01 conflict guard: if patient sent a reply after the AI message,
    retraction is blocked (409 Conflict). No audit log for blocked retraction.
    """
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        PatientRepliedConflictError,
        RetractMessageService,
    )

    msg_id = uuid4()
    now = datetime.now(UTC)

    mock_msg = MagicMock()
    mock_msg.id = msg_id
    mock_msg.channel = "whatsapp"
    mock_msg.external_message_id = "wamid.patient_replied"

    mock_receipt = MagicMock()
    mock_receipt.id = uuid4()
    mock_receipt.expires_at = now + timedelta(minutes=4)  # within window

    # Patient reply exists (non-None return from find_patient_reply_after)
    mock_patient_reply = MagicMock()
    mock_patient_reply.id = uuid4()

    mock_msg_repo = AsyncMock()
    mock_msg_repo.get_by_id = AsyncMock(return_value=mock_msg)
    mock_msg_repo.find_patient_reply_after = AsyncMock(return_value=mock_patient_reply)

    mock_receipt_repo = AsyncMock()
    mock_receipt_repo.get_active_for_message = AsyncMock(return_value=mock_receipt)

    audit_writer = _make_mock_audit_writer()
    event_bus = _make_mock_event_bus()

    svc = RetractMessageService(
        msg_repo=mock_msg_repo,
        receipt_repo=mock_receipt_repo,
        conv_repo=AsyncMock(),
        audit_writer=audit_writer,
        event_bus=event_bus,
        channel_adapters={},
        session=db_session,
    )

    with pytest.raises(PatientRepliedConflictError) as exc_info:
        await svc.retract(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=uuid4(),
            message_id=msg_id,
            retracted_by_user_id=USER_ID,
            reason="user_undo",
        )

    assert exc_info.value.message_id == msg_id

    # No audit or event for blocked retraction (patient already replied)
    audit_writer.write.assert_not_called()
    event_bus.publish.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Audit log table — row persists (requires DB schema)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_log_row_created_for_send(db_session: AsyncSession) -> None:
    """Verify audit log row written via raw SQL insert (smoke test for table existence).

    Per hipaa-lite.md: vitalia_audit_log table MUST exist and accept writes.
    Tests that INSERT INTO vitalia_audit_log succeeds with tenant_id + clinic_id + action.
    """
    import json

    from sqlalchemy import text

    tenant_id = uuid4()
    clinic_id = uuid4()
    user_id = uuid4()
    resource_id = uuid4()

    payload_bytes = json.dumps({"conversation_id": str(uuid4()), "test": True}).encode("utf-8")

    await db_session.execute(
        text("""
            INSERT INTO vitalia_audit_log
                (id, tenant_id, clinic_id, user_id, action, resource_type,
                 resource_id, from_ip, user_agent, payload_redacted, occurred_at)
            VALUES
                (gen_random_uuid(),
                 :tenant_id::uuid, :clinic_id::uuid, :user_id::uuid,
                 :action, :resource_type, :resource_id::uuid,
                 :from_ip, :user_agent, :payload, NOW())
        """),
        {
            "tenant_id": str(tenant_id),
            "clinic_id": str(clinic_id),
            "user_id": str(user_id),
            "action": "inbox.message.sent",
            "resource_type": "inbox.message",
            "resource_id": str(resource_id),
            "from_ip": None,
            "user_agent": "pytest/integration",
            "payload": payload_bytes,
        },
    )
    await db_session.flush()

    # Verify row exists for our tenant + action
    result = await db_session.execute(
        text("""
            SELECT action, resource_type FROM vitalia_audit_log
            WHERE tenant_id = :tenant_id::uuid
              AND clinic_id = :clinic_id::uuid
              AND action = 'inbox.message.sent'
            LIMIT 1
        """),
        {"tenant_id": str(tenant_id), "clinic_id": str(clinic_id)},
    )
    row = result.fetchone()
    assert row is not None, "Audit log row must be findable by tenant+clinic+action"
    assert row[0] == "inbox.message.sent"
    assert row[1] == "inbox.message"
