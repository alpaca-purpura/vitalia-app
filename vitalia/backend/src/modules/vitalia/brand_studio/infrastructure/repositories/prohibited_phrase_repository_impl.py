# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""ProhibitedPhraseRepositoryImpl — SQLA 2.0 async implementation.

Tenant isolation: every query filters tenant_id (or IS NULL for seeds).
Soft deletes only (deleted_at).
NO PhiRepositoryBase — owner config, not PHI.

downstream-regression-na: brand-local repo impl vitalia
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import structlog
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.brand_studio.domain.prohibited_phrase import ProhibitedPhrase
from src.modules.vitalia.brand_studio.infrastructure.repositories.prohibited_phrase_repository import (
    ProhibitedPhraseRepository,
)
from src.modules.vitalia.brand_studio.persistence.models.prohibited_phrase_model import (
    VitaliaProhibitedPhraseModel,
)

logger = structlog.get_logger()


def _to_domain(model: VitaliaProhibitedPhraseModel) -> ProhibitedPhrase:
    """Map SQLA model to domain entity."""
    return ProhibitedPhrase(
        id=model.id,
        tenant_id=model.tenant_id,
        phrase=model.phrase,
        suggested_alternative=model.suggested_alternative,
        severity=model.severity,
        country_scope=model.country_scope,
        deleted_at=model.deleted_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class ProhibitedPhraseRepositoryImpl(ProhibitedPhraseRepository):
    """SQLA 2.0 async implementation for prohibited phrases.

    Seed defaults have tenant_id=NULL and are visible to all tenants.
    Tenant overrides have tenant_id=UUID and are visible to that tenant only.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async SQLAlchemy session.

        Args:
            session: AsyncSession from FastAPI DI.
        """
        self._session = session

    async def list_for_tenant(
        self,
        *,
        tenant_id: UUID,
        country: str | None = None,
    ) -> list[ProhibitedPhrase]:
        """Return seed defaults + tenant overrides merged.

        Tenant isolation: returns seed defaults (tenant_id IS NULL) UNION
        tenant-specific overrides (tenant_id = tenant_id param).
        Country filter applies to both sets.
        """
        stmt = select(VitaliaProhibitedPhraseModel).where(
            or_(
                VitaliaProhibitedPhraseModel.tenant_id.is_(None),
                VitaliaProhibitedPhraseModel.tenant_id == tenant_id,
            ),
            VitaliaProhibitedPhraseModel.deleted_at.is_(None),
        )
        if country is not None:
            stmt = stmt.where(
                or_(
                    VitaliaProhibitedPhraseModel.country_scope == country.upper(),
                    VitaliaProhibitedPhraseModel.country_scope.is_(None),
                )
            )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        logger.debug(
            "prohibited_phrase_list",
            tenant_id=str(tenant_id),
            country=country,
            count=len(models),
        )
        return [_to_domain(m) for m in models]

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
    ) -> ProhibitedPhrase | None:
        """Retrieve phrase by ID — tenant or seed."""
        stmt = select(VitaliaProhibitedPhraseModel).where(
            VitaliaProhibitedPhraseModel.id == entity_id,
            or_(
                VitaliaProhibitedPhraseModel.tenant_id.is_(None),
                VitaliaProhibitedPhraseModel.tenant_id == tenant_id,
            ),
            VitaliaProhibitedPhraseModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return _to_domain(model) if model else None

    async def create(self, phrase: ProhibitedPhrase) -> ProhibitedPhrase:
        """Persist a new prohibited phrase."""
        now = datetime.now(timezone.utc)
        model = VitaliaProhibitedPhraseModel(
            id=phrase.id if phrase.id else uuid4(),
            tenant_id=phrase.tenant_id,
            phrase=phrase.phrase.lower().strip(),
            suggested_alternative=phrase.suggested_alternative,
            severity=phrase.severity,
            country_scope=phrase.country_scope.upper() if phrase.country_scope else None,
            created_at=now,
            updated_at=None,
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "prohibited_phrase_created",
            phrase_id=str(model.id),
            tenant_id=str(phrase.tenant_id) if phrase.tenant_id else "seed",
        )
        return _to_domain(model)

    async def soft_delete(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
    ) -> None:
        """Soft-delete a tenant override phrase (not seeds)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(VitaliaProhibitedPhraseModel)
            .where(
                VitaliaProhibitedPhraseModel.id == entity_id,
                VitaliaProhibitedPhraseModel.tenant_id == tenant_id,  # only tenant overrides
                VitaliaProhibitedPhraseModel.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        await self._session.execute(stmt)
        logger.info(
            "prohibited_phrase_soft_deleted",
            phrase_id=str(entity_id),
            tenant_id=str(tenant_id),
        )
