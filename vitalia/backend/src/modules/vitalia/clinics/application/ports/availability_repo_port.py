# cap: clinics.lisa.doctores
"""AvailabilityRepoPort — ABC interface for AvailabilityBlock repository.

Application layer depends on this port, NOT on the concrete implementation.
Enables dependency injection and mock-friendly testing.

All methods enforce HIPAA dual filter (tenant_id + clinic_id) even though
availability blocks are not PHI — dual-filter is applied for cross-clinic
isolation consistency (same repo contract as DoctorRepository).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock
from src.modules.vitalia.clinics.infrastructure.models.availability_slot_model import (
    VitaliaAvailabilitySlotModel,
)


class AvailabilityRepoPort(ABC):
    """Abstract interface for AvailabilityBlock + Slot data access.

    Concrete implementation: AvailabilityBlockRepository (infrastructure layer).
    """

    @abstractmethod
    async def list_blocks(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
    ) -> list[AvailabilityBlock]:
        """List active (non-deleted) availability blocks for a doctor."""
        ...

    @abstractmethod
    async def get_block(
        self,
        block_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AvailabilityBlock | None:
        """Get a single block by ID with dual filter."""
        ...

    @abstractmethod
    async def create_block(
        self,
        block: AvailabilityBlock,
        slots: list[VitaliaAvailabilitySlotModel],
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AvailabilityBlock:
        """Persist block + projected slots in a single transaction."""
        ...

    @abstractmethod
    async def update_block(
        self,
        block: AvailabilityBlock,
        new_slots: list[VitaliaAvailabilitySlotModel],
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> AvailabilityBlock:
        """Update block and replace future slots (reproject-future-only).

        Past slots (slot_date < today) are never touched.
        Confirmed future slots (has_confirmed_appointment=True) are preserved.
        """
        ...

    @abstractmethod
    async def delete_block(
        self,
        block_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> int:
        """Soft-delete block; retire future non-confirmed slots.

        Returns: count of preserved slots (has_confirmed_appointment=True).
        """
        ...

    @abstractmethod
    async def count_future_confirmed(
        self,
        block_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> int:
        """Count future slots with confirmed appointments (slot_date >= today)."""
        ...

    @abstractmethod
    async def persist_excluded_dates(
        self,
        block_id: UUID,
        excluded_dates: list[str],
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> "AvailabilityBlock":
        """Persist updated excluded_dates on an active block (scope=occurrence delete).

        Does NOT soft-delete the block — only updates the excluded_dates column.
        Returns the updated block entity.
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def truncate_block(
        self,
        block_id: UUID,
        *,
        new_end_date: date,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> "AvailabilityBlock":
        """Set end_condition_kind='end_date' and end_date=new_end_date (scope=this_and_future).

        Block stays active (deleted_at stays NULL).
        Returns the updated block entity.
        """
        ...

    @abstractmethod
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
        ...
