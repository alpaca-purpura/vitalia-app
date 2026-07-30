"""TDD RED-first tests for migration 035_vitalia_crm_phi_base_tables.

Story: vitalia-crm-phi-base-tables-migration · T-1 · release F2.
ADR: ADR-vitalia-007-phi-pgcrypto-encryption.

Tests verify:
  - Migration file exists with correct revision chain (035_vitalia → 034_vitalia)
  - Raw SQL IF NOT EXISTS used throughout (no op.create_table / op.add_column / sa.Enum)
  - vitalia_patients: PHI columns are BYTEA (name/date_of_birth/dni/phone/email/address)
  - vitalia_patients: marketing_opt_out_at is TIMESTAMPTZ (NOT BYTEA — metadata)
  - vitalia_leads: net-new table with BYTEA PHI cols + status TEXT default 'new'
  - All timestamp columns are TIMESTAMPTZ
  - No indexes on ciphertext columns (ADR-007 D4)
  - downgrade: drops vitalia_leads + PHI cols from patients; does NOT drop
    vitalia_patients nor pgcrypto extension (ADR-007 D5)
  - Integration test: migration applies idempotently (2x upgrade = no-op)
    — skipped when Postgres unavailable (document in impl-log if skipped)

Per .claude/rules/backend-migrations.md:
  - IF NOT EXISTS everywhere
  - NEVER op.create_table() / op.add_column() / sa.Enum(create_type=True)
  - TIMESTAMPTZ for all timestamp columns

downstream-regression-na: brand-local vitalia migration idempotency test
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
_MIGRATION_FILE = _VERSIONS_DIR / "035_vitalia_crm_phi_base_tables.py"

# PHI BYTEA columns expected in vitalia_patients (added by 035)
_PATIENTS_PHI_BYTEA_COLS = [
    "name",
    "date_of_birth",
    "dni",
    "phone",
    "email",
    "address",
]

# PHI BYTEA columns expected in vitalia_leads (created by 035)
_LEADS_PHI_BYTEA_COLS = [
    "name",
    "email",
    "phone",
    "notes",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _migration_content() -> str:
    """Read migration 035 source."""
    return _MIGRATION_FILE.read_text(encoding="utf-8")


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


def _is_postgres_available() -> bool:
    """True SOLO cuando DATABASE_URL (SSoT del compose — alembic/env.py la prioriza) responde.

    Sin DATABASE_URL el test se SKIPea: el fallback localhost:5432 puede apuntar a
    un Postgres incidental del host (≠ DB canónica :5435) → falso RED + downgrade
    contra una DB ajena (hallazgo audit DELTA-BE 2026-06-12 — misma clase que
    test_040/test_042). La verificación canónica vive en gate 10 / container dev.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return False
    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )
    try:
        import psycopg2  # type: ignore[import]

        conn = psycopg2.connect(dsn, connect_timeout=3)
        conn.close()
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Static structural tests (no Postgres required)
# ─────────────────────────────────────────────────────────────────────────────


class TestMigration035Exists:
    """Migration 035 must exist with correct revision chain."""

    def test_migration_file_exists(self) -> None:
        """Migration 035 file must exist at alembic/versions/."""
        assert _MIGRATION_FILE.exists(), (
            f"Migration file not found: {_MIGRATION_FILE}.\n"
            "Create vitalia/backend/alembic/versions/035_vitalia_crm_phi_base_tables.py "
            "(story vitalia-crm-phi-base-tables-migration T-1)."
        )

    def test_revision_id_correct(self) -> None:
        """revision must be '035_vitalia'."""
        content = _migration_content()
        assert 'revision = "035_vitalia"' in content, "Migration 035 must declare revision = '035_vitalia'"

    def test_down_revision_points_to_034(self) -> None:
        """down_revision must be '034_vitalia' (personality_profiles hotfix)."""
        content = _migration_content()
        assert 'down_revision = "034_vitalia"' in content, "Migration 035 down_revision must be '034_vitalia'"


