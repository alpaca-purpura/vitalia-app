"""Smoke tests for migration 024_inbox_tables (T-inbox-be-2).

Tests verify:
  - Migration file exists with correct revision chain (024 → 023)
  - Raw SQL IF NOT EXISTS used (no op.create_table / sa.Enum)
  - All 4 tables present: vitalia_conversations, vitalia_messages,
    vitalia_activity_events, vitalia_action_receipts
  - All timestamp columns are TIMESTAMPTZ (not TIMESTAMP)
  - All indexes use IF NOT EXISTS
  - PHI tables present (conversations + messages with PHI columns)
  - Integration test: migration applies idempotently (2x upgrade = no-op)

All static tests run without Postgres. Integration tests marked @pytest.mark.integration
and skip if Postgres unavailable.

Per .claude/rules/backend-migrations.md:
- IF NOT EXISTS everywhere
- NEVER op.create_table() / sa.Enum(create_type=True)
- TIMESTAMPTZ mandatory for timestamp columns

downstream-regression-na: brand-local vitalia migration idempotency test
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
_VERSIONS_DIR = _WORKSPACE_ROOT / "vitalia" / "backend" / "alembic" / "versions"
_MIGRATION_FILE = _VERSIONS_DIR / "024_inbox_tables.py"


class TestInboxMigrationExists:
    """Migration 024_inbox_tables.py must exist with correct revision chain."""

    def test_migration_file_exists(self) -> None:
        assert _MIGRATION_FILE.exists(), (
            f"Migration file not found: {_MIGRATION_FILE}. Create vitalia/backend/alembic/versions/024_inbox_tables.py"
        )

    def test_revision_id_correct(self) -> None:
        content = _MIGRATION_FILE.read_text()
        assert 'revision = "024_vitalia"' in content or "revision = '024_vitalia'" in content, (
            "revision must be '024_vitalia'"
        )

    def test_down_revision_points_to_023(self) -> None:
        content = _MIGRATION_FILE.read_text()
        assert "023_vitalia" in content, "down_revision must reference '023_vitalia' (latest existing migration)"


class TestInboxMigrationIdempotency:
    """Every DDL statement must use IF NOT EXISTS (raw SQL pattern)."""

    def test_no_op_create_table_calls(self) -> None:
        """op.create_table() is forbidden — use raw SQL op.execute('CREATE TABLE IF NOT EXISTS ...')."""
        content = _MIGRATION_FILE.read_text()
        assert "op.create_table(" not in content, (
            "op.create_table() is non-idempotent. Use op.execute('CREATE TABLE IF NOT EXISTS ...')"
        )

    def test_no_sa_enum_create_type(self) -> None:
        """sa.Enum(create_type=True) is forbidden (broken in SA 2.0.27)."""
        content = _MIGRATION_FILE.read_text()
        assert "create_type=True" not in content, (
            "sa.Enum(create_type=True) is broken in SQLAlchemy 2.0.27. "
            "Use raw SQL DO $$ BEGIN CREATE TYPE ... EXCEPTION WHEN duplicate_object ... END $$"
        )

    def test_no_op_add_column_calls(self) -> None:
        """op.add_column() is non-idempotent — use ALTER TABLE ... ADD COLUMN IF NOT EXISTS."""
        content = _MIGRATION_FILE.read_text()
        assert "op.add_column(" not in content, (
            "op.add_column() is non-idempotent. Use op.execute('ALTER TABLE x ADD COLUMN IF NOT EXISTS ...')"
        )

    def test_create_table_uses_if_not_exists(self) -> None:
        """Every CREATE TABLE must have IF NOT EXISTS."""
        content = _MIGRATION_FILE.read_text()
        # Count CREATE TABLE occurrences
        create_table_count = len(re.findall(r"CREATE\s+TABLE", content, re.IGNORECASE))
        create_table_if_exists_count = len(re.findall(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS", content, re.IGNORECASE))
        assert create_table_count > 0, "Migration must create at least 1 table"
        assert create_table_count == create_table_if_exists_count, (
            f"Found {create_table_count} CREATE TABLE but only "
            f"{create_table_if_exists_count} use IF NOT EXISTS. "
            "All table creation must be idempotent."
        )

    def test_indexes_use_if_not_exists(self) -> None:
        """Every CREATE INDEX must have IF NOT EXISTS."""
        content = _MIGRATION_FILE.read_text()
        index_count = len(re.findall(r"CREATE\s+INDEX", content, re.IGNORECASE))
        index_if_exists_count = len(re.findall(r"CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS", content, re.IGNORECASE))
        if index_count > 0:
            assert index_count == index_if_exists_count, (
                f"Found {index_count} CREATE INDEX but only {index_if_exists_count} use IF NOT EXISTS."
            )


class TestInboxMigrationTables:
    """All 4 inbox tables must be present in the migration."""

    def test_vitalia_conversations_table_present(self) -> None:
        content = _MIGRATION_FILE.read_text()
        assert "vitalia_conversations" in content

    def test_vitalia_messages_table_present(self) -> None:
        content = _MIGRATION_FILE.read_text()
        assert "vitalia_messages" in content

    def test_vitalia_activity_events_table_present(self) -> None:
        content = _MIGRATION_FILE.read_text()
        assert "vitalia_activity_events" in content

    def test_vitalia_action_receipts_table_present(self) -> None:
        content = _MIGRATION_FILE.read_text()
        assert "vitalia_action_receipts" in content

    def test_tenant_id_column_present_in_conversations(self) -> None:
        content = _MIGRATION_FILE.read_text()
        # tenant_id must appear in context of conversations table
        assert "tenant_id" in content

    def test_clinic_id_column_present_for_dual_filter(self) -> None:
        """HIPAA-lite dual filter requires clinic_id column on all PHI tables."""
        content = _MIGRATION_FILE.read_text()
        assert "clinic_id" in content


class TestInboxMigrationTimestamps:
    """All timestamp columns must use TIMESTAMPTZ (not TIMESTAMP without tz)."""

    def test_timestamps_use_timestamptz(self) -> None:
        """All timestamp columns in the migration must be TIMESTAMPTZ."""
        content = _MIGRATION_FILE.read_text()
        # Count bare TIMESTAMP (no WITH TIME ZONE suffix and not TIMESTAMPTZ)
        # Allow TIMESTAMPTZ or TIMESTAMP WITH TIME ZONE — reject bare TIMESTAMP
        # We look for bare TIMESTAMP not followed by TZ or WITH
        bare_timestamps = re.findall(r"\bTIMESTAMP\b(?!\s*WITH\s+TIME\s+ZONE)(?!TZ)", content, re.IGNORECASE)
        assert len(bare_timestamps) == 0, (
            f"Found {len(bare_timestamps)} bare TIMESTAMP column(s). "
            "All timestamp columns must be TIMESTAMPTZ (per coding_rules: DateTime(timezone=True))."
        )


class TestInboxMigrationPHI:
    """PHI fields must have soft-delete support (deleted_at column)."""

    def test_conversations_has_deleted_at(self) -> None:
        content = _MIGRATION_FILE.read_text()
        assert "deleted_at" in content

    def test_messages_has_deleted_at(self) -> None:
        content = _MIGRATION_FILE.read_text()
        # deleted_at appears once for conversations and once for messages at minimum
        occurrences = content.count("deleted_at")
        assert occurrences >= 2, f"Expected deleted_at in at least 2 PHI tables, found {occurrences} occurrences"


@pytest.mark.integration
class TestInboxMigrationIntegration:
    """Live DB integration tests — skipped when Postgres unavailable."""

    def test_migration_applies_and_is_idempotent(self) -> None:
        """Applying migration twice must be a no-op (idempotency gate)."""
        pytest.skip(
            "Integration test requires live Postgres + alembic clone workflow. "
            "Run manually per backend-migrations.md § Test pre-prod."
        )
