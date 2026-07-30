"""Conftest for admin integration tests — T-4 (fn-be-webhook-clerk-integration,
fn-be-hipaa-audit-log-verify, fn-be-cross-tenant-isolation-admin).

Provides:
- HMAC-signed Clerk webhook payload factories (valid + tampered)
- Fake super-admin session fixtures
- Test tenant/clinic fixtures for cross-tenant isolation tests

Postgres-gated tests use @pytest.mark.integration.
HMAC-only tests (no DB) do NOT use @pytest.mark.integration.
"""

from __future__ import annotations

import base64
import hashlib
import hmac as hmac_lib
import json
import os
import time
from typing import Any
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: F401

# ---------------------------------------------------------------------------
# Postgres availability gate (same pattern as parent conftest)
# ---------------------------------------------------------------------------

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/vitalia_test",
)


def _is_postgres_available() -> bool:
    """Quick TCP + credentials probe — same logic as parent conftest."""
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


def pytest_collection_modifyitems(items: list[Any]) -> None:  # noqa: ANN001
    """Auto-skip @pytest.mark.integration tests when Postgres is unavailable."""
    if _POSTGRES_UP:
        return
    skip_mark = pytest.mark.skip(reason="Postgres unavailable (POSTGRES_DSN not reachable)")
    for item in items:
        if item.get_closest_marker("integration") is not None:
            item.add_marker(skip_mark)


# ---------------------------------------------------------------------------
# DB session fixtures (Postgres-gated)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_engine():  # noqa: ANN201
    """Session-scoped async engine for integration tests."""
    return create_async_engine(POSTGRES_DSN, echo=False)


@pytest_asyncio.fixture
async def db_session(test_engine):  # noqa: ANN001, ANN201
    """Function-scoped AsyncSession with rollback cleanup."""
    async_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Clerk HMAC helpers — no Postgres required
# ---------------------------------------------------------------------------

# Test webhook secret — format matches Clerk Svix format (base64 after whsec_ prefix)
# Real secret format: whsec_<base64-encoded-32-bytes>
_TEST_RAW_SECRET = b"test-vitalia-clerk-webhook-secret-32b!!"  # 40 bytes for safety
_TEST_WEBHOOK_SECRET = "whsec_" + base64.b64encode(_TEST_RAW_SECRET).decode()


def build_clerk_webhook_headers(
    raw_body: bytes,
    event_id: str | None = None,
    timestamp: str | None = None,
    secret: str | None = None,
    tamper_signature: bool = False,
) -> dict[str, str]:
    """Build Svix-signed Clerk webhook headers for testing.

    Generates valid HMAC-SHA256 signature using the Svix algorithm:
    signed_content = f"{svix_id}.{svix_timestamp}.{raw_body_str}"
    Supports `tamper_signature=True` to produce an invalid signature.

    Args:
        raw_body: Raw JSON body bytes to sign
        event_id: Svix delivery ID (default: generated uuid)
        timestamp: Unix timestamp string (default: current time)
        secret: Webhook secret (default: _TEST_WEBHOOK_SECRET)
        tamper_signature: If True, produce an invalid signature for negative tests

    Returns:
        Dict of HTTP headers: svix-id, svix-timestamp, svix-signature
    """
    _secret = secret or _TEST_WEBHOOK_SECRET
    _event_id = event_id or f"evt_test_{uuid4().hex[:16]}"
    _timestamp = timestamp or str(int(time.time()))

    # Svix HMAC algorithm: signed_content = "{id}.{timestamp}.{body}"
    signed_content = f"{_event_id}.{_timestamp}.".encode() + raw_body

    # Decode key (strip whsec_ prefix, base64-decode)
    raw_key_b64 = _secret
    if raw_key_b64.startswith("whsec_"):
        raw_key_b64 = raw_key_b64[len("whsec_") :]
    raw_key = base64.b64decode(raw_key_b64)

    digest = hmac_lib.new(raw_key, signed_content, hashlib.sha256).digest()
    sig_b64 = base64.b64encode(digest).decode()

    if tamper_signature:
        sig_b64 = "v1," + "A" * len(sig_b64)  # Invalid base64 garbage
    else:
        sig_b64 = "v1," + sig_b64

    return {
        "svix-id": _event_id,
        "svix-timestamp": _timestamp,
        "svix-signature": sig_b64,
    }


def build_clerk_user_created_payload(
    clerk_user_id: str | None = None,
    email: str = "test@vitalia.com",
) -> tuple[bytes, str]:
    """Build a Clerk user.created webhook payload.

    Returns:
        Tuple of (raw_body_bytes, clerk_user_id)
    """
    _clerk_user_id = clerk_user_id or f"user_{uuid4().hex[:16]}"
    payload = {
        "type": "user.created",
        "object": "event",
        "data": {
            "id": _clerk_user_id,
            "email_addresses": [{"email_address": email, "id": f"idn_{uuid4().hex[:8]}"}],
            "first_name": "Test",
            "last_name": "User",
            "created_at": int(time.time() * 1000),
        },
    }
    return json.dumps(payload).encode(), _clerk_user_id


# ---------------------------------------------------------------------------
# FastAPI test client (no Postgres required for webhook HMAC tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def vitalia_app():  # noqa: ANN201
    """Import vitalia FastAPI app for webhook ASGI testing.

    Returns the FastAPI app instance for use with httpx.AsyncClient.
    """
    # Set required env vars for webhook tests
    os.environ.setdefault("VITALIA_CLERK_WEBHOOK_SECRET", _TEST_WEBHOOK_SECRET)
    os.environ.setdefault("VITALIA_STRIPE_WEBHOOK_SECRET", "whsec_test_stripe_secret_123456")
    os.environ.setdefault("VITALIA_ADMIN_PASSWORD_HASH", "$2b$12$fakehashfortesting.onlythistime")

    from src.main import app  # noqa: PLC0415

    return app


@pytest_asyncio.fixture
async def webhook_client(vitalia_app):  # noqa: ANN001, ANN201
    """Async test client for webhook endpoint tests."""
    async with AsyncClient(transport=ASGITransport(app=vitalia_app), base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# Test data fixtures — tenant/clinic isolation
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant_a_id() -> UUID:
    """Fixed tenant A UUID for cross-tenant isolation tests."""
    return UUID("aaaaaaaa-0000-4000-8000-000000000001")


@pytest.fixture
def clinic_a_id() -> UUID:
    """Fixed clinic A UUID (belongs to tenant A)."""
    return UUID("aaaaaaaa-0000-4000-8000-000000000002")


@pytest.fixture
def tenant_b_id() -> UUID:
    """Fixed tenant B UUID — should NOT see tenant A data."""
    return UUID("bbbbbbbb-0000-4000-8000-000000000001")


@pytest.fixture
def clinic_b_id() -> UUID:
    """Fixed clinic B UUID (belongs to tenant B)."""
    return UUID("bbbbbbbb-0000-4000-8000-000000000002")
