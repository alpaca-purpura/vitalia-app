# cap: scheduling.mateo-agenda
# story-origin: TBD
"""AgendaGridRepository — interface (Protocol) for agenda grid queries.

Defines the contract for listing appointment slots for the Valeria Agenda
cockpit calendar view.

HIPAA-lite dual filter: tenant_id + clinic_id mandatory on ALL queries.
PHI projection: patient_name_masked + dni_masked only (no raw PHI).

Per 03-arch § 3.1 + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from src.modules.vitalia.scheduling.domain.agenda_filter import AgendaPresetFilter


class AgendaGridRepository(Protocol):
    """Interface for agenda grid slot queries.

    All implementations MUST:
    1. Apply dual filter (tenant_id + clinic_id) on every query.
    2. Return PHI-masked slot projections only.
    3. Not expose raw patient names or DNI values.
    """

    async def list_slots(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        date_from: datetime,
        date_to: datetime,
        preset_filter: AgendaPresetFilter | None = None,
        doctor_id: UUID | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List appointment slots for the calendar view.

        Returns PHI-masked slot projections:
          - patient_name_masked (e.g. "P. Hernández")
          - dni_masked (e.g. "12.***.***")
          - service, doctor, start_at, end_at
          - payment_status, origin, balance_amount_cents, currency

        Args:
            tenant_id: Tenant UUID (dual filter key 1).
            clinic_id: Clinic UUID (HIPAA-lite dual filter key 2).
            date_from: Start of date range (inclusive, UTC tz-aware).
            date_to: End of date range (inclusive, UTC tz-aware).
            preset_filter: Optional preset chip filter (HOY, NO_SHOWS_DIA, etc.).
            doctor_id: Optional doctor filter.
            limit: Max results (default 500 — calendar month view).
            offset: Pagination offset.

        Returns:
            List of slot projection dicts (PHI-masked).
        """
        ...  # pragma: no cover
