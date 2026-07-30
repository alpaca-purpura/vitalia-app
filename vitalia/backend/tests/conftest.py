"""Shared conftest for vitalia backend tests.

Hosts the shared `engine` + `db_session` async fixtures and the
`pytest_collection_modifyitems` hook that auto-skips `@pytest.mark.integration`
tests when Postgres is unreachable.

Originally lived only in `tests/integration/conftest.py`, which scoped these
fixtures to tests under that path. Other modules (e.g. fidelizacion/infrastructure)
mark tests `@pytest.mark.integration` but live outside `tests/integration/`, so
they need the fixture available here.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# ── Test-hermetic env defaults (fix 2026-06-11) ──────────────────────────────
# luana_core_platform.core.config instancia Settings() al IMPORT con
# env_file=".env" cwd-relativo — corriendo pytest nativo desde vitalia/backend
# ese archivo no existe → ValidationError (16 campos required) en ~20 tests.
# setdefault: NO pisa env real exportado (CI/container); solo llena lo ausente
# con valores sintéticos. La suite debe ser hermética — nunca depender de un
# .env local presente (synthetic-first, ver pii-sanitisation.md).
_SETTINGS_TEST_DEFAULTS = {
    "LOG_LEVEL": "INFO",
    "DOMAIN_NAME": "test.localhost",
    "TRAEFIK_NETWORK": "test-net",
    "API_SECRET_KEY": "test-secret-key-not-real",
    "WHATSAPP_API_TOKEN": "test-wa-token",
    "WHATSAPP_PHONE_NUMBER_ID": "0000000000",
    "WHATSAPP_VERIFY_TOKEN": "test-verify",
    "OPENAI_API_KEY": "sk-test-not-real",
    "REDIS_URL": "redis://localhost:6379/9",
    "QDRANT_URL": "http://localhost:6333",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "password",
    "POSTGRES_DB": "vitalia_test",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5435",
    "API_URL": "http://localhost:8002",
    # KEK sintético: unit tests de repos PHI construyen KEKClient.from_env()
    "VITALIA_PHI_KEK": "a" * 64,
}
for _k, _v in _SETTINGS_TEST_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

# DSN default alineado a la infra dev REAL del workspace: postgres compartido
# en host:5435 (compose luana_postgres_dev), creds postgres/password, DB de
# tests dedicada vitalia_test (creada + migrada vía alembic — ver README tests).
POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql+asyncpg://postgres:password@localhost:5435/vitalia_test",
)


def _is_postgres_available() -> bool:
    """Probe Postgres availability by attempting a real connection.

    Returns True only if connection succeeds (DB exists + credentials work).
    Returns False if TCP connection fails OR auth fails (DB not ready for tests).
    """
    import socket

    try:
        parts = POSTGRES_DSN.split("@")[-1].split("/")[0].split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 5432
        with socket.create_connection((host, port), timeout=1):
            pass
    except OSError:
        return False

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

    Only skips tests with explicit `@pytest.mark.integration` decorator.
    Tests using httpx ASGITransport (webhooks, adapter unit-style) are NOT skipped.
    Directory-level keyword 'integration' is intentionally NOT used as skip trigger.
    """
    if _POSTGRES_UP:
        return
    skip_mark = pytest.mark.skip(reason="Postgres unavailable (POSTGRES_DSN not reachable)")
    for item in items:
        if item.get_closest_marker("integration") is not None:
            item.add_marker(skip_mark)


@pytest.fixture(scope="session")
def engine():  # noqa: ANN201
    """Session-scoped async engine. Schema must already exist (alembic upgrade head).

    NullPool (fix 2026-06-12): el pool por default ataba conexiones al PRIMER event
    loop → 2º test async en otro loop reventaba con "attached to a different loop"
    (clase L3 pre-existente: test_doctor_cross_tenant). Sin pool, cada connect se
    ata al loop vigente. Costo: reconexión por test (aceptable en suite local).
    """
    from sqlalchemy.pool import NullPool  # noqa: PLC0415

    return create_async_engine(POSTGRES_DSN, echo=False, poolclass=NullPool)


@pytest_asyncio.fixture
async def db_session(engine):  # noqa: ANN001, ANN201
    """Function-scoped AsyncSession with rollback cleanup."""
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session
        await session.rollback()
