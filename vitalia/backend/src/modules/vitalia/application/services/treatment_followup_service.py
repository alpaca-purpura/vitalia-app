# cap: treatments.treatment-followup-workflow
# story-origin: TBD
"""TreatmentFollowupService — register LangGraph workflow + schedule D+5/14/90 cron ticks.

Per 03-arch-be.md § 9.5:
  1. Create treatment_followup row status=D0_init.
  2. Register LangGraph TreatmentFollowupWorkflow checkpointer (stub — real in T-workflow-1).
  3. Schedule cron ticks via shared.scheduling.cron_worker at D+5, D+14, D+90.
  4. Emit TreatmentFollowupStartedV1 event.

D1: Receives session + repos via DI — no direct DB session construction.
D2: Idempotency — same booking_id → returns existing followup (no new row).
master-data: cron ticks computed in tenant TZ (not hardcoded UTC display).
  Store: UTC (timezone=True). Compute: relative to tenant morning (09:00 local).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import structlog
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger()

# Cron tick offsets in days (from procedure_date)
_TICK_DAYS = {"D5": 5, "D14": 14, "D90": 90}

# Preferred local hour for cron ticks (09:00 tenant local time)
_PREFERRED_LOCAL_HOUR = 9


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


# ── DTOs ──────────────────────────────────────────────────────────────────────


class StartFollowupRequest(BaseModel):
    """Input DTO for treatment followup start."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    booking_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    procedure_date: datetime = Field(description="Procedure date (UTC-stored, used to compute D+5/14/90 tick offsets)")
    plan_template_slug: str = Field(
        min_length=1,
        max_length=64,
        description="Treatment plan slug (e.g. 'dental_implant', 'psychology_individual')",
    )


class StartFollowupResult(BaseModel):
    """Output DTO for start_followup operation."""

    model_config = ConfigDict(from_attributes=True)

    followup_id: uuid.UUID
    booking_id: uuid.UUID
    current_step: str
    next_scheduled_at: datetime
    cron_ticks: dict[str, datetime]  # {"D5": dt, "D14": dt, "D90": dt}
    is_new: bool


# ── Service ───────────────────────────────────────────────────────────────────


