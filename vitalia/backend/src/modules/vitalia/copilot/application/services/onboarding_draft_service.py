# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""OnboardingDraftService — CRUD operations for wizard OnboardingDraft entity.

Handles lifecycle management of wizard onboarding sessions:
- create_draft: Initialize a new onboarding session with default slots
- get_draft: Retrieve with tenant_id filter (isolation enforced)
- update_slot: Apply a slot update and persist

No PHI: wizard onboarding config only (clinic identity, vertical, tone).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import structlog
from sqlalchemy.exc import IntegrityError

from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

logger = structlog.get_logger()


class DraftAlreadyExistsError(Exception):
    """A draft already exists for this (tenant_id, user_id).

    The DB enforces one onboarding draft per tenant+user
    (uq_vitalia_onboarding_progress_tenant_user). Raised instead of leaking a
    raw IntegrityError → the route maps it to 409, not 500 (HB-88).
    """


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


def _default_required_slots() -> dict[str, WizardSlot]:
    """Return the default set of required wizard slots with empty values."""
    slot_ids = [
        "tenant.name",
        "tenant.vertical",
        "tenant.location",
    ]
    return {
        sid: WizardSlot(
            slot_id=sid,
            value=None,
            confidence=0.0,
            confirmed_at=None,
            source="extracted",
        )
        for sid in slot_ids
    }


def _default_optional_slots() -> dict[str, WizardSlot]:
    """Return the default set of optional wizard slots with empty values."""
    slot_ids = [
        "brand.tone_default",
    ]
    return {
        sid: WizardSlot(
            slot_id=sid,
            value=None,
            confidence=0.0,
            confirmed_at=None,
            source="extracted",
        )
        for sid in slot_ids
    }


class OnboardingDraftService:
    """Application service for OnboardingDraft CRUD lifecycle.

    Dependencies injected at construction — no direct DB imports.
    """

    def __init__(self, draft_repo: "object") -> None:
        """Initialize service with draft repository."""
        self._draft_repo = draft_repo

    async def create_draft(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        mode: str = "libre",
        clinic_id: Optional[UUID] = None,
    ) -> OnboardingDraft:
        """Create and persist a new onboarding draft with default slot set.

        Args:
            tenant_id: Tenant isolation identifier.
            user_id: User initiating the onboarding session.
            mode: Wizard mode — "libre" or "guiado".
            clinic_id: Optional clinic identifier (HIPAA-lite dual filter).

        Returns:
            Persisted OnboardingDraft entity.
        """
        now = _utc_now()
        draft = OnboardingDraft(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            clinic_id=clinic_id,
            mode=mode,
            slots_required=_default_required_slots(),
            slots_optional=_default_optional_slots(),
            bonus_extracted={},
            consent_voice_activation=False,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            completed_at=None,
        )
        try:
            saved = await self._draft_repo.save(draft)
        except IntegrityError as exc:
            # uq_vitalia_onboarding_progress_tenant_user — one draft per tenant+user.
            # DB constraint is the source of truth (handles the check-then-insert race).
            logger.info(
                "onboarding_draft_already_exists",
                tenant_id=str(tenant_id),
                user_id=str(user_id),
            )
            raise DraftAlreadyExistsError(f"Ya existe un borrador de onboarding para tenant {tenant_id}.") from exc
        logger.info(
            "onboarding_draft_created",
            draft_id=str(draft.id),
            tenant_id=str(tenant_id),
        )
        return saved

    async def get_draft(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
    ) -> Optional[OnboardingDraft]:
        """Retrieve a draft by ID, filtered by tenant_id.

        Args:
            draft_id: Draft identifier.
            tenant_id: Tenant isolation identifier — MUST be passed to repo.

        Returns:
            OnboardingDraft if found, None otherwise.
        """
        return await self._draft_repo.get_by_id(draft_id, tenant_id=tenant_id)

    async def update_slot(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
        slot_id: str,
        new_slot: WizardSlot,
    ) -> OnboardingDraft:
        """Retrieve draft, apply slot update, and persist.

        Args:
            draft_id: Draft to update.
            tenant_id: Tenant isolation identifier.
            slot_id: Dot-notation slot identifier.
            new_slot: New frozen WizardSlot value.

        Returns:
            Updated and persisted OnboardingDraft.
        """
        draft = await self._draft_repo.get_by_id(draft_id, tenant_id=tenant_id)
        draft.update_slot(slot_id, new_slot)
        draft.updated_at = _utc_now()
        saved = await self._draft_repo.save(draft)
        logger.info(
            "onboarding_draft_slot_updated",
            draft_id=str(draft_id),
            tenant_id=str(tenant_id),
            slot_id=slot_id,
        )
        return saved
