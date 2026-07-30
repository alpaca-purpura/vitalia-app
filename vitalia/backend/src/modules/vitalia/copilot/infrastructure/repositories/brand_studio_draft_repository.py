# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""SqlAlchemyBrandStudioDraftRepository — SQLA 2.0 implementation.

Implements BrandStudioDraftRepository ABC using SQLAlchemy 2.0 async queries.
All queries filter tenant_id — no exceptions (tenant isolation rule).
Expired drafts (expires_at < now) purged by cron — no soft-delete (no deleted_at column).

Table: vitalia_brand_studio_drafts (migration 012_vitalia).
Not PHI: brand identity extraction staging. Single tenant_id filter.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.copilot.domain.entities.brand_studio_draft import BrandStudioDraft
from src.modules.vitalia.copilot.domain.repositories.brand_studio_draft_repository import (
    BrandStudioDraftRepository,
)
from src.modules.vitalia.copilot.persistence.models.brand_studio_draft_model import (
    BrandStudioDraftModel,
)

logger = structlog.get_logger()


def _utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(tz=timezone.utc)


def _model_to_entity(model: BrandStudioDraftModel) -> BrandStudioDraft:
    """Map BrandStudioDraftModel ORM row to BrandStudioDraft domain entity."""
    return BrandStudioDraft(
        id=model.id,
        tenant_id=model.tenant_id,
        user_id=model.user_id,
        draft_kind=model.draft_kind,
        draft_payload=model.draft_payload or {},
        voice_profile_partial_json=model.voice_profile_partial_json,
        committed_at=model.committed_at,
        expires_at=model.expires_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyBrandStudioDraftRepository(BrandStudioDraftRepository):
    """SQLA 2.0 async implementation of BrandStudioDraftRepository.

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
        draft_kind: str = "onboarding_extraction",
        draft_payload: dict | None = None,
        voice_profile_partial_json: dict | None = None,
        expires_at: datetime | None = None,
    ) -> BrandStudioDraft:
        """Create a new vitalia_brand_studio_drafts row.

        Calls session.add() + session.flush(). Caller commits.
        """
        now = _utc_now()
        model = BrandStudioDraftModel(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            draft_kind=draft_kind,
            draft_payload=draft_payload or {},
            voice_profile_partial_json=voice_profile_partial_json,
            committed_at=None,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        await self._session.flush()

        logger.info(
            "brand_studio_draft_created",
            draft_id=str(model.id),
            tenant_id=str(tenant_id),
            draft_kind=draft_kind,
        )
        return _model_to_entity(model)

    async def get_by_id_tenant(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
    ) -> BrandStudioDraft | None:
        """Retrieve brand studio draft by ID + tenant_id filter.

        Returns None if not found or belongs to different tenant (cross-tenant returns None).
        """
        stmt = select(BrandStudioDraftModel).where(
            BrandStudioDraftModel.id == draft_id,
            BrandStudioDraftModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _model_to_entity(model)

    async def append_payload_patch(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
        patch: dict,
        voice_profile_patch: dict | None = None,
    ) -> BrandStudioDraft:
        """Merge patch into existing draft_payload (shallow merge).

        Fetches row (with tenant_id filter), applies merge, flushes.
        Existing keys preserved; patch keys added/overwritten.
        If voice_profile_patch provided, replaces voice_profile_partial_json.
        Caller controls commit.
        """
        stmt = select(BrandStudioDraftModel).where(
            BrandStudioDraftModel.id == draft_id,
            BrandStudioDraftModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"BrandStudioDraft {draft_id!s} not found for tenant {tenant_id!s}")

        # Shallow merge: preserve existing keys, add/overwrite with patch
        merged = {**(model.draft_payload or {}), **patch}
        model.draft_payload = merged
        model.updated_at = _utc_now()

        if voice_profile_patch is not None:
            model.voice_profile_partial_json = voice_profile_patch

        await self._session.flush()

        logger.info(
            "brand_studio_draft_payload_patched",
            draft_id=str(draft_id),
            tenant_id=str(tenant_id),
            patch_keys=list(patch.keys()),
        )
        return _model_to_entity(model)

    async def mark_committed(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
        committed_at: datetime,
    ) -> BrandStudioDraft:
        """Mark brand studio draft as committed to canonical brand settings.

        Sets committed_at timestamp. Flushes. Caller commits.
        """
        stmt = select(BrandStudioDraftModel).where(
            BrandStudioDraftModel.id == draft_id,
            BrandStudioDraftModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"BrandStudioDraft {draft_id!s} not found for tenant {tenant_id!s}")

        model.committed_at = committed_at
        model.updated_at = _utc_now()

        await self._session.flush()

        logger.info(
            "brand_studio_draft_committed",
            draft_id=str(draft_id),
            tenant_id=str(tenant_id),
        )
        return _model_to_entity(model)
