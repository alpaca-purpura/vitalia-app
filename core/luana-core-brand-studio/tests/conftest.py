"""
Brand studio test fixtures.

Sets mandatory env vars before any import that triggers config loading.
Pattern mirrors luana-core-connections/tests/conftest.py (Story 4 baseline).
"""

from __future__ import annotations

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
os.environ.setdefault("USE_OUTBOX_PATTERN_BRAND", "true")
os.environ.setdefault(
    "ENCRYPTION_KEY",
    "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleQ==",
)

# --- Mock missing optional dependencies for test environment ---
for mod_name in ("passlib", "passlib.context", "passlib.hash"):
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# --- Monkeypatch PostgreSQL Types for SQLite (mirrors Story 4 connections conftest) ---
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

# ---------------------------------------------------------------------------
# Import models AFTER patching dialects
# ---------------------------------------------------------------------------
import sqlalchemy as _sa  # noqa: E402

# Register brand-studio models
from luana_core_brand_studio.infrastructure.models.avatar_model import AvatarModel  # noqa: F401
from luana_core_brand_studio.infrastructure.models.brand_summary_model import BrandSummaryModel  # noqa: F401
from luana_core_brand_studio.infrastructure.models.buyer_persona_model import BuyerPersonaModel  # noqa: F401
from luana_core_brand_studio.infrastructure.models.extraction_trace_model import BrandExtractionTrace  # noqa: F401
from luana_core_brand_studio.infrastructure.models.personality_model import PersonalityProfileModel  # noqa: F401
from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: F401
from luana_core_iam.infrastructure.models.user_model import UserModel  # noqa: F401
from luana_core_platform.domain.base_entity import Base  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# Stub models for FK targets not yet lifted (offer products + scheduling + sales_agent)
if "products" not in Base.metadata.tables:

    class ProductModel(Base):  # type: ignore[misc]
        """Stub for offer.ProductModel (future lift). FK target only."""

        __tablename__ = "products"
        id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
        tenant_id = _sa.Column(MockUUID(as_uuid=True), nullable=True)


# Test constants
TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
USER_A = uuid.UUID("cccc0000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# SQLite in-memory DB fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped SQLite engine with all brand-studio models registered."""
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
    return TENANT_A


@pytest.fixture
def other_tenant_id() -> uuid.UUID:
    """Alternative tenant ID for isolation tests."""
    return TENANT_B


@pytest.fixture
def user_id() -> uuid.UUID:
    """Standard test user ID."""
    return USER_A


@pytest.fixture
def seed_tenant(db, tenant_id):
    """Persist a TenantModel row so FK constraints are satisfied."""
    tenant = TenantModel(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def seed_other_tenant(db, other_tenant_id):
    """Persist a second TenantModel row for tenant isolation tests."""
    tenant = TenantModel(
        id=other_tenant_id,
        name="Other Tenant",
        slug="other-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant


# ---------------------------------------------------------------------------
# Brand domain object fixtures (mirrors AISALESHT tests/modules/brand/conftest.py)
# ---------------------------------------------------------------------------
from luana_core_brand_studio.domain import BrandIdentity, BrandSettings, BrandStory, BrandVisuals  # noqa: E402
from luana_core_brand_studio.domain.entities import Avatar  # noqa: E402


@pytest.fixture
def sample_identity():
    """Sample brand identity for tests."""
    return BrandIdentity(
        brand_name="TestBrand",
        tagline="Test tagline",
        description="A test brand",
        industry="Technology",
        website="https://testbrand.com",
        founding_year="2020",
    )


@pytest.fixture
def sample_visuals():
    """Sample brand visuals for tests."""
    return BrandVisuals(
        primary_color="#0f172a",
        secondary_color="#1e293b",
        accent_color="#3b82f6",
        background_color="#ffffff",
        font_heading="Inter",
        font_body="Inter",
    )


@pytest.fixture
def sample_story():
    """Sample brand story for tests."""
    return BrandStory(
        origin_story="Founded in a garage",
        mission="Make the world better",
        vision="Be the best",
    )


@pytest.fixture
def sample_settings(sample_identity, sample_visuals, sample_story):
    """Sample brand settings for tests."""
    return BrandSettings(
        identity=sample_identity,
        visuals=sample_visuals,
        story=sample_story,
    )


@pytest.fixture
def sample_avatar(tenant_id, user_id):
    """Sample avatar domain entity for tests."""
    return Avatar(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        name="Ideal Customer",
        scope="GLOBAL",
        icp_description="Tech-savvy entrepreneur",
        anti_avatar="People who don't value quality",
    )
