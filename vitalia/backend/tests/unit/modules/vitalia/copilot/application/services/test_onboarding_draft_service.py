"""RED tests — OnboardingDraftService (Valeria wizard CRUD operations).

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- create_draft() stores OnboardingDraft with tenant_id + default required slots
- get_draft() returns draft filtered by tenant_id (isolation enforced)
- update_draft() stores updated slot values
- get_draft() returns None when not found (no leak)
- No PHI in this service (wizard config data only)
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

TENANT_ID = uuid4()
USER_ID = uuid4()
DRAFT_ID = uuid4()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_slot(slot_id: str) -> "object":
    from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

    return WizardSlot(
        slot_id=slot_id,
        value=None,
        confidence=0.0,
        confirmed_at=None,
        source="extracted",
    )


def _make_draft(draft_id: UUID | None = None) -> "object":
    from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft

    return OnboardingDraft(
        id=draft_id or DRAFT_ID,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        clinic_id=None,
        mode="libre",
        slots_required={
            "tenant.name": _make_slot("tenant.name"),
            "tenant.vertical": _make_slot("tenant.vertical"),
            "tenant.location": _make_slot("tenant.location"),
        },
        slots_optional={
            "brand.tone_default": _make_slot("brand.tone_default"),
        },
        bonus_extracted={},
        consent_voice_activation=False,
        created_at=_utc_now(),
        updated_at=_utc_now(),
        deleted_at=None,
        completed_at=None,
    )


class TestOnboardingDraftServiceCreate:
    """Tests for OnboardingDraftService.create_draft()."""

    @pytest.mark.asyncio
    async def test_create_draft_stores_with_tenant_id(self) -> None:
        """create_draft() persists draft with correct tenant_id."""
        from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
            OnboardingDraftService,
        )

        mock_repo = AsyncMock()
        draft = _make_draft()
        mock_repo.save = AsyncMock(return_value=draft)

        service = OnboardingDraftService(draft_repo=mock_repo)
        await service.create_draft(
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            mode="libre",
            clinic_id=None,
        )

        mock_repo.save.assert_called_once()
        saved_draft = mock_repo.save.call_args[0][0]
        assert saved_draft.tenant_id == TENANT_ID
        assert saved_draft.user_id == USER_ID
        assert saved_draft.mode == "libre"
        assert saved_draft.deleted_at is None

    @pytest.mark.asyncio
    async def test_create_draft_duplicate_raises_domain_error(self) -> None:
        """A unique-violation on save → DraftAlreadyExistsError, not raw IntegrityError (HB-88)."""
        from sqlalchemy.exc import IntegrityError

        from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
            DraftAlreadyExistsError,
            OnboardingDraftService,
        )

        mock_repo = AsyncMock()
        mock_repo.save = AsyncMock(
            side_effect=IntegrityError("INSERT ...", params=None, orig=Exception("duplicate key"))
        )
        service = OnboardingDraftService(draft_repo=mock_repo)

        with pytest.raises(DraftAlreadyExistsError):
            await service.create_draft(tenant_id=TENANT_ID, user_id=USER_ID, mode="libre", clinic_id=None)

    @pytest.mark.asyncio
    async def test_create_draft_initializes_required_slots(self) -> None:
        """create_draft() initializes the required slot set."""
        from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
            OnboardingDraftService,
        )

        mock_repo = AsyncMock()

        async def capture_save(draft: "object") -> "object":
            return draft

        mock_repo.save = AsyncMock(side_effect=capture_save)

        service = OnboardingDraftService(draft_repo=mock_repo)
        result = await service.create_draft(
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            mode="libre",
            clinic_id=None,
        )

        # required slots must be present
        assert "tenant.name" in result.slots_required
        assert "tenant.vertical" in result.slots_required
        assert "tenant.location" in result.slots_required


class TestOnboardingDraftServiceGet:
    """Tests for OnboardingDraftService.get_draft()."""

    @pytest.mark.asyncio
    async def test_get_draft_returns_for_correct_tenant(self) -> None:
        """get_draft() returns draft when tenant_id matches."""
        from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
            OnboardingDraftService,
        )

        draft = _make_draft()
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=draft)

        service = OnboardingDraftService(draft_repo=mock_repo)
        result = await service.get_draft(draft_id=DRAFT_ID, tenant_id=TENANT_ID)

        assert result is not None
        assert result.id == DRAFT_ID
        mock_repo.get_by_id.assert_called_once_with(DRAFT_ID, tenant_id=TENANT_ID)

    @pytest.mark.asyncio
    async def test_get_draft_returns_none_when_not_found(self) -> None:
        """get_draft() returns None (no exception) when draft not found."""
        from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
            OnboardingDraftService,
        )

        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=None)

        service = OnboardingDraftService(draft_repo=mock_repo)
        result = await service.get_draft(draft_id=DRAFT_ID, tenant_id=TENANT_ID)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_draft_tenant_isolation_passes_tenant_id(self) -> None:
        """get_draft() always passes tenant_id to repository (isolation)."""
        from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
            OnboardingDraftService,
        )

        other_tenant = uuid4()
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=None)

        service = OnboardingDraftService(draft_repo=mock_repo)
        await service.get_draft(draft_id=DRAFT_ID, tenant_id=other_tenant)

        # Repo must be called with the OTHER tenant's ID, not TENANT_ID
        mock_repo.get_by_id.assert_called_once_with(DRAFT_ID, tenant_id=other_tenant)


class TestOnboardingDraftServiceUpdateSlot:
    """Tests for OnboardingDraftService.update_slot()."""

    @pytest.mark.asyncio
    async def test_update_slot_persists_new_value(self) -> None:
        """update_slot() retrieves draft, updates slot, and saves."""
        from src.modules.vitalia.copilot.application.services.onboarding_draft_service import (
            OnboardingDraftService,
        )
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        draft = _make_draft()
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=draft)
        mock_repo.save = AsyncMock(return_value=draft)

        service = OnboardingDraftService(draft_repo=mock_repo)
        new_slot = WizardSlot(
            slot_id="tenant.name",
            value="Clínica Nueva",
            confidence=0.95,
            confirmed_at=_utc_now(),
            source="user_text",
        )
        await service.update_slot(
            draft_id=DRAFT_ID,
            tenant_id=TENANT_ID,
            slot_id="tenant.name",
            new_slot=new_slot,
        )

        mock_repo.save.assert_called_once()
        # The saved draft should have the updated slot
        saved = mock_repo.save.call_args[0][0]
        assert saved.slots_required["tenant.name"].value == "Clínica Nueva"
