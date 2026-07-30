"""Tests for Slice 1 fidelización migrations (T-1) — 020-023.

Migration files live under vitalia/backend/src/modules/vitalia/persistence/migrations/
(module-local path, NOT alembic/versions/ chain).

Tests verify:
  - All 4 migration files exist at the module-local path
  - Raw SQL IF NOT EXISTS pattern used throughout (no op.create_table / sa.Enum)
  - BYTEA columns present for PHI-encrypted fields per hipaa-lite.md
  - vitalia_re_engagement_events is PARTITION BY RANGE (trigger_at)
  - pgcrypto extension enabled in migration 020
  - All timestamps are TIMESTAMPTZ (never plain TIMESTAMP)
  - Dual filter: tenant_id + clinic_id NOT NULL in all 3 new tables
  - Soft delete: deleted_at TIMESTAMPTZ NULL in tables 020, 021, 022
  - Migration 023 uses ADD COLUMN IF NOT EXISTS for vitalia_patients
  - No op.create_table() / op.add_column() / sa.Enum(create_type=True)
  - All indexes use IF NOT EXISTS

All static tests run without Postgres. Integration tests marked @pytest.mark.integration
and skip if Postgres unavailable.

Per .claude/rules/backend-migrations.md:
- IF NOT EXISTS everywhere
- NEVER op.create_table() / sa.Enum(create_type=True)
Per vitalia/.claude/rules/hipaa-lite.md:
- Dual filter tenant_id + clinic_id on all PHI tables
- PHI BYTEA columns: notes (020), payload_phi (021), comment (022)
- pgcrypto extension mandatory for PHI encryption at rest
"""

from __future__ import annotations

import io
import os
import re
import tokenize
from pathlib import Path

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
_MIGRATIONS_DIR = _WORKSPACE_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "persistence" / "migrations"

# Expected migration files (module-local, NOT alembic/versions/)
_FIDELIZACION_MIGRATIONS: list[str] = [
    "020_slice1_treatment_plans.py",
    "021_slice1_re_engagement_events.py",
    "022_slice1_nps_responses.py",
    "023_slice1_patients_opt_in_columns.py",
]


def _is_postgres_available() -> bool:
    """Check if a local Postgres is reachable."""
    try:
        import psycopg2  # type: ignore[import]

        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "password"),
            dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
            connect_timeout=3,
        )
        conn.close()
        return True
    except Exception:
        return False


def _read_migration(filename: str) -> str:
    """Read migration file content from module-local path."""
    path = _MIGRATIONS_DIR / filename
    return path.read_text()


def _strip_docstrings_and_comments(source: str) -> str:
    """Remove triple-quoted docstrings and # comments from Python source."""
    result = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok_type, tok_string, _, _, _ in tokens:
            if tok_type == tokenize.STRING and tok_string.startswith(('"""', "'''")):
                result.append(" ")
            elif tok_type == tokenize.COMMENT:
                result.append(" ")
            else:
                result.append(tok_string)
    except tokenize.TokenError:
        return source
    return "".join(result)


# ─────────────────────────────────────────────────────────────────────────────
# Static structural tests (no Postgres required)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("filename", _FIDELIZACION_MIGRATIONS)
def test_migration_file_exists(filename: str) -> None:
    """All 4 fidelización migration files must exist at module-local path."""
    path = _MIGRATIONS_DIR / filename
    assert path.exists(), f"Migration file not found: {path}\nExpected at: {_MIGRATIONS_DIR}"


@pytest.mark.parametrize("filename", _FIDELIZACION_MIGRATIONS)
def test_no_op_create_table(filename: str) -> None:
    """No op.create_table() — non-idempotent per backend-migrations.md."""
    content = _read_migration(filename)
    code_only = _strip_docstrings_and_comments(content)
    assert "op.create_table(" not in code_only, (
        f"{filename}: op.create_table() found — use raw SQL CREATE TABLE IF NOT EXISTS"
    )


