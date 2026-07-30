"""
Connections test fixtures.

Sets mandatory env vars before any import that triggers config loading.
Pattern mirrors luana-core-crm/tests/conftest.py (Story 4 baseline).
"""

import os
import sys
import uuid
from unittest.mock import MagicMock

import pytest

# --- Set mandatory env vars before any imports that trigger config loading ---
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
# Connections-specific
os.environ.setdefault("SHOPIFY_API_SECRET", "ci-shopify-secret")
os.environ.setdefault("META_APP_SECRET", "ci-meta-secret")
os.environ.setdefault("GOOGLE_CLIENT_ID", "ci-google-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "ci-google-client-secret")
# Encryption key for EncryptedJSON type (32 url-safe base64 chars required by Fernet)
os.environ.setdefault(
    "ENCRYPTION_KEY",
    "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleQ==",  # base64("testkeytestkeytestkeytestkey")
)

# --- Mock missing optional dependencies for test environment ---
for mod_name in ("passlib", "passlib.context", "passlib.hash"):
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# --- Monkeypatch PostgreSQL Types for SQLite (mirrors IAM + CRM conftest pattern) ---
from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.types import CHAR, Text, TypeDecorator  # noqa: E402

_ORIGINAL_POSTGRESQL_JSONB = postgresql.JSONB
_ORIGINAL_POSTGRESQL_UUID = postgresql.UUID


class MockJSONB(TypeDecorator):
    """SQLite-compatible JSONB replacement."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load dialect implementation."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_ORIGINAL_POSTGRESQL_JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        """Serialize to JSON string."""
        if value is None:
            return None
        import json

        return json.dumps(value)

    def process_result_value(self, value, dialect):
        """Deserialize from JSON string."""
        if value is None:
            return None
        import json

        try:
            return json.loads(value)
        except Exception:  # noqa: BLE001
            return {}


class MockUUID(TypeDecorator):
    """SQLite-compatible UUID replacement."""

    impl = CHAR(36)
    cache_ok = True

    def __init__(self, as_uuid=True):
        """Initialize with as_uuid flag."""
        self.as_uuid = as_uuid
        super().__init__()

    def load_dialect_impl(self, dialect):
        """Load dialect implementation."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_ORIGINAL_POSTGRESQL_UUID(as_uuid=self.as_uuid))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        """Serialize UUID to string."""
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        """Deserialize string to UUID."""
        if value is None:
            return None
        if self.as_uuid:
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value)
        return value


postgresql.JSONB = MockJSONB
postgresql.UUID = MockUUID

# Patch EncryptedJSON to use MockJSONB for SQLite tests
from luana_core_platform.infrastructure.database import types as _db_types  # noqa: E402

_db_types.EncryptedJSON.impl = MockJSONB  # type: ignore[assignment]


# Import models AFTER patching dialects
# ---------------------------------------------------------------------------
# Cross-module stub models for SQLite test isolation
# Story 4 connections tests need stubs for: AppointmentModel, ProductModel.
# Story 7 T-16: MessageModel STUB REMOVED — sales_agent.MessageModel now real
# (lifted from luana_core_sales_agent), imported BEFORE stub guard runs so the
# real model registers first in Base.metadata. ChatOrchestrator wiring requires
# real model. Stubs satisfy SQLAlchemy mapper + FK resolution for remaining
# deferred lifts (scheduling.AppointmentModel = Story 8; offer.ProductModel).
# ---------------------------------------------------------------------------
import sqlalchemy as _sa  # noqa: E402

# Import IAM models first (channel_connections has FK to 'tenants')
from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: F401
from luana_core_iam.infrastructure.models.user_model import UserModel  # noqa: F401
from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel  # noqa: F401
from luana_core_platform.domain.base_entity import Base  # noqa: E402

# Story 7 T-16: Register real sales_agent.MessageModel BEFORE stub guard runs.
# T-16 resolves Stories 4+6 deferral — connections api/dependencies now wires
# real ChatOrchestrator → transitively imports sales_agent models. The real
# MessageModel claims 'messages' in Base.metadata; stub guard below skips.
from luana_core_sales_agent.infrastructure.models.message_model import (  # noqa: F401, E402
    MessageModel,
)
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

if "products" not in Base.metadata.tables:

    class ProductModel(Base):  # type: ignore[misc]
        """Stub for offer.ProductModel (future lift). FK target only."""

        __tablename__ = "products"
        id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
        tenant_id = _sa.Column(MockUUID(as_uuid=True), nullable=True)


if "appointments" not in Base.metadata.tables:

    class AppointmentModel(Base):  # type: ignore[misc]
        """Stub for scheduling.AppointmentModel (future lift). FK target only."""

        __tablename__ = "appointments"
        id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
        lead_id = _sa.Column(MockUUID(as_uuid=True), _sa.ForeignKey("leads.id"), nullable=True)


# Import CRM models (for tests that reference LeadModel/CustomerProfileModel)
# Import connections model
from luana_core_connections.infrastructure.models.channel_connection_model import (  # noqa: F401
    ChannelConnectionModel,
)
from luana_core_platform.infrastructure.models.crm import (  # noqa: F401
    CustomerIdentityModel,
    CustomerProfileModel,
    JourneyEventModel,
    LeadModel,
    LifecycleTransitionModel,
    NpsResponseModel,
    NpsSurveyModel,
    ReferralCodeModel,
    SaleModel,
)

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


# ---------------------------------------------------------------------------
# SQLite in-memory DB fixtures (mirrors luana-core-iam/luana-core-crm pattern)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped SQLite engine with all connections models registered."""
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
    """Function-scoped DB session with transaction rollback isolation."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def tenant_id() -> uuid.UUID:
    """Standard test tenant ID."""
    return SAMPLE_TENANT_ID


@pytest.fixture
def other_tenant_id() -> uuid.UUID:
    """Alternative tenant ID for isolation tests."""
    return OTHER_TENANT_ID
