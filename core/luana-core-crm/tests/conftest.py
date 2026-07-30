"""
CRM test fixtures.

Provides sample CustomerProfileModel, JourneyEventModel, and LifecycleTransitionModel
instances for use across CRM test modules (plans 02 and 03).
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from sqlalchemy.orm import Session

# --- Set mandatory env vars before any imports that trigger config loading ---
# Pattern mirrors luana-core-iam/tests/conftest.py (Story 3 baseline).
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

# --- Monkeypatch PostgreSQL Types for SQLite (mirrors IAM conftest pattern) ---
from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.types import CHAR, Text, TypeDecorator  # noqa: E402

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

import sqlalchemy as _sa

# Import IAM models first (CRM models have FK to 'tenants')
from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: F401
from luana_core_iam.infrastructure.models.user_model import UserModel  # noqa: F401
from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel  # noqa: F401
from luana_core_platform.domain.base_entity import Base

# ---------------------------------------------------------------------------
# Cross-module FK targets for SQLite test isolation
# Story 4 CRM tests need FK resolution for: ProductModel, MessageModel, AppointmentModel.
# Story 7 D-T2 cement (2026-05-12): MessageModel real-lift complete — eager-import
# real model so subsequent stub guard skips it (mirrors connections T-16 pattern).
# ProductModel stub stays until Story 8 catalog lift.
# AppointmentModel stub stays until Story 8 scheduling lift.
# ---------------------------------------------------------------------------
from luana_core_platform.domain.base_entity import Base as _Base
from luana_core_sales_agent.infrastructure.models.message_model import (  # noqa: F401
    MessageModel,  # Story 7 D-T2 cement — real model (T-5 batch 2 lift), claims 'messages' table
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Only register stubs if tables not already registered
if "products" not in _Base.metadata.tables:

    class ProductModel(_Base):  # type: ignore[misc]
        """Stub for offer.ProductModel (Story 5 lift). FK target only."""

        __tablename__ = "products"
        id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
        tenant_id = _sa.Column(MockUUID(as_uuid=True), nullable=True)


if "appointments" not in _Base.metadata.tables:

    class AppointmentModel(_Base):  # type: ignore[misc]
        """Stub for scheduling.AppointmentModel (future lift). FK target only."""

        __tablename__ = "appointments"
        id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
        lead_id = _sa.Column(MockUUID(as_uuid=True), _sa.ForeignKey("leads.id"), nullable=True)


# Import ALL CRM models so SA can create their tables
from luana_core_crm.domain.enums import LifecycleStage
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

# ---------------------------------------------------------------------------
# SQLite in-memory DB fixtures (mirrors luana-core-iam/tests/conftest.py pattern)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped SQLite engine with all CRM models registered."""
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


SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


def create_crm_test_app() -> FastAPI:
    """Create a minimal FastAPI app with CRM routers for lift-mode API tests.

    Story 4 lift: replaces `from src.main import app` in AISALESHT API tests
    with a self-contained mini-app. Mirrors AISALESHT main.py CRM router registrations.
    """
    from luana_core_crm.api import cdp as crm_cdp
    from luana_core_crm.api import leads as crm_leads
    from luana_core_crm.api import nps as crm_nps
    from luana_core_crm.api import pipeline as crm_pipeline
    from luana_core_crm.api import referral as crm_referral
    from luana_core_crm.api import sales as crm_sales

    test_app = FastAPI(redirect_slashes=False)
    test_app.include_router(crm_leads.router, prefix="/api/v1/crm/leads", tags=["CRM - Leads"])
    test_app.include_router(crm_cdp.router, prefix="/api/v1/crm/cdp", tags=["CRM - CDP"])
    test_app.include_router(crm_sales.router, prefix="/api/v1/crm/sales", tags=["CRM - Sales"])
    test_app.include_router(crm_pipeline.router, prefix="/api/v1/crm/pipeline", tags=["CRM - Pipeline"])
    test_app.include_router(crm_referral.router, prefix="/api/v1/crm", tags=["CRM - Referrals"])
    test_app.include_router(crm_nps.router, prefix="/api/v1/crm", tags=["CRM - NPS"])
    return test_app


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return SAMPLE_TENANT_ID