@pytest.mark.parametrize("filename", _FIDELIZACION_MIGRATIONS)
def test_no_op_add_column(filename: str) -> None:
    """No op.add_column() — non-idempotent per backend-migrations.md."""
    content = _read_migration(filename)
    code_only = _strip_docstrings_and_comments(content)
    assert "op.add_column(" not in code_only, (
        f"{filename}: op.add_column() found — use raw SQL ALTER TABLE ... ADD COLUMN IF NOT EXISTS"
    )


@pytest.mark.parametrize("filename", _FIDELIZACION_MIGRATIONS)
def test_no_sa_enum_create_type(filename: str) -> None:
    """No sa.Enum(create_type=True) — broken SA 2.0.27."""
    content = _read_migration(filename)
    code_only = _strip_docstrings_and_comments(content)
    assert "create_type=True" not in code_only, f"{filename}: sa.Enum(create_type=True) found — broken in SA 2.0.27"


@pytest.mark.parametrize("filename", _FIDELIZACION_MIGRATIONS)
def test_all_indexes_have_if_not_exists(filename: str) -> None:
    """Every CREATE INDEX statement must use IF NOT EXISTS."""
    content = _read_migration(filename)
    index_creates = re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\b[^\n;]+", content, re.IGNORECASE)
    for stmt in index_creates:
        assert "IF NOT EXISTS" in stmt.upper(), f"{filename}: index missing IF NOT EXISTS: {stmt[:100]}"


@pytest.mark.parametrize("filename", _FIDELIZACION_MIGRATIONS)
def test_all_timestamps_are_timestamptz(filename: str) -> None:
    """All timestamp columns must use TIMESTAMPTZ (never plain TIMESTAMP)."""
    content = _read_migration(filename)
    code_only = _strip_docstrings_and_comments(content)
    plain_ts = re.findall(r"\bTIMESTAMP\b(?!\s*W|\s*Z|\s+WITH)", code_only, re.IGNORECASE)
    assert len(plain_ts) == 0, f"{filename}: found plain TIMESTAMP — must use TIMESTAMPTZ: {plain_ts[:3]}"


def test_pgcrypto_extension_in_migration_020() -> None:
    """pgcrypto extension must be enabled in migration 020 (first PHI table)."""
    content = _read_migration("020_slice1_treatment_plans.py")
    assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in content, (
        "020_slice1_treatment_plans: must enable pgcrypto via "
        "CREATE EXTENSION IF NOT EXISTS pgcrypto (PHI encryption at rest per hipaa-lite.md)"
    )


def test_treatment_plans_table_created() -> None:
    """Migration 020 must create vitalia_treatment_plans with CREATE TABLE IF NOT EXISTS."""
    content = _read_migration("020_slice1_treatment_plans.py")
    assert re.search(
        r"CREATE TABLE IF NOT EXISTS\s+vitalia_treatment_plans\b",
        content,
        re.IGNORECASE,
    ), "020_slice1_treatment_plans: missing CREATE TABLE IF NOT EXISTS vitalia_treatment_plans"


def test_treatment_plans_phi_bytea_notes() -> None:
    """vitalia_treatment_plans.notes must be BYTEA (PHI encrypted per hipaa-lite.md)."""
    content = _read_migration("020_slice1_treatment_plans.py")
    assert re.search(r"\bnotes\s+BYTEA\b", content, re.IGNORECASE), (
        "020_slice1_treatment_plans: 'notes BYTEA' not found — notes is PHI, must use BYTEA for pgcrypto encryption"
    )


def test_treatment_plans_dual_filter_columns() -> None:
    """vitalia_treatment_plans must have tenant_id UUID NOT NULL + clinic_id UUID NOT NULL."""
    content = _read_migration("020_slice1_treatment_plans.py")
    assert re.search(r"\btenant_id\s+UUID\s+NOT NULL\b", content, re.IGNORECASE), (
        "020_slice1_treatment_plans: tenant_id UUID NOT NULL missing"
    )
    assert re.search(r"\bclinic_id\s+UUID\s+NOT NULL\b", content, re.IGNORECASE), (
        "020_slice1_treatment_plans: clinic_id UUID NOT NULL missing (dual filter mandatory per hipaa-lite.md)"
    )


