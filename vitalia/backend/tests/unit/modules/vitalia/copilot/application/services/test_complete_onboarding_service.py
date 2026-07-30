"""RED tests — CompleteOnboardingService.

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- complete() verifies draft exists for tenant (raises DraftNotFoundError if missing)
- complete() calls personality adapter to compile full profile
- complete() calls brand_studio_port to commit brand profile
- complete() calls tenant_port to mark tenant as onboarded
- complete() writes audit_log SYNC (before return)
- complete() publishes TenantOnboardedEvent via outbox/event_bus
- complete() returns CompleteResponse with tenant_activated=True
- tenant_id always passed for isolation
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
USER_ID = uuid4()
DRAFT_ID = uuid4()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_confirmed_draft() -> "object":
    from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
    from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

    def _confirmed_slot(slot_id: str, value: str) -> WizardSlot:
        return WizardSlot(
            slot_id=slot_id,
            value=value,
            confidence=0.95,
            confirmed_at=_utc_now(),
            source="user_text",
        )

    return OnboardingDraft(
        id=DRAFT_ID,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        clinic_id=None,
        mode="libre",
        slots_required={
            "tenant.name": _confirmed_slot("tenant.name", "Clínica Test"),
            "tenant.vertical": _confirmed_slot("tenant.vertical", "dental"),
            "tenant.location": _confirmed_slot("tenant.location", "Lima"),
        },
        slots_optional={},
        bonus_extracted={},
        consent_voice_activation=False,
        created_at=_utc_now(),
        updated_at=_utc_now(),
        deleted_at=None,
        completed_at=None,
    )


class TestCompleteOnboardingServiceBasic:
    """Tests for CompleteOnboardingService.complete() happy path."""

    @pytest.mark.asyncio
    async def test_complete_raises_if_draft_not_found(self) -> None:
        """complete() raises DraftNotFoundError when draft doesn't exist."""
        from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
            CompleteOnboardingService,
            DraftNotFoundError,
        )

        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=None)

        service = CompleteOnboardingService(
            draft_repo=mock_draft_repo,
            personality_adapter=AsyncMock(),
            brand_studio_port=AsyncMock(),
            tenant_port=AsyncMock(),
            audit_log_repo=AsyncMock(),
            event_bus=AsyncMock(),
        )

        with pytest.raises(DraftNotFoundError):
            await service.complete(draft_id=DRAFT_ID, tenant_id=TENANT_ID, user_id=USER_ID)

    @pytest.mark.asyncio
    async def test_complete_calls_personality_compile(self) -> None:
        """complete() calls personality_adapter.compile_full() with confirmed slots."""
        from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
            CompleteOnboardingService,
        )

        draft = _make_confirmed_draft()
        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=draft)
        mock_draft_repo.save = AsyncMock(side_effect=lambda d: d)

        mock_personality = AsyncMock()
        mock_personality.compile_full = AsyncMock(return_value=MagicMock(id=uuid4()))
        mock_brand_studio = AsyncMock()
        mock_brand_studio.commit_brand = AsyncMock()
        mock_tenant_port = AsyncMock()
        mock_tenant_port.mark_onboarded = AsyncMock()
        mock_audit = AsyncMock()
        mock_audit.write = AsyncMock()
        mock_event_bus = AsyncMock()
        mock_event_bus.publish = AsyncMock()

        service = CompleteOnboardingService(
            draft_repo=mock_draft_repo,
            personality_adapter=mock_personality,
            brand_studio_port=mock_brand_studio,
            tenant_port=mock_tenant_port,
            audit_log_repo=mock_audit,
            event_bus=mock_event_bus,
        )
        await service.complete(draft_id=DRAFT_ID, tenant_id=TENANT_ID, user_id=USER_ID)

        mock_personality.compile_full.assert_called_once()
        call_kwargs = mock_personality.compile_full.call_args.kwargs
        assert call_kwargs.get("tenant_id") == TENANT_ID

    @pytest.mark.asyncio
    async def test_complete_calls_tenant_port_mark_onboarded(self) -> None:
        """complete() marks tenant as onboarded via tenant_port."""
        from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
            CompleteOnboardingService,
        )

        draft = _make_confirmed_draft()
        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=draft)
        mock_draft_repo.save = AsyncMock(side_effect=lambda d: d)

        mock_personality = AsyncMock()
        mock_personality.compile_full = AsyncMock(return_value=MagicMock(id=uuid4()))
        mock_brand_studio = AsyncMock()
        mock_tenant_port = AsyncMock()
        mock_tenant_port.mark_onboarded = AsyncMock()
        mock_audit = AsyncMock()
        mock_audit.write = AsyncMock()
        mock_event_bus = AsyncMock()
        mock_event_bus.publish = AsyncMock()

        service = CompleteOnboardingService(
            draft_repo=mock_draft_repo,
            personality_adapter=mock_personality,
            brand_studio_port=mock_brand_studio,
            tenant_port=mock_tenant_port,
            audit_log_repo=mock_audit,
            event_bus=mock_event_bus,
        )
        await service.complete(draft_id=DRAFT_ID, tenant_id=TENANT_ID, user_id=USER_ID)

        mock_tenant_port.mark_onboarded.assert_called_once_with(tenant_id=TENANT_ID)

    @pytest.mark.asyncio
    async def test_complete_writes_audit_log_sync(self) -> None:
        """complete() writes audit_log synchronously before returning."""
        from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
            CompleteOnboardingService,
        )

        draft = _make_confirmed_draft()
        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=draft)
        mock_draft_repo.save = AsyncMock(side_effect=lambda d: d)

        mock_personality = AsyncMock()
        mock_personality.compile_full = AsyncMock(return_value=MagicMock(id=uuid4()))
        mock_brand_studio = AsyncMock()
        mock_tenant_port = AsyncMock()
        mock_tenant_port.mark_onboarded = AsyncMock()
        mock_audit = AsyncMock()
        mock_audit.write = AsyncMock()  # sync write
        mock_event_bus = AsyncMock()
        mock_event_bus.publish = AsyncMock()

        service = CompleteOnboardingService(
            draft_repo=mock_draft_repo,
            personality_adapter=mock_personality,
            brand_studio_port=mock_brand_studio,
            tenant_port=mock_tenant_port,
            audit_log_repo=mock_audit,
            event_bus=mock_event_bus,
        )
        await service.complete(draft_id=DRAFT_ID, tenant_id=TENANT_ID, user_id=USER_ID)

        # audit_log.write() must have been awaited
        mock_audit.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_publishes_tenant_onboarded_event(self) -> None:
        """complete() publishes TenantOnboardedEvent via event_bus."""
        from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
            CompleteOnboardingService,
        )

        draft = _make_confirmed_draft()
        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=draft)
        mock_draft_repo.save = AsyncMock(side_effect=lambda d: d)

        mock_personality = AsyncMock()
        mock_personality.compile_full = AsyncMock(return_value=MagicMock(id=uuid4()))
        mock_brand_studio = AsyncMock()
        mock_tenant_port = AsyncMock()
        mock_tenant_port.mark_onboarded = AsyncMock()
        mock_audit = AsyncMock()
        mock_audit.write = AsyncMock()
        mock_event_bus = AsyncMock()
        mock_event_bus.publish = AsyncMock()

        service = CompleteOnboardingService(
            draft_repo=mock_draft_repo,
            personality_adapter=mock_personality,
            brand_studio_port=mock_brand_studio,
            tenant_port=mock_tenant_port,
            audit_log_repo=mock_audit,
            event_bus=mock_event_bus,
        )
        await service.complete(draft_id=DRAFT_ID, tenant_id=TENANT_ID, user_id=USER_ID)

        mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_returns_tenant_activated_true(self) -> None:
        """complete() returns CompleteResponse with tenant_activated=True."""
        from src.modules.vitalia.copilot.application.services.complete_onboarding_service import (
            CompleteOnboardingService,
        )

        draft = _make_confirmed_draft()
        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=draft)
        mock_draft_repo.save = AsyncMock(side_effect=lambda d: d)

        mock_personality = AsyncMock()
        mock_personality.compile_full = AsyncMock(return_value=MagicMock(id=uuid4()))
        mock_brand_studio = AsyncMock()
        mock_tenant_port = AsyncMock()
        mock_tenant_port.mark_onboarded = AsyncMock()
        mock_audit = AsyncMock()
        mock_audit.write = AsyncMock()
        mock_event_bus = AsyncMock()
        mock_event_bus.publish = AsyncMock()

        service = CompleteOnboardingService(
            draft_repo=mock_draft_repo,
            personality_adapter=mock_personality,
            brand_studio_port=mock_brand_studio,
            tenant_port=mock_tenant_port,
            audit_log_repo=mock_audit,
            event_bus=mock_event_bus,
        )
        result = await service.complete(draft_id=DRAFT_ID, tenant_id=TENANT_ID, user_id=USER_ID)

        assert result.tenant_activated is True
        assert result.redirect_url is not None
