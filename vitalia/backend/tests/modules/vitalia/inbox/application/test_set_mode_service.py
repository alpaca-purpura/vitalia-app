"""Tests for SetModeService — TDD RED (T-inbox-be-3).

SC-03 OCC coverage:
- Happy path: mode changed, ModeChanged event emitted
- OCC conflict (stale expected_updated_at) → raises OCCConflictError (→ 409)
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()
USER_ID = uuid4()


def _make_conversation_model(handler_mode: str = "ai") -> MagicMock:
    conv = MagicMock()
    conv.id = CONV_ID
    conv.tenant_id = TENANT_ID
    conv.clinic_id = CLINIC_ID
    conv.handler_mode = handler_mode
    conv.proposal_required = False
    conv.status = "active"
    conv.pause_until = None
    conv.help_needed = False
    conv.updated_at = datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC)
    conv.deleted_at = None
    return conv


@pytest.mark.asyncio
async def test_set_mode_happy_path_emits_mode_changed_event() -> None:
    """SC-03: mode ai → human, OCC match → ModeChanged event emitted."""
    from src.modules.vitalia.crm.domain.events import ModeChanged
    from src.modules.vitalia.inbox.application.services.set_mode_service import (
        SetModeService,
    )

    conv_repo = AsyncMock()
    audit_writer = AsyncMock()
    session = AsyncMock()

    published_events: list[object] = []

    async def capture(event: object, **kwargs: object) -> None:
        published_events.append(event)

    event_bus = AsyncMock()
    event_bus.publish = AsyncMock(side_effect=capture)

    conv_model = _make_conversation_model(handler_mode="ai")
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)

    updated_conv = _make_conversation_model(handler_mode="human")
    updated_conv.updated_at = datetime(2026, 5, 20, 12, 1, 0, tzinfo=UTC)
    conv_repo.update_handler_mode = AsyncMock(return_value=True)
    conv_repo.get_by_id = AsyncMock(return_value=updated_conv)

    svc = SetModeService(
        conv_repo=conv_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        session=session,
    )

    result = await svc.set_mode(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        new_mode="human",
        proposal_required=False,
        expected_updated_at=datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC),
        changed_by_user_id=USER_ID,
    )

    assert result is not None
    assert any(isinstance(e, ModeChanged) for e in published_events)
    audit_writer.write.assert_called_once()


@pytest.mark.asyncio
async def test_set_mode_occ_conflict_raises_error() -> None:
    """SC-03: stale expected_updated_at → OCCConflictError (→ 409)."""
    from src.modules.vitalia.inbox.application.services.set_mode_service import (
        OCCConflictError,
        SetModeService,
    )

    conv_repo = AsyncMock()

    conv_model = _make_conversation_model(handler_mode="ai")
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)
    # OCC update returns False (row was updated by another request)
    conv_repo.update_handler_mode = AsyncMock(return_value=False)

    svc = SetModeService(
        conv_repo=conv_repo,
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        session=AsyncMock(),
    )

    with pytest.raises(OCCConflictError):
        await svc.set_mode(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            new_mode="human",
            proposal_required=False,
            expected_updated_at=datetime(2026, 5, 19, 0, 0, 0, tzinfo=UTC),  # stale
            changed_by_user_id=USER_ID,
        )


@pytest.mark.asyncio
async def test_set_mode_conversation_not_found() -> None:
    """Conversation not found → ConversationNotFoundError."""
    from src.modules.vitalia.inbox.application.services.set_mode_service import (
        ConversationNotFoundError,
        SetModeService,
    )

    conv_repo = AsyncMock()
    conv_repo.get_by_id = AsyncMock(return_value=None)

    svc = SetModeService(
        conv_repo=conv_repo,
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        session=AsyncMock(),
    )

    with pytest.raises(ConversationNotFoundError):
        await svc.set_mode(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=uuid4(),
            new_mode="human",
            proposal_required=False,
            expected_updated_at=datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC),
            changed_by_user_id=USER_ID,
        )
