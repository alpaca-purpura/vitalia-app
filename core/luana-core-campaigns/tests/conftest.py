"""Test configuration for luana-core-campaigns.

Adapted from luana-core-sales-agent/tests/conftest.py pattern.
Sets env vars before config loading + patches PostgreSQL types for SQLite.
"""

from __future__ import annotations

import os
import sys
import uuid
from unittest.mock import MagicMock

# --- Set mandatory env vars before any imports trigger config loading ---
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
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "ci-dummy-bot-token")

# --- Mock missing optional dependencies for test environment ---
for mod_name in ("passlib", "passlib.context", "passlib.hash"):
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# --- Monkeypatch PostgreSQL Types for SQLite ---
from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.types import CHAR, Text, TypeDecorator  # noqa: E402

_ORIGINAL_POSTGRESQL_JSONB = postgresql.JSONB
_ORIGINAL_POSTGRESQL_UUID = postgresql.UUID


class MockJSONB(TypeDecorator):
    """SQLite-compatible JSONB replacement."""

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
    """SQLite-compatible UUID replacement."""

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

# Patch EncryptedJSON to use MockJSONB for SQLite tests
try:
    from luana_core_platform.infrastructure.database import types as _db_types  # noqa: E402

    _db_types.EncryptedJSON.impl = MockJSONB  # type: ignore[assignment]
except (ImportError, AttributeError):
    pass

# ---------------------------------------------------------------------------
# Imports AFTER patching dialects
# ---------------------------------------------------------------------------
import pytest  # noqa: E402
import sqlalchemy as _sa  # noqa: E402
from luana_core_platform.domain.base_entity import Base  # noqa: E402
from luana_core_platform.domain.base_entity import Base as _Base  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# ---------------------------------------------------------------------------
# Cross-module stub models for SQLite test isolation
# ---------------------------------------------------------------------------

# MessageModel: luana_core_sales_agent lifted in Story 7 — import real model
try:
    import luana_core_sales_agent.infrastructure.models.message_model  # noqa: F401
except ImportError:
    # Fallback stub if sales_agent not in environment
    if "messages" not in _Base.metadata.tables:

        class MessageModel(_Base):  # type: ignore[misc]
            """Stub for sales_agent MessageModel."""

            __tablename__ = "messages"
            id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
            lead_id = _sa.Column(MockUUID(as_uuid=True), nullable=True)
            user_id = _sa.Column(MockUUID(as_uuid=True), nullable=True)


# AppointmentModel: scheduling not yet lifted — stub until Story scheduling lift
if "appointments" not in _Base.metadata.tables:

    class AppointmentModel(_Base):  # type: ignore[misc]
        """Stub for scheduling.AppointmentModel (Story 8 lift).

        Per DEFERRED-FILES.md: AppointmentModel stays deferred until
        scheduling module lift.
        """

        __tablename__ = "appointments"
        id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
        lead_id = _sa.Column(MockUUID(as_uuid=True), _sa.ForeignKey("leads.id"), nullable=True)


# ---------------------------------------------------------------------------
# Register cross-package models for SQLite metadata
# ---------------------------------------------------------------------------
def _safe_import_models():
    """Import every model needed for campaigns tests, soft-fail on missing."""
    import importlib

    model_paths = [
        # IAM
        "luana_core_iam.infrastructure.models.tenant_model",
        "luana_core_iam.infrastructure.models.user_model",
        # Brand Studio
        "luana_core_brand_studio.infrastructure.models.brand_summary_model",
        "luana_core_brand_studio.infrastructure.models.buyer_persona_model",
        "luana_core_brand_studio.infrastructure.models.personality_model",
        # CRM
        "luana_core_platform.infrastructure.models.crm",
        # Connections
        "luana_core_connections.infrastructure.models.channel_connection_model",
        # Sales agent
        "luana_core_sales_agent.infrastructure.models.message_model",
        # Observability
        "luana_core_observability.persistence.models.llm_call_model",
        "luana_core_observability.persistence.models.trace_event_model",
        "luana_core_observability.persistence.models.pricing_snapshot_model",
        "luana_core_observability.persistence.models.tenant_billing_config_model",
        # Offer Studio (products table — FK from sales model in luana-core-platform)
        "luana_core_offer_studio.infrastructure.models.product_model",
        "luana_core_offer_studio.infrastructure.models.launch_edition_model",
        "luana_core_offer_studio.infrastructure.models.offer_asset_model",
        "luana_core_offer_studio.infrastructure.models.knowledge_source_model",
        # Social Proof (for FK chains)
        "luana_core_social_proof.infrastructure.models",
        # Landing
        "luana_core_landing.infrastructure.models.landing_model",
        # Tenant Domains / Profile
        "luana_core_tenant_domains.infrastructure.models.tenant_domain_model",
        "luana_core_tenant_profile.infrastructure.models.tenant_profile_model",
        # LLM
        "luana_core_llm.infrastructure.audit_model",
        "luana_core_llm.infrastructure.role_binding_model",
        # Copilot models
        "luana_core_copilot.infrastructure.models.trace_event_model",
        "luana_core_copilot.infrastructure.models.conversation_model",
    ]

    for path in model_paths:
        try:
            importlib.import_module(path)
        except ImportError:
            pass


_safe_import_models()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped SQLite engine with all available models registered."""
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


@pytest.fixture(scope="function")
def db_session(db):
    """Alias `db_session` fixture for AISALESHT compatibility."""
    return db


# ---------------------------------------------------------------------------
# Singleton reset
# ---------------------------------------------------------------------------
def _do_singleton_reset() -> None:
    """Reset class-level singletons between tests."""
    try:
        from luana_core_llm.factory import LLMFactory

        LLMFactory._instance = None
    except (ImportError, AttributeError):
        pass

    try:
        from luana_core_platform.domain.events import EventBus

        EventBus.clear()
    except (ImportError, AttributeError):
        pass

    try:
        from luana_core_events.outbox.application.event_bus_adapter import (
            _reset_module_inference_cache,
        )

        _reset_module_inference_cache()
    except (ImportError, AttributeError):
        pass


@pytest.fixture(autouse=True)
def _reset_singletons_between_tests() -> None:
    """Reset class-level singletons + module-level caches pre+post each test."""
    _do_singleton_reset()
    yield
    _do_singleton_reset()


# ---------------------------------------------------------------------------
# Campaign-specific fixtures
# ---------------------------------------------------------------------------
TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return TENANT_A


@pytest.fixture
def lead_id() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Test app factory — replaces `from src.main import app` in API test files
# ---------------------------------------------------------------------------


def _make_campaigns_test_app():
    """Create a minimal FastAPI test app with campaigns routers mounted.

    Replaces the AISALESHT `from src.main import app` pattern used in api tests.
    Mounts all three campaigns routers under /api/v1 matching production prefix.
    Per backend-ddd.md: redirect_slashes=False mandatory.
    """
    from fastapi import FastAPI
    from luana_core_campaigns.api.routers.campaigns_router import router as campaigns_router
    from luana_core_campaigns.api.routers.segments_router import router as segments_router
    from luana_core_campaigns.api.routers.templates_router import router as templates_router

    _app = FastAPI(redirect_slashes=False)
    _app.include_router(campaigns_router, prefix="/api/v1")
    _app.include_router(segments_router, prefix="/api/v1")
    _app.include_router(templates_router, prefix="/api/v1")
    return _app
