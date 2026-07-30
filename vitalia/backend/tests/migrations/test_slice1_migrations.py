"""Smoke tests for Slice 1 migrations 002-016 (T-infra-1) + Slice 1 story migrations 017-021 (T-be-migrations-1).

Tests verify:
  - All 15 migration files exist with correct revision chain
  - Raw SQL IF NOT EXISTS pattern used throughout (no op.create_table / sa.Enum)
  - BYTEA columns present for PHI-encrypted fields per hipaa-lite.md
  - audit_log table is partitioned (PARTITION BY RANGE)
  - pgcrypto extension enabled
  - maintenance_schedule_enum exists in migration SQL
  - tenants location columns present in migration 014
  - offers adherence columns + check constraints present in migration 015
  - Integration tests (require Postgres) verify actual migration applies + idempotency

All static tests run without Postgres. Integration tests marked @pytest.mark.integration
and skip if Postgres unavailable.

Per .claude/rules/backend-migrations.md:
- IF NOT EXISTS everywhere
- Enum via DO $$ BEGIN ... EXCEPTION WHEN duplicate_object END $$ block
- NEVER op.create_table() / sa.Enum(create_type=True)
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
_VERSIONS_DIR = _WORKSPACE_ROOT / "vitalia" / "backend" / "alembic" / "versions"

# Expected migration files and revision IDs
_MIGRATIONS: list[tuple[str, str, str | None]] = [
    # (filename, revision, down_revision)
    ("001_vitalia_initial_snapshot.py", "001_vitalia", None),
    ("002_vitalia_appointments_columns.py", "002_vitalia", "001_vitalia"),
    ("003_vitalia_payment_events.py", "003_vitalia", "002_vitalia"),
    ("004_vitalia_fiscal_receipts.py", "004_vitalia", "003_vitalia"),
    ("005_vitalia_treatment_plans.py", "005_vitalia", "004_vitalia"),
    ("006_vitalia_re_engagement_events.py", "006_vitalia", "005_vitalia"),
    ("007_vitalia_channel_sync_state.py", "007_vitalia", "006_vitalia"),
    ("008_vitalia_channel_metrics.py", "008_vitalia", "007_vitalia"),
    ("009_vitalia_lucas_recommendations.py", "009_vitalia", "008_vitalia"),
    ("010_vitalia_referrals.py", "010_vitalia", "009_vitalia"),
    ("011_vitalia_onboarding_progress.py", "011_vitalia", "010_vitalia"),
    ("012_vitalia_brand_studio_drafts.py", "012_vitalia", "011_vitalia"),
    ("013_vitalia_audit_log.py", "013_vitalia", "012_vitalia"),
    ("014_vitalia_tenants_columns.py", "014_vitalia", "013_vitalia"),
    ("015_vitalia_offers_columns.py", "015_vitalia", "014_vitalia"),
    ("016_vitalia_patients_columns.py", "016_vitalia", "015_vitalia"),
]

# Slice 1 new tables (002-013)
_SLICE1_NEW_TABLES = [
    "vitalia_appointments",
    "vitalia_payment_events",
    "vitalia_fiscal_receipts",
    "vitalia_treatment_plans",
    "vitalia_re_engagement_events",
    "vitalia_channel_sync_state",
    "vitalia_channel_metrics",
    "vitalia_lucas_recommendations",
    "vitalia_referrals",
    "vitalia_onboarding_progress",
    "vitalia_brand_studio_drafts",
    "vitalia_audit_log",
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
    """Read migration file content."""
    path = _VERSIONS_DIR / filename
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


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS)
def test_migration_file_exists(filename: str, revision: str, down_revision: str | None) -> None:
    """All 16 migration files (001-016) must exist."""
    path = _VERSIONS_DIR / filename
    assert path.exists(), f"Migration file not found: {path}"


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS)
def test_migration_revision_ids(filename: str, revision: str, down_revision: str | None) -> None:
    """Each migration must declare correct revision and down_revision."""
    content = _read_migration(filename)
    assert f'revision = "{revision}"' in content, f"{filename}: revision must be '{revision}'"
    if down_revision is None:
        assert "down_revision = None" in content, f"{filename}: vitalia chain root must have down_revision = None"
    else:
        assert f'down_revision = "{down_revision}"' in content, f"{filename}: down_revision must be '{down_revision}'"


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS)
def test_no_op_create_table(filename: str, revision: str, down_revision: str | None) -> None:
    """No op.create_table() in any migration — non-idempotent per backend-migrations.md."""
    content = _read_migration(filename)
    code_only = _strip_docstrings_and_comments(content)
    assert "op.create_table(" not in code_only, (
        f"{filename}: op.create_table() found — use raw SQL CREATE TABLE IF NOT EXISTS"
    )


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS)
def test_no_sa_enum_create_type(filename: str, revision: str, down_revision: str | None) -> None:
    """No sa.Enum(create_type=True) — broken SA 2.0.27."""
    content = _read_migration(filename)
    code_only = _strip_docstrings_and_comments(content)
    assert "create_type=True" not in code_only, f"{filename}: sa.Enum(create_type=True) found — broken in SA 2.0.27"


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS)
def test_all_indexes_have_if_not_exists(filename: str, revision: str, down_revision: str | None) -> None:
    """Every CREATE INDEX statement must use IF NOT EXISTS."""
    content = _read_migration(filename)
    index_creates = re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\b[^\n;]+", content, re.IGNORECASE)
    for stmt in index_creates:
        assert "IF NOT EXISTS" in stmt.upper(), f"{filename}: index missing IF NOT EXISTS: {stmt[:80]}"


def test_slice1_tables_have_create_if_not_exists() -> None:
    """All Slice 1 new tables use CREATE TABLE IF NOT EXISTS."""
    all_content = ""
    for filename, _, _ in _MIGRATIONS[1:]:  # skip 001
        all_content += _read_migration(filename) + "\n"

    for table in _SLICE1_NEW_TABLES:
        pattern = rf"CREATE TABLE IF NOT EXISTS\s+{re.escape(table)}\b"
        assert re.search(pattern, all_content, re.IGNORECASE), (
            f"Table '{table}' must use CREATE TABLE IF NOT EXISTS in Slice 1 migrations"
        )


def test_pgcrypto_extension_in_migrations() -> None:
    """pgcrypto extension must be enabled in at least one migration (005 or 013)."""
    found = False
    for filename in ("005_vitalia_treatment_plans.py", "013_vitalia_audit_log.py"):
        content = _read_migration(filename)
        if "CREATE EXTENSION IF NOT EXISTS pgcrypto" in content:
            found = True
            break
    assert found, (
        "pgcrypto extension must be enabled via CREATE EXTENSION IF NOT EXISTS pgcrypto in migration 005 or 013"
    )


def test_phi_bytea_columns_present() -> None:
    """PHI-encrypted columns use BYTEA type per hipaa-lite.md § Encryption at rest."""
    phi_column_checks = [
        ("005_vitalia_treatment_plans.py", "notes", "BYTEA"),
        ("006_vitalia_re_engagement_events.py", "payload_phi", "BYTEA"),
        ("007_vitalia_channel_sync_state.py", "oauth_token_encrypted", "BYTEA"),
        ("013_vitalia_audit_log.py", "payload_redacted", "BYTEA"),
    ]
    for filename, column, col_type in phi_column_checks:
        content = _read_migration(filename)
        assert column in content, f"{filename}: expected column '{column}' not found"
        # Find the column declaration and verify BYTEA type
        pattern = rf"{re.escape(column)}\s+{re.escape(col_type)}"
        assert re.search(pattern, content, re.IGNORECASE), (
            f"{filename}: column '{column}' must be {col_type} (PHI encryption)"
        )


def test_audit_log_partitioned_by_range() -> None:
    """vitalia_audit_log must be PARTITION BY RANGE (occurred_at) per hipaa-lite.md."""
    content = _read_migration("013_vitalia_audit_log.py")
    assert "PARTITION BY RANGE" in content.upper(), (
        "013_vitalia_audit_log: vitalia_audit_log must be PARTITION BY RANGE (occurred_at)"
    )
    assert "occurred_at" in content, "013_vitalia_audit_log: partition key must be occurred_at"


def test_audit_log_has_monthly_partitions() -> None:
    """Migration 013 must create at least 3 monthly partition tables."""
    content = _read_migration("013_vitalia_audit_log.py")
    partition_matches = re.findall(r"vitalia_audit_log_\d{4}_\d{2}", content)
    assert len(partition_matches) >= 3, (
        f"013_vitalia_audit_log: expected >= 3 monthly partition tables, "
        f"found {len(partition_matches)}: {partition_matches}"
    )


def test_maintenance_schedule_enum_in_migration_015() -> None:
    """migration 015 must create maintenance_schedule_enum type."""
    content = _read_migration("015_vitalia_offers_columns.py")
    assert "maintenance_schedule_enum" in content, (
        "015_vitalia_offers_columns: maintenance_schedule_enum type not found"
    )
    # Must use DO $$ EXCEPTION WHEN duplicate_object pattern (idempotent)
    assert "EXCEPTION WHEN duplicate_object" in content, (
        "015_vitalia_offers_columns: enum must use DO $$ EXCEPTION WHEN duplicate_object END $$ block"
    )
    # Must have all 6 canonical enum values per MaintenanceScheduleEnum engine contract
    for value in ("NONE", "MONTHLY", "QUARTERLY", "BIANNUAL", "ANNUAL", "CUSTOM"):
        assert f"'{value}'" in content, f"015_vitalia_offers_columns: enum missing value '{value}'"


def test_tenants_location_columns_in_migration_014() -> None:
    """Migration 014 must add all 4 TenantLocationContract columns."""
    content = _read_migration("014_vitalia_tenants_columns.py")
    for column in ("is_onboarded", "location_country", "location_city", "timezone"):
        assert column in content, f"014_vitalia_tenants_columns: column '{column}' not found"
    # Must use ADD COLUMN IF NOT EXISTS
    assert "ADD COLUMN IF NOT EXISTS" in content, "014_vitalia_tenants_columns: must use ADD COLUMN IF NOT EXISTS"
    # Must backfill existing tenants
    assert "UPDATE tenants" in content, (
        "014_vitalia_tenants_columns: must backfill existing tenants (is_onboarded = TRUE)"
    )


def test_offers_check_constraints_in_migration_015() -> None:
    """Migration 015 must add both OfferAdherenceContract check constraints."""
    content = _read_migration("015_vitalia_offers_columns.py")
    assert "chk_offer_sessions_expected_positive" in content, (
        "015_vitalia_offers_columns: missing check constraint chk_offer_sessions_expected_positive"
    )
    assert "chk_offer_maintenance_custom_days_valid" in content, (
        "015_vitalia_offers_columns: missing check constraint chk_offer_maintenance_custom_days_valid"
    )


def test_offers_adherence_columns_in_migration_015() -> None:
    """Migration 015 must add all 5 OfferAdherenceContract columns."""
    content = _read_migration("015_vitalia_offers_columns.py")
    for column in (
        "requires_multi_session",
        "sessions_expected",
        "gap_alert_days",
        "maintenance_schedule",
        "maintenance_custom_days",
    ):
        assert column in content, f"015_vitalia_offers_columns: column '{column}' not found"


def test_patients_consent_columns_in_migration_016() -> None:
    """Migration 016 must add marketing consent columns to vitalia_patients."""
    content = _read_migration("016_vitalia_patients_columns.py")
    for column in ("marketing_opt_in", "opt_out", "opt_out_reason", "opt_out_at"):
        assert column in content, f"016_vitalia_patients_columns: column '{column}' not found"


def test_audit_log_no_deleted_at() -> None:
    """vitalia_audit_log must NOT have deleted_at — it is IMMUTABLE per hipaa-lite.md."""
    content = _read_migration("013_vitalia_audit_log.py")
    # Find the CREATE TABLE block
    pattern = r"CREATE TABLE IF NOT EXISTS\s+vitalia_audit_log\s*\((.+?)\)\s+PARTITION"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    assert match, "vitalia_audit_log CREATE TABLE block not found in 013"
    table_body = match.group(1)
    assert "deleted_at" not in table_body, (
        "vitalia_audit_log must NOT have deleted_at — it is immutable (10-year retention)"
    )


def test_all_timestamps_are_timestamptz() -> None:
    """All timestamp columns across Slice 1 migrations must use TIMESTAMPTZ."""
    for filename, _, _ in _MIGRATIONS[1:]:  # skip 001
        content = _read_migration(filename)
        # Strip docstrings/comments before checking — they may mention "timestamp" in prose
        code_only = _strip_docstrings_and_comments(content)
        # Count plain TIMESTAMP not followed by Z or WITH TIME ZONE
        plain_ts = re.findall(r"\bTIMESTAMP\b(?!\s*W|\s*Z|\s+WITH)", code_only, re.IGNORECASE)
        assert len(plain_ts) == 0, f"{filename}: found plain TIMESTAMP — must use TIMESTAMPTZ: {plain_ts[:3]}"


def test_revision_chain_is_sequential() -> None:
    """Verify the revision chain 001->002->...->016 is complete and sequential."""
    for i, (filename, revision, down_revision) in enumerate(_MIGRATIONS):
        content = _read_migration(filename)
        assert f'revision = "{revision}"' in content
        if down_revision is None:
            assert "down_revision = None" in content
        else:
            assert f'down_revision = "{down_revision}"' in content, (
                f"{filename}: expected down_revision='{down_revision}'"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Integration tests (require live Postgres)
# ─────────────────────────────────────────────────────────────────────────────

_postgres_available = _is_postgres_available()


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_migrations_apply_clean() -> None:
    """Slice 1: alembic upgrade head from 001 to 016 succeeds."""
    import subprocess

    backend_dir = str(_WORKSPACE_ROOT / "vitalia" / "backend")
    alembic = str(_WORKSPACE_ROOT / ".venv" / "bin" / "alembic")

    result = subprocess.run(
        [alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic upgrade head failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_migrations_are_idempotent() -> None:
    """Slice 1: applying upgrade head twice is a no-op (idempotent)."""
    import subprocess

    backend_dir = str(_WORKSPACE_ROOT / "vitalia" / "backend")
    alembic = str(_WORKSPACE_ROOT / ".venv" / "bin" / "alembic")

    result1 = subprocess.run(
        [alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    assert result1.returncode == 0, f"First upgrade failed: {result1.stderr}"

    result2 = subprocess.run(
        [alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0, f"Second upgrade (idempotent check) failed:\n{result2.stderr}"


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_audit_log_partitioned_monthly() -> None:
    """Verify vitalia_audit_log partition exists post-upgrade."""
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
                WHERE schemaname = 'public'
                  AND tablename LIKE 'vitalia_audit_log_%'
                ORDER BY tablename;
            """)
            rows = cur.fetchall()
            partitions = [r[0] for r in rows]
    finally:
        conn.close()

    assert len(partitions) >= 1, f"Expected at least 1 vitalia_audit_log partition, found: {partitions}"
    # Verify at least one partition follows the YYYY_MM naming pattern
    pattern = re.compile(r"vitalia_audit_log_\d{4}_\d{2}")
    assert any(pattern.match(p) for p in partitions), (
        f"No partition follows vitalia_audit_log_YYYY_MM pattern: {partitions}"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_pgcrypto_extension_enabled() -> None:
    """Verify pgcrypto extension is enabled in the database post-upgrade."""
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
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'pgcrypto';")
            row = cur.fetchone()
    finally:
        conn.close()

    assert row is not None, (
        "pgcrypto extension not found in pg_extension — required for PHI column encryption per hipaa-lite.md"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_phi_columns_bytea_type() -> None:
    """Verify PHI-encrypted columns have BYTEA type in the database."""
    import psycopg2  # type: ignore[import]

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
    )
    phi_columns = [
        ("vitalia_treatment_plans", "notes"),
        ("vitalia_re_engagement_events", "payload_phi"),
        ("vitalia_channel_sync_state", "oauth_token_encrypted"),
    ]
    try:
        with conn.cursor() as cur:
            for table, column in phi_columns:
                cur.execute(
                    """
                    SELECT data_type FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                      AND column_name = %s;
                """,
                    (table, column),
                )
                row = cur.fetchone()
                assert row is not None, f"Column {table}.{column} not found in information_schema"
                assert row[0] == "bytea", f"{table}.{column}: expected bytea, got {row[0]}"
    finally:
        conn.close()


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_maintenance_schedule_enum_exists() -> None:
    """Verify maintenance_schedule_enum type is registered in pg_type."""
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
            cur.execute("SELECT typname FROM pg_type WHERE typname = 'maintenance_schedule_enum';")
            row = cur.fetchone()
    finally:
        conn.close()

    assert row is not None, (
        "maintenance_schedule_enum type not found in pg_type — "
        "migration 015 must create it via DO $$ BEGIN CREATE TYPE ... END $$"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_tenants_location_columns_exist() -> None:
    """Verify tenants table has all 4 TenantLocationContract columns."""
    import psycopg2  # type: ignore[import]

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
    )
    expected_columns = ["is_onboarded", "location_country", "location_city", "timezone"]
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'tenants'
                ORDER BY column_name;
            """)
            rows = cur.fetchall()
            found_columns = {r[0] for r in rows}
    finally:
        conn.close()

    for col in expected_columns:
        assert col in found_columns, f"tenants.{col} not found — migration 014 (TenantLocationContract) must add it"


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_offers_adherence_columns_exist() -> None:
    """Verify offers table has all 5 OfferAdherenceContract columns + check constraints."""
    import psycopg2  # type: ignore[import]

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
    )
    expected_columns = [
        "requires_multi_session",
        "sessions_expected",
        "gap_alert_days",
        "maintenance_schedule",
        "maintenance_custom_days",
    ]
    expected_constraints = [
        "chk_offer_sessions_expected_positive",
        "chk_offer_maintenance_custom_days_valid",
    ]
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'offers'
                ORDER BY column_name;
            """)
            rows = cur.fetchall()
            found_columns = {r[0] for r in rows}

            cur.execute("""
                SELECT conname FROM pg_constraint
                WHERE conrelid = 'offers'::regclass
                  AND contype = 'c'
                ORDER BY conname;
            """)
            constraint_rows = cur.fetchall()
            found_constraints = {r[0] for r in constraint_rows}
    finally:
        conn.close()

    for col in expected_columns:
        assert col in found_columns, f"offers.{col} not found — migration 015 (OfferAdherenceContract) must add it"

    for constraint in expected_constraints:
        assert constraint in found_constraints, (
            f"offers constraint '{constraint}' not found — migration 015 must create it"
        )


