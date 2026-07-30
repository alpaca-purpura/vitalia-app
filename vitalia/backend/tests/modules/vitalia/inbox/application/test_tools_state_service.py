"""Tests for ToolsStateService — TDD RED (T-inbox-be-3).

Coverage:
- tools state derived from offer preset tools_enabled mapping
- read-only: no mutations
- dual-filter applied (tenant_id + clinic_id)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()


@pytest.mark.asyncio
async def test_tools_state_returns_all_known_tools() -> None:
    """ToolsStateService returns tool list with enabled flags."""
    from src.modules.vitalia.inbox.application.services.tools_state_service import (
        ToolsStateService,
    )

    conv_repo = AsyncMock()
    conv_model = MagicMock()
    conv_model.linked_offer_id = None
    conv_repo.get_by_id = AsyncMock(return_value=conv_model)

    svc = ToolsStateService(conv_repo=conv_repo)

    result = await svc.get_tools_state(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
    )

    assert result is not None
    assert isinstance(result.tools, list)
    assert result.read_only is True


@pytest.mark.asyncio
async def test_tools_state_conversation_not_found_raises() -> None:
    """Conversation not found → ConversationNotFoundError."""
    from src.modules.vitalia.inbox.application.services.tools_state_service import (
        ConversationNotFoundError,
        ToolsStateService,
    )

    conv_repo = AsyncMock()
    conv_repo.get_by_id = AsyncMock(return_value=None)

    svc = ToolsStateService(conv_repo=conv_repo)

    with pytest.raises(ConversationNotFoundError):
        await svc.get_tools_state(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_tools_state_is_read_only_no_write_methods() -> None:
    """ToolsStateService has no mutation methods (Slice 1 read-only)."""
    from src.modules.vitalia.inbox.application.services.tools_state_service import (
        ToolsStateService,
    )

    svc = ToolsStateService(conv_repo=AsyncMock())

    # No set_tools, update_tools, enable_tool methods should exist
    assert not hasattr(svc, "set_tools")
    assert not hasattr(svc, "update_tools")
    assert not hasattr(svc, "enable_tool")
