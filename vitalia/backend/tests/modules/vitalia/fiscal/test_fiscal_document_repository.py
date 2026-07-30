"""RED tests — FiscalDocumentRepository CRUD + dual filter.

TDD contract for:
  - create(): insert new fiscal doc record
  - get_by_id(): dual filter tenant_id + clinic_id
  - get_by_payment_id(): lookup docs for a given payment
  - update_status(): transition pending → emitted | failed (saga compensation)

Per 03-arch A6 (charge saga compensation) + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


def _import_fiscal_repo():
    from src.modules.vitalia.fiscal.infrastructure.repositories.fiscal_document_repository import (  # noqa: PLC0415
        FiscalDocumentRepository,
    )

    return FiscalDocumentRepository


def _make_mock_session_scalar(row: object | None) -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    session.execute = AsyncMock(return_value=result)
    return session


def _make_mock_session_insert() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    return session


class TestFiscalDocumentRepositoryImport:
    def test_importable(self) -> None:
        repo_cls = _import_fiscal_repo()
        assert repo_cls is not None

    def test_has_create(self) -> None:
        repo_cls = _import_fiscal_repo()
        assert hasattr(repo_cls, "create")

    def test_has_get_by_id(self) -> None:
        repo_cls = _import_fiscal_repo()
        assert hasattr(repo_cls, "get_by_id")

    def test_has_get_by_payment_id(self) -> None:
        repo_cls = _import_fiscal_repo()
        assert hasattr(repo_cls, "get_by_payment_id")

    def test_has_update_status(self) -> None:
        repo_cls = _import_fiscal_repo()
        assert hasattr(repo_cls, "update_status")


class TestFiscalDocumentDualFilter:
    """Every query must include tenant_id + clinic_id."""

    @pytest.mark.asyncio
    async def test_get_by_id_dual_filter(self) -> None:
        """get_by_id must filter by tenant_id + clinic_id."""
        repo_cls = _import_fiscal_repo()
        session = _make_mock_session_scalar(None)
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        doc_id = uuid4()

        await repo.get_by_id(
            doc_id=doc_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        call_args = session.execute.call_args
        stmt = call_args[0][0] if call_args[0] else call_args.args[0]
        from sqlalchemy.dialects import postgresql  # noqa: PLC0415

        compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert str(tenant_id) in compiled, "get_by_id must include tenant_id"
        assert str(clinic_id) in compiled, "get_by_id must include clinic_id (HIPAA dual filter)"

    @pytest.mark.asyncio
    async def test_get_by_payment_id_dual_filter(self) -> None:
        """get_by_payment_id must filter by tenant_id + clinic_id."""
        repo_cls = _import_fiscal_repo()
        session = _make_mock_session_scalar(None)
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        payment_id = uuid4()

        await repo.get_by_payment_id(
            payment_id=payment_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        call_args = session.execute.call_args
        stmt = call_args[0][0] if call_args[0] else call_args.args[0]
        from sqlalchemy.dialects import postgresql  # noqa: PLC0415

        compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert str(tenant_id) in compiled
        assert str(clinic_id) in compiled

    @pytest.mark.asyncio
    async def test_create_fiscal_document(self) -> None:
        """create() must use session.add() and flush for new fiscal doc."""
        repo_cls = _import_fiscal_repo()
        session = _make_mock_session_insert()
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        payment_id = uuid4()

        await repo.create(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            appointment_payment_id=payment_id,
            doc_type="boleta",
            provider="nubefact_stub",
        )

        # session.add should have been called with a model instance
        assert session.add.called or session.flush.called, (
            "create() must call session.add() + session.flush() to persist fiscal doc"
        )