# ─────────────────────────────────────────────────────────────────────────────
# T-be-migrations-1: Migrations 017-021 static tests
# ─────────────────────────────────────────────────────────────────────────────

_MIGRATIONS_017_021: list[tuple[str, str, str]] = [
    ("017_vitalia_lead_screening_events.py", "017_vitalia", "016_vitalia"),
    ("018_vitalia_attribution_matrix_snapshots.py", "018_vitalia", "017_vitalia"),
    ("019_vitalia_referrals_leaderboard_snapshots.py", "019_vitalia", "018_vitalia"),
    ("020_vitalia_langgraph_checkpoint_tables.py", "020_vitalia", "019_vitalia"),
    ("021_vitalia_screening_outcome_check.py", "021_vitalia", "020_vitalia"),
]

_NEW_STORY_TABLES = [
    "lead_screening_events",
    "attribution_matrix_snapshots",
    "referrals_leaderboard_snapshots",
]

# LangGraph checkpoint table prefixes (migration 020)
_LANGGRAPH_TABLE_PREFIXES = [
    "vitalia_wizard_onboarding_checkpoints",
    "vitalia_wizard_onboarding_checkpoint_writes",
    "vitalia_wizard_onboarding_checkpoint_blobs",
    "vitalia_lucas_analysis_checkpoints",
    "vitalia_lucas_analysis_checkpoint_writes",
    "vitalia_lucas_analysis_checkpoint_blobs",
]


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS_017_021)
def test_migration_017_021_file_exists(filename: str, revision: str, down_revision: str) -> None:
    """Migrations 017-021 must exist."""
    path = _VERSIONS_DIR / filename
    assert path.exists(), f"Migration file not found: {path}"


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS_017_021)
def test_migration_017_021_revision_ids(filename: str, revision: str, down_revision: str) -> None:
    """Each of migrations 017-021 must declare correct revision and down_revision."""
    content = _read_migration(filename)
    assert f'revision = "{revision}"' in content, f"{filename}: revision must be '{revision}'"
    assert f'down_revision = "{down_revision}"' in content, f"{filename}: down_revision must be '{down_revision}'"


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS_017_021)
def test_migration_017_021_no_op_create_table(filename: str, revision: str, down_revision: str) -> None:
    """No op.create_table() in migrations 017-021."""
    content = _read_migration(filename)
    code_only = _strip_docstrings_and_comments(content)
    assert "op.create_table(" not in code_only, (
        f"{filename}: op.create_table() found — use raw SQL CREATE TABLE IF NOT EXISTS"
    )


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS_017_021)
def test_migration_017_021_no_sa_enum_create_type(filename: str, revision: str, down_revision: str) -> None:
    """No sa.Enum(create_type=True) in migrations 017-021."""
    content = _read_migration(filename)
    code_only = _strip_docstrings_and_comments(content)
    assert "create_type=True" not in code_only, f"{filename}: sa.Enum(create_type=True) found — broken in SA 2.0.27"


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS_017_021)
def test_migration_017_021_all_indexes_if_not_exists(filename: str, revision: str, down_revision: str) -> None:
    """Every CREATE INDEX in migrations 017-021 must use IF NOT EXISTS."""
    content = _read_migration(filename)
    index_creates = re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\b[^\n;]+", content, re.IGNORECASE)
    for stmt in index_creates:
        assert "IF NOT EXISTS" in stmt.upper(), f"{filename}: index missing IF NOT EXISTS: {stmt[:80]}"


