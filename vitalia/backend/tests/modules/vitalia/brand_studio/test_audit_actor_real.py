"""T-3 sub-bug #2b — actor de audit REAL (resolver clerk_id → users.id).

Hoy el actor de audit es el valor crudo de X-User-ID parseado como UUID
(marca_router.py: user_uuid = UUID(user_id)). Con T-2 el FE pasará a mandar el
CLERK userId real (string "user_2abc...", NO UUID) → UUID(user_id) rompería 422.

Fix (orchestrator decision, mecanismo header-trust, NO JWT):
  El router resuelve el actor a users.id UUID a partir del valor de X-User-ID:
    - si parsea como UUID → usar tal cual (back-compat callers/tests legacy).
    - si NO es UUID (= Clerk userId) → resolver clerk_id → users.id vía el público
      iam resolve_user_uuid_from_clerk_id. Sin match → 422.

RED contra el comportamiento actual: PATCH con X-User-ID = Clerk userId string
hoy hace UUID(<clerk id>) → 422; tras el fix → 200 + el service recibe el
users.id resuelto (≠ tenant_id, ≠ header crudo).

§ unit (mock iam + mocked service) — siempre corre.
§ integration (@integration, real DB) — seed users + PATCH real → audit row.

Story: estabilizar-harness-e2e-lisa-marca / T-3 (A3 / SC-6 parte BE)
cap: brand_studio.lisa-marca
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import BrandPersonalityDTO

# Importa src.main (Settings env) → integration para auto-skip sin Postgres/env.
pytestmark = pytest.mark.integration

_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_USER_UUID = "11111111-1111-1111-1111-111111111111"  # legacy users.id directo (back-compat)
_RESOLVED_UUID = "33333333-3333-3333-3333-333333333333"  # users.id resuelto desde Clerk id
_CLERK_USER_ID = "user_2abcDEFghiJKLmno"  # Clerk userId real (NO es un UUID)
_PROFILE_ID = "22222222-2222-2222-2222-222222222222"
_PERSONALITY_URL = "/api/v1/lisa/marca/personality"


def _make_personality(tenant_id: str = _TENANT_A) -> BrandPersonalityDTO:
    return BrandPersonalityDTO(
        tenant_id=UUID(tenant_id),
        personality_profile_id=UUID(_PROFILE_ID),
        archetype="caregiver",
        so_i_speak="Hablo con claridad.",
        so_i_dont_speak="No uso jerga.",
        technical_context="Contexto.",
        format_instructions="Frases cortas.",
        identity_anchor="Clínica XYZ.",
        domain_context="Salud preventiva.",
        compiled_at=datetime.now(timezone.utc),
        compiler_version="v2",
    )


@pytest.fixture
def app():  # noqa: ANN201
    from src.main import app as vitalia_app

    return vitalia_app


# ---------------------------------------------------------------------------
# § 1 — actor resolution en el router (mock iam público + mocked service)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPatchPersonalityActorResolution:
    """PATCH /personality resuelve el actor a users.id UUID antes de auditar."""

    async def test_clerk_user_id_resolved_to_users_id(self, app) -> None:
        """X-User-ID = Clerk userId string → service recibe users.id resuelto (≠ header crudo).

        RED hoy: UUID("user_2abc...") → ValueError → 422.
        GREEN tras fix: 200 + service.user_id == _RESOLVED_UUID.
        """
        from httpx import ASGITransport, AsyncClient

        with (
            patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build,
            patch(
                "src.modules.vitalia.brand_studio.api.routers.marca_router.resolve_user_uuid_from_clerk_id",
                new=AsyncMock(return_value=UUID(_RESOLVED_UUID)),
            ) as mock_resolve,
        ):
            mock_bundle = AsyncMock()
            mock_bundle.marca.patch_personality.return_value = _make_personality()
            mock_build.return_value = mock_bundle

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.patch(
                    _PERSONALITY_URL,
                    json={"archetype": "sage"},
                    headers={
                        "X-Tenant-ID": _TENANT_A,
                        "X-User-ID": _CLERK_USER_ID,  # Clerk userId, NOT a UUID
                        "X-User-Role": "owner",
                    },
                )

            assert response.status_code == 200, (
                f"Clerk userId debe resolverse a users.id (no 422). Got {response.status_code}: {response.text}"
            )
            mock_resolve.assert_awaited_once()
            call_kwargs = mock_bundle.marca.patch_personality.call_args.kwargs
            assert call_kwargs["user_id"] == UUID(_RESOLVED_UUID), (
                f"El actor pasado al service debe ser el users.id resuelto, got {call_kwargs['user_id']}"
            )
            # El actor NO debe ser el tenant_id (el bug histórico) ni el header crudo.
            assert call_kwargs["user_id"] != UUID(_TENANT_A)

    async def test_uuid_user_id_passthrough_no_resolve(self, app) -> None:
        """X-User-ID = users.id UUID válido → usado tal cual, NO se llama al resolver (back-compat)."""
        from httpx import ASGITransport, AsyncClient

        with (
            patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build,
            patch(
                "src.modules.vitalia.brand_studio.api.routers.marca_router.resolve_user_uuid_from_clerk_id",
                new=AsyncMock(),
            ) as mock_resolve,
        ):
            mock_bundle = AsyncMock()
            mock_bundle.marca.patch_personality.return_value = _make_personality()
            mock_build.return_value = mock_bundle

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.patch(
                    _PERSONALITY_URL,
                    json={"archetype": "sage"},
                    headers={
                        "X-Tenant-ID": _TENANT_A,
                        "X-User-ID": _USER_UUID,  # already a users.id UUID
                        "X-User-Role": "owner",
                    },
                )

            assert response.status_code == 200
            mock_resolve.assert_not_awaited()
            call_kwargs = mock_bundle.marca.patch_personality.call_args.kwargs
            assert call_kwargs["user_id"] == UUID(_USER_UUID)

    async def test_clerk_user_id_not_found_returns_422(self, app) -> None:
        """X-User-ID = Clerk id sin match en users → UserNotFoundError → 422."""
        from httpx import ASGITransport, AsyncClient

        from src.modules.vitalia.iam.application.services.clinic_resolver import UserNotFoundError

        with (
            patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build,
            patch(
                "src.modules.vitalia.brand_studio.api.routers.marca_router.resolve_user_uuid_from_clerk_id",
                new=AsyncMock(side_effect=UserNotFoundError("no match")),
            ),
        ):
            mock_bundle = AsyncMock()
            mock_bundle.marca.patch_personality.return_value = _make_personality()
            mock_build.return_value = mock_bundle

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.patch(
                    _PERSONALITY_URL,
                    json={"archetype": "sage"},
                    headers={
                        "X-Tenant-ID": _TENANT_A,
                        "X-User-ID": "user_unknown_clerk_id",
                        "X-User-Role": "owner",
                    },
                )

            assert response.status_code == 422, (
                f"Clerk id sin match debe responder 422. Got {response.status_code}: {response.text}"
            )


# ---------------------------------------------------------------------------
# § 2 — integration: PATCH real → audit_log actor = users.id resuelto (≠ tenant)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAuditActorRealDb:
    """Real DB roundtrip: seed users + PATCH → vitalia_audit_log con actor UUID real.

    Usa un engine async PROPIO (no el fixture compartido db_session) para seed/assert/
    cleanup: el endpoint PATCH abre su propia sesión sobre el mismo engine, y compartir
    una conexión asyncpg con el fixture provoca 'another operation is in progress'
    cuando estos tests corren junto a los app-import tests. Connection dedicada = robusto
    sin importar el orden de ejecución.
    """

    async def test_patch_personality_writes_resolved_actor(self, app) -> None:  # noqa: ANN001
        """PATCH personality con Clerk userId → fila audit con user_id = users.id (≠ tenant_id).

        Seed un users(clerk_id) → el router resuelve clerk_id → users.id y lo graba
        como actor. Verifica la fila más reciente de vitalia_audit_log para el tenant.
        """
        import os

        from httpx import ASGITransport, AsyncClient
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        dsn = os.getenv(
            "POSTGRES_DSN",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/vitalia_test",
        )
        own_engine = create_async_engine(dsn, echo=False)
        own_factory = async_sessionmaker(own_engine, expire_on_commit=False)

        clerk_id = f"user_t3audit_{uuid4().hex[:8]}"
        user_id = uuid4()
        tenant_id = uuid4()

        try:
            async with own_factory() as seed_session:
                await seed_session.execute(
                    text("""
                        INSERT INTO users (id, full_name, email, clerk_id, role, is_active, created_at, updated_at)
                        VALUES (CAST(:id AS uuid), :name, :email, :clerk_id, :role, true, NOW(), NOW())
                    """),
                    {
                        "id": str(user_id),
                        "name": "T3 Audit Actor",
                        "email": f"{clerk_id}@example.com",
                        "clerk_id": clerk_id,
                        "role": "owner",
                    },
                )
                await seed_session.commit()

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.patch(
                    _PERSONALITY_URL,
                    json={"archetype": "sage"},
                    headers={
                        "X-Tenant-ID": str(tenant_id),
                        "X-User-ID": clerk_id,  # Clerk userId real
                        "X-User-Role": "owner",
                    },
                )
            assert response.status_code == 200, f"PATCH real falló: {response.status_code} {response.text}"

            async with own_factory() as assert_session:
                row = (
                    await assert_session.execute(
                        text("""
                            SELECT user_id, tenant_id FROM vitalia_audit_log
                            WHERE tenant_id = CAST(:tenant_id AS uuid)
                              AND resource_type = 'brand_personality'
                            ORDER BY occurred_at DESC LIMIT 1
                        """),
                        {"tenant_id": str(tenant_id)},
                    )
                ).first()
            assert row is not None, "No se escribió fila de audit para el PATCH personality"
            audit_user_id, _audit_tenant_id = row
            assert UUID(str(audit_user_id)) == user_id, (
                f"audit actor debe ser users.id resuelto ({user_id}), got {audit_user_id}"
            )
            assert UUID(str(audit_user_id)) != UUID(str(tenant_id)), "actor NUNCA debe ser el tenant_id (bug histórico)"
        finally:
            async with own_factory() as cleanup_session:
                await cleanup_session.execute(
                    text("DELETE FROM vitalia_audit_log WHERE tenant_id = CAST(:t AS uuid)"),
                    {"t": str(tenant_id)},
                )
                await cleanup_session.execute(
                    text("DELETE FROM users WHERE id = CAST(:i AS uuid)"), {"i": str(user_id)}
                )
                await cleanup_session.commit()
            await own_engine.dispose()
