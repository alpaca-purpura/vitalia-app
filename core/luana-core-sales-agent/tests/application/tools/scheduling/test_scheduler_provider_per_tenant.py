"""Tier-2 (multibrand-graph-runtime 2026-06-22 · ESC-1) — per-tenant scheduler resolution.

``scheduler_provider_for_tenant`` used to ignore ``tenant_id`` and always return the
``internal`` provider (`_ = tenant_id  # reserved`). A brand that registered its own
``SchedulerProvider`` via ``register_scheduler_provider`` could never be routed to.

The resolver now reads ``tenants.config_json['scheduler_provider']`` (the same JSONB the
engine already reads for prompts/keys) and returns the registered provider for that id.
Resilient: missing/unknown/typo'd id → ``internal`` (a misconfig must never break booking).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any

import pytest

from luana_core_sales_agent.application.tools.scheduling.providers import (
    SCHEDULER_PROVIDERS,
    InternalSchedulerProvider,
    register_scheduler_provider,
    scheduler_provider_for_tenant,
)


def _make_tenant(db: Any, config_json: dict[str, Any]) -> uuid.UUID:
    from luana_core_iam.infrastructure.models.tenant_model import TenantModel

    tid = uuid.uuid4()
    db.add(
        TenantModel(
            id=tid,
            slug=f"t-{tid.hex[:8]}",
            name="Test Clinic",
            config_json=config_json,
        )
    )
    db.commit()
    return tid


class _FakeBrandProvider:
    """A brand-registered provider stand-in (only needs provider_id + db ctor)."""

    provider_id = "vitalia_cal_test"

    def __init__(self, db: Any) -> None:
        self.db = db


@pytest.fixture(autouse=True)
def _restore_registry() -> Iterator[None]:
    snapshot = dict(SCHEDULER_PROVIDERS)
    yield
    SCHEDULER_PROVIDERS.clear()
    SCHEDULER_PROVIDERS.update(snapshot)


def test_no_config_defaults_to_internal(db: Any) -> None:
    tid = _make_tenant(db, {})
    provider = scheduler_provider_for_tenant(db, tid)
    assert isinstance(provider, InternalSchedulerProvider)


def test_explicit_internal_returns_internal(db: Any) -> None:
    tid = _make_tenant(db, {"scheduler_provider": "internal"})
    provider = scheduler_provider_for_tenant(db, tid)
    assert isinstance(provider, InternalSchedulerProvider)


def test_registered_brand_provider_is_routed(db: Any) -> None:
    register_scheduler_provider(_FakeBrandProvider)  # type: ignore[arg-type]
    tid = _make_tenant(db, {"scheduler_provider": "vitalia_cal_test"})
    provider = scheduler_provider_for_tenant(db, tid)
    assert isinstance(provider, _FakeBrandProvider)
    assert provider.db is db


def test_unregistered_provider_id_falls_back_to_internal(db: Any) -> None:
    # Tenant asked for a provider nobody registered (typo / not-yet-deployed).
    tid = _make_tenant(db, {"scheduler_provider": "cal_com_not_deployed"})
    provider = scheduler_provider_for_tenant(db, tid)
    assert isinstance(provider, InternalSchedulerProvider)


def test_unknown_tenant_falls_back_to_internal(db: Any) -> None:
    provider = scheduler_provider_for_tenant(db, uuid.uuid4())
    assert isinstance(provider, InternalSchedulerProvider)


def test_malformed_config_value_falls_back_without_crashing(db: Any) -> None:
    # Operator-set JSONB could hold a non-string (unhashable in the registry `in` check).
    tid = _make_tenant(db, {"scheduler_provider": ["cal_com"]})
    provider = scheduler_provider_for_tenant(db, tid)
    assert isinstance(provider, InternalSchedulerProvider)