class TestMigration035Idempotency:
    """Every DDL statement must use IF NOT EXISTS (raw SQL pattern)."""

    def test_no_op_create_table_calls(self) -> None:
        """op.create_table() is forbidden — use raw SQL op.execute('CREATE TABLE IF NOT EXISTS ...')."""
        content = _migration_content()
        code_only = _strip_docstrings_and_comments(content)
        assert "op.create_table(" not in code_only, (
            "op.create_table() is non-idempotent. "
            "Use op.execute('CREATE TABLE IF NOT EXISTS ...') per backend-migrations.md"
        )

    def test_no_op_add_column_calls(self) -> None:
        """op.add_column() is non-idempotent — use ALTER TABLE ... ADD COLUMN IF NOT EXISTS."""
        content = _migration_content()
        code_only = _strip_docstrings_and_comments(content)
        assert "op.add_column(" not in code_only, (
            "op.add_column() is non-idempotent. "
            "Use op.execute('ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...') per backend-migrations.md"
        )

    def test_no_op_create_index_calls(self) -> None:
        """op.create_index() is non-idempotent — use CREATE INDEX IF NOT EXISTS."""
        content = _migration_content()
        code_only = _strip_docstrings_and_comments(content)
        assert "op.create_index(" not in code_only, (
            "op.create_index() is non-idempotent. "
            "Use op.execute('CREATE INDEX IF NOT EXISTS ...') per backend-migrations.md"
        )

    def test_no_sa_enum_create_type(self) -> None:
        """sa.Enum(create_type=True) is forbidden (broken in SA 2.0.27)."""
        content = _migration_content()
        code_only = _strip_docstrings_and_comments(content)
        assert "create_type=True" not in code_only, (
            "sa.Enum(create_type=True) is broken in SQLAlchemy 2.0.27. Use raw SQL per backend-migrations.md"
        )

    def test_create_extension_is_idempotent(self) -> None:
        """CREATE EXTENSION must use IF NOT EXISTS."""
        content = _migration_content()
        assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in content, (
            "pgcrypto extension must use CREATE EXTENSION IF NOT EXISTS pgcrypto"
        )

    def test_all_create_table_use_if_not_exists(self) -> None:
        """Every CREATE TABLE statement must use IF NOT EXISTS."""
        content = _migration_content()
        # Find all CREATE TABLE occurrences (case-insensitive)
        creates = re.findall(r"CREATE\s+TABLE\b[^\n;]+", content, re.IGNORECASE)
        for stmt in creates:
            assert "IF NOT EXISTS" in stmt.upper(), f"CREATE TABLE missing IF NOT EXISTS: {stmt[:80]}"

    def test_all_alter_add_column_use_if_not_exists(self) -> None:
        """Every ADD COLUMN statement must use IF NOT EXISTS."""
        content = _migration_content()
        adds = re.findall(r"ADD\s+COLUMN\b[^\n;]+", content, re.IGNORECASE)
        for stmt in adds:
            assert "IF NOT EXISTS" in stmt.upper(), f"ADD COLUMN missing IF NOT EXISTS: {stmt[:80]}"

    def test_all_create_index_use_if_not_exists(self) -> None:
        """Every CREATE INDEX statement must use IF NOT EXISTS."""
        content = _migration_content()
        indexes = re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\b[^\n;]+", content, re.IGNORECASE)
        for stmt in indexes:
            assert "IF NOT EXISTS" in stmt.upper(), f"CREATE INDEX missing IF NOT EXISTS: {stmt[:80]}"


