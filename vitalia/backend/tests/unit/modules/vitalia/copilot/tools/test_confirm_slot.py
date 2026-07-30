"""Unit tests — confirm_slot LangChain @tool.

Tests verify:
  - args_schema validates slot_id (1-128 chars), source (Literal)
  - tool name is canonical
  - tool calls service.update_slot(...) with WizardSlot(confidence=1.0, confirmed_at=now)
  - source defaults to 'user_text', accepts 'user_correction'
  - error path returns "Error confirming ..." string
  - tenant_id flows through
"""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.vitalia.copilot.tools.confirm_slot import (
    ConfirmSlotInput,
    confirm_slot,
    set_confirm_slot_service_factory,
)

cs_mod = sys.modules["src.modules.vitalia.copilot.tools.confirm_slot"]

TENANT_ID = uuid4()
DRAFT_ID = uuid4()


@pytest.fixture(autouse=True)
def _reset_factory() -> None:
    cs_mod._service_factory = None
    yield
    cs_mod._service_factory = None


class TestConfirmSlotInputSchema:
    def test_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            ConfirmSlotInput(tenant_id=TENANT_ID, slot_id="tenant.name", value="X")  # type: ignore[call-arg]

    def test_slot_id_min_length(self) -> None:
        with pytest.raises(ValidationError):
            ConfirmSlotInput(draft_id=DRAFT_ID, tenant_id=TENANT_ID, slot_id="", value="X")

    def test_slot_id_max_length(self) -> None:
        with pytest.raises(ValidationError):
            ConfirmSlotInput(
                draft_id=DRAFT_ID,
                tenant_id=TENANT_ID,
                slot_id="x" * 129,
                value="X",
            )

    def test_source_defaults_user_text(self) -> None:
        payload = ConfirmSlotInput(draft_id=DRAFT_ID, tenant_id=TENANT_ID, slot_id="tenant.name", value="X")
        assert payload.source == "user_text"

    def test_source_accepts_user_correction(self) -> None:
        payload = ConfirmSlotInput(
            draft_id=DRAFT_ID,
            tenant_id=TENANT_ID,
            slot_id="tenant.name",
            value="X",
            source="user_correction",
        )
        assert payload.source == "user_correction"

    def test_source_rejects_invalid(self) -> None:
        with pytest.raises(ValidationError):
            ConfirmSlotInput(
                draft_id=DRAFT_ID,
                tenant_id=TENANT_ID,
                slot_id="tenant.name",
                value="X",
                source="extracted",  # type: ignore[arg-type]
            )

    def test_value_accepts_dict(self) -> None:
        payload = ConfirmSlotInput(
            draft_id=DRAFT_ID,
            tenant_id=TENANT_ID,
            slot_id="tenant.compound",
            value={"a": 1, "b": "hello"},
        )
        assert payload.value == {"a": 1, "b": "hello"}

    def test_value_accepts_none(self) -> None:
        payload = ConfirmSlotInput(draft_id=DRAFT_ID, tenant_id=TENANT_ID, slot_id="tenant.x", value=None)
        assert payload.value is None


class TestConfirmSlotToolMetadata:
    def test_tool_name_is_canonical(self) -> None:
        assert confirm_slot.name == "confirm_slot"

    def test_tool_args_schema(self) -> None:
        assert confirm_slot.args_schema is ConfirmSlotInput


class TestConfirmSlotBehavior:
    @pytest.mark.asyncio
    async def test_calls_service_with_wizard_slot_confidence_one(self) -> None:
        """update_slot receives a WizardSlot with confidence=1.0 + confirmed_at set."""
        mock_service = AsyncMock()
        mock_service.update_slot = AsyncMock()
        set_confirm_slot_service_factory(lambda: mock_service)

        await confirm_slot.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "slot_id": "tenant.name",
                "value": "Clinica X",
            }
        )

        kwargs = mock_service.update_slot.await_args.kwargs
        assert kwargs["draft_id"] == DRAFT_ID
        assert kwargs["tenant_id"] == TENANT_ID
        assert kwargs["slot_id"] == "tenant.name"
        new_slot = kwargs["new_slot"]
        assert new_slot.confidence == 1.0
        assert new_slot.confirmed_at is not None
        assert new_slot.source == "user_text"
        assert new_slot.value == "Clinica X"

    @pytest.mark.asyncio
    async def test_user_correction_source_propagates(self) -> None:
        mock_service = AsyncMock()
        mock_service.update_slot = AsyncMock()
        set_confirm_slot_service_factory(lambda: mock_service)

        await confirm_slot.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "slot_id": "tenant.name",
                "value": "Updated Name",
                "source": "user_correction",
            }
        )

        kwargs = mock_service.update_slot.await_args.kwargs
        assert kwargs["new_slot"].source == "user_correction"

    @pytest.mark.asyncio
    async def test_returns_summary_string(self) -> None:
        mock_service = AsyncMock()
        mock_service.update_slot = AsyncMock()
        set_confirm_slot_service_factory(lambda: mock_service)

        result = await confirm_slot.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "slot_id": "tenant.name",
                "value": "Clinica X",
            }
        )

        assert "tenant.name" in result
        assert "confirmed" in result
        assert str(DRAFT_ID) in result

    @pytest.mark.asyncio
    async def test_service_error_returns_string(self) -> None:
        mock_service = AsyncMock()
        mock_service.update_slot = AsyncMock(side_effect=RuntimeError("db down"))
        set_confirm_slot_service_factory(lambda: mock_service)

        result = await confirm_slot.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "slot_id": "tenant.name",
                "value": "X",
            }
        )

        assert "Error" in result
        assert "RuntimeError" in result

    @pytest.mark.asyncio
    async def test_tenant_id_flows_through(self) -> None:
        mock_service = AsyncMock()
        mock_service.update_slot = AsyncMock()
        set_confirm_slot_service_factory(lambda: mock_service)

        await confirm_slot.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "slot_id": "tenant.vertical",
                "value": "dental",
            }
        )

        kwargs = mock_service.update_slot.await_args.kwargs
        assert kwargs["tenant_id"] == TENANT_ID