def test_treatment_plans_soft_delete() -> None:
    """vitalia_treatment_plans must have deleted_at TIMESTAMPTZ NULL (soft delete)."""
    content = _read_migration("020_slice1_treatment_plans.py")
    assert re.search(r"\bdeleted_at\s+TIMESTAMPTZ\s+NULL\b", content, re.IGNORECASE), (
        "020_slice1_treatment_plans: deleted_at TIMESTAMPTZ NULL missing"
    )


def test_treatment_plans_indexes() -> None:
    """Migration 020 must create all 3 required indexes for vitalia_treatment_plans."""
    content = _read_migration("020_slice1_treatment_plans.py")
    required_indexes = [
        "ix_vitalia_treatment_plans_tenant_clinic_status",
        "ix_vitalia_treatment_plans_patient",
        "ix_vitalia_treatment_plans_gap_query",
    ]
    for idx in required_indexes:
        assert idx in content, f"020_slice1_treatment_plans: index '{idx}' not found"


def test_re_engagement_events_table_created() -> None:
    """Migration 021 must create vitalia_re_engagement_events with CREATE TABLE IF NOT EXISTS."""
    content = _read_migration("021_slice1_re_engagement_events.py")
    assert re.search(
        r"CREATE TABLE IF NOT EXISTS\s+vitalia_re_engagement_events\b",
        content,
        re.IGNORECASE,
    ), "021_slice1_re_engagement_events: missing CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events"


def test_re_engagement_events_partition_by_range() -> None:
    """vitalia_re_engagement_events must be PARTITION BY RANGE (trigger_at) per hipaa-lite.md."""
    content = _read_migration("021_slice1_re_engagement_events.py")
    assert "PARTITION BY RANGE" in content.upper(), (
        "021_slice1_re_engagement_events: PARTITION BY RANGE missing — required for HIPAA-lite 10y retention policy"
    )
    assert "trigger_at" in content, "021_slice1_re_engagement_events: partition key trigger_at not found"


def test_re_engagement_events_phi_bytea_payload() -> None:
    """vitalia_re_engagement_events.payload_phi must be BYTEA (PHI encrypted)."""
    content = _read_migration("021_slice1_re_engagement_events.py")
    assert re.search(r"\bpayload_phi\s+BYTEA\b", content, re.IGNORECASE), (
        "021_slice1_re_engagement_events: 'payload_phi BYTEA' not found — "
        "payload_phi is PHI, must use BYTEA for pgcrypto encryption"
    )


def test_re_engagement_events_dual_filter_columns() -> None:
    """vitalia_re_engagement_events must have tenant_id + clinic_id NOT NULL."""
    content = _read_migration("021_slice1_re_engagement_events.py")
    assert re.search(r"\btenant_id\s+UUID\s+NOT NULL\b", content, re.IGNORECASE), (
        "021_slice1_re_engagement_events: tenant_id UUID NOT NULL missing"
    )
    assert re.search(r"\bclinic_id\s+UUID\s+NOT NULL\b", content, re.IGNORECASE), (
        "021_slice1_re_engagement_events: clinic_id UUID NOT NULL missing (dual filter per hipaa-lite.md)"
    )


def test_re_engagement_events_idempotency_unique_index() -> None:
    """vitalia_re_engagement_events must have UNIQUE index on idempotency_key."""
    content = _read_migration("021_slice1_re_engagement_events.py")
    assert re.search(
        r"CREATE\s+UNIQUE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+uq_vitalia_re_engagement_events_idempotency",
        content,
        re.IGNORECASE,
    ), (
        "021_slice1_re_engagement_events: UNIQUE index uq_vitalia_re_engagement_events_idempotency not found — "
        "required for cron dedup idempotency"
    )


def test_re_engagement_events_indexes() -> None:
    """Migration 021 must create all 4 required indexes."""
    content = _read_migration("021_slice1_re_engagement_events.py")
    required_indexes = [
        "ix_vitalia_re_engagement_events_pattern_patient",
        "ix_vitalia_re_engagement_events_throttle",
        "uq_vitalia_re_engagement_events_idempotency",
        "ix_vitalia_re_engagement_events_outcome_status",
    ]
    for idx in required_indexes:
        assert idx in content, f"021_slice1_re_engagement_events: index '{idx}' not found"


