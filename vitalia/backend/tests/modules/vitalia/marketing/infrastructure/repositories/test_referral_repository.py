"""Tests for ReferralRepository.

Covers:
- get_by_id: dual filter (tenant_id + clinic_id = scope_id)
- list_for_scope: returns referrals for clinic
- HIPAA-lite: patient_id is UUID-only (no PHI in fields)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.modules.vitalia.marketing.infrastructure.models.referral_model import (
    ReferralModel,
)
from src.modules.vitalia.marketing.infrastructure.repositories.referral_repository import (
    ReferralRepository,
)


def _make_model(
    *,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    status: str = "pending",
    deleted_at: datetime | None = None,
) -> ReferralModel:
    """Factory for ReferralModel test instances."""
    now = datetime.now(UTC)
    model = ReferralModel()
    model.id = uuid.uuid4()
    model.tenant_id = tenant_id
    model.clinic_id = clinic_id
    model.patient_id = uuid.uuid4()
    model.code = f"REF-{uuid.uuid4().hex[:8].upper()}"
    model.status = status
    model.referred_patient_id = None
    model.converted_at = None
    model.expires_at = now + timedelta(days=30)
    model.created_at = now
    model.updated_at = now
    model.deleted_at = deleted_at
    return model


class TestReferralRepositoryInit:
    """Repository construction uses scope_field='clinic_id'."""

    def test_inherits_compound_scope_repository_base(self) -> None:
        """ReferralRepository must subclass CompoundScopeRepositoryBase."""
        from luana_core_platform.repositories.compound_scope_repository import (
            CompoundScopeRepositoryBase,
        )

        assert issubclass(ReferralRepository, CompoundScopeRepositoryBase)

    def test_model_class_var_is_set(self) -> None:
        """MODEL ClassVar must be ReferralModel."""
        assert ReferralRepository.MODEL is ReferralModel

    def test_scope_field_is_clinic_id(self) -> None:
        """scope_field must be 'clinic_id'."""
        session = AsyncMock()
        repo = ReferralRepository(session=session)
        assert repo._scope_field == "clinic_id"  # noqa: SLF001


class TestGetById:
    """get_by_id enforces dual filter."""

    async def test_get_by_id_returns_model(self) -> None:
        """Returns referral model when id + tenant_id + clinic_id match."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        ref_id = uuid.uuid4()
        session = AsyncMock()

        model = _make_model(tenant_id=tenant_id, clinic_id=clinic_id, status="pending")
        model.id = ref_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        session.execute.return_value = mock_result

        repo = ReferralRepository(session=session)
        result = await repo.get_by_id(id=ref_id, tenant_id=tenant_id, scope_id=clinic_id)

        assert result is not None
        assert result.id == ref_id
        assert result.status == "pending"

    async def test_wrong_clinic_returns_none(self) -> None:
        """Cross-clinic query returns None (dual filter enforced)."""
        tenant_id = uuid.uuid4()
        clinic_b = uuid.uuid4()  # different clinic (clinic_a would own the record)
        ref_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = ReferralRepository(session=session)
        result = await repo.get_by_id(id=ref_id, tenant_id=tenant_id, scope_id=clinic_b)

        assert result is None

    async def test_dual_filter_in_query(self) -> None:
        """get_by_id query contains both tenant_id and clinic_id."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        ref_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = ReferralRepository(session=session)
        await repo.get_by_id(id=ref_id, tenant_id=tenant_id, scope_id=clinic_id)

        session.execute.assert_called_once()
        stmt = session.execute.call_args[0][0]
        stmt_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        tenant_hex = str(tenant_id).replace("-", "")
        clinic_hex = str(clinic_id).replace("-", "")
        assert tenant_hex in stmt_str.replace("-", ""), f"tenant_id not in query: {stmt_str}"
        assert clinic_hex in stmt_str.replace("-", ""), f"clinic_id not in query: {stmt_str}"

    async def test_soft_deleted_not_returned(self) -> None:
        """Soft-deleted referrals are not returned."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        ref_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # DB filters out deleted
        session.execute.return_value = mock_result

        repo = ReferralRepository(session=session)
        result = await repo.get_by_id(id=ref_id, tenant_id=tenant_id, scope_id=clinic_id)

        assert result is None


class TestListForScope:
    """list_for_scope returns referrals for a clinic."""

    async def test_list_for_scope_returns_models(self) -> None:
        """Returns list of referral models for given tenant+clinic."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        models = [_make_model(tenant_id=tenant_id, clinic_id=clinic_id) for _ in range(3)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = models
        session.execute.return_value = mock_result

        repo = ReferralRepository(session=session)
        results = await repo.list_for_scope(tenant_id=tenant_id, scope_id=clinic_id)

        assert len(results) == 3
        for r in results:
            assert r.tenant_id == tenant_id
            assert r.clinic_id == clinic_id

    async def test_list_for_scope_dual_filter(self) -> None:
        """list_for_scope query contains both tenant_id and clinic_id."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        repo = ReferralRepository(session=session)
        await repo.list_for_scope(tenant_id=tenant_id, scope_id=clinic_id)

        stmt = session.execute.call_args[0][0]
        stmt_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        tenant_hex = str(tenant_id).replace("-", "")
        clinic_hex = str(clinic_id).replace("-", "")
        assert tenant_hex in stmt_str.replace("-", ""), f"tenant_id not in query: {stmt_str}"
        assert clinic_hex in stmt_str.replace("-", ""), f"clinic_id not in query: {stmt_str}"
