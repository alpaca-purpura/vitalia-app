# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Async repository — VitaliaPlanTierConfigModel.

CROSS-TENANT catalog — no tenant_id filter (global platform data).
Read-only for tenant services. Platform ops manages via seed data in migration.
"""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.infrastructure.models.plan_tier_config_model import (
    VitaliaPlanTierConfigModel,
)

logger = structlog.get_logger()


class PlanTierConfigRepository:
    """Cross-tenant read-only repository for VitaliaPlanTierConfigModel.

    SPECIAL CASE: No tenant_id filter — this is a global catalog that all
    tenants share. Repository has no tenant_id constructor parameter.

    Per § 8.2 arch: "PlanTierConfigRepository (cross-tenant catalog — special:
    NO tenant_id filter; read-only)".
    """

    def __init__(self, session: AsyncSession) -> None:
        """Note: No tenant_id parameter — cross-tenant catalog."""
        self._session = session

    async def get_by_id(self, tier_id: uuid.UUID) -> VitaliaPlanTierConfigModel | None:
        """Return plan tier config by ID (cross-tenant — no tenant filter)."""
        stmt = select(VitaliaPlanTierConfigModel).where(
            VitaliaPlanTierConfigModel.id == tier_id,
            VitaliaPlanTierConfigModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, plan_tier_slug: str) -> VitaliaPlanTierConfigModel | None:
        """Return plan tier config by slug (e.g. 'solo_doctor', 'clinic')."""
        stmt = select(VitaliaPlanTierConfigModel).where(
            VitaliaPlanTierConfigModel.plan_tier_slug == plan_tier_slug,
            VitaliaPlanTierConfigModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[VitaliaPlanTierConfigModel]:
        """List all active plan tier configurations."""
        stmt = (
            select(VitaliaPlanTierConfigModel)
            .where(VitaliaPlanTierConfigModel.is_active.is_(True))
            .order_by(VitaliaPlanTierConfigModel.price_usd_monthly.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
