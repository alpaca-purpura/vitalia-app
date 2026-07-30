# cap: clinics.lisa.doctores
"""AvailabilityBlockRepository — dual-filter implementation for availability blocks.

HIPAA-lite compliance:
  - Inherits CompoundScopeRepositoryBase (engine — post lift 2026-05-20)
    with scope_field="clinic_id" for cross-clinic isolation
  - All queries: deleted_at IS NULL, tenant_id, clinic_id
  - No PII columns — availability data is scheduling metadata, not PHI
    (but dual-filter applied for consistency with DoctorRepository contract)

Transactional block + slots creation: block and projected slots are
persisted in a single session flush (caller controls commit boundary).

delete_block preserves slots with has_confirmed_appointment=True (SC-1d, SC-3b).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

import structlog
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock
from src.modules.vitalia.clinics.infrastructure.models.availability_block_model import (
    VitaliaAvailabilityBlockModel,
)
from src.modules.vitalia.clinics.infrastructure.models.availability_slot_model import (
    VitaliaAvailabilitySlotModel,
)

logger = structlog.get_logger()


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(tz=timezone.utc)


def _today_utc() -> date:
    """Return today's UTC date."""
    return datetime.now(tz=timezone.utc).date()


class AvailabilityBlockRepository(CompoundScopeRepositoryBase[VitaliaAvailabilityBlockModel, UUID]):
    """Async repository for AvailabilityBlock + VitaliaAvailabilitySlotModel entities.

    Enforces:
      - Cross-clinic isolation (tenant_id + clinic_id) via CompoundScopeRepositoryBase
      - Soft deletes only (deleted_at IS NULL on reads)
      - delete_block preserves slots with confirmed appointments (SC-1d, SC-3b)
    """

    MODEL = VitaliaAvailabilityBlockModel

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async session.

        Args:
            session: SQLAlchemy async session (caller owns commit boundary).
        """
        super().__init__(session=session, scope_field="clinic_id")

    def validate_dual_filter(
        self,
        *,
        tenant_id: UUID | None,
        clinic_id: UUID | None,
    ) -> None:
        """Validate dual filter (tenant_id + clinic_id) — consistent with DoctorRepository.

        Raises:
            ValueError: If tenant_id is None.
            MissingClinicFilterError: If clinic_id is None.
        """
        from src.modules.vitalia._shared.repositories.phi_repository import (  # noqa: PLC0415
            MissingClinicFilterError,
        )

        if tenant_id is None:
            raise ValueError("Repository requires tenant_id — never bypass root tenant isolation")
        if clinic_id is None:
            logger.warning(
                "dual_filter_violation",
                repository=self.__class__.__name__,
                reason="clinic_id missing from availability query",
            )
            raise MissingClinicFilterError()

    # ── Abstract method implementations ─────────────────────────────────────

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AvailabilityBlock | None:
        """Get a single block by ID with dual filter.

        Returns None if not found or belongs to different tenant/clinic.
        """
        return await self.get_block(entity_id, tenant_id=tenant_id, clinic_id=clinic_id)

    # ── Port methods ──────────────────────────────────────────────────────────

    async def list_blocks(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
    ) -> list[AvailabilityBlock]:
        """List active blocks for a doctor with dual filter."""
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = (
            select(VitaliaAvailabilityBlockModel)
            .where(
                VitaliaAvailabilityBlockModel.tenant_id == tenant_id,
                VitaliaAvailabilityBlockModel.clinic_id == clinic_id,
                VitaliaAvailabilityBlockModel.doctor_id == doctor_id,
                VitaliaAvailabilityBlockModel.deleted_at.is_(None),
            )
            .order_by(VitaliaAvailabilityBlockModel.created_at)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [_model_to_block(m) for m in models]

    async def get_block(
        self,
        block_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AvailabilityBlock | None:
        """Get a block by ID with dual filter."""
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = select(VitaliaAvailabilityBlockModel).where(
            VitaliaAvailabilityBlockModel.id == block_id,
            VitaliaAvailabilityBlockModel.tenant_id == tenant_id,
            VitaliaAvailabilityBlockModel.clinic_id == clinic_id,
            VitaliaAvailabilityBlockModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _model_to_block(model) if model is not None else None

    async def create_block(
        self,
        block: AvailabilityBlock,
        slots: list[VitaliaAvailabilitySlotModel],
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AvailabilityBlock:
        """Persist block + projected slots in a single transaction.

        Block and all slots are flushed together; caller commits the session.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        block_model = _block_to_model(block)
        self._session.add(block_model)
        for slot in slots:
            self._session.add(slot)
        await self._session.flush()

        logger.info(
            "availability_block_created",
            block_id=str(block.id),
            doctor_id=str(block.doctor_id),
            tenant_id=str(tenant_id),
            kind=block.kind,
            slots_materialized=len(slots),
        )
        return block

    async def update_block(
        self,
        block: AvailabilityBlock,
        new_slots: list[VitaliaAvailabilitySlotModel],
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AvailabilityBlock:
        """Update block and replace future non-confirmed slots (reproject-future-only).

        Steps:
        1. Update block fields (kind, times, freq, end_condition, etc.)
        2. Soft-delete future slots with has_confirmed_appointment=False
        3. Insert new_slots (projected from updated block, reference_date=today)
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)
        today = _today_utc()

        # Update block metadata (D3-F: include days_of_week + interval)
        update_stmt = (
            update(VitaliaAvailabilityBlockModel)
            .where(
                VitaliaAvailabilityBlockModel.id == block.id,
                VitaliaAvailabilityBlockModel.tenant_id == tenant_id,
                VitaliaAvailabilityBlockModel.clinic_id == clinic_id,
                VitaliaAvailabilityBlockModel.deleted_at.is_(None),
            )
            .values(
                kind=block.kind,
                days_of_week=block.days_of_week or None,
                interval=block.interval,
                day_of_week=block.day_of_week,
                start_time=block.start_time,
                end_time=block.end_time,
                freq=block.freq,
                end_condition_kind=block.end_condition_kind,
                end_date=block.end_date,
                occurrences=block.occurrences,
                specific_date=block.specific_date,
                updated_at=_utc_now(),
            )
        )
        await self._session.execute(update_stmt)

        # Soft-delete future free slots (dual-filter: tenant_id + clinic_id)
        delete_future_free_stmt = (
            update(VitaliaAvailabilitySlotModel)
            .where(
                VitaliaAvailabilitySlotModel.block_id == block.id,
                VitaliaAvailabilitySlotModel.tenant_id == tenant_id,
                VitaliaAvailabilitySlotModel.clinic_id == clinic_id,
                VitaliaAvailabilitySlotModel.slot_date >= today,
                VitaliaAvailabilitySlotModel.has_confirmed_appointment.is_(False),
                VitaliaAvailabilitySlotModel.deleted_at.is_(None),
            )
            .values(deleted_at=_utc_now())
        )
        await self._session.execute(delete_future_free_stmt)

        # Insert new projected slots
        for slot in new_slots:
            self._session.add(slot)
        await self._session.flush()

        logger.info(
            "availability_block_updated",
            block_id=str(block.id),
            tenant_id=str(tenant_id),
            new_slots=len(new_slots),
        )
        return block

    async def delete_block(
        self,
        block_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> int:
        """Soft-delete block + retire future non-confirmed slots.

        Returns: count of slots preserved (has_confirmed_appointment=True).
        SC-1d / SC-3b: confirmed slots are never deleted.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)
        today = _today_utc()

        # Count confirmed future slots before deletion
        confirmed_count = await self.count_future_confirmed(block_id, tenant_id=tenant_id, clinic_id=clinic_id)

        # Soft-delete future non-confirmed slots (dual-filter: tenant_id + clinic_id)
        delete_free_stmt = (
            update(VitaliaAvailabilitySlotModel)
            .where(
                VitaliaAvailabilitySlotModel.block_id == block_id,
                VitaliaAvailabilitySlotModel.tenant_id == tenant_id,
                VitaliaAvailabilitySlotModel.clinic_id == clinic_id,
                VitaliaAvailabilitySlotModel.slot_date >= today,
                VitaliaAvailabilitySlotModel.has_confirmed_appointment.is_(False),
                VitaliaAvailabilitySlotModel.deleted_at.is_(None),
            )
            .values(deleted_at=_utc_now())
        )
        await self._session.execute(delete_free_stmt)

        # Soft-delete the block itself
        delete_block_stmt = (
            update(VitaliaAvailabilityBlockModel)
            .where(
                VitaliaAvailabilityBlockModel.id == block_id,
                VitaliaAvailabilityBlockModel.tenant_id == tenant_id,
                VitaliaAvailabilityBlockModel.clinic_id == clinic_id,
                VitaliaAvailabilityBlockModel.deleted_at.is_(None),
            )
            .values(deleted_at=_utc_now())
        )
        await self._session.execute(delete_block_stmt)
        await self._session.flush()

        logger.info(
            "availability_block_deleted",
            block_id=str(block_id),
            tenant_id=str(tenant_id),
            preserved_appointments=confirmed_count,
        )
        return confirmed_count

    async def count_future_confirmed(
        self,
        block_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> int:
        """Count future slots with confirmed appointments."""
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)
        today = _today_utc()

        from sqlalchemy import func  # noqa: PLC0415

        stmt = (
            select(func.count())
            .select_from(VitaliaAvailabilitySlotModel)
            .where(
                VitaliaAvailabilitySlotModel.block_id == block_id,
                VitaliaAvailabilitySlotModel.tenant_id == tenant_id,
                VitaliaAvailabilitySlotModel.slot_date >= today,
                VitaliaAvailabilitySlotModel.has_confirmed_appointment.is_(True),
                VitaliaAvailabilitySlotModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar() or 0)

    async def persist_excluded_dates(
        self,
        block_id: UUID,
        excluded_dates: list[str],
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AvailabilityBlock:
        """Persist updated excluded_dates on an active block (scope=occurrence delete).

        Does NOT soft-delete the block — only updates excluded_dates column.
        Returns the updated block entity.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = (
            update(VitaliaAvailabilityBlockModel)
            .where(
                VitaliaAvailabilityBlockModel.id == block_id,
                VitaliaAvailabilityBlockModel.tenant_id == tenant_id,
                VitaliaAvailabilityBlockModel.clinic_id == clinic_id,
                VitaliaAvailabilityBlockModel.deleted_at.is_(None),
            )
            .values(excluded_dates=excluded_dates or None, updated_at=_utc_now())
        )
        await self._session.execute(stmt)
        await self._session.flush()

        updated = await self.get_block(block_id, tenant_id=tenant_id, clinic_id=clinic_id)
        assert updated is not None, "Block disappeared after persist_excluded_dates"

        logger.info(
            "availability_block_excluded_dates_persisted",
            block_id=str(block_id),
            excluded_count=len(excluded_dates),
        )
        return updated

    async def retire_free_slots_on_date(
        self,
        block_id: UUID,
        *,
        slot_date: date,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> int:
        """Soft-delete FREE slots for block on a specific date (scope=occurrence).

        Slots with has_confirmed_appointment=True are NEVER touched.
        Returns count of slots retired.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        from sqlalchemy import func  # noqa: PLC0415

        # Count before retiring
        count_stmt = (
            select(func.count())
            .select_from(VitaliaAvailabilitySlotModel)
            .where(
                VitaliaAvailabilitySlotModel.block_id == block_id,
                VitaliaAvailabilitySlotModel.tenant_id == tenant_id,
                VitaliaAvailabilitySlotModel.clinic_id == clinic_id,
                VitaliaAvailabilitySlotModel.slot_date == slot_date,
                VitaliaAvailabilitySlotModel.has_confirmed_appointment.is_(False),
                VitaliaAvailabilitySlotModel.deleted_at.is_(None),
            )
        )
        count_result = await self._session.execute(count_stmt)
        retire_count = int(count_result.scalar() or 0)

        retire_stmt = (
            update(VitaliaAvailabilitySlotModel)
            .where(
                VitaliaAvailabilitySlotModel.block_id == block_id,
                VitaliaAvailabilitySlotModel.tenant_id == tenant_id,
                VitaliaAvailabilitySlotModel.clinic_id == clinic_id,
                VitaliaAvailabilitySlotModel.slot_date == slot_date,
                VitaliaAvailabilitySlotModel.has_confirmed_appointment.is_(False),
                VitaliaAvailabilitySlotModel.deleted_at.is_(None),
            )
            .values(deleted_at=_utc_now())
        )
        await self._session.execute(retire_stmt)
        await self._session.flush()

        logger.info(
            "availability_slots_retired_on_date",
            block_id=str(block_id),
            slot_date=slot_date.isoformat(),
            retired_count=retire_count,
        )
        return retire_count

    async def truncate_block(
        self,
        block_id: UUID,
        *,
        new_end_date: date,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AvailabilityBlock:
        """Set end_condition_kind='end_date' and end_date=new_end_date (scope=this_and_future).

        Block stays active (deleted_at stays NULL).
        Returns the updated block entity.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = (
            update(VitaliaAvailabilityBlockModel)
            .where(
                VitaliaAvailabilityBlockModel.id == block_id,
                VitaliaAvailabilityBlockModel.tenant_id == tenant_id,
                VitaliaAvailabilityBlockModel.clinic_id == clinic_id,
                VitaliaAvailabilityBlockModel.deleted_at.is_(None),
            )
            .values(
                end_condition_kind="end_date",
                end_date=new_end_date,
                updated_at=_utc_now(),
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

        updated = await self.get_block(block_id, tenant_id=tenant_id, clinic_id=clinic_id)
        assert updated is not None, "Block disappeared after truncate_block"

        logger.info(
            "availability_block_truncated",
            block_id=str(block_id),
            new_end_date=new_end_date.isoformat(),
        )
        return updated

    async def retire_free_slots_from_date(
        self,
        block_id: UUID,
        *,
        from_date: date,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> int:
        """Soft-delete FREE slots for block where slot_date >= from_date (scope=this_and_future).

        Slots with has_confirmed_appointment=True are NEVER touched.
        Returns count of slots retired.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        from sqlalchemy import func  # noqa: PLC0415

        count_stmt = (
            select(func.count())
            .select_from(VitaliaAvailabilitySlotModel)
            .where(
                VitaliaAvailabilitySlotModel.block_id == block_id,
                VitaliaAvailabilitySlotModel.tenant_id == tenant_id,
                VitaliaAvailabilitySlotModel.clinic_id == clinic_id,
                VitaliaAvailabilitySlotModel.slot_date >= from_date,
                VitaliaAvailabilitySlotModel.has_confirmed_appointment.is_(False),
                VitaliaAvailabilitySlotModel.deleted_at.is_(None),
            )
        )
        count_result = await self._session.execute(count_stmt)
        retire_count = int(count_result.scalar() or 0)

        retire_stmt = (
            update(VitaliaAvailabilitySlotModel)
            .where(
                VitaliaAvailabilitySlotModel.block_id == block_id,
                VitaliaAvailabilitySlotModel.tenant_id == tenant_id,
                VitaliaAvailabilitySlotModel.clinic_id == clinic_id,
                VitaliaAvailabilitySlotModel.slot_date >= from_date,
                VitaliaAvailabilitySlotModel.has_confirmed_appointment.is_(False),
                VitaliaAvailabilitySlotModel.deleted_at.is_(None),
            )
            .values(deleted_at=_utc_now())
        )
        await self._session.execute(retire_stmt)
        await self._session.flush()

        logger.info(
            "availability_slots_retired_from_date",
            block_id=str(block_id),
            from_date=from_date.isoformat(),
            retired_count=retire_count,
        )
        return retire_count


# ── Domain ↔ Model mappers ────────────────────────────────────────────────────


def _model_to_block(model: VitaliaAvailabilityBlockModel) -> AvailabilityBlock:
    """Map ORM model to domain entity.

    D3-F: pass days_of_week + interval from model if present (post-042 migrated rows),
    else pass legacy day_of_week + freq (pre-migration rows; domain __post_init__
    will backfill days_of_week from day_of_week).
    """
    return AvailabilityBlock(
        id=model.id,
        tenant_id=model.tenant_id,
        clinic_id=model.clinic_id,
        doctor_id=model.doctor_id,
        kind=model.kind,  # type: ignore[arg-type]
        start_time=model.start_time,
        end_time=model.end_time,
        days_of_week=list(model.days_of_week) if model.days_of_week else [],
        interval=model.interval if model.interval is not None else 1,
        day_of_week=model.day_of_week,
        freq=model.freq,  # type: ignore[arg-type]
        end_condition_kind=model.end_condition_kind,  # type: ignore[arg-type]
        end_date=model.end_date,
        occurrences=model.occurrences,
        specific_date=model.specific_date,
        excluded_dates=list(model.excluded_dates) if model.excluded_dates else [],
        created_at=model.created_at,
        updated_at=model.updated_at or model.created_at,
        deleted_at=model.deleted_at,
    )


def _block_to_model(block: AvailabilityBlock) -> VitaliaAvailabilityBlockModel:
    """Map domain entity to ORM model (for INSERT).

    D3-F: persist days_of_week + interval alongside legacy day_of_week + freq.
    """
    return VitaliaAvailabilityBlockModel(
        id=block.id,
        tenant_id=block.tenant_id,
        clinic_id=block.clinic_id,
        doctor_id=block.doctor_id,
        kind=block.kind,
        days_of_week=block.days_of_week or None,
        interval=block.interval,
        day_of_week=block.day_of_week,
        start_time=block.start_time,
        end_time=block.end_time,
        freq=block.freq,
        end_condition_kind=block.end_condition_kind,
        end_date=block.end_date,
        occurrences=block.occurrences,
        specific_date=block.specific_date,
        excluded_dates=block.excluded_dates or None,
    )
