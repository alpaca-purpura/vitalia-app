# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""TrustSignalRepository ABC — tenant trust signals (certifications/authority).

NO PhiRepositoryBase — owner config, not PHI.
Single tenant_id filter mandatory.

downstream-regression-na: brand-local repo ABC vitalia
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.vitalia.brand_studio.domain.trust_signal import TrustSignal


class TrustSignalRepository(ABC):
    """Abstract repository for trust signals — tenant certifications/authority.

    NO PhiRepositoryBase (not PHI — owner config per §8.1 hipaa-lite overlay).
    Single tenant_id filter.
    """

    @abstractmethod
    async def list_for_tenant(self, *, tenant_id: UUID) -> list[TrustSignal]:
        """Return all active trust signals for a tenant.

        Args:
            tenant_id: Tenant UUID — root isolation.

        Returns:
            List of active TrustSignal entities (empty if none).
        """
        ...

    @abstractmethod
    async def create(self, signal: TrustSignal) -> TrustSignal:
        """Persist a new trust signal.

        Args:
            signal: Domain entity to persist.

        Returns:
            Persisted entity with generated ID and timestamps.
        """
        ...

    @abstractmethod
    async def soft_delete(
        self,
        signal_id: UUID,
        *,
        tenant_id: UUID,
    ) -> None:
        """Soft-delete a trust signal (set deleted_at).

        Args:
            signal_id: Trust signal UUID.
            tenant_id: Tenant UUID — enforces ownership.
        """
        ...

    @abstractmethod
    async def get_by_id(
        self,
        signal_id: UUID,
        *,
        tenant_id: UUID,
    ) -> TrustSignal | None:
        """Retrieve trust signal by ID and tenant.

        Args:
            signal_id: Trust signal UUID.
            tenant_id: Tenant UUID — root isolation.

        Returns:
            TrustSignal or None if not found.
        """
        ...
