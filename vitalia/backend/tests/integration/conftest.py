"""Integration test conftest — real Postgres via asyncpg.

Tests are skipped automatically when POSTGRES_DSN env var is not set or
the DB is unreachable. Marking is done via pytest.mark.integration.

Usage:
    POSTGRES_DSN="postgresql+asyncpg://postgres:postgres@localhost:5432/vitalia_test" \
        pytest tests/integration/ -m integration -v
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Skip guard — skip all integration tests when no Postgres available
# ---------------------------------------------------------------------------

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/vitalia_test",
)


def _is_postgres_available() -> bool:
    """Probe Postgres availability by attempting a real connection.

    Returns True only if connection succeeds (DB exists + credentials work).
    Returns False if TCP connection fails OR auth fails (DB not ready for tests).
    """
    import socket

    try:
        # Quick TCP probe first
        parts = POSTGRES_DSN.split("@")[-1].split("/")[0].split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 5432
        with socket.create_connection((host, port), timeout=1):
            pass
    except OSError:
        return False

    # TCP up — verify credentials + DB exists via psycopg2 (sync, fast)
    try:
        import sqlalchemy

        engine = sqlalchemy.create_engine(
            POSTGRES_DSN.replace("+asyncpg", ""),
            connect_args={"connect_timeout": 2},
        )
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


_POSTGRES_UP = _is_postgres_available()


def pytest_collection_modifyitems(items):  # noqa: ANN001
    """Auto-skip integration tests when Postgres is down.

    Only skips tests with explicit @pytest.mark.integration decorator.
    Tests in this directory that use httpx ASGITransport (webhook tests,
    adapter unit-style tests) are NOT skipped — they don't need Postgres.
    Directory-level keyword 'integration' is intentionally NOT used as skip
    trigger to avoid blanket-skipping ASGI-only tests (T-be-8 webhook receivers).
    """
    if _POSTGRES_UP:
        return
    skip_mark = pytest.mark.skip(reason="Postgres unavailable (POSTGRES_DSN not reachable)")
    for item in items:
        # Use get_closest_marker to check EXPLICIT marker only — not directory keyword.
        if item.get_closest_marker("integration") is not None:
            item.add_marker(skip_mark)


# ---------------------------------------------------------------------------
# Async engine + session fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def engine():  # noqa: ANN201
    """Session-scoped engine. Schema must already exist (alembic upgrade head)."""
    return create_async_engine(POSTGRES_DSN, echo=False)


@pytest_asyncio.fixture
async def db_session(engine):  # noqa: ANN001, ANN201
    """Function-scoped AsyncSession with rollback cleanup."""
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session
        await session.rollback()
