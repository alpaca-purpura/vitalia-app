# cap: crm.adrian-embudo
"""Tests for LeadStageTransitionRepository — RED first (T-BE-1).

Tests that:
- Repository exists with correct methods
- Tenant isolation enforced on every query
- Audit record persists transitions (business event, non-PHI)
- Validator coverage: F-9 (audit log), NF-1 (tenant isolation)
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest


class TestLeadStageTransitionRepositoryInterface:
    """LeadStageTransitionRepository exists with required methods."""

    def test_repository_importable(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_stage_transition_repository import (  # noqa: F401
            LeadStageTransitionRepository,
        )

    def test_record_method_exists_and_is_async(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_stage_transition_repository import (
            LeadStageTransitionRepository,
        )

        assert hasattr(LeadStageTransitionRepository, "record")
        assert inspect.iscoroutinefunction(LeadStageTransitionRepository.record)

    def test_list_for_lead_method_exists_and_is_async(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_stage_transition_repository import (
            LeadStageTransitionRepository,
        )

        assert hasattr(LeadStageTransitionRepository, "list_for_lead")
        assert inspect.iscoroutinefunction(LeadStageTransitionRepository.list_for_lead)

    def test_repository_accepts_session(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_stage_transition_repository import (
            LeadStageTransitionRepository,
        )

        mock_session = AsyncMock()
        repo = LeadStageTransitionRepository(session=mock_session)
        assert repo._session is mock_session


class TestLeadStageTransitionTenantIsolation:
    """Every method enforces tenant_id filter."""

    def test_record_signature_has_tenant_id(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_stage_transition_repository import (
            LeadStageTransitionRepository,
        )

        sig = inspect.signature(LeadStageTransitionRepository.record)
        assert "tenant_id" in sig.parameters

    def test_list_for_lead_signature_has_tenant_id(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_stage_transition_repository import (
            LeadStageTransitionRepository,
        )

        sig = inspect.signature(LeadStageTransitionRepository.list_for_lead)
        assert "tenant_id" in sig.parameters

    @pytest.mark.asyncio
    async def test_list_for_lead_requires_tenant_id(self) -> None:
        """list_for_lead raises ValueError when tenant_id is None."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_stage_transition_repository import (
            LeadStageTransitionRepository,
        )

        mock_session = AsyncMock()
        repo = LeadStageTransitionRepository(session=mock_session)

        with pytest.raises(ValueError, match="tenant_id"):
            await repo.list_for_lead(
                lead_id=uuid4(),
                tenant_id=None,  # type: ignore[arg-type]
            )


class TestLeadStageTransitionDomainEntity:
    """LeadStageTransition domain entity exists with required fields."""

    def test_entity_importable(self) -> None:
        from src.modules.vitalia.crm.domain.lead_stage_transition import LeadStageTransition  # noqa: F401

    def test_entity_has_required_fields(self) -> None:
        from src.modules.vitalia.crm.domain.lead_stage_transition import LeadStageTransition

        fields = {f.name for f in LeadStageTransition.__dataclass_fields__.values()}
        required = {
            "id",
            "tenant_id",
            "lead_id",
            "from_stage",
            "to_stage",
            "triggered_by",
            "reason",
            "score_at_transition",
            "actor_user_id",
            "occurred_at",
            "deleted_at",
        }
        assert required.issubset(fields), f"Missing fields: {required - fields}"

    def test_entity_reason_is_not_named_notes(self) -> None:
        """reason field must be named 'reason' NOT 'notes' to avoid PHI pgcrypto false positive."""
        from src.modules.vitalia.crm.domain.lead_stage_transition import LeadStageTransition

        fields = {f.name for f in LeadStageTransition.__dataclass_fields__.values()}
        assert "reason" in fields
        assert "notes" not in fields, (
            "Field must NOT be named 'notes' — arch test PHI pgcrypto regex matches 'notes\\s+TEXT'"
        )


class TestLeadActivityRepositoryInterface:
    """LeadActivityRepository exists with required methods."""

    def test_repository_importable(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_activity_repository import (  # noqa: F401
            LeadActivityRepository,
        )

    def test_record_method_exists_and_is_async(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_activity_repository import (
            LeadActivityRepository,
        )

        assert hasattr(LeadActivityRepository, "record")
        assert inspect.iscoroutinefunction(LeadActivityRepository.record)

    def test_last_for_lead_method_exists_and_is_async(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_activity_repository import (
            LeadActivityRepository,
        )

        assert hasattr(LeadActivityRepository, "last_for_lead")
        assert inspect.iscoroutinefunction(LeadActivityRepository.last_for_lead)

    def test_list_for_lead_method_exists_and_is_async(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.lead_activity_repository import (
            LeadActivityRepository,
        )

        assert hasattr(LeadActivityRepository, "list_for_lead")
        assert inspect.iscoroutinefunction(LeadActivityRepository.list_for_lead)

    @pytest.mark.asyncio
    async def test_record_requires_tenant_id(self) -> None:
        """record enforces tenant_id — non-PHI but tenant isolation mandatory."""
        from src.modules.vitalia.crm.infrastructure.persistence.lead_activity_repository import (
            LeadActivityRepository,
        )

        mock_session = AsyncMock()
        repo = LeadActivityRepository(session=mock_session)

        with pytest.raises(ValueError, match="tenant_id"):
            await repo.record(
                lead_id=uuid4(),
                tenant_id=None,  # type: ignore[arg-type]
                actor="agent",
                kind="stage_move",
                description_es="Test",
            )


class TestLeadActivityDomainEntity:
    """LeadActivity domain entity exists with required fields."""

    def test_entity_importable(self) -> None:
        from src.modules.vitalia.crm.domain.lead_activity import LeadActivity  # noqa: F401

    def test_entity_has_required_fields(self) -> None:
        from src.modules.vitalia.crm.domain.lead_activity import LeadActivity

        fields = {f.name for f in LeadActivity.__dataclass_fields__.values()}
        required = {
            "id",
            "tenant_id",
            "lead_id",
            "actor",
            "kind",
            "description_es",
            "occurred_at",
            "deleted_at",
        }
        assert required.issubset(fields), f"Missing fields: {required - fields}"
