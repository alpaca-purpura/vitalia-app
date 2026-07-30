# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""OnboardingProgressRepository — ABC interface for onboarding progress persistence.

Domain layer — pure Python, zero framework imports.
Implemented by infrastructure.repositories.SqlAlchemyOnboardingProgressRepository.

Table backing this interface: vitalia_onboarding_progress (migration 011_vitalia).
Not PHI: wizard onboarding config only (step name, slot state, mode).
Single tenant_id filter — no clinic_id dual filter required for onboarding tables.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft


class OnboardingProgressRepository(ABC):
    """Abstract repository for OnboardingDraft wizard session persistence.

    All methods are async. Every method that queries data MUST filter by tenant_id.
    """

    @abstractmethod
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
        """Create a new onboarding progress record.

        Args:
            tenant_id: Tenant isolation identifier.
            user_id: User starting the onboarding session.
            step: Initial wizard step name.
            mode: Wizard mode — "libre" or "guiado". None if not yet selected.
            draft_id: Optional linked BrandStudioDraft UUID.
            slots_confirmed: Dict of confirmed slot state.
            slots_pending: Dict of pending slot state.

        Returns:
            Domain entity representing the created record.
        """

    @abstractmethod
    async def get_by_tenant_user(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
    ) -> OnboardingDraft | None:
        """Retrieve the active onboarding progress record for a tenant+user.

        Applies tenant_id isolation filter. Returns None when not found
        (never raises for missing records — cross-tenant returns None, not 404).

        Args:
            tenant_id: Tenant isolation identifier.
            user_id: User identifier.

        Returns:
            Domain entity if found, None otherwise.
        """

    @abstractmethod
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
        """Update the current step (and optionally slots / draft_id) in place.

        Mutates the ORM row and flushes. Does not commit (caller controls tx).

        Args:
            progress_id: Progress record UUID to update.
            tenant_id: Tenant isolation filter.
            step: New wizard step name.
            slots_confirmed: Updated confirmed slots (None = unchanged).
            slots_pending: Updated pending slots (None = unchanged).
            draft_id: Updated draft link (None = unchanged).

        Returns:
            Updated domain entity.
        """

    @abstractmethod
    async def mark_completed(
        self,
        *,
        progress_id: UUID,
        tenant_id: UUID,
        completed_at: datetime,
    ) -> OnboardingDraft:
        """Mark an onboarding progress record as completed.

        Sets status='completed' and completed_at timestamp.

        Args:
            progress_id: Progress record UUID to complete.
            tenant_id: Tenant isolation filter.
            completed_at: UTC timestamp of completion.

        Returns:
            Updated domain entity with status='completed'.
        """
