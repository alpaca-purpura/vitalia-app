# cap: __shared__
# story-origin: TBD
"""PHI Repository base class — dual filter enforcement.

Every repository that accesses PHI (Protected Health Information) MUST
inherit from PhiRepositoryBase and call validate_dual_filter() in every
query method.

Dual filter rule (vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo):
  - tenant_id: root isolation per .claude/rules/tenant-isolation.md
  - clinic_id: second mandatory filter for vitalia PHI queries

Usage:
    class PatientRepository(PhiRepositoryBase):
        async def get_by_id(
            self, entity_id: UUID, *, tenant_id: UUID, clinic_id: UUID
        ) -> Patient | None:
            self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)
            stmt = select(PatientModel).where(
                PatientModel.tenant_id == tenant_id,
                PatientModel.clinic_id == clinic_id,
                PatientModel.id == entity_id,
                PatientModel.deleted_at.is_(None),
            )
            ...

downstream-regression-na: brand-local base class for vitalia PHI repos
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

import structlog

logger = structlog.get_logger()


class MissingClinicFilterError(Exception):
    """Raised when a PHI repository query omits the required clinic_id filter.

    HIPAA-lite dual-filter violation: all PHI queries MUST include BOTH
    tenant_id AND clinic_id. Omitting clinic_id risks cross-clinic data leak
    within the same tenant.
    """

    def __init__(self, message: str | None = None) -> None:
        default = (
            "PHI repository query missing clinic_id filter. "
            "All PHI queries MUST include both tenant_id AND clinic_id "
            "(vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo). "
            "Skip dual filter 'because single-tenant clinic' is PROHIBITED."
        )
        super().__init__(message or default)


class PhiRepositoryBase(ABC):
    """Abstract base for all PHI repositories in Vitalia.

    Enforces the HIPAA-lite dual filter contract:
      1. tenant_id — root multitenant isolation
      2. clinic_id — second filter preventing cross-clinic PHI leak

    Subclasses MUST:
      - Accept tenant_id: UUID and clinic_id: UUID in every method
      - Call self.validate_dual_filter(tenant_id=..., clinic_id=...) at the top
        of every method that executes a DB query
      - Never return PHI data without both filters applied

    Architecture gate:
      vitalia/backend/tests/architecture/test_phi_dual_filter.py
    """

    def validate_dual_filter(
        self,
        *,
        tenant_id: UUID | None,
        clinic_id: UUID | None,
    ) -> None:
        """Validate that both tenant_id and clinic_id are present.

        Raises MissingClinicFilterError if clinic_id is None.
        Raises ValueError if tenant_id is None.

        Args:
            tenant_id: The tenant UUID for root isolation.
            clinic_id: The clinic UUID for HIPAA-lite dual filter.

        Raises:
            ValueError: If tenant_id is None.
            MissingClinicFilterError: If clinic_id is None.
        """
        if tenant_id is None:
            raise ValueError(
                "PHI repository requires tenant_id — never bypass root tenant isolation (tenant-isolation.md)"
            )
        if clinic_id is None:
            logger.warning(
                "phi_dual_filter_violation",
                repository=self.__class__.__name__,
                reason="clinic_id missing from PHI query",
            )
            raise MissingClinicFilterError()

    @abstractmethod
    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> object | None:
        """Retrieve a PHI entity by its ID.

        Both tenant_id and clinic_id MUST be applied in the query.

        Args:
            entity_id: Primary key of the entity.
            tenant_id: Tenant UUID (root isolation).
            clinic_id: Clinic UUID (HIPAA-lite dual filter).

        Returns:
            The domain entity or None if not found / not accessible.
        """
        ...

    @abstractmethod
    async def list_by_filter(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        **filters: object,
    ) -> list[object]:
        """List PHI entities matching the given filters.

        Both tenant_id and clinic_id MUST be applied in the query.

        Args:
            tenant_id: Tenant UUID (root isolation).
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            **filters: Additional domain-specific filter criteria.

        Returns:
            List of matching domain entities (empty list if none found).
        """
        ...
