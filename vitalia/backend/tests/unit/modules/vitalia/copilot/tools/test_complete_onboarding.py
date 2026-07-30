"""Unit tests — complete_onboarding LangChain @tool."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.vitalia.copilot.tools.complete_onboarding import (
    CompleteOnboardingInput,
    complete_onboarding,
    set_complete_onboarding_service_factory,
)

co_mod = sys.modules["src.modules.vitalia.copilot.tools.complete_onboarding"]

TENANT_ID = uuid4()
DRAFT_ID = uuid4()
USER_ID = uuid4()


@pytest.fixture(autouse=True)
def _reset_factory() -> None:
    co_mod._service_factory = None
    yield
    co_mod._service_factory = None


class _FakeResp:
    def __init__(self, activated: bool = True, redirect: str = "/inbox") -> None:
        self.tenant_activated = activated
        self.redirect_url = redirect


class TestCompleteOnboardingInputSchema:
    def test_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            CompleteOnboardingInput(tenant_id=TENANT_ID, user_id=USER_ID)  # type: ignore[call-arg]

    def test_accepts_uuids(self) -> None:
        payload = CompleteOnboardingInput(draft_id=DRAFT_ID, tenant_id=TENANT_ID, user_id=USER_ID)
        assert payload.draft_id == DRAFT_ID
        assert payload.tenant_id == TENANT_ID
        assert payload.user_id == USER_ID


class TestCompleteOnboardingToolMetadata:
    def test_tool_name_is_canonical(self) -> None:
        assert complete_onboarding.name == "complete_onboarding"

    def test_tool_args_schema(self) -> None:
        assert complete_onboarding.args_schema is CompleteOnboardingInput


class TestCompleteOnboardingBehavior:
    @pytest.mark.asyncio
    async def test_calls_service_complete_with_kwargs(self) -> None:
        mock_service = AsyncMock()
        mock_service.complete = AsyncMock(return_value=_FakeResp())
        set_complete_onboarding_service_factory(lambda: mock_service)

        await complete_onboarding.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "user_id": USER_ID,
            }
        )

        mock_service.complete.assert_awaited_once_with(
            draft_id=DRAFT_ID,
            tenant_id=TENANT_ID,
            user_id=USER_ID,
        )

    @pytest.mark.asyncio
    async def test_returns_activation_summary(self) -> None:
        mock_service = AsyncMock()
        mock_service.complete = AsyncMock(return_value=_FakeResp(activated=True))
        set_complete_onboarding_service_factory(lambda: mock_service)

        result = await complete_onboarding.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "user_id": USER_ID,
            }
        )

        assert "activated" in result
        assert "/inbox" in result

    @pytest.mark.asyncio
    async def test_returns_pending_when_not_activated(self) -> None:
        mock_service = AsyncMock()
        mock_service.complete = AsyncMock(return_value=_FakeResp(activated=False))
        set_complete_onboarding_service_factory(lambda: mock_service)

        result = await complete_onboarding.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "user_id": USER_ID,
            }
        )

        assert "pending" in result

    @pytest.mark.asyncio
    async def test_draft_not_found_surfaces_as_error_string(self) -> None:
        from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
            DraftNotFoundError,
        )

        mock_service = AsyncMock()
        mock_service.complete = AsyncMock(
            side_effect=DraftNotFoundError(DRAFT_ID, TENANT_ID),
        )
        set_complete_onboarding_service_factory(lambda: mock_service)

        result = await complete_onboarding.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "user_id": USER_ID,
            }
        )

        assert "Error completing onboarding" in result
        assert "DraftNotFoundError" in result

    @pytest.mark.asyncio
    async def test_runtime_error_surfaces_as_error_string(self) -> None:
        mock_service = AsyncMock()
        mock_service.complete = AsyncMock(side_effect=RuntimeError("brand commit fail"))
        set_complete_onboarding_service_factory(lambda: mock_service)

        result = await complete_onboarding.ainvoke(
            {
                "draft_id": DRAFT_ID,
                "tenant_id": TENANT_ID,
                "user_id": USER_ID,
            }
        )

        assert "Error" in result
        assert "RuntimeError" in result
