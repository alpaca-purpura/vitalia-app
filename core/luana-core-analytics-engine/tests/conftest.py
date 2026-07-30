import os
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from sqlalchemy import CHAR, Text, create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

# --- Monkeypatch PostgreSQL Types for SQLite BEFORE any model imports ---
# Models use postgresql.JSONB and postgresql.UUID which SQLite can't compile.
# Patch them to SQLite-compatible TypeDecorators here, before model_registry
# is imported. Pattern mirrored from AISALESHT backend/tests/conftest.py.

_ORIGINAL_POSTGRESQL_JSONB = postgresql.JSONB
_ORIGINAL_POSTGRESQL_UUID = postgresql.UUID


class _MockJSONB(TypeDecorator):
    """SQLite-compatible JSONB: stores as Text, delegates to real JSONB on Postgres."""

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


class _MockUUID(TypeDecorator):
    """SQLite-compatible UUID: stores as CHAR(36), delegates to real UUID on Postgres."""

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


postgresql.JSONB = _MockJSONB  # type: ignore[attr-defined]
postgresql.UUID = _MockUUID  # type: ignore[attr-defined]

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


@pytest.fixture
def test_tenant_id() -> UUID:
    """Fixed tenant UUID for test determinism."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def mock_credentials() -> dict:
    """Simulated OAuth credentials dict."""
    return {
        "access_token": "test-access-token-abc123",
        "refresh_token": "test-refresh-token-xyz789",
    }


@pytest.fixture
def mock_connection_credentials():
    """ConnectionCredentials instance for testing."""
    from luana_core_analytics_engine.domain.ports import ConnectionCredentials

    return ConnectionCredentials(
        channel_type="meta",
        credentials={"access_token": "test-token"},
        config={"page_id": "123456"},
    )


@pytest.fixture
def sample_offer_id() -> UUID:
    """Fixed offer UUID for test determinism."""
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def sample_customer_id() -> UUID:
    """Fixed customer UUID for test determinism."""
    return uuid.UUID("33333333-3333-3333-3333-333333333333")


# ── New fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def date_range() -> tuple[date, date]:
    """Fixed 14-day date range for test determinism."""
    return (date(2026, 3, 1), date(2026, 3, 14))


@pytest.fixture
def mock_db_session() -> MagicMock:
    """MagicMock DB session with async execute/commit/rollback."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_cache() -> AsyncMock:
    """AsyncMock cache that always returns None (cache miss)."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.invalidate_tenant = AsyncMock()
    return cache


@pytest.fixture
def make_extracted_metric():
    """Factory fixture for ExtractedMetric objects."""
    from luana_core_analytics_engine.infrastructure.providers.base import ExtractedMetric

    def _factory(**overrides):
        defaults = {
            "provider": "meta",
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 1000.0,
            "unit": "count",
            "date": date(2026, 3, 10),
        }
        defaults.update(overrides)
        return ExtractedMetric(**defaults)

    return _factory


@pytest.fixture
def make_extraction_result():
    """Factory fixture for ExtractionResult objects."""
    from luana_core_analytics_engine.domain.extraction_result import ExtractionResult

    def _factory(metrics=None, failures=None):
        return ExtractionResult(
            metrics=metrics or [],
            failures=failures or [],
        )

    return _factory


def seed_official_metrics(
    db,
    tenant_id,
    *,
    channel_slug: str = "meta-ads",
    provider: str = "meta",
    metric_name: str = "impressions",
    unit: str = "count",
    cost_type: str | None = "investment",
    rows: list[dict] | None = None,
) -> list:
    """Insert OfficialMetricModel rows into SQLite db. Returns inserted instances."""
    import uuid
    from datetime import date

    from luana_core_analytics_engine.infrastructure.models.official_metrics_model import (
        OfficialMetricModel,
    )

    if rows is None:
        rows = [
            {"metric_date": date(2026, 3, 1), "value": 1000.0},
            {"metric_date": date(2026, 3, 2), "value": 1500.0},
            {"metric_date": date(2026, 3, 3), "value": 800.0},
        ]
    instances = []
    for r in rows:
        obj = OfficialMetricModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            provider=provider,
            channel_slug=channel_slug,
            metric_name=metric_name,
            value=r["value"],
            unit=unit,
            cost_type=cost_type,
            metric_date=r["metric_date"],
            campaign_id=r.get("campaign_id"),
            ad_set_id=r.get("ad_set_id"),
            ad_id=r.get("ad_id"),
        )
        db.add(obj)
        instances.append(obj)
    db.commit()
    return instances


@pytest.fixture
def sample_official_metrics(test_tenant_id) -> list[dict]:
    """Sample official_metrics row dicts for aggregation tests."""
    return [
        {
            "tenant_id": test_tenant_id,
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 1000.0,
            "unit": "count",
            "currency": None,
            "cost_type": "investment",
            "metric_date": date(2026, 3, 1),
        },
        {
            "tenant_id": test_tenant_id,
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 1500.0,
            "unit": "count",
            "currency": None,
            "cost_type": "investment",
            "metric_date": date(2026, 3, 2),
        },
        {
            "tenant_id": test_tenant_id,
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 800.0,
            "unit": "count",
            "currency": None,
            "cost_type": "investment",
            "metric_date": date(2026, 3, 3),
        },
    ]


# ──────────────────────────────────────────────────────────────────────────────
# SQLite in-memory DB fixtures for integration tests that require a real session
# (e.g., test_channel_granularity_filter, test_extraction_run_metadata, etc.)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def db_engine():
    """Create an in-memory SQLite engine with all analytics models registered.

    postgresql.JSONB and postgresql.UUID are patched to SQLite-compatible
    TypeDecorators at module load time (top of this file), so create_all
    works against SQLite.
    """
    import luana_core_analytics_engine.infrastructure.models  # noqa: F401 — register all models
    from luana_core_platform.domain.base_entity import Base

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
    """Provide a transactional DB session that rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
