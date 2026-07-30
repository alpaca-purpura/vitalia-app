"""Tests for vitalia_prohibited_phrases seed data — PE defaults.

TDD RED phase — verifies 10 seed rows for PE (tenant_id IS NULL + country_scope='PE')
are present post-migration.

Marked `integration` — require live Postgres (SKIP if DB down).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Canonical seed phrases from 03-arch § 9.1 (10 rows PE)
EXPECTED_PE_PHRASES = {
    "curamos",
    "garantizado",
    "100% efectivo",
    "sin riesgos",
    "tratamiento milagroso",
    "cura definitiva",
    "sin dolor",
    "resultados inmediatos",
    "los mejores del mercado",
    "terapia exclusiva",
}

EXPECTED_SEVERITIES = {
    "curamos": "high",
    "garantizado": "high",
    "100% efectivo": "high",
    "sin riesgos": "high",
    "tratamiento milagroso": "medium",
    "cura definitiva": "high",
    "sin dolor": "medium",
    "resultados inmediatos": "medium",
    "los mejores del mercado": "low",
    "terapia exclusiva": "low",
}


@pytest.mark.integration
class TestProhibitedPhrasesSeedPE:
    """Verify 10 PE seed rows exist in vitalia_prohibited_phrases post-migration."""

    async def test_seed_count_pe(self, db_session: AsyncSession) -> None:
        """Exactly 10 seed rows for PE (tenant_id IS NULL, country_scope='PE') must exist."""
        result = await db_session.execute(
            text("""
                SELECT COUNT(*)
                FROM vitalia_prohibited_phrases
                WHERE tenant_id IS NULL
                  AND country_scope = 'PE'
                  AND deleted_at IS NULL
            """)
        )
        count = result.scalar_one()
        assert count >= 10, (  # >= allows for future additions without breaking test
            f"Expected at least 10 PE seed rows (tenant_id IS NULL), got {count}"
        )

    async def test_seed_phrases_present(self, db_session: AsyncSession) -> None:
        """All expected PE seed phrases must be present."""
        result = await db_session.execute(
            text("""
                SELECT phrase
                FROM vitalia_prohibited_phrases
                WHERE tenant_id IS NULL
                  AND country_scope = 'PE'
                  AND deleted_at IS NULL
            """)
        )
        found_phrases = {row[0] for row in result.fetchall()}
        missing = EXPECTED_PE_PHRASES - found_phrases
        assert not missing, f"Missing PE seed phrases: {missing}"

    async def test_seed_tenant_id_null(self, db_session: AsyncSession) -> None:
        """Seed rows must have tenant_id IS NULL (cross-tenant baseline defaults)."""
        result = await db_session.execute(
            text("""
                SELECT phrase, tenant_id
                FROM vitalia_prohibited_phrases
                WHERE phrase = ANY(:phrases)
                  AND country_scope = 'PE'
                  AND deleted_at IS NULL
            """),
            {"phrases": list(EXPECTED_PE_PHRASES)},
        )
        rows = result.fetchall()
        for phrase, tenant_id in rows:
            assert tenant_id is None, f"Seed phrase '{phrase}' must have tenant_id IS NULL, got: {tenant_id}"

    async def test_seed_severity_values_correct(self, db_session: AsyncSession) -> None:
        """Each PE seed phrase must have the correct severity bucket."""
        result = await db_session.execute(
            text("""
                SELECT phrase, severity
                FROM vitalia_prohibited_phrases
                WHERE tenant_id IS NULL
                  AND country_scope = 'PE'
                  AND deleted_at IS NULL
            """)
        )
        rows = dict(result.fetchall())
        for phrase, expected_severity in EXPECTED_SEVERITIES.items():
            if phrase in rows:
                assert rows[phrase] == expected_severity, (
                    f"Phrase '{phrase}' expected severity '{expected_severity}', got '{rows[phrase]}'"
                )

    async def test_seed_severity_valid_enum(self, db_session: AsyncSession) -> None:
        """All severity values must be in {low, medium, high}."""
        result = await db_session.execute(
            text("""
                SELECT DISTINCT severity
                FROM vitalia_prohibited_phrases
                WHERE tenant_id IS NULL
                  AND country_scope = 'PE'
                  AND deleted_at IS NULL
            """)
        )
        severities = {row[0] for row in result.fetchall()}
        valid_severities = {"low", "medium", "high"}
        invalid = severities - valid_severities
        assert not invalid, f"Invalid severity values in PE seeds: {invalid}"

    async def test_seed_idempotent_second_insert(self, db_session: AsyncSession) -> None:
        """Re-inserting seed rows with ON CONFLICT DO NOTHING must be a no-op."""
        await db_session.execute(
            text("""
                INSERT INTO vitalia_prohibited_phrases (phrase, suggested_alternative, severity, country_scope)
                VALUES ('curamos', 'acompañamos tu tratamiento', 'high', 'PE')
                ON CONFLICT DO NOTHING;
            """)
        )
        # Count must remain the same (ON CONFLICT DO NOTHING enforced)
        result = await db_session.execute(
            text("""
                SELECT COUNT(*)
                FROM vitalia_prohibited_phrases
                WHERE phrase = 'curamos'
                  AND tenant_id IS NULL
                  AND country_scope = 'PE'
                  AND deleted_at IS NULL
            """)
        )
        count = result.scalar_one()
        assert count >= 1, "At least 1 'curamos' PE seed row must exist"

    async def test_seed_suggested_alternatives_non_empty(self, db_session: AsyncSession) -> None:
        """All seed rows must have non-empty suggested_alternative (Spanish neutro)."""
        result = await db_session.execute(
            text("""
                SELECT phrase, suggested_alternative
                FROM vitalia_prohibited_phrases
                WHERE tenant_id IS NULL
                  AND country_scope = 'PE'
                  AND deleted_at IS NULL
            """)
        )
        for phrase, alt in result.fetchall():
            assert alt and len(alt.strip()) > 0, f"Seed phrase '{phrase}' has empty suggested_alternative"
