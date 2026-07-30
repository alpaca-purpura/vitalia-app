# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""SqlAlchemyOnboardingProgressRepository — SQLA 2.0 implementation.

Implements OnboardingProgressRepository ABC using SQLAlchemy 2.0 async queries.
All queries filter tenant_id — no exceptions (tenant isolation rule).
Status 'abandoned' replaces soft-delete for onboarding tables (no deleted_at).

Table: vitalia_onboarding_progress (migration 011_vitalia).
Not PHI: wizard onboarding config only. Single tenant_id filter.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot
from src.modules.vitalia.copilot.domain.repositories.onboarding_progress_repository import (
    OnboardingProgressRepository,
)
from src.modules.vitalia.copilot.persistence.models.onboarding_progress_model import (
    OnboardingProgressModel,
)

logger = structlog.get_logger()

# Mapping helpers are defined module-level (used by both save() bridge + repository methods)


def _utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(tz=timezone.utc)


def _model_to_draft(model: OnboardingProgressModel) -> OnboardingDraft:
    """Map OnboardingProgressModel ORM row to OnboardingDraft domain entity.

    The onboarding_progress table stores slot state as JSONB dicts.
    We reconstruct minimal WizardSlot objects from stored JSONB.
    Required slots come from slots_pending; confirmed from slots_confirmed.
    """
    # Reconstruct WizardSlot dicts from stored JSONB
    slots_required: dict[str, WizardSlot] = {}
    slots_optional: dict[str, WizardSlot] = {}

    # Confirmed slots → go into slots_required (they are fully confirmed)
    for slot_id, slot_data in (model.slots_confirmed or {}).items():
        if isinstance(slot_data, dict):
            slots_required[slot_id] = WizardSlot(
                slot_id=slot_id,
                value=slot_data.get("value"),
                confidence=float(slot_data.get("confidence", 1.0)),
                confirmed_at=None,  # stored as confirmed — treat as confirmed slot
                source=slot_data.get("source", "extracted"),
            )
        else:
            # Scalar value stored directly
            slots_required[slot_id] = WizardSlot(
                slot_id=slot_id,
                value=slot_data,
                confidence=1.0,
                confirmed_at=None,
                source="extracted",
            )

    # Pending slots → go into slots_optional (not yet confirmed)
    for slot_id, slot_data in (model.slots_pending or {}).items():
        if isinstance(slot_data, dict):
            slots_optional[slot_id] = WizardSlot(
                slot_id=slot_id,
                value=slot_data.get("value"),
                confidence=float(slot_data.get("confidence", 0.0)),
                confirmed_at=None,
                source=slot_data.get("source", "extracted"),
            )
        else:
            slots_optional[slot_id] = WizardSlot(
                slot_id=slot_id,
                value=slot_data,
                confidence=0.0,
                confirmed_at=None,
                source="extracted",
            )

    return OnboardingDraft(
        id=model.id,
        tenant_id=model.tenant_id,
        user_id=model.user_id,
        clinic_id=None,  # onboarding is user-level (pre-clinic-setup)
        mode=model.mode,
        slots_required=slots_required,
        slots_optional=slots_optional,
        bonus_extracted={},
        consent_voice_activation=False,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=None,
        completed_at=model.completed_at,
    )