@pytest.mark.parametrize("filename,revision,down_revision", _MIGRATIONS_017_021)
def test_migration_017_021_timestamps_are_timestamptz(filename: str, revision: str, down_revision: str) -> None:
    """All timestamp columns in migrations 017-021 must use TIMESTAMPTZ."""
    content = _read_migration(filename)
    code_only = _strip_docstrings_and_comments(content)
    plain_ts = re.findall(r"\bTIMESTAMP\b(?!\s*W|\s*Z|\s+WITH)", code_only, re.IGNORECASE)
    assert len(plain_ts) == 0, f"{filename}: found plain TIMESTAMP — must use TIMESTAMPTZ: {plain_ts[:3]}"


def test_migration_017_lead_screening_events_schema() -> None:
    """Migration 017 must create lead_screening_events with all required columns."""
    content = _read_migration("017_vitalia_lead_screening_events.py")
    # Table must exist
    assert "CREATE TABLE IF NOT EXISTS lead_screening_events" in content
    # Required columns
    for column in (
        "id",
        "tenant_id",
        "clinic_id",
        "lead_id",
        "vertical",
        "questions_asked",
        "response_text",
        "outcome",
        "reasoning",
        "evaluated_at",
        "created_at",
        "deleted_at",
    ):
        assert column in content, f"017: column '{column}' not found in lead_screening_events"
    # Must have tenant+clinic+lead index
    assert "ix_lead_screening_events_tenant_clinic_lead" in content
    # Must have tenant+vertical+outcome index
    assert "ix_lead_screening_events_tenant_vertical_outcome" in content
    # Outcome stored as VARCHAR (no create_type sa.Enum)
    assert "VARCHAR" in content


