"""Fixtures for IAM module tests in luana-platform.

Lifted from AISALESHT backend/tests/modules/iam/conftest.py.
Adapted: removed dependency on tests.factories (AISALESHT-specific).
Provides local TenantFactory, UserFactory, and db fixtures.
"""

import os
import sys
import uuid
from unittest.mock import MagicMock

import pytest

# --- Set mandatory env vars before any imports ---
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("DOMAIN_NAME", "localhost")
os.environ.setdefault("TRAEFIK_NETWORK", "test_network")
os.environ.setdefault("API_SECRET_KEY", "ci-test-secret-key-not-for-prod")
os.environ.setdefault("WHATSAPP_API_TOKEN", "ci-dummy-token")
os.environ.setdefault("WHATSAPP_PHONE_NUMBER_ID", "000000000")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "ci-verify-token")
os.environ.setdefault("OPENAI_API_KEY", "sk-ci-dummy-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("API_URL", "http://localhost:8000")
os.environ.setdefault("DASHBOARD_DOMAIN", "http://localhost:3000")
os.environ.setdefault("PROMPT_SOURCE", "file")
os.environ.setdefault("AI_PROVIDER", "openai")
os.environ.setdefault("AI_MODEL_NANO", "gpt-4o-mini")
os.environ.setdefault("AI_MODEL_FAST", "deepseek-v4-flash")
os.environ.setdefault("AI_MODEL_REASONING", "deepseek-v4-pro")
os.environ.setdefault("AI_MODEL_AGENT", "kimi-k2.6")
os.environ.setdefault("AI_MODEL_VISION", "gpt-4o")
os.environ.setdefault("AI_MODEL_EMBEDDING", "text-embedding-3-large")
os.environ.setdefault("AI_PROVIDER_NANO", "openai")
os.environ.setdefault("AI_PROVIDER_FAST", "deepseek")
os.environ.setdefault("AI_PROVIDER_REASONING", "deepseek")
os.environ.setdefault("AI_PROVIDER_AGENT", "kimi")
os.environ.setdefault("AI_PROVIDER_VISION", "openai")
os.environ.setdefault("AI_PROVIDER_EMBEDDING", "openai")
os.environ.setdefault("KIMI_API_KEY", "ci-dummy-key")
os.environ.setdefault("DEEPSEEK_API_KEY", "ci-dummy-key")
os.environ.setdefault("DASHSCOPE_API_KEY", "ci-dummy-key")
os.environ.setdefault("CLERK_SECRET_KEY", "sk_test_ci_dummy_clerk_key")
os.environ.setdefault("CLERK_JWT_PUBLIC_KEY", "ci-dummy-jwt-key")

# --- Mock missing optional dependencies for test environment ---
for mod_name in ("passlib", "passlib.context", "passlib.hash"):
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# --- Monkeypatch PostgreSQL Types for SQLite ---
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import CHAR, Text, TypeDecorator

_ORIGINAL_POSTGRESQL_JSONB = postgresql.JSONB
_ORIGINAL_POSTGRESQL_UUID = postgresql.UUID


class MockJSONB(TypeDecorator):
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_ORIGINAL_POSTGRESQL_JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        import json

        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        import json

        try:
            return json.loads(value)
        except Exception:  # noqa: BLE001
            return {}


class MockUUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True

    def __init__(self, as_uuid=True):
        self.as_uuid = as_uuid
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_ORIGINAL_POSTGRESQL_UUID(as_uuid=self.as_uuid))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if self.as_uuid:
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value)
        return value


postgresql.JSONB = MockJSONB
postgresql.UUID = MockUUID

# --- DB fixtures ---
from luana_core_platform.domain.base_entity import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
USER_A = uuid.UUID("cccc0000-0000-0000-0000-000000000001")


@pytest.fixture(scope="session")
def db_engine():
    # Register all IAM models so SA can create tables
    from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: F401
    from luana_core_iam.infrastructure.models.user_model import UserModel  # noqa: F401
    from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return TENANT_A


@pytest.fixture
def other_tenant_id() -> uuid.UUID:
    return TENANT_B


@pytest.fixture
def user_id() -> uuid.UUID:
    return USER_A


class _TenantFactory:
    """Minimal TenantModel factory for luana-platform tests (no AISALESHT cross-imports)."""

    @staticmethod
    def build(**kwargs):
        from luana_core_iam.infrastructure.models.tenant_model import TenantModel

        defaults = {
            "id": uuid.uuid4(),
            "name": "Test Tenant",
            "slug": "test-tenant",
            "config_json": {},
            "is_active": True,
        }
        defaults.update(kwargs)
        return TenantModel(**defaults)


TenantFactory = _TenantFactory


@pytest.fixture
def sample_tenant(tenant_id: uuid.UUID):
    """Build a TenantModel (not persisted) for use in unit-level tests."""
    return TenantFactory.build(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={"company_name": "TestCo", "agent_persona": "Friendly"},
    )


@pytest.fixture
def seed_tenant(db, tenant_id: uuid.UUID):
    """Override shared seed_tenant -- IAM tests need richer config_json."""
    tenant = TenantFactory.build(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={"company_name": "TestCo", "agent_persona": "Friendly"},
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def seed_other_tenant(db, other_tenant_id: uuid.UUID):
    """Persist a TenantModel for TENANT_B (isolation testing)."""
    tenant = TenantFactory.build(
        id=other_tenant_id,
        name="Other Tenant",
        slug="other-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def seed_user(db, user_id: uuid.UUID):
    """Persist a UserModel for USER_A to the in-memory SQLite DB."""
    from luana_core_iam.infrastructure.models.user_model import UserModel

    user = UserModel(
        id=user_id,
        full_name="Alice Test",
        email="alice@example.com",
        clerk_id="clerk_alice_001",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def seed_user_tenant_link(
    db,
    seed_user,
    seed_tenant,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
):
    """Link USER_A to TENANT_A via UserTenantModel."""
    from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel

    link = UserTenantModel(
        user_id=user_id,
        tenant_id=tenant_id,
        role="admin",
        is_active=True,
    )
    db.add(link)
    db.commit()
    return link
