"""Unit tests — OnboardingService (T-be-4 A1).

TDD RED → GREEN. All tests use mocked repositories (no Postgres needed).

Acceptance criteria (T-be-4):
  A1: OnboardingService idempotent same clerk_user_id within 1s window →
      returns existing tenant (test_idempotency).

Decision coverage:
  D1: DDD inside-out — services receive repos via DI, no direct DB access.
  D7: HIPAA-lite — contains_phi=false metadata on tenant creation.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.vitalia.application.services.onboarding_service import (
    CreateClinicProfileRequest,
    OnboardingResult,
    OnboardingService,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture()
def clerk_user_id() -> str:
    return "user_2abc123xyz"


@pytest.fixture()
def create_request(tenant_id: uuid.UUID) -> CreateClinicProfileRequest:
    return CreateClinicProfileRequest(
        clerk_user_id="user_2abc123xyz",
        clinic_name="Aurora Dental",
        clinic_type="dental",
        country="AR",
        city="Buenos Aires",
        owner_email="dra.aurora@example.com",
        plan_tier="starter",
    )


def _make_mock_result(tenant_id: uuid.UUID, clerk_user_id: str) -> OnboardingResult:
    return OnboardingResult(
        tenant_id=tenant_id,
        clerk_user_id=clerk_user_id,
        clinic_name="Aurora Dental",
        clinic_type="dental",
        is_new=True,
    )


# ── A1: Idempotency within 1s window ────────────────────────────────────────


def test_idempotency(tenant_id: uuid.UUID, clerk_user_id: str, create_request: CreateClinicProfileRequest) -> None:
    """A1: Same clerk_user_id within 1s window returns existing tenant (idempotent).

    OnboardingService must check an idempotency store keyed on clerk_user_id.
    If key exists (within TTL), it MUST return the cached result and NOT
    call the repo again.
    """
    existing_result = OnboardingResult(
        tenant_id=tenant_id,
        clerk_user_id=clerk_user_id,
        clinic_name="Aurora Dental",
        clinic_type="dental",
        is_new=False,
    )

    mock_idempotency_store = MagicMock()
    mock_idempotency_store.get = AsyncMock(return_value=existing_result.model_dump())

    mock_session = MagicMock()
    mock_audit_repo = MagicMock()

    import asyncio

    async def run() -> OnboardingResult:
        svc = OnboardingService(
            session=mock_session,
            audit_repo=mock_audit_repo,
            idempotency_store=mock_idempotency_store,
        )
        return await svc.create_clinic_profile(request=create_request)

    result = asyncio.get_event_loop().run_until_complete(run())

    assert result.tenant_id == tenant_id
    assert result.clerk_user_id == clerk_user_id
    assert result.is_new is False  # returned existing — not new
    # Must NOT have called session.add or session.flush (no DB writes on idempotent hit)
    mock_session.add.assert_not_called()


def test_create_new_tenant_calls_session_add(
    tenant_id: uuid.UUID,
    clerk_user_id: str,
    create_request: CreateClinicProfileRequest,
) -> None:
    """When no idempotency key exists, OnboardingService creates a new tenant row."""
    mock_idempotency_store = MagicMock()
    mock_idempotency_store.get = AsyncMock(return_value=None)  # no cached entry
    mock_idempotency_store.set = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()

    mock_audit_repo = MagicMock()
    mock_audit_repo.save = AsyncMock()

    import asyncio

    async def run() -> OnboardingResult:
        svc = OnboardingService(
            session=mock_session,
            audit_repo=mock_audit_repo,
            idempotency_store=mock_idempotency_store,
        )
        return await svc.create_clinic_profile(request=create_request)

    result = asyncio.get_event_loop().run_until_complete(run())

    assert result.is_new is True
    assert result.clerk_user_id == clerk_user_id
    mock_session.add.assert_called_once()


def test_onboarding_service_constructor_requires_di_params(
    tenant_id: uuid.UUID,
) -> None:
    """D1: OnboardingService must be constructable via DI params (no hardcoded session)."""
    import inspect

    sig = inspect.signature(OnboardingService.__init__)
    params = list(sig.parameters.keys())
    assert "session" in params, "OnboardingService must accept session via DI"
    assert "audit_repo" in params, "OnboardingService must accept audit_repo via DI"
    assert "idempotency_store" in params, "OnboardingService must accept idempotency_store via DI"


def test_create_clinic_profile_request_requires_clerk_user_id() -> None:
    """CreateClinicProfileRequest must have clerk_user_id as required field."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateClinicProfileRequest(
            # missing clerk_user_id
            clinic_name="Test",
            clinic_type="dental",
            country="AR",
            city="BA",
            owner_email="test@test.com",
            plan_tier="starter",
        )


def test_onboarding_result_is_pydantic_model() -> None:
    """OnboardingResult must be a Pydantic model with required fields."""
    result = OnboardingResult(
        tenant_id=uuid.uuid4(),
        clerk_user_id="user_abc",
        clinic_name="Test Clinic",
        clinic_type="dental",
        is_new=True,
    )
    assert result.is_new is True
    assert isinstance(result.tenant_id, uuid.UUID)