def test_migration_018_attribution_matrix_snapshots_schema() -> None:
    """Migration 018 must create attribution_matrix_snapshots with required columns."""
    content = _read_migration("018_vitalia_attribution_matrix_snapshots.py")
    assert "CREATE TABLE IF NOT EXISTS attribution_matrix_snapshots" in content
    for column in (
        "id",
        "tenant_id",
        "clinic_id",
        "period_start",
        "period_end",
        "channel_breakdown",
        "total_attributed_revenue",
        "currency",
        "computed_at",
        "deleted_at",
    ):
        assert column in content, f"018: column '{column}' not found in attribution_matrix_snapshots"
    # Must have clinic+period index
    assert "ix_attribution_matrix_snapshots" in content
    # Revenue stored as NUMERIC
    assert "NUMERIC" in content


def test_migration_019_referrals_leaderboard_snapshots_schema() -> None:
    """Migration 019 must create referrals_leaderboard_snapshots with required columns."""
    content = _read_migration("019_vitalia_referrals_leaderboard_snapshots.py")
    assert "CREATE TABLE IF NOT EXISTS referrals_leaderboard_snapshots" in content
    for column in (
        "id",
        "tenant_id",
        "clinic_id",
        "period_start",
        "period_end",
        "top_referrers",
        "total_referrals",
        "total_converted",
        "computed_at",
        "deleted_at",
    ):
        assert column in content, f"019: column '{column}' not found in referrals_leaderboard_snapshots"
    assert "ix_referrals_leaderboard_snapshots" in content
    assert "JSONB" in content