class TestMigration035PhiColumns:
    """PHI/PII BYTEA columns must be present with correct types."""

    @pytest.mark.parametrize("col", _PATIENTS_PHI_BYTEA_COLS)
    def test_vitalia_patients_phi_col_is_bytea(self, col: str) -> None:
        """Each PHI column in vitalia_patients must be declared as BYTEA.

        Migration 035 adds these via ADD COLUMN IF NOT EXISTS.
        Encrypted at rest using pgp_sym_encrypt(:val, :kek) at repo layer.
        Per hipaa-lite.md § Encryption at rest + ADR-vitalia-007 D3.
        """
        content = _migration_content()
        # Expect: ADD COLUMN IF NOT EXISTS <col> BYTEA  (in any case)
        pattern = rf"ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+{re.escape(col)}\s+BYTEA"
        assert re.search(pattern, content, re.IGNORECASE), (
            f"vitalia_patients.{col} must be declared as BYTEA via "
            f"ADD COLUMN IF NOT EXISTS {col} BYTEA in migration 035. "
            "Per hipaa-lite.md § Encryption at rest + ADR-vitalia-007 D3."
        )

    def test_vitalia_patients_marketing_opt_out_at_is_timestamptz(self) -> None:
        """marketing_opt_out_at must be TIMESTAMPTZ (NOT BYTEA — metadata, ADR-007 D3)."""
        content = _migration_content()
        # Should exist as ADD COLUMN IF NOT EXISTS marketing_opt_out_at TIMESTAMPTZ
        assert re.search(
            r"marketing_opt_out_at\s+TIMESTAMPTZ",
            content,
            re.IGNORECASE,
        ), (
            "vitalia_patients.marketing_opt_out_at must be TIMESTAMPTZ (not BYTEA). "
            "It is metadata (not PHI), per ADR-vitalia-007 D3."
        )
        # Must NOT be declared as BYTEA
        assert not re.search(
            r"marketing_opt_out_at\s+BYTEA",
            content,
            re.IGNORECASE,
        ), "vitalia_patients.marketing_opt_out_at must NOT be BYTEA — it is metadata TIMESTAMPTZ."

    @pytest.mark.parametrize("col", _LEADS_PHI_BYTEA_COLS)
    def test_vitalia_leads_phi_col_is_bytea(self, col: str) -> None:
        """Each PHI/PII column in vitalia_leads must be declared as BYTEA.

        Migration 035 creates vitalia_leads with these columns as BYTEA.
        Encrypted at rest using pgp_sym_encrypt(:val, :kek) at repo layer.
        Per ADR-vitalia-007 D3.
        """
        content = _migration_content()
        # In CREATE TABLE vitalia_leads, col must appear with BYTEA type
        # Pattern: <col> BYTEA (with optional nullability)
        pattern = rf"\b{re.escape(col)}\s+BYTEA"
        assert re.search(pattern, content, re.IGNORECASE), (
            f"vitalia_leads.{col} must be declared as BYTEA in migration 035 "
            "CREATE TABLE vitalia_leads. Per ADR-vitalia-007 D3."
        )

    def test_vitalia_leads_status_default_new(self) -> None:
        """vitalia_leads.status must be TEXT NOT NULL DEFAULT 'new'."""
        content = _migration_content()
        assert re.search(
            r"status\s+TEXT\s+NOT\s+NULL\s+DEFAULT\s+'new'",
            content,
            re.IGNORECASE,
        ), "vitalia_leads.status must be TEXT NOT NULL DEFAULT 'new' (per 03-arch.md § 2.2 vitalia_leads schema)"

    def test_vitalia_leads_table_created(self) -> None:
        """vitalia_leads table must be created with CREATE TABLE IF NOT EXISTS."""
        content = _migration_content()
        assert re.search(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+vitalia_leads",
            content,
            re.IGNORECASE,
        ), "vitalia_leads must be created with CREATE TABLE IF NOT EXISTS vitalia_leads"

    def test_vitalia_patients_table_skeleton_present(self) -> None:
        """vitalia_patients must be reconstructed with CREATE TABLE IF NOT EXISTS (drift fix)."""
        content = _migration_content()
        assert re.search(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+vitalia_patients",
            content,
            re.IGNORECASE,
        ), (
            "Migration 035 must open with CREATE TABLE IF NOT EXISTS vitalia_patients (...) "
            "to reconstruct the skeleton on drifted DBs (drift fix per 03-arch.md § 2 note)."
        )


class TestMigration035Timestamps:
    """All timestamp columns must use TIMESTAMPTZ."""

    def test_all_timestamps_are_timestamptz(self) -> None:
        """Timestamp columns must use TIMESTAMPTZ (not plain TIMESTAMP)."""
        content = _migration_content()
        # Look for TIMESTAMP not followed by Z or WITH TIME ZONE
        plain_ts = re.findall(r"\bTIMESTAMP\b(?!\s*Z|\s*WITH\s+TIME)", content, re.IGNORECASE)
        # Exclude occurrences inside docstrings (rough check: count only code lines)
        # The raw count is a good proxy — migration 035 should have 0 plain TIMESTAMP
        assert len(plain_ts) == 0, (
            f"Found {len(plain_ts)} plain TIMESTAMP column(s) — must use TIMESTAMPTZ. First occurrence: {plain_ts[:2]}"
        )


