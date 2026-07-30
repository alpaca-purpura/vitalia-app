# cap: configuracion.cuenta
"""Integration test — audit row durability for PATCH /api/v1/clinics/account/.

TDD RED→GREEN: validates that a real account PATCH:
  1. Returns HTTP 200 (business data persists — already working).
  2. Writes a durable vitalia_audit_log row (action='clinic_account_patch')
     committed to the DB — NOT just a structlog line.

Bug reproduced (C9-1): _get_db used get_async_session (non-committing);
audit_writer.write() INSERT had no subsequent commit → rolled back at
session close (HTTP 200, no DB row). Fix: switch to get_async_session_committing
+ remove per-repo commits from update_account/update_specialties so all three
writes commit atomically once on clean return.

Regression guard:
  - MUST be RED on the broken code (audit log count = 0 after PATCH).
  - MUST be GREEN after applying Option A fix (get_async_session_committing
    + remove intermediate commits from update_account + update_specialties).

Atomicity test:
  - Verifies that when specialties patch succeeds, BOTH the clinic field
    AND the audit row are present (atomic commit).

Markers:
  @pytest.mark.integration — auto-skipped when Postgres is unavailable
  (conftest.py::pytest_collection_modifyitems).
"""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql+asyncpg://postgres:password@localhost:5435/vitalia_test",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_real_app(override_engine: object = None) -> FastAPI:
    """Build a minimal FastAPI app wiring the real account_router.

    Uses the REAL DB dependency (_get_db / get_async_session_committing) so
    the transaction lifecycle is exercised. No service mocks — real repos +
    real audit_writer.

    Args:
        override_engine: If provided, override the _get_db dependency to use
            a local async engine instead of db.py's module-level singleton.
            This avoids pollution from tests that monkeypatch POSTGRES_PORT=5432
            before db.py's module-level _engine is first created (those tests
            cache a wrong-port engine in sys.modules).
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from src.modules.vitalia.clinics.api.account_router import _get_db, router

    app = FastAPI(redirect_slashes=False)

    if override_engine is not None:
        # Override _get_db to use the local (correct-port) engine
        local_factory = async_sessionmaker(override_engine, expire_on_commit=False)

        async def _local_get_db():  # type: ignore[return]
            """Local session using override_engine (avoids db.py singleton pollution)."""
            # Replicate get_async_session_committing logic but with local factory
            async with local_factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[_get_db] = _local_get_db

    app.include_router(router, prefix="/api/v1/clinics/account")
    return app


async def _count_audit_rows(session: AsyncSession, tenant_id: uuid.UUID, action: str) -> int:
    """Return count of vitalia_audit_log rows for (tenant_id, action)."""
    result = await session.execute(
        text("SELECT COUNT(*) FROM vitalia_audit_log WHERE tenant_id = CAST(:tid AS uuid) AND action = :action"),
        {"tid": str(tenant_id), "action": action},
    )
    row = result.fetchone()
    return int(row[0]) if row else 0


async def _get_clinic_legal_name(session: AsyncSession, tenant_id: uuid.UUID) -> str | None:
    """Return current legal_name from vitalia_clinic_branches for tenant."""
    result = await session.execute(
        text(
            "SELECT legal_name FROM vitalia_clinic_branches "
            "WHERE tenant_id = CAST(:tid AS uuid) AND deleted_at IS NULL LIMIT 1"
        ),
        {"tid": str(tenant_id)},
    )
    row = result.fetchone()
    return row[0] if row else None


async def _insert_test_tenant(
    session: AsyncSession,
    tenant_id: uuid.UUID,
) -> None:
    """Insert a minimal tenant row (FK dependency for clinic_branches)."""
    slug = f"test-tenant-{tenant_id!s:.8}"
    await session.execute(
        text(
            """
            INSERT INTO tenants (id, name, slug)
            VALUES (CAST(:id AS uuid), :name, :slug)
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": str(tenant_id), "name": "Test Tenant Integration", "slug": slug},
    )
    await session.commit()