def test_migration_020_langgraph_checkpoint_tables() -> None:
    """Migration 020 must create all 6 LangGraph checkpoint tables with IF NOT EXISTS."""
    content = _read_migration("020_vitalia_langgraph_checkpoint_tables.py")
    for table in _LANGGRAPH_TABLE_PREFIXES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in content, f"020: LangGraph checkpoint table '{table}' missing"


def test_migration_021_screening_outcome_check_constraint() -> None:
    """Migration 021 must add CHECK constraint for lead_screening_events.outcome."""
    content = _read_migration("021_vitalia_screening_outcome_check.py")
    # Must use idempotent approach (DO block with EXCEPTION or ADD CONSTRAINT IF NOT EXISTS via DO block)
    assert "screening_outcome_chk" in content, "021: constraint name screening_outcome_chk missing"
    # Must include all valid outcome values
    for value in ("booking_ready", "objection_handle", "disqualified", "manual_review"):
        assert value in content, f"021: outcome value '{value}' missing from CHECK constraint"
    # Must be idempotent (use DO block pattern)
    assert "DO $" in content or "DO $$" in content, "021: must use DO $$ block for idempotent constraint add"


def test_revision_chain_017_021_sequential() -> None:
    """Verify the revision chain 016->017->...->021 is complete and sequential."""
    for filename, revision, down_revision in _MIGRATIONS_017_021:
        content = _read_migration(filename)
        assert f'revision = "{revision}"' in content
        assert f'down_revision = "{down_revision}"' in content, f"{filename}: expected down_revision='{down_revision}'"


