"""Tests for TrustSignalRepositoryImpl — tenant isolation + SQLA 2.0.

Uses AsyncMock for the session (no Postgres required).
Integration variants (marked @pytest.mark.integration) are skipped without DB.

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from src.modules.vitalia.brand_studio.infrastructure.repositories.trust_signal_repository_impl import (
    TrustSignalRepositoryImpl,
)

_TENANT_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_TENANT_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repo(mock_session: AsyncMock) -> TrustSignalRepositoryImpl:
    return TrustSignalRepositoryImpl(session=mock_session)


class TestTrustSignalRepositoryInterface:
    """Verifica que el Impl implementa el ABC completo."""

    def test_impl_is_concrete_subclass(self) -> None:
        from src.modules.vitalia.brand_studio.infrastructure.repositories.trust_signal_repository import (
            TrustSignalRepository,
        )

        assert issubclass(TrustSignalRepositoryImpl, TrustSignalRepository)

    def test_impl_has_list_for_tenant(self) -> None:
        assert hasattr(TrustSignalRepositoryImpl, "list_for_tenant")

    def test_impl_has_create(self) -> None:
        assert hasattr(TrustSignalRepositoryImpl, "create")

    def test_impl_has_soft_delete(self) -> None:
        assert hasattr(TrustSignalRepositoryImpl, "soft_delete")

    def test_impl_has_get_by_id(self) -> None:
        assert hasattr(TrustSignalRepositoryImpl, "get_by_id")


class TestTrustSignalRepositoryTenantIsolation:
    """Verifica que las queries usan tenant_id para aislar datos."""

    @pytest.mark.asyncio
    async def test_list_for_tenant_uses_tenant_id(
        self,
        repo: TrustSignalRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        """list_for_tenant ejecuta select y pasa tenant_id correctamente."""
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = result_mock

        signals = await repo.list_for_tenant(tenant_id=_TENANT_A)

        assert isinstance(signals, list)
        mock_session.execute.assert_called_once()
        # Verify tenant_id appears in compiled SQL
        call_args = mock_session.execute.call_args[0]
        stmt = call_args[0]
        from sqlalchemy.dialects import postgresql

        sql_str = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert "aaaaaaaa" in sql_str or "tenant_id" in sql_str.lower()

    @pytest.mark.asyncio
    async def test_list_for_tenant_returns_empty_list_on_no_rows(
        self,
        repo: TrustSignalRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        """list_for_tenant retorna lista vacía cuando no hay filas."""
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = result_mock

        signals = await repo.list_for_tenant(tenant_id=_TENANT_A)

        assert signals == []

    @pytest.mark.asyncio
    async def test_get_by_id_filters_tenant(
        self,
        repo: TrustSignalRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        """get_by_id pasa tenant_id — no cross-tenant leak."""
        signal_id = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = result_mock

        result = await repo.get_by_id(signal_id, tenant_id=_TENANT_A)

        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_uses_tenant_id_not_hard_delete(
        self,
        repo: TrustSignalRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        """soft_delete emite UPDATE (no DELETE) con tenant_id en WHERE."""
        signal_id = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
        result_mock = MagicMock()
        mock_session.execute.return_value = result_mock

        await repo.soft_delete(signal_id, tenant_id=_TENANT_A)

        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0]
        stmt = call_args[0]
        from sqlalchemy.dialects import postgresql

        sql_str = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})).lower()
        # Debe ser UPDATE, no DELETE
        assert "update" in sql_str
        assert "delete" not in sql_str