def test_re_engagement_events_monthly_partitions() -> None:
    """Migration 021 must create at least 3 monthly partition tables."""
    content = _read_migration("021_slice1_re_engagement_events.py")
    partition_matches = re.findall(r"vitalia_re_engagement_events_\d{4}_\d{2}", content)
    assert len(partition_matches) >= 3, (
        f"021_slice1_re_engagement_events: expected >= 3 monthly partition tables, "
        f"found {len(partition_matches)}: {partition_matches}"
    )


def test_nps_responses_table_created() -> None:
    """Migration 022 must create vitalia_nps_responses with CREATE TABLE IF NOT EXISTS."""
    content = _read_migration("022_slice1_nps_responses.py")
    assert re.search(
        r"CREATE TABLE IF NOT EXISTS\s+vitalia_nps_responses\b",
        content,
        re.IGNORECASE,
    ), "022_slice1_nps_responses: missing CREATE TABLE IF NOT EXISTS vitalia_nps_responses"


def test_nps_responses_phi_bytea_comment() -> None:
    """vitalia_nps_responses.comment must be BYTEA (PHI encrypted — patient free text)."""
    content = _read_migration("022_slice1_nps_responses.py")
    assert re.search(r"\bcomment\s+BYTEA\b", content, re.IGNORECASE), (
        "022_slice1_nps_responses: 'comment BYTEA' not found — "
        "comment is PHI (patient text), must use BYTEA for pgcrypto encryption"
    )


def test_nps_responses_score_check_constraint() -> None:
    """vitalia_nps_responses.score must have CHECK (score >= 0 AND score <= 10)."""
    content = _read_migration("022_slice1_nps_responses.py")
    assert re.search(r"score\s+INT\s+NOT NULL\s+CHECK", content, re.IGNORECASE), (
        "022_slice1_nps_responses: score CHECK constraint missing — must enforce CHECK (score >= 0 AND score <= 10)"
    )


def test_nps_responses_dual_filter_columns() -> None:
    """vitalia_nps_responses must have tenant_id + clinic_id NOT NULL."""
    content = _read_migration("022_slice1_nps_responses.py")
    assert re.search(r"\btenant_id\s+UUID\s+NOT NULL\b", content, re.IGNORECASE), (
        "022_slice1_nps_responses: tenant_id UUID NOT NULL missing"
    )
    assert re.search(r"\bclinic_id\s+UUID\s+NOT NULL\b", content, re.IGNORECASE), (
        "022_slice1_nps_responses: clinic_id UUID NOT NULL missing (dual filter per hipaa-lite.md)"
    )


def test_nps_responses_soft_delete() -> None:
    """vitalia_nps_responses must have deleted_at TIMESTAMPTZ NULL."""
    content = _read_migration("022_slice1_nps_responses.py")
    assert re.search(r"\bdeleted_at\s+TIMESTAMPTZ\s+NULL\b", content, re.IGNORECASE), (
        "022_slice1_nps_responses: deleted_at TIMESTAMPTZ NULL missing"
    )


def test_nps_responses_indexes() -> None:
    """Migration 022 must create both required indexes."""
    content = _read_migration("022_slice1_nps_responses.py")
    required_indexes = [
        "ix_vitalia_nps_responses_tenant_clinic_band",
        "ix_vitalia_nps_responses_patient",
    ]
    for idx in required_indexes:
        assert idx in content, f"022_slice1_nps_responses: index '{idx}' not found"


def test_patients_opt_in_uses_add_column_if_not_exists() -> None:
    """Migration 023 must use ALTER TABLE ... ADD COLUMN IF NOT EXISTS (not op.add_column)."""
    content = _read_migration("023_slice1_patients_opt_in_columns.py")
    assert "ADD COLUMN IF NOT EXISTS" in content, (
        "023_slice1_patients_opt_in_columns: 'ADD COLUMN IF NOT EXISTS' missing — "
        "must use raw SQL ALTER TABLE for idempotency"
    )


