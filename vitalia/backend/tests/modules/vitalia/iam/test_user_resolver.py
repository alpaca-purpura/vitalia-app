"""T-3 sub-bug #2b — iam public resolver: clerk_id → users.id.

M2 (DDD boundary): brand_studio NO debe llamar el privado
ClinicResolver._resolve_user_uuid cross-module. iam expone un punto PÚBLICO
(app service) que hace SOLO el lookup clerk_id → users.id, sin requerir el
ClerkJwtDecoder. brand_studio consume ese público (cross-module sancionado:
app service público, no internals privados).

Unit (mock AsyncSession) — no requiere Postgres.
Integration (@integration, auto-skip) — seed users row + resolve real.

Story: estabilizar-harness-e2e-lisa-marca / T-3 (sub-bug #2b)
cap: iam.iam-scaffold-slice-1
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import text

from src.modules.vitalia.iam.application.services.clinic_resolver import UserNotFoundError
from src.modules.vitalia.iam.application.services.user_resolver import (
    resolve_user_uuid_from_clerk_id,
)


class TestResolveUserUuidFromClerkIdUnit:
    """Unit — query + UserNotFoundError sin Postgres (mock session)."""

    @pytest.mark.asyncio
    async def test_returns_uuid_when_match(self) -> None:
        """clerk_id con match → devuelve users.id UUID."""
        expected = uuid4()
        result_proxy = MagicMock()
        result_proxy.scalar_one_or_none.return_value = expected

        session = AsyncMock()
        session.execute.return_value = result_proxy

        got = await resolve_user_uuid_from_clerk_id(session, "user_2abc")

        assert got == expected
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_user_not_found_when_no_match(self) -> None:
        """clerk_id sin match → UserNotFoundError (no devuelve None silencioso)."""
        result_proxy = MagicMock()
        result_proxy.scalar_one_or_none.return_value = None

        session = AsyncMock()
        session.execute.return_value = result_proxy

        with pytest.raises(UserNotFoundError):
            await resolve_user_uuid_from_clerk_id(session, "user_does_not_exist")


@pytest.mark.integration
class TestResolveUserUuidFromClerkIdIntegration:
    """Integration — real DB roundtrip (auto-skip sin Postgres).

    Engine dedicado (no fixture db_session compartido) para evitar contención de
    conexión asyncpg cuando estos tests corren junto a app-import tests.
    """

    @staticmethod
    def _own_factory():  # noqa: ANN205
        import os

        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        dsn = os.getenv(
            "POSTGRES_DSN",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/vitalia_test",
        )
        engine = create_async_engine(dsn, echo=False)
        return engine, async_sessionmaker(engine, expire_on_commit=False)

    @pytest.mark.asyncio
    async def test_resolves_seeded_user(self) -> None:
        """Seed users(clerk_id, id) → resolve devuelve ese id."""
        engine, factory = self._own_factory()
        clerk_id = f"user_t3_{uuid4().hex[:8]}"
        user_id = uuid4()
        try:
            async with factory() as session:
                await session.execute(
                    text("""
                        INSERT INTO users (id, full_name, email, clerk_id, role, is_active, created_at, updated_at)
                        VALUES (CAST(:id AS uuid), :name, :email, :clerk_id, :role, true, NOW(), NOW())
                    """),
                    {
                        "id": str(user_id),
                        "name": "T3 Resolver User",
                        "email": f"{clerk_id}@example.com",
                        "clerk_id": clerk_id,
                        "role": "owner",
                    },
                )
                await session.commit()
                got = await resolve_user_uuid_from_clerk_id(session, clerk_id)
                assert got == user_id
        finally:
            async with factory() as cleanup:
                await cleanup.execute(text("DELETE FROM users WHERE id = CAST(:i AS uuid)"), {"i": str(user_id)})
                await cleanup.commit()
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_unknown_clerk_id_raises(self) -> None:
        """clerk_id inexistente en DB → UserNotFoundError."""
        engine, factory = self._own_factory()
        try:
            async with factory() as session:
                with pytest.raises(UserNotFoundError):
                    await resolve_user_uuid_from_clerk_id(session, f"user_missing_{uuid4().hex}")
        finally:
            await engine.dispose()