class TestMigration035NoCiphertextIndex:
    """Indexes must NOT be created on PHI/ciphertext columns (ADR-007 D4)."""

    @pytest.mark.parametrize(
        "col",
        _PATIENTS_PHI_BYTEA_COLS + _LEADS_PHI_BYTEA_COLS,
    )
    def test_no_index_on_phi_column(self, col: str) -> None:
        """No index must be created on a PHI/ciphertext column."""
        content = _migration_content()
        pattern = rf"CREATE\s+(?:UNIQUE\s+)?INDEX[^\n;]*\b{re.escape(col)}\b"
        match = re.search(pattern, content, re.IGNORECASE)
        assert not match, (
            f"Migration 035 must NOT create an index on PHI column '{col}' (ciphertext). "
            "ADR-vitalia-007 D4: blind index is a follow-up, NOT this story. "
            f"Found: {match.group()[:80] if match else ''}"
        )


class TestMigration035Downgrade:
    """Downgrade must drop vitalia_leads + PHI cols from patients; NOT drop patients or pgcrypto."""

    def _downgrade_body(self) -> str:
        """Extract the downgrade() function body (code only, no comments/docstrings)."""
        content = _migration_content()
        match = re.search(
            r"def downgrade\(\)[^:]*:(.*?)(?=^def |\Z)",
            content,
            re.DOTALL | re.MULTILINE,
        )
        raw_body = match.group(1) if match else ""
        # Strip comments and docstrings so NOTE lines don't falsely match
        return _strip_docstrings_and_comments(raw_body)

    def test_downgrade_drops_vitalia_leads(self) -> None:
        """downgrade() must drop vitalia_leads (net-new by 035)."""
        body = self._downgrade_body()
        assert re.search(
            r"DROP\s+TABLE\s+IF\s+EXISTS\s+vitalia_leads",
            body,
            re.IGNORECASE,
        ), "downgrade() must DROP TABLE IF EXISTS vitalia_leads"

    def test_downgrade_does_not_drop_vitalia_patients(self) -> None:
        """downgrade() must NOT drop vitalia_patients (owned by 016 — ADR-007 D5)."""
        body = self._downgrade_body()
        assert not re.search(
            r"DROP\s+TABLE.*vitalia_patients",
            body,
            re.IGNORECASE,
        ), "downgrade() must NOT drop vitalia_patients — owned by migration 016. Per ADR-vitalia-007 D5."

    def test_downgrade_does_not_drop_pgcrypto(self) -> None:
        """downgrade() must NOT drop pgcrypto extension (shared — ADR-007 D5)."""
        body = self._downgrade_body()
        assert not re.search(
            r"DROP\s+EXTENSION.*pgcrypto",
            body,
            re.IGNORECASE,
        ), "downgrade() must NOT drop pgcrypto extension — it is shared by other tables. Per ADR-vitalia-007 D5."

    @pytest.mark.parametrize("col", _PATIENTS_PHI_BYTEA_COLS)
    def test_downgrade_drops_patients_phi_col(self, col: str) -> None:
        """downgrade() must drop each PHI column added by 035 from vitalia_patients."""
        body = self._downgrade_body()
        pattern = rf"DROP\s+COLUMN\s+IF\s+EXISTS\s+{re.escape(col)}"
        assert re.search(pattern, body, re.IGNORECASE), (
            f"downgrade() must DROP COLUMN IF EXISTS {col} from vitalia_patients. "
            "Only columns added by 035 are dropped (not the 016 skeleton)."
        )

    def test_downgrade_drops_marketing_opt_out_at(self) -> None:
        """downgrade() must also drop marketing_opt_out_at (added by 035)."""
        body = self._downgrade_body()
        assert re.search(
            r"DROP\s+COLUMN\s+IF\s+EXISTS\s+marketing_opt_out_at",
            body,
            re.IGNORECASE,
        ), "downgrade() must DROP COLUMN IF EXISTS marketing_opt_out_at from vitalia_patients"