def test_patients_opt_in_columns_present() -> None:
    """Migration 023 must add all 4 patient opt-in columns."""
    content = _read_migration("023_slice1_patients_opt_in_columns.py")
    for column in ("marketing_opt_in", "opt_out", "opt_out_reason", "opt_out_at"):
        assert column in content, f"023_slice1_patients_opt_in_columns: column '{column}' not found"


def test_patients_opt_in_index_present() -> None:
    """Migration 023 must create ix_vitalia_patients_opt_in_status index."""
    content = _read_migration("023_slice1_patients_opt_in_columns.py")
    assert "ix_vitalia_patients_opt_in_status" in content, (
        "023_slice1_patients_opt_in_columns: index 'ix_vitalia_patients_opt_in_status' not found"
    )


def test_patients_opt_in_targets_vitalia_patients_table() -> None:
    """Migration 023 must target the vitalia_patients table (not a new table)."""
    content = _read_migration("023_slice1_patients_opt_in_columns.py")
    assert "vitalia_patients" in content, (
        "023_slice1_patients_opt_in_columns: 'vitalia_patients' not found — "
        "migration must ALTER the existing vitalia_patients table"
    )
    # Should NOT create a new table
    assert not re.search(
        r"CREATE TABLE IF NOT EXISTS\s+vitalia_patients\b",
        content,
        re.IGNORECASE,
    ), (
        "023_slice1_patients_opt_in_columns: must ALTER existing vitalia_patients, "
        "not CREATE TABLE (table already exists from Story 11)"
    )


def test_all_new_tables_have_vitalia_prefix() -> None:
    """All new tables (020-022) use vitalia_ prefix."""
    new_table_migrations = [
        ("020_slice1_treatment_plans.py", "vitalia_treatment_plans"),
        ("021_slice1_re_engagement_events.py", "vitalia_re_engagement_events"),
        ("022_slice1_nps_responses.py", "vitalia_nps_responses"),
    ]
    for filename, expected_table in new_table_migrations:
        content = _read_migration(filename)
        assert expected_table in content, (
            f"{filename}: expected table name '{expected_table}' not found — all tables must use vitalia_ prefix"
        )


def test_no_hard_deletes_in_migrations() -> None:
    """No DELETE FROM in migrations — soft deletes only (deleted_at per backend-ddd.md)."""
    for filename in _FIDELIZACION_MIGRATIONS:
        content = _read_migration(filename)
        code_only = _strip_docstrings_and_comments(content)
        assert not re.search(r"\bDELETE\s+FROM\b", code_only, re.IGNORECASE), (
            f"{filename}: DELETE FROM found — use soft deletes (deleted_at) only"
        )


def test_upgrade_and_downgrade_functions_present() -> None:
    """All migration files must define upgrade() and downgrade() functions."""
    for filename in _FIDELIZACION_MIGRATIONS:
        content = _read_migration(filename)
        assert "def upgrade()" in content, f"{filename}: upgrade() function missing"
        assert "def downgrade()" in content, f"{filename}: downgrade() function missing"


def test_migrations_use_op_execute() -> None:
    """All migration files must use op.execute() for raw SQL (idempotent pattern)."""
    for filename in _FIDELIZACION_MIGRATIONS:
        content = _read_migration(filename)
        assert "op.execute(" in content, (
            f"{filename}: op.execute() not found — "
            "must use op.execute() with raw SQL IF NOT EXISTS per backend-migrations.md"
        )


def test_init_file_exists_in_migrations_dir() -> None:
    """persistence/migrations/__init__.py must exist (package marker)."""
    init_path = _MIGRATIONS_DIR / "__init__.py"
    assert init_path.exists(), f"__init__.py not found at: {init_path}\nmigrations directory must be a Python package"


