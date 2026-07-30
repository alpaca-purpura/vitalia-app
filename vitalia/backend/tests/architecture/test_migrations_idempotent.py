"""Architecture fitness: all vitalia migrations must be idempotent (IF NOT EXISTS).

Per .claude/rules/backend-migrations.md:
  - `op.create_table()` → FORBIDDEN (not idempotent). Use raw `op.execute("CREATE TABLE IF NOT EXISTS ...")`
  - `op.add_column()` → FORBIDDEN. Use `op.execute("ALTER TABLE x ADD COLUMN IF NOT EXISTS ...")`
  - `op.create_index()` → FORBIDDEN. Use `op.execute("CREATE INDEX IF NOT EXISTS ...")`
  - `sa.Enum(..., create_type=True)` → FORBIDDEN (broken SA 2.0.27)
  - Every DDL statement must use IF NOT EXISTS / IF EXISTS patterns

This test scans all vitalia/backend/alembic/versions/*.py migration files
using AST analysis for forbidden patterns plus regex for DDL statement validation.

Known-violations baseline follows ratchet pattern (shrink-only).

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

WS_ROOT = Path(__file__).resolve().parents[4]
MIGRATIONS_ROOT = WS_ROOT / "vitalia" / "backend" / "alembic" / "versions"

# AST: attribute calls that indicate non-idempotent Alembic ops
FORBIDDEN_OP_CALLS: frozenset[str] = frozenset(
    [
        "create_table",
        "add_column",
        "drop_column",
        "create_index",
        "drop_index",
        "drop_table",
        "create_unique_constraint",
        "drop_constraint",
    ]
)

# Regex: DDL statements in op.execute() strings that lack IF NOT EXISTS / IF EXISTS
# We specifically look for CREATE TABLE, ALTER TABLE ADD COLUMN, CREATE INDEX without IF NOT EXISTS
DDL_WITHOUT_IDEMPOTENT_PATTERNS: list[tuple[str, str]] = [
    (
        r"CREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)",
        "CREATE TABLE without IF NOT EXISTS",
    ),
    (
        r"ALTER\s+TABLE\s+\S+\s+ADD\s+COLUMN\s+(?!IF\s+NOT\s+EXISTS)",
        "ALTER TABLE ADD COLUMN without IF NOT EXISTS",
    ),
    (
        r"CREATE\s+(UNIQUE\s+)?INDEX\s+(?!IF\s+NOT\s+EXISTS)",
        "CREATE INDEX without IF NOT EXISTS",
    ),
    (
        r"DROP\s+TABLE\s+(?!IF\s+EXISTS)",
        "DROP TABLE without IF EXISTS",
    ),
    (
        r"DROP\s+INDEX\s+(?!IF\s+EXISTS)",
        "DROP INDEX without IF EXISTS",
    ),
    (
        r"DROP\s+COLUMN\s+(?!IF\s+EXISTS)",
        "DROP COLUMN without IF EXISTS",
    ),
]

# Known baseline violations at time of T-infra-4 (frozen — shrink-only).
# Format: "versions/00X_file.py::violation_description"
KNOWN_IDEMPOTENCY_VIOLATIONS: frozenset[str] = frozenset(
    [
        # Add any pre-existing violations here.
    ]
)


def _migration_files() -> list[Path]:
    """Return all .py migration files (excluding __init__.py)."""
    if not MIGRATIONS_ROOT.exists():
        return []
    return [p for p in MIGRATIONS_ROOT.glob("*.py") if p.name != "__init__.py"]


def _relative(p: Path) -> str:
    return str(p.relative_to(WS_ROOT / "vitalia" / "backend" / "alembic"))


class TestMigrationsIdempotent:
    """All vitalia Alembic migration files must use idempotent DDL patterns."""

    def test_migrations_directory_exists(self) -> None:
        """Alembic versions directory must exist."""
        assert MIGRATIONS_ROOT.exists(), (
            f"Alembic migrations versions directory not found: {MIGRATIONS_ROOT}\n"
            "Expected: vitalia/backend/alembic/versions/"
        )

    def test_migration_files_exist(self) -> None:
        """At least one migration file must exist."""
        files = _migration_files()
        assert len(files) >= 1, (
            "No migration files found in vitalia/backend/alembic/versions/. "
            "Expected Slice 1 migrations per 03-arch-be.md § 2."
        )

    def test_no_op_create_table_calls(self) -> None:
        """Migration files must not call op.create_table() — use raw SQL IF NOT EXISTS.

        op.create_table() is not idempotent: running the migration twice will fail.
        Use: op.execute("CREATE TABLE IF NOT EXISTS tablename (...)")
        """
        violations: list[str] = []

        for mig_file in _migration_files():
            source = mig_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(mig_file))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue

                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_OP_CALLS:
                    # Check it's `op.` prefix
                    if isinstance(func.value, ast.Name) and func.value.id == "op":
                        rel = _relative(mig_file)
                        key = f"{rel}::{func.attr}"
                        if key not in KNOWN_IDEMPOTENCY_VIOLATIONS:
                            violations.append(
                                f"{rel}:{node.lineno}: "
                                f"op.{func.attr}() is not idempotent — "
                                f"use raw SQL op.execute() with IF NOT EXISTS/IF EXISTS instead"
                            )

        assert violations == [], (
            "Non-idempotent Alembic op calls detected in migrations:\n" + "\n".join(violations) + "\n\nFix:\n"
            "  op.create_table(...)  →  op.execute('CREATE TABLE IF NOT EXISTS ...')\n"
            "  op.add_column(...)    →  op.execute('ALTER TABLE x ADD COLUMN IF NOT EXISTS ...')\n"
            "  op.create_index(...)  →  op.execute('CREATE INDEX IF NOT EXISTS ...')\n"
            "  op.drop_table(...)    →  op.execute('DROP TABLE IF EXISTS ...')\n"
            "Per .claude/rules/backend-migrations.md — idempotent migrations gate."
        )

    def test_no_sa_enum_create_type_true(self) -> None:
        """Migration files must not use sa.Enum(create_type=True) — broken in SA 2.0.27.

        This causes double-create errors on re-run. Use raw SQL for enum types:
          op.execute("CREATE TYPE IF NOT EXISTS myenum AS ENUM ('a', 'b')")

        Note: checks active code only (comments mentioning the anti-pattern for
        documentation purposes are excluded from the scan).
        """
        import re

        violations: list[str] = []

        for mig_file in _migration_files():
            source = mig_file.read_text(encoding="utf-8")

            # Strip comments before checking — anti-pattern docs in comments are OK.
            # Remove single-line comments (# ...) and multi-line comments (""" ... """)
            stripped = re.sub(r"#[^\n]*", "", source)  # remove # comments
            stripped = re.sub(r'""".*?"""', "", stripped, flags=re.DOTALL)  # docstrings
            stripped = re.sub(r"'''.*?'''", "", stripped, flags=re.DOTALL)  # single-quote docstrings

            if "create_type=True" in stripped or "create_type = True" in stripped:
                rel = _relative(mig_file)
                key = f"{rel}::sa_enum_create_type"
                if key not in KNOWN_IDEMPOTENCY_VIOLATIONS:
                    violations.append(
                        f"{rel}: uses sa.Enum(create_type=True) — "
                        "forbidden per .claude/rules/backend-migrations.md "
                        "(broken in SA 2.0.27). Use raw SQL CREATE TYPE IF NOT EXISTS."
                    )

        assert violations == [], "sa.Enum(create_type=True) detected in migrations:\n" + "\n".join(violations)

    def test_create_statements_use_if_not_exists(self) -> None:
        """DDL CREATE statements inside op.execute() must use IF NOT EXISTS.

        Checks the raw SQL strings passed to op.execute() for idempotency patterns.
        """
        violations: list[str] = []

        for mig_file in _migration_files():
            source = mig_file.read_text(encoding="utf-8")
            rel = _relative(mig_file)

            # Extract all string literals passed to op.execute()
            # Use AST to find op.execute("...") calls
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if not (isinstance(func, ast.Attribute) and func.attr == "execute"):
                    continue
                if not (isinstance(func.value, ast.Name) and func.value.id == "op"):
                    continue

                # Extract the SQL string from the first argument
                if not node.args:
                    continue

                sql_node = node.args[0]
                if isinstance(sql_node, ast.Constant) and isinstance(sql_node.value, str):
                    sql = sql_node.value.upper()
                elif isinstance(sql_node, ast.JoinedStr):
                    # f-string: unparse and check
                    sql = ast.unparse(sql_node).upper() if hasattr(ast, "unparse") else ""
                else:
                    continue

                for pattern, description in DDL_WITHOUT_IDEMPOTENT_PATTERNS:
                    matches = re.findall(pattern, sql, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        key = f"{rel}::{description.lower().replace(' ', '_')}"
                        if key not in KNOWN_IDEMPOTENCY_VIOLATIONS:
                            violations.append(f"{rel}:{node.lineno}: {description} — SQL statement is not idempotent")

        assert violations == [], (
            "Non-idempotent DDL statements detected in op.execute() calls:\n"
            + "\n".join(violations)
            + "\n\nAll CREATE/ALTER/DROP statements inside op.execute() must use "
            "IF NOT EXISTS / IF EXISTS qualifiers per .claude/rules/backend-migrations.md."
        )

    def test_each_migration_has_upgrade_function(self) -> None:
        """Every migration file must define an upgrade() function."""
        violations: list[str] = []

        for mig_file in _migration_files():
            source = mig_file.read_text(encoding="utf-8")
            if "def upgrade" not in source:
                violations.append(f"{_relative(mig_file)}: missing upgrade() function")

        assert violations == [], "Migration files missing upgrade() function:\n" + "\n".join(violations)

    def test_each_migration_has_downgrade_function(self) -> None:
        """Every migration file must define a downgrade() function.

        Even if downgrade is a no-op (pass), its presence is required for
        Alembic to properly manage the revision chain.
        """
        violations: list[str] = []

        for mig_file in _migration_files():
            source = mig_file.read_text(encoding="utf-8")
            if "def downgrade" not in source:
                violations.append(f"{_relative(mig_file)}: missing downgrade() function")

        assert violations == [], "Migration files missing downgrade() function:\n" + "\n".join(violations)

    def test_no_op_execute_without_sql_string(self) -> None:
        """op.execute() calls must receive a SQL string, not a SQLAlchemy construct.

        Per .claude/rules/backend-migrations.md: use raw SQL strings for all DDL.
        """
        violations: list[str] = []

        for mig_file in _migration_files():
            source = mig_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if not (isinstance(func, ast.Attribute) and func.attr == "execute"):
                    continue
                if not (isinstance(func.value, ast.Name) and func.value.id == "op"):
                    continue

                # Check first argument is a string constant (or a triple-quoted string)
                if not node.args:
                    rel = _relative(mig_file)
                    violations.append(f"{rel}:{node.lineno}: op.execute() called without arguments")
                    continue

                first_arg = node.args[0]
                if not isinstance(first_arg, (ast.Constant, ast.JoinedStr)):
                    # Non-string argument (e.g., sa.text(), Column()) — flag it
                    rel = _relative(mig_file)
                    arg_type = type(first_arg).__name__
                    violations.append(
                        f"{rel}:{node.lineno}: op.execute() receives a {arg_type} "
                        "instead of a raw SQL string — use string literal"
                    )

        assert violations == [], (
            "op.execute() calls with non-string arguments detected:\n"
            + "\n".join(violations)
            + "\n\nUse: op.execute('CREATE TABLE IF NOT EXISTS ...') with raw SQL strings."
        )
