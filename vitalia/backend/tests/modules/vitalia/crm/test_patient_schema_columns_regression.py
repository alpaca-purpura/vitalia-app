# cap: crm.crm-consent-optout
"""Regression test — T-BE-5 schemafix: vitalia_patients missing columns.

ROOT CAUSE (live 500 2026-06-22):
    patient_repository.create_minimal() referenced columns `channel_first` and
    `notes` that DO NOT EXIST in vitalia_patients. Unit tests all passed because
    they mock the DB. This regression test hits the REAL schema.

TDD (tdd-mandatory.md § Bugs):
    - Test written BEFORE migration 051 (RED — column does not exist)
    - Test goes GREEN after `alembic upgrade head` runs migration 051
    - A mock-only test does NOT count for this class of bug

HIPAA-lite (hipaa-lite.md):
    - `channel_first` is acquisition channel metadata — NOT PHI. Plaintext OK.
    - `notes` MAY hold PHI in future. Column added nullable; inline create flow
      always passes None. TODO(D10): encrypt notes if it ever carries PHI.

pytestmark: integration — skipped when Postgres is not reachable.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helper: raw async Postgres ping via asyncpg / psycopg to avoid full stack
# ---------------------------------------------------------------------------


def _get_db_url() -> str:
    """Read DSN from environment (same source as vitalia backend settings).

    Defaults match vitalia/.env.dev — host is localhost with port 5435
    (the Docker Postgres exposed port) and DB is vitalia_dev.
    """
    import os

    host = os.getenv("POSTGRES_HOST", "localhost")
    # Default port 5435 = Docker postgres mapped port (see docker port luana-dev-luana_postgres_dev-1)
    port = os.getenv("POSTGRES_PORT", "5435")
    # vitalia backend uses vitalia_dev (see vitalia/.env.dev)
    db = os.getenv("POSTGRES_DB", "vitalia_dev")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


# ---------------------------------------------------------------------------
# SC-schema-regression: prove columns exist in real schema
# ---------------------------------------------------------------------------


class TestVitaliaPatientSchemaCols:
    """Integration: vitalia_patients must expose channel_first + notes columns.

    These tests verify the REAL Postgres schema. They are deliberately NOT
    mocked — a mock would have hidden this class of bug (as it did for T-BE-5).

    Skips automatically when Postgres is not reachable (CI without DB).
    """

    @pytest.mark.asyncio
    async def test_channel_first_column_exists_in_schema(self) -> None:
        """vitalia_patients.channel_first column must exist.

        RED before migration 051 (column "channel_first" does not exist).
        GREEN after migration 051 runs.
        """
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        url = _get_db_url()
        try:
            engine = create_async_engine(url, echo=False)
        except Exception:
            pytest.skip("asyncpg not available")

        try:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'vitalia_patients'
                          AND column_name = 'channel_first'
                        """
                    )
                )
                row = result.fetchone()
                assert row is not None, (
                    "Column 'channel_first' does not exist in vitalia_patients. Run migration 051 to add it."
                )
        except Exception as exc:
            if "Connection refused" in str(exc) or "connect" in str(exc).lower():
                pytest.skip(f"Postgres not reachable: {exc}")
            raise
        finally:
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_notes_column_exists_in_schema(self) -> None:
        """vitalia_patients.notes column must exist.

        RED before migration 051 (column "notes" does not exist).
        GREEN after migration 051 runs.
        """
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        url = _get_db_url()
        try:
            engine = create_async_engine(url, echo=False)
        except Exception:
            pytest.skip("asyncpg not available")

        try:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'vitalia_patients'
                          AND column_name = 'notes'
                        """
                    )
                )
                row = result.fetchone()
                assert row is not None, (
                    "Column 'notes' does not exist in vitalia_patients. Run migration 051 to add it."
                )
        except Exception as exc:
            if "Connection refused" in str(exc) or "connect" in str(exc).lower():
                pytest.skip(f"Postgres not reachable: {exc}")
            raise
        finally:
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_insert_with_channel_first_and_notes_succeeds(self) -> None:
        """INSERT into vitalia_patients referencing channel_first + notes must NOT 500.

        This is the exact SQL that caused the live 500 (simplified, no pgcrypto).
        RED: sqlalchemy.exc.ProgrammingError: column "channel_first" does not exist
        GREEN: INSERT succeeds, row is cleaned up.
        """
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        url = _get_db_url()
        try:
            engine = create_async_engine(url, echo=False)
        except Exception:
            pytest.skip("asyncpg not available")

        test_tenant = uuid4()
        test_clinic = uuid4()
        test_patient = uuid4()

        try:
            async with engine.begin() as conn:
                # Insert a row referencing ONLY the columns that were missing.
                # We omit marketing_opt_in/opt_out to avoid dependency on older
                # schema state of vitalia_test (those come from migration 023).
                # The goal is to prove channel_first + notes accept writes.
                await conn.execute(
                    text(
                        """
                        INSERT INTO vitalia_patients
                          (id, tenant_id, clinic_id,
                           name, phone, email,
                           channel_first, notes,
                           created_at, updated_at)
                        VALUES
                          (:id, :tenant_id, :clinic_id,
                           'TEST_NAME_PLAIN', 'TEST_PHONE', 'test@example.com',
                           :channel_first, :notes,
                           NOW(), NOW())
                        """
                    ),
                    {
                        "id": str(test_patient),
                        "tenant_id": str(test_tenant),
                        "clinic_id": str(test_clinic),
                        "channel_first": "walk_in",
                        "notes": None,
                    },
                )

                # Clean up immediately (soft-delete pattern requires deleted_at;
                # for regression test we hard-delete the test row only)
                await conn.execute(
                    text("DELETE FROM vitalia_patients WHERE id = :id"),
                    {"id": str(test_patient)},
                )
        except Exception as exc:
            exc_str = str(exc)
            if "Connection refused" in exc_str or "connect" in exc_str.lower():
                pytest.skip(f"Postgres not reachable: {exc}")
            raise
        finally:
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_select_channel_first_from_vitalia_patients_succeeds(self) -> None:
        """SELECT channel_first FROM vitalia_patients must NOT 500.

        This is the exact column reference in patient_repository.search() that
        caused the live 500 on GET /api/v1/crm/patients?q=.
        RED: column "channel_first" does not exist
        GREEN: SELECT returns successfully (even with 0 rows).
        """
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        url = _get_db_url()
        try:
            engine = create_async_engine(url, echo=False)
        except Exception:
            pytest.skip("asyncpg not available")

        try:
            async with engine.connect() as conn:
                # Reproduce the exact SELECT shape that caused the 500
                result = await conn.execute(
                    text(
                        """
                        SELECT id, channel_first
                        FROM vitalia_patients
                        WHERE tenant_id = :tenant_id
                          AND deleted_at IS NULL
                        LIMIT 1
                        """
                    ),
                    {"tenant_id": str(uuid4())},
                )
                # Don't care about rows — just that the query parses and executes
                result.fetchall()
        except Exception as exc:
            exc_str = str(exc)
            if "Connection refused" in exc_str or "connect" in exc_str.lower():
                pytest.skip(f"Postgres not reachable: {exc}")
            raise
        finally:
            await engine.dispose()
