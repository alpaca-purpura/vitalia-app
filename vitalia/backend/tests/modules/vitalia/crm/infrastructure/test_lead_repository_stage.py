# cap: crm.adrian-embudo
"""Tests for LeadRepository stage/funnel extensions — RED first (T-BE-1).

Tests the optimistic lock update_stage method and list_for_board sort.
Validator coverage: NF-1 (optimistic lock / SC-5), NF-6 (board sort RN-17).
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


class TestLeadRepositoryStageInterface:
    """LeadRepository has the new funnel methods."""

    def test_update_stage_method_exists(self) -> None:
        """update_stage method must be async."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        assert hasattr(LeadRepository, "update_stage")
        assert inspect.iscoroutinefunction(LeadRepository.update_stage)

    def test_list_for_board_method_exists(self) -> None:
        """list_for_board method must be async."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        assert hasattr(LeadRepository, "list_for_board")
        assert inspect.iscoroutinefunction(LeadRepository.list_for_board)

    def test_freeze_method_exists(self) -> None:
        """freeze method must be async."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        assert hasattr(LeadRepository, "freeze")
        assert inspect.iscoroutinefunction(LeadRepository.freeze)

    def test_reactivate_method_exists(self) -> None:
        """reactivate method must be async."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        assert hasattr(LeadRepository, "reactivate")
        assert inspect.iscoroutinefunction(LeadRepository.reactivate)


class TestLeadRepositoryUpdateStageSignature:
    """update_stage must accept the optimistic lock parameters."""

    def test_update_stage_signature_has_expected_version(self) -> None:
        """update_stage must accept expected_version for optimistic locking."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        sig = inspect.signature(LeadRepository.update_stage)
        params = sig.parameters
        assert "expected_version" in params, (
            "update_stage must accept expected_version param for optimistic lock (SC-5)"
        )

    def test_update_stage_signature_has_to_stage(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        sig = inspect.signature(LeadRepository.update_stage)
        assert "to_stage" in sig.parameters

    def test_update_stage_signature_has_tenant_id(self) -> None:
        """update_stage requires tenant_id (tenant isolation — every method)."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        sig = inspect.signature(LeadRepository.update_stage)
        assert "tenant_id" in sig.parameters


class TestLeadRepositoryOptimisticLock:
    """Optimistic lock raises StaleStateError when version mismatch (SC-5)."""

    @pytest.mark.asyncio
    async def test_update_stage_version_mismatch_raises_stale_error(self) -> None:
        """When rowcount == 0 (version mismatch), StaleStateError is raised."""
        from src.modules.vitalia.crm.domain.exceptions import StaleStateError
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        mock_session = AsyncMock()
        # Simulate 0 rows updated (version mismatch)
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        repo = LeadRepository(session=mock_session)

        with pytest.raises(StaleStateError):
            await repo.update_stage(
                lead_id=uuid4(),
                tenant_id=uuid4(),
                to_stage="calificando",
                expected_version=1,
                score=50,
                actor_user_id=None,
            )

    @pytest.mark.asyncio
    async def test_update_stage_requires_tenant_id(self) -> None:
        """update_stage enforces tenant_id — never bypass isolation."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        mock_session = AsyncMock()
        repo = LeadRepository(session=mock_session)

        with pytest.raises((ValueError, TypeError)):
            await repo.update_stage(
                lead_id=uuid4(),
                tenant_id=None,  # type: ignore[arg-type]
                to_stage="calificando",
                expected_version=1,
                score=50,
                actor_user_id=None,
            )


class TestLeadRepositoryBoardSort:
    """list_for_board returns leads ordered by stage_entered_at ASC (oldest first = RN-17)."""

    def test_list_for_board_signature_has_sort_param(self) -> None:
        """list_for_board accepts sort parameter for RN-17 sort modes."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        sig = inspect.signature(LeadRepository.list_for_board)
        # sort parameter (default stage_age_desc = ORDER BY stage_entered_at ASC — oldest first)
        assert "sort" in sig.parameters

    def test_list_for_board_signature_has_tenant_id(self) -> None:
        """list_for_board requires tenant_id — tenant isolation mandatory."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        sig = inspect.signature(LeadRepository.list_for_board)
        assert "tenant_id" in sig.parameters

    def test_list_for_board_signature_has_stage_filter(self) -> None:
        """list_for_board accepts stage_filter to scope to HOT_BOARD_STAGES."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
            LeadRepository,
        )

        sig = inspect.signature(LeadRepository.list_for_board)
        assert "stage_filter" in sig.parameters
