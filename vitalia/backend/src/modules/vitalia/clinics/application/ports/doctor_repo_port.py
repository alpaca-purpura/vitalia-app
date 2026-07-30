# cap: clinics.lisa.doctores
"""DoctorRepoPort — ABC interface for Doctor repository.

Application layer depends on this port, NOT on the concrete implementation.
Enables dependency injection and mock-friendly testing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.modules.vitalia.clinics.domain.doctor import Doctor
from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile


class DoctorRepoPort(ABC):
    """Abstract interface for Doctor data access.

    All methods enforce HIPAA dual filter (tenant_id + clinic_id).
    Concrete implementation: DoctorRepository (infrastructure layer).
    """

    @abstractmethod
    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> Doctor | None:
        """Retrieve a Doctor by ID with dual filter."""
        ...

    @abstractmethod
    async def list_by_filter(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        q: str | None = None,
        specialty: str | None = None,
        active: bool | None = None,
        page: int = 1,
        page_size: int = 24,
    ) -> list[Doctor]:
        """List Doctors with optional filters and pagination."""
        ...

    @abstractmethod
    async def count_by_filter(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        active: bool | None = None,
        specialty: str | None = None,
    ) -> int:
        """Count Doctors matching filters."""
        ...

    @abstractmethod
    async def get_by_dni_hash(
        self,
        dni_hash: str,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> Doctor | None:
        """Look up a Doctor by DNI hash (for uniqueness check)."""
        ...

    @abstractmethod
    async def create(
        self,
        doctor: Doctor,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> Doctor:
        """Persist a new Doctor."""
        ...

    @abstractmethod
    async def update(
        self,
        doctor: Doctor,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> Doctor:
        """Update an existing Doctor."""
        ...

    @abstractmethod
    async def soft_deactivate(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> None:
        """Soft-deactivate a Doctor (active=False, not deleted)."""
        ...

    @abstractmethod
    async def list_public(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> list[Doctor]:
        """List public doctors (visible_en_landing=True AND active=True)."""
        ...

    @abstractmethod
    async def update_public_profile(
        self,
        *,
        doctor_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        public_profile: DoctorPublicProfile,
        bio_generated_at: datetime,
        public_slug: str | None,
    ) -> "Doctor | None":
        """Persist generated public profile, timestamp, and slug.

        bio_generated_at ONLY updated via this method (RN-D3B-4).
        Returns updated Doctor entity or None if not found.
        """
        ...

    @abstractmethod
    async def update_public_profile_sections(
        self,
        *,
        doctor_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        public_profile: DoctorPublicProfile,
    ) -> "Doctor | None":
        """Persist manually-edited public profile sections WITHOUT touching bio_generated_at.

        RN-D3B-4: bio_generated_at is ONLY set by generate-profile, NEVER here.
        Returns updated Doctor entity or None if not found (dual filter miss).
        """
        ...
