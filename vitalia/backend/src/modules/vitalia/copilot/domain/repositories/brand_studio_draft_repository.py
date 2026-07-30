# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""BrandStudioDraftRepository — ABC interface for brand studio draft persistence.

Domain layer — pure Python, zero framework imports.
Implemented by infrastructure.repositories.SqlAlchemyBrandStudioDraftRepository.

Table backing this interface: vitalia_brand_studio_drafts (migration 012_vitalia).
Not PHI: brand identity extraction staging area (clinic name, vertical, voice samples).
Single tenant_id filter — no clinic_id dual filter required for brand studio tables.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.modules.vitalia.copilot.domain.entities.brand_studio_draft import BrandStudioDraft


class BrandStudioDraftRepository(ABC):
    """Abstract repository for BrandStudioDraft onboarding extraction staging.

    All methods are async. Every method that queries data MUST filter by tenant_id.
    """

    @abstractmethod
    async def create(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        draft_kind: str = "onboarding_extraction",
        draft_payload: dict | None = None,
        voice_profile_partial_json: dict | None = None,
        expires_at: datetime | None = None,
    ) -> BrandStudioDraft:
        """Create a new brand studio draft record.

        Args:
            tenant_id: Tenant isolation identifier.
            user_id: User initiating the extraction session.
            draft_kind: Draft type — "onboarding_extraction" (Slice 1), extensible.
            draft_payload: Initial extraction payload (defaults to empty dict).
            voice_profile_partial_json: Optional partial PersonalityProfile (None = empty).
            expires_at: TTL for uncommitted draft. None if not time-bounded.

        Returns:
            Domain entity representing the created record.
        """

    @abstractmethod
    async def get_by_id_tenant(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
    ) -> BrandStudioDraft | None:
        """Retrieve a brand studio draft by ID with tenant_id isolation filter.

        Returns None when not found — never raises for missing records.
        Cross-tenant requests return None (not 404) for security.

        Args:
            draft_id: Draft UUID to retrieve.
            tenant_id: Tenant isolation identifier.

        Returns:
            Domain entity if found, None otherwise.
        """

    @abstractmethod
    async def append_payload_patch(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
        patch: dict,
        voice_profile_patch: dict | None = None,
    ) -> BrandStudioDraft:
        """Merge a payload patch into the draft's existing payload.

        Applies shallow merge (existing keys preserved, patch keys added/overwritten).
        If voice_profile_patch is provided, replaces voice_profile_partial_json.
        Mutates the ORM row and flushes. Does not commit (caller controls tx).

        Args:
            draft_id: Draft UUID to update.
            tenant_id: Tenant isolation filter.
            patch: Dict of key-value pairs to merge into draft_payload.
            voice_profile_patch: Optional dict to replace voice_profile_partial_json.

        Returns:
            Updated domain entity with merged payload.
        """

    @abstractmethod
    async def mark_committed(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
        committed_at: datetime,
    ) -> BrandStudioDraft:
        """Mark a brand studio draft as committed to canonical brand settings.

        Sets committed_at timestamp. After commit, draft is considered final.

        Args:
            draft_id: Draft UUID to commit.
            tenant_id: Tenant isolation filter.
            committed_at: UTC timestamp of commitment.

        Returns:
            Updated domain entity with committed_at set.
        """