def test_new_tables_have_tenant_and_clinic_id() -> None:
    """All new PHI tables (017-019) must have tenant_id + clinic_id NOT NULL (dual filter per hipaa-lite.md)."""
    phi_migrations = [
        ("017_vitalia_lead_screening_events.py", "lead_screening_events"),
        ("018_vitalia_attribution_matrix_snapshots.py", "attribution_matrix_snapshots"),
        ("019_vitalia_referrals_leaderboard_snapshots.py", "referrals_leaderboard_snapshots"),
    ]
    for filename, table in phi_migrations:
        content = _read_migration(filename)
        assert "tenant_id" in content, f"{filename}: tenant_id missing in {table}"
        assert "clinic_id" in content, f"{filename}: clinic_id missing in {table}"
        # Ensure NOT NULL on both
        assert re.search(r"tenant_id\s+UUID\s+NOT NULL", content, re.IGNORECASE), (
            f"{filename}: tenant_id must be UUID NOT NULL"
        )
        assert re.search(r"clinic_id\s+UUID\s+NOT NULL", content, re.IGNORECASE), (
            f"{filename}: clinic_id must be UUID NOT NULL"
        )


def test_new_tables_have_soft_delete() -> None:
    """Tables 017-019 must have deleted_at TIMESTAMPTZ column for soft delete."""
    phi_migrations = [
        "017_vitalia_lead_screening_events.py",
        "018_vitalia_attribution_matrix_snapshots.py",
        "019_vitalia_referrals_leaderboard_snapshots.py",
    ]
    for filename in phi_migrations:
        content = _read_migration(filename)
        assert "deleted_at" in content, f"{filename}: deleted_at column missing (soft delete mandatory)"


