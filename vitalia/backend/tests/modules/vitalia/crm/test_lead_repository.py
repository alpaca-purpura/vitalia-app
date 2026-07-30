"""Tests for LeadRepository — single tenant_id filter (Lead is not PHI).

TDD: RED tests defined before implementation (T-infra-9).

downstream-regression-na: brand-local CRM lead repo tests
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.vitalia._shared.repositories.phi_repository import PhiRepositoryBase


class TestLeadRepositoryStructure:
    """LeadRepository is NOT a PHI repo — single tenant_id filter only."""

    def test_lead_repository_is_not_phi_repository(self) -> None:
        """Lead is not PHI — LeadRepository should NOT inherit PhiRepositoryBase."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        assert not issubclass(LeadRepository, PhiRepositoryBase), (
            "LeadRepository must NOT inherit PhiRepositoryBase — "
            "Lead entity is not PHI per 03-arch-be.md § T-infra-9 scope."
        )

    def test_lead_repository_has_get_by_id(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        assert hasattr(LeadRepository, "get_by_id")
        assert inspect.iscoroutinefunction(LeadRepository.get_by_id)

    def test_lead_repository_accepts_session(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        mock_session = AsyncMock()
        repo = LeadRepository(session=mock_session)
        assert repo._session is mock_session


class TestLeadRepositoryTenantFilter:
    """LeadRepository enforces tenant_id filter."""

    def test_get_by_id_raises_without_tenant_id(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        mock_session = AsyncMock()
        repo = LeadRepository(session=mock_session)

        with pytest.raises(ValueError, match="tenant_id"):
            import asyncio

            # asyncio.run (no get_event_loop): py3.12 RuntimeError sin loop corriente
            asyncio.run(
                repo.get_by_id(entity_id=uuid4(), tenant_id=None)  # type: ignore[arg-type]
            )
