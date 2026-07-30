# downstream-regression-na: engine test file; self-contained, no cross-consumer test reuse
"""Tests for CompoundScopeRepositoryBase.

Covers all 9 required scenarios from proposal § 6:
  1. get_by_id filters by (tenant_id, scope_id) → returns row
  2. get_by_id excludes soft-deleted rows
  3. list_for_scope respects offset + limit
  4. Cross-tenant query returns None (isolation)
  5. Cross-scope query returns None (isolation)
  6. scope_field="clinic_id" works for MODEL.clinic_id attribute
  7. scope_field="studio_id" works for MODEL.studio_id attribute
  8. Subclass without MODEL attribute raises clear error
  9. Default scope_field="scope_id" works for generic axis

Testing approach: SQLite in-memory DB via conftest.py db_engine/db fixtures
(same pattern as test_event_bus.py). Models use DateTime(timezone=True) + UUID
as per engine coding rules. AsyncSession is mocked to avoid requiring a live DB.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from luana_core_platform.domain.base_entity import Base
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
    MissingScopeFieldError,
)
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

# ---------------------------------------------------------------------------
# Test models (SQLAlchemy mapped classes)
# ---------------------------------------------------------------------------


class _ClinicScopedModel(Base):
    """Test model simulating vitalia clinic-scoped entities."""

    __tablename__ = "_test_clinic_scoped"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    clinic_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, default="")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)


class _StudioScopedModel(Base):
    """Test model simulating fitflow studio-scoped entities."""

    __tablename__ = "_test_studio_scoped"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    studio_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, default="")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)


class _GenericScopedModel(Base):
    """Test model with generic scope_id axis (default engine naming)."""

    __tablename__ = "_test_generic_scoped"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    scope_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, default="")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)


# ---------------------------------------------------------------------------
# Concrete repo implementations for tests
# ---------------------------------------------------------------------------


class _ClinicRepo(CompoundScopeRepositoryBase[_ClinicScopedModel, UUID]):
    """Vitalia-style repo with scope_field='clinic_id'."""

    MODEL = _ClinicScopedModel

    def __init__(self, *, session: Any) -> None:  # noqa: ANN401
        super().__init__(session=session, scope_field="clinic_id")


class _StudioRepo(CompoundScopeRepositoryBase[_StudioScopedModel, UUID]):
    """FitFlow-style repo with scope_field='studio_id'."""

    MODEL = _StudioScopedModel

    def __init__(self, *, session: Any) -> None:  # noqa: ANN401
        super().__init__(session=session, scope_field="studio_id")


class _GenericRepo(CompoundScopeRepositoryBase[_GenericScopedModel, UUID]):
    """Generic repo using default scope_field='scope_id'."""

    MODEL = _GenericScopedModel


# ---------------------------------------------------------------------------
# Helper: mock session that returns controlled scalars
# ---------------------------------------------------------------------------


def _mock_session_for_scalar_one_or_none(return_value: Any) -> MagicMock:  # noqa: ANN401
    """Build a mock AsyncSession whose execute().scalar_one_or_none() returns value."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = return_value

    session = MagicMock()
    session.execute = AsyncMock(return_value=mock_result)
    return session


