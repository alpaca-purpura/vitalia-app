"""Test configuration for luana-core-copilot (T-15 — canonical pattern).

Adapts AISALESHT backend/tests/conftest.py to luana-platform paradigm.
Pattern mirrors luana-core-offer-studio/tests/conftest.py (Story 5 baseline)
+ adds copilot-specific stubs and helpers (prime_cost_bridge, observability
context stub).

Story 7 sales_agent + Story 8 scheduling not yet lifted → MessageModel +
AppointmentModel cross-module stubs preserved (D-T2 evaluation: AppointmentModel
stays until Story 8; MessageModel will be replaced T-17 with real
luana_core_copilot import once T-16 unlift completes).
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

# --- Mock missing optional dependencies for test environment ---
for mod_name in ("passlib", "passlib.context", "passlib.hash"):
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# --- Monkeypatch PostgreSQL Types for SQLite (Story 5 baseline pattern) ---
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
            return dialect.type_descriptor(
                _ORIGINAL_POSTGRESQL_UUID(as_uuid=self.as_uuid)
            )
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
# Story 7 sales_agent + Story 8 scheduling not yet lifted. The shared CRM
# luana_core_platform.infrastructure.models.crm declares LeadModel.messages
# -> "MessageModel" and LeadModel.appointments -> "AppointmentModel".
# Without stubs, SA mapper config fails with InvalidRequestError.
# ---------------------------------------------------------------------------

# T-11/T-12 (Story 7 batch 4) — MessageModel lifted in T-5 batch 2. Eager-import
# the real model so the stub guard below skips stub creation, preventing the
# "Table 'messages' is already defined" collision when _do_singleton_reset
# triggers the orchestrator chain (chat → conversation_pipeline → graph →
# agents/sales → tracing → audit_repository → message_model).
#
# Known pre-existing tech debt (NOT introduced by Story 7): luana-core-platform
# CRM's LeadModel.messages relationship declares `foreign_keys="MessageModel.lead_id"`
# but the real MessageModel uses `user_id` Column (with `lead_id` as @property alias
# for AISALESHT back-compat). The previous stub masked this by providing a real
# `lead_id` Column. Now that the real model is imported, tests touching the
# LeadModel.messages relationship (e.g., test_closer_studio_service.py) fail
# with "Class MessageModel does not have a mapped column named 'lead_id'".
# Proper fix: align luana-core-platform CRM relationship to AISALESHT pattern
# (back_populates without foreign_keys hint, since MessageModel.lead specifies
# foreign_keys=[user_id]). Scoped to luana-core-platform Story 4 follow-up,
# NOT Story 7. AppointmentModel stub remains until Story 8 scheduling lift.
import luana_core_sales_agent.infrastructure.models.message_model  # noqa: E402, F401

# Story 7 D-T2 cement (2026-05-12): MessageModel stub removed — real model
# eager-imported above claims 'messages' table in _Base.metadata. Defensive
# stub block dropped; if real import fails, ImportError propagates (V-AG-4
# catches regression). AppointmentModel stub stays until Story 8 scheduling lift.

if "appointments" not in _Base.metadata.tables:

    class AppointmentModel(_Base):  # type: ignore[misc]
        """Stub for scheduling.AppointmentModel (Story 8 lift).

        Per D-T2 evaluation: stub stays until Story 8 scheduling module lift.
        """

        __tablename__ = "appointments"
        id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
        lead_id = _sa.Column(
            MockUUID(as_uuid=True), _sa.ForeignKey("leads.id"), nullable=True
        )


# ---------------------------------------------------------------------------
# Register cross-package models (every successful import expands metadata)
# All wrapped in try/except — missing modules don't break test collection.
# ---------------------------------------------------------------------------
def _safe_import_models():
    """Import every model needed for copilot tests, soft-fail on missing modules."""
    import importlib

    model_paths = [
        # IAM
        "luana_core_iam.infrastructure.models.tenant_model",
        "luana_core_iam.infrastructure.models.user_model",
        # Brand Studio
        "luana_core_brand_studio.infrastructure.models.avatar_model",
        "luana_core_brand_studio.infrastructure.models.brand_summary_model",
        "luana_core_brand_studio.infrastructure.models.buyer_persona_model",
        "luana_core_brand_studio.infrastructure.models.extraction_trace_model",
        "luana_core_brand_studio.infrastructure.models.personality_model",
        # Commercial Calendar
        "luana_core_commercial_calendar.infrastructure.models.calendar_event_model",
        # Connections
        "luana_core_connections.infrastructure.models.channel_connection_model",
        # Copilot (this package)
        "luana_core_copilot.infrastructure.models.conversation_model",
        "luana_core_copilot.infrastructure.models.inspiration_model",
        "luana_core_copilot.infrastructure.models.mutation_journal_model",
        "luana_core_copilot.infrastructure.models.pinned_memory_model",
        "luana_core_copilot.infrastructure.models.routing_log_model",
        "luana_core_copilot.infrastructure.models.trace_event_model",
        "luana_core_copilot.infrastructure.models.workflow_metric_model",
        # CRM
        "luana_core_platform.infrastructure.models.crm",
        # Landing
        "luana_core_landing.infrastructure.models.landing_model",
        # Offer Studio
        "luana_core_offer_studio.infrastructure.models.knowledge_source_model",
        "luana_core_offer_studio.infrastructure.models.launch_edition_model",
        "luana_core_offer_studio.infrastructure.models.offer_asset_model",
        "luana_core_offer_studio.infrastructure.models.product_model",
        # Social Proof
        "luana_core_social_proof.infrastructure.models",
        # Tenant Domains / Profile
        "luana_core_tenant_domains.infrastructure.models.tenant_domain_model",
        "luana_core_tenant_profile.infrastructure.models.tenant_profile_model",
        # LLM
        "luana_core_llm.infrastructure.audit_model",
        "luana_core_llm.infrastructure.role_binding_model",
        # Observability
        "luana_core_observability.persistence.models.llm_call_model",
        "luana_core_observability.persistence.models.trace_event_model",
        "luana_core_observability.persistence.models.routing_log_model",
        "luana_core_observability.persistence.models.pricing_snapshot_model",
        "luana_core_observability.persistence.models.tenant_billing_config_model",
    ]

    for path in model_paths:
        try:
            importlib.import_module(path)
        except ImportError:
            # Missing module = forward-Story (sales_agent/scheduling) or
            # not-yet-lifted submodel. Soft-fail per established T-15 pattern.
            pass


_safe_import_models()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _force_prompt_source_file(monkeypatch):
    """Force PROMPT_SOURCE=file for every test (hermetic prompt resolution)."""
    try:
        from luana_core_platform.core.config import PromptSource, settings

        monkeypatch.setattr(settings, "PROMPT_SOURCE", PromptSource.FILE)
    except (ImportError, AttributeError):
        pass


@pytest.fixture(autouse=True)
def _stub_copilot_observability_context(monkeypatch, request):
    """Stub ObservabilityContext to avoid 30s DNS retries.

    Skip this stub for observability tests which need the real context.
    """
    if "tests/observability" in request.fspath.strpath:
        return

    from contextlib import asynccontextmanager
    from unittest.mock import MagicMock as _MM
    from uuid import uuid4 as _uuid4

    @classmethod
    def _stub_start(cls, **kwargs):
        @asynccontextmanager
        async def _noop_observe(**_kw):
            yield ctx

        ctx = _MM()
        ctx.tenant_id = kwargs.get("tenant_id") or _uuid4()
        ctx.conversation_id = kwargs.get("conversation_id")
        ctx.user_id = kwargs.get("user_id")
        ctx.turn_id = kwargs.get("turn_id") or _uuid4()
        ctx.langchain_config.return_value = {}
        ctx.set_turn_summary.return_value = None
        ctx.observe_turn = _noop_observe
        return ctx

    try:
        from luana_core_copilot.observability.recording.turn_envelope import (
            ObservabilityContext,
        )

        monkeypatch.setattr(ObservabilityContext, "start", _stub_start)
    except ImportError:
        pass


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


# Alias for AISALESHT compatibility (some tests use `db_session` name)
@pytest.fixture(scope="function")
def db_session(db):
    """Alias `db_session` fixture for AISALESHT compatibility."""
    return db


# ---------------------------------------------------------------------------
# Singleton reset (PI-11 PR-1 Fase 3 — adapted for luana-platform paradigm)
# ---------------------------------------------------------------------------
def _do_singleton_reset() -> None:
    """Reset class-level singletons + module-level caches.

    sales_agent ChatOrchestrator + SemanticRouter singletons are soft (Story 7
    not yet lifted — try/except ImportError suppresses if module missing).
    """
    try:
        from luana_core_llm.factory import LLMFactory

        LLMFactory._instance = None
    except (ImportError, AttributeError):
        pass

    # sales_agent (Story 7 — soft)
    try:
        from luana_core_sales_agent.application.orchestrator.chat import (
            ChatOrchestrator,
        )

        if ChatOrchestrator._instance is not None and hasattr(
            ChatOrchestrator._instance, "buffer_service"
        ):
            ChatOrchestrator._instance.buffer_service = None  # type: ignore[attr-defined]
        ChatOrchestrator._instance = None
    except (ImportError, AttributeError):
        pass

    try:
        from luana_core_sales_agent.application.services.semantic_router import (
            SemanticRouter,
        )

        SemanticRouter._instance = None
    except (ImportError, AttributeError):
        pass

    # EventBus
    try:
        from luana_core_platform.domain.events import EventBus

        EventBus.clear()
    except (ImportError, AttributeError):
        pass

    # EventBusAdapter module-inference cache
    try:
        from luana_core_events.outbox.application.event_bus_adapter import (
            _reset_module_inference_cache,
        )

        _reset_module_inference_cache()
    except (ImportError, AttributeError):
        pass


def prime_cost_bridge(call_id, cost):  # noqa: ANN001
    """Pre-stash cost in module-level TTL cache (PI-12 S1 D-T1bis-3 bridge pattern).

    Test helpers call this to simulate LiteLLM CustomLogger so
    BaseAgentCallbackHandler._persist_llm_call() retrieves cost_usd > 0
    during on_llm_end when LangChain mocks bypass proxy.
    """
    from decimal import Decimal as _Decimal

    from luana_core_observability.recording.cost_recorder import _stash

    _stash(call_id, _Decimal(str(cost)) if not isinstance(cost, _Decimal) else cost)


@pytest.fixture(autouse=True)
def _reset_singletons_between_tests() -> None:
    """Reset class-level singletons + module-level caches pre+post each test."""
    _do_singleton_reset()
    yield
    _do_singleton_reset()


# ---------------------------------------------------------------------------
# Sales-agent specific fixtures (lifted from AISALESHT conftest.py)
# ---------------------------------------------------------------------------
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


@pytest.fixture
def tenant_id_b() -> uuid.UUID:
    return TENANT_B


@pytest.fixture
def lead_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def customer_profile_id() -> uuid.UUID:
    return uuid.uuid4()