# ─────────────────────────────────────────────────────────────────────────────
# T-be-migrations-1: Integration tests for 017-021 (require Postgres)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_migrations_017_021_apply_clean() -> None:
    """Migrations 017-021: alembic upgrade head succeeds from current head."""
    import subprocess

    backend_dir = str(_WORKSPACE_ROOT / "vitalia" / "backend")
    alembic = str(_WORKSPACE_ROOT / ".venv" / "bin" / "alembic")

    result = subprocess.run(
        [alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic upgrade head (017-021) failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_migrations_017_021_idempotent() -> None:
    """Migrations 017-021: applying upgrade head twice is a no-op (idempotent)."""
    import subprocess

    backend_dir = str(_WORKSPACE_ROOT / "vitalia" / "backend")
    alembic = str(_WORKSPACE_ROOT / ".venv" / "bin" / "alembic")

    r1 = subprocess.run([alembic, "upgrade", "head"], cwd=backend_dir, capture_output=True, text=True)
    assert r1.returncode == 0, f"First upgrade failed: {r1.stderr}"

    r2 = subprocess.run([alembic, "upgrade", "head"], cwd=backend_dir, capture_output=True, text=True)
    assert r2.returncode == 0, f"Second upgrade (idempotent) failed: {r2.stderr}"


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_lead_screening_events_table_exists() -> None:
    """Verify lead_screening_events table was created with correct columns."""
    import psycopg2  # type: ignore[import]

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
    )
    expected_columns = [
        "id",
        "tenant_id",
        "clinic_id",
        "lead_id",
        "vertical",
        "questions_asked",
        "response_text",
        "outcome",
        "reasoning",
        "evaluated_at",
        "created_at",
        "deleted_at",
    ]
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'lead_screening_events'
                ORDER BY column_name;
            """)
            found = {r[0] for r in cur.fetchall()}
    finally:
        conn.close()

    for col in expected_columns:
        assert col in found, f"lead_screening_events.{col} not found post-migration"


@pytest.mark.integration
@pytest.mark.skipif(
    not _postgres_available,
    reason="Postgres not available — skipping integration test (document in impl-log)",
)
def test_screening_outcome_check_constraint_exists() -> None:
    """Verify screening_outcome_chk CHECK constraint exists on lead_screening_events."""
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
                SELECT conname FROM pg_constraint
                WHERE conrelid = 'lead_screening_events'::regclass
                  AND contype = 'c'
                  AND conname = 'screening_outcome_chk';
            """)
            row = cur.fetchone()
    finally:
        conn.close()

    assert row is not None, (
        "screening_outcome_chk CHECK constraint not found on lead_screening_events — migration 021 must create it"
    )
