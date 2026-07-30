# cap: clinics.lisa.doctores
"""TDD RED-first tests for migration 040_vitalia_doctor_bio_files (delta v3 D3-B).

Story: vitalia-fase2-lisa-doctores · T-BE-bio-docs.

Verifies:
  - Migration file exists with correct revision chain (040_vitalia -> 039_vitalia)
  - Raw SQL IF NOT EXISTS throughout (no op.create_table / op.add_column / sa.Enum)
  - vitalia_doctor_bio_files columns per 03-arch-delta § 3.1 (dual-filter cols,
    storage_key, filename, size_bytes BIGINT, content_type, uploaded_at TIMESTAMPTZ,
    deleted_at soft delete)
  - 2 indexes: ix_doctor_bio_files_scope + ix_doctor_bio_files_tenant
  - downgrade uses IF EXISTS
  - Integration: double upgrade is a no-op (skipped when Postgres unavailable)

Per .claude/rules/backend-migrations.md: IF NOT EXISTS everywhere; NEVER
op.create_table() / op.add_column() / sa.Enum(create_type=True); TIMESTAMPTZ.

downstream-regression-na: brand-local vitalia migration idempotency test
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import tokenize
from pathlib import Path

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
_BACKEND_DIR = _WORKSPACE_ROOT / "vitalia" / "backend"
_VERSIONS_DIR = _BACKEND_DIR / "alembic" / "versions"
_MIGRATION_FILE = _VERSIONS_DIR / "040_vitalia_doctor_bio_files.py"

_EXPECTED_COLUMNS = [
    "id",
    "tenant_id",
    "clinic_id",
    "doctor_id",
    "storage_key",
    "filename",
    "size_bytes",
    "content_type",
    "uploaded_at",
    "created_at",
    "deleted_at",
]

_EXPECTED_INDEXES = [
    "ix_doctor_bio_files_scope",
    "ix_doctor_bio_files_tenant",
]


def _migration_content() -> str:
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

    Sin DATABASE_URL el test se SKIPea: el fallback localhost:5432 de env.py puede
    apuntar a un Postgres incidental del host (≠ DB canónica :5435) → falso RED +
    mutación de una DB ajena (hallazgo audit DELTA-BE 2026-06-12). La verificación
    canónica del doble-upgrade es el clone de gate 10 / alembic en el container dev.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return False
    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )
    try:
        import psycopg2  # type: ignore[import-untyped]  # noqa: PLC0415

        conn = psycopg2.connect(dsn, connect_timeout=3)
        conn.close()
    except Exception:
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Static structural tests (no Postgres required)
# ─────────────────────────────────────────────────────────────────────────────


class TestMigration040Exists:
    """Migration 040 must exist with correct revision chain."""

    def test_migration_file_exists(self) -> None:
        """040_vitalia_doctor_bio_files.py must exist at alembic/versions/."""
        assert _MIGRATION_FILE.exists(), f"Missing migration file: {_MIGRATION_FILE}"

    def test_revision_chain(self) -> None:
        """revision=040_vitalia, down_revision=039_vitalia."""
        content = _migration_content()
        assert re.search(r'revision\s*=\s*"040_vitalia"', content), "revision must be '040_vitalia'"
        assert re.search(r'down_revision\s*=\s*"039_vitalia"', content), "down_revision must be '039_vitalia'"


class TestMigration040Idempotent:
    """All DDL must be idempotent raw SQL (backend-migrations.md)."""

    def test_no_forbidden_alembic_ops(self) -> None:
        """No op.create_table / op.add_column / op.create_index (non-idempotent)."""
        code = _strip_docstrings_and_comments(_migration_content())
        for forbidden in ("op.create_table", "op.add_column", "op.create_index", "sa.Enum"):
            assert forbidden not in code, f"{forbidden} is forbidden — use raw SQL IF NOT EXISTS"

    def test_create_table_uses_if_not_exists(self) -> None:
        """CREATE TABLE IF NOT EXISTS vitalia_doctor_bio_files."""
        content = _migration_content()
        assert re.search(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+vitalia_doctor_bio_files",
            content,
            re.IGNORECASE,
        ), "Table creation must use CREATE TABLE IF NOT EXISTS vitalia_doctor_bio_files"

    def test_two_indexes_with_if_not_exists(self) -> None:
        """Both indexes created with CREATE INDEX IF NOT EXISTS."""
        content = _migration_content()
        for idx in _EXPECTED_INDEXES:
            assert re.search(
                rf"CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+{idx}",
                content,
                re.IGNORECASE,
            ), f"Missing idempotent index creation: {idx}"

    def test_downgrade_uses_if_exists(self) -> None:
        """downgrade drops with IF EXISTS (idempotent both ways)."""
        content = _migration_content()
        assert re.search(r"DROP\s+TABLE\s+IF\s+EXISTS\s+vitalia_doctor_bio_files", content, re.IGNORECASE), (
            "downgrade must use DROP TABLE IF EXISTS vitalia_doctor_bio_files"
        )


class TestMigration040Schema:
    """Column contract per 03-arch-delta § 3.1."""

    def test_all_columns_declared(self) -> None:
        """All expected columns appear in the CREATE TABLE statement."""
        content = _migration_content()
        for col in _EXPECTED_COLUMNS:
            assert re.search(rf"^\s+{col}\s+", content, re.MULTILINE), f"Missing column in migration: {col}"

    def test_size_bytes_is_bigint(self) -> None:
        """size_bytes BIGINT NOT NULL."""
        content = _migration_content()
        assert re.search(r"size_bytes\s+BIGINT\s+NOT\s+NULL", content, re.IGNORECASE)

    def test_timestamps_are_timestamptz(self) -> None:
        """uploaded_at / created_at / deleted_at use TIMESTAMPTZ (never naive TIMESTAMP)."""
        content = _migration_content()
        for col in ("uploaded_at", "created_at", "deleted_at"):
            assert re.search(rf"{col}\s+TIMESTAMPTZ", content, re.IGNORECASE), f"{col} must be TIMESTAMPTZ"
        # No bare TIMESTAMP type (would lose timezone)
        assert not re.search(r"\sTIMESTAMP\s", content), "Use TIMESTAMPTZ, never bare TIMESTAMP"

    def test_dual_filter_columns_not_null(self) -> None:
        """tenant_id + clinic_id + doctor_id are UUID NOT NULL (hipaa-lite dual filter)."""
        content = _migration_content()
        for col in ("tenant_id", "clinic_id", "doctor_id"):
            assert re.search(rf"{col}\s+UUID\s+NOT\s+NULL", content, re.IGNORECASE), f"{col} must be UUID NOT NULL"


# ─────────────────────────────────────────────────────────────────────────────
# Integration: double upgrade no-op (skipped when Postgres unavailable)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not _is_postgres_available(), reason="Postgres unavailable — document in impl-log if skipped")
def test_double_upgrade_is_noop() -> None:
    """alembic upgrade head twice = no-op (gate 10 /test-backend equivalent).

    Runs inside the vitalia backend dir using the workspace venv alembic.
    The second upgrade must succeed without errors (IF NOT EXISTS absorbs reruns).
    """
    alembic_bin = _WORKSPACE_ROOT / ".venv" / "bin" / "alembic"
    if not alembic_bin.exists():
        pytest.skip("workspace venv alembic not found")

    env = os.environ.copy()
    for _ in range(2):
        result = subprocess.run(  # noqa: S603
            [str(alembic_bin), "upgrade", "head"],
            cwd=str(_BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, f"alembic upgrade head failed:\nstdout={result.stdout}\nstderr={result.stderr}"
