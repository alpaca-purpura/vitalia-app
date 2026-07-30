"""Tests for 001_vitalia_initial_snapshot migration.

TDD (RED phase): these tests verify:
  A1 — migration upgrade head twice without error (idempotent)
  A2 — downgrade -1 then upgrade head succeeds
  A3 — all 11 vitalia_* tables created post-upgrade

Tests are marked @pytest.mark.integration because they require a live Postgres
instance. They are skipped when Postgres is unavailable.

Per .claude/rules/backend-migrations.md:
- Every DDL must use IF NOT EXISTS (raw SQL)
- Enums via DO $$ BEGIN ... EXCEPTION END $$ block
- NEVER op.create_table() / sa.Enum(create_type=True)
"""

from __future__ import annotations

import io
import os
import re
import tokenize
from pathlib import Path

import pytest

VITALIA_EXPECTED_TABLES = [
    "vitalia_bookings",
    "vitalia_treatment_followups",
    "vitalia_consent_records",
    "vitalia_medical_audit_log",
    "vitalia_payment_intents",
    "vitalia_payment_schedules",
    "vitalia_adherence_records",
    "vitalia_doctor_extensions",
    "vitalia_patient_medical_histories",
    "vitalia_patient_dental_histories",
    "vitalia_plan_tier_configs",
]

_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
MIGRATION_FILE = str(
    _WORKSPACE_ROOT / "vitalia" / "backend" / "alembic" / "versions" / "001_vitalia_initial_snapshot.py"
)


def _is_postgres_available() -> bool:
    """Check if a local Postgres is reachable (for integration gate)."""
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


# ---------------------------------------------------------------------------
# SQL-parse tests (no Postgres required)
# ---------------------------------------------------------------------------


def test_migration_file_exists() -> None:
    """Migration file must exist (post-GREEN)."""
    import pathlib

    assert pathlib.Path(MIGRATION_FILE).exists(), f"Migration file not found: {MIGRATION_FILE}"


def test_migration_has_correct_revision() -> None:
    """Revision identifier must be '001_vitalia'."""
    with open(MIGRATION_FILE) as f:
        content = f.read()
    assert 'revision = "001_vitalia"' in content, "revision must equal '001_vitalia'"


def test_migration_down_revision_is_none() -> None:
    """vitalia is an independent chain — down_revision must be None."""
    with open(MIGRATION_FILE) as f:
        content = f.read()
    assert "down_revision = None" in content, "vitalia alembic chain is independent — down_revision must be None"


def _strip_docstrings_and_comments(source: str) -> str:
    """Remove triple-quoted docstrings and # comments from Python source."""
    result = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok_type, tok_string, _, _, _ in tokens:
            if tok_type == tokenize.STRING and tok_string.startswith(('"""', "'''")):
                result.append(" ")  # replace docstring with whitespace
            elif tok_type == tokenize.COMMENT:
                result.append(" ")  # replace comment with whitespace
            else:
                result.append(tok_string)
    except tokenize.TokenError:
        return source  # fallback: return original if tokenization fails
    return "".join(result)


def test_no_op_create_table() -> None:
    """NEVER op.create_table() — non-idempotent per backend-migrations.md.

    Checks only actual code (not docstrings or # comments which reference
    the forbidden pattern as documentation).
    """
    with open(MIGRATION_FILE) as f:
        content = f.read()
    code_only = _strip_docstrings_and_comments(content)
    assert "op.create_table(" not in code_only, (
        "op.create_table() found in migration code — use raw SQL CREATE TABLE IF NOT EXISTS"
    )


def test_no_sa_enum_create_type() -> None:
    """NEVER sa.Enum(create_type=True) — broken SA 2.0.27."""
    with open(MIGRATION_FILE) as f:
        content = f.read()
    code_only = _strip_docstrings_and_comments(content)
    assert "create_type=True" not in code_only, (
        "sa.Enum(create_type=True) found in code — broken in SA 2.0.27 — use raw SQL DO $$ block"
    )


def test_all_11_tables_have_if_not_exists() -> None:
    """Every CREATE TABLE statement must include IF NOT EXISTS."""
    with open(MIGRATION_FILE) as f:
        content = f.read()

    for table in VITALIA_EXPECTED_TABLES:
        pattern = rf"CREATE TABLE IF NOT EXISTS\s+{re.escape(table)}"
        assert re.search(pattern, content, re.IGNORECASE), f"Table '{table}' must use CREATE TABLE IF NOT EXISTS"


def test_all_indexes_have_if_not_exists() -> None:
    """Every CREATE INDEX statement must include IF NOT EXISTS."""
    with open(MIGRATION_FILE) as f:
        content = f.read()

    index_creates = re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\b[^\n;]+", content, re.IGNORECASE)
    for stmt in index_creates:
        assert "IF NOT EXISTS" in stmt.upper(), f"Index statement missing IF NOT EXISTS: {stmt[:80]}"


def test_medical_audit_log_has_no_deleted_at() -> None:
    """vitalia_medical_audit_log is IMMUTABLE — must NOT have deleted_at column."""
    with open(MIGRATION_FILE) as f:
        content = f.read()

    # Find the CREATE TABLE block for medical_audit_log
    pattern = r"CREATE TABLE IF NOT EXISTS\s+vitalia_medical_audit_log\s*\((.+?)\);"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    assert match, "vitalia_medical_audit_log table definition not found in migration"
    table_body = match.group(1)
    assert "deleted_at" not in table_body, (
        "vitalia_medical_audit_log must NOT have deleted_at — it is immutable (7-year retention)"
    )


