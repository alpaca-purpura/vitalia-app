# cap: clinics.lisa.doctores
"""AvailabilityBlockService — application service for availability block CRUD.

HIPAA-lite rules (vitalia/.claude/rules/hipaa-lite.md):
  - Audit log write SYNC (awaited) BEFORE response on every mutation
  - Dual filter enforced by AvailabilityBlockRepository (CompoundScopeRepositoryBase)
  - Availability blocks are scheduling metadata (not PHI), but dual-filter applied
    for cross-clinic isolation consistency

Architecture:
  - project_block: AvailabilityProjectionService(dateutil.rrule) expands block -> slots
  - reproject-future-only: PATCH only modifies slot_date >= today
  - delete preserves: slots with has_confirmed_appointment=True are NEVER deleted (SC-1d, SC-3b)
  - audit sync: doctor.availability_block_created / doctor.availability_block_deleted
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogEntry,
    AuditLogRepository,
)
from src.modules.vitalia.clinics.application.availability_projection_service import (
    AvailabilityProjectionService,
    ProjectedSlot,
)
from src.modules.vitalia.clinics.application.ports.availability_repo_port import (
    AvailabilityRepoPort,
)
from src.modules.vitalia.clinics.application.recurrence_summary import (
    format_recurrence_summary,
)
from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock
from src.modules.vitalia.clinics.infrastructure.models.availability_slot_model import (
    VitaliaAvailabilitySlotModel,
)

logger = structlog.get_logger()

_DEFAULT_SLOT_DURATION_MINUTES = 30

# D3-C (03-arch-delta § 4.3): from/to bounded to avoid unbounded projection
_MAX_OCCURRENCES_RANGE_DAYS = 62


@dataclass
class BlockOccurrence:
    """A block-level occurrence within a queried range (D3-C paint SSoT).

    The calendar paints blocks, not 30-min slots — slots collapse to one
    occurrence per (block, date). Returned by
    AvailabilityBlockService.list_occurrences; the router maps it to
    AvailabilityOccurrenceDTO.
    """

    block_id: UUID
    occurrence_date: date
    start_time: time
    end_time: time
    kind: str
    freq: str | None
    pattern_summary: str


class AvailabilityBlockService:
    """Application service for AvailabilityBlock CRUD.

    Orchestrates:
    - project_block (via AvailabilityProjectionService + dateutil.rrule)
    - create (block + slots transactional)
    - update (reproject-future-only)
    - delete (retire future free slots; preserve confirmed)
    - audit log SYNC writes

    Transaction boundary: caller (router) owns commit — this service only flushes.
    """

    def __init__(
        self,
        block_repo: AvailabilityRepoPort,
        audit_repo: AuditLogRepository,
        slot_duration_minutes: int = _DEFAULT_SLOT_DURATION_MINUTES,
    ) -> None:
        """Initialize with injected dependencies.

        Args:
            block_repo: AvailabilityRepoPort (AvailabilityBlockRepository in production).
            audit_repo: AuditLogRepository for sync audit writes.
            slot_duration_minutes: Slot granularity for projection (default 30 min).
        """
        self._repo = block_repo
        self._audit = audit_repo
        self._projection = AvailabilityProjectionService(slot_duration_minutes=slot_duration_minutes)

    async def list_blocks(
        self,
        *,
        doctor_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> list[AvailabilityBlock]:
        """List active availability blocks for a doctor (dual filter).

        Args:
            doctor_id: Doctor UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.

        Returns:
            List of active AvailabilityBlock entities ordered by creation date.
        """
        return await self._repo.list_blocks(tenant_id=tenant_id, clinic_id=clinic_id, doctor_id=doctor_id)

    async def list_occurrences(
        self,
        *,
        doctor_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        range_start: date,
        range_end: date,
    ) -> list[BlockOccurrence]:
        """Collapse active blocks into block-level occurrences within [range_start, range_end].

        D3-C (03-arch-delta § 4.3): this projection is the paint SSoT the FE
        consumes — client-side expansion (recurrentBlockVisibleInWeek) dies
        (V-D3C-NODUP). REUSES AvailabilityProjectionService.occurrence_dates_in_range
        (no new expansion logic); pattern_summary comes from the shared
        format_recurrence_summary (RN-D3F-1 single source).

        Dual filter (hipaa-lite): tenant_id + clinic_id enforced by the repo.
        Read-only over scheduling metadata (non-PHI) — no audit row (mirrors
        list_blocks).

        Args:
            doctor_id: Doctor UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            range_start: First date of the window (inclusive).
            range_end: Last date of the window (inclusive).

        Returns:
            BlockOccurrence list ordered by (occurrence_date, start_time).

        Raises:
            ValueError: range_end < range_start, or span > 62 days.
        """
        if range_end < range_start:
            raise ValueError("Rango inválido: la fecha final debe ser igual o posterior a la inicial.")
        if (range_end - range_start).days > _MAX_OCCURRENCES_RANGE_DAYS:
            raise ValueError(f"El rango máximo de proyección es de {_MAX_OCCURRENCES_RANGE_DAYS} días.")

        blocks = await self._repo.list_blocks(tenant_id=tenant_id, clinic_id=clinic_id, doctor_id=doctor_id)

        occurrences: list[BlockOccurrence] = []
        for block in blocks:
            summary = format_recurrence_summary(block)
            for occ_date in self._projection.occurrence_dates_in_range(
                block, range_start=range_start, range_end=range_end
            ):
                occurrences.append(
                    BlockOccurrence(
                        block_id=block.id,
                        occurrence_date=occ_date,
                        start_time=block.start_time,
                        end_time=block.end_time,
                        kind=block.kind,
                        freq=block.freq,
                        pattern_summary=summary,
                    )
                )

        occurrences.sort(key=lambda o: (o.occurrence_date, o.start_time, str(o.block_id)))

        logger.info(
            "availability_occurrences_projected",
            doctor_id=str(doctor_id),
            tenant_id=str(tenant_id),
            range_start=range_start.isoformat(),
            range_end=range_end.isoformat(),
            blocks=len(blocks),
            occurrences=len(occurrences),
        )
        return occurrences

    async def create_block(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        user_id: UUID,
        kind: str,
        start_time: time,
        end_time: time,
        # D3-F primary recurrent fields
        days_of_week: list[int] | None = None,
        interval: int = 1,
        # Legacy recurrent fields (backward compat)
        day_of_week: int | None = None,
        freq: str | None = None,
        end_condition_kind: str | None = None,
        end_date: date | None = None,
        occurrences: int | None = None,
        # One-off field
        specific_date: date | None = None,
    ) -> AvailabilityBlock:
        """Create a new availability block and materialize slots.

        Steps:
        1. Build AvailabilityBlock domain entity (domain validation in __post_init__)
        2. Project slots via AvailabilityProjectionService (dateutil.rrule)
        3. Convert ProjectedSlot list -> VitaliaAvailabilitySlotModel list
        4. Persist block + slots transactionally (via repo.create_block)
        5. Write audit log SYNC (doctor.availability_block_created)

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            doctor_id: Doctor UUID.
            user_id: Actor user UUID (for audit log).
            kind: 'recurrent' | 'one_off'.
            start_time: Block start time (UTC).
            end_time: Block end time (UTC).
            days_of_week: Primary D3-F — list of weekday ints 0=Mon..6=Sun.
            interval: Primary D3-F — recurrence interval in weeks (≥1).
            day_of_week: Legacy — 0=Mon..6=Sun (recurrent only).
            freq: Legacy — 'weekly' | 'biweekly' (recurrent only).
            end_condition_kind: 'end_date' | 'occurrences' | 'open_ended' (recurrent only).
            end_date: End date for end_date condition.
            occurrences: Count for occurrences condition.
            specific_date: The specific date for one_off kind.

        Returns:
            Persisted AvailabilityBlock entity.

        Raises:
            ValueError: If domain validation fails (from AvailabilityBlock.__post_init__)
                        or if the block date is in the past.
        """
        # Feature #2 — past block guard
        today = datetime.now(tz=timezone.utc).date()
        if kind == "one_off" and specific_date is not None and specific_date < today:
            raise ValueError("No puedes crear bloques en fechas pasadas.")
        if kind == "recurrent" and end_condition_kind == "end_date" and end_date is not None and end_date < today:
            raise ValueError("La fecha de fin no puede estar en el pasado.")

        # 1. Build domain entity (validates invariants in __post_init__)
        # D3-F precedence: days_of_week (non-empty) wins over legacy day_of_week.
        block = AvailabilityBlock(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            kind=kind,  # type: ignore[arg-type]
            start_time=start_time,
            end_time=end_time,
            days_of_week=days_of_week or [],
            interval=interval,
            day_of_week=day_of_week,
            freq=freq,  # type: ignore[arg-type]
            end_condition_kind=end_condition_kind,  # type: ignore[arg-type]
            end_date=end_date,
            occurrences=occurrences,
            specific_date=specific_date,
        )

        # 2. Project slots (reference_date = today)
        projected_slots = self._projection.project_block(block)

        # 3. Convert projected slots to ORM models
        slot_models = [_projected_slot_to_model(s) for s in projected_slots]

        # 4. Persist block + slots transactionally
        saved = await self._repo.create_block(block, slot_models, tenant_id=tenant_id, clinic_id=clinic_id)

        # 5. Audit log SYNC (HIPAA-lite mandatory)
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.availability_block_created",
                resource_type="availability_block",
                resource_id=saved.id,
            )
        )

        logger.info(
            "availability_block_created",
            block_id=str(saved.id),
            doctor_id=str(doctor_id),
            tenant_id=str(tenant_id),
            kind=kind,
            slots_materialized=len(slot_models),
        )
        return saved

    async def update_block(
        self,
        *,
        block_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        user_id: UUID,
        kind: str,
        start_time: time,
        end_time: time,
        # D3-F primary recurrent fields
        days_of_week: list[int] | None = None,
        interval: int = 1,
        # Legacy recurrent fields (backward compat)
        day_of_week: int | None = None,
        freq: str | None = None,
        end_condition_kind: str | None = None,
        end_date: date | None = None,
        occurrences: int | None = None,
        # One-off field
        specific_date: date | None = None,
    ) -> AvailabilityBlock | None:
        """Edit a block (reproject-future-only invariant).

        Steps:
        1. Get existing block (dual filter — returns None if not found)
        2. Build updated AvailabilityBlock domain entity
        3. Re-project future slots (reference_date = today)
        4. repo.update_block: soft-delete future free slots + insert new slots
        5. No audit write on update (read-only schedule management — only create/delete audited)

        Args:
            days_of_week: Primary D3-F — list of weekday ints 0=Mon..6=Sun.
            interval: Primary D3-F — recurrence interval in weeks (≥1).
            day_of_week: Legacy — 0=Mon..6=Sun (backward compat).
            freq: Legacy — 'weekly' | 'biweekly' (backward compat).

        Returns:
            Updated AvailabilityBlock or None if block not found.
        """
        existing = await self._repo.get_block(block_id, tenant_id=tenant_id, clinic_id=clinic_id)
        if existing is None:
            return None

        # Build updated domain entity
        # D3-F precedence: days_of_week (non-empty) wins over legacy day_of_week.
        updated = AvailabilityBlock(
            id=block_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            kind=kind,  # type: ignore[arg-type]
            start_time=start_time,
            end_time=end_time,
            days_of_week=days_of_week or [],
            interval=interval,
            day_of_week=day_of_week,
            freq=freq,  # type: ignore[arg-type]
            end_condition_kind=end_condition_kind,  # type: ignore[arg-type]
            end_date=end_date,
            occurrences=occurrences,
            specific_date=specific_date,
        )

        # Re-project future slots
        projected_slots = self._projection.project_block(updated)
        slot_models = [_projected_slot_to_model(s) for s in projected_slots]

        # update_block: soft-deletes future free slots + inserts new slots
        saved = await self._repo.update_block(updated, slot_models, tenant_id=tenant_id, clinic_id=clinic_id)

        logger.info(
            "availability_block_updated",
            block_id=str(block_id),
            doctor_id=str(doctor_id),
            tenant_id=str(tenant_id),
            kind=kind,
            new_slots=len(slot_models),
        )
        return saved

    async def delete_block(
        self,
        *,
        block_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
    ) -> tuple[bool, int]:
        """Soft-delete block + retire future non-confirmed slots.

        CRITICAL INVARIANT (delete-block-preserves-confirmed-appointments):
        Slots with has_confirmed_appointment=True are NEVER deleted (SC-1d, SC-3b).

        Steps:
        1. repo.delete_block: retires future free slots, soft-deletes block,
           returns count of preserved (confirmed) slots
        2. Write audit log SYNC (doctor.availability_block_deleted, preserved_appointments=N)

        Returns:
            Tuple (deleted=True, preserved_appointments=N).
        """
        preserved_count = await self._repo.delete_block(block_id, tenant_id=tenant_id, clinic_id=clinic_id)

        # Audit log SYNC (HIPAA-lite mandatory)
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.availability_block_deleted",
                resource_type="availability_block",
                resource_id=block_id,
            )
        )

        logger.info(
            "availability_block_deleted",
            block_id=str(block_id),
            tenant_id=str(tenant_id),
            preserved_appointments=preserved_count,
        )
        return True, preserved_count

    async def count_future_confirmed(
        self,
        *,
        block_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> int:
        """Return count of future confirmed slots for the block (dual filter).

        Delegates to repo — keeps router DDD-clean (no svc._repo access from API layer).
        """
        return await self._repo.count_future_confirmed(block_id, tenant_id=tenant_id, clinic_id=clinic_id)

    async def exclude_occurrence(
        self,
        *,
        block_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        occurrence_date: date,
    ) -> "AvailabilityBlock":
        """Exclude a single occurrence from a recurrent block (scope=occurrence delete).

        Steps:
        1. Get block (dual filter — 404 if not found)
        2. Append occurrence_date to block.excluded_dates (dedup)
        3. Retire FREE slots on that exact date (preserve confirmed)
        4. Persist updated excluded_dates (block stays active — deleted_at stays NULL)
        5. Audit SYNC (doctor.availability_block_occurrence_excluded)

        Confirmed slots (has_confirmed_appointment=True) are NEVER retired.

        Returns:
            Updated AvailabilityBlock entity.
        """
        block = await self._repo.get_block(block_id, tenant_id=tenant_id, clinic_id=clinic_id)
        if block is None:
            raise ValueError("Bloque de disponibilidad no encontrado.")

        # Dedup append
        existing = list(block.excluded_dates or [])
        iso = occurrence_date.isoformat()
        if iso not in existing:
            existing.append(iso)
        block.excluded_dates = existing

        # Retire free slots on that date
        await self._repo.retire_free_slots_on_date(
            block_id,
            slot_date=occurrence_date,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        # Persist excluded_dates
        saved = await self._repo.persist_excluded_dates(
            block_id,
            existing,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        # Audit SYNC
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.availability_block_occurrence_excluded",
                resource_type="availability_block",
                resource_id=block_id,
            )
        )

        logger.info(
            "availability_block_occurrence_excluded",
            block_id=str(block_id),
            tenant_id=str(tenant_id),
            occurrence_date=iso,
        )
        return saved

    async def truncate_from(
        self,
        *,
        block_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        occurrence_date: date,
    ) -> "AvailabilityBlock":
        """Truncate a recurrent block series from occurrence_date onward (scope=this_and_future).

        Steps:
        1. Get block (dual filter — 404 if not found)
        2. Truncate series: set end_condition_kind='end_date', end_date = occurrence_date - 1 day
        3. Retire FREE slots where slot_date >= occurrence_date (preserve confirmed)
        4. Audit SYNC (doctor.availability_block_truncated)

        Confirmed slots (has_confirmed_appointment=True) are NEVER retired.
        Block stays active — deleted_at stays NULL.

        Returns:
            Updated AvailabilityBlock entity.
        """
        from datetime import timedelta  # noqa: PLC0415

        block = await self._repo.get_block(block_id, tenant_id=tenant_id, clinic_id=clinic_id)
        if block is None:
            raise ValueError("Bloque de disponibilidad no encontrado.")

        new_end_date = occurrence_date - timedelta(days=1)

        # Retire free slots from occurrence_date onward
        await self._repo.retire_free_slots_from_date(
            block_id,
            from_date=occurrence_date,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        # Truncate the series
        saved = await self._repo.truncate_block(
            block_id,
            new_end_date=new_end_date,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        # Audit SYNC
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.availability_block_truncated",
                resource_type="availability_block",
                resource_id=block_id,
            )
        )

        logger.info(
            "availability_block_truncated",
            block_id=str(block_id),
            tenant_id=str(tenant_id),
            occurrence_date=occurrence_date.isoformat(),
            new_end_date=new_end_date.isoformat(),
        )
        return saved


# ── Domain ↔ Model helpers ────────────────────────────────────────────────────


def _projected_slot_to_model(slot: ProjectedSlot) -> VitaliaAvailabilitySlotModel:
    """Convert a ProjectedSlot value object to an ORM model."""
    return VitaliaAvailabilitySlotModel(
        id=slot.id,
        tenant_id=slot.tenant_id,
        clinic_id=slot.clinic_id,
        doctor_id=slot.doctor_id,
        block_id=slot.block_id,
        slot_date=slot.slot_date,
        start_ts=slot.start_ts,
        end_ts=slot.end_ts,
        has_confirmed_appointment=slot.has_confirmed_appointment,
    )