class SqlAlchemyOnboardingProgressRepository(OnboardingProgressRepository):
    """SQLA 2.0 async implementation of OnboardingProgressRepository.

    Every query filters tenant_id — no exceptions.
    Caller (application service) controls transaction commits.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialise with async SQLAlchemy session.

        Args:
            session: Injected AsyncSession (caller owns commit lifecycle).
        """
        self._session = session

    async def create(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        step: str,
        mode: str | None = None,
        draft_id: UUID | None = None,
        slots_confirmed: dict | None = None,
        slots_pending: dict | None = None,
    ) -> OnboardingDraft:
        """Create a new vitalia_onboarding_progress row.

        Calls session.add() + session.flush(). Caller commits.
        """
        now = _utc_now()
        model = OnboardingProgressModel(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            step=step,
            mode=mode,
            draft_id=draft_id,
            slots_confirmed=slots_confirmed or {},
            slots_pending=slots_pending or {},
            attachments=[],
            status="in_progress",
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        await self._session.flush()

        logger.info(
            "onboarding_progress_created",
            progress_id=str(model.id),
            tenant_id=str(tenant_id),
            step=step,
        )
        return _model_to_draft(model)

    async def get_by_tenant_user(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
    ) -> OnboardingDraft | None:
        """Retrieve active onboarding progress for tenant+user.

        Applies tenant_id isolation filter. Returns None if not found.
        """
        stmt = select(OnboardingProgressModel).where(
            OnboardingProgressModel.tenant_id == tenant_id,
            OnboardingProgressModel.user_id == user_id,
            OnboardingProgressModel.status != "abandoned",
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _model_to_draft(model)

    async def update_step(
        self,
        *,
        progress_id: UUID,
        tenant_id: UUID,
        step: str,
        slots_confirmed: dict | None = None,
        slots_pending: dict | None = None,
        draft_id: UUID | None = None,
    ) -> OnboardingDraft:
        """Update wizard step and optionally slot state / draft_id.

        Fetches row (with tenant_id filter), mutates in-place, flushes.
        Caller controls commit.
        """
        stmt = select(OnboardingProgressModel).where(
            OnboardingProgressModel.id == progress_id,
            OnboardingProgressModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"OnboardingProgress {progress_id!s} not found for tenant {tenant_id!s}")

        model.step = step
        model.updated_at = _utc_now()
        if slots_confirmed is not None:
            model.slots_confirmed = slots_confirmed
        if slots_pending is not None:
            model.slots_pending = slots_pending
        if draft_id is not None:
            model.draft_id = draft_id

        await self._session.flush()

        logger.info(
            "onboarding_progress_step_updated",
            progress_id=str(progress_id),
            tenant_id=str(tenant_id),
            step=step,
        )
        return _model_to_draft(model)

    async def mark_completed(
        self,
        *,
        progress_id: UUID,
        tenant_id: UUID,
        completed_at: datetime,
    ) -> OnboardingDraft:
        """Mark onboarding progress as completed.

        Sets status='completed' and completed_at. Flushes. Caller commits.
        """
        stmt = select(OnboardingProgressModel).where(
            OnboardingProgressModel.id == progress_id,
            OnboardingProgressModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"OnboardingProgress {progress_id!s} not found for tenant {tenant_id!s}")

        model.status = "completed"
        model.completed_at = completed_at
        model.updated_at = _utc_now()

        await self._session.flush()

        logger.info(
            "onboarding_progress_completed",
            progress_id=str(progress_id),
            tenant_id=str(tenant_id),
        )
        return _model_to_draft(model)

    # ------------------------------------------------------------------
    # Bridge methods — OnboardingDraftService compat interface
    # ------------------------------------------------------------------
    # OnboardingDraftService (application layer) calls draft_repo.save(draft)
    # and draft_repo.get_by_id(draft_id, tenant_id=...).
    # These bridge methods allow this repo to serve as that draft_repo
    # without modifying the existing service (preserves shipped behavior).

    async def save(self, draft: OnboardingDraft) -> OnboardingDraft:
        """Upsert an OnboardingDraft entity into the progress table.

        Called by OnboardingDraftService as ``draft_repo.save(draft)``.
        Performs INSERT or UPDATE based on whether the progress record exists.
        """
        # Try find existing row for this draft (by id + tenant_id)
        stmt = select(OnboardingProgressModel).where(
            OnboardingProgressModel.id == draft.id,
            OnboardingProgressModel.tenant_id == draft.tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        now = _utc_now()

        if model is None:
            # INSERT: create new progress row from draft state
            model = OnboardingProgressModel(
                id=draft.id,
                tenant_id=draft.tenant_id,
                user_id=draft.user_id,
                step="slot_collection",
                mode=draft.mode,
                draft_id=None,
                slots_confirmed={},
                slots_pending={},
                attachments=[],
                status="completed" if draft.completed_at else "in_progress",
                completed_at=draft.completed_at,
                created_at=draft.created_at or now,
                updated_at=now,
            )
            self._session.add(model)
        else:
            # UPDATE: refresh mutable fields
            model.mode = draft.mode
            model.status = "completed" if draft.completed_at else "in_progress"
            model.completed_at = draft.completed_at
            model.updated_at = now

        await self._session.flush()

        logger.info(
            "onboarding_draft_saved",
            draft_id=str(draft.id),
            tenant_id=str(draft.tenant_id),
        )
        return draft

    async def get_by_id(
        self,
        draft_id: UUID,
        *,
        tenant_id: UUID,
    ) -> OnboardingDraft | None:
        """Retrieve OnboardingDraft by id with tenant_id isolation.

        Called by OnboardingDraftService as ``draft_repo.get_by_id(id, tenant_id=...)``.
        Returns None if not found or belongs to different tenant.
        """
        stmt = select(OnboardingProgressModel).where(
            OnboardingProgressModel.id == draft_id,
            OnboardingProgressModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _model_to_draft(model)
