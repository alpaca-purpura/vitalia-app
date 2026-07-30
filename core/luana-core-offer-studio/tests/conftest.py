"""Offer module test fixtures.

Sets mandatory env vars before any import that triggers config loading.
Pattern mirrors luana-core-brand-studio/tests/conftest.py (Story 5 baseline).
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

# ---------------------------------------------------------------------------
# Cross-module FK targets for SQLite test isolation
# Story 5 offer-studio tests trigger SQLA mapper resolution on ProductModel.
# The shared CRM crm.py (luana_core_platform.infrastructure.models.crm) declares
# LeadModel.messages -> "MessageModel" and LeadModel.appointments -> "AppointmentModel".
# Story 7 D-T2 cement (2026-05-12): MessageModel real-lift complete in
# luana_core_sales_agent.infrastructure.models.message_model — eager-import below
# registers real model so subsequent stub guard skips it (mirrors connections T-16).
# AppointmentModel stub stays until Story 8 scheduling lift.
# ---------------------------------------------------------------------------
# Register IAM models first (offer-studio FK -> tenants/users)
from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: F401, E402
from luana_core_iam.infrastructure.models.user_model import UserModel  # noqa: F401, E402
from luana_core_platform.domain.base_entity import Base  # noqa: E402
from luana_core_platform.domain.base_entity import Base as _Base  # noqa: E402
from luana_core_sales_agent.infrastructure.models.message_model import (  # noqa: F401, E402
    MessageModel,  # Story 7 D-T2 cement — real model (T-5 batch 2 lift), claims 'messages' table
)
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# Cross-module stubs: only register if not already in registry (idempotent)
if "appointments" not in _Base.metadata.tables:

    class AppointmentModel(_Base):  # type: ignore[misc]
        """Stub for scheduling.AppointmentModel (Story 7 lift). FK target only.

        Production model lives in src.modules.scheduling.infrastructure.models.appointment_model.
        This stub satisfies SQLA mapper resolution for LeadModel.appointments relationship
        declared in shared crm.py without forward-importing Story 7 code.
        """

        __tablename__ = "appointments"
        id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
        lead_id = _sa.Column(MockUUID(as_uuid=True), _sa.ForeignKey("leads.id"), nullable=True)


# Register CRM models (FK target for stubs above + SaleModel.offer -> products FK)
# These are shared in luana_core_platform.infrastructure.models.crm and reachable
# by LeadModel relationship resolution. Registering them ensures `leads` table
# exists when MessageModel/AppointmentModel stubs reference it.
from luana_core_offer_studio.domain.enums import OfferArchetype, OfferStatus, OfferValueLevel  # noqa: E402
from luana_core_offer_studio.infrastructure.models.external_product_mapping_model import (
    ExternalProductMappingModel,  # noqa: F401, E402
)
from luana_core_offer_studio.infrastructure.models.knowledge_source_model import (
    KnowledgeSourceModel,  # noqa: F401, E402
)
from luana_core_offer_studio.infrastructure.models.launch_edition_model import LaunchEditionModel  # noqa: F401, E402
from luana_core_offer_studio.infrastructure.models.offer_asset_model import OfferAssetModel  # noqa: F401, E402
from luana_core_offer_studio.infrastructure.models.offer_extraction_trace_model import (
    OfferExtractionTrace,  # noqa: F401, E402
)

# Register offer-studio models (triggers JSONB column registration via patched dialect)
from luana_core_offer_studio.infrastructure.models.product_model import ProductModel  # noqa: F401, E402
from luana_core_platform.infrastructure.models.crm import (  # noqa: F401, E402
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

TENANT_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TENANT_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

# ---------------------------------------------------------------------------
# SQLite in-memory DB fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped SQLite engine with all offer-studio models registered."""
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
def tenant_a() -> uuid.UUID:
    """Standard test tenant A."""
    return TENANT_A


@pytest.fixture
def tenant_b() -> uuid.UUID:
    """Standard test tenant B."""
    return TENANT_B


def create_product_model(
    tenant_id: uuid.UUID,
    *,
    archetype: str = OfferArchetype.PRODUCTO.value,
    status: str = OfferStatus.ACTIVE.value,
    name: str = "Test Offer",
    value_level: str | None = OfferValueLevel.ACTIVACION.value,
    **overrides,
) -> ProductModel:
    """Create a ProductModel with defaults for testing."""
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "name": name,
        "archetype": archetype,
        "status": status,
        "value_level": value_level,
        "format_hint": None,
        "is_lead_magnet": False,
        "has_editions": True,
        "pricing": [],
        "currency": "USD",
        "specific_details": {},
        "deliverables": [],
        "headline_promise": "Headline",
        "primary_outcome": "Outcome",
        "time_to_value": "1 week",
        "marketing_pain_points": [],
        "marketing_desires": [],
        "objections": [],
        "target_avatar_match": [],
        "access_duration": None,
        "access_duration_text": None,
        "support_duration_days": None,
        "delivery_model": "diy",
        "requires_application": False,
        "min_financial_capacity": "LOW_INCOME",
        "prerequisites": [],
        "anti_avatar_keywords": [],
        "guarantee_type": "none",
        "guarantee_terms": "",
        "downsell_product_id": None,
        "upsell_product_id": None,
        "includes_offers": [],
        "onboarding_action": None,
        "onboarding_url": None,
        "calendar_type_id": None,
        "checkout_page_url": None,
        "vsl_link": None,
        "landing_page_config": {},
        "metadata_info": {},
        "archived_at": None,
        "deleted_at": None,
    }
    defaults.update(overrides)
    return ProductModel(**defaults)


@pytest.fixture
def db_with_offers(db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID):
    """Fixture with 3 offers across 2 tenants."""
    offer_a1 = create_product_model(tenant_a, name="Offer A1", status="active")
    offer_a2 = create_product_model(tenant_a, name="Offer A2", status="draft")
    offer_b1 = create_product_model(tenant_b, name="Offer B1", status="active")
    db.add_all([offer_a1, offer_a2, offer_b1])
    db.flush()
    return {"a1": offer_a1, "a2": offer_a2, "b1": offer_b1}