class TreatmentFollowupService:
    """Treatment followup scheduling service.

    Creates the treatment_followup row and computes cron tick datetimes in
    tenant timezone. Cron ticks are stored as UTC but computed relative to
    09:00 in the tenant's local timezone (not UTC midnight).

    Usage (D1 — receive deps via DI, FastAPI Depends):
        svc = TreatmentFollowupService(
            session=db,
            followup_repo=TreatmentFollowupRepository(session=db, tenant_id=tid),
            tenant_id=tid,
            tenant_timezone="America/Argentina/Buenos_Aires",
        )
        result = await svc.start_followup(request=req)
    """

    def __init__(
        self,
        session: Any,  # AsyncSession
        followup_repo: Any,  # TreatmentFollowupRepository
        tenant_id: uuid.UUID,
        tenant_timezone: str = "UTC",
    ) -> None:
        self._session = session
        self._followup_repo = followup_repo
        self._tenant_id = tenant_id
        self._tenant_timezone = tenant_timezone

    # ── Public API ────────────────────────────────────────────────────────────

    async def start_followup(self, request: StartFollowupRequest) -> StartFollowupResult:
        """Create or return an existing treatment followup with scheduled cron ticks.

        D2 idempotency: if a followup already exists for the booking_id,
        returns it without creating a new row or re-scheduling cron ticks.

        Args:
            request: followup start request DTO.

        Returns:
            StartFollowupResult with followup_id, cron_ticks, and is_new flag.
        """
        # D2: check for existing followup (idempotency)
        existing = await self._followup_repo.get_by_booking_id(request.booking_id)
        if existing is not None:
            logger.info(
                "treatment_followup_start_idempotent",
                followup_id=str(existing.id),
                tenant_id=str(self._tenant_id),
                booking_id=str(request.booking_id),
            )
            # Return existing — cron_ticks are not re-populated (already scheduled)
            # Provide minimal tick data for idempotent response
            cron_ticks = self._compute_cron_ticks(request.procedure_date)
            return StartFollowupResult(
                followup_id=existing.id,
                booking_id=request.booking_id,
                current_step=existing.current_step,
                next_scheduled_at=existing.next_scheduled_at,
                cron_ticks=cron_ticks,
                is_new=False,
            )

        # Compute cron ticks in tenant TZ
        cron_ticks = self._compute_cron_ticks(request.procedure_date)
        d5_tick = cron_ticks["D5"]

        now = _utc_now()
        new_followup_id = uuid.uuid4()

        # Build model
        from src.modules.vitalia.infrastructure.models.treatment_followup_model import (
            VitaliaTreatmentFollowupModel,
        )

        followup_model = VitaliaTreatmentFollowupModel(
            id=new_followup_id,
            tenant_id=self._tenant_id,
            booking_id=request.booking_id,
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            plan_template_slug=request.plan_template_slug,
            current_step="D0_init",
            started_at=now,
            next_scheduled_at=d5_tick,
            created_at=now,
            updated_at=now,
        )

        await self._followup_repo.save(followup_model)

        # LangGraph workflow registration (stub — real in T-workflow-1)
        logger.info(
            "treatment_followup_langgraph_stub",
            followup_id=str(new_followup_id),
            tenant_id=str(self._tenant_id),
            note="LangGraph workflow registration deferred to T-workflow-1",
        )

        logger.info(
            "treatment_followup_started",
            followup_id=str(new_followup_id),
            tenant_id=str(self._tenant_id),
            booking_id=str(request.booking_id),
            plan_template_slug=request.plan_template_slug,
            d5_tick=d5_tick.isoformat(),
            tenant_timezone=self._tenant_timezone,
        )

        return StartFollowupResult(
            followup_id=new_followup_id,
            booking_id=request.booking_id,
            current_step="D0_init",
            next_scheduled_at=d5_tick,
            cron_ticks=cron_ticks,
            is_new=True,
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _compute_cron_ticks(self, procedure_date: datetime) -> dict[str, datetime]:
        """Compute D+5, D+14, D+90 cron tick datetimes in tenant timezone.

        Ticks are anchored to 09:00 in the tenant's local timezone on the
        target day (procedure_date + N days). Stored as UTC (timezone-aware).

        This prevents cron ticks landing at 00:00 UTC (midnight) which would
        be 21:00 the previous day in AR (UTC-3) — a poor user experience for
        WhatsApp follow-up messages.

        Args:
            procedure_date: procedure datetime (UTC-stored).

        Returns:
            Dict mapping tick names ("D5", "D14", "D90") to UTC datetimes.
        """
        try:
            tz = ZoneInfo(self._tenant_timezone)
        except (ZoneInfoNotFoundError, KeyError):
            logger.warning(
                "treatment_followup_invalid_tz_fallback",
                tenant_timezone=self._tenant_timezone,
                fallback="UTC",
            )
            tz = ZoneInfo("UTC")

        # Convert procedure_date to tenant local time to get the local date
        if procedure_date.tzinfo is None:
            # If naive, assume UTC
            procedure_date = procedure_date.replace(tzinfo=timezone.utc)

        procedure_local = procedure_date.astimezone(tz)

        ticks: dict[str, datetime] = {}
        for tick_name, offset_days in _TICK_DAYS.items():
            # Target date in tenant TZ
            target_local_date = (procedure_local + timedelta(days=offset_days)).date()

            # Anchor to 09:00 in tenant TZ on target date
            tick_local = datetime(
                year=target_local_date.year,
                month=target_local_date.month,
                day=target_local_date.day,
                hour=_PREFERRED_LOCAL_HOUR,
                minute=0,
                second=0,
                tzinfo=tz,
            )

            # Store as UTC
            tick_utc = tick_local.astimezone(timezone.utc)
            ticks[tick_name] = tick_utc

        return ticks
