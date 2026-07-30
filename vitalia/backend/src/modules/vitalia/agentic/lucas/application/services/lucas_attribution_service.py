# cap: agentic.lucas-daily-analysis
# story-origin: TBD
"""Lucas application service — LucasAttributionService.

Pure DB service — no LLM calls. Queries analytics engine adapter for
channel attribution data and persists snapshot.

HIPAA-lite:
  - No PHI processed — analytics revenue data only.
  - Clinic_id ALWAYS passed to repo (dual filter).
  - Currency from locale.currency — NEVER hardcoded.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.agentic.lucas.domain.entities.attribution_matrix_snapshot import (
    AttributionMatrixSnapshot,
)
from src.modules.vitalia.agentic.lucas.infrastructure.adapters.analytics_engine_query_adapter import (
    AnalyticsEngineQueryAdapter,
)
from src.modules.vitalia.agentic.lucas.infrastructure.repositories.attribution_matrix_snapshot_repository import (
    AttributionMatrixSnapshotRepository,
)

logger = structlog.get_logger()


class TenantLocaleProtocol(Protocol):
    """Minimal locale protocol — currency from TenantLocale."""

    currency: str
    timezone: str


class LucasAttributionService:
    """Application service for computing attribution matrix snapshots.

    Pure DB — no LLM. Queries analytics engine and persists snapshot.

    Flow:
        1. AnalyticsEngineQueryAdapter.get_attribution_breakdown() — engine query.
        2. Compute total_attributed_revenue from breakdown.
        3. Build AttributionMatrixSnapshot with locale.currency (NEVER hardcoded).
        4. repo.save() — persist with tenant_id + clinic_id.
        5. Return entity.
    """

    def __init__(
        self,
        *,
        repo: AttributionMatrixSnapshotRepository,
        analytics_adapter: AnalyticsEngineQueryAdapter,
    ) -> None:
        """Initialise with DI'd dependencies."""
        self._repo = repo
        self._analytics_adapter = analytics_adapter

    async def compute_attribution(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: dt.date,
        period_end: dt.date,
        locale: TenantLocaleProtocol,
    ) -> AttributionMatrixSnapshot:
        """Compute and persist attribution matrix snapshot.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            period_start: Start of period (inclusive).
            period_end: End of period (inclusive).
            locale: TenantLocale — provides currency (NEVER hardcoded).

        Returns:
            AttributionMatrixSnapshot with currency from tenant locale.
        """
        now = dt.datetime.now(tz=dt.timezone.utc)

        # Query analytics engine (READ-ONLY)
        channel_breakdown = await self._analytics_adapter.get_attribution_breakdown(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
        )

        # Compute total from breakdown values
        total = Decimal("0.00")
        for value in channel_breakdown.values():
            try:
                total += Decimal(str(value))
            except Exception:
                pass  # Skip non-numeric values gracefully

        # Currency from locale — NEVER hardcoded
        currency = locale.currency

        entity = AttributionMatrixSnapshot(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
            channel_breakdown=channel_breakdown,
            total_attributed_revenue=total,
            currency=currency,
            computed_at=now,
            deleted_at=None,
        )

        saved = await self._repo.save(entity)

        logger.info(
            "lucas_attribution_snapshot_saved",
            snapshot_id=str(saved.id),
            tenant_id=str(tenant_id),
            period_start=str(period_start),
            currency=currency,
        )

        return saved
