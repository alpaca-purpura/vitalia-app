# cap: scheduling.mateo-agenda
# story-origin: TBD
"""AppointmentAggregatesRepository — monthly slot counts for virtualized calendar.

Provides server-side aggregates for react-window month view.
Returns slot count per day (not full slot details) to avoid serializing
30+ days × 10-20 slots = 300+ objects per calendar month render.

HIPAA-lite dual filter: tenant_id + clinic_id on ALL queries.

Per 03-arch § 3.4 + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AppointmentAggregatesRepository:
    """Async repository for monthly appointment slot aggregates.

    count_per_day() returns list of (date, count) dicts for a given year+month.
    Used by FE react-window virtualized month grid to show slot density per cell.
    No PHI returned — only integer counts.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_per_day(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        year: int,
        month: int,
        doctor_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Count appointment slots per calendar day for a month.

        Dual filter: tenant_id + clinic_id applied in WHERE.
        Returns PHI-free data (counts only).

        Args:
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).
            year: Calendar year (e.g. 2026).
            month: Calendar month (1-12).
            doctor_id: Optional doctor filter.

        Returns:
            List of dicts with keys:
              - slot_date: date string "YYYY-MM-DD"
              - slot_count: number of appointments that day
        """
        conditions = [
            text(f"tenant_id = '{tenant_id}'"),
            text(f"clinic_id = '{clinic_id}'"),
            text(f"EXTRACT(YEAR FROM slot_iso) = {year}"),
            text(f"EXTRACT(MONTH FROM slot_iso) = {month}"),
            text("deleted_at IS NULL"),
        ]

        if doctor_id is not None:
            conditions.append(text(f"doctor_id = '{doctor_id}'"))

        stmt = (
            select(
                text("DATE(slot_iso) AS slot_date"),
                text("COUNT(*) AS slot_count"),
            )
            .select_from(text("vitalia_appointments"))
            .where(*conditions)
            .group_by(text("DATE(slot_iso)"))
            .order_by(text("DATE(slot_iso) ASC"))
        )

        logger.debug(
            "appointment_aggregates_count_per_day",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            year=year,
            month=month,
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        return [
            {
                "slot_date": str(row[0]),
                "slot_count": int(row[1]),
            }
            for row in rows
        ]

    async def count_by_status(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        year: int,
        month: int,
    ) -> dict[str, int]:
        """Count appointments grouped by status for a month.

        Used for summary statistics (dashboard counters).
        Dual filter: tenant_id + clinic_id.

        Args:
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).
            year: Calendar year.
            month: Calendar month.

        Returns:
            Dict mapping status → count.
        """
        stmt = (
            select(
                text("status"),
                text("COUNT(*) AS cnt"),
            )
            .select_from(text("vitalia_appointments"))
            .where(
                text(f"tenant_id = '{tenant_id}'"),
                text(f"clinic_id = '{clinic_id}'"),
                text(f"EXTRACT(YEAR FROM slot_iso) = {year}"),
                text(f"EXTRACT(MONTH FROM slot_iso) = {month}"),
                text("deleted_at IS NULL"),
            )
            .group_by(text("status"))
        )

        result = await self._session.execute(stmt)
        return {row[0]: int(row[1]) for row in result.all()}