# ─────────────────────────────────────────────────────────────────────────────
# Integration tests (require live Postgres)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.skipif(
    not _is_postgres_available(),
    reason=(
        "Postgres not available — skipping integration idempotency test. "
        "Document in T-1-result.md: 'integration skipped (no DB in native env); "
        "static tests GREEN; migration applied in T-3 live verification (supervised).'"
    ),
)
def test_upgrade_head_twice_idempotent() -> None:
    """SC-3: upgrade head twice without error (idempotency gate).

    A re-run of alembic upgrade head after 035 applied must be a no-op.
    IF NOT EXISTS pattern ensures every DDL is safe to re-execute.
    """
    import subprocess

    backend_dir = str(_WORKSPACE_ROOT / "vitalia" / "backend")
    venv_alembic = str(_WORKSPACE_ROOT / ".venv" / "bin" / "alembic")

    # First upgrade
    result1 = subprocess.run(
        [venv_alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(_WORKSPACE_ROOT)},
    )
    assert result1.returncode == 0, (
        f"First alembic upgrade head failed:\nstdout: {result1.stdout}\nstderr: {result1.stderr}"
    )

    # Second upgrade — must be a no-op
    result2 = subprocess.run(
        [venv_alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(_WORKSPACE_ROOT)},
    )
    assert result2.returncode == 0, (
        f"Second alembic upgrade head (idempotency check) failed:\nstdout: {result2.stdout}\nstderr: {result2.stderr}"
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not _is_postgres_available(),
    reason="Postgres not available — skipping DB column type verification",
)
def test_vitalia_patients_phi_cols_are_bytea_in_db() -> None:
    """Verify vitalia_patients PHI columns are actual BYTEA in DB post-upgrade."""
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
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'vitalia_patients'
                  AND column_name = ANY(%s)
                ORDER BY column_name
                """,
                (_PATIENTS_PHI_BYTEA_COLS,),
            )
            rows = {row[0]: row[1] for row in cur.fetchall()}
    finally:
        conn.close()

    for col in _PATIENTS_PHI_BYTEA_COLS:
        assert col in rows, f"Column vitalia_patients.{col} not found in DB"
        assert rows[col] == "bytea", f"vitalia_patients.{col} must be bytea in DB, got: {rows[col]}"


@pytest.mark.integration
@pytest.mark.skipif(
    not _is_postgres_available(),
    reason="Postgres not available — skipping DB column type verification",
)
def test_vitalia_leads_exists_with_status_default(self: None = None) -> None:  # type: ignore[assignment]
    """Verify vitalia_leads exists and status column has DEFAULT 'new'."""
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
            # Check table exists
            cur.execute(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename = 'vitalia_leads'
                """
            )
            assert cur.fetchone() is not None, "vitalia_leads table not found in DB"

            # Check status column default
            cur.execute(
                """
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = 'vitalia_leads' AND column_name = 'status'
                """
            )
            row = cur.fetchone()
            assert row is not None, "vitalia_leads.status column not found"
            col_default = row[0] or ""
            assert "new" in col_default.lower(), f"vitalia_leads.status DEFAULT must include 'new', got: {col_default}"
    finally:
        conn.close()


@pytest.mark.integration
@pytest.mark.skipif(
    not _is_postgres_available(),
    reason="Postgres not available — skipping downgrade test",
)
def test_downgrade_does_not_drop_vitalia_patients() -> None:
    """Verify downgrade drops vitalia_leads + PHI cols but keeps vitalia_patients."""
    import subprocess

    import psycopg2  # type: ignore[import]

    backend_dir = str(_WORKSPACE_ROOT / "vitalia" / "backend")
    venv_alembic = str(_WORKSPACE_ROOT / ".venv" / "bin" / "alembic")

    # Downgrade -1 (back to 034)
    result_down = subprocess.run(
        [venv_alembic, "downgrade", "-1"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(_WORKSPACE_ROOT)},
    )
    assert result_down.returncode == 0, f"Downgrade failed:\nstdout: {result_down.stdout}\nstderr: {result_down.stderr}"

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
    )
    try:
        with conn.cursor() as cur:
            # vitalia_leads must NOT exist post-downgrade
            cur.execute(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename = 'vitalia_leads'
                """
            )
            assert cur.fetchone() is None, "vitalia_leads must be dropped by downgrade (it was created by 035)"

            # vitalia_patients must still exist (owned by 016)
            cur.execute(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename = 'vitalia_patients'
                """
            )
            assert cur.fetchone() is not None, (
                "vitalia_patients must NOT be dropped by downgrade — owned by 016 (ADR-007 D5)"
            )

            # pgcrypto must still be available
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'pgcrypto'")
            assert cur.fetchone() is not None, (
                "pgcrypto extension must NOT be dropped by downgrade — shared by other tables (ADR-007 D5)"
            )
    finally:
        conn.close()

    # Re-upgrade to restore state
    result_up = subprocess.run(
        [venv_alembic, "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(_WORKSPACE_ROOT)},
    )
    assert result_up.returncode == 0, (
        f"Re-upgrade after downgrade failed:\nstdout: {result_up.stdout}\nstderr: {result_up.stderr}"
    )