# ─────────────────────────────────────────────────────────────────────────────
# Integration tests (require Postgres)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.skipif(not _is_postgres_available(), reason="Postgres not available")
def test_migration_020_applies_idempotent() -> None:
    """Migration 020 SQL must be idempotent (apply 2x without error)."""
    import psycopg2  # type: ignore[import]

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
        connect_timeout=3,
    )
    content = _read_migration("020_slice1_treatment_plans.py")

    # Extract SQL strings from op.execute() calls
    sql_blocks = re.findall(r'op\.execute\s*\(\s*(?:"""|\')(.+?)(?:"""|\')[\s,\)]*\)', content, re.DOTALL)

    try:
        cur = conn.cursor()
        # Apply once
        for sql in sql_blocks:
            cur.execute(sql.strip())
        conn.commit()

        # Apply again — must not raise (idempotent)
        for sql in sql_blocks:
            cur.execute(sql.strip())
        conn.commit()

        # Verify table exists
        cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'vitalia_treatment_plans'")
        assert cur.fetchone() is not None, "vitalia_treatment_plans table was not created"
        cur.close()
    finally:
        conn.close()


@pytest.mark.integration
@pytest.mark.skipif(not _is_postgres_available(), reason="Postgres not available")
def test_migration_021_applies_idempotent() -> None:
    """Migration 021 SQL must be idempotent (apply 2x without error)."""
    import psycopg2  # type: ignore[import]

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
        connect_timeout=3,
    )
    content = _read_migration("021_slice1_re_engagement_events.py")
    sql_blocks = re.findall(r'op\.execute\s*\(\s*(?:"""|\')(.+?)(?:"""|\')[\s,\)]*\)', content, re.DOTALL)

    try:
        cur = conn.cursor()
        for sql in sql_blocks:
            cur.execute(sql.strip())
        conn.commit()

        for sql in sql_blocks:
            cur.execute(sql.strip())
        conn.commit()

        cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'vitalia_re_engagement_events'")
        assert cur.fetchone() is not None, "vitalia_re_engagement_events table was not created"
        cur.close()
    finally:
        conn.close()


@pytest.mark.integration
@pytest.mark.skipif(not _is_postgres_available(), reason="Postgres not available")
def test_migration_022_applies_idempotent() -> None:
    """Migration 022 SQL must be idempotent (apply 2x without error)."""
    import psycopg2  # type: ignore[import]

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
        connect_timeout=3,
    )
    content = _read_migration("022_slice1_nps_responses.py")
    sql_blocks = re.findall(r'op\.execute\s*\(\s*(?:"""|\')(.+?)(?:"""|\')[\s,\)]*\)', content, re.DOTALL)

    try:
        cur = conn.cursor()
        for sql in sql_blocks:
            cur.execute(sql.strip())
        conn.commit()

        for sql in sql_blocks:
            cur.execute(sql.strip())
        conn.commit()

        cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'vitalia_nps_responses'")
        assert cur.fetchone() is not None, "vitalia_nps_responses table was not created"
        cur.close()
    finally:
        conn.close()


@pytest.mark.integration
@pytest.mark.skipif(not _is_postgres_available(), reason="Postgres not available")
def test_migration_023_applies_idempotent() -> None:
    """Migration 023 SQL must be idempotent (apply 2x without error)."""
    import psycopg2  # type: ignore[import]

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
        connect_timeout=3,
    )
    content = _read_migration("023_slice1_patients_opt_in_columns.py")
    sql_blocks = re.findall(r'op\.execute\s*\(\s*"([^"]+)"\s*\)', content, re.DOTALL)

    try:
        cur = conn.cursor()
        for sql in sql_blocks:
            cur.execute(sql.strip())
        conn.commit()

        for sql in sql_blocks:
            cur.execute(sql.strip())
        conn.commit()

        # Verify columns were added
        cur.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'vitalia_patients'
            AND column_name IN ('marketing_opt_in', 'opt_out', 'opt_out_reason', 'opt_out_at')
            ORDER BY column_name
            """
        )
        found = [row[0] for row in cur.fetchall()]
        expected = sorted(["marketing_opt_in", "opt_out", "opt_out_reason", "opt_out_at"])
        assert found == expected, f"Expected columns {expected} in vitalia_patients, found {found}"
        cur.close()
    finally:
        conn.close()