@pytest.fixture
def other_tenant_id() -> uuid.UUID:
    return OTHER_TENANT_ID


@pytest.fixture
def sample_profile(db: Session, tenant_id: uuid.UUID) -> CustomerProfileModel:
    """A basic SUBSCRIBER profile with default scoring fields."""
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email="test@example.com",
        full_name="Test User",
        lifecycle_stage=LifecycleStage.SUBSCRIBER,
        lead_score=0.0,
        lifetime_value=0.0,
        is_inactive=False,
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


@pytest.fixture
def sample_mql_profile(db: Session, tenant_id: uuid.UUID) -> CustomerProfileModel:
    """A profile at MQL stage with score above MQL threshold."""
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email="mql@example.com",
        full_name="MQL User",
        lifecycle_stage=LifecycleStage.MQL,
        lead_score=45.0,
        lifetime_value=0.0,
        is_inactive=False,
        last_activity_at=datetime.now(timezone.utc),
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


@pytest.fixture
def sample_customer_profile(db: Session, tenant_id: uuid.UUID) -> CustomerProfileModel:
    """A profile at CUSTOMER stage (sale-driven, decay paused)."""
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email="customer@example.com",
        full_name="Customer User",
        lifecycle_stage=LifecycleStage.CUSTOMER,
        lead_score=80.0,
        lifetime_value=99.0,
        is_inactive=False,
        first_conversion_at=datetime.now(timezone.utc) - timedelta(days=30),
        last_activity_at=datetime.now(timezone.utc) - timedelta(days=5),
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


@pytest.fixture
def sample_journey_events(
    db: Session,
    sample_profile: CustomerProfileModel,
    tenant_id: uuid.UUID,
) -> list:
    """A set of journey events for the sample_profile."""
    events = [
        JourneyEventModel(
            id=uuid.uuid4(),
            profile_id=sample_profile.id,
            tenant_id=tenant_id,
            event_name="page_view",
            event_type="track",
            properties={"page": "/landing"},
            occurred_at=datetime.now(timezone.utc) - timedelta(days=3),
        ),
        JourneyEventModel(
            id=uuid.uuid4(),
            profile_id=sample_profile.id,
            tenant_id=tenant_id,
            event_name="email_opened",
            event_type="track",
            properties={"campaign": "welcome"},
            occurred_at=datetime.now(timezone.utc) - timedelta(days=2),
        ),
        JourneyEventModel(
            id=uuid.uuid4(),
            profile_id=sample_profile.id,
            tenant_id=tenant_id,
            event_name="form_submitted",
            event_type="track",
            properties={"form": "contact"},
            occurred_at=datetime.now(timezone.utc) - timedelta(days=1),
        ),
    ]
    db.add_all(events)
    db.flush()
    return events


@pytest.fixture
def sample_transition(
    db: Session,
    sample_profile: CustomerProfileModel,
    tenant_id: uuid.UUID,
) -> LifecycleTransitionModel:
    """A sample lifecycle transition record."""
    transition = LifecycleTransitionModel(
        id=uuid.uuid4(),
        profile_id=sample_profile.id,
        tenant_id=tenant_id,
        from_stage=LifecycleStage.SUBSCRIBER,
        to_stage=LifecycleStage.LEAD,
        reason="Score crossed LEAD threshold (12.0 >= 10)",
        triggered_by="scoring_rule",
        score_at_transition=12.0,
        transition_metadata={
            "score": 12.0,
            "threshold": 10.0,
            "threshold_name": "lead",
        },
    )
    db.add(transition)
    db.flush()
    return transition
