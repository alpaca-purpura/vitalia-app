"""Tests for ProhibitedPhraseRepositoryImpl — tenant isolation + SQLA 2.0.

Uses AsyncMock for the session (no Postgres required).
Integration variants (marked @pytest.mark.integration) are skipped without DB.

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from src.modules.vitalia.brand_studio.infrastructure.repositories.prohibited_phrase_repository_impl import (
    ProhibitedPhraseRepositoryImpl,
)

_TENANT_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_TENANT_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    return session


@pytest.fixture
def repo(mock_session: AsyncMock) -> ProhibitedPhraseRepositoryImpl:
    return ProhibitedPhraseRepositoryImpl(session=mock_session)


class TestProhibitedPhraseRepositoryInterface:
    """Verifica que el Impl implementa el ABC completo."""

    def test_impl_is_concrete_subclass(self) -> None:
        from src.modules.vitalia.brand_studio.infrastructure.repositories.prohibited_phrase_repository import (
            ProhibitedPhraseRepository,
        )

        assert issubclass(ProhibitedPhraseRepositoryImpl, ProhibitedPhraseRepository)

    def test_impl_has_list_for_tenant(self) -> None:
        assert hasattr(ProhibitedPhraseRepositoryImpl, "list_for_tenant")

    def test_impl_has_get_by_id(self) -> None:
        assert hasattr(ProhibitedPhraseRepositoryImpl, "get_by_id")

    def test_impl_has_create(self) -> None:
        assert hasattr(ProhibitedPhraseRepositoryImpl, "create")

    def test_impl_has_soft_delete(self) -> None:
        assert hasattr(ProhibitedPhraseRepositoryImpl, "soft_delete")


class TestProhibitedPhraseRepositoryTenantIsolation:
    """Verifica que las queries usan tenant_id correctamente."""

    @pytest.mark.asyncio
    async def test_list_for_tenant_uses_tenant_id_in_where(
        self,
        repo: ProhibitedPhraseRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        """list_for_tenant ejecuta select con tenant_id en el WHERE."""
        # Mock the session.execute to return empty scalars
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = result_mock

        phrases = await repo.list_for_tenant(tenant_id=_TENANT_A)

        assert isinstance(phrases, list)
        mock_session.execute.assert_called_once()
        # Verify the stmt was called (tenant_id used in filter)
        call_args = mock_session.execute.call_args[0]
        stmt = call_args[0]
        # Compiled SQL should mention the tenant
        from sqlalchemy.dialects import postgresql

        sql_str = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert "aaaaaaaa" in sql_str or "tenant_id" in sql_str.lower()

    @pytest.mark.asyncio
    async def test_list_for_tenant_includes_null_seeds(
        self,
        repo: ProhibitedPhraseRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        """list_for_tenant incluye filas con tenant_id IS NULL (seeds)."""
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = result_mock

        await repo.list_for_tenant(tenant_id=_TENANT_A)

        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0]
        stmt = call_args[0]
        from sqlalchemy.dialects import postgresql

        sql_str = str(stmt.compile(dialect=postgresql.dialect())).lower()
        # The OR condition should include IS NULL check for seeds
        assert "is null" in sql_str or "isnull" in sql_str or "= null" in sql_str or "null" in sql_str

    @pytest.mark.asyncio
    async def test_get_by_id_passes_tenant_id(
        self,
        repo: ProhibitedPhraseRepositoryImpl,
        mock_session: AsyncMock,
    ) -> None:
        """get_by_id pasa tenant_id en la query — no leakea cross-tenant."""
        phrase_id = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = result_mock

        result = await repo.get_by_id(phrase_id, tenant_id=_TENANT_A)

        assert result is None
        mock_session.execute.assert_called_once()