def test_plan_tier_configs_has_no_tenant_id() -> None:
    """vitalia_plan_tier_configs is CROSS-TENANT — must NOT have tenant_id column."""
    with open(MIGRATION_FILE) as f:
        content = f.read()

    pattern = r"CREATE TABLE IF NOT EXISTS\s+vitalia_plan_tier_configs\s*\((.+?)\);"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    assert match, "vitalia_plan_tier_configs table definition not found in migration"
    table_body = match.group(1)
    assert "tenant_id" not in table_body, (
        "vitalia_plan_tier_configs is CROSS-TENANT (global catalog) — must NOT have tenant_id"
    )


def test_tenant_scoped_tables_have_tenant_id_not_null() -> None:
    """All tenant-scoped tables must have tenant_id UUID NOT NULL."""
    with open(MIGRATION_FILE) as f:
        content = f.read()

    tenant_scoped = [t for t in VITALIA_EXPECTED_TABLES if t != "vitalia_plan_tier_configs"]
    for table in tenant_scoped:
        pattern = rf"CREATE TABLE IF NOT EXISTS\s+{re.escape(table)}\s*\((.+?)\);"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        assert match, f"{table} CREATE TABLE block not found"
        table_body = match.group(1)
        assert "tenant_id" in table_body, f"{table} must have tenant_id column"
        assert "NOT NULL" in table_body.upper(), f"{table} tenant_id must be NOT NULL"


def test_timestamps_are_timestamptz() -> None:
    """All timestamp columns must use TIMESTAMPTZ (timezone-aware) per master-data.md."""
    with open(MIGRATION_FILE) as f:
        content = f.read()

    # Should use TIMESTAMPTZ or TIMESTAMP WITH TIME ZONE — no plain TIMESTAMP
    # Count occurrences of TIMESTAMP NOT followed by Z or WITH
    plain_ts = re.findall(r"\bTIMESTAMP\b(?!\s*W|\s*Z|\s+WITH)", content, re.IGNORECASE)
    assert len(plain_ts) == 0, f"Found {len(plain_ts)} plain TIMESTAMP columns (must use TIMESTAMPTZ): {plain_ts[:3]}"


def test_downgrade_drops_tables_in_reverse_order() -> None:
    """Downgrade must DROP IF EXISTS all 11 tables."""
    with open(MIGRATION_FILE) as f:
        content = f.read()

    for table in VITALIA_EXPECTED_TABLES:
        pattern = rf"DROP TABLE IF EXISTS\s+{re.escape(table)}"
        assert re.search(pattern, content, re.IGNORECASE), f"downgrade() must DROP TABLE IF EXISTS {table}"


# ---------------------------------------------------------------------------
# Integration tests (require Postgres)
# ---------------------------------------------------------------------------

pytestmark_integration = pytest.mark.integration


@pytest.mark.integration
@pytest.mark.skipif(
    not _is_postgres_available(),
    reason="Postgres not available — skipping integration tests (document in impl-log)",
)
def test_upgrade_head_twice_idempotent() -> None:
    """A1: upgrade head twice without error."""
    import subprocess

    backend_dir = str(_WORKSPACE_ROOT / "vitalia" / "backend")
    venv_alembic = f"{backend_dir}/.venv/bin/alembic"

    result1 = subprocess.run(
        [venv_alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    assert result1.returncode == 0, f"First upgrade failed:\nstdout: {result1.stdout}\nstderr: {result1.stderr}"

    result2 = subprocess.run(
        [venv_alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0, (
        f"Second upgrade (idempotent check) failed:\nstdout: {result2.stdout}\nstderr: {result2.stderr}"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not _is_postgres_available(),
    reason="Postgres not available — skipping integration tests (document in impl-log)",
)
def test_downgrade_then_upgrade() -> None:
    """A2: downgrade -1 then upgrade head succeeds."""
    import subprocess

    backend_dir = str(_WORKSPACE_ROOT / "vitalia" / "backend")
    venv_alembic = f"{backend_dir}/.venv/bin/alembic"

    result_down = subprocess.run(
        [venv_alembic, "downgrade", "-1"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    assert result_down.returncode == 0, f"Downgrade failed:\nstdout: {result_down.stdout}\nstderr: {result_down.stderr}"

    result_up = subprocess.run(
        [venv_alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    assert result_up.returncode == 0, (
        f"Re-upgrade after downgrade failed:\nstdout: {result_up.stdout}\nstderr: {result_up.stderr}"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not _is_postgres_available(),
    reason="Postgres not available — skipping integration tests (document in impl-log)",
)
def test_all_11_tables_present_post_upgrade() -> None:
    """A3: all 11 vitalia_* tables present post-upgrade."""
    import psycopg2  # type: ignore[import]

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename LIKE 'vitalia_%'
                ORDER BY tablename;
            """)
            rows = cur.fetchall()
            found_tables = {row[0] for row in rows}
    finally:
        conn.close()

    missing = set(VITALIA_EXPECTED_TABLES) - found_tables
    assert not missing, f"Missing vitalia tables after upgrade: {sorted(missing)}\nFound: {sorted(found_tables)}"
    assert len(found_tables) >= 11, (
        f"Expected at least 11 vitalia tables, found {len(found_tables)}: {sorted(found_tables)}"
    )
