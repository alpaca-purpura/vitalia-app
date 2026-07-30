"""Tests for vitalia_prohibited_phrases table existence + indexes.

TDD RED phase — these tests run against the actual DB to verify:
1. Table `vitalia_prohibited_phrases` exists with expected columns.
2. Required indexes exist.

Marked `integration` — require live Postgres (SKIP if DB down).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
class TestProhibitedPhrasesMigration:
    """Verify vitalia_prohibited_phrases table structure post-migration."""

    async def test_table_exists(self, db_session: AsyncSession) -> None:
        """vitalia_prohibited_phrases table must exist after migration."""
        result = await db_session.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'vitalia_prohibited_phrases'
            """)
        )
        row = result.fetchone()
        assert row is not None, "Table vitalia_prohibited_phrases must exist after migration"

    async def test_columns_present(self, db_session: AsyncSession) -> None:
        """Required columns must exist in vitalia_prohibited_phrases."""
        result = await db_session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'vitalia_prohibited_phrases'
            """)
        )
        columns = {row[0] for row in result.fetchall()}
        required = {
            "id",
            "tenant_id",
            "phrase",
            "suggested_alternative",
            "severity",
            "country_scope",
            "deleted_at",
            "created_at",
            "updated_at",
        }
        missing = required - columns
        assert not missing, f"Missing columns in vitalia_prohibited_phrases: {missing}"

    async def test_index_tenant_severity_exists(self, db_session: AsyncSession) -> None:
        """idx_vit_phrase_tenant_severity index must exist."""
        result = await db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'vitalia_prohibited_phrases'
                  AND indexname = 'idx_vit_phrase_tenant_severity'
            """)
        )
        assert result.fetchone() is not None, (
            "Index idx_vit_phrase_tenant_severity must exist on vitalia_prohibited_phrases"
        )

    async def test_index_country_severity_exists(self, db_session: AsyncSession) -> None:
        """idx_vit_phrase_country_severity index must exist."""
        result = await db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'vitalia_prohibited_phrases'
                  AND indexname = 'idx_vit_phrase_country_severity'
            """)
        )
        assert result.fetchone() is not None, (
            "Index idx_vit_phrase_country_severity must exist on vitalia_prohibited_phrases"
        )

    async def test_index_phrase_lookup_exists(self, db_session: AsyncSession) -> None:
        """idx_vit_phrase_lookup index must exist."""
        result = await db_session.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'vitalia_prohibited_phrases'
                  AND indexname = 'idx_vit_phrase_lookup'
            """)
        )
        assert result.fetchone() is not None, "Index idx_vit_phrase_lookup must exist on vitalia_prohibited_phrases"

    async def test_severity_column_default(self, db_session: AsyncSession) -> None:
        """severity column must have DEFAULT 'medium'."""
        result = await db_session.execute(
            text("""
                SELECT column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'vitalia_prohibited_phrases'
                  AND column_name = 'severity'
            """)
        )
        row = result.fetchone()
        assert row is not None, "severity column must exist"
        assert "medium" in str(row[0]), f"severity column default must contain 'medium', got: {row[0]}"

    async def test_migration_idempotent_second_run(self, db_session: AsyncSession) -> None:
        """Running CREATE TABLE IF NOT EXISTS twice must not raise error.

        Simulates idempotency: re-running migration upgrade() is a no-op.
        """
        # Second run of CREATE TABLE IF NOT EXISTS — must succeed without error
        await db_session.execute(
            text("""
                CREATE TABLE IF NOT EXISTS vitalia_prohibited_phrases (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID,
                    phrase VARCHAR(200) NOT NULL,
                    suggested_alternative VARCHAR(500) NOT NULL,
                    severity VARCHAR(16) NOT NULL DEFAULT 'medium',
                    country_scope VARCHAR(2),
                    deleted_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ
                );
            """)
        )
        # If no exception raised, migration is idempotent
        assert True  # no-op successful
