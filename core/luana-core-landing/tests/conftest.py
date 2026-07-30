"""Fixtures for landing module tests."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

# --- Set mandatory env vars before any imports that trigger config loading ---
# Pattern mirrors luana-core-crm/tests/conftest.py (Story 4 baseline).
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

from sqlalchemy import CHAR, Text, create_engine  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlalchemy.types import TypeDecorator  # noqa: E402


class _MockJSONB(TypeDecorator):
    """SQLite-compatible JSONB: stores as Text."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.JSONB())
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

        return json.loads(value)


_ORIGINAL_POSTGRESQL_UUID = postgresql.UUID


class _MockUUID(TypeDecorator):
    """SQLite-compatible UUID: stores as CHAR(36), accepts as_uuid kwarg."""

    impl = CHAR(36)
    cache_ok = True

    def __init__(self, as_uuid: bool = True, **kwargs):
        self.as_uuid = as_uuid
        super().__init__(**kwargs)

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
        import uuid

        if self.as_uuid:
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(str(value))
        return str(value)


# Patch postgresql types globally before model imports
postgresql.JSONB = _MockJSONB  # type: ignore[assignment]
postgresql.UUID = _MockUUID  # type: ignore[assignment]

# Import models AFTER patching
# Import landing models to register with Base metadata
import luana_core_landing.infrastructure.models.landing_model  # noqa: E402, F401
import sqlalchemy as _sa  # noqa: E402
from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: E402
from luana_core_platform.domain.base_entity import Base  # noqa: E402

# ---------------------------------------------------------------------------
# Cross-module stub models for SQLite test isolation
# Story 4 landing tests need a stub for: ProductModel (offer module — Story 5 lift)
# The stub registers in Base.metadata so FK resolution works in SQLite.
# ---------------------------------------------------------------------------
if "products" not in Base.metadata.tables:

    class _ProductStub(Base):  # type: ignore[misc]
        """Stub for offer.ProductModel (Story 5 lift). FK target only.

        Columns mirror the fields used by landing integration tests
        and LandingService.generate_landing_for_offer SQL query.
        """

        __tablename__ = "products"
        id = _sa.Column(_MockUUID(as_uuid=True), primary_key=True)
        tenant_id = _sa.Column(_MockUUID(as_uuid=True), nullable=True)
        name = _sa.Column(_sa.String, nullable=True)
        archetype = _sa.Column(_sa.String, nullable=True)
        status = _sa.Column(_sa.String, nullable=True)
        # Full set of columns queried by landing_service.generate_landing_for_offer
        headline_promise = _sa.Column(_sa.Text, nullable=True)
        primary_outcome = _sa.Column(_sa.Text, nullable=True)
        marketing_pain_points = _sa.Column(_sa.Text, nullable=True)
        preset_id = _sa.Column(_sa.String, nullable=True)
        # Promise narrative
        before_state = _sa.Column(_sa.Text, nullable=True)
        after_state = _sa.Column(_sa.Text, nullable=True)
        why_now = _sa.Column(_sa.Text, nullable=True)
        measurable_outcomes = _sa.Column(_sa.Text, nullable=True)
        # Psychology narrative
        objections = _sa.Column(_sa.Text, nullable=True)
        marketing_desires = _sa.Column(_sa.Text, nullable=True)
        cultural_trust_barriers = _sa.Column(_sa.Text, nullable=True)
        emotional_triggers = _sa.Column(_sa.Text, nullable=True)
        status_drivers = _sa.Column(_sa.Text, nullable=True)
        regret_scenarios = _sa.Column(_sa.Text, nullable=True)
        # Closing narrative
        refund_process_description = _sa.Column(_sa.Text, nullable=True)
        urgency_drivers = _sa.Column(_sa.Text, nullable=True)
        scarcity_reason_honest = _sa.Column(_sa.Text, nullable=True)
        bonus_if_act_now = _sa.Column(_sa.Text, nullable=True)
        final_push_copy = _sa.Column(_sa.Text, nullable=True)
        # Supporting fields
        guarantee_terms = _sa.Column(_sa.Text, nullable=True)
        guarantee_type = _sa.Column(_sa.String, nullable=True)
        support_duration_days = _sa.Column(_sa.Integer, nullable=True)
        deliverables = _sa.Column(_sa.Text, nullable=True)
        pricing = _sa.Column(_sa.Text, nullable=True)
        # Additional standard fields
        description = _sa.Column(_sa.Text, nullable=True)
        value_level = _sa.Column(_sa.String, nullable=True)
        price = _sa.Column(_sa.Float, nullable=True)
        currency = _sa.Column(_sa.String, nullable=True)
        slug = _sa.Column(_sa.String, nullable=True)
        specific_details = _sa.Column(_sa.Text, nullable=True)
        platform_details = _sa.Column(_sa.Text, nullable=True)
        deleted_at = _sa.Column(_sa.DateTime, nullable=True)


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped SQLite in-memory engine with landing models registered."""
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


import uuid  # noqa: E402

SAMPLE_TENANT_ID = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
OTHER_TENANT_ID = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


@pytest.fixture
def tenant_id() -> uuid.UUID:
    """Standard test tenant UUID."""
    return SAMPLE_TENANT_ID


@pytest.fixture
def other_tenant_id() -> uuid.UUID:
    """Secondary test tenant UUID (for isolation tests)."""
    return OTHER_TENANT_ID


@pytest.fixture
def seed_tenant(db, tenant_id: uuid.UUID) -> TenantModel:
    """Persist a TenantModel row so FK constraints are satisfied."""
    tenant = TenantModel(
        id=tenant_id,
        slug="test-tenant",
        name="Test Tenant",
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def seed_other_tenant(db, other_tenant_id: uuid.UUID) -> TenantModel:
    """Persist a second TenantModel row for tenant isolation tests."""
    tenant = TenantModel(
        id=other_tenant_id,
        slug="other-tenant",
        name="Other Tenant",
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def sample_squeeze_config_dict():
    """Minimal valid LandingPageConfig dict for THE_SQUEEZE archetype."""
    return {
        "archetype": "THE_SQUEEZE",
        "slug": "my-squeeze-page",
        "content": {
            "headline": "Grab This Free Guide",
            "subheadline": "No more struggling with X",
            "bullets": ["Benefit 1", "Benefit 2", "Benefit 3"],
            "cta_text": "Send it now",
            "privacy_text": "Your data is safe.",
        },
    }


@pytest.fixture
def sample_transformer_config_dict():
    """Minimal valid LandingPageConfig dict for THE_TRANSFORMER archetype."""
    return {
        "archetype": "THE_TRANSFORMER",
        "slug": "my-transformer-page",
        "content": {
            "headline": "Become a 6-Figure Coach in 90 Days",
            "subheadline": "Even if you're starting from zero",
            "problem_text": "You're tired of trading time for money",
            "agitation_text": "Every month without a system costs you thousands",
            "solution_text": "The Accelerator Method gets you there fast",
            "method_name": "The Accelerator Method",
            "method_description": "A 3-phase system proven to work",
            "authority_name": "Jane Doe",
            "authority_bio": "Helped 500+ coaches scale to 6-figures",
            "modules": [
                {"title": "Module 1: Foundations", "description": "Build your base"},
            ],
            "price_anchor": "$2,997",
            "price_offer": "$997",
            "scarcity_text": "Only 10 spots left",
            "cta_text": "Join now",
        },
    }