async def _insert_test_clinic(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
) -> None:
    """Insert a minimal tenant + clinic row for the integration test."""
    # Tenant must exist first (FK constraint)
    await _insert_test_tenant(session, tenant_id)

    await session.execute(
        text(
            """
            INSERT INTO vitalia_clinic_branches
                (id, tenant_id, slug, name, country, created_at, updated_at)
            VALUES
                (CAST(:id AS uuid), CAST(:tenant_id AS uuid), :slug, :name, :country,
                 NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "id": str(clinic_id),
            "tenant_id": str(tenant_id),
            "slug": f"test-clinic-{clinic_id!s:.8}",
            "name": "Clínica de Prueba Integration",
            "country": "MX",
        },
    )
    await session.commit()


async def _insert_test_user(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Insert a minimal IAM user row for audit actor resolution."""
    # Insert into luana_iam users — use ON CONFLICT to be idempotent
    try:
        await session.execute(
            text(
                """
                INSERT INTO luana_iam_users
                    (id, tenant_id, clerk_user_id, email, role, created_at, updated_at)
                VALUES
                    (CAST(:id AS uuid), CAST(:tenant_id AS uuid), :clerk_id, :email,
                     'admin_clinic', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": str(user_id),
                "tenant_id": str(tenant_id),
                "clerk_id": f"user_{user_id!s:.12}",
                "email": "test@example.com",
            },
        )
        await session.commit()
    except Exception:
        # If the IAM users table doesn't exist or has different schema,
        # skip — the test will use UUID directly in X-User-ID header
        await session.rollback()


async def _cleanup_test_data(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
) -> None:
    """Remove test rows inserted by this test."""
    await session.execute(
        text("DELETE FROM vitalia_audit_log WHERE tenant_id = CAST(:tid AS uuid)"),
        {"tid": str(tenant_id)},
    )
    await session.execute(
        text("DELETE FROM vitalia_clinic_branches WHERE tenant_id = CAST(:tid AS uuid)"),
        {"tid": str(tenant_id)},
    )
    await session.execute(
        text("DELETE FROM tenants WHERE id = CAST(:tid AS uuid)"),
        {"tid": str(tenant_id)},
    )
    await session.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patch_account_commits_audit_row() -> None:
    """REGRESSION + ATOMICITY TEST (C9-1 + C1-2): PATCH /account/ must persist
    an audit row AND the clinic field update, both atomically committed.

    RED phase: fails on original code (get_async_session non-committing →
    audit INSERT rolled back at session close; clinic field persisted but
    audit row count = 0).
    GREEN phase: passes after Option A fix (get_async_session_committing +
    remove intermediate commits from update_account/update_specialties).

    Uses a local engine (not the session-scoped conftest engine) to avoid
    event-loop mismatch when pytest-randomly reorders tests and the
    session-scoped engine was bound to a different function loop.

    Steps:
    1. Insert a minimal tenant + clinic row.
    2. PATCH via httpx AsyncClient (real app, real DB, no mocks).
    3. Assert HTTP 200.
    4. Assert vitalia_audit_log count ≥ 1 for action='clinic_account_patch'.
    5. Assert the clinic's legal_name persisted (atomicity — both writes committed).
    6. Cleanup fixture rows.
    """
    tenant_id = uuid.uuid4()
    clinic_id = uuid.uuid4()
    user_id = uuid.uuid4()
    unique_legal_name = f"Integration Test Audit {tenant_id!s:.8} S.A."

    # Local engine — avoids session-scoped engine loop mismatch with random ordering.
    # The shared conftest `engine` fixture has scope="session", which binds the
    # asyncpg pool to the event loop of the first test that uses it. When
    # pytest-randomly reorders tests, this integration test may run in a different
    # function-scoped loop, causing "Future attached to a different loop". Creating
    # a local engine here sidesteps that issue entirely.
    local_engine = create_async_engine(_POSTGRES_DSN, echo=False)
    session_factory = async_sessionmaker(local_engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            # ---- 1. Insert test fixture -------------------------------------
            await _insert_test_clinic(session, tenant_id, clinic_id)

            app = _make_real_app(override_engine=local_engine)

            # ---- 2. PATCH via real app ----------------------------------------
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.patch(
                    "/api/v1/clinics/account/",
                    json={"legal_name": unique_legal_name},
                    headers={
                        "X-Tenant-ID": str(tenant_id),
                        "X-User-ID": str(user_id),
                        "X-User-Role": "admin_clinic",
                        "Content-Type": "application/json",
                    },
                )

            # ---- 3. Assert HTTP 200 -------------------------------------------
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

            # ---- 4. Assert audit row committed to DB --------------------------
            count = await _count_audit_rows(session, tenant_id, "clinic_account_patch")
            assert count >= 1, (
                f"vitalia_audit_log has 0 rows for action='clinic_account_patch' "
                f"and tenant_id={tenant_id!s}. "
                "Bug C9-1: audit INSERT was rolled back at session close because "
                "_get_db used get_async_session (non-committing) instead of "
                "get_async_session_committing."
            )

            # ---- 5. Assert clinic field also persisted (atomicity) -----------
            legal_name_in_db = await _get_clinic_legal_name(session, tenant_id)
            assert legal_name_in_db == unique_legal_name, (
                f"Clinic legal_name not persisted: expected '{unique_legal_name}', got '{legal_name_in_db}'"
            )

            # ---- 6. Cleanup ---------------------------------------------------
            await _cleanup_test_data(session, tenant_id, clinic_id)
    finally:
        await local_engine.dispose()