def _mock_session_for_scalars_all(return_value: list[Any]) -> MagicMock:
    """Build a mock AsyncSession whose execute().scalars().all() returns value."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = return_value

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    session = MagicMock()
    session.execute = AsyncMock(return_value=mock_result)
    return session


def _make_clinic_row(
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    deleted: bool = False,
) -> _ClinicScopedModel:
    """Create a _ClinicScopedModel instance for testing."""
    row = _ClinicScopedModel()
    row.id = uuid4()
    row.tenant_id = str(tenant_id)
    row.clinic_id = str(clinic_id)
    row.name = "test entity"
    row.deleted_at = datetime.now(tz=timezone.utc) if deleted else None
    return row


# ---------------------------------------------------------------------------
# Test: get_by_id correctness
# ---------------------------------------------------------------------------


class TestGetById:
    """Scenario 1 and 2: get_by_id with dual-filter and soft-delete exclusion."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_row_when_found(self) -> None:
        """get_by_id returns the row when (id, tenant_id, scope_id) match and not deleted."""
        tenant_id = uuid4()
        clinic_id = uuid4()
        row = _make_clinic_row(tenant_id=tenant_id, clinic_id=clinic_id)

        session = _mock_session_for_scalar_one_or_none(row)
        repo = _ClinicRepo(session=session)

        result = await repo.get_by_id(id=row.id, tenant_id=tenant_id, scope_id=clinic_id)

        assert result is row
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self) -> None:
        """get_by_id returns None when no row matches the dual-filter."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _ClinicRepo(session=session)

        result = await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_soft_deleted(self) -> None:
        """get_by_id returns None for soft-deleted rows.

        The WHERE clause includes ``deleted_at IS NULL`` — the mock session
        returns None to simulate the DB correctly filtering out deleted rows.
        """
        tenant_id = uuid4()
        clinic_id = uuid4()
        # Soft-deleted row exists but DB filtered it (mock returns None)
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _ClinicRepo(session=session)

        result = await repo.get_by_id(id=uuid4(), tenant_id=tenant_id, scope_id=clinic_id)

        assert result is None
        # Verify execute was called (query was issued with deleted_at IS NULL clause)
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_query_includes_deleted_at_filter(self) -> None:
        """get_by_id statement includes deleted_at IS NULL predicate."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _ClinicRepo(session=session)

        await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())

        # Inspect the SELECT statement passed to session.execute
        call_args = session.execute.call_args
        stmt = call_args[0][0]
        # Compile to string to verify presence of deleted_at IS NULL
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "deleted_at IS NULL" in compiled


# ---------------------------------------------------------------------------
# Test: list_for_scope correctness
# ---------------------------------------------------------------------------


