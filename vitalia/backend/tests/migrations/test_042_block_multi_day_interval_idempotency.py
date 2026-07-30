# cap: clinics.lisa.doctores
"""TDD RED-first tests for migration 042_vitalia_block_multi_day_interval (delta v3 D3-F).

Story: vitalia-fase2-lisa-doctores · T-BE-recurrencia-domain.

Verifies:
  - Migration file exists at correct path with revision chain (042 → 041, lineal 8130249c)
  - Raw SQL IF NOT EXISTS throughout (no op.add_column / op.create_table / sa.Enum)
  - days_of_week JSONB + "interval" INTEGER columns declared
  - ⚠️ "interval" quoted as SQL reserved word in both ADD COLUMN and UPDATE
  - Backfill targets days_of_week IS NULL + day_of_week IS NOT NULL (idempotent guard)
  - downgrade uses IF EXISTS (idempotent both ways)
  - Integration: double upgrade is a no-op (skipped when Postgres unavailable)

Per .claude/rules/backend-migrations.md: IF NOT EXISTS everywhere; NEVER
op.create_table() / op.add_column() / sa.Enum(create_type=True).

downstream-regression-na: brand-local vitalia migration idempotency test.
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
_MIGRATION_FILE = _VERSIONS_DIR / "042_vitalia_block_multi_day_interval.py"


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


class TestMigration042Exists:
    """Migration 042 must exist with correct revision chain."""

    def test_migration_file_exists(self) -> None:
        """042_vitalia_block_multi_day_interval.py must exist at alembic/versions/."""
        assert _MIGRATION_FILE.exists(), f"Missing migration file: {_MIGRATION_FILE}"

    def test_revision_chain(self) -> None:
        """revision=042_vitalia, down_revision=041_vitalia (re-chain lineal 8130249c, ids ≤32 chars)."""
        content = _migration_content()
        assert re.search(r'revision\s*=\s*"042_vitalia"', content), (
            "revision must be '042_vitalia' (alembic_version varchar(32) — ids cortos, re-chain 8130249c)"
        )
        assert re.search(r'down_revision\s*=\s*"041_vitalia"', content), (
            "down_revision must be '041_vitalia' (cadena lineal 039→040→041→042→043)"
        )


class TestMigration042Idempotent:
    """All DDL must be idempotent raw SQL (backend-migrations.md)."""

    def test_no_forbidden_alembic_ops(self) -> None:
        """No op.add_column / op.create_table / op.create_index (non-idempotent)."""
        code = _strip_docstrings_and_comments(_migration_content())
        for forbidden in ("op.create_table", "op.add_column", "op.create_index", "sa.Enum"):
            assert forbidden not in code, f"{forbidden} is forbidden — use raw SQL IF NOT EXISTS"

    def test_days_of_week_add_column_uses_if_not_exists(self) -> None:
        """days_of_week added with ADD COLUMN IF NOT EXISTS."""
        content = _migration_content()
        assert re.search(
            r"ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+days_of_week",
            content,
            re.IGNORECASE,
        ), "days_of_week must use ADD COLUMN IF NOT EXISTS"

    def test_interval_add_column_uses_if_not_exists_and_quoted(self) -> None:
        """interval must be quoted (SQL reserved word) and use ADD COLUMN IF NOT EXISTS."""
        content = _migration_content()
        # Must be quoted with double-quotes in DDL
        assert re.search(
            r'ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+"interval"',
            content,
            re.IGNORECASE,
        ), '"interval" must be quoted and use ADD COLUMN IF NOT EXISTS'

    def test_backfill_guards_with_where_is_null(self) -> None:
        """Backfill UPDATE uses WHERE days_of_week IS NULL (idempotent — skips migrated rows)."""
        content = _migration_content()
        assert re.search(
            r"days_of_week\s+IS\s+NULL",
            content,
            re.IGNORECASE,
        ), "Backfill must guard with WHERE days_of_week IS NULL (idempotency)"

    def test_backfill_uses_quoted_interval(self) -> None:
        """Backfill SET clause must quote \"interval\" (SQL reserved word in UPDATE)."""
        content = _migration_content()
        assert re.search(
            r'"interval"\s*=',
            content,
        ), 'Backfill SET must use "interval" = (quoted)'

    def test_downgrade_uses_if_exists(self) -> None:
        """downgrade drops columns with IF EXISTS (idempotent)."""
        content = _migration_content()
        assert re.search(
            r"DROP\s+COLUMN\s+IF\s+EXISTS\s+days_of_week",
            content,
            re.IGNORECASE,
        ), "downgrade must use DROP COLUMN IF EXISTS days_of_week"
        assert re.search(
            r'DROP\s+COLUMN\s+IF\s+EXISTS\s+"interval"',
            content,
            re.IGNORECASE,
        ), 'downgrade must use DROP COLUMN IF EXISTS "interval" (quoted)'


class TestMigration042Schema:
    """Column contract per 03-arch-delta § D3-F."""

    def test_days_of_week_is_jsonb(self) -> None:
        """days_of_week JSONB (list storage)."""
        content = _migration_content()
        assert re.search(r"days_of_week\s+JSONB", content, re.IGNORECASE), "days_of_week must be JSONB type"

    def test_interval_is_integer(self) -> None:
        """\"interval\" INTEGER (weeks count)."""
        content = _migration_content()
        assert re.search(r'"interval"\s+INTEGER', content, re.IGNORECASE), '"interval" must be INTEGER type'

    def test_backfill_uses_jsonb_build_array(self) -> None:
        """Backfill wraps day_of_week in jsonb_build_array(day_of_week)."""
        content = _migration_content()
        assert re.search(r"jsonb_build_array\s*\(\s*day_of_week\s*\)", content, re.IGNORECASE), (
            "Backfill must use jsonb_build_array(day_of_week)"
        )

    def test_backfill_biweekly_maps_to_2(self) -> None:
        """Backfill CASE: freq='biweekly' → interval=2."""
        content = _migration_content()
        assert re.search(r"biweekly.*THEN\s+2", content, re.IGNORECASE | re.DOTALL), (
            "Backfill must map freq='biweekly' to interval=2"
        )

    def test_backfill_skips_one_off_rows(self) -> None:
        """Backfill WHERE filters day_of_week IS NOT NULL (one_off rows have NULL — skip)."""
        content = _migration_content()
        assert re.search(
            r"day_of_week\s+IS\s+NOT\s+NULL",
            content,
            re.IGNORECASE,
        ), "Backfill must guard with AND day_of_week IS NOT NULL (skip one_off rows)"


# ─────────────────────────────────────────────────────────────────────────────
# Integration: double upgrade no-op (skipped when Postgres unavailable)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.integration
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
