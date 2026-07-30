# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""ProhibitedPhraseRepository ABC — tenant-scoped seeds + overrides.

NO PhiRepositoryBase — this is owner config (not PHI).
Single tenant_id filter mandatory.

downstream-regression-na: brand-local repo ABC vitalia
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.vitalia.brand_studio.domain.prohibited_phrase import ProhibitedPhrase


class ProhibitedPhraseRepository(ABC):
    """Abstract repository for prohibited phrases — tenant-scoped seeds + overrides.

    NO PhiRepositoryBase (not PHI — owner config per §8.1 hipaa-lite overlay).
    Single tenant_id filter. Seed defaults have tenant_id=NULL.
    """

    @abstractmethod
    async def list_for_tenant(
        self,
        *,
        tenant_id: UUID,
        country: str | None = None,
    ) -> list[ProhibitedPhrase]:
        """Return seed defaults (tenant_id IS NULL) + tenant overrides merged.

        Ordering: seeds first, tenant overrides after. Country filter applies
        to both seeds and overrides. None = global only (no country filter).

        Args:
            tenant_id: Tenant UUID — for tenant override lookup.
            country: ISO 3166-1 alpha-2 country code or None for global only.

        Returns:
            Combined list of seed defaults + tenant overrides (active only).
        """
        ...

    @abstractmethod
    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
    ) -> ProhibitedPhrase | None:
        """Retrieve a prohibited phrase by ID.

        Returns seed phrases (tenant_id IS NULL) OR tenant overrides matching tenant_id.

        Args:
            entity_id: Phrase UUID.
            tenant_id: Tenant UUID for ownership check.

        Returns:
            ProhibitedPhrase or None if not found.
        """
        ...

    @abstractmethod
    async def create(self, phrase: ProhibitedPhrase) -> ProhibitedPhrase:
        """Persist a new prohibited phrase.

        Args:
            phrase: Domain entity to persist.

        Returns:
            Persisted entity with generated ID and timestamps.
        """
        ...

    @abstractmethod
    async def soft_delete(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
    ) -> None:
        """Soft-delete a prohibited phrase (set deleted_at).

        Only deletes tenant overrides (tenant_id = tenant_id param).
        Seed defaults (tenant_id IS NULL) cannot be deleted via this method.

        Args:
            entity_id: Phrase UUID.
            tenant_id: Tenant UUID — enforces ownership (no cross-tenant delete).
        """
        ...
