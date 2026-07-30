# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""AttributionService — marketing attribution matrix proxy.

Application layer — thin proxy to LucasAttributionService snapshot reads.
Does NOT compute attribution itself — reads persisted snapshots.

HIPAA-lite:
  - Dual filter: tenant_id + clinic_id on all queries.
  - No PHI in attribution data (revenue by channel only).

downstream-regression-na: brand-local marketing application service (vitalia-only)
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from uuid import UUID

import structlog

from src.modules.vitalia.agentic.lucas.application.services.lucas_attribution_service import (
    LucasAttributionService,
    TenantLocaleProtocol,
)
from src.modules.vitalia.marketing.application.dtos.marketing_dtos import AttributionMatrixResponse

logger = structlog.get_logger()


class AttributionService:
    """Application service for reading attribution matrix snapshots.

    Proxies to LucasAttributionService (agentic module, read-only consumer).
    Marketing module does NOT own attribution computation — it reads snapshots
    that Lucas cron computed and persisted.

    Methods:
      - get_attribution_matrix(): latest attribution matrix snapshot for a clinic period
    """

    def __init__(
        self,
        *,
        lucas_attribution_service: LucasAttributionService,
        locale: TenantLocaleProtocol,
    ) -> None:
        """Initialise with DI'd Lucas attribution service.

        Args:
            lucas_attribution_service: LucasAttributionService instance (read-only).
            locale: TenantLocale VO — provides currency (NEVER hardcoded).
        """
        self._lucas_attribution_service = lucas_attribution_service
        self._locale = locale

    async def get_attribution_matrix(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: datetime.date,
        period_end: datetime.date,
    ) -> AttributionMatrixResponse:
        """Return attribution matrix snapshot for a clinic period.

        Delegates to LucasAttributionService.compute_attribution() which
        queries analytics engine + persists snapshot.

        Currency is ALWAYS from tenant locale — NEVER hardcoded.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            period_start: Start of period (inclusive).
            period_end: End of period (inclusive).

        Returns:
            AttributionMatrixResponse with channel breakdown and currency from locale.
        """
        snapshot = await self._lucas_attribution_service.compute_attribution(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
            locale=self._locale,
        )

        logger.info(
            "attribution_service.get_attribution_matrix",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            snapshot_id=str(snapshot.id),
            currency=snapshot.currency,
        )

        return AttributionMatrixResponse(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            clinic_id=snapshot.clinic_id,
            period_start=snapshot.period_start,
            period_end=snapshot.period_end,
            channel_breakdown=snapshot.channel_breakdown,
            total_attributed_revenue=Decimal(str(snapshot.total_attributed_revenue)),
            currency=snapshot.currency,
            computed_at=snapshot.computed_at,
        )