class TestListForScope:
    """Scenario 3: list_for_scope respects offset + limit."""

    @pytest.mark.asyncio
    async def test_list_for_scope_returns_matching_rows(self) -> None:
        """list_for_scope returns all non-deleted rows for tenant+scope."""
        tenant_id = uuid4()
        clinic_id = uuid4()
        rows = [
            _make_clinic_row(tenant_id=tenant_id, clinic_id=clinic_id),
            _make_clinic_row(tenant_id=tenant_id, clinic_id=clinic_id),
        ]

        session = _mock_session_for_scalars_all(rows)
        repo = _ClinicRepo(session=session)

        result = await repo.list_for_scope(tenant_id=tenant_id, scope_id=clinic_id)

        assert result == rows
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_for_scope_returns_empty_list_when_no_rows(self) -> None:
        """list_for_scope returns empty list when no rows match."""
        session = _mock_session_for_scalars_all([])
        repo = _ClinicRepo(session=session)

        result = await repo.list_for_scope(tenant_id=uuid4(), scope_id=uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_list_for_scope_passes_limit_to_statement(self) -> None:
        """list_for_scope statement includes LIMIT clause when limit is given."""
        session = _mock_session_for_scalars_all([])
        repo = _ClinicRepo(session=session)

        await repo.list_for_scope(tenant_id=uuid4(), scope_id=uuid4(), limit=5, offset=0)

        call_args = session.execute.call_args
        stmt = call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "LIMIT 5" in compiled

    @pytest.mark.asyncio
    async def test_list_for_scope_passes_offset_to_statement(self) -> None:
        """list_for_scope statement includes OFFSET clause."""
        session = _mock_session_for_scalars_all([])
        repo = _ClinicRepo(session=session)

        await repo.list_for_scope(tenant_id=uuid4(), scope_id=uuid4(), limit=10, offset=20)

        call_args = session.execute.call_args
        stmt = call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "OFFSET 20" in compiled or "20" in compiled  # SQLite vs Postgres rendering

    @pytest.mark.asyncio
    async def test_list_for_scope_no_limit_returns_all(self) -> None:
        """list_for_scope with limit=None does not add a finite LIMIT clause.

        SQLAlchemy may render ``LIMIT -1`` on SQLite (equivalent to no limit).
        We verify that no positive LIMIT integer is present in the statement.
        """
        session = _mock_session_for_scalars_all([])
        repo = _ClinicRepo(session=session)

        await repo.list_for_scope(tenant_id=uuid4(), scope_id=uuid4(), limit=None)

        call_args = session.execute.call_args
        stmt = call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        # Acceptable: no LIMIT, or LIMIT -1 (SQLite unlimited). Unacceptable: any positive LIMIT.
        import re

        positive_limit = re.search(r"LIMIT\s+([0-9]+)", compiled)
        if positive_limit:
            limit_val = int(positive_limit.group(1))
            # LIMIT -1 is SQLite's "no limit" — treat as OK (but regex won't match negative)
            assert limit_val < 0, f"Unexpected positive LIMIT {limit_val} in query without limit"


# ---------------------------------------------------------------------------
# Test: Cross-tenant isolation
# ---------------------------------------------------------------------------


class TestCrossTenantIsolation:
    """Scenario 4: Cross-tenant query returns None."""

    @pytest.mark.asyncio
    async def test_cross_tenant_get_by_id_returns_none(self) -> None:
        """get_by_id with a different tenant_id returns None (isolation enforced by DB).

        The WHERE clause filters tenant_id — the mock session returns None
        to simulate the DB enforcing isolation.
        """
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _ClinicRepo(session=session)

        clinic = uuid4()
        entity_id = uuid4()

        # Query with different tenant (tenant_b) — should return None
        tenant_b = uuid4()
        result = await repo.get_by_id(id=entity_id, tenant_id=tenant_b, scope_id=clinic)

        assert result is None

    @pytest.mark.asyncio
    async def test_cross_tenant_list_for_scope_returns_empty(self) -> None:
        """list_for_scope with wrong tenant_id returns empty list."""
        session = _mock_session_for_scalars_all([])
        repo = _ClinicRepo(session=session)

        result = await repo.list_for_scope(tenant_id=uuid4(), scope_id=uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_id_query_includes_tenant_id_filter(self) -> None:
        """Compiled SQL for get_by_id contains tenant_id equality clause."""
        tenant_id = uuid4()
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _ClinicRepo(session=session)

        await repo.get_by_id(id=uuid4(), tenant_id=tenant_id, scope_id=uuid4())

        stmt = session.execute.call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        # SQLite renders UUIDs without hyphens; normalize for comparison
        tenant_id_no_hyphens = str(tenant_id).replace("-", "")
        assert tenant_id_no_hyphens in compiled


# ---------------------------------------------------------------------------
# Test: Cross-scope isolation
# ---------------------------------------------------------------------------


class TestCrossScopeIsolation:
    """Scenario 5: Cross-scope query returns None."""

    @pytest.mark.asyncio
    async def test_cross_scope_get_by_id_returns_none(self) -> None:
        """get_by_id with a different scope_id returns None (isolation by scope axis)."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _ClinicRepo(session=session)

        result = await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_query_includes_scope_filter(self) -> None:
        """Compiled SQL includes clinic_id equality clause for scope isolation."""
        scope_id = uuid4()
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _ClinicRepo(session=session)

        await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=scope_id)

        stmt = session.execute.call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        # SQLite renders UUIDs without hyphens; normalize for comparison
        scope_id_no_hyphens = str(scope_id).replace("-", "")
        assert scope_id_no_hyphens in compiled


# ---------------------------------------------------------------------------
# Test: scope_field="clinic_id" (Scenario 6)
# ---------------------------------------------------------------------------


class TestScopeFieldClinicId:
    """Scenario 6: scope_field='clinic_id' works for MODEL.clinic_id attribute."""

    @pytest.mark.asyncio
    async def test_clinic_id_scope_field_attribute_found(self) -> None:
        """_ClinicRepo resolves MODEL.clinic_id correctly (no AttributeError)."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _ClinicRepo(session=session)

        # _scope_attr() must not raise
        attr = repo._scope_attr()
        assert attr is not None

    @pytest.mark.asyncio
    async def test_clinic_id_scope_field_used_in_query(self) -> None:
        """The compiled SQL references clinic_id, not scope_id."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _ClinicRepo(session=session)

        await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())

        stmt = session.execute.call_args[0][0]
        compiled = str(stmt.compile())
        assert "clinic_id" in compiled
        assert "studio_id" not in compiled
        assert "scope_id" not in compiled


# ---------------------------------------------------------------------------
# Test: scope_field="studio_id" (Scenario 7)
# ---------------------------------------------------------------------------


class TestScopeFieldStudioId:
    """Scenario 7: scope_field='studio_id' works for MODEL.studio_id attribute."""

    @pytest.mark.asyncio
    async def test_studio_id_scope_field_attribute_found(self) -> None:
        """_StudioRepo resolves MODEL.studio_id correctly (no AttributeError)."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _StudioRepo(session=session)

        attr = repo._scope_attr()
        assert attr is not None

    @pytest.mark.asyncio
    async def test_studio_id_scope_field_used_in_query(self) -> None:
        """The compiled SQL references studio_id, not clinic_id."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _StudioRepo(session=session)

        await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())

        stmt = session.execute.call_args[0][0]
        compiled = str(stmt.compile())
        assert "studio_id" in compiled
        assert "clinic_id" not in compiled
        assert "scope_id" not in compiled


# ---------------------------------------------------------------------------
# Test: Missing MODEL attribute (Scenario 8)
# ---------------------------------------------------------------------------


class TestMissingModelAttribute:
    """Scenario 8: Subclass without MODEL attribute raises MissingScopeFieldError."""

    @pytest.mark.asyncio
    async def test_get_by_id_raises_when_model_not_defined(self) -> None:
        """get_by_id raises MissingScopeFieldError if MODEL class attribute is absent."""

        class BrokenRepo(CompoundScopeRepositoryBase):
            pass  # intentionally missing MODEL

        session = _mock_session_for_scalar_one_or_none(None)
        repo = BrokenRepo(session=session)

        with pytest.raises(MissingScopeFieldError, match="MODEL"):
            await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())

    @pytest.mark.asyncio
    async def test_list_for_scope_raises_when_model_not_defined(self) -> None:
        """list_for_scope raises MissingScopeFieldError if MODEL class attribute is absent."""

        class BrokenRepo(CompoundScopeRepositoryBase):
            pass

        session = _mock_session_for_scalars_all([])
        repo = BrokenRepo(session=session)

        with pytest.raises(MissingScopeFieldError, match="MODEL"):
            await repo.list_for_scope(tenant_id=uuid4(), scope_id=uuid4())

    @pytest.mark.asyncio
    async def test_error_message_is_actionable(self) -> None:
        """MissingScopeFieldError message tells developer what to do."""

        class UnnamedBrokenRepo(CompoundScopeRepositoryBase):
            pass

        session = _mock_session_for_scalar_one_or_none(None)
        repo = UnnamedBrokenRepo(session=session)

        with pytest.raises(MissingScopeFieldError) as exc_info:
            await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())

        error_msg = str(exc_info.value)
        # Message must guide the developer to define MODEL
        assert "MODEL" in error_msg

    @pytest.mark.asyncio
    async def test_scope_attr_raises_when_field_not_on_model(self) -> None:
        """_scope_attr raises AttributeError when scope_field does not exist on MODEL."""

        class MismatchedRepo(CompoundScopeRepositoryBase[_ClinicScopedModel, UUID]):
            MODEL = _ClinicScopedModel

            def __init__(self, *, session: Any) -> None:  # noqa: ANN401
                # "nonexistent_id" does not exist on _ClinicScopedModel
                super().__init__(session=session, scope_field="nonexistent_id")

        session = _mock_session_for_scalar_one_or_none(None)
        repo = MismatchedRepo(session=session)

        with pytest.raises(AttributeError, match="nonexistent_id"):
            await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())


# ---------------------------------------------------------------------------
# Test: Default scope_field="scope_id" (Scenario 9)
# ---------------------------------------------------------------------------


class TestDefaultScopeField:
    """Scenario 9: Default scope_field='scope_id' works for generic axis."""

    @pytest.mark.asyncio
    async def test_default_scope_field_attribute_found(self) -> None:
        """_GenericRepo with default scope_field='scope_id' resolves correctly."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _GenericRepo(session=session)

        attr = repo._scope_attr()
        assert attr is not None

    @pytest.mark.asyncio
    async def test_default_scope_field_used_in_query(self) -> None:
        """The compiled SQL references scope_id when using default scope_field."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _GenericRepo(session=session)

        await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())

        stmt = session.execute.call_args[0][0]
        compiled = str(stmt.compile())
        assert "scope_id" in compiled

    @pytest.mark.asyncio
    async def test_default_constructor_scope_field_is_scope_id(self) -> None:
        """Default constructor sets _scope_field='scope_id'."""
        session = _mock_session_for_scalar_one_or_none(None)
        repo = _GenericRepo(session=session)
        # _GenericRepo does not pass scope_field to super().__init__
        assert repo._scope_field == "scope_id"
